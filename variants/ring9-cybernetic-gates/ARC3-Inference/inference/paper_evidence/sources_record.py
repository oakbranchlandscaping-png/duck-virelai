"""Claims from a level's certified census and record (WO-PE-03B, interface §2.2, record rows).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.2.

Roles (ROLE), scoped nulls (CONDITION / NO_OBSERVED_EFFECT, Sol D18), transformation patterns (one claim per pattern
and explanation status, D19), gaps and non-complete dossier chapters (GAP audits, D20), and the observed level clear
(CONDITION / LEVEL_CLEARED_BY). Each is a pure read of the sealed model; patterns come from
``world_description.describe_world``, the model's own describer.
"""
from __future__ import annotations

from typing import Any, Iterator, Mapping

from inference.paper_evidence import claims as c
from inference.paper_evidence.context import (LevelContext, entity_subject, product_attribution, role_claim_subject,
                                              track_or_level)

UNEXPLAINED = frozenset({"NOT_COVERED"})


def _base(ctx: LevelContext) -> dict[str, Any]:
    return {"game_id": ctx.game_id, "level": ctx.number}


def _audit(ctx: LevelContext, subject: Mapping[str, Any], predicate: str, obj: Any, source: Mapping[str, Any],
           status: str = "OPEN") -> dict[str, Any]:
    return c.claim(**_base(ctx), family="GAP", kind="AUDIT", subject=subject, predicate=predicate, obj=obj,
                   status=status, executor="SYSTEM", admission="NOT_APPLICABLE", certification="NONE", source=source)


def role_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    for index, role in enumerate(ctx.level["certified"]["roles"]):
        who = product_attribution(ctx, role["gate_id"])
        yield c.claim(**_base(ctx), family="ROLE", kind="PROPOSITION", subject=role_claim_subject(ctx, role),
                      predicate="ROLE_IS", obj=role["role"], status="CERTIFIED", executor="SYSTEM",
                      admission="NOT_APPLICABLE", certification=who["certification"],
                      source={"path": f"certified.roles[{index}]", "product_id": who["product_id"],
                              "provenance_event": who["provenance_event"]},
                      refs=[*(role.get("evidence_refs") or ()), *(role.get("witness_refs") or ())])


def scoped_null_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    for index, null in enumerate(ctx.level["certified"]["scoped_nulls"]):
        subject = track_or_level(ctx, null["track_id"]) if null.get("track_id") in ctx.tracks \
            else entity_subject(ctx, null.get("entity_id"))
        yield c.claim(**_base(ctx), family="CONDITION", kind="PROPOSITION", subject=subject,
                      predicate="NO_OBSERVED_EFFECT", obj=null["scope"], status="OBSERVED", executor="CONTROLLER",
                      admission="NOT_APPLICABLE", certification="RECORD_DERIVED",
                      source={"path": f"certified.scoped_nulls[{index}]"}, refs=[null.get("evidence_ref") or ""])


def _pattern_subject(ctx: LevelContext, pattern: Mapping[str, Any]) -> dict[str, Any]:
    tracks = pattern["object"].get("tracks") or []
    return track_or_level(ctx, tracks[0] if tracks else None)


def pattern_claims(ctx: LevelContext, described: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    """One TRANSFORMATION observation per (pattern, explanation status): status is on the assertion (D19)."""
    for pattern in described.get("patterns") or ():
        subject = _pattern_subject(ctx, pattern)
        for basis, count in sorted((pattern.get("explanations") or {}).items()):
            yield c.claim(**_base(ctx), family="TRANSFORMATION", kind="PROPOSITION", subject=subject,
                          predicate="OBSERVED_CHANGE", obj={"verb": pattern["verb"], "sites": pattern["sites"]},
                          scope={"actions": sorted(pattern.get("by_action") or {})},
                          status="UNEXPLAINED" if basis in UNEXPLAINED else "EXPLAINED", executor="SYSTEM",
                          admission="NOT_APPLICABLE", certification="RECORD_DERIVED",
                          source={"pattern_id": pattern["pattern_id"], "explanation": basis},
                          measures={"count": count, "pattern_count": pattern["count"],
                                    "by_action": pattern.get("by_action") or {}})


def gap_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    for index, gap in enumerate(ctx.level.get("gaps") or ()):
        yield _audit(ctx, track_or_level(ctx, gap.get("subject")), "GAP",
                     {"reason": gap.get("reason"), "chapter": gap.get("chapter")}, {"gap_index": index})


def chapter_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    """A lever chapter that is not COMPLETE is an audit of what the model does not know about that lever."""
    for entity_id, dossier in sorted((ctx.level.get("lever_dossiers") or {}).items()):
        for name, chapter in sorted((dossier.get("chapters") or {}).items()):
            if chapter.get("status") != "COMPLETE":
                closed = chapter.get("status") == "CLOSED_UNRESOLVED"
                yield _audit(ctx, entity_subject(ctx, entity_id), "CHAPTER_STATE",
                             {"chapter": name, "status": chapter.get("status")},
                             {"dossier": entity_id, "chapter": name},
                             status="CLOSED_WITHOUT_FINDING" if closed else "OPEN")


def win_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    episode = ctx.level.get("win_episode") or {}
    subject = c.plain_subject("LEVEL", f"level-{ctx.number}")
    if not str(episode.get("state") or "").startswith("OBSERVED"):
        yield _audit(ctx, subject, "NO_CLEAR_OBSERVED", episode.get("state"), {"path": "win_episode"})
        return
    identity = episode.get("identity") or {}
    action = identity.get("terminal_action") or {}
    yield c.claim(**_base(ctx), family="CONDITION", kind="PROPOSITION", subject=subject, predicate="LEVEL_CLEARED_BY",
                  obj={key: action.get(key) for key in ("action", "row", "col") if key in action},
                  status="OBSERVED", executor="SYSTEM", admission="NOT_APPLICABLE", certification="RECORD_DERIVED",
                  source={"path": "win_episode", "transition_id": identity.get("winning_transition")},
                  refs=[identity.get("evidence_ref") or ""],
                  measures={"state": episode.get("state"), "explanations": episode.get("explanations") or {},
                            "limit": (episode.get("limits") or {}).get("claim")})


__all__ = ["chapter_claims", "gap_claims", "pattern_claims", "role_claims", "scoped_null_claims", "win_claims"]

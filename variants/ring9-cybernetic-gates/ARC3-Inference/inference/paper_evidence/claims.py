"""The atomic claim record and its two identities (WO-PE-03B; Sol's D16, D17).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.1.

A claim is one proposition (or one audit statement) about one subject. Its ``claim_key`` is the full SHA-256 of the
proposition under strict canonical JSON: schema, game, level, family, kind, the canonical subject without its solver
trace, predicate, object and scope. Status, executor, admission, certification, field source, source and refs are
outside it, so the same proposition proposed by Duck and certified by the gate is one ``claim_key`` and two
assertions. ``assertion_id`` adds the exact source record.

Subjects are human-facing (D16): a readable handle plus the geometry of the object's first sighting (class, anchor,
inclusive bounding box, cell count, and the level-entry board hash when it was seen at entry). Solver ids live in
``subject.trace`` and never enter identity.
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework import strict_json

SCHEMA = "virelai-paper-claim-v1"
FAMILIES = ("ROLE", "TRANSFORMATION", "RELATION", "LAW", "PREDICTION", "CONDITION", "GAP")
KINDS = ("PROPOSITION", "AUDIT")
SUBJECT_TYPES = ("OBJECT", "AGENT", "ACTION", "COUNTER", "LEVEL")
EXECUTORS = ("DUCK", "CONTROLLER", "SYSTEM")
ADMISSIONS = ("ADMITTED", "REFUSED", "NOT_APPLICABLE", "UNCERTIFIED")
CERTIFICATIONS = ("ANSWER_CERTIFIED", "GATE_DERIVED", "UNATTRIBUTED", "RECORD_DERIVED", "NONE")
# Interface v2 §2's statuses, plus PROPOSED: what a submitted answer field asserts before any gate outcome.
STATUSES = ("OBSERVED", "CERTIFIED", "EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED", "PREDICTED", "SUPPORTED",
            "CONTRADICTED", "OPEN", "CLOSED_WITHOUT_FINDING", "PROPOSED")
ENTRY_SOURCES = frozenset({"INITIAL_FRAME", "LEVEL_ENTRY"})


class ClaimError(ValueError):
    """A claim that violates the contract (an unknown family, kind, executor, admission or certification)."""


def sha256(value: Any) -> str:
    return strict_json.sha256(value)


def track_subject(track: Mapping[str, Any], entry_sha256: str | None) -> dict[str, Any]:
    """The canonical subject of an observed object: its first sighting, in the census segmentation."""
    first = track["segments"][0]
    at_entry = first["first"]["source"] in ENTRY_SOURCES
    frame = "ENTRY" if at_entry else f"T{first['first'].get('transition_id')}"
    return {"type": "OBJECT", "handle": f"c{first['class_id']}@{first['anchor'][0]},{first['anchor'][1]}",
            "geometry": {"frame": frame, "board_sha256": entry_sha256 if at_entry else None,
                         "class": first["class_id"], "anchor": list(first["anchor"]), "bbox": list(first["bbox"]),
                         "cell_count": first["cell_count"]},
            "trace": {"track_id": track["track_id"], "entity_id": (track.get("g3_join") or {}).get("entity_id")}}


def plain_subject(kind: str, handle: str, trace: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A subject with no geometry: the agent, an action, the counter as a variable, or the level itself."""
    if kind not in SUBJECT_TYPES:
        raise ClaimError(f"unknown subject type {kind!r}")
    return {"type": kind, "handle": handle, "geometry": None, "trace": dict(trace or {})}


def identity_subject(subject: Mapping[str, Any]) -> dict[str, Any]:
    """The subject as it enters ``claim_key``: everything but the solver trace."""
    return {key: value for key, value in subject.items() if key != "trace"}


def _require(value: str, allowed: tuple[str, ...], name: str) -> None:
    if value not in allowed:
        raise ClaimError(f"unknown {name} {value!r}")


def claim(*, game_id: str, level: int, family: str, kind: str, subject: Mapping[str, Any], predicate: str,
          obj: Any, scope: Mapping[str, Any] | None = None, status: str, executor: str, admission: str,
          certification: str, field_source: str | None = None, source: Mapping[str, Any],
          refs: list[str] | None = None, measures: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One atomic claim with both identities computed from the strict canonical JSON of its parts.

    ``measures`` carries counts (witnesses, transitions, explanation tallies): evidence, never identity."""
    for value, allowed, name in ((family, FAMILIES, "family"), (kind, KINDS, "kind"), (executor, EXECUTORS, "executor"),
                                 (admission, ADMISSIONS, "admission"), (certification, CERTIFICATIONS, "certification"),
                                 (status, STATUSES, "status")):
        _require(value, allowed, name)
    refs = [refs] if isinstance(refs, str) else [ref for ref in refs or () if isinstance(ref, str)]  # malformed input
    proposition = {"schema": SCHEMA, "game_id": game_id, "level": level, "family": family, "kind": kind,
                   "subject": identity_subject(subject), "predicate": predicate, "object": obj,
                   "scope": dict(scope or {})}
    claim_key = sha256(proposition)
    return {"schema": SCHEMA, "claim_key": claim_key, "assertion_id": sha256({"claim_key": claim_key,
                                                                            "source": dict(source)}),
            "game_id": game_id, "level": level, "family": family, "kind": kind, "subject": dict(subject),
            "predicate": predicate, "object": obj, "scope": dict(scope or {}), "status": status,
            "executor": executor, "admission": admission, "certification": certification,
            "field_source": field_source, "source": dict(source), "refs": sorted({str(ref) for ref in refs or () if ref}),
            "measures": dict(measures or {})}


__all__ = ["ADMISSIONS", "CERTIFICATIONS", "ClaimError", "EXECUTORS", "FAMILIES", "KINDS", "SCHEMA", "STATUSES",
           "SUBJECT_TYPES",
           "claim", "identity_subject", "plain_subject", "sha256", "track_subject"]

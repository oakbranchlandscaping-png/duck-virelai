"""What Duck reads of the semantic library: a compact digest and paged retrieval, from a validated v2 model.

Author: Claude (Alpha build seat), 2026-10-11. Sol's directive after the WO-L2a hooks: "build the card
digest and retrieval from the validated library ... with a clear current goal, compact certified findings,
typed open gaps, and retrieval handles" (plan stage C; BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v1 §2).

- ``live_model(machine)`` compiles the census in memory and seals it, so every view below reads a model
  that passed ``world_model_v2.validate``. Its persist reason is ``LIVE_VIEW``, which the writer refuses:
  the canonical file is still written only by H1/H2. Journal checks stay PENDING (only H2 reconciles), so
  nothing the view shows claims ACCOUNTED before the run's history is checked.
- ``library_digest(model)`` and ``library_page(model, kind, ...)`` are pure: they read only the payload.
  Both are bounded however large the library grows (Sol's review, 2026-10-11): the whole rendered digest
  section, header included, fits ``DIGEST_BUDGET``; every page fits ``PAGE_BUDGET`` (below the tool's
  output limit), clips long lists to a count, and names the exact call that continues it.

The census is never compiled on the controller path or inside ``build_card`` (replay measurement): only
the Duck-facing prompt section and the ``virelai('library', ...)`` query call ``live_model``, and a cache
keyed on the gate record returns the same sealed model until something it reads has changed.
"""
from __future__ import annotations

import json
import weakref
from typing import Any, Mapping, Sequence

from inference.framework.world_model_v2 import LIVE_VIEW, seal, validate

DIGEST_SCHEMA = "virelai-library-digest-v1"
PAGE_SCHEMA = "virelai-library-page-v1"
DIGEST_BUDGET = 2_500  # characters of the rendered digest; its own budget, beside the card's
HEADER = "VIRELAI LIBRARY (read-only; certified by the gates, never by Duck):\n"

# The gate goals as ruling 22 sharpens them: the question the active gate is answering.
GOAL_QUESTIONS = {
    "G0-ACTION-METADATA": "Which actions does this world offer, and which take coordinates?",
    "G1-EGO": "Where is the control locus: what do actions move or select?",
    "G2-COUNTER": "Which object is the counter, and what changes it?",
    "G3-LEVERS": "Which objects are levers: what responds when the ego acts on it?",
    "G4-REACTIONS": "What does each lever's activation change?",
    "G4.2-LEVER-ORBITS": "Which states does each lever move through when pressed repeatedly?",
    "G4-B-LEVER-RELATIONS": "How do the levers' effects relate to one another?",
    "G4-C-LEVER-LAW": "Which law, stated for the boards tested, governs the levers together?",
    "PLAY-NORMAL": "No gate can act on this level: play with what is certified; every action is still recorded.",
}
# Gap reasons, most actionable first: a broken record before an unresolved identity before an open question.
GAP_ORDER = ("RECORD_MISMATCH", "IDENTITY_UNRESOLVED", "INCONCLUSIVE", "BUDGET", "CLASS_CHANGED",
             "NOT_REACHED", "FOUNDATION_UNRESOLVED", "NOT_BUILT")
# The open questions that belong to the active gate's goal, by the census's own wording (never a world's).
GOAL_GAP_TERMS = {"G1-EGO": "ego", "G2-COUNTER": "counter", "G3-LEVERS": "lever", "G4-REACTIONS": "lever",
                  "G4.2-LEVER-ORBITS": "lever", "G4-B-LEVER-RELATIONS": "lever", "G4-C-LEVER-LAW": "lever"}
PAGE_KINDS = ("levels", "objects", "object", "gaps", "role", "evidence")
HANDLES = (
    "virelai('library', kind='levels')",
    "virelai('library', kind='objects', offset=0, limit=10)",
    "virelai('library', kind='object', id=TRACK_ID)",
    "virelai('library', kind='gaps', reason=REASON, subject=SUBJECT, offset=0, limit=10)",
    "virelai('library', kind='role', id=ENTITY_ID_OR_ROLE)",
    "virelai('library', kind='evidence', id=REF)",
)
PAGE_LIMIT = 25
# The python tool's output limit is LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS x 4 = 4,096 characters by default; the
# query envelope and the JSON escaping of stdout take the rest, so a page's own JSON stays below this.
PAGE_BUDGET = 3_000
LIST_KEEP = 8  # a list inside a returned item keeps this many entries and states its total
TEXT_KEEP = 240  # characters of any one string
OBJECT_PARTS = ("segments", "class_events", "possible_correspondence")


# ---- the live, validated model --------------------------------------------------------------------

_CACHE: "weakref.WeakKeyDictionary[Any, tuple[Any, dict[str, Any]]]" = weakref.WeakKeyDictionary()


def _cache_key(machine: Any) -> tuple[Any, ...]:
    """Everything the census reads that can change without a new transition row."""
    journal = machine.target_journal
    products = tuple(
        (contract.target_id, product.product_id, product.revision)
        for contract in machine.target_registry.ordered()
        if (product := journal.active_product(contract.target_id)) is not None
    )
    adapter = (getattr(machine, "_adapters", None) or {}).get("G3-LEVERS")
    lifecycle = getattr(adapter, "lifecycle_journal", None)
    g3 = (
        sum(len(item.events) for item in lifecycle.entities.values()) if lifecycle is not None else -1,
        len(getattr(adapter, "_terrain_roles", None) or ()), len(getattr(adapter, "_bounded_ambiguities", None) or ()),
        len(getattr(adapter, "_lever_discoveries", None) or ()),
    )
    return (len(machine.transition_index), len(getattr(machine, "level_censuses", ())), len(machine.levels),
            machine.gate_id, machine.lives.level, machine.lives.life, products, g3)


def live_model(machine: Any, *, game_id: str = "live", run_stem: str = "live") -> dict[str, Any]:
    """The open level's census plus every frozen level, compiled in memory and sealed (validated)."""
    from inference.framework.library_census import ExecutionRecord, compile_world_model

    key = _cache_key(machine)
    cached = _CACHE.get(machine)
    if cached is not None and cached[0] == key:
        return cached[1]
    board = tuple(tuple(int(cell) for cell in row) for row in machine.ego._initial_grid)
    actions = tuple(item.action for item in machine.ego.affordances)
    # Recorded, not executed: the view never reconciles (H2 does), so these names only label the manifest.
    recorded = tuple(str((row.get("action") or {}).get("action") or "") for row in machine.transition_index)
    model = seal(compile_world_model(
        machine, ExecutionRecord(board, int(machine.lives.level), actions, recorded), game_id=game_id,
        run_stem=run_stem, persist_reason=LIVE_VIEW, frozen_levels=list(getattr(machine, "level_censuses", ())),
        reconcile_journal=False,
    ))
    _CACHE[machine] = (key, model)
    return model


# ---- the digest ------------------------------------------------------------------------------------

def _chars(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str))


def _current(model: Mapping[str, Any]) -> Mapping[str, Any]:
    levels = model["levels"]
    return next((level for level in levels if level["state"] == "OPEN"), levels[-1])


def _goal(level: Mapping[str, Any], target: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The digest's goal: the agenda's selected question when the live view supplies it (Sol's review,
    finding 1: the card, the digest and the capability name one question), else the gate in progress."""
    if target is not None:
        return {"question_id": target.get("question_id"), "gate_id": target.get("gate_id"),
                "question": str(target.get("question") or ""), "level": target.get("level", level["level"])}
    gates = level["certified"]["gates"]
    active = next((gate["gate_id"] for gate in gates if gate["disposition"] == "IN_PROGRESS"), None)
    if active is None:
        return {"gate_id": None, "question": "No gate is in progress on this level.", "level": level["level"]}
    return {"gate_id": active, "question": GOAL_QUESTIONS.get(active, f"Answer {active}."), "level": level["level"]}


def _ids(ids: Sequence[str], limit: int) -> str:
    shown = ",".join(ids[:limit])
    return f"{shown}{f' +{len(ids) - limit}' if len(ids) > limit else ''}"


def _identity(role: Mapping[str, Any]) -> str:
    identity = role.get("identity") or {}
    if identity.get("status") == "EXACT_ONE_TO_ONE":
        return f"object {identity.get('track_id')}"
    return "no object identity" if identity.get("status") == "NOT_APPLICABLE" else "object identity unresolved"


def _clip_text(text: Any, keep: int = TEXT_KEEP) -> Any:
    if not isinstance(text, str) or len(text) <= keep:
        return text
    return f"{text[:keep]}... (+{len(text) - keep} chars)"


def _clip(value: Any, keep: int = LIST_KEEP) -> Any:
    """Every list longer than ``keep`` keeps its head and gains ``<key>_total``; long strings are cut."""
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, list) and len(item) > keep:
                out[key] = [_clip(entry, keep) for entry in item[:keep]]
                out[f"{key}_total"] = len(item)
            else:
                out[key] = _clip(item, keep)
        return out
    if isinstance(value, list):
        return [_clip(entry, keep) for entry in value]
    return _clip_text(value)


def _findings(level: Mapping[str, Any], id_limit: int) -> list[str]:
    lines: list[str] = []
    roles = level["certified"]["roles"]
    for role in roles:
        if role["role"] == "EGO":
            lines.append(f"EGO ({role.get('mode')}): {role.get('subject')}, {_identity(role)}")
        elif role["role"] == "COUNTER":
            lines.append(f"COUNTER: a {role.get('mask_cell_count')}-cell mask, masked from every change; {_identity(role)}")
    levers = [role for role in roles if role["role"] == "LEVER"]
    if levers:
        accepted = sorted(role["entity_id"] for role in levers if role.get("inventory_status") == "ACCEPTED")
        pending = sorted(role["entity_id"] for role in levers if role.get("inventory_status") != "ACCEPTED")
        joined = sum(1 for role in levers if (role.get("identity") or {}).get("status") == "EXACT_ONE_TO_ONE")
        parts = [f"accepted {_ids(accepted, id_limit)}" if accepted else "", f"pending {_ids(pending, id_limit)}" if pending else ""]
        lines.append(f"LEVERS x{len(levers)} (each witnessed once at G3; {joined} joined to an object): "
                     + "; ".join(part for part in parts if part))
    nulls = level["certified"].get("scoped_nulls") or []
    if nulls:
        lines.append(f"SCOPED NULLS x{len(nulls)}: no response in the recorded state; no inertness claim")
    terrain = level["observation"].get("terrain") or []
    if terrain:
        labels = sorted({str(item.get("label")) for item in terrain})
        lines.append(f"TERRAIN x{len(terrain)} ({_ids(labels, id_limit)}): observed interaction, not a role")
    return [_clip_text(line, 200) for line in lines] or ["nothing certified yet on this level"]


def _gap_groups(gaps: Sequence[Mapping[str, Any]], goal_gate: str | None = None) -> list[dict[str, Any]]:
    """Gaps grouped by (reason, question): a record mismatch first, then the active goal's own questions."""
    groups: dict[tuple[str, str], list[str]] = {}
    for gap in gaps:
        groups.setdefault((gap["reason"], gap["archetype_question"]), []).append(str(gap.get("subject")))
    rank = {reason: index for index, reason in enumerate(GAP_ORDER)}
    term = GOAL_GAP_TERMS.get(goal_gate or "")

    def key(item: tuple[tuple[str, str], list[str]]) -> tuple[Any, ...]:
        (reason, question), subjects = item
        on_goal = bool(term) and term in question.lower()
        return (reason != "RECORD_MISMATCH", not on_goal, rank.get(reason, len(rank)), -len(subjects), question)

    ordered = sorted(groups.items(), key=key)
    return [{"reason": reason, "question": question, "count": len(subjects), "subjects": subjects}
            for (reason, question), subjects in ordered]


def _objects(level: Mapping[str, Any]) -> dict[str, int]:
    tracks = level["observation"]["tracks"]
    roled = {(role.get("identity") or {}).get("track_id") for role in level["certified"]["roles"]} - {None}
    return {
        "tracks": len(tracks),
        "present": sum(1 for track in tracks if track["present_now"]),
        "departed": sum(1 for track in tracks if (track.get("end") or {}).get("reason") == "DEPARTED"),
        "life_ended": sum(1 for track in tracks if (track.get("end") or {}).get("reason") == "LIFE_ENDED"),
        "with_a_role": sum(1 for track in tracks if track["track_id"] in roled),
    }


# (gap kinds shown, subjects per kind, ids per findings line, earlier levels shown, handles shown)
DIGEST_TIERS = ((8, 3, 6, 6, 6), (6, 2, 4, 4, 6), (5, 1, 3, 3, 3), (4, 0, 2, 2, 3), (3, 0, 0, 1, 1), (2, 0, 0, 0, 1))


def _digest_at(model: Mapping[str, Any], tier: tuple[int, int, int, int, int],
               target: Mapping[str, Any] | None = None) -> dict[str, Any]:
    groups, subjects, id_limit, earlier, handles = tier
    level = _current(model)
    goal = _goal(level, target)
    gap_groups = _gap_groups(level["gaps"], goal["gate_id"])
    shown = [
        _clip_text(f"{group['reason']} x{group['count']}: {group['question']}"
                   + (f" [{_ids(group['subjects'], subjects)}]" if subjects else ""), 220)
        for group in gap_groups[:groups]
    ]
    if len(gap_groups) > groups:
        shown.append(f"+{len(gap_groups) - groups} more gap kinds: virelai('library', kind='gaps')")
    others = [f"L{item['level']} {item['state']} {item['accounting']['status']}"
              for item in model["levels"] if item is not level]
    kept = others[len(others) - earlier:] if earlier else []
    if len(others) > len(kept):
        kept.insert(0, f"+{len(others) - len(kept)} earlier: virelai('library', kind='levels')")
    return {
        "schema": DIGEST_SCHEMA,
        "revision": model["content_sha256"][:12],
        "goal": goal,
        "gates": "; ".join(f"{gate['gate_id']} {gate['disposition']}" for gate in level["certified"]["gates"]),
        "certified": _findings(level, id_limit),
        "objects": _objects(level),
        "open_gaps": {"total": len(level["gaps"]), "kinds": shown},
        "accounting": {"status": level["accounting"]["status"], "missing": level["accounting"]["missing"][:4],
                       "journal_check": level["record"]["journal_check"]["status"]},
        "earlier_levels": kept,
        "retrieve": list(HANDLES[:handles]),
    }


def _minimal_digest(model: Mapping[str, Any], target: Mapping[str, Any] | None = None) -> dict[str, Any]:
    level = _current(model)
    goal = _goal(level, target)
    return {"schema": DIGEST_SCHEMA, "revision": model["content_sha256"][:12],
            "goal": {**goal, "question": _clip_text(goal["question"], 160)},
            "open_gaps": {"total": len(level["gaps"])}, "accounting": {"status": level["accounting"]["status"]},
            "levels": len(model["levels"]), "retrieve": [HANDLES[0]]}


def _render(digest: Mapping[str, Any]) -> str:
    return HEADER + json.dumps(digest, sort_keys=True, default=str)


def library_digest(model: Mapping[str, Any], budget: int = DIGEST_BUDGET, *,
                   target: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The compact view: goal, certified findings, typed open gaps, retrieval handles.

    Its whole rendered section, header included, fits ``budget``: each tier shows less, the last keeps only
    the goal, the counts and one handle. A budget too small even for that is refused, never exceeded.
    ``target`` is the gate agenda's selected question (``library_agenda.selected_target``); without it the
    goal is the gate in progress, as for a saved record read with no live machine.
    """
    validate(model)
    for tier in DIGEST_TIERS:
        digest = _digest_at(model, tier, target)
        if len(_render(digest)) <= budget:
            return digest
    digest = _minimal_digest(model, target)
    if len(_render(digest)) > budget:
        raise ValueError(f"a digest budget of {budget} characters cannot hold the goal and the counts")
    return digest


def render_library_digest(model: Mapping[str, Any], budget: int = DIGEST_BUDGET, *,
                          target: Mapping[str, Any] | None = None) -> str:
    return _render(library_digest(model, budget, target=target))


# ---- retrieval -------------------------------------------------------------------------------------

def _level(model: Mapping[str, Any], number: Any) -> Mapping[str, Any]:
    if number is None:
        return _current(model)
    for level in model["levels"]:
        if level["level"] == int(number):
            return level
    raise ValueError(f"level {number} is not in the library; known levels: {[item['level'] for item in model['levels']]}")


def _object_row(level: Mapping[str, Any], track: Mapping[str, Any]) -> dict[str, Any]:
    roles = [role["role"] + (f" {role['entity_id']}" if role.get("entity_id") else "")
             for role in level["certified"]["roles"] if (role.get("identity") or {}).get("track_id") == track["track_id"]]
    return {
        "track_id": track["track_id"], "life": track["life"], "present_now": track["present_now"],
        "end": (track.get("end") or {}).get("reason"), "roles": roles,
        "g3_entity": (track.get("g3_join") or {}).get("entity_id"), "segments": len(track["segments"]),
        "class_events": len(track.get("class_events") or ()),
    }


def _call(kind: str, **options: Any) -> str:
    shown = ", ".join(f"{key}={value!r}" for key, value in options.items() if value is not None)
    return f"virelai('library', kind={kind!r}{', ' if shown else ''}{shown})"


def _paged(page: dict[str, Any], rows: Sequence[Any], offset: Any, limit: Any, call: dict[str, Any]) -> dict[str, Any]:
    """A window of ``rows`` that fits ``PAGE_BUDGET``: fewer rows, then shorter lists, never a cut response."""
    start = max(0, int(offset or 0))
    size = max(1, min(PAGE_LIMIT, int(limit or 10)))
    keep = LIST_KEEP
    while True:
        items = [_clip(row, keep) for row in rows[start:start + size]]
        more = start + size < len(rows)
        result = {**page, "total": len(rows), "offset": start, "limit": size, "truncated": more, "items": items,
                  "next": _call(**call, offset=start + size, limit=size) if more else None}
        if _chars(result) <= PAGE_BUDGET:
            return result
        if size > 1:
            size = max(1, size // 2)
        elif keep > 0:
            keep = keep // 2
        else:
            return {**result, "items": [], "truncated": True,
                    "error": "one entry exceeds the page budget even with its lists reduced to counts",
                    "next": _call(**call, offset=start + 1, limit=1)}


def _object_page(model: Mapping[str, Any], page: dict[str, Any], track_id: str, part: Any,
                 offset: Any, limit: Any) -> dict[str, Any]:
    part = str(part or "segments")
    if part not in OBJECT_PARTS:
        raise ValueError(f"part must be one of {list(OBJECT_PARTS)}")
    for level in model["levels"]:
        for track in level["observation"]["tracks"]:
            if track["track_id"] != track_id:
                continue
            gaps = [gap for gap in level["gaps"] if gap.get("subject") == track_id]
            header = {**_object_row(level, track), "end_detail": _clip(track.get("end")), "band1": track.get("band1"),
                      "possible_correspondence": len(track.get("possible_correspondence") or ()),
                      "gaps": len(gaps), "gaps_call": _call("gaps", subject=track_id) if gaps else None,
                      "parts": {name: _call("object", id=track_id, part=name) for name in OBJECT_PARTS}}
            rows = list(track.get(part) or ())
            return _paged({**page, "level": level["level"], "object": header, "part": part}, rows, offset, limit,
                          {"kind": "object", "id": track_id, "part": part})
    raise ValueError(f"no object {track_id!r} in the library")


def library_page(model: Mapping[str, Any], kind: str, *, id: Any = None, reason: Any = None,  # noqa: A002
                 subject: Any = None, level: Any = None, part: Any = None, offset: Any = 0,
                 limit: Any = 10) -> dict[str, Any]:
    """One bounded page of the validated library; ``next`` is the exact call for the rest.

    Unknown kinds, ids, parts and levels raise ``ValueError``. Every response fits ``PAGE_BUDGET``.
    """
    validate(model)
    if kind not in PAGE_KINDS:
        raise ValueError(f"kind must be one of {list(PAGE_KINDS)}")
    page: dict[str, Any] = {"schema": PAGE_SCHEMA, "kind": kind, "revision": model["content_sha256"][:12]}
    if kind == "levels":
        rows = [{
            "level": item["level"], "state": item["state"], "entry": item["entry"]["source"],
            "accounting": item["accounting"], "journal_check": item["record"]["journal_check"]["status"],
            "transitions": len(item["record"]["transition_ids"]), "objects": len(item["observation"]["tracks"]),
            "roles": len(item["certified"]["roles"]), "gaps": len(item["gaps"]),
        } for item in model["levels"]]
        return _paged(page, rows, offset, limit, {"kind": "levels"})
    if kind == "evidence":
        for item in model["levels"]:
            for table in ("evidence", "products", "witnesses"):
                if str(id) in item["receipts"][table]:
                    return _paged({**page, "level": item["level"], "table": table},
                                  [item["receipts"][table][str(id)]], 0, 1, {"kind": "evidence", "id": str(id)})
        raise ValueError(f"no receipt {id!r} in the library")
    if kind == "object":
        return _object_page(model, page, str(id), part, offset, limit)
    chosen = _level(model, level)
    page["level"] = chosen["level"]
    if kind == "role":
        wanted = str(id or "")
        roles = [role for role in chosen["certified"]["roles"]
                 if role.get("entity_id") == wanted or role["role"] == wanted.upper()]
        if not roles:
            raise ValueError(f"no certified role for {wanted!r} on level {chosen['level']}")
        gaps = sum(1 for gap in chosen["gaps"] if gap.get("subject") in {wanted, wanted.upper()})
        page.update(gaps=gaps, gaps_call=_call("gaps", subject=wanted, level=chosen["level"]) if gaps else None)
        return _paged(page, roles, offset, limit, {"kind": "role", "id": wanted, "level": chosen["level"]})
    if kind == "objects":
        rows = [_object_row(chosen, track) for track in chosen["observation"]["tracks"]]
        return _paged(page, rows, offset, limit, {"kind": "objects", "level": chosen["level"]})
    wanted_reason = None if reason is None else str(reason).upper()
    rows = [gap for gap in chosen["gaps"] if (wanted_reason is None or gap["reason"] == wanted_reason)
            and (subject is None or str(gap.get("subject")) in {str(subject), str(subject).upper()})]
    return _paged(page, rows, offset, limit,
                  {"kind": "gaps", "reason": wanted_reason, "subject": subject, "level": chosen["level"]})


__all__ = ["DIGEST_BUDGET", "GOAL_QUESTIONS", "HANDLES", "HEADER", "PAGE_BUDGET", "library_digest", "library_page",
           "live_model", "render_library_digest"]

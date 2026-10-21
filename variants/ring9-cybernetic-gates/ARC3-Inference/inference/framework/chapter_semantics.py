"""Workflow settlement apart from knowledge certification for a G4 product with a closed chapter (WO-RUNTIME-01 r3).

Author: Claude (Alpha build seat), 2026-10-21. Base ``73f13d1``, on the parked revision-2 tree. Build directive
WO-RUNTIME-01 revision 3 (Sol): advancing the workflow must never make incomplete knowledge look certified.

For a G4.1 (``G4-REACTIONS``) or G4.2 (``G4.2-LEVER-ORBITS``) product holding a closed lever chapter
(``settle_payload``), recorded independently:

* ``settlement_status`` — ``SETTLED_WITH_GAPS`` once every chapter is answered or closed (the scheduler may
  advance), ``OPEN`` while one is pending; never ``COMPLETE``;
* ``knowledge_status`` — ``PARTIAL`` (some subject supported, some unresolved) or ``UNRESOLVED`` (none supported);
  ``status`` repeats it, the field every existing reader keys on (agenda, origins, census);
* ``answered_entities``, ``closed_entities``, ``pending_entities`` (and, in G4.2, ``released_entities``: levers a
  boundary released, as on the base), and the ``unresolved_lever_chapters`` rows;
* the knowledge fields hold supported facts only: in G4.1 ``anatomies`` lists the answered levers; a closed lever's
  compiled geometry moves to ``observed_geometry`` (``GATE_OBSERVED_GEOMETRY`` / ``ANATOMY_UNRESOLVED``), which
  downstream gates may route over (``region_rows``) but which never certifies an anatomy;
* ``geometry_sources``: every subject's geometry by source — ``ACCEPTED_ANSWER``, ``GATE_OBSERVED_GEOMETRY``,
  ``G3_INVENTORY_OBSERVATION`` or ``UNRESOLVED_PLACEHOLDER``;
* G4.2 never reads ``phase1_status`` ``COMPLETE`` with a chapter closed (``SETTLED_WITH_GAPS``), and a lever whose
  G4.1 chapter closed carries ``ANATOMY_UNRESOLVED`` (``anatomy_status``) wherever it is studied.

Every closure row keeps its exact ``cause`` and one epistemic ``closure_class`` with its ``revisit_policy``
(``closure_type``): a resource or interface failure is never rendered as evidence that the world's mechanics are
unresolved (``closure_text``). A product with no closure, here or upstream, is returned unchanged: byte-identical.

``payload_problems`` and ``gate_problems`` are the validator side (``world_model_v11``): a forged ``PARTIAL`` →
``CERTIFIED`` gate row, or a forged answered subject, is refused however every hash is recomputed.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

REACTIONS, ORBITS = "G4-REACTIONS", "G4.2-LEVER-ORBITS"
ROWS = "unresolved_lever_chapters"
SETTLED, OPEN = "SETTLED_WITH_GAPS", "OPEN"
PARTIAL, UNRESOLVED = "PARTIAL", "UNRESOLVED"
ACCEPTED, OBSERVED, G3_OBSERVED, PLACEHOLDER = (
    "ACCEPTED_ANSWER", "GATE_OBSERVED_GEOMETRY", "G3_INVENTORY_OBSERVATION", "UNRESOLVED_PLACEHOLDER")
SOURCES = frozenset({ACCEPTED, OBSERVED, G3_OBSERVED, PLACEHOLDER})
ANATOMY_UNRESOLVED = "ANATOMY_UNRESOLVED"

# ---- why a chapter closed --------------------------------------------------------------------------------------

CLASSES = ("RESOURCE_LIMIT", "INTERFACE_FAILURE", "EXPLICIT_DECLINE", "EVIDENCE_INCONCLUSIVE", "SUBJECT_STALE",
           "NO_LEGAL_PROBE", "UPSTREAM_UNRESOLVED")
CAUSE_CLASS = {
    # the clock class, a spent Duck budget, the turn's own size limits: resources, not the world
    "TURN_CLOCK": "RESOURCE_LIMIT", "MODEL_TIMEOUT": "RESOURCE_LIMIT", "MODEL_REQUEST_FAILED": "RESOURCE_LIMIT",
    "CONTEXT_OVERFLOW": "RESOURCE_LIMIT", "TOOL_STEP_LIMIT": "RESOURCE_LIMIT", "DUCK_BUDGET_SPENT": "RESOURCE_LIMIT",
    "CLOCK_BUDGET_SPENT": "RESOURCE_LIMIT",
    # the call or its contract failed: the interface, not the world
    "READ_ONLY_REPEAT": "INTERFACE_FAILURE", "NO_TOOL_CALL": "INTERFACE_FAILURE", "MALFORMED_ACTION": "INTERFACE_FAILURE",
    "ACTION_REFUSED": "INTERFACE_FAILURE", "PYTHON_ERROR": "INTERFACE_FAILURE",
    "CONTRACT_REPAIR_EXHAUSTED": "INTERFACE_FAILURE", "CONTROLLER_STALLED": "INTERFACE_FAILURE",
    "HARD_BUDGET_SPENT": "INTERFACE_FAILURE",
    "DECLINED": "EXPLICIT_DECLINE",
    "STALE_CHOICE": "SUBJECT_STALE",
    "SUBJECT_INADMISSIBLE": "NO_LEGAL_PROBE", "ROUTE_RETRY_EXHAUSTED": "NO_LEGAL_PROBE",
    "NO_LEGAL_CONTROLLER_MOVE": "NO_LEGAL_PROBE",
    "UPSTREAM_UNRESOLVED": "UPSTREAM_UNRESOLVED",
    "EVIDENCE_INCONCLUSIVE": "EVIDENCE_INCONCLUSIVE",
}
REVISIT = {"RESOURCE_LIMIT": "NEW_LIFE_OR_MATERIAL_EVIDENCE", "INTERFACE_FAILURE": "NEW_LIFE_OR_MATERIAL_EVIDENCE",
           "EVIDENCE_INCONCLUSIVE": "NEW_QUALIFYING_EVIDENCE", "EXPLICIT_DECLINE": "NEW_LIFE",
           "SUBJECT_STALE": "SUBJECT_REAPPEARS", "NO_LEGAL_PROBE": "NEW_LIFE_OR_MATERIAL_EVIDENCE",
           "UPSTREAM_UNRESOLVED": "UPSTREAM_RESOLVED"}
CLASS_TEXT = {
    "RESOURCE_LIMIT": "a resource ran out before the study finished; nothing is shown about the mechanics",
    "INTERFACE_FAILURE": "the study's calls failed; nothing is shown about the mechanics",
    "EXPLICIT_DECLINE": "declined; nothing is shown about the mechanics",
    "EVIDENCE_INCONCLUSIVE": "the evidence was inconclusive",
    "SUBJECT_STALE": "the subject went stale before it could be studied",
    "NO_LEGAL_PROBE": "no legal probe could study it",
    "UPSTREAM_UNRESOLVED": "an upstream chapter it needs is unresolved",
}


def closure_type(cause: str) -> dict[str, str]:
    """The row's ``cause``, ``closure_class`` and ``revisit_policy`` (an unknown cause is refused, never guessed)."""
    cause = str(cause).split(":", 1)[0].strip()  # a reason with its explanation keeps only its code
    if cause not in CAUSE_CLASS:
        raise ValueError(f"no closure class for cause {cause!r}")
    kind = CAUSE_CLASS[cause]
    return {"cause": cause, "closure_class": kind, "revisit_policy": REVISIT[kind]}


def closure_text(row: Mapping[str, Any]) -> str:
    return f"closed unresolved ({row['closure_class']}: {row['cause']}): {CLASS_TEXT[row['closure_class']]}"


def open_item(row: Mapping[str, Any]) -> dict[str, Any]:
    """The dossier chapter's typed record of its closure (an open item of kind ``CHAPTER_CLOSED``)."""
    return {"kind": "CHAPTER_CLOSED", "question_id": row["question_id"], "reason": row["reason"],
            "cause": row["cause"], "closure_class": row["closure_class"], "revisit_policy": row["revisit_policy"]}


# ---- the product ------------------------------------------------------------------------------------------------

def _entity(item: Any) -> str:
    return str((item or {}).get("entity_id") or "") if isinstance(item, Mapping) else ""


def settle_payload(gate: str, adapter: Any, payload: dict[str, Any], found: list[dict[str, Any]]) -> dict[str, Any]:
    upstream = {} if gate == REACTIONS else _upstream(adapter)
    if not found and not upstream:
        return payload  # no closure here or upstream: the base's payload, byte for byte
    out = dict(payload)
    ordered = list(adapter._ordered_entities)
    if upstream:
        out["anatomy_status"] = {entity: ANATOMY_UNRESOLVED for entity in ordered if entity in upstream}
    if not found:
        return out
    closed_ids = [row["entity_id"] for row in found]
    answered = [entity for entity in ordered if entity in adapter._answers]
    released = [] if gate == REACTIONS else [entity for entity in ordered if entity in adapter._interruptions
                                              and entity not in answered and entity not in closed_ids]
    pending = [entity for entity in ordered if entity not in answered and entity not in closed_ids
               and entity not in released] if gate == REACTIONS else list(adapter._pending())
    knowledge = PARTIAL if answered else UNRESOLVED
    out.update({"settlement_status": OPEN if pending else SETTLED, "knowledge_status": knowledge, "status": knowledge,
                "answered_entities": answered, "closed_entities": closed_ids, "pending_entities": pending, ROWS: found})
    if gate == ORBITS:
        out["released_entities"] = released
        if not pending:
            out["phase1_status"] = SETTLED  # never COMPLETE with a chapter closed; still releases the hold
    if knowledge == UNRESOLVED:
        out["unresolved_reason"] = "every settled lever chapter closed CLOSED_UNRESOLVED; nothing is supported"
    if gate == REACTIONS:
        out["anatomies"] = [item for item in payload["anatomies"] if _entity(item) in answered]
        out["observed_geometry"] = [{**item, "geometry_source": OBSERVED, "anatomy_status": ANATOMY_UNRESOLVED}
                                    for item in payload["anatomies"] if _entity(item) in closed_ids]
        out["geometry_sources"] = {entity: ACCEPTED if entity in answered else OBSERVED if entity in closed_ids
                                   else PLACEHOLDER for entity in ordered}
    return out


def _upstream(adapter: Any) -> dict[str, Any]:
    machine = getattr(adapter, "machine", None)
    product = None if machine is None else machine.target_journal.active_product(REACTIONS)
    payload = getattr(product, "payload", None)
    return {_entity(row): row for row in (payload or {}).get(ROWS) or ()} if isinstance(payload, Mapping) else {}


def region_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """What G4.2 studies and G4-B builds regions over: the supported anatomies and, for routing only, a closed
    chapter's observed geometry, in the gate's own lever order (the base's order, so scheduling is unchanged)."""
    rows = [*(payload.get("anatomies") or ()), *(payload.get("observed_geometry") or ())]
    order = {entity: index for index, entity in enumerate(payload.get("lever_entities") or ())}
    return sorted(rows, key=lambda item: order.get(_entity(item), len(order))) if payload.get("observed_geometry") else rows


def with_sources(machine: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """G4-B's product: unchanged unless an upstream G4 chapter closed; then each lever's region and orbit sources."""
    reactions = machine.target_journal.active_product(REACTIONS)
    orbits = machine.target_journal.active_product(ORBITS)
    upstream = (getattr(reactions, "payload", None) or {}).get("geometry_sources")
    orbit_rows = (getattr(orbits, "payload", None) or {}).get(ROWS)
    if not upstream and not orbit_rows:
        return payload
    answered = set((getattr(orbits, "payload", None) or {}).get("lever_entities") or ())
    levers = list(payload.get("lever_entities") or ())
    return {**payload, "region_sources": {entity: (upstream or {}).get(entity, ACCEPTED) for entity in levers},
            "orbit_sources": {entity: ACCEPTED if entity in answered else PLACEHOLDER for entity in levers}}


def prerequisites_present(machine: Any, prediction: Any, relations: Sequence[Mapping[str, Any]] = ()) -> bool:
    """G4-C: a law certifies only when every lever it acts on, explicitly names (``named``: Duck's own expectations,
    not the levers defaulted UNCHANGED), draws a relation from, or saw take part (r3.1: its region intersects the
    changed cells the test was graded on, ``observed`` other than UNCHANGED) has its G4.1 and G4.2 chapters
    supported. An unresolved participant leaves the test SUPPORTED as an observation, and the law uncertified."""
    from inference.framework.chapter_closure import closed
    from inference.framework.g4_relations import UNCHANGED

    adapters = getattr(machine, "_adapters", None) or {}
    unresolved = set()
    for gate in (REACTIONS, ORBITS):
        if gate in adapters:
            unresolved |= set(closed(adapters[gate]))
    if not unresolved:
        return True
    drawn = [relations[index] for index in getattr(prediction, "from_relations", ()) or () if 0 <= index < len(relations)]
    observed = getattr(prediction, "observed", None) or {}
    involved = {getattr(prediction, "acted_lever", None), *(getattr(prediction, "named", None) or ()),
                *(lever for item in drawn for lever in item.get("levers") or ()),
                *(lever for lever, seen in observed.items() if seen != UNCHANGED)}
    return not (involved & unresolved)


# ---- the census and the validator --------------------------------------------------------------------------------

def gate_row(payload: Any, disposition: str) -> dict[str, Any]:
    """The census gate row's fields: for a product with closed chapters, workflow and knowledge apart."""
    if not isinstance(payload, Mapping) or not payload.get(ROWS):
        return {"disposition": disposition}
    return {"disposition": disposition, "settlement_status": payload["settlement_status"],
            "knowledge_status": payload["knowledge_status"],
            "subjects": {"answered": len(payload["answered_entities"]), "closed": len(payload["closed_entities"]),
                         "pending": len(payload["pending_entities"])}}


def gate_label(row: Mapping[str, Any]) -> str:
    """The digest's gate line: a gate with gaps reads "settled with gaps", never complete or certified."""
    if not row.get("settlement_status"):
        return f"{row['gate_id']} {row['disposition']}"
    subjects = row["subjects"]
    state = "settled with gaps" if row["settlement_status"] == SETTLED else "open with gaps"
    return (f"{row['gate_id']} {state} ({row['knowledge_status']}: {subjects['answered']} answered, "
            f"{subjects['closed']} closed unresolved, {subjects['pending']} pending)")


def settlement_note(payload: Mapping[str, Any]) -> str | None:
    """The report's note for such a product: settled with gaps, and why each gap closed."""
    if not isinstance(payload, Mapping) or not payload.get(ROWS):
        return None
    gaps = "; ".join(f"{row['entity_id']} {closure_text(row)}" for row in payload[ROWS])
    answered = ", ".join(payload["answered_entities"]) or "none"
    return f"settled with gaps ({payload['knowledge_status']}): supported {answered}; {gaps}"


ROW_KEYS = frozenset({"gate_id", "chapter", "entity_id", "question_id", "reason", "level", "life", "at_transition",
                      "recovery_event_ids", "evidence_refs", "cause", "closure_class", "revisit_policy"})


def payload_problems(gate: str, payload: Mapping[str, Any]) -> list[str]:
    """Why a G4.1 / G4.2 payload with closed chapters breaks the revision-3 contract (empty: it keeps it)."""
    found_rows = payload.get(ROWS) or []
    if not found_rows:
        return []
    out: list[str] = []
    closed_ids = [row.get("entity_id") for row in found_rows]
    for row in found_rows:
        if set(row) != ROW_KEYS or row.get("gate_id") != gate:
            out.append(f"{row.get('entity_id')}: a closure row holds exactly the declared keys of its own gate")
        elif CAUSE_CLASS.get(row["cause"]) != row["closure_class"] or REVISIT.get(row["closure_class"]) != row["revisit_policy"]:
            out.append(f"{row['entity_id']}: the closure class and revisit policy follow the cause")
    answered, pending = list(payload.get("answered_entities") or []), list(payload.get("pending_entities") or [])
    with_answer = [_entity(item) for item in payload.get("answers") or ()]
    if sorted(answered) != sorted(with_answer):
        out.append("answered_entities are exactly the levers with a supported answer")
    if sorted(payload.get("closed_entities") or []) != sorted(closed_ids):
        out.append("closed_entities are exactly the closure rows' levers")
    groups = [answered, closed_ids, pending, list(payload.get("released_entities") or [])]
    if len({entity for group in groups for entity in group}) != sum(len(group) for group in groups):
        out.append("a lever is answered, closed, pending or released, never two of these")
    knowledge = PARTIAL if answered else UNRESOLVED
    if payload.get("knowledge_status") != knowledge or payload.get("status") != knowledge:
        out.append(f"knowledge_status is {knowledge}: what the answers support, never more")
    if payload.get("settlement_status") != (OPEN if pending else SETTLED):
        out.append("settlement_status is SETTLED_WITH_GAPS exactly when nothing is pending")
    if gate == ORBITS and payload.get("phase1_status") == "COMPLETE":
        out.append("a G4.2 phase with a closed chapter is never COMPLETE")
    if gate == REACTIONS:
        if sorted(_entity(item) for item in payload.get("anatomies") or ()) != sorted(answered):
            out.append("anatomies hold the supported levers only")
        geometry = payload.get("observed_geometry") or []
        if sorted(_entity(item) for item in geometry) != sorted(closed_ids) or any(
                item.get("geometry_source") != OBSERVED or item.get("anatomy_status") != ANATOMY_UNRESOLVED
                for item in geometry):
            out.append("a closed chapter's geometry is observed geometry, ANATOMY_UNRESOLVED, never an anatomy")
        sources = payload.get("geometry_sources") or {}
        if any(sources.get(entity) != ACCEPTED for entity in answered) or any(
                sources.get(entity) == ACCEPTED for entity in closed_ids) or not set(sources.values()) <= SOURCES:
            out.append("geometry_sources name ACCEPTED_ANSWER for supported levers only")
    return out


def gate_problems(level: Mapping[str, Any]) -> list[str]:
    """A census gate row agrees with the stored product it names: a product with closed chapters is PARTIAL or
    CLOSED_UNRESOLVED (never CERTIFIED), with its own counts; a PARTIAL row names such a product."""
    content = level.get("product_content") or {}
    out: list[str] = []
    for row in (level.get("certified") or {}).get("gates") or ():
        entry = content.get(row.get("product_id")) if row.get("product_id") else None
        payload = (entry or {}).get("payload") if isinstance(entry, Mapping) else None
        gated = isinstance(payload, Mapping) and bool(payload.get(ROWS))
        where = f"level {level.get('level')}: {row.get('gate_id')}"
        if gated:
            expected = PARTIAL if payload.get("knowledge_status") == PARTIAL else "CLOSED_UNRESOLVED"
            extras = gate_row(payload, expected)
            if {key: row.get(key) for key in extras} != extras:
                out.append(f"{where} is {row.get('disposition')}; its product has closed chapters, so it is "
                           f"{expected} with its own counts, never certified")
            out.extend(f"{where}: {problem}" for problem in payload_problems(row.get("gate_id"), payload))
        elif row.get("disposition") == PARTIAL or row.get("settlement_status"):
            out.append(f"{where} is {row.get('disposition')} but its product holds no closed chapter")
    return out


__all__ = ["ACCEPTED", "ANATOMY_UNRESOLVED", "CAUSE_CLASS", "CLASSES", "OBSERVED", "PARTIAL", "REVISIT", "ROWS",
           "SETTLED", "SOURCES", "UNRESOLVED", "closure_text", "closure_type", "gate_label", "gate_problems",
           "gate_row", "open_item", "payload_problems", "prerequisites_present", "region_rows", "settle_payload",
           "settlement_note", "with_sources"]

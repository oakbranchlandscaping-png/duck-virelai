"""Injected recall: the controller puts what memory knows about the current subject on the card.

Author: Claude (Alpha build seat), 2026-09-29. R9-R09 (DESIGN_VIRELAI_MEMORY_v2 §5.4, law M6).

The key is structural, never a similarity search: the current step's subject entity, its click
site, and the gate. Facts come from ``MemoryStore`` only, in the design's priority order:

1. open contradictions about the subject;
2. certified product lines about it;
3. its prior outcomes, most recent first;
4. prior outcomes at the same click site;
5. scoped nulls about it;

then Duck's UNCERTIFIED notes about it, labelled. The slot is filled to its budget and ends with a
remainder line and a pull handle. If nothing is known, it says so in one line: that tells Duck
the subject is unexplored.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from inference.framework.memory_store import MemoryStore

RECALL_BUDGET = 2_000
CONTRADICTED_STATES = {"AMBIGUOUS", "REOPENED", "BUDGET_STOPPED"}
UNEXPLORED = "nothing recorded about this subject yet: unexplored"


def _chars(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str))


def recall_key(gate_id: str, view: Mapping[str, Any], capability: Mapping[str, Any] | None) -> dict[str, Any]:
    """The current step's subject: entity, click site, gate."""
    entity, site = None, None
    target = (capability or {}).get("target") if isinstance(capability, Mapping) else None
    actions = list((capability or {}).get("actions") or ()) if isinstance(capability, Mapping) else []
    if isinstance(target, Mapping) and target.get("entity_id"):
        entity = str(target["entity_id"])
    pending = (view.get("scheduler") or {}).get("pending_dossier") if isinstance(view.get("scheduler"), Mapping) else None
    if isinstance(pending, Mapping) and pending.get("entity_id"):
        entity, actions = str(pending["entity_id"]), [pending.get("intervention") or {}]
    lever = view.get("current_lever")
    if isinstance(lever, Mapping) and lever.get("entity_id"):
        entity = str(lever["entity_id"])
        actions = [lever.get("intervention") or {}]
    levers = (target or {}).get("levers") if isinstance(target, Mapping) else None
    if isinstance(levers, (list, tuple)):
        active = [item for item in levers if isinstance(item, Mapping) and item.get("status") in {"RUNNING", "CONFIRMING", "NOT_STARTED"}]
        if active:
            entity, actions = str(active[0].get("entity_id")), [active[0].get("click") or {}]
    template = view.get("answer_template")
    if isinstance(template, Mapping) and template.get("entity_id"):  # the subject Duck must explain
        entity, actions = str(template["entity_id"]), [template.get("intervention") or {}]
    if actions and isinstance(actions[0], Mapping) and "row" in actions[0] and "col" in actions[0]:
        site = [int(actions[0]["row"]), int(actions[0]["col"])]
    return {"gate": gate_id, "entity": entity, "site": site}


def _certified_lines(machine: Any, entity: str) -> list[str]:
    lines: list[str] = []
    for row in machine.completed_gate_rows():
        payload = row["answer"]
        if row["gate_id"] == "G3-LEVERS" and entity in (payload.get("lever_entities") or ()):
            lines.append(f"[{row['gate_id']}] {entity} is a certified lever")
        if entity in (payload.get("clean_null_entities") or ()):
            lines.append(f"[{row['gate_id']}] {entity} closed with scoped null evidence")
        for anatomy in payload.get("anatomies") or ():
            if anatomy.get("entity_id") == entity:
                channels = "; ".join(
                    f"{ch.get('locality')} {ch.get('transform')} {ch.get('changed_cell_count')} cells"
                    for ch in anatomy.get("channels") or ()
                )
                lines.append(f"[{row['gate_id']}] {entity} anatomy: {channels}")
        klass = (payload.get("lever_classes") or {}).get(entity)
        if klass:
            lines.append(f"[{row['gate_id']}] {entity} orbit class {klass}")
    return lines


def _scoped_null(subject: Mapping[str, Any]) -> bool:
    """Closed or waiting on null evidence only: never witnessed, never responded."""
    reached = {event.get("to_state") for event in subject.get("lifecycle_events") or ()}
    return subject.get("lifecycle_state") in {"NO_RESPONSE_YET", "G3-CLOSED"} and not reached & {
        "RESPONDED", "WITNESSED",
    }


def _outcome_line(row: Mapping[str, Any]) -> dict[str, Any]:
    """A recalled transition, compact: the full row is one pull away (``kind='transition'``)."""
    line = {
        "transition_id": row.get("transition_id"), "gate_id": row.get("gate_id"),
        "evidence_id": row.get("evidence_id"), "changed_cells": row.get("changed_cell_count"),
    }
    if row.get("disposition"):
        line["disposition"] = row["disposition"]
    if row.get("boundary_state") not in (None, "NOT_FINISHED"):
        line["boundary_state"] = row["boundary_state"]
    return line


def _facts(machine: Any, key: Mapping[str, Any]) -> list[tuple[str, Any]]:
    store = MemoryStore(machine)
    entity, site = key.get("entity"), key.get("site")
    subject = store.subject(entity) if entity else None
    facts: list[tuple[str, Any]] = []
    if subject is not None:
        state = subject.get("lifecycle_state")
        contradicted = [c for c in subject.get("confirmations") or () if c.get("status") == "CONTRADICTED"]
        if state in CONTRADICTED_STATES or contradicted:
            facts.append(("open_contradiction", {"lifecycle_state": state, "contradicted_confirmations": len(contradicted)}))
    if entity:
        facts.extend(("certified", line) for line in _certified_lines(machine, entity))
    seen: set[Any] = set()
    if subject is not None:
        for row in subject["aimed_transitions"]["rows"]:
            seen.add(row.get("transition_id"))
            facts.append(("outcome", _outcome_line(row)))
    if site is not None:
        for row in store.site(site[0], site[1], limit=20)["rows"]:
            if row.get("transition_id") not in seen:
                facts.append(("site_outcome", _outcome_line(row)))
    if subject is not None and _scoped_null(subject):
        facts.append(("scoped_null", {"lifecycle_state": subject["lifecycle_state"]}))
    lane = getattr(machine, "annotations", None)
    for note in (lane.about(entity) if lane is not None and entity else []):
        facts.append(("uncertified_note", note.line()))
    return facts


def recall_slot(machine: Any, key: Mapping[str, Any], budget: int = RECALL_BUDGET) -> dict[str, Any] | None:
    """The S6 recall slot: facts about the key, in priority order, to budget.

    A step with no subject and no site (the metadata gates, G2's open search) has nothing to key
    recall on, so the slot is absent rather than noise.
    """
    if not key.get("entity") and key.get("site") is None:
        return None
    facts = _facts(machine, key)
    slot: dict[str, Any] = {"key": {name: value for name, value in key.items() if value is not None}}
    if not facts:
        slot["known"] = UNEXPLORED
        return slot
    shown: list[dict[str, Any]] = []
    for kind, value in facts:
        if _chars({**slot, "facts": [*shown, {kind: value}]}) > budget - 160:
            break
        shown.append({kind: value})
    slot["facts"] = shown
    if len(shown) < len(facts):
        entity = key.get("entity")
        slot["remaining"] = len(facts) - len(shown)
        slot["pull"] = (
            f"virelai('memory', kind='subject', id={entity!r})" if entity
            else f"virelai('memory', kind='site', row={key['site'][0]}, col={key['site'][1]})"
        )
    return slot


__all__ = ["RECALL_BUDGET", "UNEXPLORED", "recall_key", "recall_slot"]

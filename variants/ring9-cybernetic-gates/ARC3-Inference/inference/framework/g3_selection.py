"""G3's gate-owned eligibility read and an admitted choice (WO-G3-DIRECTED, CLICK slice).

Author: Claude (Alpha build seat), 2026-10-11. Design: INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET v2 §1.2 (Sol's
decisions D1–D3). Functions over the G3 adapter (``_LeverTarget``), kept beside it the way ``mu_return`` and
``g3_inheritance`` are, so the gate class does not grow (the ratchet):

- ``obligation`` and ``admission_candidates`` are **pure reads**: the work G3 owes before any choice, and the rows
  its scheduler serves, coverage head first. They never call ``_ensure_*`` or ``next_probe``; read them after the
  gate's own state-advancing call of the step (the controller and the card call ``next_probe_capability`` first).
- ``select`` admits a choice among the selectable CLICK rows; the next capability binds it. A refusal is recorded
  once and raised as a ``GateContractError``; there is no repair loop.
- ``selected_click_probe`` serves a valid admitted choice, the head included, with an identity-based probe id (D2;
  Sol's review, finding 2); the no-choice coverage path keeps its ids and envelopes. ``finish_target`` replaces the
  cursor advance: a finished off-head choice leaves the coverage cursor where it was. ``advance_past_chosen_rows`` keeps the sweep from serving that row again.
- ``choice_handoff_due`` / ``note_choice_handoff``: at most one bounded Duck handoff per G3 phase per level (D3).

NAV rows are listed for the agenda and served in coverage order; NAV selection is the next slice.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

SELECTABLE_STATES = frozenset({"UNTOUCHED", "REOPENED"})
IN_FLIGHT_STATES = SELECTABLE_STATES | {"ATTEMPTED"}


def obligation(g3: Any) -> dict[str, Any] | None:
    """The work G3 owes before any choice: a confirmation, dossier, reachability answer or revisit (read-only)."""
    if g3._pending_confirmation is not None:
        return {"kind": "CONFIRMATION", "entity_id": str(g3._pending_confirmation.get("entity_id") or "")}
    if g3._pending_dossier is not None:
        return {"kind": "DOSSIER", "entity_id": str(g3._pending_dossier.get("entity_id") or "")}
    if g3._pending_reachability is not None:
        return {"kind": "REACHABILITY", "entity_id": str(g3._pending_reachability.get("target_entity_id") or "")}
    if g3._mu_revisit and (g3._phase == "CLICK" or g3._world_type == "HYBRID"):
        return {"kind": "MU_REVISIT", "entity_id": str(g3._mu_revisit[0])}
    if g3._reopened_reachability_indices and g3._eligible_frontier and g3.entity_ledger is not None:
        row = g3._eligible_frontier[min(g3._reopened_reachability_indices)]
        return {"kind": "REOPENED_REACHABILITY",
                "entity_id": str(g3.entity_ledger.member_to_entity.get(row["member_id"]) or "")}
    return None


def admission_candidates(g3: Any) -> tuple[dict[str, Any], ...]:
    """The rows the scheduler serves, coverage head first; empty while an obligation holds (read-only)."""
    ledger, journal, frontier = g3.entity_ledger, g3.lifecycle_journal, g3._eligible_frontier
    if ledger is None or journal is None or frontier is None or obligation(g3) is not None:
        return ()
    inherited = set(g3._inheritance.nulls) if g3._inheritance is not None else set()
    rows: list[dict[str, Any]] = []
    for position in range(g3._target_index, len(frontier)):
        member = str(frontier[position]["member_id"])
        entity = ledger.member_to_entity.get(member)
        head = position == g3._target_index
        if not entity or (not head and member in g3._chosen_members):
            continue
        if not head and g3._phase == "NAV" and (entity in g3._terrain_roles or g3._g3_settled(entity)):
            continue
        state = journal.entities[entity].state if entity in journal.entities else None
        hypothesis = ledger.entities.get(entity)
        rows.append({
            "entity_id": entity, "member_id": member, "position": position, "phase": g3._phase,
            "coverage_rank": len(rows) + 1, "head": head,
            "selectable": g3._phase == "CLICK" and (head or (state in SELECTABLE_STATES and member not in inherited)),
            "entity_version": None if hypothesis is None else hypothesis.version,
            "obligation": "BODY_CONTACT_OWED" if g3._phase == "NAV" and state == "NO_RESPONSE_YET" else "FIRST_CONTACT",
        })
    return tuple(rows)


def note(g3: Any, event: str, selection: Mapping[str, Any], reason: str) -> None:
    """Record a selection event on the level's G3 adapter and in the game-long log the run writes to disk."""
    row = {
        "schema": "virelai-g3-selection-event-v1", "event": event, "question_id": selection.get("question_id"),
        "entity_id": selection.get("entity_id"), "actor": selection.get("actor"), "reason": reason,
        "phase": g3._phase, "level": int(g3.machine.lives.level), "life": int(g3.machine.lives.life),
        "at_transition": g3.machine.observed_through_step, "gate_revision": g3.revision,
    }
    g3._selection_events.append(row)
    g3.machine.g3_selection_events.append(row)


def select(g3: Any, question_id: str, *, actor: str) -> dict[str, Any]:
    """Admit a choice among the selectable rows; every earlier token goes stale. A refusal is recorded once."""
    from inference.framework.library_agenda import lever_question_id
    from inference.framework.virelai_gates import GateContractError

    request = {"question_id": question_id, "actor": actor}
    owed = obligation(g3)
    level = int(g3.machine.lives.level)
    row = None
    if owed is not None:
        reason = f"the gate owes its {owed['kind'].lower()} obligation first"
    else:
        row = next((item for item in admission_candidates(g3)
                    if lever_question_id(level, item["entity_id"]) == question_id), None)
        reason = ("the question names no row this G3 roster serves now" if row is None
                  else None if row["selectable"] else f"a {g3._phase} row is not selectable in this slice")
    if reason is not None:
        note(g3, "REFUSED", request, reason)
        raise GateContractError(f"G3 choice not admissible: {reason}.")
    selection = {**request, "entity_id": row["entity_id"], "member_id": row["member_id"], "position": row["position"],
                 "entity_version": row["entity_version"], "phase": g3._phase, "level": level,
                 "life": int(g3.machine.lives.life), "is_head": row["head"], "selected_at_revision": g3.revision + 1}
    g3._selection = selection
    g3.revision += 1
    note(g3, "ADMITTED", selection, "head" if row["head"] else "away from the coverage head")
    return dict(selection)


def _stale(g3: Any, selection: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> str | None:
    hypothesis = None if g3.entity_ledger is None else g3.entity_ledger.entities.get(selection["entity_id"])
    item = None if g3.lifecycle_journal is None else g3.lifecycle_journal.entities.get(selection["entity_id"])
    position = int(selection["position"])
    if g3._phase != selection["phase"] or int(g3.machine.lives.level) != selection["level"]:
        return "the phase or level changed"
    if int(g3.machine.lives.life) != selection["life"]:
        return "a new life began"
    if hypothesis is None or hypothesis.version != selection["entity_version"]:
        return "the chosen object changed"
    if position >= len(candidates) or str(candidates[position]["member_id"]) != selection["member_id"]:
        return "the roster changed"
    if not selection["is_head"] and getattr(item, "state", None) not in IN_FLIGHT_STATES:
        return "the chosen row is already settled"
    return None


def selected_click_probe(g3: Any, candidates: Sequence[Mapping[str, Any]]) -> Any | None:
    """The bound probe of an admitted CLICK choice, head or not, or None (no choice, or a stale one)."""
    from inference.framework.virelai_gates import LEVER_GATE_ID

    selection = g3._selection
    if selection is None:
        return None
    stale = _stale(g3, selection, candidates)
    if stale is not None:
        note(g3, "STALE", selection, stale)
        g3._selection = None
        return None
    position = int(selection["position"])
    target = g3._probe_target(candidates[position], position)
    target["question_id"] = selection["question_id"]
    target["selected_by"] = selection["actor"]
    probe_id = (f"{LEVER_GATE_ID}:CLICK:SEL:{selection['member_id']}:L{selection['level']}"
                f"P{selection['life']}:R{selection['selected_at_revision']}")
    return g3._click_probe(probe_id, target)


def advance_past_chosen_rows(g3: Any, candidates: Sequence[Mapping[str, Any]]) -> None:
    """The coverage sweep does not serve again a row a choice already finished (a no-op with no choice)."""
    while (g3._phase == "CLICK" and g3._target_index < len(candidates)
           and str(candidates[g3._target_index]["member_id"]) in g3._chosen_members):
        g3._target_index += 1


def finish_target(g3: Any, member_id: str | None) -> None:
    """A target's G3 work is done. A finished off-head choice leaves the coverage cursor where it was."""
    selection = g3._selection
    if selection is not None and str(member_id or "") == selection["member_id"]:
        g3._selection = None
        note(g3, "FINISHED", selection, "the chosen row's G3 work is done")
        if not selection["is_head"]:
            g3._chosen_members.add(selection["member_id"])
            return
    g3._target_index += 1


def choice_handoff_due(g3: Any) -> bool:
    """Sol, 2026-10-11 (D3): one bounded Duck handoff per G3 phase per level, only for a genuine choice."""
    if g3._phase in g3._choice_handoffs or g3._selection is not None:
        return False
    return sum(1 for row in admission_candidates(g3) if row["selectable"]) >= 2


def note_choice_handoff(g3: Any) -> None:
    g3._choice_handoffs.add(g3._phase)
    note(g3, "HANDOFF", {"actor": "CONTROLLER"}, "a genuine G3 choice was offered to Duck")


def note_coverage_resumed(g3: Any) -> None:
    """After a handoff that produced no choice (a timeout or a turn without one), the controller resumes the
    coverage head; recorded once per phase so a rehearsal can count declined handoffs."""
    phase_events = [row["event"] for row in g3._selection_events if row["phase"] == g3._phase]
    if g3._selection is None and phase_events and phase_events[-1] == "HANDOFF":
        note(g3, "COVERAGE_RESUMED", {"actor": "CONTROLLER"}, "no choice was admitted after the handoff")


__all__ = ["admission_candidates", "advance_past_chosen_rows", "choice_handoff_due", "finish_target",
           "note_choice_handoff", "note_coverage_resumed", "obligation", "select", "selected_click_probe"]

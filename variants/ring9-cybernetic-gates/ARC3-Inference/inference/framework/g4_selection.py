"""G4's gate-owned admission of a per-lever choice: library-selected study (WO-G4-DOSSIER-B, slice B2).

Author: Claude (Alpha build seat), 2026-10-18. Design: ``INTERFACE_WO_G4_DOSSIER_B2_v1`` under Sol's rulings 5-7
on ``INTERFACE_WO_G4_DOSSIER_B_v1``; ported from ``g3_selection`` (WO-G3-DIRECTED), kept beside the adapters so the
gate classes grow only by delegation lines (ruling 6, the ratchet).

Two G4 gates serve levers one at a time, and their per-lever chapter is the agenda's selected question:

* **G4.1** (``G4-REACTIONS``): each lever's effect anatomy. It is deterministic controller work with no Duck probe
  turn, so it admits no choice (revision 2, Sol's review): its candidates are listed, head first, none selectable;
* **G4-A** (``G4.2-LEVER-ORBITS``): which lever's run the controller presses next — the only live G4 choice.

G4-B and G4-C are level-scoped: Duck's frozen prediction is already their admitted choice, and their selected
question stays the gate's.

The reads (``obligation``, ``admission_candidates``, ``selected_question``, ``chosen``) are pure: they never call
``_seed``, ``next_probe`` or ``_ensure_*``. Writes happen only in ``select`` and in ``settle``, which G4-A calls from
its own state-advancing step (``next_probe``).

The question a dossier chapter answers is never stored. Revision 3 (Sol's review): the saved model's chain — admitted
question, selected-run receipts, completed chapter — is checked by the v8 validator (``lever_dossier_selection``),
from the persisted audit rows and receipts; nothing here is a test-only checker.

Priority (ruling 7, "obligations first"): an open run owes its endpoint (no choice is admitted meanwhile); a
confirmed run owes Duck's explanation; Duck's own rerun request; then the choice; then coverage. Duck chooses only on
a turn it already holds: there is no handoff turn. A decline or timeout leaves nothing bound, so coverage goes on
unchanged; a stale choice and a finished one end with a recorded event, and coverage resumes where it was.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Sequence

SCHEMA = "virelai-g4-selection-event-v1"
REACTIONS, ORBITS = "G4-REACTIONS", "G4.2-LEVER-ORBITS"
CHAPTERS = {REACTIONS: "EFFECTS", ORBITS: "ORBIT"}
ADMITTING = frozenset({ORBITS})  # revision 2: G4.1 is controller work; G4-A alone admits Duck's choice
STUDY_ORDER = ("RUNNING", "CONFIRMING", "RUN_ENDED_RESTART_NEEDED", "NOT_STARTED")  # the controller's order
IN_FLIGHT = frozenset({"RUNNING", "CONFIRMING"})
OFF_HEAD = frozenset({"NOT_STARTED", "RUN_ENDED_RESTART_NEEDED"})
RESTUDY = "INTERRUPTED_RELEASED"  # "Duck may re-study it on this level" (the G4-A card)


def _question(level: int, gate: str, entity_id: str) -> str:
    from inference.framework.library_agenda import question_id

    return question_id(level, gate, entity_id, CHAPTERS[gate])


def _adapter(machine: Any) -> Any | None:
    gate = machine.gate_id
    return machine._adapters[gate] if gate in CHAPTERS else None


# ---- pure reads ---------------------------------------------------------------------------------------------------

def obligation(machine: Any) -> dict[str, Any] | None:
    """The work G4 owes before any choice: a G4-A run under way owes its endpoint (read-only)."""
    if machine.gate_id != ORBITS:
        return None
    run = machine._adapters[ORBITS]._active_run
    if run is not None and run.status in IN_FLIGHT:
        return {"kind": "RUN_ENDPOINT", "entity_id": str(run.entity_id)}
    return None


def _orbit_rows(adapter: Any) -> list[tuple[str, str, bool, bool]]:
    """(entity, status, head, selectable) in the controller's own order: STUDY_ORDER, then the re-studiable."""
    if adapter._level_closed is not None:
        return []
    status = {entity: adapter._lever_status(entity) for entity in adapter._ordered_entities}
    coverage = [entity for state in STUDY_ORDER for entity in adapter._ordered_entities if status[entity] == state]
    restudy = [entity for entity in adapter._ordered_entities if status[entity] == RESTUDY and adapter._studying()]
    return [(entity, status[entity], index == 0, index == 0 or status[entity] in OFF_HEAD or entity in restudy)
            for index, entity in enumerate(coverage + restudy)]


def admission_candidates(machine: Any) -> tuple[dict[str, Any], ...]:
    """The levers the gate serves, coverage head first; empty while an obligation holds (read-only)."""
    adapter = _adapter(machine)
    if adapter is None or obligation(machine) is not None:
        return ()
    level, gate = int(machine.lives.level), machine.gate_id
    if gate == REACTIONS:  # listed for the agenda, head first; never Duck's to choose
        pending = [entity for entity in adapter._ordered_entities if entity not in adapter._answers]
        rows = [(entity, "UNANSWERED", index == 0, False) for index, entity in enumerate(pending)]
    else:
        rows = _orbit_rows(adapter)
    return tuple({"entity_id": entity, "question_id": _question(level, gate, entity), "gate_id": gate,
                  "chapter": CHAPTERS[gate], "status": status, "coverage_rank": index + 1, "head": head,
                  "selectable": selectable}
                 for index, (entity, status, head, selectable) in enumerate(rows))


def _ended(adapter: Any, selection: Mapping[str, Any]) -> tuple[str, str] | None:
    """Why a bound choice is over — (``FINISHED`` | ``STALE``, reason) — or None while it still stands."""
    machine = adapter.machine if hasattr(adapter, "machine") else None
    lives = machine.lives if machine is not None else None
    if lives is not None and (int(lives.level), int(lives.life)) != (selection["level"], selection["life"]):
        return "STALE", "a new life or level began"
    entity = selection["entity_id"]
    if adapter._level_closed is not None:
        return "STALE", "the level closed this G4-A study"
    if entity in adapter._completed or entity in adapter._answers:
        return "FINISHED", "the chosen lever's run reached its endpoint"
    runs = adapter._runs.get(entity, [])
    if len(runs) > int(selection["runs_at_admission"]) and not runs[-1].open:
        return "STALE", "the chosen run ended before its endpoint"
    if adapter._lever_status(entity) == RESTUDY and selection["admitted_status"] != RESTUDY:
        return "STALE", "a boundary released the chosen lever"
    return None


def chosen(machine: Any) -> dict[str, Any] | None:
    """The bound choice of the active G4 gate while it still stands, else None (read-only)."""
    adapter = _adapter(machine)
    selection = None if adapter is None else getattr(adapter, "_g4_selection", None)
    if selection is None or _ended(adapter, selection) is not None:
        return None
    return selection


def selected_question(machine: Any) -> str | None:
    """The agenda's selection in G4.1 and G4-A: the obligation's lever, the confirmed run Duck owes an explanation,
    a standing choice, else the coverage head (the earliest incomplete actionable chapter, ruling 5)."""
    adapter = _adapter(machine)
    if adapter is None:
        return None
    level, gate = int(machine.lives.level), machine.gate_id
    owed = obligation(machine)
    if owed is not None:
        return _question(level, gate, owed["entity_id"])
    awaiting = adapter._awaiting_answer() if gate == ORBITS else ()
    if awaiting:
        return _question(level, gate, awaiting[0])
    selection = chosen(machine)
    if selection is not None:
        return str(selection["question_id"])
    head = next((row for row in admission_candidates(machine) if row["head"]), None)
    return None if head is None else str(head["question_id"])


# ---- the admitted choice and its events ----------------------------------------------------------------------------

CLOSING = frozenset({"STALE", "FINISHED"})


def note(machine: Any, event: str, selection: Mapping[str, Any], reason: str, adapter: Any = None) -> None:
    """Record a selection event in the game-long log the run writes to disk (and the audit journal translates).

    Revision 4 (Sol): a closing event (``STALE``, ``FINISHED``) describes the choice it closes, so its level, life
    and gate are the admission's — even when a death or a level change closed it; ``at_transition`` is when it
    closed. ``ADMITTED`` and ``REFUSED`` are scoped where the machine is now."""
    adapter = adapter if adapter is not None else _adapter(machine)
    closing = event in CLOSING
    machine.g4_selection_events.append({
        "schema": SCHEMA, "event": event, "question_id": selection.get("question_id"),
        "entity_id": selection.get("entity_id"), "actor": selection.get("actor"), "reason": reason,
        "gate_id": selection.get("gate_id") or machine.gate_id,
        "level": int(selection["level"] if closing else machine.lives.level),
        "life": int(selection["life"] if closing else machine.lives.life), "at_transition": machine.observed_through_step,
        "gate_revision": None if adapter is None else adapter.revision,
    })


def _refusal(machine: Any, question_id: str) -> tuple[str | None, dict[str, Any] | None]:
    if machine.gate_id == REACTIONS:
        return ("G4.1 anatomy is controller work: the controller answers each lever in coverage order, and no Duck "
                "choice is admitted"), None
    if machine.gate_id not in ADMITTING:
        return f"the active gate is {machine.gate_id}; only G4-A admits a lever choice", None
    owed = obligation(machine)
    if owed is not None:
        return f"the run of {owed['entity_id']} under way owes its run endpoint first", None
    row = next((item for item in admission_candidates(machine) if item["question_id"] == question_id), None)
    if row is None:
        return "the question names no lever this G4 gate serves now", None
    if not row["selectable"]:
        return f"this lever ({row['status']}) is not admissible away from the coverage head now", None
    return None, row


def select(machine: Any, question_id: str, *, actor: str) -> dict[str, Any]:
    """Admit a choice among the gate's candidates; a refusal is recorded once and raised (no repair loop)."""
    from inference.framework.virelai_gates import GateContractError

    if str(question_id).endswith(":LIMITS"):  # B3: a lever's limits question is G4-B's bounded experiment
        from inference.framework import lever_experiments

        return lever_experiments.select(machine, question_id, actor=actor)
    request = {"question_id": question_id, "actor": actor, "gate_id": machine.gate_id}
    reason, row = _refusal(machine, question_id)
    if reason is not None or row is None:
        note(machine, "REFUSED", request, str(reason))
        raise GateContractError(f"G4 choice not admissible: {reason}.")
    adapter = _adapter(machine)
    standing = getattr(adapter, "_g4_selection", None)
    if standing is not None:  # revision 3: one open choice per gate; the replaced one ends on the record
        adapter._g4_selection = None
        note(machine, "STALE", standing, "a new choice replaced it before its run began", adapter)
    entity = row["entity_id"]
    selection = {**request, "entity_id": entity, "chapter": row["chapter"], "level": int(machine.lives.level),
                 "life": int(machine.lives.life), "is_head": row["head"], "admitted_status": row["status"],
                 "runs_at_admission": len(getattr(adapter, "_runs", {}).get(entity, ())),
                 "admission": 1 + sum(1 for item in machine.g4_selection_events if item["event"] == "ADMITTED")}
    adapter._g4_selection = selection
    note(machine, "ADMITTED", selection, "head" if row["head"] else "away from the coverage head")
    return dict(selection)


def settle(adapter: Any) -> None:
    """End a bound choice that finished or went stale (the gate's own state-advancing call); coverage resumes."""
    selection = getattr(adapter, "_g4_selection", None)
    ended = None if selection is None else _ended(adapter, selection)
    if ended is None:
        return
    adapter._g4_selection = None
    note(adapter.machine, ended[0], selection, ended[1], adapter)


def close_at_level_change(adapter: Any) -> None:
    """Revision 4: the level's G4-A study ends with its level; a choice still open there ends on the record —
    ``FINISHED`` if its run reached its endpoint, else ``STALE`` — scoped to the choice, never left open."""
    settle(adapter)
    selection = getattr(adapter, "_g4_selection", None)
    if selection is not None:
        adapter._g4_selection = None
        note(adapter.machine, "STALE", selection, "the level changed", adapter)


# ---- binding: the probe, the controller's step and the receipt -----------------------------------------------------

def bound_probe(adapter: Any, probe: Any) -> Any:
    """G4-A: while a choice stands, the guided envelope names it, with an identity-based probe id (G3's finding 2);
    with none, the envelope is exactly the coverage one."""
    selection = chosen(adapter.machine) if probe is not None else None
    if selection is None:
        return probe
    probe_id = (f"{ORBITS}:GUIDED:SEL:{selection['entity_id']}:L{selection['level']}P{selection['life']}"
                f":R{selection['admission']}:{adapter._action_count + 1}")
    target = {**dict(probe.target or {}), "question_id": selection["question_id"], "selected_by": selection["actor"],
              "selected_entity": selection["entity_id"]}
    return replace(probe, probe_id=probe_id, target=target)


SELECTION_KEYS = ("question_id", "selected_by", "selected_entity")


def admitted_action(adapter: Any, probe: Any) -> Any:
    """Revision 4: a bound envelope stays bound only for an action on the chosen lever — its listed click, or a NAV
    step whose intent names it. Any other admitted action (Duck pressing another lever, a rerun, a non-lever action)
    is recorded as ordinary coverage: the coverage probe id, no selection keys, so no receipt names a choice it did not
    serve."""
    target = dict(getattr(probe, "target", None) or {})
    entity = target.get("selected_entity")
    if getattr(probe, "gate_id", None) != ORBITS or entity is None:
        return probe
    intent = str(getattr(probe, "intent", None) or "")
    parts = intent.split(":", 2)
    lever = parts[2] if intent.startswith("NAV:") and len(parts) == 3 else (
        adapter._lever_for_action(probe.actions[0]) if probe.actions else None)
    if lever == entity:
        return probe
    coverage = f"{ORBITS}:GUIDED:{str(probe.probe_id).rsplit(':', 1)[1]}"
    return replace(probe, probe_id=coverage, target={k: v for k, v in target.items() if k not in SELECTION_KEYS})


def receipt(probe: Any) -> dict[str, Any]:
    """The question a recorded G4-A event answers to: present only for a bound probe."""
    target = getattr(probe, "target", None) or {}
    return {"question_id": target["question_id"]} if target.get("question_id") else {}


def controller_lever(machine: Any, levers: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The capability row of the chosen lever when the controller may run it now: no run under way, and the choice
    stands. Duck's explanation and rerun are served before this is asked."""
    selection = chosen(machine)
    if selection is None or any(item.get("status") in IN_FLIGHT for item in levers):
        return None
    return next((item for item in levers if item.get("entity_id") == selection["entity_id"]), None)


__all__ = ["ADMITTING", "CHAPTERS", "SCHEMA", "admission_candidates", "bound_probe", "chosen", "controller_lever",
           "admitted_action", "close_at_level_change", "note", "obligation", "receipt", "select", "selected_question", "settle"]

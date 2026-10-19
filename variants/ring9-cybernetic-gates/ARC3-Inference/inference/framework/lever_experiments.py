"""G4-B's bounded limits experiments: what a lever's dossier still owes, tested one action at a time (WO-G4-DOSSIER-B3).

Author: Claude (Alpha build seat), 2026-10-18. Interface: ``INTERFACE_WO_G4_DOSSIER_B3_v1``. Kept beside
``g4_selection`` so the gate and the controller grow only by delegation lines.

The loop: a lever's B1 observations owe a limits item (``LIMITS_PERSISTENCE``, ``LIMITS_REVERSAL``) in this level
and life → G4-B admits one bounded experiment → Duck may choose among the admitted ones on a turn it already holds →
otherwise the controller takes the head of coverage → each step is an ordinary G4-B probe, transition and receipt →
B1 derives the dossier from the record. The experiment's own verdict is the gate's account of its run; the dossier
never reads it. The record decides what the dossier can claim.

Two kinds, one subject each:

* ``SELF_REVERSAL`` — the lever's own press, repeated until its region returns to a state seen earlier in this level
  and life (a two-state return: ``REVERSAL_OBSERVED``; a longer cycle: ``RECURRENCE_OBSERVED``, which is not
  reversal), or until the cap (``CAPPED``: reversal stays owed);
* ``PERSISTENCE_TRIAL`` — one press of the first other lever while the subject's region is watched:
  ``PERSISTENCE_UNCHANGED``, ``PERSISTENCE_CHANGED``, or ``PERSISTENCE_INCONCLUSIVE`` when the acting lever's own
  region did not respond (nothing was done to test against). One trial is an observation, never a law.

A death, a level change, a stale subject, a broken chain (a step's before-board is not the last observed state, the
retired G4.3 study's continuity check) or the gate closing ends an experiment with a typed ``STALE``. A closed
experiment is not admitted again in its level and life; a new life plans afresh and inherits nothing.

The plan is B1's own reading (``lever_dossier_state.observe`` and ``derive``), computed only at an admission point
(the controller's idle G4-B step, Duck's choice, Duck's card); a step under way reads one region of its outcome.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from inference.framework import strict_json

from inference.framework.lever_experiment_contract import (  # the persisted contract the validator shares (r2)
    CODES, FINISHED_TYPES, KINDS, PREFIX, RELATIONS, STALE_TYPES, experiment_id, parse, question,
)

PURPOSE = "LIMITS_EXPERIMENT"
CHAPTER = "limits"
CONDITIONS = {
    "SELF_REVERSAL": ("the lever's own press returns its region to a state seen earlier in this level and life",
                      "the cap is reached with no return: reversal stays owed"),
    "PERSISTENCE_TRIAL": ("one press of another lever leaves the subject's region unchanged, or changes it",
                          "the acting lever's own region does not respond: the trial tested nothing"),
}


# ---- the plan: B1's reading of this level and life ---------------------------------------------------------------

def _adapter(machine: Any) -> Any | None:
    return (getattr(machine, "_adapters", None) or {}).get(RELATIONS)


def active(adapter: Any) -> dict[str, Any] | None:
    return getattr(adapter, "_lever_experiment", None)


def _idle(machine: Any) -> Any | None:
    """G4-B when it can admit an experiment now: current, open, nothing pending, nothing under way."""
    adapter = _adapter(machine)
    if machine.gate_id != RELATIONS or adapter is None or adapter._closed() or adapter._pending is not None:
        return None
    return None if active(adapter) is not None else adapter


def _reading(machine: Any) -> tuple[tuple, dict[str, Any] | None]:
    """(regions, scope): G4.1's lever regions and B1's scope of this level and its current life."""
    from inference.framework import lever_dossier_facts as F
    from inference.framework import lever_dossier_state as S
    from inference.framework.g4_reactions import anatomy_payload
    from inference.framework.g4_relations import lever_regions

    g41 = machine._adapters.get("G4-REACTIONS")
    anatomies = {e: F.plain(anatomy_payload(a)) for e, a in (getattr(g41, "_anatomies", None) or {}).items()}
    level = int(machine.lives.level)
    evidence = {str(row["evidence_id"]) for row in machine.transition_index
                if row.get("level") == level and row.get("evidence_id")}
    regions = lever_regions([dict(payload) for _e, payload in sorted(anatomies.items())], [])
    return regions, S.observe(machine, level, anatomies, dict.fromkeys(evidence, True))


def _awaits_reset(machine: Any) -> bool:
    """A death not yet followed by its reset: the next life has no entry board to plan from."""
    rows = [row for row in machine.transition_index if row.get("level") == int(machine.lives.level)]
    return bool(rows) and rows[-1].get("boundary_state") in ("GAME_OVER", "WIN")


def _servable(machine: Any, region: Any) -> dict[str, Any] | None:
    click = dict(region.click or {})
    available = {item.action for item in machine.ego.affordances if item.action in machine.ego._currently_available}
    if str(click.get("kind") or "").upper() == "NAV" or click.get("action") not in available:
        return None  # only a plain, currently available click is a G4-B experiment step (NAV levers stay owed)
    return click


def _path(scope: Mapping[str, Any], entity_id: str) -> tuple[list[str], list[str]]:
    """(path, seen) of the region in the life so far: B1's own construction in ``derive``."""
    current = scope["initial"][entity_id]
    path, seen = [current], [current]
    for row in scope["rows"]:
        if row["boundary"] == "END":
            break
        after = row["contents"][entity_id]
        if after != current:
            path.append(after)
            seen += [] if after in seen else [after]
        current = after
    return path, seen


def plan(machine: Any) -> list[dict[str, Any]]:
    """Every experiment G4-B can admit now, in coverage order (levers in order; each lever's earliest owed item
    that it can serve and has not closed in this level and life). Empty whenever G4-B is not idle."""
    from inference.framework.virelai_gates import control_archetype_prior

    adapter = _idle(machine)
    if adapter is None or _awaits_reset(machine) or control_archetype_prior(
            machine.ego.affordances)["world_type"] != "CLICK_GOD_MODE":
        return []  # NAV and HYBRID worlds route their presses: no experiment is admitted there yet
    regions, scope = _reading(machine)
    if scope is None or scope.get("initial") is None:
        return []
    out = []
    for region in regions:
        candidate = _owed(machine, adapter, scope, region, regions)
        if candidate is not None:
            out.append(candidate)
    return out


def _owed(machine: Any, adapter: Any, scope: Mapping[str, Any], region: Any, regions: Sequence[Any]
          ) -> dict[str, Any] | None:
    from inference.framework import lever_dossier_state as S

    entity = region.entity_id
    observations = S.derive(scope, entity)
    if observations["status"] != "OBSERVED":
        return None  # a failed or unbuilt reading owes nothing an experiment could honestly add to
    readings = {"LIMITS_PERSISTENCE": S.persistence_reading(observations),
                "LIMITS_REVERSAL": S.reversal_reading(observations)}
    closed = {(item["entity_id"], item["open_item"]) for item in getattr(adapter, "_lever_experiments", ())
              if (item["level"], item["life"]) == (scope["level"], scope["life"])}
    for item, (kind, code, cap) in KINDS.items():
        if readings[item] == "OBSERVED" or (entity, item) in closed:
            continue
        acting = region if kind == "SELF_REVERSAL" else next(
            (other for other in regions if other.entity_id != entity and _servable(machine, other)), None)
        action = None if acting is None else _servable(machine, acting)
        if action is None:
            continue
        path, seen = _path(scope, entity)
        state = observations["current_region_state"]
        return {"entity_id": entity, "open_item": item, "kind": kind, "code": code, "cap": cap, "action": action,
                "acting_lever": acting.entity_id, "acting_cells": [list(cell) for cell in acting.cells],
                "cells": [list(cell) for cell in region.cells], "question_id": question(scope["level"], entity),
                "level": scope["level"], "life": scope["life"], "path": path, "seen": seen,
                "start_state": {"label": state["label"], "state_sha16": state["state_sha16"]}}
    return None


# ---- admission: Duck's choice, or the head of coverage ------------------------------------------------------------

def _experiment(machine: Any, candidate: Mapping[str, Any], actor: str) -> dict[str, Any]:
    """The experiment a candidate becomes on admission (its ordinal is the next among the game's G4 admissions)."""
    admission = 1 + sum(1 for item in machine.g4_selection_events if item["event"] == "ADMITTED")
    success, inconclusive = CONDITIONS[candidate["kind"]]
    return {
        **dict(candidate), "actor": actor, "gate_id": RELATIONS, "chapter": CHAPTER, "admission": admission,
        "experiment_id": experiment_id(candidate["code"], candidate["entity_id"], candidate["level"],
                                       candidate["life"], admission),
        "success_condition": success, "inconclusive_condition": inconclusive, "status": "ACTIVE",
        "current": candidate["start_state"]["state_sha16"], "declared_at_transition": machine.observed_through_step,
        "steps": [],
    }


def _admit(machine: Any, adapter: Any, candidate: Mapping[str, Any], actor: str, head: bool) -> dict[str, Any]:
    from inference.framework import g4_selection

    experiment = _experiment(machine, candidate, actor)
    adapter._lever_experiment = experiment
    g4_selection.note(machine, "ADMITTED", experiment, f"{candidate['open_item']} owed: {candidate['kind']}"
                      + ("" if head else ", away from the coverage head"))
    return experiment


def select(machine: Any, question_id: str, *, actor: str) -> dict[str, Any]:
    """Admit Duck's choice of a lever's limits experiment; a refusal is recorded once and raised."""
    from inference.framework import g4_selection
    from inference.framework.virelai_gates import GateContractError

    request = {"question_id": question_id, "actor": actor, "gate_id": machine.gate_id}
    adapter, reason, candidates = _adapter(machine), None, []
    running = None if adapter is None else active(adapter)
    if machine.gate_id != RELATIONS or adapter is None:
        reason = f"the active gate is {machine.gate_id}; only G4-B admits a limits experiment"
    elif running is not None:
        reason = f"experiment {running['experiment_id']} is under way and cannot be replaced"
    elif adapter._pending is not None:
        reason = f"prediction {adapter._pending.prediction_id} is frozen and is taken first"
    else:
        candidates = plan(machine)
    row = next((item for item in candidates if item["question_id"] == question_id), None)
    if reason is not None or row is None:
        reason = reason or "the question names no limits experiment G4-B can serve now"
        g4_selection.note(machine, "REFUSED", request, reason)
        raise GateContractError(f"G4 choice not admissible: {reason}.")
    return dict(_admit(machine, adapter, row, actor, row is candidates[0]))


def _offer(adapter: Any) -> dict[str, Any] | None:
    """The head of coverage as G4-B offers it before the record's answer: not admitted until its first step is
    recorded, so a decline is no call at all and asking who owns the step changes nothing."""
    candidates = plan(adapter.machine)
    return None if not candidates else _experiment(adapter.machine, candidates[0], "CONTROLLER")


# ---- the gate's hooks ----------------------------------------------------------------------------------------------

def owns(probe: Any) -> bool:
    return getattr(probe, "gate_id", None) == RELATIONS and str(getattr(probe, "probe_id", "")).startswith(PREFIX)


def running(adapter: Any) -> str | None:
    experiment = active(adapter)
    return None if experiment is None else f"the controller takes {experiment['experiment_id']}"


def refuse_freeze(adapter: Any) -> None:
    experiment = active(adapter)
    if experiment is not None:
        from inference.framework.g4_relations import G4RelationError

        raise G4RelationError(f"limits experiment {experiment['experiment_id']} is under way; the controller "
                              "finishes it first")


def _close(adapter: Any, terminal: str, detail: str, at: int | None = None) -> None:
    """Close the experiment under way on the record; ``at``: the step that closed it, when a step did."""
    from inference.framework import g4_selection

    experiment = adapter._lever_experiment
    adapter._lever_experiment = None
    experiment["status"] = terminal
    adapter._lever_experiments = [*getattr(adapter, "_lever_experiments", ()),
                                  {key: value for key, value in experiment.items() if key not in ("path", "seen")}]
    event = "FINISHED" if terminal in FINISHED_TYPES else "STALE"
    g4_selection.note(adapter.machine, event, experiment, f"{terminal}: {detail}", adapter)
    if at is not None:  # the step is recorded after its gate's event: it closed at its own transition
        adapter.machine.g4_selection_events[-1]["at_transition"] = int(at)


def _subject_gone(machine: Any, entity_id: str) -> bool:
    ledger = getattr((getattr(machine, "_adapters", None) or {}).get("G3-LEVERS"), "entity_ledger", None)
    hypothesis = None if ledger is None else ledger.entities.get(entity_id)
    return hypothesis is not None and hypothesis.status != "PRESENT"


def settle(adapter: Any) -> None:
    """End an experiment its level, life, gate or subject no longer supports (G4-B's own state-advancing call)."""
    experiment, machine = active(adapter), adapter.machine
    if experiment is None:
        return
    level, life = int(machine.lives.level), int(machine.lives.life)
    if level != experiment["level"]:
        _close(adapter, "INTERRUPTED_LEVEL_CHANGE", f"level {level} began")
    elif life != experiment["life"]:
        _close(adapter, "INTERRUPTED_DEATH", f"life {life} began")
    elif adapter._closed():
        _close(adapter, "GATE_CHANGED", "G4-B closed")
    elif _subject_gone(machine, experiment["entity_id"]):
        _close(adapter, "STALE_SUBJECT", f"{experiment['entity_id']} is no longer on the board")


def close_with_gate(adapter: Any) -> None:
    """G4-B is closing (an answer, a budget close, a level boundary): an experiment under way ends with it."""
    if active(adapter) is not None:
        level_end = adapter._level_closed is not None
        _close(adapter, "INTERRUPTED_LEVEL_CHANGE" if level_end else "GATE_CHANGED", "G4-B closed")


def next_probe(adapter: Any) -> Any | None:
    """The active experiment's next step as a G4-B envelope, else None."""
    from inference.framework.virelai_gates import ProbeEnvelope

    settle(adapter)
    experiment = active(adapter) or (None if adapter._closed() else _offer(adapter))
    if experiment is None:
        return None
    k = len(experiment["steps"]) + 1
    alternatives = (("UNCHANGED", "CHANGED") if experiment["kind"] == "PERSISTENCE_TRIAL"
                    else ("RETURNED", "NOT_YET_RETURNED"))
    return ProbeEnvelope(
        probe_id=f"{experiment['experiment_id']}:{k}", gate_id=RELATIONS, purpose=PURPOSE,
        question=f"{experiment['open_item']}: {experiment['success_condition']}", actions=(dict(experiment["action"]),),
        live_alternatives=alternatives, outcome_partition=("experiment",),
        declared_at_transition=int(experiment["declared_at_transition"] or 0),
        target=_target(experiment, k),
    )


def _target(experiment: Mapping[str, Any], k: int) -> dict[str, Any]:
    keys = ("experiment_id", "question_id", "entity_id", "open_item", "kind", "chapter", "cap", "acting_lever",
            "start_state", "success_condition", "inconclusive_condition")
    return {**{key: experiment[key] for key in keys}, "step": k, "selected_by": experiment["actor"],
            "receipts": [step["evidence_id"] for step in experiment["steps"]]}


def controller_reason(capability: Mapping[str, Any] | None) -> str | None:
    target = (capability or {}).get("target") or {}
    if "experiment_id" not in target:
        return None
    chosen = ", Duck's choice" if target["selected_by"] == "DUCK" else ""
    return (f"G4-B: limits experiment {target['experiment_id']} ({target['kind']} of {target['entity_id']}), step "
            f"{target['step']} of {target['cap']}{chosen} — {target['question_id']}")


# ---- one step: recorded as any G4-B probe is, read on the subject's region ----------------------------------------

def _content(grid: Sequence[Sequence[int]], cells: Sequence[Sequence[int]]) -> str:
    return strict_json.sha16([int(grid[r][c]) for r, c in cells])


def _verdict(experiment: dict[str, Any], before: Sequence[Sequence[int]], after: Sequence[Sequence[int]],
             state: Mapping[str, Any] | None) -> tuple[str | None, str, str]:
    """(terminal type or None, the subject's content after, why) for one recorded step."""
    from inference.framework.g4_guided import is_terminal, level_changed

    was, now = _content(before, experiment["cells"]), _content(after, experiment["cells"])
    k = len(experiment["steps"]) + 1
    if is_terminal(state):
        level = level_changed(state)
        return ("INTERRUPTED_LEVEL_CHANGE" if level else "INTERRUPTED_DEATH"), now, f"step {k} ended the {'level' if level else 'life'}"
    if was != experiment["current"]:
        return "CONTRADICTION", now, f"step {k}'s before-board is not the last observed state"
    if experiment["kind"] == "PERSISTENCE_TRIAL":
        if _content(before, experiment["acting_cells"]) == _content(after, experiment["acting_cells"]):
            return "PERSISTENCE_INCONCLUSIVE", now, f"{experiment['acting_lever']}'s own region did not respond"
        return ("PERSISTENCE_UNCHANGED" if now == was else "PERSISTENCE_CHANGED"), now, \
            f"{experiment['acting_lever']}'s press, {experiment['entity_id']} {'unchanged' if now == was else 'changed'}"
    return _return(experiment, was, now, k)


def _return(experiment: dict[str, Any], was: str, now: str, k: int) -> tuple[str | None, str, str]:
    """A self-press: a return to an earlier state of the life (B1's cycle reading), else on to the cap."""
    path = experiment["path"]
    if now != was and now in path:
        cycle = len(path) - (len(path) - 1 - path[::-1].index(now))
        label = f"S{experiment['seen'].index(now)}"
        return ("REVERSAL_OBSERVED" if cycle == 2 else "RECURRENCE_OBSERVED"), now, \
            f"step {k} returned {experiment['entity_id']} to {label} (cycle {cycle})"
    if now != was:
        path.append(now)
        experiment["seen"] += [] if now in experiment["seen"] else [now]
    if k >= experiment["cap"]:
        return "CAPPED", now, f"no return in {k} presses; reversal stays owed"
    return None, now, ""


def record_outcome(adapter: Any, probe: Any, outcome: Mapping[str, Any]) -> dict[str, Any]:
    """G4-B's record of an experiment step: an evidence id like any G4-B probe's, the step's reading, and the
    experiment's close when the step ends it (a level boundary closes the gate's level as a prediction's does)."""
    from inference.framework.g4_guided import is_terminal, level_changed
    from inference.framework.masked_world_state import grids_from_probe_outcome
    from inference.framework.probe_evidence import compact_probe_outcome
    from inference.framework.virelai_gates import SCHEMA_VERSION, GateContractError, _canonical

    experiment, step = active(adapter), parse(probe.probe_id)
    offer = _offer(adapter) if experiment is None else None
    if offer is not None and step is not None and step["k"] == 1 and step["experiment_id"] == offer["experiment_id"]:
        experiment = _admit(adapter.machine, adapter, offer, "CONTROLLER", True)  # the head's first step admits it
    grids = grids_from_probe_outcome(outcome)
    if experiment is None or step is None or step["experiment_id"] != experiment["experiment_id"]:
        raise GateContractError("Outcome does not belong to the G4-B experiment under way.")
    if grids is None:
        raise GateContractError(f"{probe.gate_id} requires lossless full-grid site transitions.")
    evidence_id = "E-" + hashlib.sha256(_canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()).hexdigest()[:16]
    baseline = adapter.machine.apply_counter_baseline({**dict(outcome), "evidence_id": evidence_id})
    boundary = outcome.get("boundary_event")
    state = dict(boundary) if isinstance(boundary, Mapping) else None
    terminal, now, why = _verdict(experiment, *grids, state)
    experiment["steps"].append({"k": step["k"], "probe_id": probe.probe_id, "evidence_id": evidence_id,
                                "transition_id": int(outcome.get("transition_id") or 0), "state_sha16": now})
    experiment["current"] = now
    closed = is_terminal(state) and level_changed(state)
    event = {"schema": SCHEMA_VERSION, "evidence_id": evidence_id, "gate_id": probe.gate_id, "probe_id": probe.probe_id,
             "action": dict(outcome.get("action") or {}), "question_id": experiment["question_id"],
             "experiment": {"experiment_id": experiment["experiment_id"], "entity_id": experiment["entity_id"],
                            "kind": experiment["kind"], "step": step["k"], "terminal": terminal},
             "outcome": compact_probe_outcome(outcome), "counter_baseline": baseline,
             "level_boundary": None if not closed else {"evidence_ref": evidence_id, "level_before": state.get("level_before"),
                                                        "level_after": state.get("level_after")}}
    adapter.revision += 1
    adapter._events.append(event)
    if terminal is not None:
        _close(adapter, terminal, why, experiment["steps"][-1]["transition_id"])
    if closed and adapter._level_closed is None:
        adapter._level_closed = event["level_boundary"]
        adapter._emit_product()
    return event


def replay_hold(machine: Any, step: Mapping[str, Any]) -> str | None:
    """A record's experiment step (``tools/record_from_artifacts``) is taken before any G4-B answer then due, as live:
    the gate the replay holds its answers at (None for any other step). Duck's choice is admitted again here, before
    its first step; a coverage experiment needs nothing, its first step admits it as live."""
    experiment = step.get("experiment")
    if not isinstance(experiment, Mapping):
        return None
    first = parse(experiment.get("probe_id"))
    if (first is not None and first["k"] == 1 and experiment.get("selected_by") == "DUCK"
            and machine.gate_id == RELATIONS and active(_adapter(machine)) is None):
        machine.select_question(str(experiment.get("question_id")), actor="DUCK")
    return RELATIONS


# ---- what Duck, the agenda and the dossier read ------------------------------------------------------------------

def _row(experiment: Mapping[str, Any]) -> dict[str, Any]:
    return {key: experiment[key] for key in ("question_id", "entity_id", "open_item", "kind", "cap")}


def decorate(adapter: Any, view: dict[str, Any]) -> None:
    """G4-B's card subject, first: the experiment under way (the controller takes it), else the admissible ones."""
    experiment, block = active(adapter), None
    if experiment is not None:
        block = {"under_way": {**_row(experiment), "experiment_id": experiment["experiment_id"],
                               "steps_taken": len(experiment["steps"]), "selected_by": experiment["actor"]}}
        view.update(next_operation="CONTROLLER_TAKES_EXPERIMENT", answer_template=None)
    elif candidates := plan(adapter.machine):
        block = {"admissible": [_row(item) for item in candidates[:4]],
                 "choose": "virelai('next_probe', question_id=...) admits one; else the controller runs the first "
                           "before the record answers"}
    if block is not None:
        view["subject"] = {"experiments": block, **dict(view.get("subject") or {})}


def agenda_view(machine: Any) -> dict[str, Any]:
    """The limits questions G4-B serves now: the one under way, or the admissible ones in coverage order."""
    adapter = _adapter(machine)
    experiment = None if adapter is None or machine.gate_id != RELATIONS else active(adapter)
    if experiment is not None:
        return {"active": experiment["question_id"], "eligible": []}
    return {"active": None, "eligible": [item["question_id"] for item in plan(machine)]}


def evidence_failures(machine: Any, level: int, life: int, receipts: Mapping[str, Any]) -> dict[str, list[str]]:
    """Each subject whose experiment in this level and life lacks one-to-one execution evidence: every step one
    transition with a resolving receipt, numbered 1..n once each, and one G4-B step event per transition."""
    adapter = _adapter(machine)
    experiments = [*getattr(adapter, "_lever_experiments", ()), *([active(adapter)] if active(adapter) else [])]
    out: dict[str, list[str]] = {}
    for experiment in experiments:
        if (experiment["level"], experiment["life"]) != (int(level), int(life)):
            continue
        name = experiment["experiment_id"]
        rows = [row for row in machine.transition_index if str(row.get("probe_id") or "").startswith(name + ":")]
        events = [event["evidence_id"] for event in getattr(adapter, "_events", ())
                  if (event.get("experiment") or {}).get("experiment_id") == name]
        ks = sorted(parse(row["probe_id"])["k"] for row in rows)
        refs = [str(row.get("evidence_id")) for row in rows]
        if (ks != list(range(1, len(rows) + 1)) or any(ref not in receipts for ref in refs)
                or sorted(events) != sorted(refs)):
            out.setdefault(experiment["entity_id"], []).append(name)
    return out


__all__ = ["CODES", "FINISHED_TYPES", "KINDS", "PREFIX", "STALE_TYPES", "active", "agenda_view",
           "close_with_gate", "controller_reason", "decorate", "evidence_failures", "experiment_id", "next_probe",
           "owns", "parse", "plan", "question", "record_outcome", "refuse_freeze", "replay_hold", "running", "select",
           "settle"]

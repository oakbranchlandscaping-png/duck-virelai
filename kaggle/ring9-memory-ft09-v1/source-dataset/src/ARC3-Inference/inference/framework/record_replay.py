"""Replay a recorded world through the gate machine, measuring every card Duck would have seen.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 stage M-0).

The replay harness every later memory stage is measured against. A recorded world is a real run's
record: the initial grid, each transition's action and sparse changed cells, and the accepted gate
answers (only the parts Duck wrote; everything the controller derives — ids, templates,
evidence refs — is re-derived at replay, so the same record replays under changed code).

It drives the production gate machine exactly as a run does (capability, validation, lossless
outcome, answers when the gate demands one) and renders the binding card with the production
renderer after every step. No model is called.

Fixture format (``virelai-recorded-world-v1``, gzip JSON): ``initial_grid`` (hex rows),
``valid_actions``, ``steps`` [{transition_id, action, changed: [[r, c, before, after], ...]}],
``answers`` [{gate_id, ...Duck-written fields}] in acceptance order, and ``protocol``: the gate
machine's recording protocol (``{"g3_inherits_g2_nulls": bool}``). A record without ``protocol``
predates R9-R08 and was made with G3 re-clicking G2's nulls, so it replays that way.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.framework.card_builder import build_card
from inference.framework.gate_card import render_binding_gate_context
from inference.framework.virelai_gates import CyberneticGateMachine

HEX = "0123456789abcdef"
NOVEL_PREDICTION_FIELDS = ("action", "predicate", "expected_parameters", "because", "novelty")


@dataclass
class CardSample:
    after_transition: int
    gate_id: str
    schema: str | None
    status: str | None
    chars: int
    moment: str  # "before-step" | "before-answer" | "final"


@dataclass
class ReplayResult:
    machine: CyberneticGateMachine
    grid: list[list[int]]
    steps_replayed: int
    answers_used: int
    samples: list[CardSample] = field(default_factory=list)
    stopped: str | None = None
    measure: bool = True

    def largest(self, gate_id: str | None = None) -> CardSample:
        rows = [item for item in self.samples if gate_id is None or item.gate_id == gate_id]
        return max(rows, key=lambda item: item.chars)


def load_record(path: str | Path) -> dict[str, Any]:
    return json.loads(gzip.open(path).read())


def decode_grid(rows: Sequence[str]) -> list[list[int]]:
    return [[HEX.index(ch) for ch in row] for row in rows]


def record_protocol(record: Mapping[str, Any]) -> dict[str, bool]:
    """The protocol a record was made under; records without one predate ruling D5."""
    protocol = record.get("protocol") or {}
    return {"g3_inherits_g2_nulls": bool(protocol.get("g3_inherits_g2_nulls", False))}


def click_world_machine(
    grid: Sequence[Sequence[int]], valid_actions: Sequence[str], *, g3_inherits_g2_nulls: bool = True,
) -> CyberneticGateMachine:
    """A machine past G0 and G1 for a coordinate-action world (both derivable from metadata)."""
    machine = CyberneticGateMachine(
        valid_actions=list(valid_actions), initial_grid=grid, g3_inherits_g2_nulls=g3_inherits_g2_nulls,
    )
    machine.submit_answer({
        "answer_id": "G0-replay",
        "action_metadata": [
            {"action": item.action, "requires_coordinates": item.requires_coordinates}
            for item in machine.ego.affordances
        ],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until controlled observation reveals them.",
    })
    machine.submit_answer({
        "answer_id": "G1-replay",
        "answer_kind": "POINTER_GOD_MODE",
        "subjects": ["the coordinate-selecting control locus"],
        "mechanism": "the agent moves its pointer ego by supplying a new grid coordinate",
        "action_laws": {
            item.action: "places direct intervention at the supplied grid coordinate"
            for item in machine.ego.affordances if item.requires_coordinates
        },
        "conditions": ["the coordinate is legal"],
        "constraints": ["target effects remain unknown"],
        "evidence_refs": ["G0-ACTION-METADATA"],
        "competing_models": ["a persistent embodied grid object is controlled"],
        "falsifier": "the coordinate action requires no selected coordinate",
        "limitations": ["no target response has been classified"],
    })
    return machine


def lossless_outcome(
    grid: Sequence[Sequence[int]],
    transition_id: int,
    action: Mapping[str, Any],
    changed: Sequence[Sequence[int]],
    boundary: Mapping[str, Any] | None = None,
) -> tuple[list[list[int]], dict[str, Any]]:
    """Rebuild the total-coverage outcome a run records from a transition's sparse changes."""
    after = [list(row) for row in grid]
    for row, col, _before, value in changed:
        after[row][col] = value
    shape = [len(grid), len(grid[0])]
    return after, {
        "transition_id": int(transition_id),
        "shape_before": shape,
        "shape_after": shape,
        "action": dict(action),
        "acted_site": (
            {"row": action["row"], "col": action["col"]}
            if "row" in action and "col" in action else None
        ),
        "board_changed": bool(changed),
        "changed_cell_count": len(changed),
        "changed_cells": [{"row": r, "col": c, "before": b, "after": a} for r, c, b, a in changed],
        "site_transitions": [
            {"row": r, "col": c, "before": grid[r][c], "after": after[r][c],
             "outcome": "CHANGED" if grid[r][c] != after[r][c] else "HELD"}
            for r in range(len(grid)) for c in range(len(grid[0]))
        ],
        "boundary_event": dict(boundary or {"state": "NOT_FINISHED"}),
    }


def merge_recorded_answer(template: Mapping[str, Any], recorded: Mapping[str, Any]) -> dict[str, Any]:
    """The live template (controller-derived fields) overlaid with what Duck wrote."""
    payload = dict(template)
    for key, value in recorded.items():
        if key in {"gate_id", "novel_prediction"}:
            continue
        payload[key] = value
    if isinstance(recorded.get("novel_prediction"), Mapping) and isinstance(
        template.get("novel_prediction"), Mapping
    ):
        payload["novel_prediction"] = {
            **template["novel_prediction"],
            **{
                key: recorded["novel_prediction"][key]
                for key in NOVEL_PREDICTION_FIELDS
                if key in recorded["novel_prediction"]
            },
        }
    return payload


def _answer_due(machine: CyberneticGateMachine) -> bool:
    view = machine.gate_view()
    return view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"


def _sample(result: ReplayResult, after_transition: int, moment: str) -> None:
    if not result.measure:
        return
    view = result.machine.gate_view()
    result.samples.append(CardSample(
        after_transition=after_transition,
        gate_id=result.machine.gate_id,
        schema=view.get("schema"),
        status=view.get("status"),
        chars=len(render_binding_gate_context(result.machine)),
        moment=moment,
    ))


def replay(
    record: Mapping[str, Any], *, max_steps: int | None = None, answer_source: str = "view",
    measure: bool = True,
) -> ReplayResult:
    """Replay a recorded world; stop cleanly where the record or the machine ends.

    ``answer_source="card"`` builds each answer from the template on Duck's card (certified fields
    left marked for the controller to fill), proving an answer written from the card is accepted.
    """
    grid = decode_grid(record["initial_grid"])
    machine = click_world_machine(
        grid, record.get("valid_actions") or ["ACTION6"], **record_protocol(record)
    )
    pending = {}
    for answer in record.get("answers") or ():
        pending.setdefault(answer["gate_id"], []).append(answer)
    result = ReplayResult(machine=machine, grid=grid, steps_replayed=0, answers_used=0, measure=measure)
    last = 0
    steps = record["steps"][: max_steps if max_steps is not None else None]
    for step in steps:
        if not _submit_due_answers(result, pending, answer_source, last):
            result.stopped = f"no recorded answer for {machine.gate_id} before transition {step['transition_id']}"
            _sample(result, last, "final")
            return result
        capability = machine.next_probe_capability()
        while capability is None and _answer_due(machine) and _submit_due_answers(result, pending, answer_source, last):
            capability = machine.next_probe_capability()  # probing closed a roster; its answers came due
        _sample(result, last, "before-step")
        if capability is None:
            result.stopped = f"no capability at {machine.gate_id} before transition {step['transition_id']}"
            return result
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        result.grid, outcome = lossless_outcome(
            result.grid, step["transition_id"], step["action"], step["changed"], step.get("boundary")
        )
        machine.record_outcome(probe, outcome)
        result.steps_replayed += 1
        last = int(step["transition_id"])
    if max_steps is None or max_steps >= len(record["steps"]):
        machine.next_probe_capability()  # a completed roster asks for its answer only when probed
        _submit_due_answers(result, pending, answer_source, last)  # answers after the last action
    _sample(result, last, "final")
    return result


def _submit_due_answers(
    result: ReplayResult, pending: dict[str, list], answer_source: str, last: int
) -> bool:
    """Submit every answer the machine demands now; False if the record has none to give."""
    machine = result.machine
    while _answer_due(machine):
        queue = pending.get(machine.gate_id) or []
        if not queue:
            return False
        _sample(result, last, "before-answer")
        template = (
            build_card(machine).payload.get("answer_template")
            if answer_source == "card" else machine.gate_view().get("answer_template")
        ) or {}
        machine.submit_answer(merge_recorded_answer(template, queue.pop(0)))
        result.answers_used += 1
    return True

"""G2 under the counter axiom: find, label, mask -- purity, not isolation.

Author: Claude (Alpha build seat), 2026-09-27.

Regression for REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md. In the ft09 Kaggle run the bar
counter ticked only on effective clicks, so every witness also changed a control. G2 demanded a
"counter-only" action for its prospective test, found none, and offered no legal move for about
2.5 hours.

Axiom A1 (DOCTRINE_FRICTION_AXIOMS_v1, Director 2026-09-27): counters come in many forms; the
target is the same -- find it, label it, mask it to keep lever data pure. G2 in CLICK worlds is a
stated target: Duck chooses the actions and the prediction's action; the controller checks purity
on the record and grades a footprint-scoped prediction.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from inference.framework.virelai_gates import CyberneticGateMachine

FIXTURE = Path(__file__).parent / "fixtures" / "ft09_kaggle_v1_g2_segment.json.gz"
HEX = "0123456789abcdef"


def _load():
    return json.loads(gzip.open(FIXTURE).read())


def _decode(rows):
    return [[HEX.index(ch) for ch in row] for row in rows]


def _machine(grid):
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=grid)
    machine.submit_answer({
        "answer_id": "G0-click",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until controlled observation reveals them.",
    })
    machine.submit_answer({
        "answer_id": "G1-pointer",
        "answer_kind": "POINTER_GOD_MODE",
        "subjects": ["the ACTION6 site-selecting control locus"],
        "mechanism": "Duck moves its pointer ego by supplying a new grid coordinate",
        "action_laws": {"ACTION6": "places direct intervention at the supplied grid coordinate"},
        "conditions": ["the coordinate is legal"],
        "constraints": ["target effects remain unknown"],
        "evidence_refs": ["G0-ACTION-METADATA"],
        "competing_models": ["a persistent embodied grid object is controlled"],
        "falsifier": "ACTION6 requires no selected coordinate for direct intervention",
        "limitations": ["no target response has been classified"],
    })
    assert machine.gate_id == "G2-COUNTER"
    return machine


def _outcome(grid, transition_id, action, changed, boundary=None):
    after = [list(row) for row in grid]
    for row, col, _before, value in changed:
        after[row][col] = value
    return after, {
        "transition_id": transition_id,
        "shape_before": [len(grid), len(grid[0])],
        "shape_after": [len(grid), len(grid[0])],
        "action": dict(action),
        "acted_site": {"row": action["row"], "col": action["col"]},
        "board_changed": bool(changed),
        "changed_cell_count": len(changed),
        "changed_cells": [
            {"row": r, "col": c, "before": b, "after": a} for r, c, b, a in changed
        ],
        "site_transitions": [
            {"row": r, "col": c, "before": grid[r][c], "after": after[r][c],
             "outcome": "CHANGED" if grid[r][c] != after[r][c] else "HELD"}
            for r in range(len(grid)) for c in range(len(grid[0]))
        ],
        "boundary_event": boundary or {"state": "NOT_FINISHED"},
    }


def _act(machine, grid, transition_id, action, changed):
    """Duck's own choice of action through the guided G2 capability."""
    capability = machine.next_probe_capability()
    assert capability is not None, "G2 offered no legal move"
    assert capability["purpose"] in {"GUIDED_ACTION", "DEMONSTRATE"}
    if capability["purpose"] == "DEMONSTRATE":
        assert capability["actions"] == [action]
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [action])
    after, outcome = _outcome(grid, transition_id, action, changed)
    event = machine.record_outcome(probe, outcome)
    return after, event


def _replay_real_segment():
    data = _load()
    grid = _decode(data["initial_grid"])
    machine = _machine(grid)
    event = None
    for step in data["steps"]:
        grid, event = _act(machine, grid, step["transition_id"], step["action"], step["changed"])
    return machine, grid, event


def _answer(machine, *, action, predicate, amount):
    template = machine.gate_view()["answer_template"]
    assert template is not None, "the card must never ask for an answer without a template"
    candidate = machine.counter.candidate
    machine.submit_answer({
        **template,
        "tracked_variable": "remaining effective clicks shown by the bottom bar",
        "mechanism": "two bar cells rewrite from twelve to eleven on each click that changes a control",
        "bookkeeping_reason": "the bar changed with two different controls and stayed still on 54 dead clicks",
        "evidence_refs": list(candidate.witness_evidence_refs),
        "competing_models": ["the bar is a remote effect of those two controls only"],
        "falsifier": "a control click leaves the bar unchanged, or a dead click ticks it",
        "novel_prediction": {
            **template["novel_prediction"],
            "action": action,
            "predicate": predicate,
            "expected_parameters": {"rewrite": "12->11", "amount": amount},
            "because": "the label says the bar counts effective clicks at two cells each",
            "novelty": "this is a later transition from a state the witnesses never produced",
        },
    })


def test_real_ft09_segment_yields_a_counter_candidate_with_an_answer_path():
    machine, _grid, event = _replay_real_segment()
    candidate = machine.counter.candidate
    assert candidate is not None
    assert candidate.rewrite == "12->11"
    assert {row for row, _col in candidate.full_bar_footprint} == {63}
    assert len(candidate.full_bar_footprint) == 64
    view = machine.gate_view()
    assert view["status"] == "ANSWER_REQUIRED"
    # The ft09 defect: no counter-only witness exists, yet a template and an answer path must.
    assert machine.counter._counter_only_action is None
    assert view["answer_template"] is not None
    assert "target" in view and "done_when" in view
    assert machine.counter._purity_violations(candidate) == []
    del event


def test_rewrite_prediction_on_a_control_click_closes_g2_with_a_pure_mask():
    machine, grid, _ = _replay_real_segment()
    control = {"action": "ACTION6", "row": 36, "col": 36}
    _answer(machine, action=control, predicate="COUNTER_REWRITE", amount=2)
    assert machine.gate_view()["status"] == "DEMONSTRATION_REQUIRED"
    # Continuation (synthesized from the observed laws, not recorded): the control flips back
    # 8->9 and the bar loses its next two cells 12->11.
    changed = [[r, c, 8, 9] for r in range(36, 42) for c in range(36, 42)]
    changed += [[63, 59, 12, 11], [63, 58, 12, 11]]
    _grid, event = _act(machine, grid, 57, control, changed)
    assert event["counter_comparison"]["outcome"] == "SUPPORTED"
    assert machine.counter.status == "CLOSED"
    assert {row for row, _col in machine.counter.mask_law.cells} == {63}
    assert machine.gate_id == "G3-LEVERS"


def test_silent_prediction_on_a_dead_click_also_closes_g2():
    machine, grid, _ = _replay_real_segment()
    dead = {"action": "ACTION6", "row": 10, "col": 14}
    _answer(machine, action=dead, predicate="COUNTER_SILENT", amount=0)
    _grid, event = _act(machine, grid, 57, dead, [])
    assert event["counter_comparison"]["outcome"] == "SUPPORTED"
    assert machine.counter.status == "CLOSED"
    assert machine.gate_id == "G3-LEVERS"


def test_silent_prediction_is_contradicted_by_a_footprint_tick_and_search_resumes():
    machine, grid, _ = _replay_real_segment()
    dead = {"action": "ACTION6", "row": 10, "col": 14}
    _answer(machine, action=dead, predicate="COUNTER_SILENT", amount=0)
    _grid, event = _act(machine, grid, 57, dead, [[63, 59, 12, 11], [63, 58, 12, 11]])
    assert event["counter_comparison"]["outcome"] == "CONTRADICTED"
    assert machine.counter.mask_law is None
    assert machine.counter.status == "ACTIVE"
    assert machine.next_probe_capability() is not None


def test_candidate_whose_footprint_breaks_the_counter_law_is_rejected_not_deadlocked():
    """Purity: a footprint cell that ever changed outside the counter law cannot be masked."""
    data = _load()
    grid = _decode(data["initial_grid"])
    machine = _machine(grid)
    steps = data["steps"]
    # Plant a world effect inside the bar before the witnesses: bar cell 63,30 is rewritten
    # 12->5 by one click and restored 5->12 by the next, so it is back inside the bar footprint
    # when the counter candidate forms, but its history breaks the counter law.
    planted = [dict(steps[0], changed=[[63, 30, 12, 5]]), dict(steps[1], changed=[[63, 30, 5, 12]])]
    for step in planted + steps[2:]:
        grid, _ = _act(machine, grid, step["transition_id"], step["action"], step["changed"])
    counter = machine.counter
    assert counter.candidate is None
    assert counter.status == "ACTIVE"
    assert counter._rejected_candidates
    assert counter._rejected_candidates[-1]["reason"] == "COUNTER_CANDIDATE_IMPURE"
    assert machine.next_probe_capability() is not None

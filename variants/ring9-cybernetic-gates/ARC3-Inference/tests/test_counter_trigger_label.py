"""Axiom A1, sharpened: the counter's label must agree with the whole record.

Author: Claude (Alpha build seat), 2026-09-28.

Regression for REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md. G2 closed live on ft09 with a pure
mask, but Duck labelled the bar a count of every action "regardless of which grid cell is
clicked", while the record held 54 clicks that changed nothing and did not tick it. A prediction
on a control click cannot separate "every action" from "effective actions only", so the wrong label
passed. The controller now computes the trigger class from the record and the answer's structured
``trigger`` must agree with it.
"""
from __future__ import annotations

import pytest

from inference.framework.virelai_gates import GateContractError
from test_g2_counter_axiom import _act, _replay_real_segment

LIVE_DUCK_LABEL = {
    "tracked_variable": "Cumulative action count: each ACTION6 click increments the counter by 2 cells",
    "mechanism": "Each environment transition triggers a rewrite of exactly 2 bar cells from 12 to 11",
    "bookkeeping_reason": "The bar changes identically regardless of which grid cell is clicked",
    "competing_models": ["the bar is a remote effect of those two controls only"],
    "falsifier": "a future action produces a rewrite of a different amount",
}


def _answer(machine, trigger):
    template = machine.gate_view()["answer_template"]
    candidate = machine.counter.candidate
    payload = {
        **template,
        **LIVE_DUCK_LABEL,
        "evidence_refs": list(candidate.witness_evidence_refs),
        "novel_prediction": {
            **template["novel_prediction"],
            "action": {"action": "ACTION6", "row": 36, "col": 36},
            "predicate": "COUNTER_REWRITE",
            "expected_parameters": {"rewrite": "12->11", "amount": 2},
            "because": "the bar has rewritten two cells on each effective click so far",
            "novelty": "this is a later transition from a state the witnesses never produced",
        },
    }
    if trigger is None:
        payload.pop("trigger", None)
    else:
        payload["trigger"] = trigger
    return machine.submit_answer(payload)


def test_the_real_ft09_record_says_the_counter_ticks_on_effective_clicks_only():
    machine, _grid, _ = _replay_real_segment()
    record = machine.counter.record_trigger()
    assert record["class"] == "EFFECTIVE_TRANSITIONS_ONLY"
    assert record["null_transitions_without_tick"] == 54
    assert record["effective_transitions_with_tick"] == 2
    view = machine.gate_view()
    assert view["record_trigger"]["class"] == "EFFECTIVE_TRANSITIONS_ONLY"
    assert view["answer_template"]["trigger"] == "EFFECTIVE_TRANSITIONS_ONLY"


def test_the_live_every_action_label_is_refused_with_the_record_as_reason():
    machine, _grid, _ = _replay_real_segment()
    with pytest.raises(GateContractError, match="54 transitions changed nothing and did not tick"):
        _answer(machine, "EVERY_TRANSITION")
    with pytest.raises(GateContractError, match="trigger"):
        _answer(machine, None)
    assert machine.counter.status == "ANSWER_REQUIRED"


def test_a_label_that_agrees_with_the_record_closes_g2_and_is_kept_on_the_model():
    machine, grid, _ = _replay_real_segment()
    answer = _answer(machine, "EFFECTIVE_TRANSITIONS_ONLY")
    assert answer.trigger == "EFFECTIVE_TRANSITIONS_ONLY"
    control = {"action": "ACTION6", "row": 36, "col": 36}
    changed = [[r, c, 8, 9] for r in range(36, 42) for c in range(36, 42)]
    changed += [[63, 59, 12, 11], [63, 58, 12, 11]]
    _act(machine, grid, 57, control, changed)
    assert machine.counter.status == "CLOSED"
    assert machine.counter.counter_model.trigger == "EFFECTIVE_TRANSITIONS_ONLY"


def test_open_record_admits_either_simple_trigger():
    """Only effective, ticking transitions so far: the record cannot yet tell the two apart."""
    from inference.framework.virelai_gates import CounterCandidate, CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        affordances=action_affordances(["ACTION6"]), initial_grid=((0, 0), (5, 5)),
        observed_through_step=0,
    )
    counter.candidate = CounterCandidate(
        candidate_id="C", rewrite="5->4", observed_support=((1, 1),),
        full_bar_footprint=((1, 0), (1, 1)), footprint_geometry="HORIZONTAL_BAR",
        source_integer=5, replacement_integer=4, witness_evidence_refs=("E1", "E2"),
        witness_transition_ids=(1, 2), intervention_keys=(), amount_per_transition=(1, 1),
    )
    counter._lossless_outcomes = [
        {"evidence_id": f"E{i}", "transition_id": i, "changed_cells": [
            {"row": 0, "col": 0, "before": i - 1, "after": i},
            {"row": 1, "col": 2 - i, "before": 5, "after": 4},
        ]}
        for i in (1, 2)
    ]
    record = counter.record_trigger()
    assert record["class"] == "OPEN"
    assert set(record["admissible_claims"]) == {"EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY"}

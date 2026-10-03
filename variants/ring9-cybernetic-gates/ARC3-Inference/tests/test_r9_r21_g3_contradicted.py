"""R9-R21: level 2's G3 stall in ring9-carry-vc33-v4 (Kaggle, 2026-10-03).

Author: Claude (Alpha build seat), 2026-10-03. REVIEW_RING9_CARRY_VC33_V4_KAGGLE_2026-10-03.md and
DIAGNOSTIC_G3_CONTRADICTED_CONFIRMATION_v1_2026-10-03.md.

Live: on level 2, two of the four carried-type levers were stateful. A second identical press did
nothing at (16,0) and changed other cells at (24,0), so G3's confirmations were CONTRADICTED and both
entities went AMBIGUOUS, but unbounded (D4): every other CLICK-phase route to AMBIGUOUS records a
bounded ambiguity, and this one did not. G3's inventory refuses unbounded entities, enumeration was
complete, no probe remained, and the A2 watchdog called the state legal because a template existed (D5).
Separately, the level-completed boundary woke Duck at level entry, so Duck, not the controller,
answered level 2's G0 (D6).

Fixture: the v4 run's own record (47 transitions). Each test failed before R9-R21.
"""
from __future__ import annotations

import json
from pathlib import Path

from inference.framework.controller_executor import next_owned_step, wake_reason
from inference.framework.record_replay import load_record, lossless_outcome, record_like_live, replay

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VC33_CARRY_V4 = FIXTURES / "vc33_kaggle_carry_v4_record.json.gz"
VC33_CARRY_V2 = FIXTURES / "vc33_kaggle_carry_v2_record.json.gz"


def _drive_level_two():
    """Replay level 1, then level 2 as live: the controller's answers, the recorded actions."""
    record = load_record(VC33_CARRY_V4)
    result = replay(record, max_steps=26, measure=False)
    machine, grid = result.machine, result.grid
    for step in record["steps"][26:]:
        owned = next_owned_step(machine)
        while owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
            machine.submit_answer(json.loads(json.dumps(owned.answer)))
            owned = next_owned_step(machine)
        capability = machine.next_probe_capability()
        assert capability is not None, (step["transition_id"], machine.gate_id, owned.reason)
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"])
        record_like_live(machine, probe, outcome, ["ACTION6"])
    assert machine.lives.level == 2 and machine.gate_id == "G3-LEVERS"
    return machine


def test_a_contradicted_confirmation_is_recorded_as_a_bounded_ambiguity():
    """D4: like every other CLICK-phase route to AMBIGUOUS, with no inertness claim and a retry condition."""
    g3 = _drive_level_two()._adapters["G3-LEVERS"]
    statuses = {item["entity_id"]: item["status"] for item in g3._confirmation_records}
    assert statuses == {"E0004": "CONTRADICTED", "E0005": "CONTRADICTED", "E0006": "SUPPORTED", "E0007": "SUPPORTED"}
    assert sorted(g3._bounded_ambiguities) == ["E0004", "E0005"]
    for record in g3._bounded_ambiguities.values():
        assert record["disposition"] == "CONFIRMATION_CONTRADICTED"
        assert record["inertness_claim_permitted"] is False and record["retry_condition"]


def test_the_live_level_two_g3_reaches_an_accepted_coverage_report():
    """The v4 stall, replayed: the coverage report is Duck's by design, it is legal, and it is accepted."""
    machine = _drive_level_two()
    owned = next_owned_step(machine)
    assert owned.owner == "DUCK" and "bounded ambiguity" in owned.reason
    assert machine.legal_move_status()["legal"] is True
    answer = dict(machine.gate_view()["answer_template"])
    answer.update(
        explanation="E0006 and E0007 repeat their remote rewrite; E0004 and E0005 did not on a second press.",
        competing_models=["E0004 and E0005 respond to board state, not to the press alone."],
        falsifier="A repeated press of E0004 or E0005 from the same board that reproduces its first rewrite.",
    )
    machine.submit_answer(answer)
    inventory = machine._adapters["G3-LEVERS"]._bounded_coverage_answer
    assert inventory is not None
    assert (answer["lever_entities"], answer["ambiguous_entities"]) == (["E0006", "E0007"], ["E0004", "E0005"])


def test_an_inventory_no_answer_can_satisfy_is_not_a_legal_move():
    """D5 (axiom A2): the exact live state (ambiguity left unbounded) is a deadlock the watchdog must see."""
    machine = _drive_level_two()
    machine._adapters["G3-LEVERS"]._bounded_ambiguities.clear()  # the v4 state, before D4
    assert machine.next_probe_capability() is None
    status = machine.legal_move_status()
    assert status["legal"] is False and "unbounded" in status["reason"]


def test_a_level_change_that_restarts_the_ladder_does_not_wake_duck():
    """D6: the controller owns level entry; deaths and the run's end still wake Duck."""
    level_two = replay(load_record(VC33_CARRY_V2), measure=False).machine
    assert level_two.gate_id == "G0-ACTION-METADATA" and level_two.lives.level == 2
    assert wake_reason(level_two, {}, {"level_completed": True}) is None
    assert wake_reason(level_two, {}, {"game_over": True}) == "boundary event: game_over"
    level_one = replay(load_record(VC33_CARRY_V2), max_steps=25, measure=False).machine
    assert wake_reason(level_one, {}, {"level_completed": True}) == "boundary event: level_completed"

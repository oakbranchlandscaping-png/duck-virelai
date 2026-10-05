"""R9-R22: G3 discovers levers; G4 types them.

Author: Claude (Alpha build seat), 2026-10-03. DIAGNOSTIC_G3_G4_LEVER_TYPING_BOUNDARY_v1_2026-10-03.md;
Director ruling 2026-10-03 (diagnostic, then build).

Live (ring9-carry-vc33-v4 and v5, level 2): two of four levers did something different on G3's repeat
press. One moved, then held; one moved again to a third state. G3 read that as a contradicted witness and
kept both out of G4, the gate that types levers. By G4-A's own orbit measure, three of the four levers
(two of them "supported") revealed a third state on the repeat; only one held. The repeat press is typing
evidence, never a retraction (lever_attribution: silence never retracts an earlier witness).

Fixture: the v4 run's own record (47 transitions). Each test failed before R9-R22.
"""
from __future__ import annotations

import json

from inference.framework.controller_executor import next_owned_step, wake_reason
from inference.framework.g4_guided import LeverRun
from inference.framework.lever_repeat import certified
from inference.framework.record_replay import load_record, lossless_outcome, record_like_live, replay

from tests.test_r9_r21_g3_contradicted import FIXTURES, VC33_CARRY_V4

LEVERS = ["E0004", "E0005", "E0006", "E0007"]
REPEATS = {
    "E0004": "NULL_AT_OBSERVED_STATE",
    "E0005": "NOVEL_STATE_REVEALED",
    "E0006": "NOVEL_STATE_REVEALED",
    "E0007": "NOVEL_STATE_REVEALED",
}


def _controller_answers(machine) -> None:
    owned = next_owned_step(machine)
    while owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
        machine.submit_answer(json.loads(json.dumps(owned.answer)))
        owned = next_owned_step(machine)


def _drive_level_two():
    """Replay level 1, then level 2 as live: the controller's answers, the recorded actions."""
    record = load_record(VC33_CARRY_V4)
    result = replay(record, max_steps=26, measure=False)
    machine, grid = result.machine, result.grid
    for step in record["steps"][26:]:
        _controller_answers(machine)
        capability = machine.next_probe_capability()
        assert capability is not None, (step["transition_id"], machine.gate_id)
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"])
        record_like_live(machine, probe, outcome, ["ACTION6"])
    _controller_answers(machine)
    return machine


def test_a_repeat_press_is_typing_evidence_and_never_retracts_the_witness():
    """D7: the prediction is still graded honestly; the lever stands; the repeat is an orbit step."""
    machine = _drive_level_two()
    g3 = machine._adapters["G3-LEVERS"]
    records = {item["entity_id"]: item for item in g3._confirmation_records}
    assert {key: item["status"] for key, item in records.items()} == {
        "E0004": "CONTRADICTED", "E0005": "CONTRADICTED", "E0006": "SUPPORTED", "E0007": "SUPPORTED",
    }
    assert {key: item["repeat_disposition"] for key, item in g3._repeat_readings.items()} == REPEATS
    assert all(certified(item, g3._repeat_readings) for item in records.values())
    assert g3._bounded_ambiguities == {}
    assert all(g3.lifecycle_journal.entities[item].state == "G4-READY" for item in LEVERS)


def test_level_two_inventory_lists_all_four_levers_and_g4_opens():
    """D7 + D8: the controller's inventory is accepted with four levers, and G4 seeds all of them."""
    machine = _drive_level_two()
    product = machine.target_journal.active_product("G3-LEVERS")
    assert product is not None and sorted(product.payload["lever_entities"]) == LEVERS
    assert not product.payload.get("ambiguous_entities")
    assert machine.gate_id != "G3-LEVERS"
    reactions = machine._adapters["G4-REACTIONS"]
    reactions._seed()
    assert sorted(reactions._ordered_entities) == LEVERS


def test_each_lever_reaches_g4a_with_its_g3_pair():
    """D9: G3's two presses travel with the lever into G4-A, from their own entry state."""
    machine = _drive_level_two()
    orbits = machine._adapters["G4.2-LEVER-ORBITS"]
    pairs = orbits.g3_pairs()
    assert {key: item["repeat_disposition"] for key, item in pairs.items()} == REPEATS
    for item in pairs.values():
        assert item["witness_evidence_ref"] and item["confirmation_evidence_ref"]
        assert item["entry_state"] == "G3_WITNESS_BEFORE_STATE"


def _press(run: LeverRun, sequence) -> None:
    for index, (before, after) in enumerate(zip(sequence, sequence[1:]), start=1):
        if run.open:
            run.record(evidence_ref=f"E-{index}", transition_id=index, before=[[before]], after=[[after]])


def _run(sequence) -> LeverRun:
    run = LeverRun(run_id="R1", entity_id="E9", intervention={"action": "ACTION6"}, mask_law=None)
    _press(run, sequence)
    return run


def test_mechanism_and_condition_are_reported_separately():
    """D10: the ruled vocabulary beside the unchanged lever_class (moved-then-held is not never-moved)."""
    held = _run([0, 1, 1, 1])
    assert held.lever_class() == "ABSORBING"
    assert held.typing() == {"mechanism": "UNIFORM", "condition": None, "effective_presses": 1}
    never = _run([0, 0, 0])
    assert never.lever_class() == "ABSORBING"
    assert never.typing() == {"mechanism": "UNKNOWN", "condition": "SATURATED", "effective_presses": 0}
    toggle = _run([0, 1, 0, 1, 0])
    assert toggle.lever_class() == "TOGGLE" and toggle.typing()["mechanism"] == "TOGGLE"
    cycle = _run([0, 1, 2, 0, 1, 2, 0])
    assert cycle.lever_class() == "CYCLE" and cycle.typing()["mechanism"] == "CYCLE"
    diverged = _run([0, 1, 1, 2])
    assert diverged.lever_class() == "DIVERGENT" and diverged.typing()["mechanism"] == "UNKNOWN"
    assert _run([0, 1, 2]).typing() == {"mechanism": "UNKNOWN", "condition": None, "effective_presses": 2}


def test_a_state_that_offers_no_move_is_illegal_whatever_it_is_called(monkeypatch):
    """D11 (axiom A2, stated as the rule): a probe, an acceptable answer, or a declared end."""
    machine = _drive_level_two()
    monkeypatch.setattr(machine, "next_probe_capability", lambda: None)
    for operation in ("WAIT_FOR_DISCRIMINATING_EVIDENCE", "WAIT_FOR_SOMETHING_NOT_YET_NAMED"):
        monkeypatch.setattr(machine, "gate_view", lambda op=operation: {"next_operation": op})
        assert machine.legal_move_status()["legal"] is False, operation
    for operation in ("G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9", "WAIT_FOR_NEXT_SLICE"):
        monkeypatch.setattr(machine, "gate_view", lambda op=operation: {"next_operation": op})
        status = machine.legal_move_status()
        assert status["legal"] is True and status["move"] == "DECLARED_STATE", operation


def test_every_recorded_run_ends_in_a_legal_state():
    """D11: the general rule calls no recorded run's resting state a deadlock it was not."""
    for path in sorted(FIXTURES.glob("*_record.json.gz")):
        machine = replay(load_record(path), measure=False).machine
        status = machine.legal_move_status()
        assert status["legal"] is True, (path.name, status)


def test_the_controller_dossier_states_each_repeat_as_observed():
    """D7: the controller's dossier no longer claims a repeat reproduced what it did not."""
    machine = _drive_level_two()
    g3 = machine._adapters["G3-LEVERS"]
    ledger = g3._ensure_entity_ledger()
    texts = {ledger.member_to_entity[member]: answer.explanation for member, answer in g3._dossier_answers.items()}
    assert "it moved, then held" in texts["E0004"]
    for entity in ("E0005", "E0006", "E0007"):
        assert "changed the board again, to a third state" in texts[entity], entity
    assert not any("reproduced that residue" in text for text in texts.values())


def test_a_repeat_that_certifies_its_lever_does_not_wake_duck():
    """D7: G3 stays scripted; a typed repeat is not an anomaly. A boundary-deferred repeat still wakes Duck."""
    machine = _drive_level_two()
    g3 = machine._adapters["G3-LEVERS"]
    contradicted = next(item for item in g3._confirmation_records if item["entity_id"] == "E0004")
    assert wake_reason(machine, {"confirmation": contradicted}, {}) is None
    deferred = {**contradicted, "status": "BOUNDARY_DEFERRED", "confirmation_evidence_ref": "E-elsewhere"}
    assert wake_reason(machine, {"confirmation": deferred}, {}) == "a G3 confirmation was BOUNDARY_DEFERRED"

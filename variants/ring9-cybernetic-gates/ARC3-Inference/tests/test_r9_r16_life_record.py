"""R9-R16: the life record. A death forgets nothing, and every recorded fact knows its life.

Author: Claude (Alpha build seat), 2026-10-01. MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4 (D1-D4);
Director rulings 2026-10-01 (life record first; carry hypotheses only).

On the live exit-run records (``ring9-g4-exit-v1``): ft09 died at transition 88 and was reset at 89;
vc33 completed level 1 at transition 26. Each test failed before R9-R16.
"""
from __future__ import annotations

from inference.framework.card_builder import world_budgets
from inference.framework.life_record import PERSISTENCE, undeclared
from inference.framework.memory_store import MemoryStore
from inference.framework.record_replay import click_world_machine, decode_grid, load_record, replay
from inference.framework.recall import recall_slot
from test_g4b_relations import _predict, _take, start_g4b
from test_g4c_law import _described, _law
from test_r9_r15_replay_fidelity import FT09_EXIT, VC33_EXIT

RELATIONS, LAW = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"


def _reset_outcome(transition_id: int) -> dict:
    return {"transition_id": transition_id, "action": {"action": "RESET"}, "changed_cells": [],
            "boundary_event": {"state": "NOT_FINISHED", "actor": "SYSTEM_RESET", "reset": True}}


def test_d2_a_reset_before_g2_is_recorded_once_and_opens_the_next_life():
    """Before: a reset before G2 returned None, so the agent re-delivered it every turn and G3's
    ledger received it late, once G2 closed."""
    record = load_record(FT09_EXIT)
    machine = click_world_machine(decode_grid(record["initial_grid"]), ["ACTION6"])
    assert machine.target_journal.active_product("G2-COUNTER") is None
    row = machine.observe_system_reset(_reset_outcome(5))
    assert row is not None and row["kind"] == "RESET" and row["life"] == 2
    assert machine.observe_system_reset(_reset_outcome(5)) is None  # delivered once
    assert [item["kind"] for item in machine.transition_index] == ["RESET"]
    assert [item["life"] for item in machine.lives.summary()] == [1, 2]


def test_d1_ft09_records_the_death_and_life_two_and_recall_says_which_life():
    machine = replay(load_record(FT09_EXIT)).machine
    rows = machine.transition_index
    reset = next(row for row in rows if row["kind"] == "RESET")
    assert reset["transition_id"] == 89 and reset["life"] == 2
    assert {row["life"] for row in rows if row["transition_id"] <= 88} == {1}
    assert {row["life"] for row in rows if row["transition_id"] > 89} == {2}
    first, second = machine.lives.summary()
    assert (first["ended_by"], first["reset_transition"], first["last_transition"]) == ("GAME_OVER", 89, 88)
    assert second["ended_by"] is None and second["first_transition"] == 90
    lives = MemoryStore(machine).query("lives")
    assert lives["current_life"] == 2 and lives["total"] == 2
    assert world_budgets(machine)["life"] == 2
    slot = recall_slot(machine, {"gate": machine.gate_id, "entity": "E0056", "site": None})
    lines = [value for fact in slot["facts"] for kind, value in fact.items() if kind == "outcome"]
    assert lines and {line["life"] for line in lines} == {1, 2}  # E0056 was pressed in both lives


def test_d1_vc33_records_its_level_change():
    machine = replay(load_record(VC33_EXIT)).machine
    (life,) = machine.lives.summary()
    assert life["level"] == 1 and life["level_changes"] == [26] and life["ended_by"] is None
    assert machine.transition_index[-1]["level"] == 1 and machine.lives.level == 2


def test_d3_a_prediction_taken_on_a_death_is_not_evidence():
    machine, world = start_g4b()
    _predict(machine, "E0055")
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    outcome = world.step(capability["actions"][0])
    outcome["boundary_event"] = {**outcome["boundary_event"], "state": "GAME_OVER", "game_over": True}
    machine.record_outcome(probe, outcome)
    (prediction,) = machine._adapters[RELATIONS]._predictions
    assert prediction.status == "INDETERMINATE" and not prediction.graded
    assert machine._adapters[RELATIONS]._record.seen == {}  # nothing noted toward a missing condition
    card = machine._adapters[RELATIONS].compact_gate_view()
    assert card["progress"]["predictions"]["cut_off_by_death_or_level"] == ["P1"]
    assert "E0055" in card["progress"]["unpressed"]  # a voided press does not cover its lever
    _predict(machine, "E0055")  # Duck may predict the same press again
    _take(machine, world)
    assert machine._adapters[RELATIONS]._predictions[-1].status == "SUPPORTED"


def test_d3_a_law_test_cut_off_by_a_death_neither_certifies_nor_reopens():
    machine, world = start_g4b()
    _described(machine, world)
    _law(machine, "E0055")
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    outcome = world.step(capability["actions"][0])
    outcome["boundary_event"] = {**outcome["boundary_event"], "state": "GAME_OVER", "game_over": True}
    machine.record_outcome(probe, outcome)
    assert machine.gate_id == LAW and machine.target_journal.active_product(RELATIONS) is not None
    assert machine._adapters[RELATIONS]._reopened == []
    _law(machine, "E0055")  # the same test is still new: a voided test is not on the record
    _take(machine, world)
    assert machine.target_journal.active_product(LAW).payload["status"] == "COMPLETE"


def test_d4_every_gate_machine_field_has_a_declared_persistence_tier():
    machine = replay(load_record(FT09_EXIT)).machine
    assert undeclared(machine) == []
    for adapter in machine._adapters.values():
        assert undeclared(adapter) == [], type(adapter).__name__
    assert set(PERSISTENCE["CyberneticGateMachine"].values()) <= {"GAME", "LEVEL", "TRANSIENT"}

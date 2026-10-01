"""R9-R18 (G9-A): a finished level's levers carried to the next level as predictions it grades.

Author: Claude (Alpha build seat), 2026-10-01. MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4 (L2, L3);
Director rulings 2026-10-01 (carry hypotheses only; G0-G2 run again on each level).

On the live vc33 exit record, level 1 ended at transition 26 with two levers of one type (solid
squares of one integer, each click rewriting cells elsewhere). Level 2's spawn board, recorded in
the same transition, holds four objects of that type. Level 2 itself was never played, so its
grading is shown on a stand-in world. Each test failed before R9-R18.
"""
from __future__ import annotations

from inference.framework.carry import RECONFIRMED, UNCONFIRMED, scale_normalized_shape
from inference.framework.card_builder import world_model_digest
from inference.framework.controller_executor import next_owned_step
from inference.framework.memory_store import MemoryStore
from inference.framework.record_replay import load_record, lossless_outcome, replay
from test_r9_r15_replay_fidelity import FT09_EXIT, VC33_EXIT

SQUARE = [9, [1, 1], [1]]
RESPONSIVE = {(16, 0): (50, 30), (24, 0): (54, 30)}  # stand-in level 2: two squares rewrite a block elsewhere


def _vc33():
    result = replay(load_record(VC33_EXIT))
    return result.machine, result.grid


def _square(size: int, row: int = 0, col: int = 0) -> list[tuple[int, int]]:
    return [(row + r, col + c) for r in range(size) for c in range(size)]


def test_type_identity_ignores_position_and_scale_but_not_shape():
    assert scale_normalized_shape(_square(4, 24, 60)) == scale_normalized_shape(_square(2, 3, 3)) == (1, 1, (1,))
    ell = [(0, 0), (1, 0), (1, 1)]
    assert scale_normalized_shape(ell) == (2, 2, (1, 0, 1, 1))
    assert scale_normalized_shape([(r, c) for r, c in _square(4) if (r // 2 + c // 2) % 2 == 0]) == (2, 2, (1, 0, 0, 1))


def test_the_frozen_level_carries_each_levers_type_and_reaction():
    machine, _grid = _vc33()
    levers = {item["entity_id"]: item for item in machine.levels[0]["levers"]}
    for entity in ("E0004", "E0005"):
        assert levers[entity]["signatures"] == [SQUARE] and levers[entity]["locality"] == ["REMOTE"]


def test_level_two_freezes_its_carry_predictions_before_anything_is_clicked():
    machine, _grid = _vc33()
    view = MemoryStore(machine).query("carry")
    assert view["prior_level"] == 1 and view["declared_at_transition"] == 26
    assert [item["anchor"] for item in view["candidates"]] == [[16, 0], [24, 0], [36, 0], [44, 0]]
    assert {item["status"] for item in view["candidates"]} == {UNCONFIRMED}
    assert all(item["carried_from"] == ["E0004", "E0005"] and item["predicted_locality"] == ["REMOTE"]
               for item in view["candidates"])
    assert view["not_found"] == [] and view["not_carried"] == []
    assert "[carry] level 1 levers E0004, E0005 -> 4 same-type objects here (4 UNCONFIRMED)" in world_model_digest(machine)[1]


def _stand_in(action: dict, grid: list[list[int]], transition: int) -> list[list[int]]:
    changed = [[0, 90 - transition, grid[0][90 - transition], 4]]  # a bar that ticks on every action
    for (row, col), (r0, c0) in RESPONSIVE.items():
        if row <= action["row"] < row + 4 and col <= action["col"] < col + 4:
            changed += [[r, c, grid[r][c], (grid[r][c] + 1) % 10] for r in range(r0, r0 + 2) for c in range(c0, c0 + 6)]
    return changed


def test_the_levels_own_probes_grade_the_carry_and_g3_still_certifies_on_its_own_evidence():
    machine, grid = _vc33()
    transition = 26
    while (step := next_owned_step(machine)).owner == "CONTROLLER" and transition < 80:
        if step.kind == "ANSWER":
            machine.submit_answer(step.answer)
            continue
        probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
        transition += 1
        grid, outcome = lossless_outcome(grid, transition, step.action, _stand_in(step.action, grid, transition))
        machine.record_outcome(probe, outcome)
    grades = {item["anchor"][0]: (item["status"], item["evidence"]) for item in machine.carry.view()["candidates"]}
    assert grades[16][0] == grades[24][0] == RECONFIRMED and grades[16][1]["observed_locality"] == ["REMOTE"]
    assert grades[36] == ("FALSIFIED", {"transition_id": grades[36][1]["transition_id"], "observed_locality": [],
                                         "masked_changed_cells": 0})
    assert grades[44][0] == "FALSIFIED"
    assert all(evidence["transition_id"] > 26 for _status, evidence in grades.values())  # frozen before graded
    inventory = machine.target_journal.active_product("G3-LEVERS").payload
    assert len(inventory["lever_entities"]) == 2  # G3 witnessed the two responsive squares itself
    assert machine.gate_id == "G4.2-LEVER-ORBITS"


def test_a_click_before_the_mask_or_on_a_terminal_transition_grades_nothing():
    machine, grid = _vc33()
    click = {"action": "ACTION6", "row": 16, "col": 0}
    _after, outcome = lossless_outcome(grid, 27, click, [[50, 30, grid[50][30], 1]])
    assert machine.carry.observe(outcome, None) is None  # no counter mask on this level yet
    outcome["boundary_event"] = {"state": "GAME_OVER", "game_over": True}
    assert machine.carry.observe(outcome, [(0, 63)]) is None
    assert machine.carry.candidates[0]["status"] == UNCONFIRMED


def test_the_first_level_carries_nothing():
    machine = replay(load_record(FT09_EXIT)).machine
    assert machine.carry.candidates == [] and machine.carry.line() is None
    assert not any(line.startswith("[carry]") for line in world_model_digest(machine))

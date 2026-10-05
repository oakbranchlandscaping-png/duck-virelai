"""R9-R24: G4-B from the record, Duck's per-level G4 budget, and normal play after the gates.

Author: Claude (Alpha build seat), 2026-10-04. RULING_G4_CONTROLLER_FIRST_v2_2026-10-04 (Director-ruled).

Live (ring9-carry-vc33-v7, level 3): G4-B and G4-C took 24 actions and about 163 minutes of Duck time
(131 Duck turns, 95 cut off by the turn clock) and certified nothing: Duck's card named no lever state
(``state_now`` UNRECORDED on every row), its relations were refused unless they cited a supported
prediction, and every contradicted G4-C test reopened G4-B with no bound. The relations were already
on the record at t140 (DIAGNOSTIC_G4B_CONTROLLER_RELATIONS_v1).

Fixture: the v7 run's own record (165 transitions), driven as live up to the transition before G4-B's
first probe; Duck's recorded G4-B and G4-C answers are withheld, because under the ruling those gates
no longer ask Duck what the record answers. Duck's G4-C tests are written here from the card's own
template; their outcomes are stand-ins (an action that changes nothing), named where used.
Each test failed before R9-R24.
"""
from __future__ import annotations

import json

import pytest

from inference.agent.controller_turn import duck_turn_allowed, rest_if_no_legal_move
from inference.framework.annotation_lane import orientation_due, submit_notes
from inference.framework.controller_executor import next_owned_step, return_to_mu_if_stuck
from inference.framework.play_gate import DUCK_G4_TURNS_PER_LEVEL
from inference.framework.record_replay import (
    _answer_index, click_world_machine, decode_grid, load_record, lossless_outcome, merge_recorded_answer,
    record_like_live, record_protocol,
)
from inference.framework.virelai_gates import GateContractError

from tests.test_r9_r21_g3_contradicted import FIXTURES

VC33_CARRY_V7 = FIXTURES / "vc33_kaggle_carry_v7_record.json.gz"
RELATIONS, LAW, PLAY = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW", "PLAY-NORMAL"
G4B_FIRST = 141
WITHHELD = (RELATIONS, LAW)


class _Run:
    def __init__(self, machine, grid, transition):
        self.machine, self.grid, self.transition = machine, grid, transition

    def act(self, action, changed=(), boundary=None, decision=None):
        """One action through a fresh capability, recorded as live; ``changed`` is the transition's sparse change."""
        capability = self.machine.next_probe_capability()
        probe = self.machine.validate_probe({"probe_token": capability["probe_token"], **(decision or {})}, [action])
        self.transition += 1
        self.grid, outcome = lossless_outcome(self.grid, self.transition, action, list(changed), boundary)
        record_like_live(self.machine, probe, outcome, ["ACTION6"])
        return probe


def _drive_v7() -> _Run:
    """The v7 record as live, to the transition before G4-B's first probe; Duck's G4-B/G4-C answers withheld."""
    record = load_record(VC33_CARRY_V7)
    grid = decode_grid(record["initial_grid"])
    machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
    pending: dict[str, list] = {}
    for answer in record["answers"]:
        if answer["gate_id"] not in WITHHELD:
            pending.setdefault(answer["gate_id"], []).append(answer)

    def answers() -> None:
        while True:
            owned = next_owned_step(machine)
            if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
                machine.submit_answer(json.loads(json.dumps(owned.answer)))
                continue
            view = machine.gate_view()
            template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
            due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
            ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
            if template and (ready or (due and owned.owner == "DUCK" and queue)):
                machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
                continue
            return

    last = 0
    for step in record["steps"]:
        if step["transition_id"] >= G4B_FIRST:
            break
        answers()
        capability = machine.next_probe_capability()
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"))
        record_like_live(machine, probe, outcome, record["valid_actions"])
        last = step["transition_id"]
    answers()
    if orientation_due(machine):  # live, Duck oriented; the record keeps no orientation answer
        submit_notes(machine, [{"subject": "WORLD", "kind": "NAME", "text": "seven buttons on the bottom row"}],
                     source="ORIENTATION")
    return _Run(machine, grid, last)


def _certify_from_record(run: _Run) -> dict:
    step = next_owned_step(run.machine)
    assert (step.owner, step.kind, step.gate_id) == ("CONTROLLER", "ANSWER", RELATIONS)
    run.machine.submit_answer(json.loads(json.dumps(step.answer)))
    return step.answer


def _duck_freezes_a_new_test(run: _Run) -> dict:
    """Duck's G4-C test, written from the card's template on the first lever click not yet tested from this board."""
    template = run.machine.gate_view()["answer_template"]
    for row in run.machine._adapters[RELATIONS]._lever_rows():
        try:
            run.machine.submit_answer({**template, "action": row["click"], "expected": {row["entity_id"]: "STEPS"},
                                       "because": f"relation 0 says pressing {row['entity_id']} steps it from this board"})
            return row["click"]
        except GateContractError as exc:
            assert "already graded from this same board" in str(exc)
    raise AssertionError("every lever click was already tested from this board")


def test_d18_the_card_names_every_lever_state_from_the_levels_own_boards():
    """v7 live: 1,947 of 1,947 state_now read UNRECORDED; a press here never rewrites a whole region."""
    run = _drive_v7()
    rows = run.machine._adapters[RELATIONS]._lever_rows()
    states = {row["entity_id"]: row["state_now"] for row in rows}
    assert len(states) == 7 and "UNRECORDED" not in states.values()
    assert all(value.startswith("S") for value in states.values())


def test_d19_the_controller_certifies_g4b_from_the_record_and_the_gate_rederives_it():
    """Ruling G-1/G-2: no Duck turn; each relation cites its transitions; a stale answer is refused."""
    run = _drive_v7()
    step = next_owned_step(run.machine)
    assert (step.owner, step.kind) == ("CONTROLLER", "ANSWER")
    with pytest.raises(GateContractError, match="record does not certify"):
        run.machine.submit_answer({**step.answer, "answer_id": "G4B-REC-stale"})
    run.machine.submit_answer(json.loads(json.dumps(step.answer)))
    product = run.machine.target_journal.active_product(RELATIONS).payload
    assert product["status"] == "COMPLETE" and product["certified_by"] == "RECORD"
    record = product["from_record"]
    assert record["shared_regions"] == [["E0010", "E0011"], ["E0012", "E0013"]]  # two controls of one region, never a coupling
    e0013 = next(item for item in record["relations"] if item["levers"][0] == "E0013")
    assert {89, 123} <= set(e0013["transitions"]) and "E0015" in e0013["claim"]  # E0013 reaches E0015
    assert run.machine.gate_id == LAW  # G4-C asks Duck for one new test, nothing else


def test_d20_d21_duck_has_a_per_level_budget_and_a_spent_budget_closes_unresolved_without_a_loop(tmp_path):
    """Each contradicted test reopens G4-B, which the controller re-certifies at once; the budget ends the loop."""
    run = _drive_v7()
    _certify_from_record(run)
    log = tmp_path / "analyzer.txt"
    for turn in range(DUCK_G4_TURNS_PER_LEVEL):
        assert run.machine.gate_id == LAW and duck_turn_allowed(run.machine, log)
        click = _duck_freezes_a_new_test(run)
        run.act(click)  # stand-in outcome: the press changes nothing, so the STEPS test is contradicted
        assert run.machine._adapters[LAW]._tests[-1].status == "CONTRADICTED"
        assert run.machine.gate_id == RELATIONS  # reopened ...
        _certify_from_record(run)  # ... and re-certified from the larger record, with no Duck turn
    assert run.machine.duck_budget.snapshot()["used"] == DUCK_G4_TURNS_PER_LEVEL
    assert not duck_turn_allowed(run.machine, log)  # the next turn would exceed the budget
    law = run.machine.target_journal.active_product(LAW).payload
    assert law["status"] == "UNRESOLVED" and "budget" in law["unresolved_reason"]
    assert run.machine.gate_id == PLAY and run.machine.legal_move_status()["legal"] is True
    assert "closes UNRESOLVED" in log.read_text()


def test_d22_after_the_gates_duck_plays_normally_and_the_harness_labels_a_known_no_op(tmp_path):
    """Normal play: any available action, receipted FREE_PLAY, recorded; R-8 blocks a repeat that changed nothing."""
    run = _drive_v7()
    _certify_from_record(run)
    for _ in range(DUCK_G4_TURNS_PER_LEVEL + 1):
        if duck_turn_allowed(run.machine, tmp_path / "log.txt"):
            run.act(_duck_freezes_a_new_test(run))
            _certify_from_record(run)
    assert run.machine.gate_id == PLAY
    card = run.machine.gate_view()
    assert card["next_operation"] == "QUERY_NEXT_PROBE" and card["subject"]["levers"]
    assert "UNRECORDED" not in {row["state_now"] for row in card["subject"]["levers"]}
    capability = run.machine.next_probe_capability()
    assert capability["purpose"] == "GUIDED_ACTION" and capability["admissible_actions"] == ["ACTION6"]
    spot = {"action": "ACTION6", "row": 2, "col": 2}
    run.act(spot, decision={"intent": "try an empty corner"})  # stand-in: nothing changes
    with pytest.raises(GateContractError, match="Blocked by the harness, not the game"):
        capability = run.machine.next_probe_capability()
        run.machine.validate_probe({"probe_token": capability["probe_token"]}, [spot])
    row = run.machine.transition_index[-1]
    assert row["gate_id"] == PLAY and run.machine._adapters[PLAY]._events[-1]["receipt"] == "FREE_PLAY"
    assert next_owned_step(run.machine).owner == "DUCK"


def test_d22_a_level_won_in_play_is_receipted_free_play_and_the_next_level_opens_its_own_ladder_and_budget(tmp_path):
    run = _drive_v7()
    _certify_from_record(run)
    while duck_turn_allowed(run.machine, tmp_path / "log.txt"):
        run.act(_duck_freezes_a_new_test(run))
        _certify_from_record(run)
    win = {"action": "ACTION6", "row": 3, "col": 3}
    run.act(win, changed=[[5, 5, run.grid[5][5], (run.grid[5][5] + 1) % 10]],
            boundary={"state": "NOT_FINISHED", "level_before": 3, "level_after": 4, "level_completed": True})
    model = run.machine.levels[-1]
    assert model["level"] == 3 and model["win"]["receipt"] == "FREE_PLAY" and model["win"]["gate_id"] == PLAY
    assert model["duck_g4_budget"]["used"] == DUCK_G4_TURNS_PER_LEVEL
    assert run.machine.gate_id == "G0-ACTION-METADATA" and run.machine.duck_budget.snapshot()["used"] == 0


def test_d22_a_gate_with_no_legal_move_rests_the_level_in_play_and_mu_is_checked_once_at_rest(monkeypatch):
    run = _drive_v7()
    machine = run.machine
    real = machine.legal_move_status
    monkeypatch.setattr(machine, "legal_move_status", lambda: {**real(), "legal": False, "reason": "stand-in"})
    assert "rests in normal play" in rest_if_no_legal_move(machine)
    monkeypatch.setattr(machine, "legal_move_status", real)
    assert machine.gate_id == PLAY and machine.legal_move_status()["legal"] is True
    assert return_to_mu_if_stuck(machine) is None and machine.mu.entries["E0028"]["status"] in {"OPEN", "ABSENT"}
    assert machine._adapters[PLAY].rest_check_due() is False  # checked once for this set of products

"""WO-L2a: the level census, a read-only projection of the gate record into the v2 world model.

Author: Claude (Alpha build seat), 2026-10-10. Sol's reviews of WO-L2-00 and of the WO-L2a interface.

Fixtures are development records (ruling 10): the v2 rehearsal replays used by the G3 lifecycle slice,
cut at an early G1 stop, at the G2 close and at the first G3 NAV step, and the WO-L1a click-only world.
Premise lines marked "present tree" assert what is true without this module: the gate record's only
object ledger (G3's) does not exist before G3, so nothing else censuses a level that stops early.
"""
from __future__ import annotations

import copy
import hashlib
import pickle
from pathlib import Path

import pytest

from inference.framework.controller_executor import controller_answer
from inference.framework.library_census import (
    ExecutionRecord, board_cut, compile_level, compile_world_model, record_check,
)
from inference.framework.record_replay import decode_grid, load_record, replay
from inference.framework.virelai_gates import CyberneticGateMachine, EgoGateMachine
from inference.framework.world_model_v2 import WorldModelV2Error, seal
from test_g3_hybrid_lifecycle_replay import K008, K013, K013_LIVE_LEVERS
from test_l1a_pointer_g1_contract import GRID


def _digest(machine) -> str:
    return hashlib.sha256(pickle.dumps(machine)).hexdigest()


def _cut(path, transition_id):
    record = load_record(path)
    cut = next(i for i, step in enumerate(record["steps"]) if step["transition_id"] == transition_id)
    machine = replay(record, max_steps=cut, measure=False).machine
    execution = ExecutionRecord(
        entry_board=tuple(tuple(row) for row in decode_grid(record["initial_grid"])), entry_level=1,
        valid_actions=tuple(record["valid_actions"]),
        executed=tuple(step["action"]["action"] for step in record["steps"][:cut]),
    )
    return machine, execution


def _model(machine, execution, reason="BUDGET_STOP"):
    before = _digest(machine) if machine is not None else None
    model = seal(compile_world_model(machine, execution, game_id="g", run_stem="g_p0", persist_reason=reason))
    if machine is not None:
        assert _digest(machine) == before  # a census read leaves the gate machine byte-identical
    return model


@pytest.fixture(scope="module")
def k008_g1():
    return _cut(K008, 29)  # G1 is still open after 28 recorded transitions


@pytest.fixture(scope="module")
def k008_g2():
    return _cut(K008, 38)  # G2 closed at 37; a reset at 31 opened life 2


@pytest.fixture(scope="module")
def k013_g3():
    return _cut(K013, 401)  # the CLICK pass is done; the first NAV step is next


def _roles(model, name):
    return [role for role in model["levels"][0]["certified"]["roles"] if role["role"] == name]


def _gaps(model, reason):
    return [gap for gap in model["levels"][0]["gaps"] if gap["reason"] == reason]


def test_a_zero_action_click_level_is_censused_from_its_entry_board():
    machine = CyberneticGateMachine(valid_actions=["ACTION5", "ACTION6", "ACTION7"], initial_grid=GRID)
    for _ in range(2):  # G0 and G1 close on the controller's certified answers, at zero actions
        machine.submit_answer(controller_answer(machine, machine.gate_view())[0])
    assert machine.gate_id == "G2-COUNTER" and not machine.transition_index
    execution = ExecutionRecord(entry_board=GRID, entry_level=1, valid_actions=("ACTION5", "ACTION6", "ACTION7"))
    model = _model(machine, execution)
    level = model["levels"][0]
    assert level["entry"]["source"] == "INITIAL_FRAME" and "transition_id" not in level["entry"]
    components = board_cut(GRID, node=0, level=1).regions
    assert len(level["observation"]["tracks"]) == len(components)  # every entry-board object, counter cells too
    assert all(track["segments"][0]["first"] == {"source": "INITIAL_FRAME"} for track in level["observation"]["tracks"])
    (ego,) = _roles(model, "EGO")
    assert ego["subject"] == "POINTER_NULL_LOCUS" and ego["identity"]["status"] == "NOT_APPLICABLE"
    assert {gap["subject"] for gap in _gaps(model, "NOT_BUILT")} >= {"ACTION5", "ACTION7"}
    assert machine._adapters["G3-LEVERS"].entity_ledger is None  # the census never initializes G3
    assert level["accounting"] == {"status": "ACCOUNTED", "missing": []}


def test_an_observed_board_with_no_gate_machine_is_still_censused():
    execution = ExecutionRecord(entry_board=GRID, entry_level=1, valid_actions=("ACTION6",))
    model = _model(None, execution, reason="CANCELLED")
    assert model["manifest"]["status"] == "OBSERVED_NEVER_ACTED" and model["manifest"]["gate_machine"] is False
    assert {gate["disposition"] for gate in model["levels"][0]["certified"]["gates"]} == {"NOT_STARTED"}
    assert len(model["levels"][0]["observation"]["tracks"]) == len(board_cut(GRID, node=0, level=1).regions)
    acted = ExecutionRecord(entry_board=GRID, entry_level=1, valid_actions=("ACTION6",), executed=("ACTION6",))
    level = _model(None, acted, reason="CRASH")["levels"][0]
    assert level["record"]["journal_check"]["missing"] == [1]  # an executed action the gate never recorded
    assert level["accounting"]["status"] == "NOT_ACCOUNTED"


def test_an_early_g1_stop_has_a_census_from_level_entry(k008_g1):
    machine, execution = k008_g1
    assert machine.gate_id == "G1-EGO"
    assert machine._adapters["G3-LEVERS"].entity_ledger is None  # present tree: no object ledger yet
    level = _model(machine, execution)["levels"][0]
    tracks = level["observation"]["tracks"]
    assert tracks and all(track["segments"][0]["first"]["source"] in {"INITIAL_FRAME", "TRANSITION"} for track in tracks)
    assert any(track["segments"][0]["first"]["source"] == "INITIAL_FRAME" for track in tracks)
    assert any(len(track["segments"]) > 1 for track in tracks)  # objects the G1 probes changed
    assert level["record"]["transition_ids"] == list(range(1, 29))
    assert {gate["gate_id"]: gate["disposition"] for gate in level["certified"]["gates"]}["G1-EGO"] == "IN_PROGRESS"
    assert all(gap["reason"] == "FOUNDATION_UNRESOLVED" for gap in level["gaps"]
               if gap["archetype_question"] == "Which roles does this object hold?")


def test_lives_are_never_joined_on_identical_spawn_pixels(k008_g2):
    machine, execution = k008_g2
    level = _model(machine, execution)["levels"][0]
    tracks = level["observation"]["tracks"]
    assert {track["life"] for track in tracks} == {1, 2}
    ends = {track["end"]["reason"] for track in tracks if track["end"]}
    assert ends == {"DEPARTED", "LIFE_ENDED"}  # departed and life-ended objects stay in the census
    reborn = [track for track in tracks if "possible_correspondence" in track]
    assert reborn and any(track["possible_correspondence"] for track in reborn)
    assert all(track["track_id"].startswith("O-L1-P2-") for track in reborn)
    unresolved = {gap["subject"] for gap in level["gaps"] if gap["reason"] == "IDENTITY_UNRESOLVED"}
    assert {track["track_id"] for track in reborn} <= unresolved


def test_the_counter_is_a_certified_mask_not_every_overlapping_object(k008_g2):
    machine, execution = k008_g2
    model = _model(machine, execution)
    mask = set(map(tuple, machine.counter.mask_law.cells))
    steps = []
    for track in model["levels"][0]["observation"]["tracks"]:
        bbox = track["segments"][0]["bbox"]
        if any((r, c) in mask for r in range(bbox[0], bbox[2] + 1) for c in range(bbox[1], bbox[3] + 1)):
            steps.append(track["track_id"])
    assert len(steps) > 1  # present tree: several objects overlap the counter's mask
    (counter,) = _roles(model, "COUNTER")
    assert counter["subject"] == "MASK" and counter["mask_cell_count"] == len(mask)
    assert counter["identity"]["status"] in {"EXACT_ONE_TO_ONE", "UNRESOLVED"}
    if counter["identity"]["status"] == "UNRESOLVED":
        assert any(gap["subject"] == "COUNTER" for gap in _gaps(model, "IDENTITY_UNRESOLVED"))


def test_a_g3_witness_certifies_a_lever_before_the_inventory(k013_g3):
    machine, execution = k013_g3
    assert machine.target_journal.active_product("G3-LEVERS") is None  # no inventory yet
    model = _model(machine, execution)
    levers = _roles(model, "LEVER")
    assert {role["entity_id"] for role in levers} == K013_LIVE_LEVERS
    assert all(role["witness_refs"] and role["inventory_status"] == "PENDING" for role in levers)
    roles = {role["role"] for role in model["levels"][0]["certified"]["roles"]}
    assert roles <= {"EGO", "COUNTER", "LEVER"}  # nothing else, and never INERT
    joined = [track for track in model["levels"][0]["observation"]["tracks"] if track["g3_join"]["entity_id"]]
    assert len({track["g3_join"]["entity_id"] for track in joined}) == len(joined)  # one-to-one


def test_a_record_mismatch_is_reported_never_papered_over(k008_g2):
    machine, execution = k008_g2
    short = ExecutionRecord(execution.entry_board, 1, execution.valid_actions, execution.executed[:-1])
    level = _model(machine, short)["levels"][0]
    check = level["record"]["journal_check"]
    assert check["extra"] == [len(execution.executed)] and not check["ok"]
    assert level["accounting"]["status"] == "NOT_ACCOUNTED" and "RECORD_MISMATCH" in level["accounting"]["missing"]
    renamed = ExecutionRecord(execution.entry_board, 1, execution.valid_actions,
                              ("ACTION9",) + execution.executed[1:])
    assert _model(machine, renamed)["levels"][0]["record"]["journal_check"]["renamed"] == [1]


def test_the_census_is_deterministic(k013_g3):
    machine, execution = k013_g3
    assert _model(machine, execution)["content_sha256"] == _model(machine, execution)["content_sha256"]


def test_a_duck_declared_footprint_is_a_hint_not_an_identity(k008_g2, monkeypatch):
    machine, execution = k008_g2
    track = _model(machine, execution)["levels"][0]["observation"]["tracks"][0]
    cells = [(r, c) for r in range(track["segments"][-1]["bbox"][0], track["segments"][-1]["bbox"][2] + 1)
             for c in range(track["segments"][-1]["bbox"][1], track["segments"][-1]["bbox"][3] + 1)]
    monkeypatch.setattr(EgoGateMachine, "embodied_ego_binding",
                        lambda self: (tuple(cells), "DUCK_DECLARED_SCOPE_FALLBACK"))
    model = _model(machine, execution)
    (ego,) = _roles(model, "EGO")
    assert ego["binding_source"] == "DUCK_DECLARED_SCOPE_FALLBACK" and ego["identity"]["status"] == "UNRESOLVED"
    assert any(gap["subject"] == "EGO" for gap in _gaps(model, "IDENTITY_UNRESOLVED"))


CARRY = Path(__file__).parent / "fixtures" / "vc33_kaggle_carry_v7_record.json.gz"  # one level change at 26


def _board_sha(grid) -> str:
    return hashlib.sha256(repr([list(row) for row in grid]).encode()).hexdigest()


def test_a_frozen_census_belongs_to_the_level_that_just_ended(monkeypatch):
    """Sol's H1 finding: ``LifeRecord.tag`` moves ``machine.lives.level`` to the next level before
    ``_advance_level`` runs, while the board, rows and products still belong to the level that ended."""
    record = load_record(CARRY)
    boundary = next(step for step in record["steps"] if (step.get("boundary") or {}).get("level_completed"))
    executed = tuple(step["action"]["action"] for step in record["steps"]
                     if step["transition_id"] <= boundary["transition_id"])
    execution = ExecutionRecord(tuple(tuple(row) for row in decode_grid(record["initial_grid"])), 1,
                                tuple(record["valid_actions"]), executed)
    captured = {}
    original = CyberneticGateMachine._advance_level

    def hooked(self, outcome):  # where H1 will sit: before freeze_level and the rebuild
        before = _digest(self)
        captured["lives_level"] = self.lives.level
        with pytest.raises(ValueError, match="level_before"):
            compile_level(self, execution, state="FROZEN")  # a frozen census never reads the level itself
        captured["census"] = compile_level(self, execution, state="FROZEN",
                                           level=outcome["boundary_event"]["level_before"])
        captured["products"] = {row["gate_id"] for row in self.completed_gate_rows()}
        assert _digest(self) == before
        original(self, outcome)

    monkeypatch.setattr(CyberneticGateMachine, "_advance_level", hooked)
    machine = replay(record, measure=False).machine
    frozen = captured["census"]
    assert captured["lives_level"] == 2 and frozen["level"] == 1  # the machine already says 2; the census says 1
    assert frozen["state"] == "FROZEN" and frozen["entry"]["source"] == "INITIAL_FRAME"
    assert frozen["entry"]["board_sha256"] == _board_sha(decode_grid(record["initial_grid"]))
    assert frozen["record"]["transition_ids"] == list(range(1, boundary["transition_id"] + 1))
    assert {r["gate_id"] for r in frozen["receipts"]["products"].values()} == captured["products"]
    assert set(machine.levels[0]["products"]) == captured["products"]  # the same products freeze_level froze
    model = seal(compile_world_model(machine, execution, game_id="g", run_stem="g_p0",
                                     persist_reason="RUN_END", frozen_levels=[frozen]))
    opened = model["levels"][1]
    assert [level["level"] for level in model["levels"]] == [1, 2] and opened["state"] == "OPEN"
    assert opened["entry"] == {**opened["entry"], "source": "LEVEL_ENTRY", "after_transition": boundary["transition_id"]}
    assert opened["entry"]["board_sha256"] == _board_sha(machine.ego._initial_grid) != frozen["entry"]["board_sha256"]
    assert not {t["track_id"] for t in opened["observation"]["tracks"]} & {t["track_id"] for t in frozen["observation"]["tracks"]}


def test_an_inconclusive_attribution_is_not_an_untried_object(k013_g3):
    machine, execution = k013_g3
    lifecycle = machine._adapters["G3-LEVERS"].lifecycle_journal
    ambiguous = {entity for entity, item in lifecycle.entities.items() if item.state == "AMBIGUOUS"}
    assert ambiguous  # present tree: four objects were clicked and their attribution stayed unresolved
    model = _model(machine, execution)
    lever_questions = {gap["subject"]: gap["reason"] for gap in model["levels"][0]["gaps"]
                       if gap["archetype_question"] == "Is this object a lever?"}
    assert {lever_questions[entity] for entity in ambiguous} == {"INCONCLUSIVE"}
    untried = [gap for gap in model["levels"][0]["gaps"] if gap["archetype_question"] == "Which roles does this object hold?"]
    assert untried and {gap["reason"] for gap in untried} == {"NOT_REACHED"}


def test_a_census_role_with_a_fabricated_witness_fails_validation(k013_g3):
    machine, execution = k013_g3
    model = _model(machine, execution)
    receipts = model["levels"][0]["receipts"]
    lever = _roles(model, "LEVER")[0]
    assert all(receipts["witnesses"][ref]["entity_id"] == lever["entity_id"] for ref in lever["witness_refs"])
    forged = copy.deepcopy(model)
    del forged["content_sha256"]
    next(r for r in forged["levels"][0]["certified"]["roles"] if r["role"] == "LEVER")["witness_refs"] = ["W-forged"]
    with pytest.raises(WorldModelV2Error, match="resolves to no witness receipt"):
        seal(forged)


def test_a_duplicated_transition_is_a_record_mismatch(k008_g2):
    rows = [{"transition_id": 1, "action": {"action": "ACTION1"}}, {"transition_id": 1, "action": {"action": "ACTION1"}}]
    assert record_check(rows, ("ACTION1",))["duplicated"] == [1] and not record_check(rows, ("ACTION1",))["ok"]
    machine, execution = k008_g2
    doubled = copy.deepcopy(machine)
    doubled.transition_index.append(dict(doubled.transition_index[-1]))
    level = _model(doubled, execution)["levels"][0]
    assert level["record"]["journal_check"]["duplicated"] == [machine.transition_index[-1]["transition_id"]]
    assert level["accounting"]["status"] == "NOT_ACCOUNTED"

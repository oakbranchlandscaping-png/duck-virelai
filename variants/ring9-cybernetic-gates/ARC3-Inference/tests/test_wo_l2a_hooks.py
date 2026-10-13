"""WO-L2a hooks: H1 freezes an ended level with its journal check pending; H2 reconciles and writes.

Author: Claude (Alpha build seat), 2026-10-11. Sol's ruling on the hooks (relayed by the Director): "H1 should
freeze the ended level's census without importing harness history into the gate machine, with an explicit
pending check and no ACCOUNTED claim. H2 must reconcile every frozen and open level against the complete
execution history before writing the final model ... Test a level advance followed by finalization,
including a mismatch on the frozen level."

Fixture: the carry-v7 development record (ruling 10). One level change at transition 26; the replay stops
at 27, so the machine holds level 1 frozen (LEVER E0004 witnessed at t7, E0005 at t9) and level 2 open.
The solver tests drive the real ``_HarnessGameSession.play``; only the analyzer is a stand-in.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import arcengine
import pytest

from inference.framework import library_census, world_model_v2
from inference.framework.library_census import ExecutionRecord, assign_mismatches, compile_world_model
from inference.framework.record_replay import decode_grid, load_record, replay
from replay_checkpoints import checkpoint
from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.world_model_v2 import seal, validate
from test_duck_native_observer import _Game

CARRY = Path(__file__).parent / "fixtures" / "vc33_kaggle_carry_v7_record.json.gz"
BOUNDARY = 26  # the transition that completed level 1


def _carry():
    record = load_record(CARRY)
    machine = checkpoint(CARRY, measure=False).machine  # the shared checkpoint layer: a fresh copy
    names = tuple(step["action"]["action"] for step in record["steps"] if step["transition_id"] <= BOUNDARY)
    board = tuple(tuple(row) for row in decode_grid(record["initial_grid"]))
    return machine, board, tuple(record["valid_actions"]), names


@pytest.fixture(scope="module")
def carry():
    return _carry()


def _execution(carry, names=None):
    _machine, board, actions, executed = carry
    return ExecutionRecord(board, 1, actions, executed if names is None else names)


def _final(carry, names=None, reason="RUN_END"):
    machine = carry[0]
    return seal(compile_world_model(machine, _execution(carry, names), game_id="g", run_stem="g_p0",
                                    persist_reason=reason, frozen_levels=machine.level_censuses))


def _level(model, number):
    return next(level for level in model["levels"] if level["level"] == number)


def _levers(level):
    return sorted(role["entity_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER")


def _renamed(names, transition_id, name="ACTION5"):
    return tuple(name if index + 1 == transition_id else item for index, item in enumerate(names))


def test_h1_freezes_the_ended_level_with_its_check_pending(carry):
    machine = carry[0]
    (frozen,) = machine.level_censuses
    assert machine.lives.level == 2 and len(machine.levels) == 1  # the advance happened, and was rebuilt
    assert frozen["level"] == 1 and frozen["state"] == "FROZEN"
    assert frozen["record"]["journal_check"] == {"status": "PENDING"}
    assert frozen["accounting"]["status"] == "NOT_ACCOUNTED"
    assert "JOURNAL_CHECK_PENDING" in frozen["accounting"]["missing"]
    assert frozen["record"]["transition_ids"] == list(range(1, BOUNDARY + 1))
    assert _levers(frozen) == ["E0004", "E0005"]


def test_h2_with_a_matching_history_checks_every_level(carry):
    model = _final(carry)
    assert model["manifest"]["journal_check"] == "RECONCILED"
    assert [level["level"] for level in model["levels"]] == [1, 2]
    for level in model["levels"]:
        check = level["record"]["journal_check"]
        assert check["status"] == "CHECKED" and check["ok"] is True
        assert check["recorded"] == check["executed"] == BOUNDARY
        assert "JOURNAL_CHECK_PENDING" not in level["accounting"]["missing"]
    assert _level(model, 1)["accounting"] == {"status": "ACCOUNTED", "missing": []}
    assert _levers(_level(model, 1)) == ["E0004", "E0005"]
    assert carry[0].level_censuses[0]["record"]["journal_check"] == {"status": "PENDING"}  # H2 never edits H1's copy


@pytest.mark.parametrize(("transition_id", "lost", "kept"), [(7, "E0004", "E0005"), (9, "E0005", "E0004")])
def test_a_mismatch_on_the_frozen_level_removes_only_the_claims_it_grounds(carry, transition_id, lost, kept):
    model = _final(carry, _renamed(carry[3], transition_id))
    first, second = _level(model, 1), _level(model, 2)
    check = first["record"]["journal_check"]
    assert check["status"] == "CHECKED" and check["ok"] is False and check["renamed"] == [transition_id]
    assert first["accounting"]["status"] == "NOT_ACCOUNTED" and "RECORD_MISMATCH" in first["accounting"]["missing"]
    (gap,) = [g for g in first["gaps"] if g["reason"] == "RECORD_MISMATCH" and g["source"] == "record_check"]
    assert gap["renamed"] == [transition_id]
    assert _levers(first) == [kept]
    assert any(g["subject"] == lost and g["reason"] == "RECORD_MISMATCH" and g["transitions"] == [transition_id]
               for g in first["gaps"])
    assert second["record"]["journal_check"]["ok"] is True  # the open level is unaffected


def test_mismatched_ids_go_to_the_level_that_owns_them():
    rows = [{"transition_id": t, "level": 1} for t in (1, 2, 3)] + [{"transition_id": t, "level": 2} for t in (6, 7)]
    check = {"missing": [2, 4, 9], "extra": [7], "duplicated": [], "renamed": [3]}
    owned = assign_mismatches(check, rows, [1, 2])
    assert owned[1] == {"missing": [2], "extra": [], "duplicated": [], "renamed": [3]}
    assert owned[2] == {"missing": [4, 9], "extra": [7], "duplicated": [], "renamed": []}  # 4: the next span
    assert assign_mismatches(check, rows, [2])[2]["renamed"] == [3]  # a level the census lacks: the last one


def test_an_interim_model_validates_and_claims_nothing(carry):
    machine = carry[0]
    model = seal(compile_world_model(machine, _execution(carry), game_id="g", run_stem="g_p0",
                                     persist_reason="LEVEL_ADVANCE", frozen_levels=machine.level_censuses,
                                     reconcile_journal=False))
    validate(model)
    assert model["manifest"]["journal_check"] == "PENDING"
    for level in model["levels"]:
        assert level["record"]["journal_check"] == {"status": "PENDING"}
        assert level["accounting"]["status"] == "NOT_ACCOUNTED"


def test_a_census_failure_is_recorded_and_the_level_still_advances(monkeypatch):
    def broken(machine, *, level_before):
        raise RuntimeError("census broke")

    monkeypatch.setattr(library_census, "freeze_level_census", broken)
    carry = _carry()
    machine = carry[0]
    assert machine.level_censuses == [{"level": 1, "census_failed": "RuntimeError: census broke"}]
    assert len(machine.levels) == 1 and machine.lives.level == 2
    model = _final(carry, _renamed(carry[3], 7))
    assert model["manifest"]["census_failures"] == [{"level": 1, "census_failed": "RuntimeError: census broke"}]
    assert [level["level"] for level in model["levels"]] == [2]
    assert _level(model, 2)["record"]["journal_check"]["renamed"] == [7]  # level 1's ids fall to the last level


# ---- the solver: the real play() path -------------------------------------------------------------


class _PlayedGame(_Game):
    def __init__(self, names=()):
        super().__init__()
        self.game_run.__dict__.update(
            solver_note=None, solver_analysis_html=None, final_score=None, levels_completed=0,
            number_of_levels=1, actions_per_level=[],
        )
        self.game_run.history = [SimpleNamespace(action=SimpleNamespace(id=getattr(arcengine.GameAction, name)))
                                 for name in names]

    def finish_game(self):
        self.game_run.final_score = 0.0


def _turn(**fields):
    return SimpleNamespace(**{"fatal_failure": None, "controlled_stop": "", "planned_stop": "",
                              "retryable_failure": False, "yielded_control": False, "step_executed": False,
                              **fields})


def _play(tmp_path, game, analyze):
    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    analyzer = SimpleNamespace(generated_tokens=0)
    analyzer.analyze = lambda *a, **k: analyze(analyzer)
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=analyzer, game_index=0, pass_index=0,
        state_path=tmp_path / "state.json", transcript_path=tmp_path / "t.txt", analysis_html_relpath="a.html",
        stop_event=threading.Event(), viewer_data_path=tmp_path / "v.json",
    )
    session.play()
    return tmp_path / "virelai" / solver._run_stem("fixture", 0)


def _read(folder):
    model = json.loads((folder / "world_model.json").read_text())
    world_model_v2.read_world_model(model)  # the version-aware reader validates it
    return model


def _warnings(folder):
    path = folder / "observer_warnings.jsonl"
    return [json.loads(line)["event"] for line in path.read_text().splitlines()] if path.exists() else []


def test_a_crash_after_a_level_advance_still_writes_the_reconciled_model(tmp_path, carry):
    def crash(analyzer):
        analyzer._gate_machine = carry[0]
        raise RuntimeError("analyzer blew up")

    game = _PlayedGame(_renamed(carry[3], 9))
    folder = _play(tmp_path, game, crash)
    assert game.game_run.state == "crashed"
    assert game.game_run.solver_note == "error: RuntimeError: analyzer blew up"  # never masked
    model = _read(folder)
    assert model["manifest"]["persist_reason"] == "CRASH" and model["manifest"]["journal_check"] == "RECONCILED"
    first = _level(model, 1)
    assert first["record"]["journal_check"]["renamed"] == [9]
    assert any(g["reason"] == "RECORD_MISMATCH" and g["source"] == "record_check" for g in first["gaps"])
    assert _levers(first) == ["E0004"]
    assert not [event for event in _warnings(folder) if event.startswith("WORLD_MODEL")]


def test_the_interim_write_precedes_the_final_one(tmp_path, carry, monkeypatch):
    writes = []
    original = world_model_v2.write_canonical

    def recording(payload, directory):
        writes.append((payload["manifest"]["persist_reason"], payload["manifest"]["journal_check"]))
        return original(payload, directory)

    monkeypatch.setattr(world_model_v2, "write_canonical", recording)
    turns = []

    def analyze(analyzer):
        turns.append(1)
        if len(turns) == 1:
            analyzer._gate_machine = carry[0]  # this turn's probe advanced the level: H1 froze level 1
            return _turn()
        return _turn(planned_stop="done")

    folder = _play(tmp_path, _PlayedGame(carry[3]), analyze)
    assert writes == [("LEVEL_ADVANCE", "PENDING"), ("RUN_END", "RECONCILED")]
    model = _read(folder)
    assert _level(model, 1)["accounting"] == {"status": "ACCOUNTED", "missing": []}


def test_no_observed_board_means_no_census_only_an_event(tmp_path, monkeypatch):
    monkeypatch.setattr(_HarnessGameSession, "_ensure_game_observer", lambda self: None)
    game = _PlayedGame()
    folder = tmp_path / "virelai" / HarnessSolver()._run_stem("fixture", 0)

    def stop(analyzer):
        return _turn(planned_stop="done")

    _play(tmp_path, game, stop)
    assert not (folder / "world_model.json").exists()
    assert _warnings(folder) == ["WORLD_MODEL_NOT_OBSERVED"]

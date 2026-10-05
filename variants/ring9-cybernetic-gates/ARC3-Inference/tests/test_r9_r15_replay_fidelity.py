"""R9-R15: the replay instrument matches the live G4 exit run, and the controller's actions say so.

Author: Claude (Alpha build seat), 2026-09-30. Findings F-R1, F-R2 and F-R3 of
REVIEW_RING9_G4_EXIT_KAGGLE_V1_2026-09-30. Each test failed before its fix.

The two fixtures are the live ``ring9-g4-exit-v1`` records (source ``d2bf323``), built from the
run's own artifacts with ``tools/record_from_artifacts.py``.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from inference.framework.controller_executor import ladder_end
from inference.framework.record_replay import load_record, replay
from test_duck_native_observer import _Game, _RecordingObserver, _session
from test_memory_m2 import Run

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FT09_EXIT = FIXTURES / "ft09_kaggle_exit_v1_record.json.gz"
VC33_EXIT = FIXTURES / "vc33_kaggle_exit_v1_record.json.gz"
_TOOL = Path(__file__).resolve().parents[1] / "tools" / "record_from_artifacts.py"
_SPEC = importlib.util.spec_from_file_location("record_from_artifacts_r15", _TOOL)
record_tool = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(record_tool)

LIVE_LEVEL_WIN = {
    "done": False, "game_over": False, "level_after": 2, "level_before": 1, "level_completed": True,
    "run_complete": False, "state": "NOT_FINISHED",
}


def _outcome(transition_id: int, boundary: dict) -> dict:
    return {
        "transition_id": transition_id, "action": {"action": "ACTION6", "row": 0, "col": 0},
        "site_transitions": [{"row": 0, "col": 0, "before": 0}],
        "changed_cells": [{"row": 0, "col": 0, "before": 0, "after": 1}], "boundary_event": boundary,
    }


def test_f_r1_a_completed_level_keeps_its_boundary_in_the_record():
    """Live, a completed level reports state NOT_FINISHED; the record dropped it, so replay stayed in
    G4-A while the live run had closed the level."""
    steps = record_tool._steps([_outcome(1, LIVE_LEVEL_WIN)], [[0]])
    assert steps[-1]["boundary"] == LIVE_LEVEL_WIN
    ordinary = dict(LIVE_LEVEL_WIN, level_after=1, level_completed=False)
    assert "boundary" not in record_tool._steps([_outcome(1, ordinary)], [[0]])[-1]


def test_f_r1_vc33_exit_replays_to_the_live_level_boundary():
    """Live (at d2bf323) the run stopped here; since R9-R17 the level is frozen and the ladder restarts."""
    result = replay(load_record(VC33_EXIT))
    machine = result.machine
    assert result.stopped is None and result.steps_replayed == 26
    (frozen,) = machine.levels
    orbits = frozen["products"]["G4.2-LEVER-ORBITS"]
    assert orbits["interrupted_lever_entities"] == ["E0005"]  # interrupted by the win, as live
    assert orbits["level_boundary"]["level_before"] == 1 and orbits["level_boundary"]["level_after"] == 2


def test_f_r2_ft09_exit_replays_through_g4c_with_the_live_grades():
    """Live, Duck pressed E0057 on its own turn after the death at transition 88, so it answered E0057
    before E0056; replay asked in the machine's order and refused the answer."""
    record = load_record(FT09_EXIT)
    orbit_order = [a["entity_id"] for a in record["answers"] if a["gate_id"] == "G4.2-LEVER-ORBITS"]
    assert orbit_order.index("E0057") < orbit_order.index("E0056")
    machine = replay(record).machine
    assert ladder_end(machine) is None and machine.gate_id == "PLAY-NORMAL"  # R9-R24 D22: normal play, not a stop
    predictions = machine._adapters["G4-B-LEVER-RELATIONS"]._predictions
    assert [(p.prediction_id, p.status, p.declared_at_transition, p.transition_id) for p in predictions] == [
        (f"P{i}", "SUPPORTED", 108 + i, 109 + i) for i in range(1, 9)
    ]
    law = machine.target_journal.active_product("G4-C-LEVER-LAW").payload
    assert law["status"] == "COMPLETE"
    certified = machine._adapters["G4-C-LEVER-LAW"]._certified
    assert (certified.prediction_id, certified.status, certified.transition_id) == ("L1", "SUPPORTED", 118)


def test_f_r3_step_env_labels_the_actor_and_duck_is_the_default(tmp_path):
    """Every live transition was labelled DUCK, so the vc33 win capsule credited Duck with the
    controller's winning press."""
    actors = []
    for name, extra in (("controller", {"actor": "CONTROLLER"}), ("duck", {}), ("forged", {"actor": "ROOT"})):
        session = _session(tmp_path / name, _Game())
        observer = _RecordingObserver()
        session.game_observer, session.observer_initialized = observer, True
        session.write_viewer_payload = lambda: None  # the fixture game carries no viewer run record
        assert session.step_env({"actions": [{"action": "ACTION1"}], **extra})["executed"] is True
        actors.append(observer.transitions[-1]["actor"])
    assert actors == ["CONTROLLER", "DUCK", "DUCK"]


def test_f_r3_the_controller_sends_its_actor_with_every_action(tmp_path, monkeypatch):
    run = Run(tmp_path, monkeypatch)
    for _ in range(3):
        run.turn()
    assert run.env_calls and all(call.get("actor") == "CONTROLLER" for call in run.env_calls)

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from types import SimpleNamespace

import arcengine
import pytest

from inference.agent.tool_agent import (
    _build_system_prompt,
    _python_tool_description,
)
from inference.framework.game_observer import (
    create_game_observer,
    normalize_observer_mode,
)
from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.virelai_runtime import verify_frame_archive


RING0_SYSTEM_SHA256 = "2ffc92d92f494419d8c97105d9045d203edcbc63bb0970e6a0ce64f9a70f4ccc"
RING0_PYTHON_DESCRIPTION_SHA256 = (
    "70b4394c089117f7d4d764a4f6cc883495d850579ff05ee3850e5733a960135b"
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_off_and_observe_modes_keep_exact_ring0_model_surface():
    system = _build_system_prompt(tool_output_tokens=1024, virelai_enabled=False)
    description = _python_tool_description(virelai_enabled=False)

    assert _sha256(system) == RING0_SYSTEM_SHA256
    assert _sha256(description) == RING0_PYTHON_DESCRIPTION_SHA256
    assert "virelai" not in system.lower()
    assert "virelai" not in description.lower()


def test_tool_mode_alone_exposes_virelai_surface():
    system = _build_system_prompt(tool_output_tokens=1024, virelai_enabled=True)
    description = _python_tool_description(virelai_enabled=True)

    assert "virelai" in system.lower()
    assert "virelai" in description.lower()
    assert "ARC grid-multiverse ontology" in system
    assert "persistent, expandable physics grammar" in system
    assert "After an observed level win" in system
    assert "supplied agenda" not in system


def test_observer_mode_is_explicit_and_defaults_off(tmp_path):
    assert HarnessSolver().virelai_mode == "off"
    assert HarnessSolver(virelai_mode="observe").virelai_mode == "observe"
    assert HarnessSolver(virelai_mode="tool").virelai_mode == "tool"
    assert HarnessSolver(virelai_mode="gated").virelai_mode == "gated"
    assert create_game_observer(
        mode="off",
        game_id="vc33-5430563c",
        run_stem="vc33-5430563c_p0",
        artifact_root=tmp_path,
    ) is None
    assert not (tmp_path / "vc33-5430563c_p0").exists()


def test_invalid_observer_mode_is_rejected():
    with pytest.raises(ValueError, match="Unsupported Virelai mode"):
        normalize_observer_mode("captain")


class _Grid(list):
    def tolist(self):
        return [list(row) for row in self]


def _state(value: int):
    grid = _Grid([[0, 0], [0, value]])
    raw = SimpleNamespace(
        game_id="fixture",
        frame=[grid],
        state=arcengine.GameState.NOT_FINISHED,
        levels_completed=0,
        win_levels=1,
        guid="fixture-guid",
        full_reset=False,
        available_actions=(1, 2, 3, 4),
    )
    return SimpleNamespace(
        raw=raw,
        frame=SimpleNamespace(data=grid),
        levels_completed=0,
        won=False,
        just_won_level=False,
        available_actions=(1, 2, 3, 4),
    )


class _Game:
    def __init__(self):
        self.current_state = _state(0)
        self.game_run = SimpleNamespace(game_id="fixture", history=[], state="playing")
        self.number_of_levels = 1

    def execute_action(self, action, *, generated_tokens, uncached_input_tokens):
        del action, generated_tokens, uncached_input_tokens
        self.current_state = _state(1)
        self.game_run.history.append(object())
        return self.current_state


class _FailingObserver:
    def __init__(self):
        self.failures = []

    def observe_transition(self, **kwargs):
        del kwargs
        raise RuntimeError("observer broke")

    def record_failure(self, event, detail, *, through_step=None):
        self.failures.append((event, detail, through_step))


def _session(tmp_path: Path, game: _Game) -> _HarnessGameSession:
    solver = HarnessSolver(virelai_mode="observe")
    solver.job_dir = tmp_path
    return _HarnessGameSession(
        solver=solver,
        game=game,
        analyzer=SimpleNamespace(generated_tokens=0),
        game_index=0,
        pass_index=0,
        state_path=tmp_path / "state.pkl",
        transcript_path=tmp_path / "transcript.txt",
        analysis_html_relpath="analysis.html",
        stop_event=threading.Event(),
        viewer_data_path=tmp_path / "viewer.json",
    )


def test_gated_session_keeps_engine_actions_opaque(tmp_path):
    game = _Game()
    session = _session(tmp_path, game)
    session.solver.virelai_mode = "gated"
    assert session._public_action_names() == ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
    assert session._public_action_display("ACTION1", {}) == "ACTION1"


def test_observer_failure_cannot_interrupt_duck_action(tmp_path):
    game = _Game()
    session = _session(tmp_path, game)
    observer = _FailingObserver()
    session.game_observer = observer
    session.observer_initialized = True

    payload = session._execute_action(
        arcengine.ActionInput(id=arcengine.GameAction.ACTION1, data={}),
        batch_index=1,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
    )

    assert payload["executed"] is True
    assert payload["action_num"] == 1
    assert len(game.game_run.history) == 1
    assert "observer broke" in session.virelai_fault
    assert observer.failures[0][0] == "OBSERVATION_FAILED"


class _RecordingObserver:
    def __init__(self):
        self.transitions = []

    def observe_transition(self, **kwargs):
        self.transitions.append(kwargs)


class _CloseFailingObserver(_RecordingObserver):
    def close(self):
        raise RuntimeError("close broke")


def _stable_action_payload(payload):
    return {
        key: value
        for key, value in payload.items()
        if key not in {"run_elapsed_seconds", "time_remaining_seconds"}
    }


def test_observe_mode_does_not_change_duck_action_result(tmp_path):
    off_game = _Game()
    off_session = _session(tmp_path / "off", off_game)
    off_session.solver.virelai_mode = "off"

    observed_game = _Game()
    observed_session = _session(tmp_path / "observe", observed_game)
    observer = _RecordingObserver()
    observed_session.game_observer = observer
    observed_session.observer_initialized = True

    action = arcengine.ActionInput(id=arcengine.GameAction.ACTION1, data={})
    off_payload = off_session._execute_action(
        action,
        batch_index=1,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
    )
    observed_payload = observed_session._execute_action(
        action,
        batch_index=1,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
    )

    assert _stable_action_payload(observed_payload) == _stable_action_payload(off_payload)
    assert observed_session.history_entries == off_session.history_entries
    assert _Grid(observed_game.current_state.frame.data) == _Grid(
        off_game.current_state.frame.data
    )
    assert len(observer.transitions) == 1


def test_session_observer_writes_lossless_n_plus_one_archive(tmp_path):
    game = _Game()
    session = _session(tmp_path, game)
    session._observe_virelai_initial()
    session._execute_action(
        arcengine.ActionInput(id=arcengine.GameAction.ACTION1, data={}),
        batch_index=1,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
    )
    session._close_game_observer()

    artifact_dir = tmp_path / "virelai" / "fixture_p0"
    verification = verify_frame_archive(artifact_dir)
    assert verification["passed"] is True
    assert verification["frames"] == 2
    assert (artifact_dir / "summary.json").is_file()


def test_close_failure_is_recorded_without_raising(tmp_path):
    game = _Game()
    session = _session(tmp_path, game)
    session.game_observer = _CloseFailingObserver()
    session.observer_initialized = True

    session._close_game_observer()

    warning_path = tmp_path / "virelai" / "fixture_p0" / "observer_warnings.jsonl"
    assert "CLOSE_FAILED" in warning_path.read_text(encoding="utf-8")
    assert "close broke" in session.virelai_fault


def test_construction_failure_is_recorded_and_duck_can_still_act(
    tmp_path, monkeypatch
):
    def fail_construction(**kwargs):
        del kwargs
        raise RuntimeError("construction broke")

    monkeypatch.setattr(
        "inference.framework.game_observer.create_game_observer",
        fail_construction,
    )
    game = _Game()
    session = _session(tmp_path, game)

    session._observe_virelai_initial()
    payload = session._execute_action(
        arcengine.ActionInput(id=arcengine.GameAction.ACTION1, data={}),
        batch_index=1,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
    )

    warning_path = tmp_path / "virelai" / "fixture_p0" / "observer_warnings.jsonl"
    assert payload["executed"] is True
    assert "CONSTRUCTION_FAILED" in warning_path.read_text(encoding="utf-8")
    assert "construction broke" in session.virelai_fault

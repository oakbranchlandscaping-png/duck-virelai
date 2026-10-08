"""SUB-2: submission hardening after the 110-game dry run (REVIEW_RING9_SUBMISSION_DRYRUN_V1_KAGGLE_2026-10-07).

Author: Claude (Alpha build seat), 2026-10-07. Director ruling 2026-10-07: D-3 free play; SUB-2 built as described.

- D-1: ACTION7 exists in the engine but was missing from the harness's action names, so every press
  of it was refused as "Unknown action" (4 of the 25 public worlds offer it).
- D-2: after the environment refused a controller action, the controller replayed the same bound
  probe (its token already consumed) 12,000-18,500 times per game until the slice ended (18 of 110
  games). The controller now rests the level in normal play after a few stalled turns (axiom A2),
  and the solver loop never busy-waits on turns that execute nothing.
- D-3: in submission mode a controlled stop rests the level in normal play once, instead of ending
  the game; a second controlled stop while already in play still ends it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import arcengine

from inference.agent import controller_turn
from inference.agent.action_names import to_engine_action, to_model_action
from inference.agent.controller_turn import ControllerSession, run_controller_turn
from inference.framework import controller_executor, solver as solver_module
from inference.framework.controller_executor import ACTION, DUCK, OwnedStep
from inference.framework.solver import HarnessSolver, _HarnessGameSession

PLAY = "PLAY-NORMAL"
MAX_STALLED = getattr(controller_turn, "MAX_STALLED_CONTROLLER_TURNS", 3)  # so the test runs fail-first


class _Play:
    def __init__(self) -> None:
        self.forced: str | None = None
        self.revision = 1


class _Machine:
    """The few parts of the gate machine the controller turn and the solver touch."""

    def __init__(self, gate: str = "G1-EGO") -> None:
        self._gate = gate
        self._adapters = {PLAY: _Play()}

    @property
    def gate_id(self) -> str:
        return PLAY if self._adapters[PLAY].forced is not None else self._gate

    def legal_move_status(self) -> dict:
        return {"legal": True}


@dataclass
class _Probe:
    probe_id: str = "P1"


def _stub_executor(monkeypatch) -> None:
    def next_owned_step(machine, *, refused=frozenset(), rerun=None):
        if machine.gate_id == PLAY:
            return OwnedStep(owner=DUCK, gate_id=PLAY, reason="normal play")
        return OwnedStep(owner="CONTROLLER", gate_id=machine.gate_id, reason="bound PROBE action",
                         kind=ACTION, action={"action": "ACTION7"}, probe_token="token-1")

    monkeypatch.setattr(controller_executor, "next_owned_step", next_owned_step)
    monkeypatch.setattr(controller_executor, "ladder_end", lambda machine: None)
    monkeypatch.setattr(controller_executor, "return_to_mu_if_stuck", lambda machine: None)
    monkeypatch.setattr(controller_executor, "wake_signals", lambda machine, result=None: {})
    monkeypatch.setattr(controller_executor, "wake_reason", lambda machine, event, raw, before: None)


def _agent(machine: _Machine, *, begin, step_env) -> SimpleNamespace:
    agent = SimpleNamespace(_controller=ControllerSession(enabled=True), _virelai_query_callback=None,
                            _current_valid_actions=[])
    agent._ensure_gate_machine = lambda state_path: machine
    agent._gate_probe_begin = begin
    agent._gate_probe_record = lambda *args, **kwargs: None
    agent._apply_step_result = lambda raw, event: raw
    agent._record_gate_answer = lambda *args, **kwargs: None
    agent._step_env = step_env
    return agent


def _turn(agent, tmp_path: Path):
    agent._step_env_callback = agent._step_env  # analyze() binds the step callback before every turn
    return run_controller_turn(agent, tmp_path / "k001_p0_runtime_state.json", 8, 1, tmp_path / "analysis.log")


# D-1 ----------------------------------------------------------------------------------------------

def test_d1_action7_is_a_harness_action_with_an_opaque_label():
    assert to_engine_action("ACTION7") == "ACTION7"
    assert to_model_action("ACTION7") == "ACTION7"  # no semantic name: the world must show what it does


def test_d1_the_solver_accepts_an_action7_step():
    session = object.__new__(_HarnessGameSession)
    actions, error = session._normalize_actions({"action": "ACTION7"})
    assert error is None
    assert [action.id for action in actions] == [arcengine.GameAction.ACTION7]


# D-2 ----------------------------------------------------------------------------------------------

def test_d2_a_refused_controller_probe_rests_the_level_instead_of_spinning(monkeypatch, tmp_path):
    """The dry-run sequence: the environment refuses the probe, then its consumed token is replayed."""
    _stub_executor(monkeypatch)
    machine = _Machine()
    calls = {"step_env": 0}

    def begin(state_path, machine_, decision, actions, executor):
        if calls["step_env"]:
            raise RuntimeError("This probe_token has already been used and cannot be replayed.")
        return _Probe(), None, 8

    def step_env(payload):
        calls["step_env"] += 1
        return {"executed": False, "error": "Unknown action at index 1: 'ACTION7'"}

    agent = _agent(machine, begin=begin, step_env=step_env)
    results = [_turn(agent, tmp_path) for _ in range(MAX_STALLED)]
    assert all(result is not None and not result.step_executed for result in results)
    assert machine._adapters[PLAY].forced is None  # still within the guard
    assert _turn(agent, tmp_path) is None  # the next turn is Duck's: the level rests in normal play
    assert machine.gate_id == PLAY
    assert "consecutive turns" in machine._adapters[PLAY].forced
    assert calls["step_env"] == 1  # the refused action was never re-sent to the environment


def test_d2_an_executed_action_resets_the_stall_count(monkeypatch, tmp_path):
    _stub_executor(monkeypatch)
    machine = _Machine()
    outcomes = iter([False, False, True, False, False, True])
    agent = _agent(machine, begin=lambda *args, **kwargs: (_Probe(), None, 8),
                   step_env=lambda payload: {"executed": next(outcomes)})
    for _ in range(6):
        _turn(agent, tmp_path)
    assert machine._adapters[PLAY].forced is None
    assert agent._controller.stalled == 0


def test_d2_the_solver_loop_backs_off_on_turns_that_execute_nothing(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(solver_module.time, "sleep", sleeps.append)
    session = object.__new__(_HarnessGameSession)
    session.idle_turns = 0
    for _ in range(4):
        session._idle_backoff()
    assert len(sleeps) == 3  # the first idle turn costs nothing; repeats wait
    assert sleeps == sorted(sleeps) and max(sleeps) <= solver_module.IDLE_BACKOFF_MAX_SECONDS


# D-3 ----------------------------------------------------------------------------------------------

def _session(tmp_path: Path, machine: _Machine, *, rest: bool) -> _HarnessGameSession:
    session = object.__new__(_HarnessGameSession)
    session.solver = HarnessSolver(rest_on_controlled_stop=rest)
    session.analyzer = SimpleNamespace(_gate_machine=machine)
    session.transcript_path = tmp_path / "transcript.log"
    return session


def _stop(reason: str = "contract_repair_loop: Duck repeated a gate answer") -> SimpleNamespace:
    return SimpleNamespace(controlled_stop=reason, fatal_failure=None)


def test_d3_in_submission_mode_a_controlled_stop_rests_the_level_in_play_once(tmp_path):
    machine = _Machine("G1-EGO")
    session = _session(tmp_path, machine, rest=True)
    assert session._rest_after_controlled_stop(_stop()) is True
    assert machine.gate_id == PLAY
    assert "ruling D-3" in machine._adapters[PLAY].forced
    assert "ruling D-3" in session.transcript_path.read_text()
    assert session._rest_after_controlled_stop(_stop("no_progress_tool_loop")) is False  # already in play


def test_d3_outside_submission_mode_a_controlled_stop_still_ends_the_game(tmp_path):
    machine = _Machine("G3-LEVERS")
    session = _session(tmp_path, machine, rest=False)
    assert session._rest_after_controlled_stop(_stop("g3_route_retry_exhausted")) is False
    assert machine._adapters[PLAY].forced is None
    run = SimpleNamespace(solver_note=None)
    result = SimpleNamespace(controlled_stop="g3_route_retry_exhausted", fatal_failure=None, planned_stop="")
    assert solver_module._turn_ends_game(result, run) is True  # the canary behaviour is unchanged


def test_d3_an_ordinary_turn_is_untouched(tmp_path):
    session = _session(tmp_path, _Machine(), rest=True)
    assert session._rest_after_controlled_stop(SimpleNamespace(controlled_stop="", fatal_failure=None)) is False
    assert MAX_STALLED >= 2

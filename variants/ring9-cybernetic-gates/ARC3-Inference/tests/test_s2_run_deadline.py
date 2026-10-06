"""S-2: the run's deadline and each game's slice stop a game, and cut a model request to fit.

Author: Claude (Alpha build seat), 2026-10-06. BUILD_PLAN_PORTS_AND_PILLARS_v1 §1 S-2; submission mode.

A submission has one hard wall (the notebook's runtime limit). The notebook passes the benchmark a
soft end before that wall; every game session must stop at it, at its own per-game slice
(``max_runtime_s_per_game``) and at its action cap, and a model request must never be allowed to
outlast whichever comes first. The machinery exists in ``solver.py`` (``should_stop``,
``request_timeout_seconds``); these tests pin it with fixed clocks, so a later change cannot silently
let a game run past the deadline.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import arcengine

from inference.framework.solver import HarnessSolver, _HarnessGameSession


def _session(*, soft_end: datetime | None, per_game_s: float | None, started_ago_s: float,
             actions: int = 0, max_actions: int | None = 400, analyzer_timeout: float = 120.0):
    solver = HarnessSolver()
    solver.soft_end_time = soft_end
    solver.max_runtime_s_per_game = per_game_s
    solver.max_actions_per_game = max_actions
    session = object.__new__(_HarnessGameSession)
    session.solver = solver
    session.game = SimpleNamespace(
        game_run=SimpleNamespace(state="playing", history=[object()] * actions),
        current_state=SimpleNamespace(raw=SimpleNamespace(state=arcengine.GameState.NOT_FINISHED)),
    )
    session.stop_event = threading.Event()
    session.started_at = time.monotonic() - started_ago_s
    session.analyzer = SimpleNamespace(_timeout=analyzer_timeout)
    return session


def test_s2_a_game_with_time_and_actions_left_stops_at_the_run_deadline():
    session = _session(soft_end=datetime.now() - timedelta(seconds=1), per_game_s=3600, started_ago_s=60)
    assert session.soft_deadline_reached()
    assert session.should_stop()


def test_s2_a_game_stops_at_its_own_slice_before_the_run_deadline():
    session = _session(soft_end=datetime.now() + timedelta(hours=8), per_game_s=2700, started_ago_s=2701)
    assert not session.soft_deadline_reached()
    assert session.runtime_limit_reached()
    assert session.should_stop()


def test_s2_a_game_stops_at_its_action_cap():
    session = _session(soft_end=datetime.now() + timedelta(hours=8), per_game_s=2700, started_ago_s=10,
                       actions=400, max_actions=400)
    assert session.should_stop()


def test_s2_a_game_inside_every_limit_keeps_playing():
    session = _session(soft_end=datetime.now() + timedelta(hours=8), per_game_s=2700, started_ago_s=10,
                       actions=12)
    assert not session.should_stop()


def test_s2_a_model_request_is_cut_to_the_nearest_limit():
    near_deadline = _session(soft_end=datetime.now() + timedelta(seconds=30), per_game_s=2700, started_ago_s=10)
    assert 25.0 <= near_deadline.request_timeout_seconds() <= 30.0  # the run's end is nearest
    near_slice = _session(soft_end=datetime.now() + timedelta(hours=8), per_game_s=2700, started_ago_s=2680)
    assert 15.0 <= near_slice.request_timeout_seconds() <= 20.0  # the game's slice is nearest
    roomy = _session(soft_end=datetime.now() + timedelta(hours=8), per_game_s=2700, started_ago_s=10)
    assert roomy.request_timeout_seconds() == 120.0  # the analyzer's own timeout is nearest
    past = _session(soft_end=datetime.now() - timedelta(seconds=5), per_game_s=2700, started_ago_s=10)
    assert past.request_timeout_seconds() == 0.1  # never zero or negative: the floor, then the stop

from types import SimpleNamespace
import threading
import time

from inference.framework.solver import _HarnessGameSession


def session(*, soft_remaining, run_state="playing"):
    item = _HarnessGameSession.__new__(_HarnessGameSession)
    item.solver = SimpleNamespace(
        max_runtime_s_per_game=1200.0,
        max_actions_per_game=48,
        soft_time_remaining_seconds=lambda: soft_remaining,
    )
    item.game = SimpleNamespace(
        game_run=SimpleNamespace(state=run_state, history=[]),
        current_state=SimpleNamespace(raw=SimpleNamespace(state="PLAYING")),
    )
    item.stop_event = threading.Event()
    item.started_at = time.monotonic()
    return item


def test_soft_experiment_deadline_stops_analyzer_retry_loop():
    item = session(soft_remaining=0.0)
    assert item.soft_deadline_reached() is True
    assert item.should_stop() is True


def test_positive_soft_deadline_does_not_stop_healthy_session():
    item = session(soft_remaining=30.0)
    assert item.soft_deadline_reached() is False
    assert item.should_stop() is False


def test_absent_soft_deadline_leaves_per_game_limits_authoritative():
    item = session(soft_remaining=None)
    assert item.soft_deadline_reached() is False
    assert item.should_stop() is False

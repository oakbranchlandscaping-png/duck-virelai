"""
virelai_v4/lifecycle.py — Operator-bound lifecycle helpers.

Import sovereign: stdlib only. No arcengine, no virelai_v4 sub-package
imports. Follows FRICTION-SENTINEL-IMPORT-PATH-01: this module is the
testable primitive that virelai.py::is_done delegates its env-var cap
checks to.

Two operator environment variables:
    VIRELAI_MAX_LIVES=N    — terminate after N lives (testing mode)
    VIRELAI_MAX_ACTIONS=N  — terminate after N actions (testing mode)

Both unset = competition mode: only WIN terminates. See
docs/friction/FRICTION-CANARY-LIFE-AND-ACTION-CAPS.md.
"""

from __future__ import annotations

import os


def env_cap_reached(lives_used: int, action_counter: int) -> bool:
    """Return True if any operator-set env-var cap has been reached.

    Called by Virelai.is_done after the WIN check. When neither
    VIRELAI_MAX_LIVES nor VIRELAI_MAX_ACTIONS is set, always returns False
    (competition mode — the game's own WIN signal is the sole terminator).

    Args:
        lives_used:     ctx.lives_used — number of lives consumed so far.
        action_counter: agent.action_counter — total actions taken.

    Returns:
        True  — an operator cap fired; is_done should return True.
        False — no cap fired; continue playing.
    """
    max_lives_env = os.environ.get("VIRELAI_MAX_LIVES")
    if max_lives_env is not None and lives_used >= int(max_lives_env):
        return True
    max_actions_env = os.environ.get("VIRELAI_MAX_ACTIONS")
    if max_actions_env is not None and action_counter >= int(max_actions_env):
        return True
    return False


# ---------------------------------------------------------------------------
# WO-GAME-OVER-DETECTION (June 11, 2026) — "the game tells us when to stop".
# The no-self-cap captain probes until the environment ends the game; the
# agent must hear that signal cleanly. These pure helpers consolidate the
# is_done decision (testable without a live-API Agent) and recognize the
# framework's terminal None-frame signal.
# ---------------------------------------------------------------------------

_TERMINAL_NONE_FRAME_MARKER = "None frame data"


def should_stop(
    env_terminated: bool,
    is_win: bool,
    lives_used: int,
    action_counter: int,
) -> bool:
    """The agent's full stop decision (consolidates Virelai.is_done).

    Stops when the environment has signalled terminal (no further frame),
    OR the game is WON, OR an operator cap is reached. env_terminated is the
    environment-level terminator that preserves the no-self-cap ruling: the
    captain never caps itself; the environment's end-of-game is the cap.
    """
    if env_terminated:
        return True
    if is_win:
        return True
    return env_cap_reached(lives_used, action_counter)


def is_terminal_none_frame_error(exc: BaseException) -> bool:
    """True for the framework's `_convert_raw_frame_data` ValueError raised
    when `arc_env.step` returns no frame — i.e. the environment has no further
    frame to give because the game has ended. The agent treats this as a clean
    terminal signal rather than a crash."""
    return isinstance(exc, ValueError) and _TERMINAL_NONE_FRAME_MARKER in str(exc)


__all__ = ["env_cap_reached", "should_stop", "is_terminal_none_frame_error"]

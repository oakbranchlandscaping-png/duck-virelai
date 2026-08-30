"""
contracts/terminal_cause.py

WO-FORGE-TERMINAL-01: TerminalCause enum + classify_terminal().

Defines why a solver episode ended and provides a single authoritative
classifier used by all execution paths.

Why this matters:
    The enumeration protocol (FORGE-05) banks winning configurations based on
    a binary win/loss signal.  If that signal is wrong — e.g., STABILITY_STALL
    misclassified as WIN — the solver banks a false solution, stops searching,
    and replays a non-winning configuration on every subsequent life.

Classification priority (highest to lowest):
    1. WIN              — SDK confirmed level advance, OR visual win detector fired.
                          Either signal is sufficient; both must be absent for non-win.
    2. STABILITY_STALL  — Our own inactivity guard fired (5 consecutive no-change
                          steps).  Never a win; the solver stalled, not succeeded.
    3. BUDGET_EXHAUSTED — Action budget depleted before any terminal signal.
    4. SDK_TERMINAL     — SDK ended the episode (cause unclear — not a win by signal).
    5. UNKNOWN          — Cannot determine cause; treat as non-win.

SDK note:
    The ARC-AGI-3 SDK does NOT provide an explicit reward signal (reward is always
    0.0 per AdapterEnvironment.step()).  The win signal is:
        primary   — env.level_just_advanced (SDK level counter incremented)
        secondary — WinDetector (visual: new colour saturating ≥90% of grid)
    Both are captured in PlayTranscript.{level_advanced, win_detected}.

No game-ID-specific logic here.  The classifier is pure data → enum.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class TerminalCause(Enum):
    """Why the solver episode ended."""

    WIN = "win"                           # SDK/visual confirmed puzzle solved
    BUDGET_EXHAUSTED = "budget_exhausted" # Action budget depleted
    STABILITY_STALL = "stability_stall"   # Inactivity guard fired (NOT a win)
    SDK_TERMINAL = "sdk_terminal"         # SDK ended episode; cause unclear
    UNKNOWN = "unknown"                   # Cannot determine cause


def classify_terminal(
    abort_reason: Optional[str],
    terminated: bool,
    level_advanced: bool,
    win_detected: bool,
    budget_remaining: int,
) -> TerminalCause:
    """
    Classify why the episode ended.

    Parameters
    ----------
    abort_reason : str or None
        Abort string from PlayTranscript.abort_reason.
        "no_change_in_5_consecutive_steps" → STABILITY_STALL.
    terminated : bool
        True if the SDK reported the episode as terminated.
    level_advanced : bool
        True if any step during this run caused env.level_just_advanced=True
        (SDK level counter incremented → puzzle solved).
    win_detected : bool
        True if WinDetector fired (visual: new colour saturating grid).
    budget_remaining : int
        Actions remaining at episode end.  ≤0 → BUDGET_EXHAUSTED.

    Returns
    -------
    TerminalCause
        The classified cause.

    Notes
    -----
    WIN takes priority over all other causes.  If a level advanced *and* the
    solver also hit a stability stall (e.g., winning on level 1 then stalling
    on level 2), the WIN is the correct classification because progress occurred.
    """
    # Priority 1: WIN — SDK or visual confirmed a win
    if level_advanced or win_detected:
        return TerminalCause.WIN

    # Priority 2: STABILITY_STALL — our inactivity guard, not a win
    if abort_reason == "no_change_in_5_consecutive_steps":
        return TerminalCause.STABILITY_STALL

    # Priority 3: BUDGET_EXHAUSTED — ran out of actions
    if budget_remaining <= 0:
        return TerminalCause.BUDGET_EXHAUSTED

    # Priority 4: SDK_TERMINAL — SDK ended the episode (non-win)
    if terminated:
        return TerminalCause.SDK_TERMINAL

    # Priority 5: UNKNOWN — cannot determine cause
    return TerminalCause.UNKNOWN


__all__ = ["TerminalCause", "classify_terminal"]

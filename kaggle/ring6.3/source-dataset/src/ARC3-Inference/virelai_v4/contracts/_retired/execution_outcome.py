"""
contracts/execution_outcome.py

ExecutionOutcome — V3.5 terminal artifact.

Summarises what the solver achieved in one run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .degradation import DegradationFlag


@dataclass(frozen=True)
class ExecutionOutcome:
    """
    Outcome of one solver run.

    Fields:
        terminal_reason      — TerminalCause.value: "win" | "budget_exhausted" |
                               "stability_stall" | "sdk_terminal" | "unknown"
                               (legacy crash strings also possible for stub paths)
        levels_completed     — number of levels completed
        actions_consumed     — total environment steps consumed
        final_phase          — name of last active DFA state
        hypothesis_used      — type of hypothesis that drove execution
        win_detected         — True ONLY when classified as WIN (SDK level advance
                               or visual WinDetector); False for stability stalls
        terminal_cause_str   — WO-FORGE-TERMINAL-01: TerminalCause enum value as
                               string. None for legacy/stub outcomes.
        degradation_flags    — any degradation events during the run
    """
    terminal_reason: str
    levels_completed: int
    actions_consumed: int
    final_phase: str
    hypothesis_used: Optional[str] = None
    win_detected: bool = False
    terminal_cause_str: Optional[str] = None   # WO-FORGE-TERMINAL-01: TerminalCause.value
    degradation_flags: Tuple[DegradationFlag, ...] = ()


__all__ = ["ExecutionOutcome"]

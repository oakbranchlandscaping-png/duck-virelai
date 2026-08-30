"""
contracts/directives.py — Reentry directive type contracts.

Campaign TRIAGE WO-TRIAGE-09: Extracted from crucible/curiosity/directives.py.

These four frozen dataclasses are consumed by BOTH the crucible phase (which
creates them via parse_reentry_response) and the execution phase (which routes
on them via isinstance checks). Shared type contracts belong in contracts/,
not in any phase-internal module.

Types in this file:
    ExploreDirective       — navigate to a quadrant to discover levers
    PressDirective         — navigate to a known lever and press it
    NavigateDirective      — navigate to specific coordinates
    ResetTargetDirective   — abandon current target, re-scan

NOT in this file (stay in crucible/curiosity/directives.py):
    ProbeDirective         — QSPI probe request (crucible-internal)
    WinHypothesisDirective — Qwen win condition proposal (crucible-internal)
    ExploitDirective       — exploitation directive (crucible-internal)
    FallbackDirective      — fallback directive (crucible-internal)
    ProbeResult            — QSPI probe result (crucible-internal)
    ProbeBeliefState       — QSPI belief tracking (crucible-internal)

Consumers:
    crucible/curiosity/directives.py — re-exports for backward compat
    execution/reentry_decision.py    — constructs and returns these types
    execution/nav_executor.py        — isinstance-dispatches on these types

Zone: FRAMEWORK_CONTRACTS
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Quadrant constants ────────────────────────────────────────────────────────

_VALID_QUADRANTS: frozenset = frozenset({"Q1", "Q2", "Q3", "Q4"})


# ── Cross-phase reentry directives ────────────────────────────────────────────

@dataclass(frozen=True)
class ExploreDirective:
    """Navigate to a quadrant and probe for undiscovered levers.

    Produced by parse_reentry_response() when abort reason is LEVER_INCOMPLETE
    or EXPLORATION_EXHAUSTED and unexplored quadrants exist.
    Consumed by WO-S3-04 NAV execution loop.
    """
    quadrant: str = "Q1"    # One of: "Q1", "Q2", "Q3", "Q4"

    def __post_init__(self) -> None:
        if self.quadrant not in _VALID_QUADRANTS:
            raise ValueError(
                f"ExploreDirective.quadrant={self.quadrant!r} "
                f"not in {sorted(_VALID_QUADRANTS)}"
            )


@dataclass(frozen=True)
class PressDirective:
    """Navigate to a known lever position and press it.

    Produced by parse_reentry_response() when abort reason is LEVER_INCOMPLETE
    and a known lever site needs re-activation.
    Consumed by WO-S3-04 NAV execution loop.
    """
    row: int = 0
    col: int = 0


@dataclass(frozen=True)
class NavigateDirective:
    """Navigate to specific coordinates (door component, known target).

    Produced by parse_reentry_response() when abort reason is OSCILLATION_EXHAUSTED
    or PROTOCOL_STALL and a specific target coordinate is known.
    Consumed by WO-S3-04 NAV execution loop.
    """
    row: int = 0
    col: int = 0


@dataclass(frozen=True)
class ResetTargetDirective:
    """Abandon current target, re-scan all target candidates.

    Produced by parse_reentry_response() when abort reason is PROTOCOL_STALL,
    or as the safe fallback when Qwen output is unparseable or returns an
    unknown directive type.
    Consumed by WO-S3-04 NAV execution loop.
    """
    pass


__all__ = [
    "_VALID_QUADRANTS",
    "ExploreDirective",
    "PressDirective",
    "NavigateDirective",
    "ResetTargetDirective",
]

"""Pure lifecycle contract for Ring 6's bounded Captain phase.

No ARC, TAAF or V4 imports.  The live driver delegates its stopping and level
boundary decisions here so the experiment can be tested without a game engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ProbeLimits:
    lives: int = 2
    actions: int = 320
    seconds: float = 480.0

    def __post_init__(self) -> None:
        if self.lives < 1 or self.actions < 1 or self.seconds <= 0:
            raise ValueError("probe limits must be positive")


def captain_action_data(action: Any) -> dict[str, int]:
    """Return only the public payload TAAF accepts for a Captain action.

    ``arcengine.GameAction.action_data`` is an engine-owned model. Its
    serialized form includes an internal ``game_id`` field even for simple
    actions. TAAF rejects all payload fields on simple actions, so forwarding
    ``model_dump()`` verbatim blocks directional, SPACE, and RESET actions.

    The boundary is explicit: simple actions carry no data; the sole complex
    action carries only its public x/y coordinates.
    """
    if action.is_simple():
        return {}
    if action.is_complex():
        raw = action.action_data.model_dump()
        return {"x": int(raw["x"]), "y": int(raw["y"])}
    raise ValueError(f"Unsupported Captain action shape: {action!r}")


def level_boundary(latest_completed: int, last_seen: int) -> Optional[str]:
    """Return ADVANCE, DESCENT or None from platform level counters."""
    if latest_completed > last_seen:
        return "ADVANCE"
    if latest_completed < last_seen:
        return "DESCENT"
    return None


def probe_stop_reason(
    *,
    state_name: str,
    environment_terminal: bool,
    lives_used: int,
    actions_used: int,
    elapsed_seconds: float,
    limits: ProbeLimits,
    harness_stop: bool,
) -> Optional[str]:
    """The ordered terminal classifier for the Captain phase.

    A level advance is deliberately absent: winning a level never stops the
    Captain.  A complete-game WIN does.
    """
    if state_name == "WIN":
        return "GAME_WON"
    if environment_terminal:
        return "ENVIRONMENT_TERMINAL"
    if elapsed_seconds >= limits.seconds:
        return "TIME_CAP"
    if actions_used >= limits.actions:
        return "ACTION_CAP"
    if lives_used >= limits.lives:
        return "TWO_LIVES_USED" if limits.lives == 2 else "LIFE_CAP"
    if harness_stop:
        return "HARNESS_STOP"
    return None


__all__ = [
    "ProbeLimits", "captain_action_data", "level_boundary",
    "probe_stop_reason",
]

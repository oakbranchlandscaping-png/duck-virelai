"""
contracts/field_card.py

FieldCard — frozen dataclass for the fixed-size Qwen interface.

Extracted from V3 phase2/field_card.py (533 lines, grade B).
Only the dataclass definition lives here. Assembly logic belongs
in discovery/field_card_assembler.py (WO-V35-04).

Hard ceiling: 1,500 characters serialized. This is the Prompt Constancy
enforcement point (Governing Law 10).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

# Hard ceiling — Governing Law 10 (Prompt Constancy)
_CHAR_CEILING = 1500


@dataclass(frozen=True)
class FieldCard:
    """
    Fixed-size summary rendered for Qwen consumption.

    Fields represent the lens through which the LLM views the game state.
    The card structure is constant; missing data renders as placeholders.

    __post_init__ enforces the 1,500 character ceiling.
    """
    world_type: str                          # "NAV" | "CLICK" | "HYBRID"
    budget_remaining: int
    budget_total: int
    level: int
    ego_class: int                           # -1 if unknown
    ego_position: Tuple[int, int]            # (row, col)
    passable_classes: Tuple[int, ...]        # sorted ascending
    blocking_classes: Tuple[int, ...]        # sorted ascending
    reactive_classes: Tuple[int, ...]        # sorted ascending
    unknown_classes: Tuple[int, ...]         # sorted ascending
    target_classes: Tuple[int, ...]          # sorted ascending
    explored_pct: float                      # [0, 1]
    frontier_count: int
    win_condition: str                       # "not detected" if unknown
    counter_info: str                        # "none" if no counter
    archetype_info: str = ""                 # Library B activation summary
    falsified_info: str = ""                 # falsified archetypes summary
    react_map: Tuple[Tuple[int, str], ...] = ()  # (class_id, mechanic_type) pairs
    game_history: str = ""                       # WO-S3-07: GAME_HISTORY section (≤ 200 chars)
    mechanics: str = ""                          # WO-S3-08: MECHANICS section (≤ 250 chars)
    unknowns_section: str = ""                   # WO-CUR-04: UNKNOWNS section (≤ 250 chars)

    def __post_init__(self) -> None:
        serialized = str(self)
        if len(serialized) > _CHAR_CEILING:
            raise ValueError(
                f"FieldCard serialized length {len(serialized)} exceeds "
                f"ceiling of {_CHAR_CEILING} characters"
            )


__all__ = ["FieldCard"]

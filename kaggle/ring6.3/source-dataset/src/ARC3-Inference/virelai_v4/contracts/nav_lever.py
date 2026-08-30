"""
virelai_v4/contracts/nav_lever.py — NavLeverCandidate dataclass.

Ported VERBATIM from V3.5 ``Universal_Solver_v3_5/contracts/nav_lever.py``
per WO-CAMPAIGN3-PHASE2-01 (May 2, 2026).

NavLeverCandidate: a coordinate whose contact by the ego triggered a
world transition. Distinct from CLICK LeverArtifact — NAV activation
is driven by spatial contact (raw-frame-measurer pixel-budget excess),
not discrete clicks.

This is the raw observation artifact. Phase 2's contact_reactivity
detects the event; this dataclass packages the structured evidence
for NavAtlas writeback + library role transition.

Two-family architecture: this dataclass is a **structured artifact**
populated by the raw-frame-measurer family (contact_reactivity +
lever_kernel_reconstruction); consumed by the library role-transition
logic (aggregator concern) at the integration layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class NavLeverCandidate:
    """A coordinate whose contact by the ego triggered a world transition.

    Fields:
        coordinate          Absolute (row, col) of the inferred lever kernel
                            inside the macrotile the ego entered.
        activation_mode     Always "NAV_CONTACT" for this artifact.
        pre_activation_tile Tile values that were present BEFORE the ego
                            overwrote the destination macrotile. Captured
                            from ``prev_grid[r0:r1, c0:c1]`` before env.step().
                            Stored as numpy array; excluded from equality /
                            hash to keep the dataclass hashable.
        kernel_integer      Rarest non-ego integer in ``pre_activation_tile``.
                            The visual marker placed by the ARC designer at
                            the activation point.
        kernel_offset       (row, col) of ``kernel_integer`` within
                            ``tile_cache`` (relative to tile top-left corner).
        observed_effect_region  frozenset of (row, col) pairs — non-ego pixels
                            that changed after the step (lever effect).
        effect_pixel_count  ``len(observed_effect_region)``.
        activation_action   action_id that moved the ego to this coordinate.
        confidence          Observation confidence. Starts at 0.5, increases
                            with repeated activation at the same coordinate.

    V3.5 source: ``contracts/nav_lever.py``.
    """

    coordinate: Tuple[int, int]
    activation_mode: str
    # numpy array — excluded from equality and hash to keep instance hashable
    pre_activation_tile: np.ndarray = field(compare=False, hash=False, repr=False)
    kernel_integer: int
    kernel_offset: Tuple[int, int]
    observed_effect_region: frozenset
    effect_pixel_count: int
    activation_action: int
    confidence: float

    def pre_activation_tile_copy(self) -> np.ndarray:
        """Return a read-only copy of the cached tile."""
        arr = self.pre_activation_tile.copy()
        arr.flags.writeable = False
        return arr


__all__ = ["NavLeverCandidate"]

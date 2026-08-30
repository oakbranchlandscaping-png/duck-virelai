"""
virelai_v4/library/lever_kernel_reconstruction.py — Lever kernel reconstruction.

Ported VERBATIM from V3.5 ``Universal_Solver_v3_5/discovery/physics/lever_kernel_reconstruction.py``
per WO-CAMPAIGN3-PHASE2-01 (May 2, 2026, Phase 2 CONTACT + LEVER DISCOVERY).

V3.5 inheritance: this is the V3.5 production-grade lever kernel
reconstruction proven across V3.5 forge campaigns (WO-FORGE-06-L3).
Pure function; single frame; no side effects; zero V3.5-specific
dependencies. Verbatim port with V4 import-path adjustments only.

V4 ARCHITECTURE COMPLIANCE: file location at ``virelai_v4/library/``
(per Phase 2 testability idiom — pure functions in arcengine-independent
modules; tests target free function directly).

Two-family architecture: **raw-frame-measurer family** — operates on
raw `tile_cache: np.ndarray` (a pre-move snapshot of the destination
macrotile values). Does not consume canonical WorldDelta; correctly
classified per WO-PHASE2-00 §6 architectural verdict.
"""
from __future__ import annotations

from collections import Counter
from typing import FrozenSet, Tuple

import numpy as np


def reconstruct_lever_kernel(
    tile_cache: np.ndarray,
    ego_value_set: FrozenSet[int],
) -> Tuple[int, int, int]:
    """Find the rarest non-ego integer in the cached destination tile.

    Algorithm:
        1. Flatten the tile to a 1-D integer array.
        2. Build a frequency counter, excluding ego class values.
        3. Select the integer with the lowest count (rarest ≠ ego).
        4. Find its first (top-left) occurrence in the tile.
        5. Return (row_offset, col_offset, integer_value) relative to
           the tile's top-left corner.

    When the tile is composed entirely of ego pixels (shouldn't happen for a
    well-formed gambit but handled gracefully), returns (0, 0, -1).

    V3.5 source: ``discovery/physics/lever_kernel_reconstruction.py:24-75``.

    Args:
        tile_cache:      2-D integer numpy array — the destination macrotile
                         values BEFORE the ego overwrote them. Caller must
                         snapshot before emitting the action; ego will
                         overwrite the destination region after the action.
        ego_value_set:   frozenset of integer class values that belong to the
                         ego body (excluded from kernel search).

    Returns:
        (kernel_row_offset, kernel_col_offset, kernel_integer)
        Offsets are relative to ``tile_cache`` origin (row=0, col=0 = top-left).
        kernel_integer is the rarest non-ego pixel class in the tile —
        the visual marker placed by the ARC designer at the activation
        point.
    """
    if tile_cache.size == 0:
        return 0, 0, -1

    flat = tile_cache.flatten()

    # Build frequency map excluding ego classes
    counts: Counter = Counter()
    for v in flat:
        iv = int(v)
        if iv not in ego_value_set:
            counts[iv] += 1

    if not counts:
        # Tile was all ego — fallback
        return 0, 0, -1

    # Rarest non-ego integer
    rarest_value, _ = min(counts.items(), key=lambda x: x[1])

    # Find first occurrence (top-left, row-major order)
    positions = np.where(tile_cache == rarest_value)
    kernel_row = int(positions[0][0])
    kernel_col = int(positions[1][0])

    return kernel_row, kernel_col, rarest_value


__all__ = ["reconstruct_lever_kernel"]

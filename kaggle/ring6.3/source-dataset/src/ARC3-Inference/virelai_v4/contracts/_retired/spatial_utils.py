"""
contracts/spatial_utils.py

Pure spatial geometry utilities shared across phase boundaries.

These are stateless functions with no phase-specific dependencies.
Any phase may import from this module without violating phase sovereignty.

WO-HYGIENE-02: extracted from execution/lever_history.py to resolve
  cross-phase import in discovery/physics/cycle_probe.py.
"""

from __future__ import annotations

from typing import FrozenSet, Optional, Tuple


def estimate_direction_from_coords(
    coords_a: FrozenSet[Tuple[int, int]],
    coords_b: FrozenSet[Tuple[int, int]],
) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    """Estimate spatial direction from two consecutive changed-pixel sets.

    coords_a: pixels that changed from S(n-1) → S(n)
    coords_b: pixels that changed from S(n)   → S(n+1)

    Returns (direction_vector, direction_label) where direction_label is one of
    "UP" / "DOWN" / "LEFT" / "RIGHT".  Returns (None, None) when input is empty,
    motion is zero, or the centroid shift is diagonal (neither axis dominates).

    Pure function — no I/O, no side effects.  WO-KNIFE-12.
    """
    if not coords_a or not coords_b:
        return None, None
    rows_a = [r for r, _ in coords_a]
    rows_b = [r for r, _ in coords_b]
    cols_a = [c for _, c in coords_a]
    cols_b = [c for _, c in coords_b]
    dr = sum(rows_b) / len(rows_b) - sum(rows_a) / len(rows_a)
    dc = sum(cols_b) / len(cols_b) - sum(cols_a) / len(cols_a)
    abs_dr, abs_dc = abs(dr), abs(dc)
    if abs_dr == 0.0 and abs_dc == 0.0:
        return None, None
    dominant = max(abs_dr, abs_dc)
    if min(abs_dr, abs_dc) > dominant * 0.5:
        return None, None  # diagonal — ambiguous
    if abs_dr >= abs_dc:
        return (int(round(dr)), 0), ("DOWN" if dr > 0 else "UP")
    return (0, int(round(dc))), ("RIGHT" if dc > 0 else "LEFT")

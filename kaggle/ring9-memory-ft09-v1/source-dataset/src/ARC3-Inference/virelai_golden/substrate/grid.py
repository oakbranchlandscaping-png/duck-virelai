"""SUBSTRATE · grid — the frame as handed, total.

Ladder step 1 (observe). Canon: 01 §3 totality — every cell holds a value; the grid total is
read from the shape at runtime, never a literal.

Transcription origin (R-C): none for the type itself; the 2-D contract and the "extract the
settled grid before scanning" rule come from virelai_v4/perception/grid_scan.py:414-429
(`scan_grid` rejects 3-D input) and perception/animation.py (settled grid = last layer, G1).
What it proved: rejected 3-D input on every canary since 2026-04 (tests/perception/
test_grid_scan.py::test_rejects_3d_input).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

Grid = np.ndarray  # 2-D, integer class ids; dtype int16 so class arithmetic never wraps


class NotAGrid(ValueError):
    """Raised loudly when a frame is not a 2-D integer array. Never coerced silently."""


def as_grid(rows: Sequence[Sequence[int]] | np.ndarray) -> Grid:
    """Return a 2-D int16 array. Raises NotAGrid on any other shape."""
    arr = np.asarray(rows)
    if arr.ndim != 2:
        raise NotAGrid(f"expected a 2-D grid, got {arr.ndim}-D with shape {arr.shape}")
    if arr.size == 0:
        raise NotAGrid(f"expected a non-empty grid, got shape {arr.shape}")
    if not np.issubdtype(arr.dtype, np.integer):
        raise NotAGrid(f"expected integer classes, got dtype {arr.dtype}")
    return arr.astype(np.int16, copy=False)


def settled(frame_layers: Sequence[Sequence[Sequence[int]]]) -> Grid:
    """The settled grid of a delivery: the LAST layer (G1). Multi-layer deliveries are
    animation; the record keeps the fact, the scan reads the settled grid."""
    if len(frame_layers) == 0:
        raise NotAGrid("a delivery with zero layers has no settled grid")
    return as_grid(frame_layers[-1])


def grid_total(grid: Grid) -> int:
    """H × W, read from the shape. Canon 01 §3: never a literal."""
    h, w = grid.shape
    return int(h) * int(w)

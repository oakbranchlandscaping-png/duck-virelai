"""SUBSTRATE · delivery — what the platform handed on one turn, classified structurally.

Ladder step 1 (observe). Canon: 03 §2 — a DELIVERY fact is never an outcome; a single-grid turn
reads SILENT however much the world moved. The interior layers of a multi-grid delivery are
animation; the settled grid is the last layer (G1).

Transcription origin (R-C): virelai_v4/perception/animation.py @ oracle-v4 (305 lines, read
whole) — `classify_press` with the WO-DELIVERY-CLASS-02 cross-node rule, and
`_interior_change_magnitude`; virelai_v4/capture/ledger_build.py:37-60 `delivery_of` (the one
producer, wrapping the classifier with the previous node's settled grid). What it proved:
DELIVERY ROSTER lines on both golden ls20 runs (2026-09-05) — run 1: 6 multi-grid of 262,
magnitudes 60 / 4012; run 2: 4 of 133 (post-level-up window), magnitude 3996.

The rule, transcribed exactly:
  SILENT      — one layer or fewer (nothing to adjudicate), or a multi-grid whose interior
                never moved
  UNCOMPARED  — multi-grid, and no predecessor exists
  EFFECTIVE   — multi-grid, and the settled grid differs from the PREVIOUS node's settled grid
  FLASH       — multi-grid, settled grids agree, interior moved

NOT transcribed: `emit_animation_turn_diag` (stderr diagnostic), `scan_layers`,
`transient_only_cells` (no ladder consumer yet — R-E), and the `_UNSET` intra-delivery
fallback: every golden caller supplies the predecessor or None, so the un-updated-caller
branch has no reader here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from virelai_golden.substrate.grid import Grid, as_grid
from virelai_golden.substrate.record import Record

SILENT = "SILENT"
FLASH = "FLASH"
EFFECTIVE = "EFFECTIVE"
UNCOMPARED = "UNCOMPARED"


@dataclass(frozen=True)
class Delivery:
    node: int
    layer_count: int
    klass: str
    magnitude: int  # cells changed across consecutive interior layers, summed


def _differs(a: Grid, b: Grid) -> bool:
    return a.shape != b.shape or bool(np.any(a != b))


def interior_magnitude(layers: Sequence[Grid]) -> int:
    """Sum over adjacent layer pairs of the changed-cell count. A shape change between adjacent
    layers counts as the larger layer's cell count (origin: animation.py:86-101)."""
    total = 0
    for a, b in zip(layers[:-1], layers[1:]):
        total += int(np.count_nonzero(a != b)) if a.shape == b.shape else int(max(a.size, b.size))
    return total


def classify(layers: Sequence[Grid], previous_settled: Optional[Grid]) -> Tuple[str, int]:
    """`(class, magnitude)` for one delivery, given the previous node's settled grid (None when
    there is no predecessor — an answer, not an omission)."""
    if len(layers) == 0:
        return SILENT, 0
    magnitude = interior_magnitude(layers)
    if len(layers) <= 1:
        return SILENT, magnitude
    if previous_settled is None:
        return UNCOMPARED, magnitude
    if _differs(previous_settled, layers[-1]):
        return EFFECTIVE, magnitude
    return (FLASH if magnitude > 0 else SILENT), magnitude


def deliveries(record: Record) -> Tuple[Delivery, ...]:
    """One Delivery per node, in order, each compared against its predecessor's settled grid.
    Whole game (R-H): the predecessor across a life or level boundary is still the predecessor —
    the class then says what the boundary did to the board."""
    out = []
    previous: Optional[Grid] = None
    for node in record.nodes:
        layers = [as_grid(layer) for layer in node.layers]
        klass, magnitude = classify(layers, previous)
        out.append(Delivery(node.index, len(layers), klass, magnitude))
        previous = layers[-1]
    return tuple(out)

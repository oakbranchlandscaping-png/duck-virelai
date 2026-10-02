"""SUBSTRATE · scan — rung 2, visual objects: the exact pair (class, cells), one frame.

INTERIM_O8. Canon 02 §2: objects are per-class 4-connected components — a convention imported
from human vision, NOT derived from CANON_1, which says objects partition the arithmetic.
CANON_4 O-8 is OPEN. This module is the labeled interim (D-2, ADR-0007): one function, one
caller, so the ruling, when made, is a file swap. No rung above may cite this partition as a
settled derivation.

Transcription origin (R-C): virelai_v4/perception/grid_scan.py:111-176 `_build_raw_regions`
(pass 1 only) and scipy_check.py (the loud import). What it proved: 4-connected per-class
components with a canonical label sort, deterministic across reruns, on every canary since
2026-04 (tests/perception/test_grid_scan.py: diagonal_not_connected, two_separate_regions,
canonical_ordering_stable_across_reruns). Passes 2–4 of the origin (perimeters, borders,
value summaries, HUD-strip zones with a 0.30 threshold and an elected background) are NOT
transcribed: no consumer on the ladder (R-E), and the zone heuristics are figure/ground
elections the doctrine forbids (01 §3, 02 §5.4).

The label. `region_id` is a per-scan sort rank — (area, class, emission order) — minted for
reproducibility. It is a LABEL, never an identity (R1). Identity lives on the worldline.

This vendored Ring 8 port deliberately replaces the original scipy labeler with an exact
four-neighbour flood fill.  The partition predicate is unchanged, while the passive tool no
longer adds a package that Duck itself does not require.  This is a dependency adapter, not a
second perceptual rule: the same diagonal, separation, and canonical-order tests remain the
contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import FrozenSet, Tuple

import numpy as np

from virelai_golden.substrate.grid import Grid, as_grid

INTERIM_O8 = "individuation: 4-connected per-class components; CANON_4 O-8 is OPEN (ADR-0007)"

Cell = Tuple[int, int]

# 4-connectivity: diagonal contact does not share an object (canon 02 §2).
_NEIGHBOURS_4 = ((-1, 0), (0, -1), (0, 1), (1, 0))


@dataclass(frozen=True)
class Region:
    """One visual object: the exact pair (class, cells). Any change is a NEW object."""

    region_id: int          # per-scan label — (area, class, emission) rank; never identity
    value: int              # the class integer
    cells: FrozenSet[Cell]  # exact footprint, stored verbatim (canon 02 §2: never a summary)

    @property
    def area(self) -> int:
        return len(self.cells)

    @cached_property
    def anchor(self) -> Cell:
        """North-west cell: (min row, min col). A render convenience, never an identity."""
        return (min(r for r, _ in self.cells), min(c for _, c in self.cells))

    @property
    def fingerprint(self) -> Tuple[int, FrozenSet[Cell]]:
        return (self.value, self.cells)


def scan_grid(grid: Grid) -> Tuple[Region, ...]:
    """Partition a 2-D grid into per-class 4-connected components (INTERIM_O8).

    Returns regions in canonical label order: area ascending, then class ascending, then
    emission order. The partition is exact by construction — every cell belongs to the
    component of its own value — and `partition_breaches` proves it per node.
    """
    grid = as_grid(grid)
    unique_vals = sorted(int(v) for v in np.unique(grid))

    provisional: list[tuple[int, int, FrozenSet[Cell]]] = []  # (emission, value, cells)
    emission = 0
    height, width = (int(grid.shape[0]), int(grid.shape[1]))
    for val in unique_vals:
        unseen = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if int(grid[row, col]) == val
        }
        while unseen:
            seed = min(unseen)
            unseen.remove(seed)
            component = {seed}
            stack = [seed]
            while stack:
                row, col = stack.pop()
                for dr, dc in _NEIGHBOURS_4:
                    neighbour = (row + dr, col + dc)
                    if neighbour in unseen:
                        unseen.remove(neighbour)
                        component.add(neighbour)
                        stack.append(neighbour)
            provisional.append((emission, val, frozenset(component)))
            emission += 1

    provisional.sort(key=lambda t: (len(t[2]), t[1], t[0]))
    return tuple(
        Region(region_id=i, value=val, cells=cells)
        for i, (_e, val, cells) in enumerate(provisional, start=1)
    )


def partition_breaches(grid: Grid, regions: Tuple[Region, ...]) -> Tuple[str, ...]:
    """Prove the partition per node (canon 02 §2). Returns the named breaches, empty if none.

    COVERING_BREAK  — an in-bounds cell owned by no region (the void, smuggled in).
    DISJOINT_BREAK  — a cell owned by two regions.
    CLASS_BREAK     — a region claiming a cell whose grid value is not the region's class.
    Under totality (01 §3) all three are recording defects, never honest misses.
    """
    grid = as_grid(grid)
    h, w = grid.shape
    owner: dict[Cell, int] = {}
    breaches: list[str] = []
    for reg in regions:
        for cell in reg.cells:
            if cell in owner:
                breaches.append(f"DISJOINT_BREAK cell={cell} regions={owner[cell]},{reg.region_id}")
            owner[cell] = reg.region_id
            r, c = cell
            if int(grid[r, c]) != reg.value:
                breaches.append(f"CLASS_BREAK cell={cell} region={reg.region_id} "
                                f"claims={reg.value} grid={int(grid[r, c])}")
    if len(owner) != h * w:
        missing = [(r, c) for r in range(h) for c in range(w) if (r, c) not in owner]
        breaches.append(f"COVERING_BREAK unowned={len(missing)} first={missing[:3]}")
    return tuple(breaches)

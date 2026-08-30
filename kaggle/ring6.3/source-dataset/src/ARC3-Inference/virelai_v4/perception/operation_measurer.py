"""
virelai_v4/perception/operation_measurer.py — Per-bracket operation measurement
(WO-A.2b, Physics Reframe NR-01).

Measures WHAT MOVED between a bracket of frames (prior, current) and names
the operation, exactly as GATE-P1-20260607-GO validated offline:

  1. scan both frames (grid_scan), run diff_scans (A.2a correspondence) —
     Pass 2 minimal-displacement is the load-bearing path for the movers.
  2. take the "moved" RegionDeltas and CLUSTER them by before-cell adjacency
     (Chebyshev <= 1): a multi-color glyph (e.g. vc33's {4,11} arrow) moves
     as several per-value regions that are spatially one object. The cluster
     is the measured object; its composition signature is its identity key.
  3. emit one MeasuredOperation per cluster: signature + displacement vector.

Pure measurement: no library access, no belief, no side effects.
The frame is truth; this reads how the truth moved.

Identity model (per WO-A.2b v2): the moved cluster is a per-bracket
descriptor, NOT a persistent Slot. Operations are attributed to the pressed
lever by the caller (library/physics_accumulator.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple

import numpy as np

from virelai_v4.perception.grid_scan import scan_grid
from virelai_v4.perception.scan_diff import RegionDelta, diff_scans

# Two mover regions belong to one physical object when (a) any pair of their
# before-cells is within Chebyshev distance 1 (8-adjacency, touching corners
# count — the vc33 glyph's 4-part and 11-part rows touch) AND (b) they move
# with the same vector — one rigid object has one displacement. Without (b),
# a field region sliding 1 row would merge with the glyph riding on it.
_CLUSTER_CHEBYSHEV = 1
_CLUSTER_COS_FENCE = 0.99
_CLUSTER_MAG_FENCE = 0.9


@dataclass(frozen=True)
class MeasuredOperation:
    """One physical object's measured operation across a single bracket."""
    signature: Tuple[Tuple[int, int], ...]   # sorted (value, area) of the cluster
    vector: Tuple[float, float]              # (d_row, d_col) centroid displacement
    region_count: int                        # per-value regions in the cluster
    # WO-EFFECT-STORE-RIGID (WO1): the cluster's BEFORE-cells (prior-frame
    # footprint), unioned across member regions. Carried so the accumulator can
    # resolve which library object moved (before-cell overlap). Default empty
    # for backward compatibility with callers that ignore it.
    before_cells: FrozenSet[Tuple[int, int]] = frozenset()


def _adjacent(cells_a: FrozenSet[Tuple[int, int]],
              cells_b: FrozenSet[Tuple[int, int]]) -> bool:
    """True when any cell pair across the two sets is Chebyshev <= 1."""
    for r, c in cells_a:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in cells_b:
                    return True
    return False


def _delta_vector(d: RegionDelta) -> Tuple[float, float]:
    return (d.centroid_after[0] - d.centroid_before[0],
            d.centroid_after[1] - d.centroid_before[1])


def _same_vector(va: Tuple[float, float], vb: Tuple[float, float]) -> bool:
    """Rigid-body condition: one object, one displacement (cos/mag fences)."""
    na = (va[0] ** 2 + va[1] ** 2) ** 0.5
    nb = (vb[0] ** 2 + vb[1] ** 2) ** 0.5
    if na < 1e-9 or nb < 1e-9:
        return na < 1e-9 and nb < 1e-9
    cos = (va[0] * vb[0] + va[1] * vb[1]) / (na * nb)
    mag = min(na, nb) / max(na, nb)
    return cos > _CLUSTER_COS_FENCE and mag > _CLUSTER_MAG_FENCE


def _cluster_movers(movers: List[RegionDelta],
                    cells_by_id: Dict[int, FrozenSet[Tuple[int, int]]]
                    ) -> List[List[RegionDelta]]:
    """Group moved deltas whose before-regions touch (single-link, BFS)."""
    n = len(movers)
    visited = [False] * n
    clusters: List[List[RegionDelta]] = []
    for i in range(n):
        if visited[i]:
            continue
        stack, members = [i], []
        visited[i] = True
        while stack:
            j = stack.pop()
            members.append(movers[j])
            cj = cells_by_id[movers[j].region_id_before]
            vj = _delta_vector(movers[j])
            for k in range(n):
                if (not visited[k]
                        and _same_vector(vj, _delta_vector(movers[k]))
                        and _adjacent(
                            cj, cells_by_id[movers[k].region_id_before])):
                    visited[k] = True
                    stack.append(k)
        clusters.append(members)
    return clusters


def _operation_from_cluster(
        members: List[RegionDelta],
        cells_by_id: Dict[int, FrozenSet[Tuple[int, int]]]) -> MeasuredOperation:
    """Composition signature + area-weighted mean displacement vector.

    before_cells is the union of the member regions' prior-frame cells — the
    cluster's before-footprint, used by the accumulator for subject resolution.
    """
    signature = tuple(sorted((d.value, d.area_before) for d in members))
    total = sum(d.area_before for d in members) or 1
    d_row = sum((d.centroid_after[0] - d.centroid_before[0]) * d.area_before
                for d in members) / total
    d_col = sum((d.centroid_after[1] - d.centroid_before[1]) * d.area_before
                for d in members) / total
    before_cells: FrozenSet[Tuple[int, int]] = frozenset().union(
        *(cells_by_id[d.region_id_before] for d in members))
    return MeasuredOperation(
        signature=signature,
        vector=(round(d_row, 4), round(d_col, 4)),
        region_count=len(members),
        before_cells=before_cells,
    )


@dataclass(frozen=True)
class ShapeChange:
    """A non-rigid press's measured shape change (WO-EFFECT-NONRIGID, WO3).

    Emitted when no rigid mover is measured (the area-conservation fence
    rejected everything) but cells still changed — a shape/volume change rather
    than a rigid translation. Descriptive only; no verb label (the
    PHYSICAL_RELATION_VOCABULARY contract is a STUB — the data names itself).
    """
    changed_cells: FrozenSet[Tuple[int, int]]   # cells where prev != grid
    total_changed_cells: int                    # |changed_cells|
    net_cell_change: int                        # +foreground gained, -lost


def measure_shape_change(prev_grid, grid) -> "ShapeChange | None":
    """Measure a non-rigid shape change between a bracket of frames.

    Returns a ShapeChange describing which cells changed and the net
    foreground gain/loss (relative to prev_grid's modal background), or None
    when nothing changed. Pure measurement: no library access. WO3 uses this
    on the accumulator's non-rigid (Path 3) branch so non-rigid presses
    accumulate LeverEffect entries (closing the substrate gap that left the
    captain stuck on non-rigid levers)."""
    prev = np.asarray(prev_grid, dtype=np.int32)
    cur = np.asarray(grid, dtype=np.int32)
    if prev.shape != cur.shape:
        return None
    changed_mask = prev != cur
    if not changed_mask.any():
        return None
    vals, counts = np.unique(prev, return_counts=True)
    background = int(vals[int(counts.argmax())])
    gained = int(((prev == background) & (cur != background)).sum())
    lost = int(((prev != background) & (cur == background)).sum())
    changed_cells = frozenset(
        (int(r), int(c)) for r, c in np.argwhere(changed_mask))
    return ShapeChange(
        changed_cells=changed_cells,
        total_changed_cells=int(changed_mask.sum()),
        net_cell_change=gained - lost,
    )


def measure_operations(prev_grid: np.ndarray,
                       grid: np.ndarray) -> List[MeasuredOperation]:
    """Measure all object operations across one bracket (prior, current).

    Returns one MeasuredOperation per moved object cluster. Empty list when
    nothing moved (e.g. a saturated lever press, or HUD-only frames — HUD
    counter drain manifests as grew/shrank, never "moved").
    """
    scan_b = scan_grid(np.asarray(prev_grid, dtype=np.int32))
    scan_a = scan_grid(np.asarray(grid, dtype=np.int32))
    diff = diff_scans(scan_b, scan_a)
    # P4 conservation fence (GATE-P1): a rigid mover conserves its area
    # EXACTLY. diff_scans' "moved" tolerates 15% area drift — that admits
    # field regions whose boundary slid (e.g. vc33's 0-field gaining/losing
    # rows behind a glyph). Those are medium, not object; the measured
    # operation is the conserved mover only.
    movers = [d for d in diff.regions_moved
              if d.delta_type == "moved" and d.area_before == d.area_after]
    if not movers:
        return []
    cells_by_id = {d.region_id_before:
                   scan_b.regions_by_id[d.region_id_before].cells
                   for d in movers}
    clusters = _cluster_movers(movers, cells_by_id)
    return [_operation_from_cluster(members, cells_by_id) for members in clusters]


__all__ = [
    "MeasuredOperation",
    "measure_operations",
    "ShapeChange",
    "measure_shape_change",
]

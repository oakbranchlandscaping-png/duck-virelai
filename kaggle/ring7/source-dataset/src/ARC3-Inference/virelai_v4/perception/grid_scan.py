"""
virelai_v4/perception/grid_scan.py — Spatial Measurement Layer.

Transplanted from V3.5 discovery/census/multi_scan.py.
Includes: Region, ValueSummary, SpatialZone, BorderInfo, GridScan,
          scan_grid(), has_animation_frames().
Excludes: diff_scans(), ScanDiff, RegionDelta (delta tools, later campaign).

GridScan is pure spatial measurement. No semantic labels. No beliefs.
The frame is truth. GridScan reads it.

Import sovereignty: imports from contracts/, virelai_v4.scipy_check (package-
root dependency gate), and stdlib/numpy. scipy is accessed via
virelai_v4/scipy_check.py, not directly. The gate lives at the package root
(not inside library/) to avoid the perception↔library cycle resolved in
WO-MINE-CLEAN-08.1.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

from virelai_v4.scipy_check import ndimage_label


# ---------------------------------------------------------------------------
# 4-connectivity structuring element
# ---------------------------------------------------------------------------

_CONNECTIVITY_4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int32)


# ---------------------------------------------------------------------------
# Dataclasses — transplanted identically from V3.5
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Region:
    """A contiguous region of identical pixel value with shape descriptors."""
    region_id: int
    value: int
    area: int
    centroid: Tuple[float, float]
    bbox: Tuple[int, int, int, int]     # (min_r, min_c, max_r, max_c) inclusive
    bbox_area: int
    compactness: float
    perimeter: int
    is_full_width: bool
    is_full_height: bool
    neighbor_ids: FrozenSet[int] = frozenset()
    cells: FrozenSet[Tuple[int, int]] = frozenset()


@dataclass(frozen=True)
class ValueSummary:
    """Aggregate statistics for all cells of one pixel value."""
    value: int
    total_cells: int
    num_components: int
    grid_fraction: float
    is_contiguous: bool
    bounding_box: Tuple[int, int, int, int]


@dataclass(frozen=True)
class SpatialZone:
    """A spatial zone (full_width_strip, full_height_strip, playfield)."""
    zone_type: str
    rows: Tuple[int, int]
    cols: Tuple[int, int]
    area: int
    values: FrozenSet[int] = frozenset()
    region_ids: FrozenSet[int] = frozenset()


@dataclass(frozen=True)
class BorderInfo:
    """Border between two adjacent pixel values."""
    value_a: int
    value_b: int
    cells_a: FrozenSet[Tuple[int, int]]
    cells_b: FrozenSet[Tuple[int, int]]
    length: int


@dataclass
class GridScan:
    """Complete spatial analysis of a single grid state."""
    grid_shape: Tuple[int, int]
    grid_area: int
    unique_values: List[int]
    num_unique: int
    regions: List[Region]
    regions_by_id: Dict[int, Region]
    regions_by_value: Dict[int, List[Region]]
    value_summaries: Dict[int, ValueSummary]
    borders: List[BorderInfo]
    adjacency_graph: Dict[int, Set[int]]
    value_adjacency: Dict[int, Set[int]]
    zones: List[SpatialZone]
    background_value: int


# ---------------------------------------------------------------------------
# Pass 1 — connected component detection (no perimeter/adjacency yet)
# ---------------------------------------------------------------------------

def _build_raw_regions(
    grid: np.ndarray,
    unique_vals: List[int],
    H: int,
    W: int,
) -> Tuple[List[Region], Dict[int, Set[Tuple[int, int]]], Dict[Tuple[int, int], int]]:
    """Detect connected components per pixel value. Returns provisional Regions
    (perimeter=0, neighbor_ids=empty) plus cell lookup structures for Pass 2."""
    regions: List[Region] = []
    region_cells_map: Dict[int, Set[Tuple[int, int]]] = {}
    cell_to_region: Dict[Tuple[int, int], int] = {}
    next_id = 1

    for val in unique_vals:
        labeled, num_features = ndimage_label(grid == val, structure=_CONNECTIVITY_4)
        for label_idx in range(1, num_features + 1):
            rows_arr, cols_arr = np.where(labeled == label_idx)
            area = int(len(rows_arr))
            if area == 0:
                continue
            rid = next_id
            next_id += 1
            cr, cc_f = float(rows_arr.mean()), float(cols_arr.mean())
            min_r, max_r = int(rows_arr.min()), int(rows_arr.max())
            min_c, max_c = int(cols_arr.min()), int(cols_arr.max())
            ba = (max_r - min_r + 1) * (max_c - min_c + 1)
            cells_set: Set[Tuple[int, int]] = set(zip(rows_arr.tolist(), cols_arr.tolist()))
            region_cells_map[rid] = cells_set
            for rc in cells_set:
                cell_to_region[rc] = rid
            regions.append(Region(
                region_id=rid, value=val, area=area,
                centroid=(cr, cc_f), bbox=(min_r, min_c, max_r, max_c),
                bbox_area=ba, compactness=area / ba if ba > 0 else 0.0,
                perimeter=0,
                is_full_width=(min_c == 0 and max_c == W - 1),
                is_full_height=(min_r == 0 and max_r == H - 1),
                neighbor_ids=frozenset(), cells=frozenset(cells_set),
            ))

    # WO-OCD-CANONICAL — renumber regions in canonical order.
    # Two-key sort: cell count ASC (smallest first), then class value ASC
    # (tiebreaker). Final tiebreaker: original emission order (preserves
    # determinism across reruns on the same spawn frame). The smallest
    # region in the spawn frame becomes R1; the largest becomes R(N). Every
    # downstream surface that reads region IDs (rankers, gates, tier
    # assessors, field card) operates against canonical numbering.
    # WO-B2-03 (AMENDMENT_RULING_LIB1 §2 layer 1): this mints region_id — a
    # PER-LEVEL SPAWN ORDINAL, a LABEL, never an identity. The sort's purpose is
    # reproducibility ("preserves determinism across reruns on the same spawn
    # frame"), a canonicalization claim, not a priority claim (RULING_LIB1 §2:
    # smallest-first is an accident of the mint, inherited not licensed). Earned
    # identity is the worldline; this is only its spawn label.
    indexed = list(enumerate(regions))
    indexed.sort(key=lambda i_r: (i_r[1].area, i_r[1].value, i_r[0]))
    canonical_regions: List[Region] = []
    canonical_cells_map: Dict[int, Set[Tuple[int, int]]] = {}
    canonical_cell_to_region: Dict[Tuple[int, int], int] = {}
    for new_id, (_emission_idx, region) in enumerate(indexed, start=1):
        canonical_regions.append(replace(region, region_id=new_id))
        old_cells = region_cells_map[region.region_id]
        canonical_cells_map[new_id] = old_cells
        for cell in old_cells:
            canonical_cell_to_region[cell] = new_id

    return canonical_regions, canonical_cells_map, canonical_cell_to_region


# ---------------------------------------------------------------------------
# Pass 2 — perimeters, adjacency, borders
# ---------------------------------------------------------------------------

def _compute_topology(
    grid: np.ndarray,
    regions: List[Region],
    H: int,
    W: int,
    cell_to_region: Dict[Tuple[int, int], int],
) -> Tuple[List[Region], Dict[int, Set[int]], Dict[int, Set[int]], List[BorderInfo]]:
    """Compute perimeters, region/value adjacency, and border cells (Pass 2)."""
    adjacency_graph: Dict[int, Set[int]] = {r.region_id: set() for r in regions}
    value_adjacency: Dict[int, Set[int]] = {int(v): set() for v in np.unique(grid)}
    border_cells_a: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}
    border_cells_b: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}
    perimeter_count: Dict[int, int] = {r.region_id: 0 for r in regions}

    for r in range(H):
        for c in range(W):
            rid = cell_to_region.get((r, c))
            if rid is None:
                continue
            val = int(grid[r, c])
            is_border = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= H or nc < 0 or nc >= W:
                    is_border = True
                    continue
                nrid = cell_to_region.get((nr, nc))
                if nrid is None or nrid == rid:
                    continue
                nval = int(grid[nr, nc])
                if nval != val:
                    is_border = True
                    adjacency_graph[rid].add(nrid)
                    value_adjacency[val].add(nval)
                    key = (min(val, nval), max(val, nval))
                    border_cells_a.setdefault(key, set())
                    border_cells_b.setdefault(key, set())
                    (border_cells_a[key] if val == key[0] else border_cells_b[key]).add((r, c))
            if is_border:
                perimeter_count[rid] += 1

    final_regions = [
        Region(
            region_id=reg.region_id, value=reg.value, area=reg.area,
            centroid=reg.centroid, bbox=reg.bbox, bbox_area=reg.bbox_area,
            compactness=reg.compactness, perimeter=perimeter_count[reg.region_id],
            is_full_width=reg.is_full_width, is_full_height=reg.is_full_height,
            neighbor_ids=frozenset(adjacency_graph[reg.region_id]),
            cells=reg.cells,
        )
        for reg in regions
    ]
    borders = sorted(
        [
            BorderInfo(
                va, vb,
                frozenset(border_cells_a[(va, vb)]),
                frozenset(border_cells_b.get((va, vb), set())),
                len(border_cells_a[(va, vb)]) + len(border_cells_b.get((va, vb), set())),
            )
            for (va, vb) in border_cells_a
        ],
        key=lambda b: b.length, reverse=True,
    )
    return final_regions, adjacency_graph, value_adjacency, borders


def _find_regions(
    grid: np.ndarray, H: int, W: int, unique_vals: List[int],
) -> Tuple[List[Region], Dict[int, Set[int]], Dict[int, Set[int]], List[BorderInfo]]:
    """Orchestrate Pass 1 + Pass 2. Returns final regions with topology."""
    raw_regions, _, cell_to_region = _build_raw_regions(grid, unique_vals, H, W)
    return _compute_topology(grid, raw_regions, H, W, cell_to_region)


# ---------------------------------------------------------------------------
# Pass 3 — per-value aggregate statistics
# ---------------------------------------------------------------------------

def _build_value_summary(
    regions: List[Region],
    unique_vals: List[int],
    grid_area: int,
) -> Dict[int, ValueSummary]:
    """Compute ValueSummary for each pixel value."""
    by_value: Dict[int, List[Region]] = {}
    for r in regions:
        by_value.setdefault(r.value, []).append(r)

    summaries: Dict[int, ValueSummary] = {}
    for val in unique_vals:
        regs = by_value.get(val, [])
        total = sum(r.area for r in regs)
        if regs:
            bb = (min(r.bbox[0] for r in regs), min(r.bbox[1] for r in regs),
                  max(r.bbox[2] for r in regs), max(r.bbox[3] for r in regs))
        else:
            bb = (0, 0, 0, 0)
        summaries[val] = ValueSummary(
            value=val, total_cells=total, num_components=len(regs),
            grid_fraction=total / grid_area if grid_area > 0 else 0.0,
            is_contiguous=(len(regs) == 1), bounding_box=bb,
        )
    return summaries


# ---------------------------------------------------------------------------
# Pass 4 — spatial zone detection (transplanted from V3.5 _detect_zones)
# ---------------------------------------------------------------------------

def _detect_row_strips(
    grid: np.ndarray, regions: List[Region], H: int, W: int,
    background_value: int, val_totals: Dict[int, int],
) -> Tuple[List[SpatialZone], Set[int]]:
    """Detect full-width HUD/border strips by scanning row signatures."""
    zones: List[SpatialZone] = []
    strip_rows_used: Set[int] = set()
    row_sigs = [tuple(sorted(set(int(v) for v in grid[r, :]))) for r in range(H)]
    i = 0
    while i < H:
        sig = row_sigs[i]
        if len(sig) <= 3:
            j = i + 1
            while j < H and row_sigs[j] == sig:
                j += 1
            strip_height = j - i
            if 1 <= strip_height <= max(3, H // 4):
                non_bg = frozenset(sig) - {background_value}
                if non_bg:
                    strip_region = grid[i:j, :]
                    concentrated = any(
                        val_totals.get(v, 0) > 0
                        and int(np.count_nonzero(strip_region == v)) / val_totals[v] >= 0.30
                        for v in non_bg
                    )
                    if concentrated:
                        rids = frozenset(reg.region_id for reg in regions
                                         if reg.bbox[0] >= i and reg.bbox[2] <= j - 1)
                        zones.append(SpatialZone(
                            zone_type="full_width_strip", rows=(i, j - 1),
                            cols=(0, W - 1), area=strip_height * W,
                            values=frozenset(sig), region_ids=rids,
                        ))
                        strip_rows_used.update(range(i, j))
            i = j
        else:
            i += 1
    return zones, strip_rows_used


def _detect_col_strips(
    grid: np.ndarray, regions: List[Region], H: int, W: int,
    background_value: int, val_totals: Dict[int, int],
) -> Tuple[List[SpatialZone], Set[int]]:
    """Detect full-height HUD/border strips by scanning column signatures."""
    zones: List[SpatialZone] = []
    strip_cols_used: Set[int] = set()
    col_sigs = [tuple(sorted(set(int(v) for v in grid[:, c]))) for c in range(W)]
    i = 0
    while i < W:
        sig = col_sigs[i]
        if len(sig) <= 3:
            j = i + 1
            while j < W and col_sigs[j] == sig:
                j += 1
            strip_width = j - i
            if 1 <= strip_width <= max(3, W // 4):
                non_bg = frozenset(sig) - {background_value}
                if non_bg:
                    strip_region = grid[:, i:j]
                    concentrated = any(
                        val_totals.get(v, 0) > 0
                        and int(np.count_nonzero(strip_region == v)) / val_totals[v] >= 0.30
                        for v in non_bg
                    )
                    if concentrated:
                        rids = frozenset(reg.region_id for reg in regions
                                         if reg.bbox[1] >= i and reg.bbox[3] <= j - 1)
                        zones.append(SpatialZone(
                            zone_type="full_height_strip", rows=(0, H - 1),
                            cols=(i, j - 1), area=H * strip_width,
                            values=frozenset(sig), region_ids=rids,
                        ))
                        strip_cols_used.update(range(i, j))
            i = j
        else:
            i += 1
    return zones, strip_cols_used


def _detect_playfield(
    regions: List[Region], H: int, W: int,
    strip_rows_used: Set[int], strip_cols_used: Set[int],
) -> Optional[SpatialZone]:
    """Return the playfield SpatialZone — the grid area after removing strips."""
    pf_rows = [r for r in range(H) if r not in strip_rows_used]
    pf_cols = [c for c in range(W) if c not in strip_cols_used]
    if not pf_rows or not pf_cols:
        return None
    pf_min_r, pf_max_r = min(pf_rows), max(pf_rows)
    pf_min_c, pf_max_c = min(pf_cols), max(pf_cols)
    pf_area = (pf_max_r - pf_min_r + 1) * (pf_max_c - pf_min_c + 1)
    pf_rids = frozenset(
        reg.region_id for reg in regions
        if pf_min_r <= reg.centroid[0] <= pf_max_r
        and pf_min_c <= reg.centroid[1] <= pf_max_c
    )
    return SpatialZone(
        zone_type="playfield", rows=(pf_min_r, pf_max_r), cols=(pf_min_c, pf_max_c),
        area=pf_area, values=frozenset(), region_ids=pf_rids,
    )


def _classify_zones(
    grid: np.ndarray, regions: List[Region], H: int, W: int, background_value: int,
) -> List[SpatialZone]:
    """Detect structural spatial zones: strips (HUD/border) and playfield."""
    val_totals = {int(v): int(np.count_nonzero(grid == v)) for v in np.unique(grid)}
    row_zones, strip_rows = _detect_row_strips(grid, regions, H, W, background_value, val_totals)
    col_zones, strip_cols = _detect_col_strips(grid, regions, H, W, background_value, val_totals)
    playfield = _detect_playfield(regions, H, W, strip_rows, strip_cols)
    zones = row_zones + col_zones
    if playfield is not None:
        zones.append(playfield)
    return zones


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_grid(grid: np.ndarray) -> GridScan:
    """Perform complete spatial analysis of a 2D grid. Call once per frame.

    Args:
        grid: 2D integer numpy array (values 0–15). Must be 2D — caller is
              responsible for extracting frame[-1] from 3D FrameData.

    Returns:
        GridScan containing all spatial properties.

    Raises:
        ValueError: If grid is not 2D.
    """
    if grid.ndim != 2:
        raise ValueError(f"scan_grid expects a 2D array, got {grid.ndim}D. "
                         "Extract frame[-1] before calling.")
    H, W = grid.shape
    grid_area = H * W
    unique_vals = sorted(int(v) for v in np.unique(grid))

    regions, adj_graph, val_adj, borders = _find_regions(grid, H, W, unique_vals)
    value_summaries = _build_value_summary(regions, unique_vals, grid_area)
    background_value = max(unique_vals, key=lambda v: value_summaries[v].total_cells)
    zones = _classify_zones(grid, regions, H, W, background_value)

    # WO-OCD-CANONICAL — iterate in canonical region_id order (== smallest
    # cell count first, ties by class value, final tiebreaker by original
    # emission order — see _build_raw_regions). Downstream library construction
    # iterates this list to populate LibraryObjects in canonical order; field
    # card and ranker reads inherit that order.
    regions.sort(key=lambda r: r.region_id)
    regions_by_id = {r.region_id: r for r in regions}
    regions_by_value: Dict[int, List[Region]] = {}
    for r in regions:
        regions_by_value.setdefault(r.value, []).append(r)

    return GridScan(
        grid_shape=(H, W), grid_area=grid_area,
        unique_values=unique_vals, num_unique=len(unique_vals),
        regions=regions, regions_by_id=regions_by_id,
        regions_by_value=regions_by_value, value_summaries=value_summaries,
        borders=borders, adjacency_graph=adj_graph,
        value_adjacency=val_adj, zones=zones,
        background_value=background_value,
    )


def has_animation_frames(frame_data: list) -> bool:
    """True if the frame contains more than one layer (animation frames present).

    The frame_data list is layers × rows × cols. frame[0] is the spawn grid,
    frame[-1] is the current grid. Intermediate entries are animation frames.
    Multiple layers are a signal — flashing animations are an adversarial pattern.
    Full animation analysis is a later campaign concern. This function labels the signal.
    """
    return len(frame_data) > 1

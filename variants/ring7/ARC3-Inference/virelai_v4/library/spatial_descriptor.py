"""
virelai_v4/library/spatial_descriptor.py — Perceptual component descriptors.

Transplanted from V3.5 observer/spatial_descriptor.py (WO-NAR-06).
V4 changes: import path updated (module docstring only; no logic changes).

Converts raw pixel grid into per-component bounding boxes, centroids, quadrant
labels, region labels, and salience scores.  Rung 3.5 of the Semantic
Compression Ladder — bridging raw pixel counts and relationships with shape
and position priors.

Pure function.  Same input → identical output.  No side effects.

Import sovereignty: stdlib and numpy only.
"""

from __future__ import annotations

import collections
import logging
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_BORDER_MARGIN: int = 2  # pixels from grid edge counted as "border"


# ---------------------------------------------------------------------------
# ComponentDescriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentDescriptor:
    """Geometric and perceptual description of one connected component.

    Produced by extract_spatial_descriptors().  Immutable: same data,
    same narrative every time.

    Fields:
        class_id          — pixel value (type_map key)
        component_index   — 0-based index within this class's components
        total_components  — number of connected components for this class
        pixel_count       — number of pixels in this component
        bounding_box      — (row_min, col_min, row_max, col_max) inclusive
        width             — col_max - col_min + 1
        height            — row_max - row_min + 1
        centroid          — (row, col) integer centroid
        quadrant          — Q1 (top-right) / Q2 (top-left) /
                            Q3 (bottom-left) / Q4 (bottom-right)
        region            — HUD / arena / border
        salience          — rarity × compactness in [0, 1]
        salience_rank     — 1 = most salient; set after full sort
    """
    class_id:         int
    component_index:  int
    total_components: int
    pixel_count:      int
    bounding_box:     Tuple[int, int, int, int]
    width:            int
    height:           int
    centroid:         Tuple[int, int]
    quadrant:         str
    region:           str
    salience:         float
    salience_rank:    int


# ---------------------------------------------------------------------------
# Low-level geometry helpers
# ---------------------------------------------------------------------------

def _flood_fill_components(mask: np.ndarray) -> List[List[Tuple[int, int]]]:
    """4-connected BFS flood fill on a boolean mask.

    Returns a list of connected components, each a list of (row, col) tuples.
    Order of components is raster-scan order of first pixel encountered.
    """
    H, W = mask.shape
    visited = np.zeros((H, W), dtype=bool)
    components: List[List[Tuple[int, int]]] = []
    for r in range(H):
        for c in range(W):
            if mask[r, c] and not visited[r, c]:
                queue: collections.deque = collections.deque()
                queue.append((r, c))
                visited[r, c] = True
                cells: List[Tuple[int, int]] = []
                while queue:
                    cr, cc = queue.popleft()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc2 = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc2 < W and mask[nr, nc2] and not visited[nr, nc2]:
                            visited[nr, nc2] = True
                            queue.append((nr, nc2))
                components.append(cells)
    return components


def _classify_quadrant(centroid_row: int, centroid_col: int, H: int, W: int) -> str:
    """Map integer centroid to Q1–Q4.

    Q1 = top-right   (row < H/2, col >= W/2)
    Q2 = top-left    (row < H/2, col <  W/2)
    Q3 = bottom-left  (row >= H/2, col <  W/2)
    Q4 = bottom-right (row >= H/2, col >= W/2)
    """
    top = centroid_row < H / 2
    right = centroid_col >= W / 2
    if top and right:
        return "Q1"
    if top:
        return "Q2"
    if not right:
        return "Q3"
    return "Q4"


def _classify_region(
    cells: List[Tuple[int, int]],
    row_min: int,
    col_min: int,
    row_max: int,
    col_max: int,
    H: int,
    W: int,
    hud_mask_arr: Optional[np.ndarray],
) -> str:
    """Classify component zone as HUD, border, or arena.

    HUD: >50% of component cells lie inside the HUD mask (cell-level check).
    border: any edge is within _BORDER_MARGIN pixels of the grid boundary.
    arena: everything else.
    """
    if hud_mask_arr is not None and cells:
        hud_count = sum(1 for r, c in cells if hud_mask_arr[r, c])
        if hud_count / len(cells) > 0.5:
            return "HUD"
    if (
        row_min < _BORDER_MARGIN
        or row_max >= H - _BORDER_MARGIN
        or col_min < _BORDER_MARGIN
        or col_max >= W - _BORDER_MARGIN
    ):
        return "border"
    return "arena"


# ---------------------------------------------------------------------------
# Component building
# ---------------------------------------------------------------------------

def _build_descriptor_unranked(
    class_id: int,
    cells: List[Tuple[int, int]],
    total_components: int,
    component_index: int,
    rarity: float,
    H: int,
    W: int,
    hud_mask_arr: Optional[np.ndarray],
) -> ComponentDescriptor:
    """Build a ComponentDescriptor (salience_rank=0) from raw BFS cell list."""
    rows = [c[0] for c in cells]
    cols = [c[1] for c in cells]
    row_min, row_max = min(rows), max(rows)
    col_min, col_max = min(cols), max(cols)
    width = col_max - col_min + 1
    height = row_max - row_min + 1
    pixel_count = len(cells)
    centroid_r = int(sum(rows) / pixel_count)
    centroid_c = int(sum(cols) / pixel_count)
    compactness = pixel_count / (width * height)
    salience = rarity * compactness
    quadrant = _classify_quadrant(centroid_r, centroid_c, H, W)
    region = _classify_region(cells, row_min, col_min, row_max, col_max, H, W, hud_mask_arr)
    return ComponentDescriptor(
        class_id=class_id,
        component_index=component_index,
        total_components=total_components,
        pixel_count=pixel_count,
        bounding_box=(row_min, col_min, row_max, col_max),
        width=width,
        height=height,
        centroid=(centroid_r, centroid_c),
        quadrant=quadrant,
        region=region,
        salience=salience,
        salience_rank=0,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_spatial_descriptors(
    spawn_frame: np.ndarray,
    hud_mask: Optional[np.ndarray] = None,
    ego_classes: Optional[Set[int]] = None,
) -> List[ComponentDescriptor]:
    """Extract per-component spatial descriptors from spawn_frame.

    Runs 4-connected BFS flood fill on each pixel class (excluding ego_classes).
    Returns descriptors sorted by salience descending; salience_rank 1 = most
    salient.

    Salience = rarity × compactness, where:
      rarity      = 1.0 − (class_total_pixels / max_class_total)
      compactness = pixel_count / (width × height)

    Pure function.  No side effects.

    Args:
        spawn_frame: 2-D integer pixel array (H, W).
        hud_mask:    Optional 2-D boolean mask; True rows classified as HUD.
        ego_classes: Pixel values to skip (agent classes).

    Returns:
        List[ComponentDescriptor] sorted descending by salience.
    """
    frame = np.asarray(spawn_frame, dtype=np.int32)
    H, W = frame.shape

    hud_mask_arr: Optional[np.ndarray] = None
    if hud_mask is not None:
        hud_mask_arr = np.asarray(hud_mask, dtype=bool)
        if not hud_mask_arr.any():
            hud_mask_arr = None

    class_ids, counts = np.unique(frame, return_counts=True)
    class_totals = {int(cid): int(ct) for cid, ct in zip(class_ids, counts)}
    max_total = max(class_totals.values()) if class_totals else 1

    _ego = ego_classes or set()
    unranked: List[ComponentDescriptor] = []

    for class_id in sorted(class_totals.keys()):
        if class_id in _ego:
            continue
        rarity = 1.0 - (class_totals[class_id] / max_total)
        mask = frame == class_id
        components = _flood_fill_components(mask)
        n_comp = len(components)
        for idx, cells in enumerate(components):
            desc = _build_descriptor_unranked(
                class_id=class_id,
                cells=cells,
                total_components=n_comp,
                component_index=idx,
                rarity=rarity,
                H=H,
                W=W,
                hud_mask_arr=hud_mask_arr,
            )
            unranked.append(desc)

    unranked.sort(key=lambda d: d.salience, reverse=True)

    ranked: List[ComponentDescriptor] = []
    for rank, desc in enumerate(unranked, start=1):
        ranked.append(ComponentDescriptor(
            class_id=desc.class_id,
            component_index=desc.component_index,
            total_components=desc.total_components,
            pixel_count=desc.pixel_count,
            bounding_box=desc.bounding_box,
            width=desc.width,
            height=desc.height,
            centroid=desc.centroid,
            quadrant=desc.quadrant,
            region=desc.region,
            salience=desc.salience,
            salience_rank=rank,
        ))
    return ranked


__all__ = ["ComponentDescriptor", "extract_spatial_descriptors"]

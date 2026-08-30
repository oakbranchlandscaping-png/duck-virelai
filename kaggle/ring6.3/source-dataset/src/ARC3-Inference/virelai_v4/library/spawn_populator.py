"""virelai_v4/library/spawn_populator.py — Spawn-time library population.

Relocated from library/library_sync.py (WO-MINE-CLEAN-05-PHASE-1).
This module contains the spawn-path library population — the functions
that run once per level on the spawn frame to initialize the SemanticLibrary
from a GridScan.

Single Responsibility: read GridScan + initial frame state, write initial
SemanticLibrary objects. Does not process deltas, does not classify by
behavior, does not derive secondary artifacts from classified state.

Import sovereignty: contracts/, library/, perception/, stdlib/numpy only.
No imports from targeting/, strategy/, memory/.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import (
    LibraryObject,
    SDKAction,
    SemanticLibrary,
)
from virelai_v4.perception.grid_scan import GridScan, Region

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Position descriptor — human-readable centroid label
# ---------------------------------------------------------------------------

def _position_label(centroid: Tuple[float, float], rows: int, cols: int) -> str:
    """Produce a human-readable position from a region's centroid."""
    cr, cc = centroid
    # Vertical third
    if cr < rows / 3:
        v = "top"
    elif cr < 2 * rows / 3:
        v = "center"
    else:
        v = "bottom"
    # Horizontal third
    if cc < cols / 3:
        h = "left"
    elif cc < 2 * cols / 3:
        h = "center"
    else:
        h = "right"

    if v == "center" and h == "center":
        return "center"
    if v == "center":
        return h
    if h == "center":
        return v
    return f"{v}-{h}"


# ---------------------------------------------------------------------------
# Shape descriptor — from bounding box
# ---------------------------------------------------------------------------

def _shape_label(bbox: Tuple[int, int, int, int], area: int, bbox_area: int) -> str:
    """Produce a shape description from a region's bounding box."""
    min_r, min_c, max_r, max_c = bbox
    h = max_r - min_r + 1
    w = max_c - min_c + 1
    if area == bbox_area:
        return f"{h}x{w}"
    return f"{h}x{w}*"


# ---------------------------------------------------------------------------
# Layer assignment — foreground vs background
# ---------------------------------------------------------------------------

def _layer_for_region(region: Region, background_value: int) -> str:
    """Determine layer based on whether region is the background value."""
    if region.value == background_value:
        return "BACKGROUND"
    return "FOREGROUND"


# ---------------------------------------------------------------------------
# Count-like — how many other regions share the same class_id
# ---------------------------------------------------------------------------

def _compute_count_like(regions: List[Region]) -> Dict[int, int]:
    """For each region, count how many OTHER regions share its pixel value."""
    value_counts: Dict[int, int] = {}
    for r in regions:
        value_counts[r.value] = value_counts.get(r.value, 0) + 1
    # count_like = total with same value - 1 (exclude self)
    return {r.region_id: value_counts[r.value] - 1 for r in regions}


# ---------------------------------------------------------------------------
# Mode A — Spawn population
# ---------------------------------------------------------------------------

def _populate_from_scan(
    library: SemanticLibrary,
    grid_scan: GridScan,
    available_actions: List[int],
    game_id: str,
) -> None:
    """Mode A: populate the library from a GridScan on the first frame."""
    rows, cols = grid_scan.grid_shape
    count_like = _compute_count_like(grid_scan.regions)

    for region in grid_scan.regions:
        obj = LibraryObject(
            region_id=region.region_id,
            class_id=region.value,
            cells=region.cells,
            cell_count=region.area,
            shape_desc=_shape_label(region.bbox, region.area, region.bbox_area),
            zone="",  # WO-06a: zone is not a classification input
            position_desc=_position_label(region.centroid, rows, cols),
            layer=_layer_for_region(region, grid_scan.background_value),
            count_like=count_like.get(region.region_id, 0),
            role=LibraryRole.UNKNOWN,
            confidence=0.0,
            # WO-C5-02: baseline pixel counts for LC rate/budget estimation.
            # initial_cell_count is write-once; current_cell_count updates each Mode B.
            initial_cell_count=region.area,
            current_cell_count=region.area,
        )
        library.add_object(obj)

    # Header
    library.header.game_id = game_id
    library.header.grid_rows = rows
    library.header.grid_cols = cols

    # SDK actions — one entry per available action, status UNTESTED
    for action_id in available_actions:
        if action_id not in library.sdk_actions:
            library.sdk_actions[action_id] = SDKAction(action_id=action_id)

    logger.info(
        f"Library spawn: {len(library.objects)} objects, "
        f"{len(library.sdk_actions)} SDK actions for {game_id}"
    )

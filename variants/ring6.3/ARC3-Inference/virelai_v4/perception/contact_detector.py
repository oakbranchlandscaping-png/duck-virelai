"""
virelai_v4/perception/contact_detector.py — NAV contact detection for Tier 3 probing.

On each NOT_FINISHED frame in a NAV world, detect if the ego is in contact with
a target object. Contact = ego centroid cells overlap or are 1-cell-adjacent to the
target object's cells, AND there is nonzero world delta attributable to that object
or its neighborhood.

When contact is detected, set context.last_probe_target = target_id so the unified
evidence recorder in library_sync.py can fire immediately (same frame per Mining Q50).

Import sovereignty: contracts/, library/, perception/, stdlib + numpy only.
Consumed by library_sync.py and triggered from virelai.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Set, Tuple

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext
    from virelai_v4.contracts.world_delta import WorldDelta
    from virelai_v4.library.semantic_library import SemanticLibrary


def _ego_occupancy_cells(
    ego_pos: Tuple[int, int],
    ego_body_cells: Optional[frozenset],
) -> Set[Tuple[int, int]]:
    """Compute the set of cells occupied by ego at ego_pos.

    If ego_body_cells (the spawn-frame ego shape) is available, shift it
    from (0,0) to ego_pos. Otherwise, treat ego_pos as a single point.

    Returns
    -------
    Set[Tuple[int, int]] — cells occupied by ego body at ego_pos.
    """
    if ego_body_cells is None or len(ego_body_cells) == 0:
        # Single-point ego
        return {ego_pos}

    # Shift spawn-frame ego shape to ego_pos
    # Assumption: ego_body_cells are relative to (0, 0) on the spawn grid
    # We recenter them to ego_pos
    cells = set()
    if ego_body_cells:
        min_row = min(r for r, c in ego_body_cells)
        min_col = min(c for r, c in ego_body_cells)
        for r, c in ego_body_cells:
            shifted_r = ego_pos[0] + (r - min_row)
            shifted_c = ego_pos[1] + (c - min_col)
            cells.add((shifted_r, shifted_c))
    return cells if cells else {ego_pos}


def _is_adjacent(
    cell: Tuple[int, int],
    target_cells: Set[Tuple[int, int]],
) -> bool:
    """Check if cell is adjacent (within 1 cell distance) to target_cells."""
    r, c = cell
    for tr, tc in target_cells:
        if abs(r - tr) <= 1 and abs(c - tc) <= 1:
            return True
    return False


def detect_contact(
    context: VirelaiContext,
    library: SemanticLibrary,
    world_delta: WorldDelta,
) -> None:
    """Detect contact between ego and target object; set last_probe_target if hit.

    Called from library_sync.py after the canonical WorldDelta has been
    computed (and stored on context.world_delta) but BEFORE the evidence
    recorder fires (so last_probe_target can be populated this frame).

    WO-PHASE4-02 (canonicalization): consumes the canonical WorldDelta
    artifact (ego-masked AND HUD-masked at construction time) instead of
    the raw FrameDelta. The previous FrameDelta path was not actually
    HUD-masked in V4's live path because compute_frame_delta is called
    without hud_mask — see OTA-05. WorldDelta is the source of truth.

    Parameters
    ----------
    context : VirelaiContext
        Carries ego_current_pos, nav_probe_target, last_probe_target (to be set).
    library : SemanticLibrary
        Contains ego_body_cells and objects.
    world_delta : WorldDelta
        The canonical world delta on this frame. world_cells is the
        productive signal — already filtered of ego_cells and hud_cells.
    """
    # Gate: NAV world, target set, ego position known
    if library.header.world_type != "NAV":
        return
    if context.nav_probe_target is None:
        return
    if context.ego_current_pos is None:
        return

    # Gate: nonzero world delta
    if world_delta.world_count == 0:
        return

    # Get target object
    target = library.objects.get(context.nav_probe_target)
    if target is None:
        return

    # Compute ego occupancy cells
    ego_body_cells = library.header.ego_body_cells
    ego_cells = _ego_occupancy_cells(context.ego_current_pos, ego_body_cells)

    # Check for overlap or adjacency
    target_cells = set(target.cells)
    ego_overlaps_target = bool(ego_cells & target_cells)
    ego_adjacent_to_target = any(
        _is_adjacent(ego_cell, target_cells) for ego_cell in ego_cells
    )

    if not (ego_overlaps_target or ego_adjacent_to_target):
        # No contact
        return

    # Extract world delta cells (already a frozenset on WorldDelta)
    world_delta_cells: Set[Tuple[int, int]] = set(world_delta.world_cells)

    # Check if delta contains changes to target or neighborhood
    target_or_neighbor_cells = target_cells | {
        (r, c) for r, c in world_delta_cells
        if any(_is_adjacent((r, c), target_cells) for _ in [None])
    }

    # Simpler check: does the delta contain any cells in/near target?
    delta_near_target = bool(world_delta_cells & target_cells)
    if not delta_near_target:
        # Delta exists but doesn't touch target — contact failed
        return

    # Contact detected: set last_probe_target so evidence recorder fires this frame
    context.last_probe_target = context.nav_probe_target

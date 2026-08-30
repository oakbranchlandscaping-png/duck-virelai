"""
virelai_v4/library/cell_evidence_builder.py — CellEvidence construction helper.

Extracted from library_sync.py (WO-RM-03 headroom extraction) to keep
library_sync.py within the 800-line Yellow tier ceiling.

Builds a CellEvidence dataclass from per-cell CellHistory for one LibraryObject.
Called inside the classification pass in classification_pass._classify_objects.

Import sovereignty: library/ and stdlib only.
"""
from __future__ import annotations

from typing import Dict, Optional, Set, Tuple, TYPE_CHECKING

from virelai_v4.library.role_classifier import CellEvidence
from virelai_v4.cybernetic.cell_history import CellHistory, is_toggle

if TYPE_CHECKING:
    from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary

# Minimum total actions observed before any object is classified.
# Must be kept in sync with classification_pass.MIN_CLASSIFY_ACTIONS.
_MIN_CLASSIFY_ACTIONS: int = 3


def build_cell_evidence(
    obj: "LibraryObject",
    cell_history: Optional[Dict[Tuple[int, int], CellHistory]],
    library: "SemanticLibrary",
    total_actions: int,
) -> Optional[CellEvidence]:
    """Build a CellEvidence dataclass from CellHistory for one LibraryObject.

    Aggregates evidence across every cell in obj.cells.
    Returns None if cell_history is None or total_actions < _MIN_CLASSIFY_ACTIONS.
    Returns a zero-evidence CellEvidence when cells are absent from history —
    the classifier needs to see zero-evidence objects to assign STATIC candidates.
    """
    if cell_history is None:
        return None
    if total_actions < _MIN_CLASSIFY_ACTIONS:
        return None

    # Set of cells belonging to OTHER objects — used to filter co-change counts.
    other_cells: Set[Tuple[int, int]] = set()
    for rid, other_obj in library.objects.items():
        if rid != obj.region_id:
            other_cells.update(other_obj.cells)

    agg_change_count      = 0
    agg_cells_changed     = 0
    agg_any_toggle        = False
    agg_actions: Set[int] = set()
    agg_effect_pixels     = 0
    agg_obs_depth         = 0   # max len(ch.steps) across cells
    agg_cell_obs_depth    = 0   # sum of len(ch.steps) across cells
    max_step_seen         = -1

    for coord in obj.cells:
        ch = cell_history.get(coord)
        if ch is None:
            continue
        agg_change_count  += ch.change_count
        if ch.change_count > 0:
            agg_cells_changed += 1
        # Toggle detection — Law 6: CellHistory evidence takes priority
        if not agg_any_toggle and is_toggle(ch):
            agg_any_toggle = True
        agg_actions.update(ch.actions)
        step_count = len(ch.steps)
        agg_cell_obs_depth += step_count
        if step_count > agg_obs_depth:
            agg_obs_depth = step_count
        if ch.steps:
            s = max(ch.steps)
            if s > max_step_seen:
                max_step_seen = s
        # Co-change with OTHER objects' cells → proxy for effect_pixel_count
        for other_coord, co_count in ch.co_change_counts.items():
            if other_coord in other_cells:
                agg_effect_pixels += co_count

    # Actions since last observed change — used by _confidence_static.
    # Future campaign: replace with a per-object consecutive-inert counter.
    if max_step_seen >= 0:
        cell_inert_depth = total_actions - max_step_seen
    else:
        cell_inert_depth = total_actions   # never changed

    return CellEvidence(
        change_count=agg_change_count,
        cells_changed=agg_cells_changed,
        any_toggle=agg_any_toggle,
        total_changes=agg_change_count,    # same: cumulative changes across cells
        inert_depth=0,                     # Future campaign: consecutive-inert tracking
        regime_confidence=0.5,             # Future campaign: populate from world-type evidence
        observation_depth=agg_obs_depth,
        lever_confidence=0.0,              # Future campaign: populate from lever evidence
        cell_observation_depth=agg_cell_obs_depth,
        effect_pixel_count=agg_effect_pixels,
        contact_count=len(agg_actions),    # proxy: distinct action types that caused change
        all_profiled=False,                # Future campaign: set when all cells >= N observations
        cell_inert_depth=cell_inert_depth,
        # Action Independence Metric (WO-C5-01/02) — sourced from LibraryObject counters
        actions_observed=obj.actions_observed,
        action_independence_ratio=obj.action_independence_ratio,
    )


__all__ = ["build_cell_evidence"]

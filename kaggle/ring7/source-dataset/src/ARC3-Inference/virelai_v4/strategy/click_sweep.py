"""
virelai_v4/strategy/click_sweep.py — CLICK sweep driver (WO-04).

Ports V3.5's proven sweep architecture into V4. Replaces the queue-based
priority-queue-plus-attribution Tier 4 CLICK approach that produced zero
lever classifications across nine work orders.

Two public functions:
    build_sweep_list        — builds ordered probe list from library objects
    select_click_sweep_probe — drives one probe per Tier 4 CLICK frame

Private salience fallback:
    _v35_salience_score     — ported from V3.5 salience_scorer.py; invoked only
                              when rank_unattributed_objects returns < 3 candidates.

Note: update_sweep_from_outcome was relocated to
library/sweep_updater.py under WO-MINE-CLEAN-04 to break the library↔strategy
module-top import cycle.

Import sovereignty:
    Imports from contracts/, library/, strategy/investigation_priority.py.
    Does NOT import from perception/, targeting/.

V3.5 mining findings:
    Source: Universal_Solver_v3/world_characterization/anchoring/salience_scorer.py
    Formula: 0.40*rarity + 0.30*compactness + 0.20*isolation + 0.10*boundary_contact
    V3.5 K_INERT = 2 (per-operator saturation in dopl_policy.py) — different concept
    from sweep-global K. WO-04 specifies K=8 for global consecutive-inerts termination.

WO-04 CLICK SWEEP
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from virelai_v4.contracts.probe_types import ProbeOutcome
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.region_geometry import representative_coordinate
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary
from virelai_v4.strategy.investigation_priority import rank_unattributed_objects

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

# Global consecutive NO_EFFECT probes before sweep terminates.
# WO-04 specified value; compare to V3.5 K_INERT=2 which was per-operator
# (different concept: V3.5 saturated individual objects; this counter is global).
CLICK_SWEEP_K_CONSECUTIVE_INERTS: int = 8

# Minimum candidates from rank_unattributed_objects before falling back to salience.
_RANKER_MIN_CANDIDATES: int = 3


# ---------------------------------------------------------------------------
# Private: V3.5 salience fallback
# ---------------------------------------------------------------------------

def _v35_salience_score(region: LibraryObject, grid_class_counts: Dict[int, int], total_pixels: int) -> float:
    """Port of V3.5's salience_scorer.compute_salience.

    Only invoked when rank_unattributed_objects returns fewer than 3 candidates.

    Weights (from Universal_Solver_v3/world_characterization/anchoring/salience_scorer.py):
        Rarity      0.40  — rare values carry more information per probe
        Compactness 0.30  — compact shapes signal deliberate structure
        Isolation   0.20  — isolated regions are more likely agents or targets
        Boundary    0.10  — boundary contact is a weak structural signal

    Rarity   = 1 - (class_pixel_count / total_pixels)
    Compactness  = cell_count / bbox_area  (simplified; V3.5 uses 4π·area/perimeter²
                   but we lack perimeter here, so use fill-ratio as proxy)
    Isolation = 1.0 (unknown without spatial map; conservative constant)
    Boundary  = True if any cell touches grid edge row 0/63 or col 0/63

    This is an approximation — the exact V3.5 formula requires perimeter and
    nearest-neighbour distance, which are not in LibraryObject. The weight
    structure is ported exactly; the sub-components use the best available
    proxy data.
    """
    W_RARITY: float = 0.40
    W_COMPACTNESS: float = 0.30
    W_ISOLATION: float = 0.20
    W_BOUNDARY: float = 0.10

    # Rarity: 1 - (class pixel count / total pixels)
    class_cells = grid_class_counts.get(region.class_id, 0)
    rarity = 1.0 - (class_cells / max(total_pixels, 1))

    # Compactness: fill ratio (cell_count / bbox_area)
    if region.cells:
        rows_list = [r for r, _ in region.cells]
        cols_list = [c for _, c in region.cells]
        bbox_h = max(rows_list) - min(rows_list) + 1
        bbox_w = max(cols_list) - min(cols_list) + 1
        bbox_area = bbox_h * bbox_w
        compactness = region.cell_count / max(bbox_area, 1)
    else:
        compactness = 0.0

    # Isolation: conservative constant (no nearest-neighbour data available)
    isolation = 1.0

    # Boundary contact: True if any cell touches grid edge
    # Use common grid dimensions 64×64; clamp conservatively
    boundary = False
    if region.cells:
        for r, c in region.cells:
            if r == 0 or c == 0 or r >= 63 or c >= 63:
                boundary = True
                break

    score = (
        W_RARITY * rarity
        + W_COMPACTNESS * compactness
        + W_ISOLATION * isolation
        + W_BOUNDARY * (1.0 if boundary else 0.0)
    )
    return score


# ---------------------------------------------------------------------------
# Public: build_sweep_list
# ---------------------------------------------------------------------------

def build_sweep_list(
    library: SemanticLibrary,
    arena_filter=None,
) -> List[int]:
    """Build the CLICK sweep list from the library's current objects.

    Returns region_ids sorted by investigation priority (highest first).

    Filters out: role == EGO, role == COUNTER, BACKGROUND-tagged objects.
    Includes: REACTIVE, STATIC, UNKNOWN objects.

    Ordering: uses rank_unattributed_objects as primary sort.
    Falls back to V3.5 salience (_v35_salience_score) if ranker returns
    fewer than 3 candidates.

    Parameters
    ----------
    library : SemanticLibrary
        Current library (read-only).
    arena_filter : callable, optional
        If provided, called with (region_id, LibraryObject) → bool; only
        objects where arena_filter returns True are included.

    Returns
    -------
    List[int]
        Ordered region_ids, highest priority first.
    """
    # Filter: exclude EGO, COUNTER, BACKGROUND-tagged
    eligible: Dict[int, LibraryObject] = {}
    for rid, obj in library.objects.items():
        if obj.role in (LibraryRole.EGO, LibraryRole.COUNTER):
            continue
        if getattr(obj, "is_background", False):
            continue
        if arena_filter is not None and not arena_filter(rid, obj):
            continue
        eligible[rid] = obj

    if not eligible:
        return []

    # Primary sort: rank_unattributed_objects (scores unattributed, REACTIVE-boosted)
    ranked_pairs = rank_unattributed_objects(library)  # [(region_id, score), ...]

    # Only keep ranked IDs that are in eligible set
    ranked_eligible = [(rid, score) for rid, score in ranked_pairs if rid in eligible]

    if len(ranked_eligible) >= _RANKER_MIN_CANDIDATES:
        # Ranker has enough signal — use it as-is
        ordered_ids = [rid for rid, _ in ranked_eligible]
        # Append eligible objects not in ranked list (attributed objects)
        ranked_set = {rid for rid, _ in ranked_eligible}
        unranked = [rid for rid in eligible if rid not in ranked_set]
        ordered_ids.extend(sorted(unranked))
        return ordered_ids

    # Fallback: V3.5 salience (fewer than 3 ranked candidates)
    logger.debug(
        "[SWEEP] rank_unattributed_objects returned %d candidates — falling back to V3.5 salience",
        len(ranked_eligible),
    )

    # Build class counts for salience computation
    class_counts: Dict[int, int] = {}
    total_pixels: int = 0
    for obj in library.objects.values():
        class_counts[obj.class_id] = class_counts.get(obj.class_id, 0) + obj.cell_count
        total_pixels += obj.cell_count

    salience_pairs: List[Tuple[float, int]] = []
    for rid, obj in eligible.items():
        if getattr(obj, "is_attributed", False):
            continue
        score = _v35_salience_score(obj, class_counts, total_pixels)
        salience_pairs.append((score, rid))

    # Sort: highest salience first; tiebreak: lowest region_id (determinism)
    salience_pairs.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return [rid for _, rid in salience_pairs]


# ---------------------------------------------------------------------------
# Public: select_click_sweep_probe
# ---------------------------------------------------------------------------

def select_click_sweep_probe(
    context: "VirelaiContext",
    library: SemanticLibrary,
) -> Optional[Tuple[int, Tuple[int, int]]]:
    """Return (region_id, (row, col)) for the next probe, or None if sweep complete.

    Checks termination FIRST:
    - sweep_index >= len(sweep_list) → return None, set sweep_complete=True
    - sweep_consecutive_inerts >= CLICK_SWEEP_K_CONSECUTIVE_INERTS → return None, set sweep_complete=True

    Rebuilds sweep list if:
    - sweep_list is empty, OR
    - sweep_built_for_level != context.last_level_seen

    Advances sweep_index. Records region_id in sweep_probed.
    Does NOT mutate library. Does NOT set last_probe_target_* (caller does that).

    Parameters
    ----------
    context : VirelaiContext
        Sweep state fields read and mutated in place.
    library : SemanticLibrary
        Current library (read-only, passed to build_sweep_list).

    Returns
    -------
    Optional[Tuple[int, Tuple[int, int]]]
        (region_id, (row, col)) or None on sweep termination.
    """
    current_level = context.last_level_seen

    # Level-advance rebuild: rebuild if level changed or list is empty
    if (not context.sweep_list or
            context.sweep_built_for_level != current_level):
        context.sweep_list = build_sweep_list(library)
        context.sweep_index = 0
        context.sweep_probed = set()
        context.sweep_consecutive_inerts = 0
        context.sweep_reactive_found = 0
        context.sweep_built_for_level = current_level
        context.sweep_complete = False
        logger.debug(
            "[SWEEP] Built sweep list: %d objects (level=%d)",
            len(context.sweep_list), current_level,
        )

    # Termination check 1: consecutive inerts
    if context.sweep_consecutive_inerts >= CLICK_SWEEP_K_CONSECUTIVE_INERTS:
        if not context.sweep_complete:
            logger.info(
                "[SWEEP] Terminating: consecutive_inerts=%d >= K=%d",
                context.sweep_consecutive_inerts, CLICK_SWEEP_K_CONSECUTIVE_INERTS,
            )
        context.sweep_complete = True
        return None

    # Termination check 2: list exhausted
    if context.sweep_index >= len(context.sweep_list):
        if not context.sweep_complete:
            logger.info(
                "[SWEEP] Terminating: sweep_index=%d >= len(sweep_list)=%d",
                context.sweep_index, len(context.sweep_list),
            )
        context.sweep_complete = True
        return None

    # Advance to next probe
    region_id = context.sweep_list[context.sweep_index]
    context.sweep_index += 1
    context.sweep_probed.add(region_id)

    # Resolve region to coordinate
    obj = library.objects.get(region_id)
    if obj is None or not obj.cells:
        # Region disappeared from library — skip silently, try next call
        logger.debug("[SWEEP] Region %d not in library or has no cells — skipping", region_id)
        # Return a sentinel that will be handled by caller as a valid (skipped) probe
        # Recurse one level to get the actual next probe
        return select_click_sweep_probe(context, library)

    row, col = representative_coordinate(set(obj.cells))
    return (region_id, (row, col))


__all__ = [
    "CLICK_SWEEP_K_CONSECUTIVE_INERTS",
    "build_sweep_list",
    "select_click_sweep_probe",
]

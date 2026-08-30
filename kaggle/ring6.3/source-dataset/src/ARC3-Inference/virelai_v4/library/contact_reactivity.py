"""
virelai_v4/library/contact_reactivity.py — Contact reactivity detection.

Ported from V3.5 ``Universal_Solver_v3_5/discovery/physics/contact_reactivity.py``
per WO-CAMPAIGN3-PHASE2-01 (May 2, 2026, Phase 2 CONTACT + LEVER DISCOVERY).

V3.5 inheritance: V3.5 production-grade contact reactivity detection
proven across forge campaigns (WO-FORGE-06-L3 + WO-FORGE-NAV-02
ceiling filter). PORT-WITH-V4-ADAPTATION per WO-PHASE2-00 §3.7
Option A (motion_model parameterization).

V4 ADAPTATION (per Strategy Chamber ratification at WO-PHASE2-00):
    The V3.5 ``motion_model`` parameter is replaced with plain ``int``
    parameters in V4:
        - ``replacement_mask_size`` → ``expected_replacement_size: int``
        - ``footprint_height/width`` → explicit ``int`` parameters

    V4 callers compute these from ``library.header.ego_body_cells``:
        - ``expected_replacement_size = 2 * len(ego_body_cells)``
        - ``footprint_height/width`` = ego_body_cells bounding box dims

    Rationale: V4 doesn't have V3.5's ``motion_model`` artifact (Option A
    scope deferred per Director Ruling 1; gambit pipeline not ported).
    Parameterization eliminates the dependency without behavioral change.

Two-family architecture: **raw-frame-measurer family**. Both
``detect_contact_reactivity`` and ``build_ego_replacement_mask``
operate on raw grids. They compute their own delta inline; do not
consume canonical WorldDelta. Per WO-PHASE2-00 §6.4 Path A
ratification, this mirrors V3.5 verbatim semantics. Phase 2
bootstrap §4 amended.

Key insight (V3.5):
    A normal ego move changes exactly ``replacement_mask_size`` pixels
    (two footprint-sized blocks: departing region + arriving region).
    Any pixels changed BEYOND that threshold mean something else also
    changed — the ego contacted an interactive element (a lever).

Ceiling filter (WO-FORGE-NAV-02):
    A delta covering > 25% of the grid area is classified as LIFE_RESET,
    not as lever activation. Life resets and death events produce
    near-total redraws (3000-4000px on 64×64 grids) that would otherwise
    create false NavLeverCandidates for death coordinates.

Public API:
    detect_contact_reactivity()   — test whether a step produced excess delta
    build_ego_replacement_mask()  — construct boolean mask of ego-expected pixels
    extend_hud_mask_rows()        — utility for HUD masking
    derive_common_classes()       — derives non-interactive class set
    detect_rare_class_contact()   — backup detection for small-effect levers
"""
from __future__ import annotations

from typing import FrozenSet, Iterable, Optional, Set, Tuple

import numpy as np


def detect_contact_reactivity(
    prev_grid: np.ndarray,
    new_grid: np.ndarray,
    expected_replacement_size: int,
    hud_mask: Optional[np.ndarray] = None,
    margin: int = 5,
) -> Tuple[bool, int, Optional[np.ndarray]]:
    """Detect whether an ego move activated a lever via contact.

    Compares total pixel change (excluding HUD) against the expected
    pixel-change budget for a normal ego move
    (``expected_replacement_size``, typically ``2 * len(ego_body_cells)``).
    If ``total_changed > expected + margin``, the step is classified as
    contact-reactive — something beyond the ego's own footprint changed.

    V3.5 source: ``discovery/physics/contact_reactivity.py:33-85``.

    V4 adaptation per WO-PHASE2-00 §3.7 Option A: ``motion_model`` parameter
    replaced with ``expected_replacement_size: int``. Caller supplies
    ``2 * len(library.header.ego_body_cells)`` (departing + arriving
    footprint regions).

    Args:
        prev_grid:                 Grid before env.step().
        new_grid:                  Grid after env.step().
        expected_replacement_size: Expected pixel-change budget for a
                                   normal ego move. V4 caller computes
                                   ``2 * len(ego_body_cells)``.
        hud_mask:                  Optional boolean array — True = HUD
                                   pixel (excluded from delta).
        margin:                    Tolerance above expected change to
                                   absorb noise (default 5).

    Returns:
        ``(is_reactive, excess_delta_count, full_delta_mask)`` where:
        - ``is_reactive``: True if delta exceeds ego replacement expectation
        - ``excess_delta_count``: pixels changed beyond ego movement budget
        - ``full_delta_mask``: boolean array of ALL changed (non-HUD) pixels,
          or None if not reactive
    """
    delta = (new_grid != prev_grid)
    if hud_mask is not None:
        delta = delta & ~hud_mask.astype(bool)

    total_changed = int(delta.sum())

    if total_changed <= expected_replacement_size + margin:
        return False, 0, None

    excess = total_changed - expected_replacement_size

    # WO-FORGE-NAV-02: Ceiling filter — classify massive deltas as LIFE_RESET.
    # A delta covering > 25% of the grid is a game-reset or death event, not a
    # lever activation. Do NOT create a NavLeverCandidate for death coordinates.
    grid_area = int(prev_grid.shape[0]) * int(prev_grid.shape[1])
    _life_reset_threshold = grid_area * 0.25  # 1024px on a 64×64 grid
    if excess > _life_reset_threshold:
        return False, 0, None

    return True, excess, delta


def extend_hud_mask_rows(hud_mask: Optional[np.ndarray]) -> Optional[np.ndarray]:
    """Extend a HUD mask to cover all pixels in every row that has any HUD pixel.

    WO-FORGE-NAV-FIX-01 Patch B: the raw hud_mask typically covers only the
    class pixels detected by ARR (e.g. life counter class). The fuel bar uses
    a different class in the same HUD rows and changes 2+ pixels per step.
    Extending to full rows masks the entire HUD strip, eliminating false
    contact-reactivity fires from the fuel counter.

    V3.5 source: ``discovery/physics/contact_reactivity.py:88-111``.

    Args:
        hud_mask: boolean array or None.

    Returns:
        Extended boolean array (same shape), or None if input was None.
    """
    if hud_mask is None:
        return None
    hud_rows = np.where(hud_mask.any(axis=1))[0]
    if len(hud_rows) == 0:
        return hud_mask
    extended = hud_mask.copy()
    for hr in hud_rows:
        extended[hr, :] = True
    return extended


def derive_common_classes(
    nav_atlas,
    background_value: Optional[int] = None,
    high_frequency_classes: Optional[Iterable[int]] = None,
) -> FrozenSet[int]:
    """Derive the set of 'common' (non-interactive) pixel classes.

    Common classes are floor, walls, ego body pixels, and any class that
    appears on more than 2.4% of the grid (>100 cells on a 64×64 grid).
    Rare classes are anything in a tile cache NOT in this set — they are
    candidates for interactive elements (levers, buttons, keys).

    V3.5 source: ``discovery/physics/contact_reactivity.py:114-149``.

    V4 adaptation: V3.5 reads ``state`` dict for ``grid_scan``; V4 caller
    extracts the relevant fields (``background_value`` from grid_scan if
    available; high-frequency class set) and passes them in. Eliminates
    the V3.5 ``state`` dict dependency that V4 doesn't have.

    Args:
        nav_atlas:            NavAtlas artifact (provides
                              ``blocked_classes``, ``ego_value_set``).
        background_value:     Optional grid_scan background class value.
        high_frequency_classes: Optional iterable of class IDs that appear
                              on >100 cells (V4 caller derives from
                              grid_scan value_summaries).

    Returns:
        ``frozenset`` of integer class IDs classified as common/non-interactive.
    """
    common: Set[int] = set()

    # Ego body pixels are never interactive from the ego's perspective.
    if hasattr(nav_atlas, "ego_value_set"):
        common.update(int(v) for v in nav_atlas.ego_value_set)

    # Blocked classes (walls, barriers) are structural, not interactive.
    if hasattr(nav_atlas, "blocked_classes"):
        common.update(int(v) for v in nav_atlas.blocked_classes)

    # Grid scan background and any high-frequency class.
    if background_value is not None:
        common.add(int(background_value))
    if high_frequency_classes is not None:
        common.update(int(v) for v in high_frequency_classes)

    return frozenset(common)


def detect_rare_class_contact(
    tile_cache: np.ndarray,
    ego_classes: FrozenSet[int],
    common_classes: FrozenSet[int],
) -> Tuple[bool, Set[int], int]:
    """Check whether the ego's destination tile contained rare-class pixels.

    Rare classes are those not in ``ego_classes`` or ``common_classes``. Their
    presence in the pre-move tile cache means the ego stepped on something
    potentially interactive — a lever, button, or key — even if the pixel
    delta was too small to cross the delta threshold.

    This is the backup detection path for small-effect NAV levers where the
    delta threshold (``expected_replacement_size + margin``) is insufficient.

    V3.5 source: ``discovery/physics/contact_reactivity.py:152-180``.

    Args:
        tile_cache:     2D numpy array of pre-move pixel values at destination.
        ego_classes:    frozenset/set of int — ego pixel classes to exclude.
        common_classes: frozenset/set of int — floor/wall/background to exclude.

    Returns:
        ``(has_rare, rare_classes, rare_count)`` where:
        - ``has_rare``:     True if any rare-class pixel was found in the tile.
        - ``rare_classes``: set of rare integer class IDs present in the tile.
        - ``rare_count``:   total count of rare-class pixels in the tile.
    """
    exclude = set(ego_classes) | set(common_classes)
    unique_in_tile = set(int(v) for v in np.unique(tile_cache))
    rare_in_tile = unique_in_tile - exclude
    if not rare_in_tile:
        return False, set(), 0
    rare_count = sum(int(np.sum(tile_cache == c)) for c in rare_in_tile)
    return True, rare_in_tile, rare_count


def build_ego_replacement_mask(
    prev_pos: Tuple[int, int],
    new_pos: Tuple[int, int],
    footprint_height: int,
    footprint_width: int,
    grid_shape: Tuple[int, ...],
) -> np.ndarray:
    """Build boolean mask of pixels expected to change from ego movement alone.

    Constructs two footprint-sized blocks: the departing region (where the
    ego was) and the arriving region (where the ego now is).

    V3.5 source: ``discovery/physics/contact_reactivity.py:183-227``.

    V4 adaptation per WO-PHASE2-00 §3.7 Option A: ``motion_model`` parameter
    replaced with explicit ``footprint_height: int`` and
    ``footprint_width: int``. Caller derives both from
    ``library.header.ego_body_cells`` bounding-box dimensions.

    IMPORTANT: uses ``prev_pos`` and ``new_pos`` as ego-footprint top-left
    coordinates. The centroid is corrupted for multi-class ego bodies
    (e.g. LS20 class9 + class12); top-left anchor is the correct position
    source.

    Args:
        prev_pos:         (row, col) top-left of ego footprint BEFORE the step.
        new_pos:          (row, col) top-left of ego footprint AFTER the step.
        footprint_height: V4 caller derives from ``ego_body_cells`` bounding box.
        footprint_width:  V4 caller derives from ``ego_body_cells`` bounding box.
        grid_shape:       Shape of the grid (for bounds clamping).

    Returns:
        Boolean numpy array, same shape as ``grid_shape[:2]``.
        True  = pixel expected to change due to ego movement.
        False = pixel NOT expected to change (so any change here is lever effect).
    """
    rows, cols = grid_shape[0], grid_shape[1]
    mask = np.zeros((rows, cols), dtype=bool)

    # Departing region — ego was here
    pr, pc = prev_pos
    r0 = max(0, pr)
    r1 = min(rows, pr + footprint_height)
    c0 = max(0, pc)
    c1 = min(cols, pc + footprint_width)
    mask[r0:r1, c0:c1] = True

    # Arriving region — ego is now here
    nr, nc = new_pos
    r0 = max(0, nr)
    r1 = min(rows, nr + footprint_height)
    c0 = max(0, nc)
    c1 = min(cols, nc + footprint_width)
    mask[r0:r1, c0:c1] = True

    return mask


__all__ = [
    "detect_contact_reactivity",
    "build_ego_replacement_mask",
    "extend_hud_mask_rows",
    "derive_common_classes",
    "detect_rare_class_contact",
]

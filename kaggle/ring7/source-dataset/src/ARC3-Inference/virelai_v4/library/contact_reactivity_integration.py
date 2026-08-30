"""
virelai_v4/library/contact_reactivity_integration.py — Phase 2 cybernetic loop wiring.

Per WO-CAMPAIGN3-PHASE2-01 (May 2, 2026) + WO-CAMPAIGN3-PHASE2-03 (May 3, 2026).

V4 testability idiom (per Phase 1 pattern firing #11): pure free function
that handles gating + V3.5 contact_reactivity invocation + NavAtlas
writeback + library role transition. The Virelai class's
``_record_contact_reactivity`` helper method is a thin wrapper around
this function so the substrate-update logic can be unit-tested without
constructing a Virelai instance (arcengine-coupled).

Composes with WO-04's ``library/nav_substrate_update.py`` pattern.

Two-family architecture: this module is the **integration layer**
between the raw-frame-measurer functions (``contact_reactivity``,
``lever_kernel_reconstruction``) and the aggregator-style consumers
(library role transitions, NavAtlas writebacks). The integration
layer reads raw grids (raw-frame-measurer family invocation) and
writes structured artifacts (NavLeverCandidate; library role).

Per WO-PHASE2-00 §10.1: contact detection runs only post-stride-probe;
NAV-only gating; runs after ``_record_nav_move`` so substrate state
Phase 1 just wrote is visible.

WO-CAMPAIGN3-PHASE2-03 (May 3, 2026) — backup detection wiring per
V3.5 caller pattern at ``execution/nav_executor.py:272-277`` (start-of-life
setup) + ``execution/contact_step_handler.py:551-578`` (per-step). Per
the six ratified decisions:
  - HUD mask extension via ``extend_hud_mask_rows`` per-frame (Decision 2)
  - Common-class derivation via ``derive_common_classes`` per-frame
    through ``_derive_common_classes_from_v4_substrate`` helper that
    extracts ``background_value`` + ``high_frequency_classes`` from
    ``context.grid_scan`` (Decision 1; V4 adapter for V3.5 ``state``
    dict access)
  - ``tile_cache`` lift to before primary detection so backup path has
    access (Decision 4)
  - Backup detection fall-through verbatim from V3.5: ``if not is_reactive
    and tile_cache.size > 0: detect_rare_class_contact(...)`` (Decision 3)
  - ``full_delta_mask`` recomputation only on backup-fire path (primary
    path keeps V4 efficiency; Decision 5)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

import numpy as np

from virelai_v4.contracts.nav_lever import NavLeverCandidate
from virelai_v4.library.contact_reactivity import (
    build_ego_replacement_mask,
    derive_common_classes,
    detect_contact_reactivity,
    detect_rare_class_contact,
    extend_hud_mask_rows,
)
from virelai_v4.library.lever_kernel_reconstruction import reconstruct_lever_kernel
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
# WO-CAMPAIGN3-PHASE2-05 (re-scoped): top-left anchor source per V3.5
# find_ego_anchor_position; replaces deprecated centroid-based anchor
# at the slice site. select_anchor_class picks the rarest ego class
# for find_ego_anchor_position to scan against (V3.5 pattern).
from virelai_v4.library.nav_atlas import find_ego_anchor_position
from virelai_v4.library.stride_probe import select_anchor_class

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.nav_atlas import NavAtlas
    from virelai_v4.library.semantic_library import SemanticLibrary


_INITIAL_CONFIDENCE = 0.5

# WO-CAMPAIGN3-PHASE2-03 — V3.5 dominant-class threshold per
# ``Universal_Solver_v3_5/discovery/physics/contact_reactivity.py:146``:
# classes appearing on more than 100 cells (≈2.4% of a 64×64 grid) are
# treated as common/non-interactive backgrounds. Verbatim from V3.5.
FREQUENCY_THRESHOLD = 100

logger = logging.getLogger(__name__)


def _ego_body_bounding_box(
    ego_body_cells,
) -> Tuple[int, int]:
    """Compute (height, width) of the ego_body_cells bounding box.

    V4 caller-side helper per WO-PHASE2-00 §3.7 Option A: derives
    footprint dimensions from spawn-frame ego footprint without
    needing V3.5's ``motion_model`` artifact.

    Returns (1, 1) for empty input (defensive single-pixel ego).
    """
    if not ego_body_cells:
        return 1, 1
    rows = [r for r, _ in ego_body_cells]
    cols = [c for _, c in ego_body_cells]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    return int(height), int(width)


def _find_containing_object_id(
    library: "SemanticLibrary",
    coordinate: Tuple[int, int],
) -> Optional[int]:
    """Find the library object whose cells contain ``coordinate``.

    Point-in-cells lookup against ``library.objects[*].cells``. Returns
    the first matching ``region_id`` (lowest by iteration order) or
    None if no object contains the coordinate (orphan case).
    """
    for region_id, obj in library.objects.items():
        if coordinate in obj.cells:
            return int(region_id)
    return None


def _derive_common_classes_from_v4_substrate(
    context: "VirelaiContext",
    nav_atlas: "NavAtlas",
) -> frozenset:
    """V4 adapter — extracts grid_scan inputs and invokes V4's parameterized
    ``derive_common_classes``.

    V3.5 reads ``state["grid_scan"]`` directly (per
    ``Universal_Solver_v3_5/discovery/physics/contact_reactivity.py:140-147``).
    V4's ``derive_common_classes`` was ported with parameter extraction
    (WO-PHASE2-01 §3 adaptation): the caller pulls ``background_value``
    and ``high_frequency_classes`` from the V4 ``GridScan`` artifact and
    passes them in.

    Per WO-PHASE2-03 Decision 1: computed per-frame (V3.5 once-per-life
    was caching, not architecture; V4 ``nav_atlas.blocked_classes`` grows
    during exploration so per-frame is more accurate).

    Returns ``frozenset()`` if ``context.grid_scan`` is unavailable
    (cold start, before grid_scan populates).
    """
    grid_scan = context.grid_scan
    if grid_scan is None:
        # Defensive: still derive from nav_atlas alone (ego_value_set +
        # blocked_classes) so callers always get a meaningful set.
        return derive_common_classes(
            nav_atlas,
            background_value=None,
            high_frequency_classes=None,
        )
    background_value = getattr(grid_scan, "background_value", None)
    value_summaries = getattr(grid_scan, "value_summaries", None) or {}
    high_frequency_classes = [
        v for v, summary in value_summaries.items()
        if getattr(summary, "total_cells", 0) > FREQUENCY_THRESHOLD
    ]
    return derive_common_classes(
        nav_atlas,
        background_value=background_value,
        high_frequency_classes=high_frequency_classes,
    )


def maybe_record_contact_reactivity(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    current_grid: Optional[np.ndarray],
    prev_grid: Optional[np.ndarray],
) -> Optional[NavLeverCandidate]:
    """Conditionally invoke contact_reactivity + lever_kernel_reconstruction.

    Returns
    -------
    Optional[NavLeverCandidate]
        ``None`` if the gate suppressed the call OR no contact reactivity
        detected (neither primary nor backup). Otherwise the constructed
        NavLeverCandidate (also appended to
        ``context.nav_atlas.nav_lever_candidates`` and written to
        ``contacted_sites`` / ``mutation_targets`` / library role
        transition or orphan counter).

    Gate conditions (per WO-PHASE2-00 §10.1) — ALL must hold:
      - ``context.nav_atlas is not None`` (substrate ready)
      - ``context.stride_probe_complete`` (probe committed)
      - ``library.header.world_type == "NAV"`` (NAV-only gating)
      - ``context.last_action_id in {1, 2, 3, 4}`` (cardinal action)
      - ``context.prev_ego_pos is not None`` (movement context)
      - ``context.ego_current_pos is not None``
      - ``library.header.ego_body_cells`` non-empty (footprint known)
      - ``prev_grid is not None`` and ``current_grid is not None``

    Per WO-PHASE2-03 wiring sequence:
      1. extend_hud_mask_rows                  (Decision 2; per-frame)
      2. _derive_common_classes_from_v4_substrate (Decision 1; per-frame)
      3. tile_cache lift                       (Decision 4)
      4. detect_contact_reactivity (primary)
      5. if not is_reactive: detect_rare_class_contact (backup; Decision 3)
         — on backup fire, recompute full_delta_mask (Decision 5)
      6. existing writeback flow (NavLeverCandidate + nav_atlas + library)
    """
    # ── Gate ────────────────────────────────────────────────────────────
    nav_atlas = context.nav_atlas
    if (
        nav_atlas is None
        or not context.stride_probe_complete
        or library is None
        or library.header.world_type != "NAV"
        or context.last_action_id not in (1, 2, 3, 4)
        or context.prev_ego_pos is None
        or context.ego_current_pos is None
        or prev_grid is None
        or current_grid is None
    ):
        return None

    ego_body_cells = library.header.ego_body_cells
    if not ego_body_cells:
        return None

    # ── Derive V4-side parameters from ego_body_cells (§3.7 Option A) ──
    expected_replacement_size = 2 * len(ego_body_cells)
    footprint_height, footprint_width = _ego_body_bounding_box(ego_body_cells)

    prev_arr = np.asarray(prev_grid, dtype=np.int32)
    curr_arr = np.asarray(current_grid, dtype=np.int32)

    # ── HUD mask extension (Decision 2; V3.5 nav_executor.py:276) ──────
    # Row-extends the raw HUD mask to suppress full-row HUD noise from
    # contact detection. Per-frame computation (single np.copy).
    hud_mask = extend_hud_mask_rows(context.hud_mask)

    # ── Common-class derivation (Decision 1; V3.5 nav_executor.py:277) ──
    # Identifies dominant background classes that should not dominate
    # rare-class kernel attribution. Per-frame computation reflects
    # nav_atlas.blocked_classes growth during exploration.
    common_classes = _derive_common_classes_from_v4_substrate(context, nav_atlas)

    ego_value_set = library.header.ego_value_set
    # ego_value_set is a tuple in V4 library header; convert to frozenset
    ego_vs = (
        frozenset(int(v) for v in ego_value_set)
        if ego_value_set
        else frozenset()
    )

    # ── Tile cache LIFT to before primary (Decision 4) ─────────────────
    # Per V3.5 caller pattern at execution/contact_step_handler.py:553-602.
    # Tile boundaries: footprint-sized region anchored at the ego's
    # top-left bounding-box corner at the DESTINATION (post-action) cell,
    # sliced from the PRE-action frame so the cache shows what was at
    # the destination before the ego covered it. Lifted before primary
    # detection so backup detection has access.
    #
    # WO-CAMPAIGN3-PHASE2-05 (re-scoped, May 3, 2026): anchor at top-left
    # bounding-box corner per V3.5 find_ego_anchor_position. The prior
    # centroid-based anchor (context.ego_current_pos) is offset from
    # top-left by approximately (footprint_height // 2, footprint_width // 2)
    # for multi-cell egos, missing kernel cells in the slice. V3.5
    # deprecated centroid-based localization in WO-FORGE-NAV-05b. V4 design
    # philosophy explicitly endorses anchor-based localization
    # (DESIGN_PHILOSOPHY.md:183: "Centroid is a trap — use top-left
    # bounding box anchor").
    #
    # Two-frame split: anchor source is curr_arr (V4-natural — the ego's
    # post-action top-left IS the destination, observed directly rather
    # than computed from ego_pos + action_dirs as V3.5 does pre-env.step).
    # Slice source is prev_arr (V3.5 invariant — read pre-occlusion kernel
    # cells from before the ego footprint covered them).
    anchor_class = select_anchor_class(curr_arr, ego_vs)
    if anchor_class is None:
        return None  # ego cluster classification unavailable; suppress
    anchor_pos = find_ego_anchor_position(curr_arr, anchor_class)
    if anchor_pos is None:
        return None  # ego cluster not found in post-action frame; suppress
    new_r, new_c = anchor_pos
    # V3.5 two-stage destination clamp (nav_executor.py:433-434, 437-440)
    h, w = prev_arr.shape[:2]
    new_r = max(0, min(h - 1, new_r))   # destination clamp stage 1
    new_c = max(0, min(w - 1, new_c))
    r0 = max(0, new_r)                    # slice clamp stage 2
    r1 = min(h, new_r + footprint_height)
    c0 = max(0, new_c)
    c1 = min(w, new_c + footprint_width)
    tile_cache = prev_arr[r0:r1, c0:c1].copy()

    # ── Primary detection (V3.5 invariant) ─────────────────────────────
    is_reactive, excess, full_delta_mask = detect_contact_reactivity(
        prev_grid=prev_arr,
        new_grid=curr_arr,
        expected_replacement_size=expected_replacement_size,
        hud_mask=hud_mask,
        margin=5,
    )

    # ── Backup detection fall-through (Decision 3; V3.5 verbatim) ──────
    # Per V3.5 contact_step_handler.py:571-578: only when primary returns
    # False AND tile_cache is non-empty. On backup fire, full_delta_mask
    # must be recomputed from scratch since primary returned None for it
    # (Decision 5; V3.5 invariant at contact_step_handler.py:585-587).
    if not is_reactive and tile_cache.size > 0:
        has_rare, rare_classes, rare_count = detect_rare_class_contact(
            tile_cache, ego_vs, common_classes,
        )
        if has_rare:
            is_reactive = True
            excess = rare_count
            # Recompute full_delta_mask (V3.5 invariant for backup path).
            full_delta_mask = (curr_arr != prev_arr)
            if hud_mask is not None:
                full_delta_mask = full_delta_mask & ~hud_mask.astype(bool)
            logger.info(
                "[NAV-RARE-CONTACT] Rare classes %s at %s count=%d action=%d",
                sorted(rare_classes),
                (new_r, new_c),
                rare_count,
                int(context.last_action_id),
            )

    if not is_reactive:
        return None

    # ── Reconstruct lever kernel from cached tile ──────────────────────
    k_row, k_col, k_int = reconstruct_lever_kernel(tile_cache, ego_vs)
    lever_coord = (r0 + k_row, c0 + k_col)

    # ── Compute observed_effect_region (non-ego changed pixels) ────────
    # V3.5 pattern: build ego_replacement_mask, subtract from full_delta.
    ego_mask = build_ego_replacement_mask(
        prev_pos=context.prev_ego_pos,
        new_pos=context.ego_current_pos,
        footprint_height=footprint_height,
        footprint_width=footprint_width,
        grid_shape=prev_arr.shape,
    )
    if full_delta_mask is None:
        # Defensive: detect_contact_reactivity returned True but no mask.
        # Shouldn't happen per V3.5 contract; treat as no observable effect.
        effect_pixels: frozenset = frozenset()
    else:
        effect_mask = full_delta_mask & ~ego_mask
        effect_pixels = frozenset(
            (int(r), int(c))
            for r, c in zip(*np.where(effect_mask))
        )
    effect_count = len(effect_pixels)

    # ── Construct NavLeverCandidate ────────────────────────────────────
    candidate = NavLeverCandidate(
        coordinate=lever_coord,
        activation_mode="NAV_CONTACT",
        pre_activation_tile=tile_cache,
        kernel_integer=k_int,
        kernel_offset=(k_row, k_col),
        observed_effect_region=effect_pixels,
        effect_pixel_count=effect_count,
        activation_action=int(context.last_action_id),
        confidence=_INITIAL_CONFIDENCE,
    )

    # ── NavAtlas writeback ─────────────────────────────────────────────
    nav_atlas.nav_lever_candidates.append(candidate)
    # ego destination is the contact point (per V3.5 contacted_sites
    # semantic — coordinate where contact reactivity fired)
    nav_atlas.contacted_sites.add(context.ego_current_pos)
    # The kernel coordinate is the door-chase priority target
    nav_atlas.mutation_targets.add(lever_coord)

    # ── Library role transition (or orphan tally) ──────────────────────
    containing_id = _find_containing_object_id(library, lever_coord)
    if containing_id is not None:
        _promote_contact_lever(library, containing_id)
    else:
        nav_atlas.lever_orphan_count += 1

    return candidate


def _promote_contact_lever(library: "SemanticLibrary", containing_id: int) -> None:
    """WO_CAPTAIN_READS_TAPE D2 — the PAIRED contact-lever promotion.

    Closes the census's live one-sided writer (the former direct
    `obj.role = LEVER` at this site, categorical with no axis). Now: the
    categorical goes through the transition-checked mutator (`update_object_role`
    — so a terminal EGO/COUNTER is no longer force-overwritten), and the LEVER
    Store-A axis is accumulated at the SAME site, mirroring
    probe_outcome_processor:145/213's confidence discipline (axis 0.7 — the
    established contact-strength value; no invented numeric). Categorical
    confidence is left untouched (None), preserving prior behavior on that axis.

    If the transition is illegal (terminal role) the object is left unchanged and
    NO axis evidence is fed — pairing is all-or-nothing, never half a write.
    """
    obj = library.objects.get(containing_id)
    if obj is None:
        return
    try:
        library.update_object_role(containing_id, LibraryRole.LEVER, None)
    except (ValueError, KeyError):
        return  # terminal/illegal transition — do not force, do not feed the axis
    accumulate_role_evidence(obj, LibraryRole.LEVER, 0.7)


__all__ = [
    "_derive_common_classes_from_v4_substrate",
    "maybe_record_contact_reactivity",
]

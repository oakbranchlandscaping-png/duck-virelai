"""virelai_v4/library/delta_updater.py — Per-frame delta-driven library updates.

Relocated from library/library_sync.py (WO-MINE-CLEAN-05-PHASE-2).
This module contains the delta-path library updater — the functions that
run once per frame on the post-spawn frames to propagate observed cell
changes (FrameDelta) into the SemanticLibrary.

Single Responsibility: read FrameDelta + WorldDelta, write per-object
behavioral evidence (change counts, action attribution, active/static
observations). Does not classify objects, does not handle probe outcomes,
does not derive HUD masks.

Import sovereignty: contracts/, library/, perception/, stdlib/numpy only.
No imports from targeting/, strategy/, memory/.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Dict, Optional, Set, Tuple

import numpy as np

from virelai_v4.contracts.world_delta import WorldDelta
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import SemanticLibrary
# WO-E09-v2 D1: reuse the detector's own coverage bound + march window — no new
# constant. (role_classifier imports only library_roles, so no import cycle.)
from virelai_v4.library.role_classifier import (
    _COUNTER_MAX_COVERAGE,
    _COUNTER_MARCH_WINDOW,
)
from virelai_v4.library.counter_march import emit_counter_candidate_diag  # WO-E12 D1
from virelai_v4.perception.animation import transient_only_cells  # WO_AR D1 (pure)
from virelai_v4.cybernetic.frame_delta import FrameDelta
from virelai_v4.cybernetic.state_tracker import StateTracker

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mode B — Delta update
# ---------------------------------------------------------------------------

def _build_cell_to_region(library: SemanticLibrary) -> Dict[Tuple[int, int], int]:
    """Build a reverse lookup: cell coordinate → region_id."""
    mapping: Dict[Tuple[int, int], int] = {}
    for rid, obj in library.objects.items():
        for cell in obj.cells:
            mapping[cell] = rid
    return mapping


def _is_counter_candidate_domain(obj, grid_area: int) -> bool:
    """WO-E09-v2 D1: the set of objects for which the live cell-count (and its
    history) is maintained each sync — coverage-bounded, non-EGO. Reuses the
    detector's own `_COUNTER_MAX_COVERAGE` bound (no new threshold). COUNTER
    objects satisfy this (they were classified under the same coverage gate),
    so their `current_cell_count` computation is byte-identical to pre-WO-E09."""
    return (
        obj.role != LibraryRole.EGO
        and obj.cell_count < _COUNTER_MAX_COVERAGE * grid_area
    )


def _push_cell_count_history(obj) -> None:
    """WO-E09-v2 D1: append the current live count to the object's bounded march
    history (ring of depth _COUNTER_MARCH_WINDOW + 1 — enough to form the
    window deltas the recognizer requires). Single responsibility: history
    maintenance only; the count itself is written by the caller."""
    maxlen = _COUNTER_MARCH_WINDOW + 1
    obj.cell_count_history = (
        obj.cell_count_history + (obj.current_cell_count,)
    )[-maxlen:]


def _update_from_delta(
    library: SemanticLibrary,
    frame_delta: FrameDelta,
    last_action_id: Optional[int],
    state_tracker: Optional[StateTracker],
    is_death_frame: bool = False,
    grid: Optional[np.ndarray] = None,
    hud_mask: Optional[np.ndarray] = None,
    ego_mask: Optional[np.ndarray] = None,
    canonical_world_delta: Optional[WorldDelta] = None,
    interior_layers: Optional[list] = None,
) -> bool:
    """Mode B: update library from a FrameDelta on every subsequent frame.

    is_death_frame: when True, skip all statistical updates (FLAG-017).
    Death-frame deltas contain spurious LC drain and reset animation changes
    that would contaminate action_independence_ratio and change_count.

    grid: when provided, updates current_cell_count for COUNTER objects (WO-C5-02).
    Pixel count from live grid reflects LC drain as the game progresses.

    hud_mask: when provided (WO-C5-03), world delta = raw delta minus HUD cells.
    change_count and actions_with_change use world delta. actions_observed uses
    the raw (universal) count — the denominator is never masked.

    canonical_world_delta: when provided (WO-02-ARCH), read world_cells from the
    canonical WorldDelta stored on context instead of recomputing. This is the
    single source of truth for world cells. hud_mask and ego_mask params are
    preserved for lc_only_delta detection and future use.

    Returns:
        lc_only_delta (bool): True if the raw delta was non-empty but the world
        delta was empty (every changed cell was inside the HUD mask). Callers
        use this to increment ctx.lc_only_delta_count.
    """
    # FLAG-017: Guard against death-frame delta contamination (WO-C5-01).
    # A GAME_OVER frame's grid shows LC fully drained and reset animations —
    # changes that are artefacts of the terminal state, not of agent actions.
    if is_death_frame:
        logger.debug("[SYNC] Skipping death-frame delta (GAME_OVER)")
        return False

    # WO-02-ARCH: Read world_cells from canonical WorldDelta (single source of truth).
    # Falls back to empty tuple if canonical delta not provided (should not happen in normal flow).
    if canonical_world_delta is not None:
        world_cells = canonical_world_delta.world_cells
    else:
        world_cells = ()

    # Track which regions had at least one world-changed cell — used by both
    # reacts_to attribution and the Action Independence Metric below.
    affected_regions: Set[int] = set()

    # Update change counts from world delta (HUD-filtered when mask is established)
    if world_cells:
        cell_to_region = _build_cell_to_region(library)

        for cell in world_cells:
            rid = cell_to_region.get(cell)
            if rid is not None:
                obj = library.objects.get(rid)
                if obj is not None:
                    obj.change_count += 1
                    affected_regions.add(rid)
                    # WO-C5-05: Defeasibility — unexpected world change clears BACKGROUND tag.
                    # If the agent tagged this object as ignorable and it changes anyway,
                    # the evidence was wrong. Re-open it for investigation.
                    if obj.is_background:
                        obj.is_background = False
                        obj.ignore_score = 0.0
                        obj.ignore_channels = ""
                        logger.info(
                            "[SYNC] BACKGROUND tag removed from region %d — "
                            "unexpected world change",
                            obj.region_id,
                        )

        # Record which action caused the change (reacts_to)
        if last_action_id is not None:
            for rid in affected_regions:
                obj = library.objects.get(rid)
                if obj is not None:
                    if last_action_id not in obj.reacts_to:
                        obj.reacts_to = tuple(
                            sorted(set(obj.reacts_to) | {last_action_id})
                        )

    # WO-C5-03: Detect LC-only delta.
    # Raw delta was non-empty but world delta is empty → every change was a HUD tick.
    # WO-02-ARCH: Use canonical WorldDelta's raw_count when available (more accurate).
    # raw_cells comes from the actual grid diff. If prev_grid was None (canonical delta
    # returned empty), fall back to frame_delta.total_changed for the raw count.
    if canonical_world_delta is not None:
        _raw_changed = canonical_world_delta.raw_count
    else:
        _raw_changed = frame_delta.total_changed
    lc_only_delta = (
        _raw_changed > 0
        and len(world_cells) == 0
        and hud_mask is not None
    )
    if lc_only_delta:
        logger.debug(
            "[SYNC] LC-only delta on action %s — no world change",
            last_action_id,
        )

    # Action Independence Metric (WO-C5-01) — increment per-object counters.
    # actions_observed is UNIVERSAL — it counts every non-death action regardless of mask.
    # actions_with_change uses world evidence (affected_regions from world delta).
    # These counters persist across lives (Groundhog Day) and are used by
    # the LC classifier in WO-C5-02.
    for rid, obj in library.objects.items():
        obj.actions_observed += 1
        if rid in affected_regions:
            obj.actions_with_change += 1

    # WO-RM-02: Active/static observation — factual record, before classifier runs.
    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        # Document the actual variable name passed to the reactive classifier here
        _rc_stream_name = "world_cells"   # ACTUAL variable name: world_cells (from canonical_world_delta.world_cells — WO-02-ARCH)
        _rc_len = len(world_cells) if hasattr(world_cells, '__len__') else -1
        print(f"[WO02-DIAG2] REACTIVE-CLASSIFIER-INPUT frame_action={library.header.actions_taken} stream={_rc_stream_name} len={_rc_len}", file=sys.stderr, flush=True)
    _update_active_static(library, world_cells, library.header.actions_taken)
    # WO_AR D2: animation witness — record transient-only (flash) participation
    # beside the settled active/static column. Extract-then-call, NEVER interleaved
    # into _update_active_static; is_active stays settled-change-only and no
    # *_log_score is touched. A flash is not a settled reactive witness.
    _update_animation_witness(library, interior_layers)
    # WO-C5-02 + WO-E09-v2 D1: Update current_cell_count from the live grid.
    # Counts how many of the object's spawn-frame cells still carry its class_id —
    # a pixel-level budget reading: a draining LC loses pixels each step.
    # WO-E09-v2 D1 (corrects the v1 frozen-input drift): the domain is widened
    # from COUNTER-only to coverage-bounded, non-EGO *candidates*, so the march
    # recognizer has a live input BEFORE classification. COUNTER objects fall
    # inside this domain, so their current_cell_count is byte-identical to before.
    if grid is not None:
        grid_area = int(grid.shape[0] * grid.shape[1])
        _board_changed = bool(world_cells)
        for rid, obj in library.objects.items():
            if _is_counter_candidate_domain(obj, grid_area):
                obj.current_cell_count = int(
                    sum(1 for r, c in obj.cells if grid[r, c] == obj.class_id)
                )
                # WO-E12 D2: board-change gate. Append to the march history ONLY
                # on syncs where THIS object's cells changed (rid in the world-
                # delta's affected_regions) — so non-board-changing syncs no
                # longer inject a zero-delta into the ring. The recorded series
                # becomes the pristine monotone march (E10), independent of where
                # non-moving turns fall. current_cell_count still recomputes every
                # sync above (the gate touches only the history append).
                changed_this_sync = rid in affected_regions
                if changed_this_sync:
                    _push_cell_count_history(obj)
                # WO-E12 D1: per-sync diagnostic emit (pure read; gated on
                # VIRELAI_DIAG_DUMP). Resolves T2 (history populates + marches?)
                # and makes the firing window visible (the 5-run watch).
                emit_counter_candidate_diag(
                    obj, rid, changed_this_sync, _board_changed,
                    library.header.actions_taken, _COUNTER_MARCH_WINDOW,
                )

    # Update SDK action status
    if last_action_id is not None and last_action_id in library.sdk_actions:
        sdk = library.sdk_actions[last_action_id]
        sdk.test_count += 1
        if frame_delta.total_changed > 0:
            sdk.status = "LIVE"
            sdk.delta_cells = max(sdk.delta_cells, frame_delta.total_changed)
        elif sdk.test_count >= 2 and sdk.status != "LIVE":
            sdk.status = "NOOP"
        # WO-LGTD-02 Phase 4 (4.3.2): write Entry A operational belief
        # alongside the legacy status update. Four-state v1.0 collapse per
        # Section 5.5; cosmetic-vs-causal deferred to v1.1 amendment.
        library.update_operational_belief_after_outcome(
            action_id=last_action_id,
            status=sdk.status,
            delta_cells=frame_delta.total_changed,
        )

    # Sync exploration from StateTracker
    if state_tracker is not None:
        exp = library.exploration
        exp.unique_states = state_tracker.novel_count
        exp.repeated_states = state_tracker.repeated_count
        total = exp.unique_states + exp.repeated_states
        exp.efficiency = exp.unique_states / total if total > 0 else 1.0
        exp.consecutive_repeated = state_tracker.consecutive_repeated
        exp.actions_monitored = state_tracker.total_observations

    # Increment actions taken
    library.header.actions_taken += 1

    return lc_only_delta


def _update_active_static(  # WO-RM-02: active/static observation column
    library: "SemanticLibrary",
    world_delta_cells: Tuple[Tuple[int, int], ...],
    step_number: int,
) -> None:
    """Factual record of world-delta involvement per object. is_active is monotonically true."""
    if not world_delta_cells:
        return
    cell_to_region = _build_cell_to_region(library)
    touched_rids: Set[int] = set()
    for cell in world_delta_cells:
        rid = cell_to_region.get(cell)
        if rid is not None:
            touched_rids.add(rid)
    for rid in touched_rids:
        obj = library.objects.get(rid)
        if obj is None:
            continue
        obj.is_active = True
        obj.active_frame_count += 1
        if obj.first_active_frame == -1:
            obj.first_active_frame = step_number
            # DD gap-3a: the first observed self-delta is the reactive witness —
            # it falsifies the static conjecture (NESTED_TAXONOMY_SPEC §3). Retire
            # the static pole to -inf here. The positive reactive seal (+inf) is
            # gap-3b, deferred behind the gap-2 overload split (writing reactive
            # here would poison implied_role). static is not overloaded → the
            # retire is side-effect-free on the role read. Local import keeps this
            # WO's diff to a single hunk, clear of the counter-slice edits above.
            from virelai_v4.library.log_score_accumulator import (
                _retire_static_on_reactive_witness,
            )
            _retire_static_on_reactive_witness(obj)
        obj.last_active_frame = step_number


def _update_animation_witness(  # WO_AR D2: transient (flash) participation column
    library: "SemanticLibrary",
    interior_layers: Optional[list],
) -> None:
    """Record transient-only animation participation into the dormant witness
    fields (`flash_count` / `transition_count`), beside — never inside — the
    settled active/static column.

    A separate witness by CE ruling: a flash is transient (interior planes change,
    settled cells revert), so it must NOT flip the Band-1 tag, write `is_active`,
    influence locality, or touch any `*_log_score`. This function writes only the
    two behavior counters, through the existing `update_object_behavior` setter,
    and reads `is_active`/log-scores nowhere.

    Per turn: for each region that owned any transient-only cell, `flash_count`
    increments by one (a flash event) and `transition_count` accumulates the
    turn's excursion-step tally. Cause-child provenance (first/last transient
    frame) has no non-conflating home in the current schema — no new field this
    rung; the counts stand and the gap rides the next chartered subtree.
    """
    if not interior_layers or len(interior_layers) <= 1:
        return
    transient, desc = transient_only_cells(interior_layers)
    if not transient:
        return
    cell_to_region = _build_cell_to_region(library)
    touched: Set[int] = set()
    for cell in transient:
        rid = cell_to_region.get(cell)
        if rid is not None:
            touched.add(rid)
    steps = int(desc.get("steps", 0)) or 1
    for rid in touched:
        obj = library.objects.get(rid)
        if obj is None:
            continue
        library.update_object_behavior(
            rid,
            flash_count=obj.flash_count + 1,
            transition_count=obj.transition_count + steps,
        )

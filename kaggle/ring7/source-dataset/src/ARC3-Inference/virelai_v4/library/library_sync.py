"""
virelai_v4/library/library_sync.py — Library Sync Pipeline (Step 3).

The bridge between perception and belief. Runs on every NOT_FINISHED frame
inside choose_action, after Step 2 (Perceive) and before Step 4 (Target).

Three modes:
    Mode A — Spawn: GridScan → LibraryObjects (first frame, empty library)
    Mode B — Delta: FrameDelta → change_count, reacts_to, exploration
    Mode C — Groundhog Day: library pre-populated from previous life, skip spawn

Import sovereignty: imports from contracts/, perception/, and library/ only.
No imports from targeting/, strategy/, or memory/.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Dict, FrozenSet, List, Mapping, Optional, Tuple, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

from virelai_v4.library.attribution import update_attribution
from virelai_v4.library.classification_pass import (
    _classify_objects,
    _partition_ego_from_active,
)
# WO-E14 D3: confirm_counter_on_death re-wired to virelai.py's GAME_OVER branch
# (is_death_frame true there); the dead NOT_FINISHED-gated callsite here was removed.
from virelai_v4.library.counter_stats import (
    RATE_CONFIRM_CONFIDENCE,
    _update_counter_stats,
)
from virelai_v4.library.delta_updater import _update_from_delta
from virelai_v4.library.ego_detector import (
    detect_ego,
    ratchet_ego_detection,
    sync_ego_object_ids,
)
from virelai_v4.library.ignore_score import (
    accumulate_background_class_votes,
    compute_ignore_scores,
)
from virelai_v4.library.lever_evidence import record_lever_evidence
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.physics_accumulator import run_physics_measurement
from virelai_v4.diagnostics.frame_dump import maybe_emit_frame_event
from virelai_v4.library.probe_outcome_processor import (
    _process_previous_probe_outcome,
    _flag_state_changed_inerts,  # WO-OCD-05 Site 2
)
from virelai_v4.library.semantic_library import (
    LibraryObject,
    SDKAction,
    SemanticLibrary,
)
from virelai_v4.library.spawn_populator import _populate_from_scan
from virelai_v4.library.present_populator import populate_present_objects
from virelai_v4.library.world_delta_computer import (
    compute_world_delta,
    synthesize_world_delta_from_delta,
)
from virelai_v4.library.world_type_classifier import classify_world_type
from virelai_v4.contracts.world_delta import WorldDelta, CellCoord, ClassTransition
from virelai_v4.cybernetic.cell_history import CellHistory
from virelai_v4.perception.contact_detector import detect_contact
from virelai_v4.cybernetic.frame_delta import FrameDelta
from virelai_v4.perception.grid_scan import GridScan, Region, scan_grid
from virelai_v4.cybernetic.state_tracker import StateTracker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Calibration constants
# ---------------------------------------------------------------------------

# Ego confirmation threshold migrated to virelai_v4/library/ego_detector.py
# in WO-CLEAN-12-PHASE-3 (co-located with the ratchet consumer).


# ---------------------------------------------------------------------------
# HUD mask builder (WO-C5-03)
# ---------------------------------------------------------------------------

def _build_hud_mask(
    library: SemanticLibrary,
    grid_shape: Tuple[int, int],
) -> Optional[np.ndarray]:
    """Build a boolean HUD mask from all confirmed COUNTER objects.

    Returns a numpy bool array of shape grid_shape where True marks every cell
    that belongs to a COUNTER-role object (the life counter / HUD region).
    Returns None if no COUNTER objects are present in the library.

    The mask is permanent — it is built once when COUNTER is first detected and
    must not be recomputed in subsequent frames (Groundhog Day persistence relies
    on this: once built, the mask is stored on VirelaiContext and lives across lives).
    """
    counters = [o for o in library.objects.values() if o.role == LibraryRole.COUNTER]
    if not counters:
        return None
    rows, cols = grid_shape
    mask = np.zeros(grid_shape, dtype=bool)
    for obj in counters:
        for r, c in obj.cells:
            if 0 <= r < rows and 0 <= c < cols:
                mask[r, c] = True
    return mask


# ---------------------------------------------------------------------------
# WO-BLUEPRINT-04 — Class-change revocation hook (Blueprint Section 1.7)
# ---------------------------------------------------------------------------

def _observe_class_signature(obj, grid: np.ndarray) -> Optional[int]:
    """Compute the currently-observed class signature for a Slot.

    Per Blueprint Section 2.4.3 (single-color regime): the class signature
    is the pixel class value at the Slot's cells. For a stable Slot, all
    cells share the same value; we read the first cell as canonical
    representative.

    Returns None if the Slot has no cells (degenerate; should not occur
    in production but handled defensively).

    Per WO-BLUEPRINT-04 §1 Step 5: simple representative implementation
    for Phase B.1 scaffold. Section 4+ multi-color object support may
    evolve this to a structured signature.
    """
    if not obj.cells:
        return None
    # Take the first cell deterministically. obj.cells is a frozenset so
    # iteration order isn't guaranteed cross-Python-version; sort for
    # determinism. Cost is small (typical Slot has <100 cells).
    first_cell = min(obj.cells)
    r, c = first_cell
    rows, cols = grid.shape
    if not (0 <= r < rows and 0 <= c < cols):
        return None
    return int(grid[r, c])


def revoke_on_class_change(library: SemanticLibrary, grid: np.ndarray) -> int:
    """Class-change revocation hook per Blueprint Section 1.7.

    For each LibraryObject in the library, compare the currently-observed
    class signature against `obj.previous_class_signature`. When the
    signature has changed (or is being observed for the first time after
    a Mode A spawn that didn't initialize it), the Slot's BBA Layer One
    evidence is no longer applicable — revoke all six log-scores to 0.0
    (sigmoid-read 0.5, "no evidence"). Update the tracking field.

    The hook is idempotent on stable frames (matching signatures → no
    revocation, no field writes beyond the first-observation init).

    Per Blueprint Section 1.7:
        Class-change is observation-grounded and per-Slot; it does not
        require a global "did the world change materially" determination.

    Per Blueprint Section 2.6 (BBA Layer One semantics):
        Revoking log-scores to 0.0 represents "no evidence either way"
        in sigmoid-read terms. Hard falsification (Section 2.6.3) uses
        -inf as a separate sentinel; this hook does NOT hard-falsify —
        it returns the Slot to neutral so subsequent BBA updates start
        from a clean prior.

    Args:
        library: the SemanticLibrary being synced (mutated in place).
        grid: the current frame's grid as np.ndarray int32.

    Returns:
        Count of revoked Slots (for diagnostic surfacing). 0 on stable
        frames; >0 when class signatures changed.

    Filed under WO-BLUEPRINT-04 (Sub-Phase 2, Blueprint Absorption).
    INVENT anchor: #4 — Class-change revocation + Segment/Slot factoring.
    """
    revoked = 0
    for obj in library.objects.values():
        observed = _observe_class_signature(obj, grid)
        if observed is None:
            # Degenerate Slot or out-of-bounds; skip.
            continue
        if obj.previous_class_signature is None:
            # First observation — initialize tracking; no revocation.
            obj.previous_class_signature = observed
            continue
        if observed != obj.previous_class_signature:
            # Class signature changed — revoke the unsealed BBA log-scores to 0.0.
            # WO_SWEEP_EGO_LOCK (revoke-respects-the-lock, ported from the lever
            # leg below): a ratchet-confirmed (header.ego_confirmed), partition-
            # bound (role EGO) ego has EARNED its ego-axis evidence; class-change
            # must not erase it. The ego is the one object guaranteed to re-class
            # every frame it moves (_observe_class_signature reads the pixel at
            # its fixed anchor, which the body leaves behind), so unguarded
            # revocation over-fires on it specifically — zeroing the axis each
            # frame while the D1a partition skip-guard blocks re-earning, which
            # collapses the captain-store read to no-evidence (the Store-B EGO /
            # Store-A neutral split). The lock is DERIVED, not stored: it yields
            # automatically to falsification (a future unbind clears role or
            # ego_confirmed), never to re-classing. Sole zeroer of ego_log_score
            # (level_advance.py:114 carries it), so this is the only guard site.
            ego_locked = (obj.role == LibraryRole.EGO
                          and library.header.ego_confirmed)
            # WO_COUNTER_LOCK (revoke-respects-the-lock, same Delphi PORT as the
            # ego leg): the counter is the ego's twin — a depleting life-counter
            # re-classes every life (its anchor cell value falls as cells drain),
            # so unguarded revocation over-fires on it too, wiping the earned
            # counter axis while the Store-B-only rate ratchet
            # (counter_stats.py:91) re-confirms confidence but feeds no axis — the
            # exact one-sided-categorical the derived tier reads then refuse.
            # Confirmation predicate = role COUNTER ∧ confidence at/above the
            # ratchet's own bar (RATE_CONFIRM_CONFIDENCE). DERIVED, not stored: it
            # auto-yields to falsification (a role transition or confidence
            # dropping below the bar re-enables the wipe). Sole zeroer of
            # counter_log_score (level_advance.py:114 carries it).
            counter_locked = (obj.role == LibraryRole.COUNTER
                              and obj.confidence >= RATE_CONFIRM_CONFIDENCE)
            obj.static_log_score = 0.0
            obj.reactive_log_score = 0.0
            if not ego_locked:
                obj.ego_log_score = 0.0
            if not counter_locked:
                obj.counter_log_score = 0.0
            # SC2b Leg 1 (revoke-respects-the-lock): a confirmed lever's EARNED
            # lock evidence is not erased by a class-change. lever_locked is set
            # only by the probe-confirmation path (probe_outcome_processor.py:153),
            # which co-accumulates the lock evidence in the same branch (:190), so
            # lever_locked=True ⟹ the lever axis carries earned evidence. Preserving
            # it here keeps the LOCKED→TYPED two-threshold band intact across a
            # revoke (the +inf seal-at-lock alternative would collapse the band to
            # TYPED). Every other axis still revokes — class-change hygiene intact.
            if not obj.lever_locked:
                obj.lever_log_score = 0.0
            # DD gap-5: gate axis retired — no gate_log_score to revoke.
            obj.previous_class_signature = observed
            revoked += 1
    return revoked


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sync_library(
    library: SemanticLibrary,
    grid: np.ndarray,
    frame_delta: Optional[FrameDelta],
    state_tracker: Optional[StateTracker],
    last_action_id: Optional[int],
    available_actions: List[int],
    game_id: str,
    context: Optional[VirelaiContext] = None,
    cell_history: Optional[Dict[Tuple[int, int], CellHistory]] = None,
    spawn_grid: Optional[list] = None,
    prev_grid: Optional[np.ndarray] = None,
    is_death_frame: bool = False,
    hud_mask: Optional[np.ndarray] = None,
    spawn_class_frequencies: Optional[Dict[int, int]] = None,
    background_class_votes: Optional[Dict[int, int]] = None,
    interior_layers: Optional[list] = None,   # WO_AR D2: animation witness input (pure read)
    cell_transitions: Optional[Mapping[CellCoord, ClassTransition]] = None,  # WO-W1b-01: one birthplace
    raw_cells: Optional[FrozenSet[CellCoord]] = None,  # WO-W1b-02: birth the changed-set
    step: Optional[int] = None,        # WO-W1b-03: record identity, threaded like raw_cells
    action_id: Optional[int] = None,   # WO-W1b-03: record identity, threaded like raw_cells
) -> Tuple[Optional[GridScan], Optional[np.ndarray], bool, Optional[Dict[int, int]]]:
    """Feed perception evidence into the library. Mutates library in place.

    Returns (grid_scan, new_hud_mask, lc_only_delta, new_spawn_class_frequencies):
        grid_scan:                GridScan if Mode A was run (spawn), else None.
        new_hud_mask:             Newly built HUD mask if COUNTER was first detected this frame,
                                  else None. Caller should store on ctx.hud_mask.
                                  None if hud_mask was already set (never recomputed).
        lc_only_delta:            True if raw delta was non-empty but world delta was empty.
                                  Caller should increment ctx.lc_only_delta_count.
        new_spawn_class_frequencies: Dict computed from spawn frame in Mode A, else None.
                                  Caller should store on ctx.spawn_class_frequencies.

    hud_mask: current mask from ctx (None until COUNTER is first detected).
    spawn_class_frequencies: per-class pixel counts from spawn (None until Mode A returns it).
    background_class_votes: mutable dict accumulated from NAV ego departures (Channel 4).
    cell_transitions: WO-W1b-01 — the frame's one cell-transitions catalog,
        built ONCE by the caller (virelai.py's choose_action) and threaded
        down to compute_world_delta. None for every caller outside this
        WO's scope fence — compute_world_delta then builds its own,
        exactly as it always has.
    raw_cells: WO-W1b-02 — the frame's one changed-cell set, built ONCE by
        the caller (virelai.py's choose_action, beside cell_transitions)
        and threaded down to compute_world_delta. None for every caller
        outside this WO's scope fence — compute_world_delta then computes
        Step 2 itself, exactly as it always has.
    step, action_id: WO-W1b-03 — RULING_OBSERVERS_INTEGRATOR_v1 Clause A.
        The same frame-identity facts the observer (compute_frame_delta)
        carries, threaded to compute_world_delta via the same path as
        raw_cells, populating WorldDelta.step/.action_id. None for every
        caller outside this WO's scope fence.

    Modes:
        A (spawn):  len(library.objects) == 0 → run GridScan, populate objects
        C (GHD):    library already populated from previous life → skip spawn
        B (delta):  everything else → update from FrameDelta
    """
    grid_scan = None
    lc_only = False

    # Mode A — Spawn population (empty library, first frame)
    if len(library.objects) == 0:
        grid_scan = scan_grid(grid)
        _populate_from_scan(library, grid_scan, available_actions, game_id)
        # Compute spawn-frame class frequencies for Channel 3 of ignore scoring.
        # The spawn frame IS the current grid in Mode A.
        spawn_freqs: Dict[int, int] = {}
        for val in grid.flat:
            spawn_freqs[int(val)] = spawn_freqs.get(int(val), 0) + 1
        return grid_scan, None, False, spawn_freqs

    # Mode C — Groundhog Day (library already populated, no delta yet)
    # Nothing special needed — just ensure SDK actions are initialized
    for action_id in available_actions:
        if action_id not in library.sdk_actions:
            library.sdk_actions[action_id] = SDKAction(action_id=action_id)

    # WO-LGTD-02 Phase 4 (4.3.1): substrate write of Entry A declarative
    # belief per Library Blueprint Section 5.3. Refreshes every frame —
    # the platform's per-frame declaration is authoritative. The method
    # handles SDKAction creation for newly-declared ids (idempotent with
    # the loop above) and ABSENT marking for previously-declared ids
    # that no longer appear.
    library.refresh_affordance_declarative_belief(available_actions)

    # Mode B — Delta update (every subsequent frame)
    if frame_delta is not None:
        # WO-02-ARCH: Canonical WorldDelta computation — Frame Sovereignty Step 3.
        # Computed ONCE here at the top of Mode B. All downstream systems read
        # context.world_delta instead of calling _compute_world_delta separately.
        # Variable names: prev_grid=prev_grid, curr_grid=grid, ego_mask=context.ego_mask,
        # hud_mask=hud_mask, frame_action=library.header.actions_taken.
        _ego_mask_for_delta = context.ego_mask if context is not None else None
        if os.environ.get("VIRELAI_WO02_DIAG") == "1":
            _pgrid = prev_grid
            _cgrid = grid
            _emask = _ego_mask_for_delta
            _hmask = hud_mask
            _same_obj = (_pgrid is _cgrid)
            _same_content = False
            try:
                _same_content = _pgrid == _cgrid
            except Exception:
                _same_content = "compare_failed"
            _pgrid_hash = hash(tuple(tuple(row) for row in _pgrid)) if _pgrid is not None else None
            _cgrid_hash = hash(tuple(tuple(row) for row in _cgrid)) if _cgrid is not None else None
            _emask_len = len(_emask) if _emask is not None else -1
            _hmask_len = len(_hmask) if _hmask is not None else -1
            print(f"[WO02-ARCH-DIAG] CANONICAL-INPUTS action={library.header.actions_taken} same_obj={_same_obj} same_content={_same_content} pgrid_hash={_pgrid_hash} cgrid_hash={_cgrid_hash} ego_mask_len={_emask_len} hud_mask_len={_hmask_len}", file=sys.stderr, flush=True)
        _canonical_world_delta: WorldDelta = compute_world_delta(
            prev_grid=prev_grid,
            curr_grid=grid,
            ego_mask=_ego_mask_for_delta,
            hud_mask=hud_mask,
            frame_action=library.header.actions_taken,
            cell_transitions=cell_transitions,  # WO-W1b-01: one birthplace
            raw_cells=raw_cells,                # WO-W1b-02: birth the changed-set
            step=step,                          # WO-W1b-03: record identity
            action_id=action_id,                # WO-W1b-03: record identity
        )
        # WO-W1b-03 HALT (item 4, this WO's own review): the WO's own text
        # names this condition ("frame_delta.total_changed") as a migration
        # site to the canonical raw count. Verified and NOT migrated — see
        # this WO's return, HALT section. `raw_cells` is unconditionally
        # empty whenever `prev_grid is None` (birth site's `_changed_cells`
        # guards on exactly that), so substituting `len(raw_cells) > 0` here
        # would make this branch permanently unreachable (its own guarding
        # first conjunct, `prev_grid is None`, and the substituted third
        # conjunct can never both hold) — a real behavior regression, not a
        # safe mechanical substitution. Left reading `frame_delta.total_changed`
        # unchanged, pending Alpha Coder's ruling.
        if prev_grid is None and frame_delta is not None and frame_delta.total_changed > 0:
            _canonical_world_delta = synthesize_world_delta_from_delta(
                frame_delta,
                _ego_mask_for_delta,
                hud_mask,
                library.header.actions_taken,
            )
        if context is not None:
            context.world_delta = _canonical_world_delta
        if os.environ.get("VIRELAI_WO02_DIAG") == "1":
            _wd = _canonical_world_delta
            print(f"[WO02-ARCH-DIAG] CANONICAL-OUTPUT action={library.header.actions_taken} raw={len(_wd.raw_cells)} ego={len(_wd.ego_cells)} hud={len(_wd.hud_cells)} world={len(_wd.world_cells)}", file=sys.stderr, flush=True)
        if os.environ.get("VIRELAI_WO02_DIAG") == "1":
            # WO-W1-D3 — do FrameDelta and WorldDelta agree on which cells
            # changed? frame_delta.changed_cells (tuple) vs
            # _canonical_world_delta.raw_cells (frozenset) are the
            # apples-to-apples pair (both pre-ego/HUD-subtraction; raw_cells
            # is NOT world_cells). path separates the canonical
            # compute_world_delta route from the synthesize_world_delta_
            # from_delta fallback, since agreement on the synth path is
            # trivially true (WorldDelta is built FROM frame_delta there)
            # and proves nothing. Diagnostic only — no production value is
            # read, changed, or consumed here.
            try:
                _d3_path = (
                    "SYNTH"
                    if (prev_grid is None and frame_delta is not None and frame_delta.total_changed > 0)
                    else "CANONICAL"
                )
                _d3_fd_tuple = frame_delta.changed_cells
                _d3_wd_set = _canonical_world_delta.raw_cells
                _d3_fd_set = set(_d3_fd_tuple)
                _d3_agree = "Y" if _d3_fd_set == set(_d3_wd_set) else "N"
                _d3_only_fd = len(_d3_fd_set - set(_d3_wd_set))
                _d3_only_wd = len(set(_d3_wd_set) - _d3_fd_set)
                print(
                    f"[W1-D3] action={library.header.actions_taken} path={_d3_path} "
                    f"fd={len(_d3_fd_tuple)} wd={len(_d3_wd_set)} agree={_d3_agree} "
                    f"only_fd={_d3_only_fd} only_wd={_d3_only_wd}",
                    file=sys.stderr, flush=True,
                )
            except Exception as _d3_exc:
                print(
                    f"[W1-D3] action={library.header.actions_taken} agree=ERR exc={type(_d3_exc).__name__}",
                    file=sys.stderr, flush=True,
                )
        if os.environ.get("VIRELAI_WO02_DIAG") == "1":
            _wd_len = _canonical_world_delta.world_count
            _ed_len = len(_canonical_world_delta.ego_cells)
            print(f"[WO02-DIAG2] DELTA-COMPUTED frame_action={library.header.actions_taken} world_len={_wd_len} ego_len={_ed_len}", file=sys.stderr, flush=True)
        if os.environ.get("VIRELAI_WO02_DIAG") == "1":
            _raw_len = -1
            try:
                _raw_len = sum(
                    1 for y in range(len(grid))
                    for x in range(len(grid[0]))
                    if grid[y][x] != prev_grid[y][x]
                )
            except Exception as _e:
                _raw_len = -2
            print(f"[WO02-DIAG2] DELTA-RAW frame_action={library.header.actions_taken} raw_len={_raw_len}", file=sys.stderr, flush=True)

        # WO-LAYER1-01 v2 — add-only present-object population. Scan the CURRENT
        # frame and add a slot for every present visual object (class_id, cells)
        # fingerprint not already a slot. Runs BEFORE revoke/_update_from_delta so
        # added slots receive class-signature init and behavioural evidence this
        # same frame (they enter _build_cell_to_region below). ADD-ONLY: never
        # removes a slot (stale slots linger for the Layer-2 absorber). No match
        # rule, no correspondence, no weave — present == fingerprint in scan.
        # PREMISE CORRECTION (WO §0.2): Mode B computes no current-frame scan
        # (grid_scan is None outside Mode A), so this computes the one scan here;
        # the WO's "reuse the already-computed scan" premise did not hold.
        _present_scan = scan_grid(grid)
        _n_present_added = populate_present_objects(library, _present_scan)
        if _n_present_added:
            logger.info(
                "[LAYER1] added %d present visual object(s) to roster "
                "(now %d slots)", _n_present_added, len(library.objects)
            )

        # WO-BLUEPRINT-04: Class-change revocation hook (Blueprint Section 1.7).
        # Per-Slot comparison of currently-observed class signature against
        # `previous_class_signature`. On change: revoke all six BBA log-scores
        # to 0.0 (no evidence) for this Slot. Runs once per Mode B frame BEFORE
        # _update_from_delta so the role classifier sees a clean slate when
        # class signatures have changed. The hook is idempotent on stable
        # frames (no changes → no revocations).
        revoke_on_class_change(library, grid)

        lc_only = _update_from_delta(
            library, frame_delta, last_action_id, state_tracker,
            is_death_frame=is_death_frame, grid=grid, hud_mask=hud_mask,
            ego_mask=context.ego_mask if context is not None else None,
            canonical_world_delta=_canonical_world_delta,
            interior_layers=interior_layers,   # WO_AR D2: animation witness input
        )
        # WO-RM-03: Ego partition — classify EGO from displacement coherence.
        # Runs after _update_active_static (inside _update_from_delta above),
        # before general role classifier so EGO objects are skipped by _classify_objects.
        _partition_ego_from_active(
            library,
            library.header.ego_body_cells,
            set(library.header.ego_value_set),
        )
        # WO-02 LEVER-CATALOG: Tier 4 probe outcome processing.
        # Fires when the previous action was a Tier 4 probe (context.last_probe_target_region_id set).
        # Must run after delta update (so change_count reflects this frame) but before
        # role classification (so lever_locked guard is in effect when classifier runs).
        # Frame sovereignty call order: delta → process_probe → classify → update_attribution.
        if context is not None and context.last_probe_target_region_id is not None:
            _process_previous_probe_outcome(
                library, context, _canonical_world_delta
            )
            # WO-A.2b (Physics Reframe NR-01): per-lever operation measurement
            # + vector-consistency accumulation into causal_agreement.
            # Additive and write-only; runs before the clears (needs the rid).
            # Life-start fence: prev_grid is None. Level-advance fence:
            # structural — reset_for_new_level clears last_probe_target_*.
            run_physics_measurement(library, context, prev_grid, grid)
            # WO-PHASE1-DIAG-DUMP (NR-01 Phase 1): read-only per-frame physics
            # dump. No-op unless VIRELAI_DIAG_DUMP=1. Must precede the clears
            # below — it reads last_probe_target_cells / _region_id.
            maybe_emit_frame_event(context, library, prev_grid, grid)
            # Clear probe target fields after processing
            context.last_probe_target_region_id = None
            context.last_probe_target_cells = None
            context.last_probe_action_kind = None
        # Classification pass — after delta update (Mode A/C skipped). WO-RM-02 active/static runs inside _update_from_delta.
        _classify_objects(library, cell_history, library.header.actions_taken)
        # WO-E14 D3: the death-frame confirmer was DEAD here — sync_library is
        # gated to NOT_FINISHED (virelai.py), so is_death_frame is always False
        # at this callsite (context.py:195-197). It has been re-wired to the
        # GAME_OVER branch (virelai.py) where is_death_frame is true. Removed
        # from here so no structurally-dead invocation ships.
        # WO-02 LEVER-CATALOG: update_attribution after role classification (§4.4).
        # Fires every frame so the next frame's ranker sees fresh attribution state.
        update_attribution(library)
        # WO-OCD-05 Site 2 — Evidence Asymmetry reinvestigation trigger. Re-open
        # inert objects whose last probe was under a different grid-state hash
        # (self-clearing; computed fresh every Mode-B frame, before the ranker reads).
        _oc05_state_hash = ""
        if context is not None and context.state_tracker is not None:
            _oc05_state_hash = getattr(context.state_tracker, "_last_signature", "") or ""
        _flag_state_changed_inerts(library, _oc05_state_hash)
        # Counter stats update (WO-C5-02) — compute lc_rate and lc_budget_est for
        # COUNTER objects. Runs after _classify_objects so newly promoted objects
        # are covered in the same frame they are first classified.
        _update_counter_stats(library)
        # Background recognition (WO-C5-05) — compute ignore scores for all objects
        # using four evidence channels. Runs after classification so COUNTER/EGO
        # exemptions are current. Extracted to library/ignore_score.py (WO-C5-06).
        compute_ignore_scores(library, grid.shape, spawn_class_frequencies, background_class_votes)
        # Tier 3 NAV contact detection (WO-03) — detect ego-object contact on this frame.
        # Sets context.last_probe_target if contact is made, so the unified evidence wire below fires.
        # Must run before evidence wire to populate last_probe_target this frame (Mining Q50).
        # WO-PHASE4-02 (canonicalization): consumes the canonical WorldDelta
        # (ego- and HUD-masked at construction) instead of raw FrameDelta.
        if (context is not None
                and library is not None
                and library.header.world_type == "NAV"
                and library.header.ego_confirmed):
            detect_contact(context, library, _canonical_world_delta)
        # Tier 3 lever evidence recording (WO-02b, WO-03) — this is the NAV-lane
        # recorder. It fires only when last_probe_target is set, which only the
        # NAV contact path does (contact_detector). WO-D4 correction: this does
        # NOT write CLICK locality (the prior "fires for both CLICK and NAV"
        # comment was false — last_probe_target was never set on CLICK, so
        # lever_locality wrote zero times there). lever_locality is now
        # single-writer-per-world-type: CLICK → probe_outcome_processor (which
        # writes it from the outcome it already classifies), NAV → here. Each
        # writer asserts its lane at the point of write.
        # WO-PHASE4-02 (canonicalization): same WorldDelta source as detect_contact above.
        if context is not None and context.last_probe_target is not None:
            record_lever_evidence(context, library, _canonical_world_delta)
    else:
        # No delta but not spawn — first frame of a new life (GHD)
        # Still increment actions_taken for the RESET action
        if last_action_id is not None:
            library.header.actions_taken += 1

    # World type classification (WO-03) — runs on every non-spawn frame.
    # Confidence ratchet: only update if new confidence exceeds current.
    wt, ego, wt_conf = classify_world_type(library)
    if wt_conf > library.header.world_type_confidence:
        library.header.world_type = wt
        library.header.ego_mode = ego
        library.header.world_type_confidence = wt_conf

    # Ego detection (WO-04c/04d/04g) — displacement-based, runs on directional actions.
    # Confidence ratchet: only update if new confidence exceeds current.
    agent_values, disp_map, ego_conf, ego_centroid, ego_body_cells_new = detect_ego(
        library=library,
        prev_grid=prev_grid,
        current_grid=grid,
        last_action_id=last_action_id,
        spawn_grid=spawn_grid,
    )
    ratchet_ego_detection(
        library,
        agent_values,
        disp_map,
        ego_conf,
        ego_centroid,
        ego_body_cells_new,
    )
    # WO_SWEEP_EGO_BIND D1b: sole writer of header.ego_object_ids, at the
    # ratchet's confirm point — after the partition and classification pass
    # have finalised the EGO roster this frame. Closes the evidence→object-id
    # bridge so the WORLD AXIOMS row and the field-card ego gate read a live
    # value instead of the orphaned default ().
    sync_ego_object_ids(library)

    if (
        background_class_votes is not None
        and last_action_id in {1, 2, 3, 4}
        and prev_grid is not None
        and library.header.world_type == "NAV"
        and library.header.ego_confirmed
        and agent_values
    ):
        accumulate_background_class_votes(background_class_votes, prev_grid, grid, agent_values)

    # WO-C5-03: Build HUD mask if COUNTER was just detected for the first time.
    # Only builds when: (a) no mask yet (hud_mask is None), and (b) a COUNTER exists.
    # Once built, the mask is returned to the caller who stores it on ctx.hud_mask.
    # Permanent: the mask is never rebuilt once set (stored on ctx, persists across lives).
    new_hud_mask: Optional[np.ndarray] = None
    if hud_mask is None:
        candidate = _build_hud_mask(library, grid.shape)
        if candidate is not None:
            new_hud_mask = candidate
            logger.info(
                "[SYNC] HUD mask built: %d cells masked from %d COUNTER object(s)",
                int(candidate.sum()),
                sum(1 for o in library.objects.values() if o.role == LibraryRole.COUNTER),
            )

    return grid_scan, new_hud_mask, lc_only, None



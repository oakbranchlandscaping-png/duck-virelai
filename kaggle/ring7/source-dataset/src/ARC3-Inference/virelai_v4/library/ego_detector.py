"""
virelai_v4/library/ego_detector.py — Displacement-based ego detection for NAV worlds.

Identifies the ego via spatial displacement in frame diffs, not behavioral
CellHistory metadata (WO-04c replaces the CellHistory-based WO-04 approach).
WO-04d: adds centroid return, V3.5 Layer 2 overlap ratio, _get_object_centroid helper.

Algorithm:
  1. For each directional action, compute the frame diff (curr - prev).
  2. Find cells that disappeared (delta < 0) and appeared (delta > 0).
  3. Compute centroid of each set; displacement = centroid_appear - centroid_disappear.
  4. Validate that the displacement direction matches the expected action direction.
  5. Extract ego pixel classes as the intersection of departing and arriving values.
  6. V3.5 Layer 2: shift disappearing cells by displacement, measure overlap with
     appearing cells. High overlap (>= 0.80) → rigid-body confidence bonus (+0.15).
  7. Accumulate across frames; confidence grows with confirmed direction count.

Return value (detect_ego):
  (agent_value_set, displacement_map, confidence, ego_centroid) where:
    agent_value_set  — set of pixel class IDs composing the ego
    displacement_map — {action_id: (d_row, d_col)} for confirmed directions
    confidence       — 0.0–0.95 from confirmed directions + stride + overlap bonuses
    ego_centroid     — (row, col) centroid of disappearing cells, or None

  Returns (set(), {}, 0.0, None) when no new evidence is available.

Spatial filtering of library objects (deciding WHICH objects to mark EGO) is done
in library_sync.py via direct cell-overlap, not centroid-distance. This is multi-ego
safe: multiple simultaneous ego bodies controlled by the same direction actions are
supported because each body's spawn cells will overlap the disappearing set.

This module handles ego-related responsibilities in two stages (WO-CLEAN-12-PHASE-3):
  1. Pure detection: detect_ego() and supporting helpers compute ego state
     from frame state without side effects.
  2. Post-detection state ratchet: ratchet_ego_detection() applies confidence-
     gated state updates to library.header.* fields under write-once rules.

Callers: library_sync.sync_library calls detect_ego, then ratchet_ego_detection
on the result. Both are public API; detect_ego is pure read-only, while
ratchet_ego_detection mutates library.header in place.

Import sovereignty: library/ and stdlib + numpy only.
"""
from __future__ import annotations

from typing import Dict, FrozenSet, Optional, Set, Tuple

import numpy as np

from virelai_v4.scipy_check import ndimage_label
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

# Ego confirmation threshold — must be kept in sync with
# virelai_v4/targeting/assessor.py::TIER1_EGO_CONFIDENCE
# Migrated from library_sync.py in WO-CLEAN-12-PHASE-3.
EGO_CONFIRMATION_THRESHOLD: float = 0.65


# ---------------------------------------------------------------------------
# Calibration constants
# ---------------------------------------------------------------------------

_DIRECTIONAL_IDS: frozenset = frozenset({1, 2, 3, 4})

# Expected centroid displacement direction per action.
# Tuple: (expected_d_row, expected_d_col).  0 means "not checked on this axis".
_EXPECTED_DIRECTION: Dict[int, Tuple[int, int]] = {
    1: (-1, 0),   # ACTION1/UP:    row decreases
    2: (1,  0),   # ACTION2/DOWN:  row increases
    3: (0, -1),   # ACTION3/LEFT:  col decreases
    4: (0,  1),   # ACTION4/RIGHT: col increases
}

# Confidence ceiling — never fully certain from geometric evidence alone.
_MAX_CONFIDENCE: float = 0.95

# Stride consistency ratio — max/min displacement magnitude allowed for bonus.
_STRIDE_RATIO_CAP: float = 2.0

# Stride bonus added when all confirmed directions show consistent stride.
_STRIDE_BONUS: float = 0.20

# V3.5 Layer 2: rigid-body overlap threshold and confidence bonus.
_OVERLAP_THRESHOLD: float = 0.80
_OVERLAP_BONUS: float = 0.15


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_displacement(
    prev_grid: object,
    current_grid: object,
    last_action_id: int,
) -> Tuple[
    Optional[Tuple[float, float]],
    Optional[Set[int]],
    Optional[Tuple[float, float]],
]:
    """Compute centroid displacement, ego pixel classes, and disappearing centroid.

    Returns (displacement, agent_value_set, disapp_centroid) on success, or
    (None, None, None) when no valid ego displacement is detected (wall, wrong
    direction, no shared pixel class).
    """
    prev = np.asarray(prev_grid, dtype=np.int32)
    curr = np.asarray(current_grid, dtype=np.int32)
    delta = curr - prev

    disappearing = np.argwhere(delta < 0)   # cells that lost value
    appearing    = np.argwhere(delta > 0)   # cells that gained value

    if len(disappearing) == 0 or len(appearing) == 0:
        return None, None, None  # no movement (wall collision or no change)

    centroid_d = disappearing.mean(axis=0)
    centroid_a = appearing.mean(axis=0)
    d_row = float(centroid_a[0] - centroid_d[0])
    d_col = float(centroid_a[1] - centroid_d[1])

    # Validate directional sign consistency
    exp_row, exp_col = _EXPECTED_DIRECTION[last_action_id]
    if exp_row != 0 and np.sign(d_row) != np.sign(exp_row):
        return None, None, None  # centroid moved opposite to expected
    if exp_col != 0 and np.sign(d_col) != np.sign(exp_col):
        return None, None, None  # centroid moved opposite to expected

    # Ego pixel classes = intersection of departing and arriving values
    departing_vals = {int(v) for v in np.unique(prev[disappearing[:, 0], disappearing[:, 1]])}
    arriving_vals  = {int(v) for v in np.unique(curr[appearing[:, 0],    appearing[:, 1]])}
    agent_values = departing_vals & arriving_vals

    if not agent_values:
        return None, None, None  # no shared pixel class — not a rigid body move

    disapp_centroid = (float(centroid_d[0]), float(centroid_d[1]))
    return (d_row, d_col), agent_values, disapp_centroid


def _compute_overlap_ratio(
    prev_grid: object,
    current_grid: object,
    displacement: Tuple[float, float],
) -> float:
    """V3.5 Layer 2: validate rigid body translation via shifted-overlap.

    Shifts the disappearing cells by (d_row, d_col) and checks what fraction
    overlap with the appearing cells. Returns 0.0–1.0; >= _OVERLAP_THRESHOLD
    indicates a clean rigid body translation and qualifies for the bonus.
    """
    prev = np.asarray(prev_grid, dtype=np.int32)
    curr = np.asarray(current_grid, dtype=np.int32)
    delta = curr - prev
    d_row, d_col = displacement

    disapp = np.argwhere(delta < 0)
    appear = np.argwhere(delta > 0)

    if len(disapp) == 0 or len(appear) == 0:
        return 0.0

    # Shift disappearing cells by the displacement vector
    shifted = disapp.astype(float) + np.array([d_row, d_col])
    rows, cols = prev.shape
    valid_mask = (
        (shifted[:, 0] >= 0) & (shifted[:, 0] < rows) &
        (shifted[:, 1] >= 0) & (shifted[:, 1] < cols)
    )
    shifted_ints = np.round(shifted[valid_mask]).astype(int)

    appear_set  = set(map(tuple, appear.tolist()))
    shifted_set = set(map(tuple, shifted_ints.tolist()))
    overlap = len(appear_set & shifted_set)

    denominator = max(len(appear_set), len(shifted_set))
    return overlap / denominator if denominator > 0 else 0.0


def _get_object_centroid(obj: LibraryObject) -> Tuple[float, float]:
    """Compute the centroid (row, col) of an object's spawn cells.

    Returns (0.0, 0.0) for objects with no cells.
    Used for diagnostic display; not used for EGO filtering (library_sync
    uses direct cell-overlap instead, which is multi-ego safe).
    """
    if not obj.cells:
        return (0.0, 0.0)
    rows = [r for r, c in obj.cells]
    cols = [c for r, c in obj.cells]
    return (sum(rows) / len(rows), sum(cols) / len(cols))


def _compute_confidence(
    displacement_map: Dict[int, Tuple[float, float]],
    overlap_ratio: float = 0.0,
) -> float:
    """Confidence from confirmed direction count + stride consistency + overlap bonus.

    WO-04d: adds overlap_ratio parameter. Bonus of +_OVERLAP_BONUS if ratio
    >= _OVERLAP_THRESHOLD (rigid-body translation confirmed for this frame).
    """
    confirmed = len(displacement_map)
    if confirmed == 0:
        return 0.0

    conf = confirmed / 4.0

    magnitudes = [abs(dr) + abs(dc) for (dr, dc) in displacement_map.values()]
    if len(magnitudes) >= 2:
        min_mag = max(min(magnitudes), 0.1)   # guard against near-zero
        if max(magnitudes) / min_mag <= _STRIDE_RATIO_CAP:
            conf += _STRIDE_BONUS

    if overlap_ratio >= _OVERLAP_THRESHOLD:
        conf += _OVERLAP_BONUS

    return min(_MAX_CONFIDENCE, conf)


# ---------------------------------------------------------------------------
# Private helper — three-gate ego body selection (WO-RM-03-FIX-2)
# ---------------------------------------------------------------------------

def _compute_ego_body_cells(
    spawn_grid: object,
    agent_value_set: Set[int],
    ego_centroid: Tuple[float, float],
) -> FrozenSet[Tuple[int, int]]:
    """Identify spawn-frame ego cells using three gates.

      1. Class gate    — only cells whose pixel value is in agent_value_set
      2. Component gate — split same-class cells into connected components (scipy)
      3. Proximity gate — select the component whose centroid is nearest ego_centroid

    Returns a frozenset of (row, col) spawn-frame coordinates.
    On ls20: returns exactly 25 cells (R16 + R20), not 55.

    scipy is a hard dependency (see virelai_v4/scipy_check.py). ImportError at
    call time is not handled here — it is caught at module import time with
    a loud error message. FRICTION-RM-01.
    """
    spawn_np = np.asarray(spawn_grid, dtype=np.int32)
    ego_cells: Set[Tuple[int, int]] = set()
    ego_row, ego_col = ego_centroid

    for class_id in agent_value_set:
        mask = (spawn_np == class_id)
        if not mask.any():
            continue

        labeled, num_components = ndimage_label(mask)

        if num_components == 0:
            continue
        elif num_components == 1:
            rows, cols = np.where(labeled == 1)
            ego_cells |= set(zip(rows.tolist(), cols.tolist()))
        else:
            # Multiple components — select by proximity to ego_centroid
            best_distance = float("inf")
            best_cells: Set[Tuple[int, int]] = set()

            for comp_id in range(1, num_components + 1):
                rows, cols = np.where(labeled == comp_id)
                comp_cells = list(zip(rows.tolist(), cols.tolist()))
                comp_row = sum(r for r, c in comp_cells) / len(comp_cells)
                comp_col = sum(c for r, c in comp_cells) / len(comp_cells)
                distance = (
                    (comp_row - ego_row) ** 2 + (comp_col - ego_col) ** 2
                ) ** 0.5

                if distance < best_distance:
                    best_distance = distance
                    best_cells = set(comp_cells)

            ego_cells |= best_cells

    return frozenset(ego_cells)


# ---------------------------------------------------------------------------
# Public API — spawn-frame ego body derivation
# ---------------------------------------------------------------------------

def derive_coherent_movers(
    spawn_grid: object,
    agent_value_set: Set[int],
    ego_centroid: Optional[Tuple[float, float]] = None,
) -> FrozenSet[Tuple[int, int]]:
    """Derive spawn-frame cells of the ego body using connected component analysis.

    Ported from V3.5 with WO-04f enhancement: when ego_centroid is provided,
    selects the component nearest to it (displacement centroid = pre-action ego
    position). This correctly handles games where a same-class world object is
    larger than the ego body — proximity beats size.

    Tiebreak on equal L1 distance: prefer the smaller component. Ego bodies are
    compact; large equidistant regions are more likely world geometry.

    Falls back to largest-component selection when ego_centroid is None (no
    displacement evidence yet) or when there is only one component.

    Why spawn-frame: library object cells come from the spawn-frame GridScan.
    Intersecting spawn-vs-spawn is invariant to ego position at call time.

    scipy is a hard dependency (see virelai_v4/scipy_check.py). ImportError at
    call time is not handled here — it is caught at module import time with
    a loud error message. FRICTION-RM-01.
    """
    grid = np.asarray(spawn_grid, dtype=np.int32)
    ego_cells: Set[Tuple[int, int]] = set()

    for cls in agent_value_set:
        mask = (grid == cls).astype(np.int32)
        labeled, n_components = ndimage_label(mask)
        if n_components == 0:
            continue

        if n_components == 1:
            # Single component — selection is trivial
            selected_label = 1
        elif ego_centroid is not None:
            # WO-04f: proximity selection — component nearest displacement centroid
            best_label = 1
            best_dist  = float('inf')
            best_size  = float('inf')
            for label_id in range(1, n_components + 1):
                comp_cells   = np.argwhere(labeled == label_id)
                comp_centroid = comp_cells.mean(axis=0)
                dist = (abs(float(comp_centroid[0]) - float(ego_centroid[0]))
                        + abs(float(comp_centroid[1]) - float(ego_centroid[1])))
                size = len(comp_cells)
                # Primary: closer wins. Tiebreak: smaller wins (ego is compact).
                if dist < best_dist - 1e-6 or (
                    abs(dist - best_dist) < 1e-6 and size < best_size
                ):
                    best_dist  = dist
                    best_size  = size
                    best_label = label_id
            selected_label = best_label
        else:
            # Fallback: largest component when no centroid available
            sizes = np.bincount(labeled.ravel())
            sizes[0] = 0
            selected_label = int(np.argmax(sizes))

        coords = np.argwhere(labeled == selected_label)
        for r, c in coords:
            ego_cells.add((int(r), int(c)))

    return frozenset(ego_cells)


# ---------------------------------------------------------------------------
# Public API — displacement detection
# ---------------------------------------------------------------------------

def detect_ego(
    library: SemanticLibrary,
    prev_grid: object = None,
    current_grid: object = None,
    last_action_id: Optional[int] = None,
    spawn_grid: object = None,
) -> Tuple[Set[int], Dict[int, Tuple[float, float]], float, Optional[Tuple[float, float]], Optional[FrozenSet[Tuple[int, int]]]]:
    """Detect the ego via spatial displacement in a single frame transition.

    Accumulates evidence across calls by reading the existing displacement
    map and value set from library.header.  Returns the UPDATED accumulated
    state so the caller can apply a confidence ratchet.

    Returns (agent_value_set, displacement_map, confidence, ego_centroid, ego_body_cells).
    Returns (set(), {}, 0.0, None, None) when no new evidence is available this
    frame; the caller's ratchet then preserves the existing library state.

    ego_centroid is the (row, col) centroid of the disappearing cells from
    this frame — the pre-action ego position. None when detection fails.

    ego_body_cells (WO-04g / WO-RM-03-FIX): On the first confirmed displacement,
    ego_body_cells is derived from spawn_grid (if provided) — all cells whose pixel
    value is in agent_values. This guarantees spawn-frame coordinates that match
    library obj.cells from GridScan. Falls back to prev_grid when spawn_grid is None
    (backward compatible with callers that do not supply spawn_grid).
    If ego_body_cells is already in the library header, the stored value is returned
    unchanged (write-once semantics). None when detection fails this frame.

    Note on EGO filtering: which library objects to mark EGO is determined
    in library_sync.py using direct cell-overlap against the ego_body_cells.
    This is multi-ego safe — multiple simultaneous bodies controlled by the
    same direction actions all appear in the disappearing set.
    """
    # Gate: NAV world, directional action, previous frame available
    if library.header.world_type != "NAV":
        return (set(), {}, 0.0, None, None)
    if last_action_id not in _DIRECTIONAL_IDS:
        return (set(), {}, 0.0, None, None)
    if prev_grid is None or current_grid is None:
        return (set(), {}, 0.0, None, None)

    # Compute displacement for this single frame transition
    displacement, agent_values, disapp_centroid = _compute_displacement(
        prev_grid, current_grid, last_action_id
    )

    if displacement is None:
        return (set(), {}, 0.0, None, None)  # no valid displacement this frame

    # V3.5 Layer 2: overlap ratio for rigid-body confidence bonus
    overlap_ratio = _compute_overlap_ratio(prev_grid, current_grid, displacement)

    # WO-04g / WO-RM-03-FIX-2: Three-gate ego body capture — spawn-frame coordinates.
    # Write-once: if already captured in a prior frame, return stored value.
    existing_body = library.header.ego_body_cells
    if existing_body:
        ego_body_cells: Optional[FrozenSet[Tuple[int, int]]] = existing_body
    else:
        # First confirmed displacement — run three-gate selection.
        # Use spawn_grid if available (spawn-frame coordinates match obj.cells from
        # GridScan). Fall back to prev_grid when spawn_grid is not supplied so that
        # callers without spawn_grid (e.g. existing unit tests) still get a result.
        coord_grid = spawn_grid if spawn_grid is not None else prev_grid
        ego_body_cells = _compute_ego_body_cells(
            coord_grid, agent_values, disapp_centroid
        )

    # Accumulate with evidence already in the library header
    new_disp_map = dict(library.header.ego_displacement_map)
    new_disp_map[last_action_id] = displacement

    new_values = set(library.header.ego_value_set) | agent_values

    confidence = _compute_confidence(new_disp_map, overlap_ratio)
    return (new_values, new_disp_map, confidence, disapp_centroid, ego_body_cells)


# ----------------------------------------------------------------------
# Post-detection state ratchet (mutates library.header.* in place)
# ----------------------------------------------------------------------

def ratchet_ego_detection(
    library: SemanticLibrary,
    agent_values: Set[int],
    disp_map: Dict[int, Tuple[float, float]],
    ego_conf: float,
    ego_centroid: Optional[Tuple[float, float]],
    ego_body_cells_new: Optional[FrozenSet[Tuple[int, int]]],
) -> None:
    """Apply detect_ego results to library.header under confidence-gated ratchet rules.

    Performs post-detection state capture: when ego_conf exceeds the existing
    library.header.ego_confidence, this function updates library.header fields
    to reflect the new detection. ego_body_cells follows a write-once rule
    (set on first capture, never overwritten).

    MUTATION CONTRACT:
        Mutates library.header.* fields IN PLACE. Returns None.
        Mutated fields (when outer ratchet gate passes):
            - library.header.ego_confidence (always updated)
            - library.header.ego_value_set (always updated)
            - library.header.ego_displacement_map (always updated)
            - library.header.ego_centroid (updated when ego_centroid is not None)
            - library.header.ego_body_cells (write-once: only set on first capture)
            - library.header.ego_confirmed (set True when ego_conf >= EGO_CONFIRMATION_THRESHOLD)
        Outer gate: ego_conf > library.header.ego_confidence.
        Threshold: EGO_CONFIRMATION_THRESHOLD module constant.

        Inputs library, agent_values, disp_map, ego_conf, ego_centroid,
        ego_body_cells_new are read-only. None are mutated except library.header.

    Args:
        library: SemanticLibrary; mutated via library.header.* in place.
        agent_values: Set of class values currently held by ego (from detect_ego).
        disp_map: Displacement map (from detect_ego).
        ego_conf: Detection confidence (from detect_ego).
        ego_centroid: Optional centroid coordinates (from detect_ego).
        ego_body_cells_new: Optional frozenset of body cells (from detect_ego).

    Returns:
        None. library.header is mutated in place.

    Extracted from sync_library's body (L300-L315 sub-block of L291-L315 capture)
    in WO-CLEAN-12-PHASE-3 as part of the Hard cap decomposition campaign per
    Apex Q4 ruling (Stop B Green-tier-V3.5-match target). Per FRICTION-WO-15,
    Option B chosen because plumbing locals (agent_values etc.) are consumed
    downstream of the ratchet block by Phase 2's accumulate_background_class_votes.
    """
    if ego_conf > library.header.ego_confidence:
        library.header.ego_confidence = ego_conf
        library.header.ego_value_set = tuple(sorted(agent_values))
        library.header.ego_displacement_map = disp_map
        if ego_centroid is not None:
            library.header.ego_centroid = ego_centroid   # WO-04f: persist for pathfinding / field card
        # WO-04g: write-once direct capture. First confirmed displacement wins.
        if ego_body_cells_new is not None and not library.header.ego_body_cells:
            library.header.ego_body_cells = ego_body_cells_new
        if ego_conf >= EGO_CONFIRMATION_THRESHOLD:
            library.header.ego_confirmed = True
            # WO-RM-01: EGO ratchet promotion removed.
            # Object-level EGO role assignment is handled by ego partition
            # (classification_pass._partition_ego_from_active). ego_confirmed
            # flag, ego_value_set, ego_body_cells, and ego_centroid persist for
            # downstream consumers (field card, assessor, ego mask).
            pass


def sync_ego_object_ids(library: SemanticLibrary) -> None:
    """WO_SWEEP_EGO_BIND D1b: the SOLE writer of header.ego_object_ids.

    Recomputes header.ego_object_ids from the current EGO roster — the region
    ids of every object bound to LibraryRole.EGO by displacement coherence
    (classification_pass._partition_ego_from_active) or the general classifier.
    Pure derivation from obj.role; idempotent; reflects both additions and
    roster removals. Called from library_sync at the ratchet's confirm point,
    AFTER the partition and the classification pass, so the roster is final.

    Before this writer, header.ego_object_ids had no live source and defaulted
    () forever — orphaning every downstream reader (the WORLD AXIOMS row, the
    field-card ego region-detail gate). This closes the evidence→object-id
    bridge WO-RM-01 severed.
    """
    library.header.ego_object_ids = tuple(sorted(
        region_id for region_id, obj in library.objects.items()
        if obj.role == LibraryRole.EGO
    ))

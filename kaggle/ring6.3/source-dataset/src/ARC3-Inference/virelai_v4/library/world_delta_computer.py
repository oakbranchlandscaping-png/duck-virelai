"""
virelai_v4/library/world_delta_computer.py — Canonical WorldDelta computation.

WO-02-ARCH LEVER-CATALOG

Frame Sovereignty: the only function that reads raw grids and produces WorldDelta.
Called exactly once per frame at the top of sync_library.

Import sovereignty: imports from contracts/world_delta.py (plus stdlib/numpy),
and, as of WO-W1-01a, from library/cell_transition_view.py — the one sibling
module holding the two concrete lazy views this file constructs and injects
into WorldDelta's cell_transitions/world_transitions fields. Otherwise still
does NOT import from library/, strategy/, perception/, or targeting/.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, FrozenSet, Mapping, Optional, Set, TYPE_CHECKING, Tuple, Union

import numpy as np

from virelai_v4.contracts.world_delta import WorldDelta, CellCoord, ClassTransition
from virelai_v4.library.cell_transition_view import (
    RestrictedCellView,
    TotalCellTransitions,
)

if TYPE_CHECKING:
    from virelai_v4.cybernetic.frame_delta import FrameDelta


def compute_world_delta(
    prev_grid: Optional[np.ndarray],   # numpy array (H×W int) or None
    curr_grid: Optional[np.ndarray],   # numpy array (H×W int) or None
    ego_mask: Optional[np.ndarray],    # numpy bool array (H×W) or None
    hud_mask: Optional[np.ndarray],    # numpy bool array (H×W) or None
    frame_action: int,
    cell_transitions: Optional[Mapping[CellCoord, ClassTransition]] = None,
    raw_cells: Optional[FrozenSet[CellCoord]] = None,
    step: Optional[int] = None,
    action_id: Optional[int] = None,
) -> WorldDelta:
    """Compute the canonical WorldDelta for the current frame.

    Called exactly once per frame at the top of sync_library.
    Frame Sovereignty: the only function that reads raw grids and produces delta.

    Parameters
    ----------
    prev_grid : np.ndarray or None
        Previous frame's grid (H×W int numpy array). None on spawn.
    curr_grid : np.ndarray or None
        Current frame's grid (H×W int numpy array). None on spawn.
    ego_mask : np.ndarray or None
        Boolean H×W mask where True = ego cell. None if ego not yet detected.
    hud_mask : np.ndarray or None
        Boolean H×W mask where True = HUD/LC cell. None until COUNTER detected.
    frame_action : int
        Current actions_taken value for provenance.
    cell_transitions : Mapping[CellCoord, ClassTransition] or None
        WO-W1b-01 — one birthplace. The canonical per-frame catalog, built
        ONCE by the caller (virelai.py's choose_action, before either
        consumer) and threaded down here — never constructed here when
        supplied. Defaults to None for every caller outside this WO's scope
        fence (60+ existing call sites, this fence: virelai.py,
        library/library_sync.py, library/world_delta_computer.py, and new
        tests only) — omitting it preserves today's behavior exactly:
        this function builds its own, precisely as it always has.
    raw_cells : FrozenSet[CellCoord] or None
        WO-W1b-02 — birth the changed-set. The frame's one "which cells
        changed" record, built ONCE by the caller (virelai.py's
        choose_action, beside cell_transitions) and threaded down here —
        never recomputed here when supplied. Defaults to None for every
        caller outside this WO's scope fence — omitting it preserves
        today's behavior exactly: this function computes Step 2 itself,
        precisely as it always has. Does NOT affect
        `cybernetic/frame_delta.py`'s own independent diff — that
        redundancy is deliberate (the D-3 grading instrument), not
        collapsed by this parameter.
    step : int or None
        WO-W1b-03 — RULING_OBSERVERS_INTEGRATOR_v1 Clause A: the same
        step-counter fact the observer (compute_frame_delta) carries for
        this frame, threaded via the same path as raw_cells. Populates
        WorldDelta.step. Defaults to None for every caller outside this
        WO's scope fence; WorldDelta.step then keeps its own field default
        (-1) — no fallback recomputation is possible or needed (this is an
        opaque identity value, not a derived quantity).
    action_id : int or None
        Same note as `step`, for WorldDelta.action_id.

    Returns
    -------
    WorldDelta
        Frozen, canonical per-frame delta.
    """
    _step = step if step is not None else -1
    _action_id = action_id if action_id is not None else -1

    _empty = WorldDelta(
        raw_cells=frozenset(),
        ego_cells=frozenset(),
        hud_cells=frozenset(),
        world_cells=frozenset(),
        world_transitions={},
        cell_transitions={},   # WO-W1-01: no prior grid on this path — honest empty, not invented.
        frame_action=frame_action,
        prev_frame_hash=None,
        curr_frame_hash=None,
        step=_step,
        action_id=_action_id,
    )

    # Step 1: Handle None grids — return empty WorldDelta
    if prev_grid is None or curr_grid is None:
        return _empty

    # Step 9: Compute frame hashes (numpy arrays → tobytes)
    try:
        prev_frame_hash: Optional[int] = hash(prev_grid.tobytes())
        curr_frame_hash: Optional[int] = hash(curr_grid.tobytes())
    except Exception:
        prev_frame_hash = None
        curr_frame_hash = None

    # Step 2: Compute raw_cells — (r, c) where grids differ
    # WO-W1b-02: birth the changed-set. When the caller already built the
    # frame's one changed-set (the new calling convention), it is used
    # as-is — not recomputed a second time. When absent (every caller
    # outside this WO's fence), the fallback below is byte-for-byte the
    # prior unconditional computation — same two grids, same try/except,
    # same exception-path early return, nothing else changed.
    if raw_cells is None:
        try:
            changed_mask = (prev_grid != curr_grid)
            coords = np.argwhere(changed_mask)
            raw_cells = frozenset(
                (int(r), int(c)) for r, c in coords
            )
        except Exception:
            return WorldDelta(
                raw_cells=frozenset(),
                ego_cells=frozenset(),
                hud_cells=frozenset(),
                world_cells=frozenset(),
                world_transitions={},
                cell_transitions={},
                frame_action=frame_action,
                prev_frame_hash=prev_frame_hash,
                curr_frame_hash=curr_frame_hash,
                step=_step,
                action_id=_action_id,
            )

    if not raw_cells:
        return WorldDelta(
            raw_cells=frozenset(),
            ego_cells=frozenset(),
            hud_cells=frozenset(),
            world_cells=frozenset(),
            world_transitions={},
            cell_transitions={},
            frame_action=frame_action,
            prev_frame_hash=prev_frame_hash,
            curr_frame_hash=curr_frame_hash,
            step=_step,
            action_id=_action_id,
        )

    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        _sample_raw = list(raw_cells)[:5]
        _sample_ego = list(ego_mask)[:5] if ego_mask is not None else []
        _sample_hud = list(hud_mask)[:5] if hud_mask is not None else []
        print(f"[WO02-ARCH-DIAG] COMPUTER-INTERNALS frame_action={frame_action} raw_count={len(raw_cells)} raw_sample={_sample_raw} ego_mask_len={len(ego_mask) if ego_mask is not None else 0} ego_mask_sample={_sample_ego} hud_mask_len={len(hud_mask) if hud_mask is not None else 0} hud_mask_sample={_sample_hud}", file=sys.stderr, flush=True)

    # Step 3: Normalize ego_mask and hud_mask to frozensets
    ego_mask_set: FrozenSet[CellCoord] = frozenset()
    if ego_mask is not None:
        try:
            ego_coords = np.argwhere(ego_mask)
            ego_mask_set = frozenset((int(r), int(c)) for r, c in ego_coords)
        except Exception:
            ego_mask_set = frozenset()

    hud_mask_set: FrozenSet[CellCoord] = frozenset()
    if hud_mask is not None:
        try:
            hud_coords = np.argwhere(hud_mask)
            hud_mask_set = frozenset((int(r), int(c)) for r, c in hud_coords)
        except Exception:
            hud_mask_set = frozenset()

    # Step 5: Disjointness warning — check ego/hud overlap before computing ego_cells
    overlap = ego_mask_set & hud_mask_set
    if overlap:
        if os.environ.get("VIRELAI_WORLDDELTA_WARN") == "1":
            print(
                f"[WORLDDELTA-WARN] ego/hud overlap detected at frame {frame_action}: "
                f"{len(overlap)} cells",
                file=sys.stderr,
                flush=True,
            )

    # Step 4: Compute ego_cells = raw_cells ∩ ego_mask
    ego_cells: FrozenSet[CellCoord] = frozenset(raw_cells & ego_mask_set)

    # Step 6: Compute hud_cells = (raw_cells - ego_cells) ∩ hud_mask
    hud_cells: FrozenSet[CellCoord] = frozenset((raw_cells - ego_cells) & hud_mask_set)

    # Step 7: Compute world_cells = raw_cells - ego_cells - hud_cells
    world_cells: FrozenSet[CellCoord] = frozenset(raw_cells - ego_cells - hud_cells)

    # Step 8: WO-W1-01 — one canonical store, one derived narrowing.
    # `cell_transitions` is the total, convention-free catalog over the whole
    # frame-pair (every cell, HELD included — SPEC_DELTA_LEDGER §2);
    # `world_transitions` is no longer an independent per-cell loop — it is a
    # read-only restriction of that same store to `world_cells`, identical in
    # observable content to the loop it replaces (proven by the golden-fence
    # test: `diagnostics/dossier.py::_delta_attribution`, world_transitions'
    # one live reader, is unchanged either way).
    #
    # WO-W1b-01: this is no longer an unconditional construction. When the
    # caller already built the frame's one catalog (the new calling
    # convention), it is used as-is — not rebuilt a second time. When absent
    # (every caller outside this WO's fence), the fallback below is byte-for-
    # byte the prior unconditional line — same two grids, same class,
    # nothing else changed.
    if cell_transitions is None:
        cell_transitions = TotalCellTransitions(prev_grid, curr_grid)
    world_transitions = RestrictedCellView(cell_transitions, world_cells)

    # Step 8b: WO-W2-B-01 — the transition-keyed index (SPEC_DELTA_LEDGER §2's
    # ledger form: cells grouped by (from, to)), materialized canonical-side
    # (RULING_OBSERVERS_INTEGRATOR_v1 Clause A: the index lives on the record,
    # not the observer). One pass over `raw_cells` — already materialized at
    # Step 2, so this rides that traversal rather than opening a second
    # O(grid) walk — point-querying the already-constructed `cell_transitions`
    # (O(1) per lookup, no scanning; WO-W2-B-00 §0.3). `raw_cells`, not
    # `cell_transitions.items()`, bounds this to the changed population only:
    # no (a, a) HELD entry can ever appear, because every coordinate in
    # `raw_cells` is one where prev != curr by construction (Step 2). Values
    # are the member cells, not a count — a count is always derivable
    # (`len(cells)`) but identity is not recoverable from a count once
    # discarded, and no constraint yet forces that cut (the catalog is
    # per-frame, never accumulated — its own bound already applies; ruling,
    # RULING_OBSERVERS_INTEGRATOR_v1). The observer
    # (`cybernetic/frame_delta.py`'s `class_transitions`, a Counter over this
    # SAME changed population) is deliberately left untouched by this WO — it
    # keeps computing independently, and becomes this index's parallax
    # grading surface (Clause B): for every (from, to) key, the observer's own
    # triple count should equal `len(transition_index[(from, to)])`.
    _mutable_index: Dict[ClassTransition, Set[CellCoord]] = {}
    for coord in raw_cells:
        _mutable_index.setdefault(cell_transitions[coord], set()).add(coord)
    transition_index: Dict[ClassTransition, FrozenSet[CellCoord]] = {
        key: frozenset(cells) for key, cells in _mutable_index.items()
    }

    return WorldDelta(
        raw_cells=raw_cells,
        ego_cells=ego_cells,
        hud_cells=hud_cells,
        world_cells=world_cells,
        world_transitions=world_transitions,
        cell_transitions=cell_transitions,
        frame_action=frame_action,
        prev_frame_hash=prev_frame_hash,
        curr_frame_hash=curr_frame_hash,
        step=_step,
        action_id=_action_id,
        transition_index=transition_index,
    )


# ----------------------------------------------------------------------
# WorldDelta synthesis from FrameDelta (backward-compat fallback pathway)
# ----------------------------------------------------------------------

def synthesize_world_delta_from_delta(
    frame_delta: FrameDelta,
    ego_mask: Optional[np.ndarray],
    hud_mask: Optional[np.ndarray],
    frame_action: int,
) -> WorldDelta:
    """Synthesize a WorldDelta from FrameDelta state when canonical pipeline did not produce one.

    Used as the backward-compat fallback path inside sync_library when compute_world_delta
    returns None or an incomplete result. Performs mask normalization, set arithmetic, and
    WorldDelta construction matching the canonical pipeline's output shape.

    Args:
        frame_delta: FrameDelta from cybernetic loop's per-frame computation.
        ego_mask: numpy bool array marking ego cells.
        hud_mask: numpy bool array marking HUD cells.
        frame_action: int action ID for this frame.

    Returns:
        WorldDelta with cells, masks, and action populated; zero side effects on inputs.

    Extracted from sync_library's body (L189-L224) in WO-CLEAN-12-PHASE-1 as part of the
    Hard cap decomposition campaign per Apex Q4 ruling (Stop B Green-tier-V3.5-match target).

    Transform pipeline applied per FRICTION-WO-12 + FRICTION-WO-13: gate-strip + re-indent
    (strip-8 per post-gate-strip depth math) + rename
    (_ego_mask_for_delta -> ego_mask; library.header.actions_taken -> frame_action).
    """
    _raw_from_delta: frozenset = frozenset(frame_delta.changed_cells)
    _ego_set: frozenset = frozenset()
    if ego_mask is not None:
        try:
            import numpy as _np
            _ec = _np.argwhere(ego_mask)
            _ego_set = frozenset((int(r), int(c)) for r, c in _ec)
        except Exception:
            pass
    _hud_set: frozenset = frozenset()
    if hud_mask is not None:
        try:
            import numpy as _np
            _hc = _np.argwhere(hud_mask)
            _hud_set = frozenset((int(r), int(c)) for r, c in _hc)
        except Exception:
            pass
    _ego_cells_fb = frozenset(_raw_from_delta & _ego_set)
    _hud_cells_fb = frozenset((_raw_from_delta - _ego_cells_fb) & _hud_set)
    _world_cells_fb = frozenset(_raw_from_delta - _ego_cells_fb - _hud_cells_fb)
    # WO-W1-01 §0.4 verdict: (b) — no prior grid exists anywhere on this path.
    # This function receives only `frame_delta` (which never retains grids —
    # "grids are consumed at computation time, not stored", per
    # cybernetic/frame_delta.py) plus the two masks; neither this function's
    # signature nor its caller (library_sync.py's Mode B) threads a prior
    # grid or a retained frame record through to here. `cell_transitions`
    # therefore stays the honest empty Mapping, exactly like
    # `world_transitions` before it — not an invented catalog. (Whether a
    # cross-life grid, e.g. from `context.frame_record_log`, should ever be
    # threaded in as a new data source is a design question this WO does not
    # decide — see the return's §0.4 discussion.)
    # WO-W1b-03 (discretionary completeness, not a named §2.2 migration
    # site): frame_delta.step / .action_id are already in scope here — the
    # same identity facts WorldDelta.step/.action_id now carry on the
    # canonical path. Populating them costs nothing (data already held) and
    # avoids leaving this one construction site the sole -1-default outlier
    # once every other WorldDelta build site in this module carries real
    # values.
    _canonical_world_delta = WorldDelta(
        raw_cells=_raw_from_delta,
        ego_cells=_ego_cells_fb,
        hud_cells=_hud_cells_fb,
        world_cells=_world_cells_fb,
        world_transitions={},
        cell_transitions={},
        frame_action=frame_action,
        prev_frame_hash=None,
        curr_frame_hash=None,
        step=frame_delta.step,
        action_id=frame_delta.action_id,
    )
    return _canonical_world_delta

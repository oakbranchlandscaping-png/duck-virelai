"""
cybernetic/frame_delta.py — Universal frame delta analysis.

Campaign FRAME — the atomic observation record.

One FrameDelta per action, immutable, LC-separated, class-aware.
Pure computation — no state access, no side effects, no phase imports.

Architecture:
    FrameDelta is the deterministic difference between two consecutive Frames.
    The atomic evidence unit (Glossary v2.1).

    compute_frame_delta() is a pure function that produces a FrameDelta from
    pre/post grids, an action descriptor, and an optional HUD mask.

    compute_consecutive_pure_lc() counts trailing pure-LC deltas in a sequence
    (the "torque counter" — how many consecutive actions produced zero world change).

Dependencies: numpy, stdlib only. No imports from execution/, discovery/,
falsification/, or crucible/. Infrastructure code — consumed by all phases,
owned by none.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# FrameDelta — the atomic observation record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FrameDelta:
    """Deterministic difference between two consecutive frames.

    One record per env.step() or env.step_click() call.
    Immutable. All fields are hashable (tuples of primitives).
    No numpy arrays — grids are consumed at computation time, not stored.
    """

    # Identity
    step: int                                    # Global step counter (aligns with env.steps_taken)
    action_id: int                               # Action ID (1-7)
    action_coord: Optional[Tuple[int, int]]      # (row, col) for click actions, None for directional

    # Raw delta
    changed_cells: Tuple[Tuple[int, int], ...]   # (row, col) of ALL cells that changed value
    total_changed: int                           # len(changed_cells)

    # Class transitions
    class_transitions: Tuple[Tuple[int, int, int], ...]  # (from_class, to_class, count) triples

    # LC separation
    # WO-PHASE4-02 (OTA-05): the lc/world split below is conditional on
    # compute_frame_delta being called WITH a hud_mask. In V4's live
    # perception path (virelai.py:_perceive) hud_mask is not passed, so
    # lc_changed = 0, world_changed = total_changed, and
    # world_cells = changed_cells. The fields below are accurate when
    # the function is called with hud_mask (e.g., V3.5 callers, tests).
    # Post-WO-PHASE4-02: no live causal consumer reads world_cells —
    # detect_contact and record_lever_evidence now read the canonical
    # WorldDelta artifact (contracts/world_delta.py). Field retained for
    # use by compute_consecutive_pure_lc, CellHistory's batch builder,
    # and tests; candidate for deletion in a future cleanup WO.
    # Annotation merged from perception/frame_delta.py during WO-BLUEPRINT-02
    # (May 17, 2026) before that file was retired.
    lc_changed: int                              # Cells inside HUD/LC region (0 if hud_mask not passed)
    world_changed: int                           # total_changed - lc_changed (== total_changed if hud_mask not passed)
    world_cells: Tuple[Tuple[int, int], ...]     # Changed cells outside LC region (== changed_cells if hud_mask not passed)

    # Torque signal
    is_pure_lc: bool                             # True if world_changed == 0


# ---------------------------------------------------------------------------
# Sentinel — represents "no real action occurred"
# ---------------------------------------------------------------------------

EMPTY_DELTA = FrameDelta(
    step=-1,
    action_id=0,
    action_coord=None,
    changed_cells=(),
    total_changed=0,
    class_transitions=(),
    lc_changed=0,
    world_changed=0,
    world_cells=(),
    is_pure_lc=True,
)


# ---------------------------------------------------------------------------
# Pure computation function
# ---------------------------------------------------------------------------

def compute_frame_delta(
    pre_grid: np.ndarray,
    post_grid: np.ndarray,
    action_id: int,
    step: int,
    hud_mask: Optional[np.ndarray] = None,
    action_coord: Optional[Tuple[int, int]] = None,
) -> FrameDelta:
    """Compute FrameDelta from pre/post grids.

    Pure function. Deterministic. No side effects. No state access.

    Parameters
    ----------
    pre_grid : np.ndarray
        Grid state before the action (H×W int array).
    post_grid : np.ndarray
        Grid state after the action (H×W int array).
    action_id : int
        Action ID (1-7).
    step : int
        Global step counter (aligns with env.steps_taken).
    hud_mask : np.ndarray, optional
        Boolean H×W mask. True = HUD/LC pixel (excluded from world delta).
    action_coord : tuple of (int, int), optional
        (row, col) for click actions. None for directional actions.

    Returns
    -------
    FrameDelta
        Frozen, immutable observation record.
    """
    # 1. Boolean diff mask
    changed_mask = (pre_grid != post_grid)

    # 2. Changed cell coordinates
    coords = np.argwhere(changed_mask)
    changed_cells = tuple(tuple(int(v) for v in rc) for rc in coords)
    total_changed = int(changed_mask.sum())

    # 3. LC separation
    if hud_mask is not None:
        lc_changed = int((changed_mask & hud_mask).sum())
        world_mask = changed_mask & ~hud_mask
    else:
        lc_changed = 0
        world_mask = changed_mask
    world_changed = total_changed - lc_changed

    # 4. World cells (changed cells outside LC region)
    world_coords = np.argwhere(world_mask)
    world_cells = tuple(tuple(int(v) for v in rc) for rc in world_coords)

    # 5. Class transitions — (from_class, to_class, count) triples
    if total_changed > 0:
        rows, cols = coords[:, 0], coords[:, 1]
        pre_vals = pre_grid[rows, cols]
        post_vals = post_grid[rows, cols]
        transition_counter: Counter = Counter()
        for pv, qv in zip(pre_vals, post_vals):
            transition_counter[(int(pv), int(qv))] += 1
        class_transitions = tuple(
            (from_c, to_c, count)
            for (from_c, to_c), count in sorted(transition_counter.items())
        )
    else:
        class_transitions = ()

    # 6. Torque signal
    is_pure_lc = (world_changed == 0)

    return FrameDelta(
        step=step,
        action_id=action_id,
        action_coord=action_coord,
        changed_cells=changed_cells,
        total_changed=total_changed,
        class_transitions=class_transitions,
        lc_changed=lc_changed,
        world_changed=world_changed,
        world_cells=world_cells,
        is_pure_lc=is_pure_lc,
    )


# ---------------------------------------------------------------------------
# Torque counter utility
# ---------------------------------------------------------------------------

def compute_consecutive_pure_lc(deltas: Sequence[FrameDelta]) -> int:
    """Count consecutive is_pure_lc=True records from the END of the sequence.

    The "torque counter" — how many consecutive actions produced zero
    world change. When this number is high, the solver is spinning its
    wheels (only LC ticking, no structural effect on the world).

    Parameters
    ----------
    deltas : sequence of FrameDelta
        Ordered sequence of frame deltas (oldest first).

    Returns
    -------
    int
        Count of trailing consecutive pure-LC deltas.
    """
    count = 0
    for delta in reversed(deltas):
        if delta.is_pure_lc:
            count += 1
        else:
            break
    return count

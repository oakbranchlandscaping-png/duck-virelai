"""
cybernetic/cell_history.py — Per-cell behavioral memory.

Campaign FRAME — WO-FRAME-03.

CellHistory is the per-cell accumulator that transforms raw FrameDelta
records into structured per-cell knowledge.  Layer 2 of the three-dimensional
understanding: Space (GridScan), Identity (Delphi+Library), Time (FrameDelta+CellHistory).

Each CellHistory tracks:
    - How many times a cell changed (change_count)
    - Which steps it changed on (steps)
    - What class transitions it underwent (transitions)
    - Which actions caused it to change (actions)
    - Which other cells changed alongside it (co_change_counts)

Convenience queries:
    - is_toggle: does the cell alternate between exactly 2 classes?
    - cycle_length: if the cell cycles, how long is the cycle?
    - top_co_changers: which cells change most often with this one?

Dependencies: stdlib only (plus cybernetic.frame_delta types).
No imports from execution/, discovery/, falsification/, or crucible/.
Infrastructure code — consumed by all phases, owned by none.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from virelai_v4.cybernetic.frame_delta import FrameDelta

import numpy as np


# ---------------------------------------------------------------------------
# CellHistory — per-cell behavioral accumulator
# ---------------------------------------------------------------------------

@dataclass
class CellHistory:
    """Mutable per-cell record accumulating behavioral evidence over time.

    One instance per (row, col) that has ever changed.  Grows monotonically
    as FrameDeltas are processed.
    """

    row: int
    col: int

    # Aggregate counters
    change_count: int = 0

    # Temporal trace — which steps this cell changed on
    steps: List[int] = field(default_factory=list)

    # Class transitions — (from_class, to_class) pairs in order
    transitions: List[Tuple[int, int]] = field(default_factory=list)

    # Actions that caused change — action_id per delta
    actions: List[int] = field(default_factory=list)

    # Co-change map — how many times each other cell changed in the same delta
    co_change_counts: Dict[Tuple[int, int], int] = field(default_factory=dict)

    # WO-LIBRARY-CLEAN-01: steps flagged as transition events (world_changed > threshold)
    transition_steps: set = field(default_factory=set)


# ---------------------------------------------------------------------------
# Core update function
# ---------------------------------------------------------------------------

def update_cell_history(
    history: CellHistory,
    delta: FrameDelta,
    pre_grid: Optional[np.ndarray] = None,
    post_grid: Optional[np.ndarray] = None,
    view: Optional[Mapping[Tuple[int, int], Tuple[int, int]]] = None,
    step: Optional[int] = None,
    action_id: Optional[int] = None,
    raw_cells: Optional[FrozenSet[Tuple[int, int]]] = None,
) -> None:
    """Mutate a CellHistory in place from a single FrameDelta.

    The cell at (history.row, history.col) must be in delta.changed_cells
    (or, when raw_cells is supplied, in raw_cells — see below).
    Caller is responsible for only calling this for cells that actually changed.

    Parameters
    ----------
    history : CellHistory
        The per-cell record to update.
    delta : FrameDelta
        The observation record containing this cell's change. Still
        required (unchanged signature for every caller that predates
        WO-W1b-03) — but no longer the sole source of steps/actions/
        co-change when the three canonical-record parameters below are
        supplied.
    pre_grid : np.ndarray, optional
        Grid before the action.  Ignored when `view` is supplied. Kept for
        every caller that does not build a view (record_probe_observation,
        build_cell_history, existing tests) — their exact prior behavior is
        unchanged.
    post_grid : np.ndarray, optional
        Grid after the action.  Same note as `pre_grid`.
    view : Mapping[(row, col), (from_class, to_class)], optional
        WO-W1-02a — the single, canonical derivation of "what happened at
        this cell" (see `library/cell_transition_view.py`'s
        `TotalCellTransitions`), built ONCE by the caller and passed in —
        never constructed here. Duck-typed to `Mapping` rather than the
        concrete class: this module's own import sovereignty ("stdlib only,
        plus cybernetic.frame_delta types") stays intact, since nothing here
        imports `library/`. When supplied, this is the sole source for step
        4 below; `pre_grid`/`post_grid` are not read. When absent (every
        caller that predates this WO), step 4 falls back to the original
        raw-grid index, unchanged.
    step, action_id, raw_cells : optional
        WO-W1b-03 — RULING_OBSERVERS_INTEGRATOR_v1 Clause A: consumers-of-
        record read the canonical record; the observer (`delta`, a
        FrameDelta) is retained for grading only. When supplied, these
        three replace `delta.step` / `delta.action_id` / `delta.changed_cells`
        as the source for steps 2/3/5 below. Duck-typed to bare scalars and
        a FrozenSet — not a `contracts.world_delta.WorldDelta` object —
        because the production caller (`virelai.py`'s `_perceive`) has no
        WorldDelta instance available at this point in the frame (it is
        built later, inside `_sync_library`); these are the same birth-site
        values threaded there too. Defaults to None for every caller that
        predates this WO (record_probe_observation, build_cell_history,
        existing tests) — their exact prior behavior, reading `delta`
        directly, is unchanged.
    """
    r, c = history.row, history.col

    # 1. Increment change count
    history.change_count += 1

    # 2. Record step — WO-W1b-03: canonical record when supplied, else delta.
    history.steps.append(step if step is not None else delta.step)

    # 3. Record action — WO-W1b-03: canonical record when supplied, else delta.
    history.actions.append(action_id if action_id is not None else delta.action_id)

    # 4. Per-cell class transition — single derivation (WO-W1-02a) when a
    # view is supplied; the legacy raw-grid index otherwise (unchanged
    # behavior for every caller that does not build one).
    if view is not None:
        transition = view.get((r, c))
        if transition is not None:
            history.transitions.append(transition)
    elif pre_grid is not None and post_grid is not None:
        from_class = int(pre_grid[r, c])
        to_class = int(post_grid[r, c])
        history.transitions.append((from_class, to_class))

    # 5. Co-change — every OTHER changed cell in this delta. WO-W1b-03:
    # canonical raw_cells when supplied, else delta.changed_cells. Order is
    # immaterial here — co_change_counts is a Dict accumulated by addition,
    # read downstream only as a mapping (cell_evidence_builder.py's filtered
    # sum) or via max()/sorted() convenience queries with no live reader.
    _co_change_source = raw_cells if raw_cells is not None else delta.changed_cells
    for cell in _co_change_source:
        cell_tuple = (cell[0], cell[1])
        if cell_tuple != (r, c):
            history.co_change_counts[cell_tuple] = (
                history.co_change_counts.get(cell_tuple, 0) + 1
            )


# ---------------------------------------------------------------------------
# Convenience queries
# ---------------------------------------------------------------------------

def is_toggle(cell: CellHistory) -> bool:
    """Does this cell alternate between exactly 2 classes?

    A toggle cell has transitions that use exactly 2 distinct class values.
    Requires at least 2 transitions to determine.

    Returns False if no transitions recorded or if more/fewer than 2 classes.
    """
    if len(cell.transitions) < 2:
        return False
    classes = set()
    for from_c, to_c in cell.transitions:
        classes.add(from_c)
        classes.add(to_c)
    return len(classes) == 2


def cycle_length(cell: CellHistory) -> Optional[int]:
    """Detect repeating cycle in class transitions.

    Looks for the shortest prefix of the transition targets (to_class values)
    that repeats perfectly.  Returns None if no cycle detected or if fewer
    than 2 transitions exist.

    Returns
    -------
    int or None
        Length of the shortest repeating cycle, or None.
    """
    if len(cell.transitions) < 2:
        return None

    # Extract the sequence of destination classes
    seq = [to_c for _, to_c in cell.transitions]
    n = len(seq)

    # Try each candidate cycle length from 1 up to n//2
    for clen in range(1, n // 2 + 1):
        pattern = seq[:clen]
        match = True
        for i in range(clen, n):
            if seq[i] != pattern[i % clen]:
                match = False
                break
        if match:
            return clen

    return None


def top_co_changers(
    cell: CellHistory, n: int = 5,
) -> List[Tuple[Tuple[int, int], int]]:
    """Return the top-N cells that most frequently co-change with this cell.

    Parameters
    ----------
    cell : CellHistory
        The cell to query.
    n : int
        Number of top co-changers to return (default 5).

    Returns
    -------
    list of ((row, col), count) tuples, sorted descending by count.
    """
    items = sorted(
        cell.co_change_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    return items[:n]


# ---------------------------------------------------------------------------
# Standalone probe observation recorder — WO-LIBRARY-BRIDGE-01
# ---------------------------------------------------------------------------

_TRANSITION_THRESHOLD = 500  # §D: world_changed above this = transition event


def record_probe_observation(
    pre_grid: np.ndarray,
    post_grid: np.ndarray,
    step: int,
    action_id: int,
    action_coord: Tuple[int, int],
    hud_mask: Optional[np.ndarray],
    cell_history: Dict[Tuple[int, int], "CellHistory"],
    state_tracker: Optional[object] = None,
) -> bool:
    """Record a single probe's observation into CellHistory and StateTracker.

    Standalone: no AdapterEnvironment dependency.  Called by the click mapper
    after each probe to close the observation gap (WO-LIBRARY-BRIDGE-01).

    Parameters
    ----------
    pre_grid, post_grid : np.ndarray
        Grids before and after the probe action.
    step : int
        Global step counter for this probe.
    action_id : int
        Action ID (6 for click).
    action_coord : (row, col)
        Click coordinate.
    hud_mask : np.ndarray or None
        Boolean HUD mask for LC separation.
    cell_history : dict
        Mutable (row, col) → CellHistory map.  Updated in place.
    state_tracker : StateTracker or None
        If provided, records the post-grid state.

    Returns
    -------
    bool
        True if the post-grid is a novel state (or no tracker), False if repeated.
    """
    from virelai_v4.cybernetic.frame_delta import compute_frame_delta

    fd = compute_frame_delta(
        pre_grid=pre_grid,
        post_grid=post_grid,
        action_id=action_id,
        step=step,
        hud_mask=hud_mask,
        action_coord=action_coord,
    )

    # §D: flag transition events but still record them.
    is_transition = fd.world_changed >= _TRANSITION_THRESHOLD

    # Update CellHistory for each changed cell.
    for cell in fd.changed_cells:
        key = (cell[0], cell[1])
        if key not in cell_history:
            cell_history[key] = CellHistory(row=key[0], col=key[1])
        update_cell_history(cell_history[key], fd, pre_grid, post_grid)
        # WO-LIBRARY-CLEAN-01: tag transition steps for downstream filtering.
        if is_transition:
            cell_history[key].transition_steps.add(step)

    # Record state in StateTracker.
    # WO-PUSH-P1-R1 (OG-4 retention): pre_grid (from-state) and action_id are
    # already parameters in hand — feed them so this probe's transition is
    # retained instead of discarded. from_sig uses the tracker's own signature()
    # so it is key-consistent with `visited` (no second hashing path). The
    # `novel` return is unchanged.
    novel = True
    if state_tracker is not None and hasattr(state_tracker, "record"):
        _from_sig = (
            state_tracker.signature(pre_grid)
            if hasattr(state_tracker, "signature") else None
        )
        novel = state_tracker.record(
            post_grid, step, action_id=action_id, from_sig=_from_sig,
        )

    return novel


# ---------------------------------------------------------------------------
# Batch builder — process a sequence of FrameDeltas
# ---------------------------------------------------------------------------

def build_cell_history(
    deltas: Sequence[FrameDelta],
    pre_grids: Optional[Sequence[np.ndarray]] = None,
    post_grids: Optional[Sequence[np.ndarray]] = None,
) -> Dict[Tuple[int, int], CellHistory]:
    """Build complete CellHistory map from a sequence of FrameDeltas.

    Parameters
    ----------
    deltas : sequence of FrameDelta
        Ordered observation records.
    pre_grids : sequence of np.ndarray, optional
        Pre-action grids aligned 1:1 with deltas.  Enables per-cell transitions.
    post_grids : sequence of np.ndarray, optional
        Post-action grids aligned 1:1 with deltas.  Enables per-cell transitions.

    Returns
    -------
    dict mapping (row, col) -> CellHistory
        One entry per cell that changed in at least one delta.
    """
    histories: Dict[Tuple[int, int], CellHistory] = {}

    for i, delta in enumerate(deltas):
        pre = pre_grids[i] if pre_grids is not None else None
        post = post_grids[i] if post_grids is not None else None

        for cell in delta.changed_cells:
            key = (cell[0], cell[1])
            if key not in histories:
                histories[key] = CellHistory(row=key[0], col=key[1])
            update_cell_history(histories[key], delta, pre, post)

    return histories

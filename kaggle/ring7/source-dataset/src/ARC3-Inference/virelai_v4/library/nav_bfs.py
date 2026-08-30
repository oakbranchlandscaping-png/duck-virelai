"""
virelai_v4/library/nav_bfs.py — Stride-aware BFS pathfinding over NavAtlas substrate.

Ported from V3.5 standalone function at
``Universal_Solver_v3_5/memory/nav_atlas.py:324-415`` per
WO-CAMPAIGN3-PHASE1-02 (May 2, 2026, Phase 1 NAV SUBSTRATE).

V3.5 inheritance: this is the BFS pathfinding algorithm proven across
the V3.5 forge campaigns and the WO-LS20-RESTORE-06 amendment. The
function reads NavAtlas substrate (`walkable_classes`, `blocked_classes`,
`ego_value_set`, `action_dirs`) and the current grid; returns an
ordered list of action IDs to reach the target, or `None` if
unreachable.

V4 ARCHITECTURE COMPLIANCE MODIFICATIONS (per WO-CAMPAIGN3-PHASE1-02 §INHERITANCE):
    1. File location: ``virelai_v4/library/nav_bfs.py``. The file is
       separate from ``library/nav_atlas.py`` per V4 module-boundary
       preference (substrate class on one file; algorithm consuming the
       substrate on another).
    2. Function signature ports verbatim from V3.5. The WO §Step 1
       contemplated a V4 modification to make NavAtlas the first
       parameter. The Step 0 inventory recommended porting verbatim
       (Choice α) — see ``WO-CAMPAIGN3-PHASE1-02-STEP0-FINDINGS.md``
       §6.3 for the rationale: V3.5's field-input contract was
       deliberate (testability + decoupling); callers extract NavAtlas
       fields at the call site (one line at WO-05's NavPlan
       construction).
    3. Type annotations explicit (``np.ndarray`` in signature; ``Set``,
       ``FrozenSet``, ``Dict``, ``Tuple``, ``Optional``, ``List``).
    4. ``nav_bfs_visited`` (V3.5 sibling at lines 418-465) is **NOT**
       ported in this WO. Its passability oracle is `visited_cells`
       rather than class membership; it is a different algorithm. Out
       of WO-02 scope.

DUAL-MODE PASSABILITY (BLACKLIST MODE — WO-LS20-RESTORE-06):
    The function supports two passability modes via the optional
    ``blocked_classes`` parameter:

    - **Whitelist mode** (default, ``blocked_classes=None``): a cell is
      passable if its class is in ``passable_classes`` OR ``ego_value_set``.
      Used when the substrate is fully populated and conservative
      pathfinding is preferred.

    - **Blacklist mode** (``blocked_classes`` provided): a cell is
      passable UNLESS its class is in ``blocked_classes``. Unknown
      cells are treated as passable. This is the **preferred mode for
      early-game states** where ``walkable_classes`` is sparse — the
      Director Ruling 1 Option B mechanism for substrate-bootstrapping
      Life 1 BFS.

    Activation is caller-controlled via the optional parameter; the
    function is mode-agnostic — it just dispatches on whether the
    argument is provided. This is the V3.5 contract preserved.

Design contract (preserved verbatim from V3.5):
    - Pure function: no side effects on inputs
    - Reads grid for class lookups; reads passable/blocked/ego sets for
      passability classification
    - Returns ordered ``List[int]`` of action IDs (path), ``[]`` if
      ``start == target``, or ``None`` if target unreachable
    - Stride-aware via ``action_dirs``; arrival uses Chebyshev tolerance
      computed from ``max(stride // 2, 1)``

Precondition contract:
    Caller is responsible for ensuring NavAtlas is populated before
    extracting fields and invoking. NavPlan construction at WO-05 will
    gate on ``context.nav_atlas is not None`` upstream of any
    ``nav_bfs_stride`` call.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np


def nav_bfs_stride(
    grid: np.ndarray,
    start: Tuple[int, int],
    target: Tuple[int, int],
    passable_classes: Set[int],
    ego_value_set: FrozenSet[int],
    action_dirs: Dict[int, Tuple[int, int]],
    blocked_classes: Optional[Set[int]] = None,
) -> Optional[List[int]]:
    """BFS in stride-quantized action space.

    V3.5 source: ``memory/nav_atlas.py:324-415``.
    Transplanted from V3 ``phase2/strategy_executor.nav_bfs_path``,
    extended to use stride-aware ``action_dirs`` and dual-mode
    passability (WO-LS20-RESTORE-06).

    Parameters
    ----------
    grid : 2D array
        Current observation. Used for cell-class lookups during
        neighbor expansion.
    start : (row, col)
        Current ego centroid position. BFS begins here.
    target : (row, col)
        Target position. BFS terminates when a neighbor is within
        Chebyshev tolerance of this coordinate.
    passable_classes : Set[int]
        Confirmed traversable classes (whitelist, legacy mode).
        Ignored when ``blocked_classes`` is provided.
    ego_value_set : FrozenSet[int]
        Ego class IDs (always passable for the ego).
    action_dirs : Dict[int, Tuple[int, int]]
        Stride-aware displacement per action ID. ``{action_id: (dr, dc)}``.
        For a stride-5 NAV world: ``{1: (-5, 0), 2: (5, 0), 3: (0, -5),
        4: (0, 5)}``.
    blocked_classes : Optional[Set[int]]
        Confirmed wall classes (blacklist mode, **preferred for
        early-game states**). When provided, only cells whose class is
        in ``blocked_classes`` are excluded; all unknown classes are
        assumed passable. WO-LS20-RESTORE-06 mechanism.

    Returns
    -------
    Optional[List[int]]
        - Ordered list of action IDs to reach the target, or
        - ``[]`` if ``start == target``, or
        - ``None`` if target is unreachable from start under the
          provided passability oracle.
    """
    if start == target:
        return []

    frame = np.asarray(grid, dtype=np.int32)
    H, W = frame.shape[:2]

    # Stride-tolerance arrival: targets may not be exactly on the stride lattice.
    # Use Chebyshev distance tolerance = max(1, stride // 2) so the agent lands
    # within one stride half-step of the target (agent footprint covers the rest).
    _strides = [
        max(abs(dr), abs(dc))
        for dr, dc in action_dirs.values()
        if dr != 0 or dc != 0
    ]
    _stride_val = max(_strides) if _strides else 1
    _tol = max(1, _stride_val // 2)  # e.g. stride=5 → tol=2

    visited: Set[Tuple[int, int]] = {start}
    queue: deque = deque([(start, [])])

    while queue:
        pos, path = queue.popleft()
        r, c = pos

        for action_id, (dr, dc) in sorted(action_dirs.items()):
            nr, nc = r + dr, c + dc
            next_pos = (nr, nc)

            if not (0 <= nr < H and 0 <= nc < W):
                continue
            if next_pos in visited:
                continue

            new_path = path + [action_id]

            # Arrival: Chebyshev tolerance — target may not be exactly on the
            # stride lattice; accept when within tol of target.
            if abs(nr - target[0]) <= _tol and abs(nc - target[1]) <= _tol:
                return new_path

            # WO-LS20-RESTORE-06: Passability — blacklist preferred over whitelist.
            # When blocked_classes is provided: assume unknown = passable, only
            # skip proven walls. This handles early-game state where
            # walkable_classes is sparse (ego has explored little of the map).
            # Legacy whitelist (passable_classes) used when blocked_classes=None.
            cell_class = int(frame[nr, nc])
            if blocked_classes is not None:
                # Blacklist path: only confirmed wall classes are excluded.
                # Ego classes are never in blocked_classes so always pass.
                if cell_class in blocked_classes:
                    continue
            else:
                # Legacy whitelist path: only confirmed walkable classes allowed.
                if (
                    cell_class not in passable_classes
                    and cell_class not in ego_value_set
                ):
                    continue

            visited.add(next_pos)
            queue.append((next_pos, new_path))

    return None


__all__ = ["nav_bfs_stride"]

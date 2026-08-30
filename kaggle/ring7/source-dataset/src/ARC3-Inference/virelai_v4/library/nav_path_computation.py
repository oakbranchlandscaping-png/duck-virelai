"""
virelai_v4/library/nav_path_computation.py — BFS-driven path computation for NavPlan.

Per WO-CAMPAIGN3-PHASE1-05 (May 2, 2026, Phase 1 NAV SUBSTRATE
culminating WO).

Per Director Ruling 2 (May 2, 2026, north star prep, Option α):
    NavPlan reads BFS paths from the substrate via this module's
    compute_path. On unreachable, returns None; NavPlan aborts;
    dispatch layer falls back to reactive Tier 3 NAV.

PORT/INVENT split (per Step 0 §7.1):
    PORT (verbatim semantics):
        - The BFS invocation pattern from V3.5
          ``execution/nav_executor.py:1000-1006`` (always blacklist mode)

    INVENT (V4-native):
        - Single-target compute_path (V3.5's `_plan_bfs_path` handles
          target rotation / mutation prioritization / attempted_set /
          near-target safety net / visited-cells fallback — these are
          dispatch-layer concerns in V4 per Director Ruling 2 Option α)
        - V4 module structure (arcengine-independent free function;
          tests target the free function directly per V4 testability
          idiom established at WO-04 nav_substrate_update)

V4 simplifications vs V3.5 ``_plan_bfs_path``:
    - Single target (no rotation, no mutation prioritization)
    - No near-target safety net (defer to future polish WO if needed)
    - No visited-cells fallback (defer to future WO if needed)
    - Returns ``Optional[List[int]]`` directly: None on unreachable,
      [] on start==target, ordered list otherwise. (V3.5 returns []
      for both unreachable and start==target; V4's distinction lets
      NavPlan abort on None vs complete on [].)
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from virelai_v4.library.nav_atlas import NavAtlas
from virelai_v4.library.nav_bfs import nav_bfs_stride


def compute_path(
    nav_atlas: NavAtlas,
    target: Tuple[int, int],
    ego_pos: Tuple[int, int],
    grid: np.ndarray,
) -> Optional[List[int]]:
    """Compute BFS path from ``ego_pos`` to ``target`` through the
    NavAtlas substrate.

    PORT (V3.5 ``execution/nav_executor.py:1000-1006``):
        Always uses blacklist mode (passes ``nav_atlas.blocked_classes``).
        Caller's substrate determines correctness — empty
        ``blocked_classes`` (Life 1 pre-record_move) yields optimistic
        BFS that treats every cell as passable; populated
        ``blocked_classes`` (post-record_move accumulation) avoids
        known walls.

    Parameters
    ----------
    nav_atlas : NavAtlas
        The substrate. Must be non-None — caller (NavPlan.next_action)
        gates on ``context.nav_atlas is not None``.
    target : Tuple[int, int]
        The target coordinate. Single target per Director Ruling 2
        Option α; target rotation is the dispatch layer's concern.
    ego_pos : Tuple[int, int]
        Current ego position. From ``context.ego_current_pos``.
    grid : np.ndarray
        Current observation. Used by ``nav_bfs_stride`` for cell-class
        lookups during neighbor expansion.

    Returns
    -------
    Optional[List[int]]
        - Ordered list of action IDs to reach target, OR
        - ``[]`` if ego_pos == target (already arrived), OR
        - ``None`` if target is unreachable from ego_pos under the
          current substrate.

    NavPlan contract: on None, NavPlan sets ``aborted=True``; dispatch
    layer falls back to reactive Tier 3 NAV per Director Ruling 2.
    """
    return nav_bfs_stride(
        grid=grid,
        start=ego_pos,
        target=target,
        passable_classes=nav_atlas.walkable_classes,
        ego_value_set=nav_atlas.ego_value_set,
        action_dirs=nav_atlas.action_dirs,
        blocked_classes=nav_atlas.blocked_classes,
    )


__all__ = ["compute_path"]

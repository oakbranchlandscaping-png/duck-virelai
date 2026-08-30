"""
virelai_v4/library/nav_atlas.py — NAV World Spatial Memory

Ported from V3.5 canonical implementation at
``Universal_Solver_v3_5/memory/nav_atlas.py:30`` per
WO-CAMPAIGN3-PHASE1-01 (May 2, 2026, Phase 1 NAV SUBSTRATE).

V3.5 inheritance source: this class is the V3.5 production-grade NavAtlas
proven across the V3.5 forge campaigns (WO-FORGE-06, WO-FORGE-NAV-04,
WO-FORGE-NAV-06, WO-FORGE-NAV-II-02, WO-FORGE-NAV-II-03, WO-NAV-SITE-MEM-01,
WO-NAR-07). The V3.5 closing audit Module Guide flagged it
``TRANSPLANT AS-IS``; this port follows that disposition with the
modifications enumerated below.

V3.5 LEGACY DROP (Halt 3 ratified May 2, 2026):
    A second ``NavAtlas`` exists at V3.5
    ``memory/world_rule_memory.py:117`` with a different interface
    (passable_cells / blocking_cells sets-of-coordinates, not
    walkable_classes / blocked_classes sets-of-class-IDs). It is the
    legacy class flagged for deprecation. **It is NOT ported.** Tests
    targeting the legacy class (``test_memory/test_world_rule_memory.py``,
    26 tests) are DROPPED with the legacy class.

V4 ARCHITECTURE COMPLIANCE MODIFICATIONS (per WO-CAMPAIGN3-PHASE1-01 §INHERITANCE):
    1. File location: ``virelai_v4/library/nav_atlas.py`` (not ``memory/``).
       NavAtlas is the spatial substrate for the semantic library; it
       lives where the library lives in V4 architecture.
    2. ``nav_bfs_stride`` and ``nav_bfs_visited`` are **NOT** ported in
       this WO. They land in WO-02 as standalone module functions.
    3. Empirical population of ``action_dirs`` is **NOT** ported here.
       It lands in WO-03 (minimal stride probe per Option B).
    4. ``record_move`` integration into the V4 cybernetic loop is
       **NOT** wired here. It lands in WO-04. The class is ported and
       the method is callable; nothing in production code paths
       invokes it yet.

PERSISTENCE TAXONOMY (field-granular, per Halt 2 ratified May 2, 2026):

    PER_GAME — preserved across level transitions; cleared only at
    game end. Populated once per game by the V3.5 gambit / V4 stride
    probe (WO-03):

        ego_class, ego_value_set, ego_spawn, action_dirs

    PER_LEVEL — cleared on level transition by ``reset_spatial()``.
    These are position-specific; coordinates and class memberships
    change between levels:

        visited_cells, walkable_classes, blocked_classes,
        adjacent_classes, target_candidates, contacted_sites,
        target_attempt_count, mutation_targets, unreachable_targets,
        blocked_edges, site_delta_history, step_delta_log

    The pre-WO-CAMPAIGN3-PHASE1-00 OPEN_FLAGS_REGISTER classification of
    ``walkable_classes`` / ``blocked_classes`` / ``visited_cells`` as
    ``PERSIST_LIVES_AND_LEVELS`` was Strategy Chamber inference, not
    V3.5 source verification. ``reset_spatial()`` in V3.5 clears those
    fields on level transition; the corrected taxonomy is field-granular.
    See INHERITANCE_PRE_AUDIT_PATTERN.md Example F.

Design contract (preserved verbatim from V3.5):
    - Ground truth only — no inference, no class derivation
    - Updated per-observation in the cybernetic loop (WO-04 wires this)
    - Read by ``nav_bfs_stride`` (WO-02) for passability oracle
    - Held on ``VirelaiContext.nav_atlas``

Module-level utility functions ported in this WO:
    find_ego_position, find_ego_anchor_position, find_nav_targets

Functions DEFERRED to WO-02 (BFS port):
    nav_bfs_stride, nav_bfs_visited
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

from virelai_v4.contracts.lever_mechanism import LeverCensus


# ---------------------------------------------------------------------------
# NavAtlas — empirical world model for NAV worlds
# ---------------------------------------------------------------------------


@dataclass
class NavAtlas:
    """Persistent empirical world model built during NAV exploration.

    Ported from V3.5 canonical implementation. Field-granular
    persistence taxonomy ratified at WO-CAMPAIGN3-PHASE1-00 Halt 2
    (May 2, 2026).

    Held on ``VirelaiContext.nav_atlas``. Per-game fields persist via
    the context's ``persist_lives_and_levels`` enclosure;
    per-level fields clear at level transition via
    ``reset_spatial()``.
    """

    # ─── PER_GAME fields (preserved across level transitions) ───────────────
    ego_class: int                                    # primary ego class (V3 compat)
    ego_value_set: FrozenSet[int]                     # full multi-class ego identity
    ego_spawn: Tuple[int, int]                        # spawn position (row, col)

    # ─── PER_LEVEL fields (cleared on level transition by reset_spatial) ────
    visited_cells: Set[Tuple[int, int]] = field(default_factory=set)
    walkable_classes: Set[int] = field(default_factory=set)
    blocked_classes: Set[int] = field(default_factory=set)
    adjacent_classes: Set[int] = field(default_factory=set)

    # ─── PER_GAME field — populated by stride probe (WO-03) ─────────────────
    # Stride-aware action directions {action_id: (dr, dc)}.
    # Default: pixel-space unit vectors (stride=1 fallback). The minimal
    # stride probe (WO-03) overwrites this once per game with stride-aware
    # values (e.g., {1:(-5,0), 2:(5,0), 3:(0,-5), 4:(0,5)} for a stride-5
    # world like ls20). Once populated, persists across levels.
    action_dirs: Dict[int, Tuple[int, int]] = field(
        default_factory=lambda: {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}
    )

    # ─── PER_LEVEL: NAV target candidates surfaced from grid scan ───────────
    target_candidates: List[Tuple[int, int]] = field(default_factory=list)

    # ─── PER_LEVEL: WO-FORGE-06-NAV-HOTFIX-02 Bug B ─────────────────────────
    # Coordinates where NAV contact reactivity fired — excluded from BFS
    # target selection so the solver does not oscillate between the same
    # button tiles across multiple lives.
    contacted_sites: Set[Tuple[int, int]] = field(default_factory=set)

    # ─── PER_LEVEL: WO-FORGE-NAV-04 Target Rotation ─────────────────────────
    # Per-target BFS attempt count across lives within the same level.
    # Incremented once per life for every target that BFS was dispatched
    # toward. Used to deprioritize previously attempted targets so each life
    # explores different territory. Cleared at level transition because
    # coordinates are level-local.
    target_attempt_count: Dict[Tuple[int, int], int] = field(default_factory=dict)

    # ─── PER_LEVEL: WO-FORGE-NAV-06 Door Chase ──────────────────────────────
    # World mutation centroids extracted from confirmed lever contact events.
    # E.g. door location after a button press. These are BFS-prioritized
    # above all normal candidates (score = attempts:-1).
    mutation_targets: Set[Tuple[int, int]] = field(default_factory=set)

    # ─── PER_LEVEL: WO-FORGE-NAV-II-02 Unreachability Detection ─────────────
    # Targets confirmed unreachable via consecutive blocked navigation
    # attempts. Filtered from all BFS candidate lists so the solver never
    # re-attempts a dead zone.
    unreachable_targets: Set[Tuple[int, int]] = field(default_factory=set)

    # ─── PER_LEVEL: WO-FORGE-NAV-II-03 Wall Crawl ───────────────────────────
    # Specific (position, action_id) pairs that produced zero movement.
    # Prevents reissuing the exact same blocked action at the same position.
    # Tier 1 of the wall crawl strategy.
    # Element type: Tuple[Tuple[int, int], int] ← frozenset-safe tuples.
    blocked_edges: Set[Tuple[Tuple[int, int], int]] = field(default_factory=set)

    # ─── PER_LEVEL: WO-NAV-SITE-MEM-01 Per-site delta history ───────────────
    # Maps (row, col) → [effect_pixel_count, ...] — one entry per confirmed
    # contact. Cleared at level transition (coordinates change between
    # levels). Replaces the local _site_delta_history dict in V3.5
    # run_nav_execution, which was reset each life and therefore invisible
    # to Qwen on Life 2+.
    site_delta_history: Dict[Tuple[int, int], List[int]] = field(default_factory=dict)

    # ─── PER_LEVEL: WO-NAR-07 Per-step delta log ────────────────────────────
    # Per-step (world_delta, hud_delta) log for narrative TEMPORAL BEHAVIOR.
    # Appended to by _process_nav_step for every non-teleport step.
    # Cleared at level transition. Teleport steps are excluded.
    step_delta_log: List[Tuple[int, int]] = field(default_factory=list)

    # ─── PER_LEVEL: WO-CAMPAIGN3-PHASE2-01 NAV lever candidate evidence ──
    # Structured evidence from contact_reactivity detection. Each candidate
    # captures the NavLeverCandidate dataclass (coordinate, kernel_integer,
    # observed_effect_region, etc.). Cleared at level transition because
    # lever coordinates are level-local. The companion ``contacted_sites``
    # field (above) stores the ego destination coordinates for BFS-exclusion;
    # this field stores the structured evidence for downstream consumption
    # (mechanic_memory.lever_kernel_classes; library role transition).
    nav_lever_candidates: List[object] = field(default_factory=list)

    # ─── PER_GAME: WO-CAMPAIGN3-PHASE2-01 lever orphan counter ──────────
    # Increments whenever contact_reactivity flags a lever candidate at a
    # coordinate that does NOT fall within any library object's cells
    # (point-in-cells lookup miss). Survives life and level transitions
    # so Phase 2 closure can surface the orphan rate as a tunable
    # diagnostic per Director Ruling. PER_GAME because lever-orphan
    # phenomena are about library-grid_scan completeness, not level state.
    lever_orphan_count: int = 0

    # ─── PER_LEVEL: WO-CAMPAIGN3-PHASE3-01 cycle probe aggregate ──────────
    # LeverCensus aggregating per-lever TransitionProfile verdicts produced
    # by the cycle probe. PER_LEVEL because lever coordinates are level-local
    # (per Phase 2 nav_lever_candidates persistence). Cleared in
    # reset_spatial(). Wired in WO-PHASE3-02 Lever Verdict Integration.
    lever_census: Optional[LeverCensus] = None

    @property
    def coverage(self) -> float:
        """Fraction of a 64×64 grid that has been visited."""
        return len(self.visited_cells) / 4096.0 if self.visited_cells else 0.0

    def reset_spatial(self) -> None:
        """Clear PER_LEVEL state on level transition.

        V3.5 source: ``memory/nav_atlas.py:105-133`` (WO-BOOTSTRAP-01).

        Fields cleared (PER_LEVEL — position-specific, invalidated by
        level change):

            visited_cells, walkable_classes, blocked_classes,
            adjacent_classes, target_candidates, contacted_sites,
            target_attempt_count, mutation_targets, unreachable_targets,
            blocked_edges, site_delta_history, step_delta_log.

        Fields preserved (PER_GAME — game-global physics, valid on
        Level 2+):

            ego_class, ego_value_set, ego_spawn (overwritten by
            bootstrap on level entry), action_dirs.

        Field-granular persistence taxonomy ratified at WO-CAMPAIGN3-
        PHASE1-00 Halt 2 (May 2, 2026).
        """
        self.visited_cells.clear()
        self.walkable_classes.clear()
        self.blocked_classes.clear()
        self.adjacent_classes.clear()
        self.target_candidates.clear()
        self.contacted_sites.clear()
        self.target_attempt_count.clear()
        self.mutation_targets.clear()
        self.unreachable_targets.clear()
        self.blocked_edges.clear()
        self.site_delta_history.clear()
        self.step_delta_log.clear()
        # WO-CAMPAIGN3-PHASE2-01: PER_LEVEL nav_lever_candidates clear.
        # ``lever_orphan_count`` is PER_GAME and intentionally NOT cleared
        # here (survives level transitions to support Phase 2 closure
        # diagnostics).
        self.nav_lever_candidates.clear()
        # WO-CAMPAIGN3-PHASE3-01: PER_LEVEL lever_census clear.
        # Cycle probe verdicts are level-local (lever coordinates change
        # between levels); cleared on level transition.
        self.lever_census = None

    def record_move(
        self,
        prev_pos: Tuple[int, int],
        new_pos: Tuple[int, int],
        action_id: int,
        moved: bool,
        grid: Optional[np.ndarray] = None,
        prev_grid: Optional[np.ndarray] = None,
    ) -> None:
        """Update atlas from a single observation.

        V3.5 source: ``memory/nav_atlas.py:135-204``.
        Signature corrected per WO-CAMPAIGN3-PHASE1-00 Q1.3 finding —
        primer's claimed signature ``(action_id, ego_before, ego_after,
        frame_before, frame_after)`` was DRIFT; this is the actual V3.5
        signature.

        Caller passes the ``moved`` boolean; this method does not infer
        move success from displacement.

        Method body is **NOT** invoked from V4 production paths in
        WO-CAMPAIGN3-PHASE1-01 — integration into the cybernetic loop
        is deferred to WO-04. The method is callable for tests.

        Parameters
        ----------
        prev_pos  : ego position before action
        new_pos   : ego position after action
        action_id : 1=UP 2=DOWN 3=LEFT 4=RIGHT
        moved     : True if ego actually moved (not blocked)
        grid      : post-step grid (ego is at new_pos here)
        prev_grid : pre-step grid (ego was at prev_pos; new_pos shows floor class)
        """
        if moved:
            self.visited_cells.add(new_pos)
            if grid is not None:
                try:
                    g = np.asarray(grid)
                    # Bug A fix: read prev_pos in post-step grid (ego just vacated
                    # → reveals the floor class the ego was standing on).
                    floor_class = int(g[prev_pos[0], prev_pos[1]])
                    if floor_class not in self.ego_value_set:
                        self.walkable_classes.add(floor_class)
                        self.blocked_classes.discard(floor_class)
                        self.adjacent_classes.discard(floor_class)
                except (IndexError, TypeError):
                    pass
            if prev_grid is not None:
                try:
                    pg = np.asarray(prev_grid)
                    # Destination floor class: class at new_pos BEFORE ego entered.
                    # Confirms the destination cell is also traversable.
                    dest_floor_class = int(pg[new_pos[0], new_pos[1]])
                    if dest_floor_class not in self.ego_value_set:
                        self.walkable_classes.add(dest_floor_class)
                        self.blocked_classes.discard(dest_floor_class)
                        self.adjacent_classes.discard(dest_floor_class)
                        # Class 0/1 destination → target candidate
                        if dest_floor_class in (0, 1):
                            if new_pos not in self.target_candidates:
                                self.target_candidates.append(new_pos)
                except (IndexError, TypeError):
                    pass
        else:
            # Blocked — record the adjacent (destination) class
            _d = self.action_dirs.get(action_id)
            if _d is not None and grid is not None:
                br, bc = prev_pos[0] + _d[0], prev_pos[1] + _d[1]
                try:
                    g = np.asarray(grid)
                    if 0 <= br < g.shape[0] and 0 <= bc < g.shape[1]:
                        cell_class = int(g[br, bc])
                        if cell_class not in self.ego_value_set:
                            self.adjacent_classes.add(cell_class)
                            if cell_class not in self.walkable_classes:
                                self.blocked_classes.add(cell_class)
                            # Class 0/1 adjacent → target candidate
                            if cell_class in (0, 1):
                                adj_pos = (br, bc)
                                if adj_pos not in self.target_candidates:
                                    self.target_candidates.append(adj_pos)
                except (IndexError, TypeError, AttributeError):
                    pass

    def set_target_candidates(self, candidates: List[Tuple[int, int]]) -> None:
        """Set target candidates (from grid scan).

        V3.5 source: ``memory/nav_atlas.py:206-210``.
        """
        for c in candidates:
            if c not in self.target_candidates:
                self.target_candidates.append(c)


# ---------------------------------------------------------------------------
# Utility: detect ego position from grid
# ---------------------------------------------------------------------------


def find_ego_position(
    grid,
    agent_value_set: FrozenSet[int],
) -> Optional[Tuple[int, int]]:
    """Compute ego centroid from grid using agent_value_set.

    Returns (row, col) centroid rounded to int, or None if not found.

    V3.5 source: ``memory/nav_atlas.py:217-232``.
    """
    frame = np.asarray(grid, dtype=np.int32)
    ego_mask = np.zeros(frame.shape[:2], dtype=bool)
    for class_id in agent_value_set:
        ego_mask |= (frame == class_id)
    if not ego_mask.any():
        return None
    rows, cols = np.where(ego_mask)
    return (int(round(float(rows.mean()))), int(round(float(cols.mean()))))


def find_ego_anchor_position(
    grid,
    anchor_class: int,
) -> Optional[Tuple[int, int]]:
    """Find ego position by scanning the grid for the anchor class.

    Returns (min_row, min_col) — the top-left corner of the ego's
    bounding box.

    V3.5 production method (probe_priority_queue.py → find_agent_pos):
        ``np.argwhere(grid == anchor_class)[0]`` returns the topmost-
        leftmost pixel in row-major order, which equals (min_row,
        min_col) for a contiguous cluster. Integer-exact, stride-clean,
        immune to asymmetric class pixel density.

    WO-FORGE-NAV-05b: Primary ego position source replacing dead reckoning.

    V3.5 source: ``memory/nav_atlas.py:235-255``.
    """
    frame = np.asarray(grid, dtype=np.int32)
    positions = np.argwhere(frame == anchor_class)
    if len(positions) == 0:
        return None
    return (int(positions[0][0]), int(positions[0][1]))


# ---------------------------------------------------------------------------
# Utility: find NAV target candidates from grid
# ---------------------------------------------------------------------------


def find_nav_targets(
    grid,
    atlas: NavAtlas,
    max_targets: int = 8,
) -> List[Tuple[int, int]]:
    """Scan grid for NAV target candidates.

    Priority:
        1. Class 0/1 positions (zero-magnet: destination holes,
           binary displays)
        2. Rarest non-ego, non-walkable, non-blocked classes
        3. Any non-ego class not yet classified

    Returns list of (row, col) positions sorted by priority.

    V3.5 source: ``memory/nav_atlas.py:262-317``.
    """
    frame = np.asarray(grid, dtype=np.int32)
    targets: List[Tuple[int, int]] = []

    # Priority 1: class 0/1 positions (V3 zero-magnet pattern)
    for class_id in (0, 1):
        mask = (frame == class_id)
        if mask.any():
            rows, cols = np.where(mask)
            for r, c in zip(rows[:2].tolist(), cols[:2].tolist()):
                pos = (int(r), int(c))
                if pos not in targets:
                    targets.append(pos)

    # Existing atlas targets
    for t in atlas.target_candidates:
        if t not in targets:
            targets.append(t)

    if len(targets) >= max_targets:
        return targets[:max_targets]

    # Priority 2: rarest classes not yet confirmed walkable/blocked/ego
    unique, counts = np.unique(frame, return_counts=True)
    # sort by pixel count ascending (rarest first)
    order = np.argsort(counts)
    for idx in order:
        class_id = int(unique[idx])
        if class_id in atlas.ego_value_set:
            continue
        if class_id in atlas.walkable_classes:
            continue
        mask = (frame == class_id)
        if not mask.any():
            continue
        rows, cols = np.where(mask)
        pos = (int(rows[0]), int(cols[0]))
        if pos not in targets:
            targets.append(pos)
        if len(targets) >= max_targets:
            break

    return targets[:max_targets]


__all__ = [
    "NavAtlas",
    "find_ego_position",
    "find_ego_anchor_position",
    "find_nav_targets",
]

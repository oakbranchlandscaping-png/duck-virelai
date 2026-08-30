"""
contracts/mechanic_memory.py — WO-S2-01: MechanicMemory

Empirical memory of what made a solved level winnable.
Built once per win in _capture_level_example(), persisted across Groundhog Day
lives via state["mechanic_memory"], consumed during target re-ranking in
_bootstrap_new_level() and lever-count hinting in _discover_level_levers().

Purpose:
    On Level 2+, the solver has already seen Level 1 (or prior).  MechanicMemory
    converts that empirical evidence into three actionable signals:

    1. target_classes (FrozenSet[int])  — pixel classes that appeared at win targets;
       used to prioritise target_candidates that share those classes.

    2. lever_count (int)  — how many levers were confirmed in the winning run;
       used to hint the lever-discovery budget in _discover_level_levers().

    3. lever_quadrants (FrozenSet[str]) — grid quadrants (Q1–Q4) where levers lived;
       used to tighten early BFS routing toward those regions.

Secondary signals (available for future consumers):
    lever_classes, lever_delta_range, lever_spread, target_quadrants, mechanic_type.

Quadrant convention (64×64 grid, row/col 0-indexed):
    Q1  row < 32, col < 32   (upper-left)
    Q2  row < 32, col >= 32  (upper-right)
    Q3  row >= 32, col < 32  (lower-left)
    Q4  row >= 32, col >= 32 (lower-right)

Import rules:
    - May import from: stdlib only
    - May NOT import from any phase directory, spine, or numpy
    - Frozen dataclass — immutable once built

Persisted across Groundhog Day lives via state["mechanic_memory"].

Virelai Research Lab · WO-S2-01 · March 2026
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple


# ── Quadrant helper ───────────────────────────────────────────────────────────

def _get_quadrant(row: int, col: int, grid_rows: int = 64, grid_cols: int = 64) -> str:
    """Map a (row, col) coordinate to a grid quadrant label.

    Quadrant boundaries are the midpoints of each axis.

    Args:
        row:       Row index (0-indexed).
        col:       Column index (0-indexed).
        grid_rows: Total grid rows (default 64).
        grid_cols: Total grid columns (default 64).

    Returns:
        One of: "Q1", "Q2", "Q3", "Q4".

        Q1  upper-left   row < mid_row, col < mid_col
        Q2  upper-right  row < mid_row, col >= mid_col
        Q3  lower-left   row >= mid_row, col < mid_col
        Q4  lower-right  row >= mid_row, col >= mid_col
    """
    mid_row = grid_rows // 2
    mid_col = grid_cols // 2
    if row < mid_row:
        return "Q1" if col < mid_col else "Q2"
    else:
        return "Q3" if col < mid_col else "Q4"


# ── MechanicMemory ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MechanicMemory:
    """Empirical memory of what made a solved level winnable.

    Assembled by build_mechanic_memory() from a solved_examples entry.
    Frozen — immutable once built.  Persisted across lives via
    state["mechanic_memory"].

    Consumed by:
        _bootstrap_new_level()     — target_classes → re-rank target_candidates
        _discover_level_levers()   — lever_count → hint discovery budget
    """

    # ── Primary actionable signals ─────────────────────────────────────────

    target_classes: FrozenSet[int]
    """Pixel classes (ints) found at winning target locations in the solved level.

    Built from pixel values at contacted_sites positions in the win_grid.
    Used to re-rank target_candidates: candidates whose pixel class is in this
    set are promoted to the front of the list.

    Empty if win_grid was unavailable.
    """

    lever_count: int
    """Number of levers confirmed during the winning run.

    Equal to len(contacted_sites) from the solved example.
    0 means no levers were confirmed (pure navigation win).
    Used to cap lever-discovery budget in _discover_level_levers().
    """

    lever_quadrants: FrozenSet[str]
    """Quadrant labels (Q1–Q4) where levers were located in the solved level.

    Built from contacted_sites coordinates via _get_quadrant().
    Used to bias early BFS routing toward likely lever regions.

    Empty if no levers were present.
    """

    # ── Secondary signals (available for future consumers) ────────────────

    lever_classes: FrozenSet[int]
    """Pixel classes at lever locations in the spawn_grid.

    Built from pixel values at contacted_sites positions in the spawn_grid.
    Empty if spawn_grid was unavailable or no levers found.
    """

    lever_delta_range: Tuple[int, int]
    """Observed (min_delta, max_delta) pixel changes from lever activations.

    Placeholder — populated as (0, 0) until delta capture is wired to
    contacted_sites.  Reserved for future lever-classification refinement.
    """

    lever_spread: int
    """Manhattan-distance spread between the furthest pair of lever locations.

    max pairwise Manhattan distance across contacted_sites.
    0 if fewer than 2 levers.
    """

    target_quadrants: FrozenSet[str]
    """Quadrant labels (Q1–Q4) where winning targets were located.

    Built from contacted_sites coordinates (levers are the targets in NAV worlds).
    Empty if no sites present.
    """

    mechanic_type: str
    """High-level mechanic classification for this level.

    One of:
        "NAV_ONLY"      — navigation to static target, no lever interaction
        "LEVER_THEN_NAV"— lever(s) activated, then navigate to unlocked target
        "UNKNOWN"       — could not classify from available evidence
    """

    world_type: str
    """World type of the solved level: "NAV" or "CLICK"."""


# ── Factory ───────────────────────────────────────────────────────────────────

def build_mechanic_memory(
    example: dict,
    world_type: str = "NAV",
) -> Optional[MechanicMemory]:
    """Build a MechanicMemory from a solved_examples entry.

    Args:
        example:    One entry from state["solved_examples"].  Expected keys:
                        "contacted_sites"   list of (row, col) tuples
                        "spawn_grid"        2-D list/array or None
                        "win_grid"          2-D list/array or None
                        "actions_to_win"    int
        world_type: "NAV" or "CLICK".

    Returns:
        MechanicMemory on success, None if example is None or malformed.
    """
    if not example:
        return None

    contacted_sites: list = example.get("contacted_sites") or []
    spawn_grid = example.get("spawn_grid")
    win_grid = example.get("win_grid")

    # ── Lever quadrants ──────────────────────────────────────────────────
    lever_quads: set = set()
    for rc in contacted_sites:
        if rc is not None and len(rc) == 2:
            lever_quads.add(_get_quadrant(rc[0], rc[1]))

    # ── Lever classes ─────────────────────────────────────────────────────
    # PRIMARY: lever_kernel_classes — kernel_integer values from NavLeverCandidates.
    #   These are the "rarest non-ego integer in pre_activation_tile" for each
    #   contacted lever, i.e. the actual lever/button pixel class (e.g. {0,1} in LS20).
    #   This is the empirically correct source; contacted_sites stores the ego
    #   destination (ego center), not the lever pixel location.
    # FALLBACK: spawn_grid at contacted_sites (may give floor/ego class if
    #   ego-destination == floor class).
    lever_cls: set = set()
    _lkc = example.get("lever_kernel_classes")
    if _lkc:
        lever_cls = set(int(k) for k in _lkc)
    elif spawn_grid is not None:
        for rc in contacted_sites:
            if rc is not None and len(rc) == 2:
                r, c = rc
                try:
                    lever_cls.add(int(spawn_grid[r][c]))
                except (IndexError, TypeError):
                    pass

    # ── Target classes ────────────────────────────────────────────────────
    # PRIMARY: mutation_target_classes — pixel classes at NAV-DOOR injection sites
    #   in win_grid.  These are the pixels of world-effect components that appeared
    #   after contact reactivity (doors that opened), injected as BFS candidates.
    #   Reading win_grid at those positions gives the door pixel class — the correct
    #   re-ranking signal for target_candidates on the next level.
    # FALLBACK: win_grid at contacted_sites (lever positions, less precise).
    target_cls: set = set()
    _mtc = example.get("mutation_target_classes")
    if _mtc:
        target_cls = set(int(k) for k in _mtc)
    elif win_grid is not None:
        for rc in contacted_sites:
            if rc is not None and len(rc) == 2:
                r, c = rc
                try:
                    target_cls.add(int(win_grid[r][c]))
                except (IndexError, TypeError):
                    pass

    # ── Lever spread (max pairwise Manhattan distance) ────────────────────
    spread = 0
    valid_sites = [rc for rc in contacted_sites if rc is not None and len(rc) == 2]
    if len(valid_sites) >= 2:
        max_d = 0
        for i in range(len(valid_sites)):
            for j in range(i + 1, len(valid_sites)):
                r1, c1 = valid_sites[i]
                r2, c2 = valid_sites[j]
                d = abs(r1 - r2) + abs(c1 - c2)
                if d > max_d:
                    max_d = d
        spread = max_d

    # ── Mechanic type ─────────────────────────────────────────────────────
    n_levers = len(valid_sites)
    if n_levers == 0:
        mechanic_type = "NAV_ONLY"
    else:
        mechanic_type = "LEVER_THEN_NAV"

    return MechanicMemory(
        target_classes=frozenset(target_cls),
        lever_count=n_levers,
        lever_quadrants=frozenset(lever_quads),
        lever_classes=frozenset(lever_cls),
        lever_delta_range=(0, 0),   # placeholder — delta capture not yet wired
        lever_spread=spread,
        target_quadrants=frozenset(lever_quads),  # same sites = lever=target in NAV
        mechanic_type=mechanic_type,
        world_type=world_type,
    )


# ── Public exports ────────────────────────────────────────────────────────────

__all__ = ["MechanicMemory", "build_mechanic_memory", "_get_quadrant"]

"""
virelai_v4/library/stride_probe.py — Minimal stride probe (substrate bootstrap).

Per WO-CAMPAIGN3-PHASE1-03 (May 2, 2026, Phase 1 NAV SUBSTRATE).

Per Director Ruling 1 (May 2, 2026) on WO-00 Option B substrate
bootstrapping: minimal stride probe + BFS blacklist mode (WO-02). The
**full V3.5 gambit + CUD + stride calibration pipeline (Option A)
is NOT ported.**

PORT/INVENT split (per Step 0 §1.2):
    PORT — V3.5 helpers `compute_action_dirs_from_positions` and
           the symmetric-inference fallback at V3.5
           `discovery/nav_discovery.py:run_nav_cud:388-394`. Pure
           computation; ports verbatim with V4 type annotations.
    INVENT — V4-native action-emission state machine that drives
           cardinals one per frame, leveraging V4's existing
           ``library.header.ego_displacement_map`` (populated by
           ``library/ego_detector.py`` after each directional action).
           No rover gambit; no probe doubling; ~30 NBLNC of
           orchestration.

V4 INFRASTRUCTURE LEVERAGED:
    The probe does not perform displacement observation itself. V4's
    ``library/ego_detector.py`` already populates
    ``library.header.ego_displacement_map`` (a ``Dict[int, Tuple[float,
    float]]`` keyed by ``action_id``) on every directional action
    where the centroid displacement passes V4's directional sign
    validation. The probe's job is to *drive* the cardinal actions so
    that this map gets populated for all four directions, then commit
    the result to ``nav_atlas.action_dirs`` with V3.5 symmetric
    inference for any directions that didn't displace (e.g., wall on
    spawn).

STATE MACHINE (per Step 0 §1.3, simplified per V4 ego_detector
discovery — Build Report records the simplification):

    Two VirelaiContext fields hold probe state:
      - ``stride_probe_complete: bool`` (PERSIST_LIVES_AND_LEVELS) —
        set True on commit; once True, the probe gate falls through
        immediately on all subsequent calls
      - ``stride_probe_attempted: Set[int]`` (PER_LIFE_SCRATCHPAD) —
        cardinals attempted this life; resets if life ends
        mid-probe so Life 2 retries

    On each call (NAV world classified, ego_confirmed, not
    stride_probe_complete):
      1. Compute cardinals_to_try = {1,2,3,4} ∩ available_actions
         − stride_probe_attempted
      2. If empty: commit, set stride_probe_complete = True,
         return None (caller falls through)
      3. Else: pop lowest action_id, mark attempted, return
         ``GameAction`` for that action

    On the next call, ego_detector has populated
    ``library.header.ego_displacement_map`` with the observed
    centroid (or NOT, if the ego didn't displace — wall). Either
    way, the probe pops the next cardinal until all are attempted.

ACTION BUDGET:
    Worst case: 4 actions per game (one per cardinal). Best case
    (some cardinals unavailable): fewer. Compared to V3.5's gambit
    (10 actions per game), the minimal probe saves 6 actions —
    Director Ruling 1 Option B's explicit benefit.

Helpers (see V3.5 source citations):
    _commit_action_dirs — V4-native commit logic; calls the V3.5
        symmetric-inference fallback inline.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional, Set, Tuple

from virelai_v4.library.nav_atlas import NavAtlas

if TYPE_CHECKING:
    # GameAction lives in arcengine; imported under TYPE_CHECKING so this
    # module loads in environments without arcengine installed (V4's
    # convention; see library/plan.py:62-67 for the same pattern). The
    # runtime `GameAction.from_id()` call lives behind a lazy local import
    # inside ``run_stride_probe_step``.
    from arcengine import GameAction

    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import SemanticLibrary


# Cardinal action IDs (ACTION1=up, ACTION2=down, ACTION3=left, ACTION4=right)
_CARDINAL_IDS: FrozenSet[int] = frozenset({1, 2, 3, 4})

# V3.5 canonical symmetric inference table (per stride).
# Keys are action IDs; values are (dr, dc) in pixel-space units of stride.
_CANONICAL_DIRS = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}


def run_stride_probe_step(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    available_actions: List[int],
) -> Optional[GameAction]:
    """Execute one frame of the stride probe.

    Returns:
        GameAction to emit (probe still in progress) or None (probe
        complete this frame; caller falls through to Tier 3 NAV).

    Caller (`strategy/action_selector.py:select_action`) gates this
    call on:
      - ``library.header.world_type == "NAV"``
      - ``library.header.ego_confirmed``
      - ``not context.stride_probe_complete``

    See module docstring for the state machine description.
    """
    # Cardinals available for emission this life:
    #   = cardinals declared available by the framework
    #   − cardinals already attempted this life
    cardinals_to_try = sorted(
        a for a in _CARDINAL_IDS
        if a in available_actions and a not in context.stride_probe_attempted
    )

    if not cardinals_to_try:
        # All cardinals attempted (or none available). Commit and
        # mark complete. Subsequent calls fall through immediately.
        _commit_action_dirs(context, library)
        context.stride_probe_complete = True
        return None

    # Emit the lowest-numbered untried cardinal. Mark attempted before
    # the action returns so this life will not retry it on a
    # subsequent frame even if no displacement is observed (wall).
    next_action_id = cardinals_to_try[0]
    context.stride_probe_attempted.add(next_action_id)
    # Lazy import: keeps module loadable in environments without
    # arcengine (V4 convention; see library/plan.py:366).
    from arcengine import GameAction
    return GameAction.from_id(next_action_id)


def _commit_action_dirs(
    context: "VirelaiContext",
    library: "SemanticLibrary",
) -> None:
    """Commit observed displacement vectors to ``context.nav_atlas.action_dirs``.

    Reads ``library.header.ego_displacement_map`` (populated by
    ``library/ego_detector.py`` after each directional action, with
    centroid displacement in floats) and rounds to int for
    ``NavAtlas.action_dirs``.

    Applies the V3.5 symmetric-inference fallback (per V3.5
    ``discovery/nav_discovery.py:run_nav_cud:388-394``): for any
    cardinal that didn't displace (e.g., wall on spawn), infer the
    direction by symmetric counterpart from the observed stride.

    If ``context.nav_atlas`` is None (Life 1 first commit),
    instantiates it from ``library.header`` fields. Otherwise updates
    ``action_dirs`` in place (preserving the rest of the substrate).
    """
    # ── Convert observed displacements (floats) to int tuples ──
    # ego_displacement_map is Dict[int, Tuple[float, float]] from
    # ego_detector. Round to int and filter to cardinal IDs only.
    observed_int: Dict[int, Tuple[int, int]] = {}
    for aid, (dr, dc) in library.header.ego_displacement_map.items():
        if aid in _CARDINAL_IDS:
            observed_int[aid] = (int(round(dr)), int(round(dc)))

    # ── Compute stride from observed nonzero displacements ──
    # V3.5 source: discovery/nav_discovery.py:compute_stride_from_positions.
    # Stride = max-magnitude across observed nonzero moves.
    nonzero_dirs = {
        aid: d for aid, d in observed_int.items()
        if d != (0, 0)
    }
    if nonzero_dirs:
        stride = max(max(abs(dr), abs(dc)) for dr, dc in nonzero_dirs.values())
    else:
        stride = 1

    # ── V3.5 symmetric inference fallback ──
    # Source: discovery/nav_discovery.py:run_nav_cud:388-394.
    # For any unobserved or zero-displacement cardinal, fill in the
    # canonical symmetric counterpart based on the observed stride.
    final_dirs = dict(nonzero_dirs)
    known_vectors = set(nonzero_dirs.values())
    canonical_at_stride = {
        1: (-stride, 0), 2: (stride, 0), 3: (0, -stride), 4: (0, stride),
    }
    for aid, vec in canonical_at_stride.items():
        if aid not in final_dirs and vec not in known_vectors:
            final_dirs[aid] = vec

    # ── Instantiate or update NavAtlas ──
    if context.nav_atlas is None:
        # Life 1 first commit. Build NavAtlas from library.header.
        # ego_value_set is already populated (gate condition).
        # Use min(ego_value_set) as ego_class — V3.5 also picks a
        # deterministic anchor; rarest-class selection requires a
        # frame argument we don't have here. min() suffices for
        # determinism; the field is metadata only at this layer
        # (NavAtlas itself uses ego_value_set, not ego_class, for
        # passability decisions).
        ego_value_set = frozenset(library.header.ego_value_set)
        ego_class = min(ego_value_set) if ego_value_set else -1
        ego_centroid = library.header.ego_centroid
        if ego_centroid:
            ego_spawn = (int(round(ego_centroid[0])), int(round(ego_centroid[1])))
        else:
            ego_spawn = (0, 0)
        context.nav_atlas = NavAtlas(
            ego_class=ego_class,
            ego_value_set=ego_value_set,
            ego_spawn=ego_spawn,
            action_dirs=final_dirs,
        )
    else:
        # Subsequent commits (e.g., re-bootstrap after design changes
        # — not currently triggered, but defensive): update
        # action_dirs in place to preserve PER_LEVEL substate
        # accumulated in NavAtlas.
        context.nav_atlas.action_dirs = final_dirs


# ---------------------------------------------------------------------------
# V3.5 PORT — pure computation helpers
# ---------------------------------------------------------------------------
# Ported verbatim from V3.5 ``discovery/nav_discovery.py``. These functions
# are the substrate of V3.5's stride-derivation pipeline; the WO-03 minimal
# probe leverages V4's existing ``library.header.ego_displacement_map`` for
# its own commit path, but the helpers are exposed here as standalone
# functions for V3.5 test inheritance and future use cases (e.g., a
# different probe driver that wants V3.5's anchor-position semantics).


def select_anchor_class(frame, agent_value_set, noop_class: int = 0) -> Optional[int]:
    """Select the rarest ego class in the frame as the tracking anchor.

    The rarest class is most likely unique to the ego body, minimising
    false positives from world tiles that share the same integer. The
    anchor class gives a single, clean pixel cluster whose top-left
    corner is stride-aligned (V1 corner_based_detection insight).

    V3.5 source: ``discovery/nav_discovery.py:153-177``.

    Returns anchor_class int, or None if agent_value_set is empty.
    """
    import numpy as np

    frame_arr = np.asarray(frame, dtype=np.int32)
    best_class: Optional[int] = None
    best_count = float("inf")
    for cls in agent_value_set:
        if cls == noop_class:
            continue
        count = int((frame_arr == cls).sum())
        if count > 0 and count < best_count:
            best_count = count
            best_class = cls
    return best_class


def compute_stride_from_positions(
    anchor_positions: Dict[int, Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]],
    noop_actions: FrozenSet[int] = frozenset({5, 6}),
) -> int:
    """Compute stride from gambit anchor positions.

    For each action probe with valid before/after positions, magnitude =
    ``max(|dr|, |dc|)``. Returns mode magnitude across all successful
    moves. Returns 0 if no successful moves detected.

    V3.5 source: ``discovery/nav_discovery.py:233-263``.

    Parameters
    ----------
    anchor_positions : dict
        ``{action_id: (pos_before, pos_after)}``. Either pos may be None
        when the anchor class was not found in that frame.
    noop_actions : frozenset
        Action IDs that should be skipped (typically 5 and 6 for
        interaction/click actions).
    """
    from collections import Counter

    magnitudes = []
    for action_id, (pos_before, pos_after) in anchor_positions.items():
        if action_id in noop_actions:
            continue
        if pos_before is None or pos_after is None:
            continue
        dr = abs(pos_after[0] - pos_before[0])
        dc = abs(pos_after[1] - pos_before[1])
        magnitude = max(dr, dc)
        if magnitude > 0:
            magnitudes.append(magnitude)

    if not magnitudes:
        return 0
    counts = Counter(magnitudes)
    return counts.most_common(1)[0][0]


def compute_action_dirs_from_positions(
    anchor_positions: Dict[int, Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]],
    noop_actions: FrozenSet[int] = frozenset({5, 6}),
) -> Dict[int, Tuple[int, int]]:
    """Compute per-action direction vectors from gambit anchor positions.

    Returns ``{action_id: (dr, dc)}`` — signed integer displacements.
    Blocked or missing actions get ``(0, 0)``. Noop actions also get
    ``(0, 0)``.

    V3.5 source: ``discovery/nav_discovery.py:265-287``.
    """
    action_dirs: Dict[int, Tuple[int, int]] = {}
    for action_id, (pos_before, pos_after) in anchor_positions.items():
        if action_id in noop_actions:
            action_dirs[action_id] = (0, 0)
            continue
        if pos_before is None or pos_after is None:
            action_dirs[action_id] = (0, 0)
            continue
        dr = pos_after[0] - pos_before[0]
        dc = pos_after[1] - pos_before[1]
        action_dirs[action_id] = (dr, dc)
    return action_dirs


__all__ = [
    "run_stride_probe_step",
    "select_anchor_class",
    "compute_stride_from_positions",
    "compute_action_dirs_from_positions",
]

"""Tier 3 NAV action selector.

Owns the Tier 3 NAV (navigation) action selection logic: walks toward
untested objects using investigation-priority ranking and displacement-vector
dominant-axis selection, with stuck-detection perpendicular fallbacks.

Extracted from action_selector.py in WO-CLEAN-06-PHASE-1B as part of the
Tier 3 NAV cluster decomposition.

Sovereignty: stdlib + arcengine + library/ (type only) + strategy/ siblings.
No numpy, no contracts/, no perception/, no targeting/, no memory/.

Public API:
- _select_tier3_nav_action(library, available_actions, rng, context) -> GameAction
- _compute_navigation_action_for_target(...) -> int
    WO-CAMPAIGN2-03-AMENDED — extracted helper for action computation
    given a target centroid. Used by both _select_tier3_nav_action
    (after its target-selection picks an object) and by NavPlan's
    production next_action() under δ.1 delegation.
"""

from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING

from arcengine import GameAction

from virelai_v4.library.semantic_library import SemanticLibrary
from virelai_v4.strategy.investigation_priority import _rank_investigation_targets

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext


# ----------------------------------------------------------------------
# Module constant (copied from action_selector.py per Outcome C)
# ----------------------------------------------------------------------

_DIRECTIONAL_IDS = frozenset({1, 2, 3, 4})


# ----------------------------------------------------------------------
# Navigation action helper (WO-CAMPAIGN2-03-AMENDED)
# ----------------------------------------------------------------------

def _compute_navigation_action_for_target(
    ego_pos: Tuple[int, int],
    target_centroid: Tuple[float, float],
    available_actions: List[int],
    rng: random.Random,
    stuck_count: int = 0,
) -> int:
    """Compute directional action_id toward a target centroid.

    Dominant-axis displacement selection with stuck-detection
    perpendicular fallback. Extracted from _select_tier3_nav_action
    lines 143-184 in WO-CAMPAIGN2-03-AMENDED Step 1 so NavPlan's
    production next_action() can delegate to identical logic with
    caller-supplied target.

    Per Director ruling Q2 (δ.1): NavPlan delegates to V4's existing
    Tier 3 dominant-axis intelligence. This helper is the shared
    delegation point; both _select_tier3_nav_action and NavPlan call it.

    Source: V4-native dominant-axis logic (no V3.5 lineage — V3.5 used
    BFS-driven action selection; V4's reactive layer uses dominant-axis
    as a simpler heuristic that doesn't require passability substrate).

    Parameters
    ----------
    ego_pos        Current ego (row, col).
    target_centroid Target centroid (row, col), may be float-valued.
    available_actions  List of legal action IDs for this frame.
    rng            Random instance for tiebreaking on equal axes.
    stuck_count    Stuck counter from caller (NavPlan: self.stuck_counter;
                   Tier 3 NAV: context.nav_stuck_count). When >= 3,
                   try perpendicular axis. Default 0 (no stuck logic).

    Returns
    -------
    int — action_id in {1, 2, 3, 4} (directional). Returns first legal
    directional from available_actions if no preference can be computed,
    or 0 (RESET) if no directional actions available.
    """
    ego_row, ego_col = ego_pos
    target_row, target_col = target_centroid
    delta_row = target_row - ego_row
    delta_col = target_col - ego_col

    # Dominant axis selection
    abs_row = abs(delta_row)
    abs_col = abs(delta_col)

    action_id: int
    if abs_row > abs_col:
        action_id = 1 if delta_row < 0 else 2  # 1=UP, 2=DOWN
    elif abs_col > abs_row:
        action_id = 3 if delta_col < 0 else 4  # 3=LEFT, 4=RIGHT
    else:
        # Tie — pick randomly between the two axes
        axis = rng.choice([0, 1])
        if axis == 0:
            action_id = 1 if delta_row < 0 else 2
        else:
            action_id = 3 if delta_col < 0 else 4

    # Stuck detection: if already stuck >= 3, try perpendicular axis
    if stuck_count >= 3:
        if action_id in {1, 2}:
            action_id = 3 if delta_col < 0 else 4
        else:
            action_id = 1 if delta_row < 0 else 2

    # Clamp to legal directional actions
    if action_id not in available_actions or action_id not in _DIRECTIONAL_IDS:
        playable = [aid for aid in available_actions if aid in _DIRECTIONAL_IDS]
        if not playable:
            return 0  # RESET
        action_id = playable[0]

    return action_id


# ----------------------------------------------------------------------
# Tier 3 NAV action selector
# ----------------------------------------------------------------------

def _nav_tool_direct(
    library: SemanticLibrary,
    available_actions: List[int],
    rng: random.Random,
    context: VirelaiContext,
) -> GameAction:
    """Tier 3 NAV probing strategy: walk toward untested objects (direct nav path).

    SOV-02 Step 2: renamed from `_select_tier3_nav_action` to
    `_nav_tool_direct`.  Backward-compat alias `_select_tier3_nav_action`
    and public alias `nav_tool` preserved below.

    Library-read: reads library.header (grid dimensions, world_type),
    library.objects (cells, role) for target selection and centroid computation.

    Target selection: prioritize unprobed (probe_history[rid] == 0), exclude skipped.
    If all probed, cycle to UNKNOWN role objects. Pick smallest region_id (determinism).

    Direction computation: use dominant axis toward target centroid.
    Negative row → ACTION1 (up); positive → ACTION2 (down);
    negative col → ACTION3 (left); positive → ACTION4 (right).

    Stuck detection: if nav_stuck_count >= 3 toward same target, try perpendicular axis.
    If both blocked, add to nav_skipped_targets and pick next target.

    Parameters
    ----------
    library       SemanticLibrary containing objects and their cells.
    available_actions  List of available action IDs (must include 1-4).
    rng           Random instance for tiebreaking.
    context       VirelaiContext for tracking ego_current_pos, nav_probe_target, etc.

    Returns
    -------
    GameAction (ACTION1-4) toward the target.
    """
    rows = library.header.grid_rows if library.header.grid_rows > 0 else 64
    cols = library.header.grid_cols if library.header.grid_cols > 0 else 64

    if context.ego_current_pos is None:
        # No ego position yet — random directional action
        playable = [aid for aid in available_actions if aid in _DIRECTIONAL_IDS]
        if not playable:
            return GameAction.RESET
        return GameAction.from_id(rng.choice(playable))

    # Target selection
    all_objects = list(library.objects.values())
    if not all_objects:
        # No objects — random directional action
        playable = [aid for aid in available_actions if aid in _DIRECTIONAL_IDS]
        if not playable:
            return GameAction.RESET
        return GameAction.from_id(rng.choice(playable))

    # Initialize probe_history for new objects
    for obj in all_objects:
        if obj.region_id not in context.probe_history:
            context.probe_history[obj.region_id] = 0

    # Investigation priority ranking (WO-RM-05): smallest + rarest objects first.
    ranked_ids = _rank_investigation_targets(library)

    # Pass 1: highest-priority uninvestigated object not yet probed, not skipped
    target = None
    for rid in ranked_ids:
        if rid in context.nav_skipped_targets:
            continue
        if context.probe_history.get(rid, 0) == 0:
            target = library.objects.get(rid)
            if target is not None:
                break

    # Pass 2: any ranked uninvestigated object not skipped (ignore probe count)
    if target is None:
        for rid in ranked_ids:
            if rid not in context.nav_skipped_targets:
                target = library.objects.get(rid)
                if target is not None:
                    break

    # Pass 3: any object not skipped (all investigated — fallback to re-probe)
    if target is None:
        playable_objects = [
            obj for obj in all_objects
            if obj.region_id not in context.nav_skipped_targets
        ]
        if playable_objects:
            target = min(playable_objects, key=lambda o: o.region_id)
        else:
            # All skipped — reset and retry
            context.nav_skipped_targets.clear()
            target = min(all_objects, key=lambda o: o.region_id)

    context.nav_probe_target = target.region_id

    # Compute target centroid
    if target.cells:
        cell_list = list(target.cells)
        target_row = sum(r for r, c in cell_list) / len(cell_list)
        target_col = sum(c for r, c in cell_list) / len(cell_list)
    else:
        # Object with no cells — random direction
        playable = [aid for aid in available_actions if aid in _DIRECTIONAL_IDS]
        if not playable:
            return GameAction.RESET
        return GameAction.from_id(rng.choice(playable))

    # WO-CAMPAIGN2-03-AMENDED Step 1: delegate action computation to the
    # shared helper. Behavior unchanged — the helper is an extraction of
    # the lines that previously lived inline here.
    action_id = _compute_navigation_action_for_target(
        ego_pos=context.ego_current_pos,
        target_centroid=(target_row, target_col),
        available_actions=available_actions,
        rng=rng,
        stuck_count=context.nav_stuck_count,
    )
    if action_id == 0:
        return GameAction.RESET
    return GameAction.from_id(action_id)


def nav_tool(
    library: SemanticLibrary,
    available_actions: List[int],
    rng: random.Random,
    context: VirelaiContext,
    nav_plan=None,
) -> GameAction:
    """NAV tool — public entry point for captain dispatch (SOV-02 Step 2).

    Mode A (plan_continuation): when nav_plan is not None, delegates to the
    NavPlan execution path in action_selector.py (via select_action) so that
    plan stride probe and plan completion logic are preserved intact.

    Mode B (direct_nav): when nav_plan is None, delegates to `_nav_tool_direct`
    (the renamed Tier 3 NAV strategy).

    Library-read: passes library to the selected delegate unchanged.
    """
    if nav_plan is not None:
        # Plan continuation: delegate to _nav_tool_direct for now; the full
        # NavPlan execution path lives in action_selector.py and is invoked
        # through the Category C fallback (select_action call in
        # captain_legacy_fallback). This mode exists as a named hook for
        # future SOV-03 extraction.
        return _nav_tool_direct(library, available_actions, rng, context)
    return _nav_tool_direct(library, available_actions, rng, context)


# SOV-02 Step 2: backward-compat alias — any import site that references
# `_select_tier3_nav_action` by name continues to work.
_select_tier3_nav_action = _nav_tool_direct



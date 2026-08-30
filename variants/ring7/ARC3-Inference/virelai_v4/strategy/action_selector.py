"""
virelai_v4/strategy/action_selector.py — Directive-driven action selection.

Reads the RoutingDirective and SemanticLibrary to select the single best
action for the current frame. The library is read-only here — this function
picks actions; it does not interpret their results.

Import sovereignty: contracts/, library/, arcengine, stdlib only.
No imports from targeting/, perception/, or memory/.
The RoutingDirective is received as a parameter, not imported from targeting/.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING  # Tuple: WO-03-AMENDED _select_navigation_target return type

logger = logging.getLogger(__name__)

from arcengine import GameAction

from virelai_v4.contracts.routing_directive import RoutingDirective
from virelai_v4.library.semantic_library import SemanticLibrary
from virelai_v4.strategy.investigation_priority import (
    _is_uninvestigated,
    _rank_investigation_targets,  # used by _select_navigation_target (WO-03-AMENDED)
    investigation_coverage_complete,  # WO-OCD-06 — Tier 4 enforcement gate
    rank_unattributed_objects,
)
from virelai_v4.strategy.tier3_nav import _select_tier3_nav_action
from virelai_v4.strategy.tier4_click import _select_tier4_click_action

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RESET_ID = 0
# ACTION1-4 are the fastest discriminator between NAV (embodied, reacts to
# directional movement) and CLICK (no ego, ignores directional input).
_DIRECTIONAL_IDS = frozenset({1, 2, 3, 4})



# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def tier1_probe_tool(
    library: SemanticLibrary,
    available_actions: List[int],
    rng: random.Random,
) -> GameAction:
    """Tier 1 probe strategy: exhaust each available channel before repeating.

    SOV-02 Step 2: renamed from `_select_tier1_action` to `tier1_probe_tool`.
    Backward-compat alias preserved below.

    Library-read: reads library.sdk_actions (action status and test_count),
    library.header (grid_rows, grid_cols for complex action coordinate bounds).

    Priority order:
      1. UNTESTED directional actions (ACTION1-4) — fastest NAV/CLICK discriminator
      2. UNTESTED interaction actions (ACTION5, ACTION6) and any unknown actions
      3. All tested: pick the action with fewest test_count, tiebreak randomly

    RESET (id=0) is never selected — lifecycle action, not a probe.
    """
    candidates = [aid for aid in available_actions if aid != _RESET_ID]
    if not candidates:
        return GameAction.RESET

    sdk = library.sdk_actions
    rows = library.header.grid_rows if library.header.grid_rows > 0 else 64
    cols = library.header.grid_cols if library.header.grid_cols > 0 else 64

    def _is_untested(aid: int) -> bool:
        entry = sdk.get(aid)
        return entry is None or entry.status == "UNTESTED"

    def _test_count(aid: int) -> int:
        entry = sdk.get(aid)
        return entry.test_count if entry is not None else 0

    untested = [aid for aid in candidates if _is_untested(aid)]

    if untested:
        directional_untested = [aid for aid in untested if aid in _DIRECTIONAL_IDS]
        chosen_id = rng.choice(directional_untested if directional_untested else untested)
    else:
        # All channels tested at least once — balance evidence across all
        min_count = min(_test_count(aid) for aid in candidates)
        pool = [aid for aid in candidates if _test_count(aid) == min_count]
        chosen_id = rng.choice(pool)

    action = GameAction.from_id(chosen_id)
    if action.is_complex():
        action.set_data({"x": rng.randint(0, cols - 1), "y": rng.randint(0, rows - 1)})
    return action


def random_probe_tool(
    available_actions: List[int],
    rng: random.Random,
    grid_rows: int = 64,
    grid_cols: int = 64,
) -> GameAction:
    """Random legal action selection. RESET (id=0) excluded.

    SOV-02 Step 2: renamed from `_random_action` to `random_probe_tool`.
    Backward-compat alias preserved below.

    Library-read: no library argument; uses grid_rows/grid_cols passed from
    caller (library.header values). Used as fallback for non-Tier-1
    directives, None directive, and when the library is not yet initialised.
    """
    playable = [aid for aid in available_actions if aid != _RESET_ID]
    if not playable:
        return GameAction.RESET
    action = GameAction.from_id(rng.choice(playable))
    if action.is_complex():
        action.set_data({"x": rng.randint(0, grid_cols - 1), "y": rng.randint(0, grid_rows - 1)})
    return action


# SOV-02 Step 2: backward-compat aliases — any callers that use the old
# private names continue to work without changes.
_select_tier1_action = tier1_probe_tool
_random_action = random_probe_tool


def _select_navigation_target(
    context: VirelaiContext,
    library: SemanticLibrary,
) -> Optional[Tuple[int, int]]:
    """Pick a target coordinate for NavPlan construction (WO-03-AMENDED).

    Uses the same investigation-priority ranking that Tier 3 NAV uses
    internally — picks the highest-priority unprobed unskipped object
    and returns its centroid as the target coordinate.

    Returns None if no candidate available (no objects, ego not
    localized, all candidates skipped). Callers handle None by
    skipping plan construction and falling through to reactive.

    NOTE: this duplicates the target-selection portion of
    `_select_tier3_nav_action` (lines 90-129 of strategy/tier3_nav.py).
    Acknowledged technical debt under WO-03-AMENDED Q2 ruling (no
    speculative scaffolding); future cleanup may extract a shared
    target-selection helper when a second consumer surfaces.
    """
    if context.ego_current_pos is None:
        return None  # ego not yet localized
    all_objects = list(library.objects.values())
    if not all_objects:
        return None
    # Initialize probe_history for new objects (mirrors Tier 3 NAV)
    for obj in all_objects:
        if obj.region_id not in context.probe_history:
            context.probe_history[obj.region_id] = 0
    ranked_ids = _rank_investigation_targets(library)
    for rid in ranked_ids:
        if rid in context.nav_skipped_targets:
            continue
        if context.probe_history.get(rid, 0) == 0:
            target = library.objects.get(rid)
            if target is not None and target.cells:
                cell_list = list(target.cells)
                row = sum(r for r, _ in cell_list) / len(cell_list)
                col = sum(c for _, c in cell_list) / len(cell_list)
                return (round(row), round(col))
    return None


# ---------------------------------------------------------------------------
# Cycle probe + dispatch routing helpers (WO-CAMPAIGN3-PHASE3-02-RESUMPTION
# Step 1; corrective extraction May 5, 2026 per Constitution §3 Interleaving
# Ban compliance). Single-call helpers invoked from select_action keep the
# caller's body length under Yellow ceiling and preserve "function calls
# between existing lines" composition per the constitution's Permitted rule.
# ---------------------------------------------------------------------------


def _maybe_run_cycle_probe_section(
    library: Optional[SemanticLibrary],
    context: Optional[VirelaiContext],
    available_actions: List[int],
) -> Optional[GameAction]:
    """Pre-Tier cycle probe section for select_action (cycle_probe_tool Mode B).

    SOV-02 Step 2: this function is NOT renamed (AST-pinned by two tests in
    test_cycle_probe_invocation.py that verify its name and position in
    select_action's AST).  It serves as cycle_probe_tool's Mode B
    (legacy_coverage path) — called from select_action's pre-Tier block.

    Library-read: reads library.header.world_type to gate NAV/CLICK worlds;
    reads library.objects to find confirmed levers for cycle probe
    initialization; reads object.classification and cycle_length for
    probe-state decisions.

    Per WO-PHASE3-02-RESUMPTION Step 0 Recommendation 1: cycle probe
    integrates in the Decide phase (select_action), not the Update phase
    (choose_action). Per Recommendation 2: pre-Tier placement spans CLICK +
    NAV worlds. Per Recommendation 3: ``latest_frame`` resolves via
    ``context.prev_grid`` (post-_perceive value = current observed frame;
    soft halt verification at Step 1 confirmed prev_grid lifecycle precedes
    select_action invocation).

    Returns
    -------
    Optional[GameAction]
        GameAction to emit (probe in progress) or None (no active probe,
        no unprobed lever to initialize, or probe completed this frame
        with verdict written + state cleared; caller falls through).
    """
    if (library is None or context is None
            or library.header.world_type not in ("NAV", "CLICK")
            or context.prev_grid is None):
        return None

    # WO-SOV-03 Category B (site 1): captain_is_active retired.
    # Under single-actor architecture the captain owns all cycle probe
    # dispatch via DISPATCH_TABLE (_cycle_probe_mode_a). This legacy
    # bypass is unconditionally dead — always skip. The conditional
    # gate that previously protected against double-firing is no longer
    # needed; the structural guarantee is provided by the single-actor
    # entrypoint in virelai.py choose_action.
    return None
def _maybe_compute_dispatch_routes(
    library: Optional[SemanticLibrary],
) -> None:
    """Compute per-lever dispatch routes for diagnostic + Phase 4 substrate.

    Per WO-PHASE3-02-RESUMPTION Step 0 Hypothesis B (CONFIRMED): Phase 3
    dispatch scope is "compute routes; act on routes V4 has substrate for;
    defer Gray code / depth sequence to Phase 4 Combination Search" per
    Campaign 3 north star. The dispatch call here computes routes; per-
    mechanism action emission (Gray code / depth sequence) is Phase 4
    territory. SATURATED routes to SKIP_LEVER per Hybrid (Step 0
    sub-deliverable 1B) — currently observability-only at Phase 3.
    """
    if library is None:
        return

    from virelai_v4.library.lever_dispatch import LeverDispatch
    from virelai_v4.library.semantic_library import LibraryRole

    lever_objects = [
        obj for obj in library.objects.values()
        if obj.role == LibraryRole.LEVER
    ]
    if not lever_objects:
        return

    dispatch = LeverDispatch()
    routes = [(obj.region_id, dispatch.route_lever(obj)) for obj in lever_objects]
    if routes:
        logger.debug(
            "[CYCLE-PROBE-DISPATCH] routes computed: %s "
            "(per-mechanism action emission = Phase 4)",
            routes,
        )


def select_action(
    directive: Optional[RoutingDirective],
    library: Optional[SemanticLibrary],
    available_actions: List[int],
    rng: random.Random,
    probe_history: Optional[dict] = None,
    context: Optional[VirelaiContext] = None,
) -> GameAction:
    """Select the next action from the routing directive and library state.

    DISPATCH LAYER (WO-CAMPAIGN2-02)

    Plan-driven dispatch runs first. If a plan is active on
    ``context.current_plan``, the plan emits the next action; the cursor
    advances; the plan is torn down when ``is_complete()`` returns True
    (Strategize then falls through to reactive mode on the same frame).

    Reactive dispatch (Tier 4 → Tier 3 CLICK → Tier 3 NAV → Tier 1 →
    fallback random) runs unchanged when ``current_plan`` is None.

    Source: V3.5 spine/handlers/execution.py dispatch principle (per-life
    routing by hypothesis_type + world_type). V4 makes the dispatch
    explicit per-frame because the stepwise architecture requires it.
    See WO-CAMPAIGN2-02 inheritance declaration for principle-port-not-
    symbol-port framing.

    Parameters
    ----------
    directive         Current RoutingDirective from targeting (read-only).
                      Received as parameter — not imported from targeting/.
    library           Current SemanticLibrary state (read-only).
    available_actions Raw integer list from FrameData.available_actions.
    rng               Agent's seeded Random instance for deterministic tiebreaking.
    probe_history     Dict[int, int] for Tier 3 CLICK worlds (region_id → probe_count).
                      Mutated in place, persists across lives (Groundhog Day).
    context           VirelaiContext for setting last_probe_target (Tier 3 only)
                      AND for plan dispatch (current_plan field).

    Returns
    -------
    GameAction ready to submit. For ACTION6, coordinates are set via set_data().
    """
    # ---- Plan-driven dispatch (WO-CAMPAIGN2-02 + WO-03-AMENDED) ----
    # If a plan is active and incomplete, observe prior step outcome at
    # start of tick (WO-03-AMENDED correction from WO-02 provisional
    # post-emission advancement), then emit the plan's next action.
    # If complete, tear down (current_plan = None) and fall through to
    # reactive dispatch on the same frame.
    if context is not None and context.current_plan is not None:
        plan = context.current_plan

        # Start-of-tick observation gating (WO-03-AMENDED Step 3).
        # Under δ.1's lazy population, cursor == len(actions); the
        # prior emission's expected position is at expected_positions[-1].
        # Compare actual ego position (read from context) to the
        # expected. If matched, check for target-reach; if mismatched,
        # call handle_unmoved_ego (which may set aborted=True).
        from virelai_v4.library.plan import NavPlan as _NavPlan
        if isinstance(plan, _NavPlan) and plan.expected_positions:
            actual = context.ego_current_pos
            expected = plan.expected_positions[-1]
            if actual is not None and actual != expected:
                # Surprise — ego didn't move as expected
                plan.handle_unmoved_ego(context)
            elif actual is not None and actual == plan.target:
                # Target reached — completion
                plan.completed = True

        if plan.is_complete():
            # Tear down the completed (or aborted) plan; fall through
            # to reactive below on the same frame.
            context.current_plan = None
        else:
            # Lazy emission: next_action appends to actions and
            # expected_positions, then returns the GameAction.
            return plan.next_action(context, library, available_actions, rng)

    # ---- Cycle probe pre-Tier check (WO-CAMPAIGN3-PHASE3-02-RESUMPTION) ----
    # Constitution §3 (Interleaving Ban) compliance: section extracted to
    # _maybe_run_cycle_probe_section helper; called as a single function
    # call between two existing lines per spec ("Permitted: adding a new
    # function call between two existing lines").
    #
    # WO-OCD-06 Tier Enforcement Gate: cycle probe is Tier 5 work. It fires
    # only when Tier 4 closes through exhaustive investigation per Object
    # Investigation Doctrine Principle 1. Before this gate landed, the bypass
    # fired whenever any LEVER had lever_mechanism is None — producing the
    # greediness problem documented in WO-OCD-00 Q4.4. The new outer predicate
    # withholds the bypass until investigation_coverage_complete returns True.
    if investigation_coverage_complete(library):
        cycle_probe_action = _maybe_run_cycle_probe_section(
            library, context, available_actions,
        )
        if cycle_probe_action is not None:
            # WO-OCD-CHOKE-POINT (Step 4) — provenance tag for cycle-probe
            # emissions. The cycle probe sets last_probe_target_region_id
            # in cycle_probe._activate_click_step (WO Step 5); this tag
            # routes the choke-point sidecar entry under emitter="cycle_probe".
            if context is not None and cycle_probe_action.value == 6:
                context.last_emitter_path = "cycle_probe"
            return cycle_probe_action

    # ---- Dispatch routing call (WO-CAMPAIGN3-PHASE3-02-RESUMPTION 1A) ----
    # AST contract pin invariant: dispatch routing follows cycle probe
    # section in source order; gated on LEVER objects existing.
    # Constitution §3 (Interleaving Ban) compliance: section extracted to
    # _maybe_compute_dispatch_routes helper; single function call.
    _maybe_compute_dispatch_routes(library)

    if probe_history is None:
        probe_history = {}

    # WO-FM11-FIX: world-discrimination relocated to the Router/Registry.
    # The selector consults the Registry verdict for this frame; `world_type`
    # is read ONLY inside resolve_dispatch_primitive (the sole world-
    # discrimination locus per Law 5 / FM-11), never branched on here. The
    # selector acts on the two primitive verdicts the legacy world-keyed
    # branches dispatched (TIER4_CLICK, TIER3_NAV); every other verdict
    # (captain-owned cells, typed gaps, None) falls through unchanged.
    from virelai_v4.targeting.dispatch_registry import (
        PrimitiveId,
        resolve_dispatch_primitive,
    )
    _dispatch = resolve_dispatch_primitive(directive, library)

    # Tier 4 CLICK: Unattributed-object probe strategy (was `tier == 4 and
    # world_type == "CLICK"`; the Registry maps (CLICK, tier-4 attribute) →
    # TIER4_CLICK). DEBT-LC-03: Two rankers coexist — Tier 3 uses
    # _rank_investigation_targets (uninvestigated); Tier 4 uses
    # rank_unattributed_objects (unattributed, REACTIVE-boosted). No merger
    # in WO-02. Remediation deferred.
    if _dispatch is PrimitiveId.TIER4_CLICK:
        if context is not None:
            return _select_tier4_click_action(library, context)
        # context required for Tier 4 to record probe target; fall through to random
        logger.warning("[TIER4-CLICK] context is None — cannot record probe target; falling back")

    # Tier 3 CLICK: removed (WO-FM11-FIX). The SOV-03 tombstone (`if False`)
    # is retired. (CLICK, tier-3 attribute) is a captain-owned cell in the
    # Registry (FIRST_TOUCH_CLICK), so the selector falls through here exactly
    # as the dead tombstone did — behavior preserved.

    # Tier 3 NAV: Directional navigation toward target objects (WO-03)
    # WO-CAMPAIGN2-03-AMENDED Step 4: construction site wiring under
    # δ.1. On the first NAV frame of each life (when nav_probe_target
    # is still None — it gets set by Tier 3 NAV after first call;
    # PER_LIFE_SCRATCHPAD resets at life advance), construct a NavPlan
    # toward the highest-priority investigation target. The plan
    # delegates to the same Tier 3 NAV intelligence via
    # _compute_navigation_action_for_target. Once-per-life construction
    # guarantees PLAN STATUS appears in at least one ls20 field card —
    # the WO-03-AMENDED proving criterion.
    if _dispatch is PrimitiveId.TIER3_NAV:
        # COLLIDE-WITH-EVERYTHING rung 2 (env-gated, additive, zero default-path
        # risk). When VIRELAI_COLLIDE_SWEEP is set and the ego is confirmed, drive
        # the systematic object-by-object collide sweep — the embodied-ego analog
        # of click-with-everything, a live replay-gradeable coverage run. Falls
        # through to the committed nav path when the flag is off, no ego, or the
        # sweep returns None (complete). Writes no belief.
        if os.environ.get("VIRELAI_COLLIDE_SWEEP") and context is not None:
            from virelai_v4.strategy.collide_sweep import (
                collide_sweep_action, _log as _cs_log,
            )
            _hdr = library.header
            _ego_ok = getattr(_hdr, "ego_confirmed", False)
            # Self-explaining gate: log WHY the sweep does or does not fire, so a
            # canary never goes silently inert again. Only reached once dispatch
            # resolves to TIER3_NAV — its ABSENCE from the log means the run never
            # left world-type/stride bootstrap (too short / still UNKNOWN).
            _cs_log(context, "COLLIDE-SWEEP | gate @TIER3_NAV: world_type="
                    f"{getattr(_hdr, 'world_type', '?')} ego_confirmed={_ego_ok} "
                    f"stride_complete={getattr(context, 'stride_probe_complete', '?')}")
            if _ego_ok:
                _cs = collide_sweep_action(library, available_actions, rng, context)
                if _cs is not None:
                    return _cs
                _cs_log(context, "COLLIDE-SWEEP | gate open, driver returned None "
                        "(sweep complete / no directional)")
        # WO-CAMPAIGN3-PHASE1-03: stride probe substrate bootstrap.
        # Drives cardinals one per Life 1 frame to populate
        # nav_atlas.action_dirs from observed ego displacement.
        # Falls through immediately when stride_probe_complete=True
        # (Life 2+ or after first-life probe completion).
        if (context is not None
                and library.header.ego_confirmed
                and not context.stride_probe_complete):
            from virelai_v4.library.stride_probe import run_stride_probe_step
            probe_action = run_stride_probe_step(
                context=context,
                library=library,
                available_actions=available_actions,
            )
            if probe_action is not None:
                return probe_action
            # probe_action is None → probe completed this frame; fall
            # through to existing Tier 3 NAV / NavPlan dispatch with a
            # bootstrapped nav_atlas.
        # WO-CAMPAIGN3-PHASE1-05: substrate-ready gating for NavPlan
        # construction. NavPlan now reads BFS paths from nav_atlas via
        # library.nav_path_computation.compute_path; construction is
        # gated on nav_atlas being instantiated AND the stride probe
        # having committed action_dirs. If either is False, fall through
        # to reactive Tier 3 NAV (which doesn't require substrate).
        if (context is not None
                and context.current_plan is None
                and context.nav_probe_target is None
                and context.nav_atlas is not None
                and context.stride_probe_complete):
            target_coord = _select_navigation_target(context, library)
            if target_coord is not None:
                from virelai_v4.library.plan_construction import construct_nav_plan
                context.current_plan = construct_nav_plan(
                    ctx=context,
                    target=target_coord,
                    source_hypothesis_id="reactive_exhaustion",
                )
                # Dispatch the just-constructed plan immediately on
                # this same frame. The plan emits via its lazy
                # delegation to the Tier 3 NAV helper.
                plan = context.current_plan
                if not plan.is_complete():
                    return plan.next_action(
                        context, library, available_actions, rng,
                    )
                else:
                    # Defense-in-depth: empty-target case shouldn't
                    # land here under δ.1 (NavPlan starts with
                    # aborted=False, completed=False), but if it does,
                    # tear down cleanly.
                    context.current_plan = None
        return _select_tier3_nav_action(library, available_actions, rng, context)

    # WO-SOV-03 Category C: select_action_gated_by_captain deleted.
    # The gate was vacuous under single-actor architecture:
    # (a) when captain dispatched directly via DISPATCH_TABLE, select_action
    #     was never reached; (b) when captain fell to legacy, captain_is_active
    #     was False (walk produced no target), so the gate never fired.
    # Verified by Case 5 of TestCaptainIsActiveRoutingPredicate.

    # Tier 1: Exhaustive channel probing
    if library is not None and directive is not None and directive.tier == 1:
        tier1_action = _select_tier1_action(library, available_actions, rng)
        # WO-OCD-CHOKE-POINT (Step 4) — provenance tag. Tier 1 only triggers
        # the choke-point write when it happens to draw ACTION6 from the
        # available pool; the conditional avoids tagging non-CLICK emissions.
        if context is not None and tier1_action.value == 6:
            context.last_emitter_path = "tier1"
        return tier1_action

    # WO-FM11-FIX-B: typed-gap action (Apex Ruling B, behavioral leg). Any
    # non-None Registry verdict not dispatched above — a TypedGap (no primitive
    # built; owned by WO-PRIMITIVES), or a captain-owned PrimitiveId that reached
    # the legacy selector because the Form B walk yielded nothing this frame —
    # emits a DETERMINISTIC, logged gap action instead of falling silently to
    # random. This closes Ruling B at the emitted-action layer (FM11-FIX-A
    # closed it only at Registry resolution).
    if _dispatch is not None:
        return _select_typed_gap_action(
            _dispatch, library, available_actions, context,
        )

    # Fallback: degenerate no-key path ONLY — `_dispatch is None`, i.e. no
    # directive or no library. random_probe is no longer reachable on any
    # substantive resolved frame (Ruling B).
    rows = library.header.grid_rows if library is not None and library.header.grid_rows > 0 else 64
    cols = library.header.grid_cols if library is not None and library.header.grid_cols > 0 else 64
    fallback_action = _random_action(available_actions, rng, grid_rows=rows, grid_cols=cols)
    # WO_PUSH_SILENCE_LABEL_COVERAGE: stamp the silence label on EVERY random
    # fallback, not only clicks (was value==6-gated — mute on directional).
    from virelai_v4.strategy.typed_gap_action import stamp_silence_emitter
    stamp_silence_emitter(context, "random_fallback")
    return fallback_action


def _select_typed_gap_action(
    dispatch: object,
    library: Optional[SemanticLibrary],
    available_actions: List[int],
    context: Optional[VirelaiContext],
) -> GameAction:
    """Build the deterministic typed-gap action (WO-FM11-FIX-B).

    The pure selection logic (deterministic, frame-keyed, no rng, no state) lives
    in `strategy.typed_gap_action` and is sandbox-tested; this wrapper builds the
    GameAction and emits the audit notice. SR boundary: this is a placeholder —
    no classification write, no probe strategy; WO-PRIMITIVES replaces the cell
    with a real primitive. FM-10: no new state.
    """
    from virelai_v4.strategy.typed_gap_action import (
        emit_typed_gap_warning,
        gap_click_coords_lever_anchored,
        select_anchored_lever,
        select_typed_gap_action_id,
        stamp_silence_emitter,
    )

    frame = context.prev_grid if context is not None else None
    action_id = select_typed_gap_action_id(available_actions, frame)

    world_type = library.header.world_type if library is not None else "UNKNOWN"
    attr_name = getattr(getattr(dispatch, "attribute_type", None), "name", None)
    if attr_name is None:  # captain-owned PrimitiveId reaching the selector
        attr_name = getattr(dispatch, "name", str(dispatch))
    # WO-LOGGING-CARDINALITY: first-occurrence-per-(world,probe) + silent tally,
    # replacing the per-action flood; quiet routes to DEBUG (F-2).
    emit_typed_gap_warning(world_type, attr_name)

    action = GameAction.from_id(action_id)
    if action_id == 6:
        rows = library.header.grid_rows if library is not None and library.header.grid_rows > 0 else 64
        cols = library.header.grid_cols if library is not None and library.header.grid_cols > 0 else 64
        # WO-FALLBACK-LEVER-ROTATION: anchor the post-walk fallback click to a
        # TYPED lever (hash-indexed) when typed levers exist; falls through to
        # the board-hash gap_click_coords when none. Read-only over library.
        x, y = gap_click_coords_lever_anchored(frame, library, rows, cols)
        action.set_data({"x": x, "y": y})
        # WO-FALLBACK-LEVER-ATTRIBUTION: when the fallback presses a TYPED
        # lever, claim it so the substrate (run_physics_measurement, read at
        # library_sync.py:361) attributes the press and writes
        # observation_status / causal_observation_count for that lever. This
        # mirrors the captain's region_id-set at dispatch (captain.py:580 — the
        # REAL attribution mechanism; the live tier4_click primitive sets no
        # metadata). select_anchored_lever is the same selection source the coord
        # used, so coord and attribution cannot diverge. The board-hash
        # fall-through (no typed lever) claims nothing — leaving the prior
        # untargeted behavior intact.
        if context is not None:
            selected = select_anchored_lever(frame, library)
            if selected is not None:
                context.last_probe_target_region_id = selected[0]
                context.last_probe_target_cells = selected[1]
                context.last_probe_action_kind = "CLICK"
    # WO_PUSH_SILENCE_LABEL_COVERAGE: stamp the silence label on EVERY typed-gap
    # emission, not only clicks — a mute directional emitter left the Push blind.
    stamp_silence_emitter(context, "typed_gap")
    return action

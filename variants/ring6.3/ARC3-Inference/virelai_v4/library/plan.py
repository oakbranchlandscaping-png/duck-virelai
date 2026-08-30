"""
virelai_v4/library/plan.py — Plan substrate for V4 execution (WO-CAMPAIGN2-01).

Plans represent multi-step intentions held across choose_action calls.
A plan lives on VirelaiContext.current_plan; the Strategize step reads
the plan, emits its next action, and advances the cursor.

Three plan types share PlanBase:
  - NavPlan         BFS-driven embodied navigation (NAV worlds)
  - CycleProbePlan  per-lever measurement (cycle characterization +
                    target-state-driven characterization, parameterized)
  - TraversalPlan   combinatorial enumeration (FINITE_SEARCH worlds,
                    gray-code traversal with per-lever recovery)

INHERITANCE BASELINE

WO-CAMPAIGN2-00.5-SYNTHESIS-UPDATE.md (RATIFIED April 28, 2026), refined
by WO-CAMPAIGN2-01-STEP-0-AUDIT.md (April 29, 2026). PORT-WITH-MODIFICATIONS
verdict for all three dataclasses: V3.5's implicit stack-local plan state
becomes V4's explicit dataclass fields. Field defaults come from V3.5
source where verified; V4 contributions (cursor, expected_positions,
source_hypothesis_id, compiled_at_step, state_history hash augmentation)
are documented as such per field.

V3.5 source citations:
  - NavPlan fields:        Universal_Solver_v3_5/execution/nav_executor.py
                           lines 239 (_bfs_path), 251 (_consec_blocked),
                           252 (_current_nav_target)
  - NavPlan stuck:         Universal_Solver_v3_5/execution/nav_executor.py
                           line 250 (_UNREACHABLE_THRESH = 5)
  - CycleProbePlan max:    Universal_Solver_v3_5/discovery/physics/
                           cycle_probe.py line 172 (depth = 4)
  - CycleProbePlan sat:    Universal_Solver_v3_5/discovery/physics/
                           cycle_probe.py lines 247-258 (immediate
                           frame-equality, threshold 1)
  - TraversalPlan torque:  Universal_Solver_v3_5/execution/click_traversal.py
                           line 21 (_TORQUE_THRESHOLD = 3)

PERSISTENCE

All plan instances live on VirelaiContext.current_plan, classified
PER_LIFE_SCRATCHPAD. Plans do not survive Groundhog Day. Library
knowledge that informed the plan persists under its own tier
annotations. Life N+1 reconstructs plans from updated state.

WHAT THIS FILE SHIPS

Dataclass definitions, abstract method declarations, surprise method
shells. NO execution logic — concrete next_action() implementations
and surprise method bodies are deferred to WO-02 (Strategize integration)
and WO-03 (NAV execution port).
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

if TYPE_CHECKING:
    # GameAction lives in arcengine; imported under TYPE_CHECKING so this
    # module remains importable in environments without the arcengine wheel
    # (Cowork sandbox runs Python 3.10; arcengine requires Python 3.12+).
    # See WO-PHASE4-03.1 — primitive-level inheritance to avoid orchestration
    # imports.
    from arcengine import GameAction
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import SemanticLibrary


# ---------------------------------------------------------------------------
# PlanBase — shared interface for all plan dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PlanBase(ABC):
    """Shared interface for all plan dataclasses.

    Persistence: PER_LIFE_SCRATCHPAD (registered in
    VirelaiContext._PERSISTENCE_TIERS via the `current_plan` field).
    Plans do not survive Groundhog Day. Life N+1 reconstructs plans
    from updated library state.

    Lifecycle:
        1. Strategize step constructs a plan when library state justifies
           a multi-step intention (e.g., a NavPlan when the library
           identifies a probe target the ego must reach).
        2. The plan persists on VirelaiContext.current_plan across
           choose_action calls.
        3. Each call: Strategize checks is_complete(); if False, calls
           next_action() to emit the action; advances cursor after
           observation confirms the action's outcome.
        4. Plan completes when is_complete() returns True. Strategize
           tears down the plan and either constructs a new plan or
           returns to reactive mode.

    V3.5 lineage: V3.5 monolithic loops (run_nav_execution, probe_lever_cycle,
    _execute_lever_traversal) carried this state implicitly on the stack.
    V4's stepwise interface forces explicit storage. The dataclass IS the
    explicit storage.
    """

    source_hypothesis_id: str
    """The hypothesis or library target this plan serves. Traceability —
    enables post-hoc analysis of which plans were constructed from which
    library states. V4 contribution; not in V3.5.
    """

    compiled_at_step: int
    """Step count when the plan was constructed. Useful for stale-plan
    detection (e.g., a plan constructed 50 steps ago against a
    now-stale ego_centroid). V4 contribution; not in V3.5.
    """

    cursor: int = 0
    """Current position in the plan's sequence. Advances after each
    successful step. V4 contribution — V3.5 used implicit pop-from-front
    (`_bfs_path.pop(0)` at nav_executor.py:413). V4 makes the cursor
    explicit for debuggability and clearer test assertions.
    """

    @abstractmethod
    def is_complete(self) -> bool:
        """Return True if the plan has finished, successfully or by abort.

        Strategize checks this each frame; True triggers plan teardown
        and either new-plan construction or return-to-reactive mode.

        Concrete implementation lives on each subclass — the completion
        criterion differs by plan type (NavPlan: cursor end OR aborted;
        CycleProbePlan and TraversalPlan: completed_with_verdict is
        not None).
        """
        ...

    @abstractmethod
    def next_action(
        self,
        context: "VirelaiContext",
        library: "SemanticLibrary",
        available_actions: List[int],
        rng: random.Random,
    ) -> "GameAction":
        """Return the action to emit on the current frame.

        Called by Strategize after verifying is_complete() returns False.

        WO-CAMPAIGN2-03-AMENDED signature update: production NavPlan
        delegation requires access to context (for ego position),
        library (for object lookups during target re-resolution if
        ever needed), available_actions (for legal-action clamping),
        and rng (for tiebreaking). WO-01's argumentless signature was
        a placeholder; production needs these inputs. CycleProbePlan
        and TraversalPlan accept the same signature for protocol
        consistency though they do not yet use the args (Campaign 3
        production logic).
        """
        ...


# ---------------------------------------------------------------------------
# NavPlan — BFS-driven embodied navigation
# ---------------------------------------------------------------------------

@dataclass
class NavPlan(PlanBase):
    """BFS-driven embodied navigation plan for NAV worlds.

    Created when the library decides the ego needs to move to a specific
    coordinate (lever candidate, probe target, unexplored region). Holds
    the precomputed BFS path and walks it one step per frame.

    SOURCE LINEAGE

    V3.5 run_nav_execution() at execution/nav_executor.py carries this
    state in stack-local variables:

      - V3.5 _bfs_path (line 239)            ↔  V4 NavPlan.actions
      - V3.5 _consec_blocked (line 251)      ↔  V4 NavPlan.stuck_counter
      - V3.5 _current_nav_target (line 252)  ↔  V4 NavPlan.target
      - V3.5 _UNREACHABLE_THRESH (line 250)  ↔  V4 NavPlan.stuck_threshold default

    Per WO-CAMPAIGN2-01-STEP-0-AUDIT (Step 0a), three V3.5 variables map
    to NavPlan fields. Four NavPlan fields are V4 contributions:
      - cursor               (V3.5 used implicit pop-from-front)
      - expected_positions   (V3.5 derived empirically per step)
      - source_hypothesis_id (V4 traceability)
      - compiled_at_step     (V4 traceability)

    SURPRISE PATTERN

    Stuck counter increments when the ego doesn't reach its expected
    position after an emitted action. At threshold (V3.5 = 5; default
    here matches), the surprise method runs. V3.5 source eliminates the
    target and forces a replan; whether V4 implements that semantic OR
    the simpler `aborted = True` semantic is a WO-03 concrete-
    implementation decision — both are accommodated by this dataclass.

    See WO-CAMPAIGN2-01-STEP-0-AUDIT.md §0b for the semantic question.
    """

    actions: List[int] = field(default_factory=list)
    """The action_id sequence computed by BFS. Walked by cursor advancement.
    Each element is an integer in 1-7 (V3.5 NAV taxonomy: 1=UP, 2=DOWN,
    3=LEFT, 4=RIGHT, 5=SELECT, plus 6=COMPLEX, 7=UNDO). Source: V3.5
    _bfs_path at nav_executor.py:239.
    """

    target: Tuple[int, int] = (0, 0)
    """The coordinate the ego is navigating to. Source: V3.5
    _current_nav_target at nav_executor.py:252. Default (0, 0) is a
    placeholder; planners must set this at construction.
    """

    expected_positions: List[Tuple[int, int]] = field(default_factory=list)
    """Expected ego position after each action in `actions`. Same length
    as `actions`. Used by handle_unmoved_ego to detect stuck — compares
    actual ego position (read from VirelaiContext.ego_current_pos after
    the step) to expected_positions[cursor].

    V4 contribution. V3.5 derived expectations empirically per step via
    _process_nav_step(); V4 records them at plan-construction time so
    the surprise check is a simple list lookup rather than a
    recomputation.

    Invariant: len(expected_positions) == len(actions) when both are
    populated. Tested in test_navplan_field_invariants.
    """

    stuck_counter: int = 0
    """Increments when actual ego position != expected_positions[cursor].
    Resets when the ego successfully moves to the expected position OR
    when the target changes. Source: V3.5 _consec_blocked at
    nav_executor.py:251.
    """

    stuck_threshold: int = 5
    """Consecutive stucks before the surprise method fires. V3.5 source-
    verified value: _UNREACHABLE_THRESH = 5 at nav_executor.py:250
    (file-local constant). The synthesis specified 3 as a provisional
    default; Step 0b verified the actual V3.5 value is 5.

    Note: V3.5 source uses `>=` comparison (line 642), so threshold of
    5 means the surprise fires on the FIFTH consecutive stuck.
    """

    aborted: bool = False
    """V4 explicit abort flag. Set True when the surprise handler decides
    the plan cannot continue (e.g., stuck threshold breached).
    is_complete() returns True when aborted=True.

    V3.5 had this implicit in the run_nav_execution loop's break
    conditions; V4 makes it data on the dataclass so Strategize can
    inspect it without re-running the surprise logic.

    Under δ.1 (WO-CAMPAIGN2-03-AMENDED): handle_unmoved_ego sets
    aborted=True when stuck_counter reaches stuck_threshold (=5).
    """

    completed: bool = False
    """V4 explicit completion flag (added WO-CAMPAIGN2-03-AMENDED).

    Set True when ego reaches target. Distinct from aborted —
    `aborted=True` means the plan failed (stuck); `completed=True`
    means the plan succeeded (target reached). Both trigger
    is_complete()=True and dispatch teardown, but the verdict
    distinction matters for analysis and Campaign 3 work where
    CycleProbePlan and TraversalPlan have richer completion verdicts.

    The dispatch layer in select_action sets this field at start-of-tick
    observation when actual ego position equals self.target.
    """

    bfs_path: List[int] = field(default_factory=list)
    """Cached BFS path (WO-CAMPAIGN3-PHASE1-05).

    The action sequence computed by ``library.nav_path_computation.compute_path``
    on first ``next_action`` call. Each call pops one action from the head
    via ``pop(0)`` (matching V3.5's destructive-consumption pattern at
    ``execution/nav_executor.py:413``). Recomputed on path-exhausted
    (V3.5 trigger at ``execution/nav_executor.py:394``); if recompute
    returns None, ``aborted=True`` is set.

    Distinct from ``actions``: ``bfs_path`` is the upstream cache of
    not-yet-emitted action IDs; ``actions`` is the emitted history
    (each ``next_action`` call moves one ID from ``bfs_path`` to
    ``actions``).

    V3.5 source analog: ``_bfs_path`` local at
    ``execution/nav_executor.py:239``.
    """

    def is_complete(self) -> bool:
        """NavPlan completes when aborted (stuck threshold breached) OR
        completed (target reached).

        WO-CAMPAIGN2-03-AMENDED semantic shift from WO-01: under δ.1's
        lazy population, ``cursor`` is always equal to ``len(actions)``
        between emissions, so the cursor-vs-len check from WO-01 no
        longer applies as a completion criterion. Terminal state is
        signaled exclusively by the aborted/completed flags.
        """
        return self.aborted or self.completed

    def next_action(
        self,
        context: "VirelaiContext",
        library: "SemanticLibrary",
        available_actions: List[int],
        rng: random.Random,
    ) -> "GameAction":
        """Production δ.1 implementation: delegate to V4's existing Tier 3
        dominant-axis intelligence, then record the emission.

        Per Director ruling Q2 (WO-CAMPAIGN2-03-AMENDED): NavPlan
        delegates ``next_action()`` into the shared
        ``_compute_navigation_action_for_target`` helper (extracted
        from ``_select_tier3_nav_action`` in WO-03-AMENDED Step 1).
        The helper computes a directional action_id toward
        ``self.target`` using dominant-axis selection with
        stuck-detection perpendicular fallback.

        LAZY POPULATION INVARIANT

        Under δ.1, ``actions`` and ``expected_positions`` populate as
        the plan emits — they are NOT pre-computed at construction
        time. The invariant ``cursor == len(actions)`` holds before
        each call; after this call appends, the invariant still holds
        because ``self.cursor = len(self.actions)`` runs before the
        return statement (see end of function body).

        WO-CAMPAIGN2-03-AMENDED-CRASH-FIX (April 30, 2026): the
        original WO-03-AMENDED docstring stated "cursor is updated
        by the dispatch layer to match" — that was incorrect. No
        version of the dispatch layer ever updated cursor; the canary
        at ls20 Frame 2 fired the invariant check deterministically
        because cursor stayed at 0 after Frame 1's emission while
        len(actions) grew to 1. The fix restored cursor maintenance
        to next_action() itself, where it logically belongs alongside
        the actions/expected_positions appends.

        Source: V4-native dominant-axis intelligence (no V3.5 lineage).
        Inheritance: NEW — V3.5 had no plan substrate; this delegation
        is V4-native because V4's stepwise architecture creates a
        delegation point V3.5's monolithic spine handled implicitly.

        Raises:
            ValueError: if plan is aborted (is_complete() should have
                prevented this — defensive guard).
            ValueError: if invariant ``cursor == len(actions)`` is
                broken (defensive guard against caller bugs).

        Returns:
            GameAction.from_id(action_id) where action_id ∈ {1,2,3,4}
            (directional) per Tier 3 NAV taxonomy. Returns
            GameAction.RESET if no legal directional action available
            (helper returns 0 in that case).
        """
        if self.aborted:
            raise ValueError(
                "NavPlan.next_action called on aborted plan. "
                "is_complete() should have prevented this — "
                "dispatch contract violation."
            )
        if self.completed:
            raise ValueError(
                "NavPlan.next_action called on completed plan. "
                "is_complete() should have prevented this — "
                "dispatch contract violation."
            )
        if self.cursor != len(self.actions):
            raise ValueError(
                f"NavPlan invariant violated: cursor ({self.cursor}) "
                f"must equal len(actions) ({len(self.actions)}) before "
                f"next_action emission. Lazy population requires this "
                f"invariant — δ.1 protocol."
            )

        # WO-CAMPAIGN3-PHASE1-05: BFS-driven path emission.
        # Replaces the WO-CAMPAIGN2-03-AMENDED δ.1 delegation to
        # _compute_navigation_action_for_target with a cache-and-consume
        # pattern over a precomputed BFS path (V3.5 _bfs_path analog at
        # nav_executor.py:239-413).
        #
        # Per Director Ruling 2 (May 2, 2026, north star prep) Option α:
        # BFS or abort. On unreachable, set aborted=True and raise; the
        # dispatch layer in select_action falls back to reactive Tier 3
        # NAV (_select_tier3_nav_action), which still uses the dominant-
        # axis helper for no-plan-active frames.
        from arcengine import GameAction

        # ego_pos must be available; if not, plan should not have been
        # constructed (construction-site gating per WO-CAMPAIGN3-PHASE1-05
        # ensures this). Defensive fallback: emit RESET.
        if context.ego_current_pos is None:
            return GameAction.RESET

        # Compute (or recompute on path-exhausted) the BFS path through
        # the NavAtlas substrate. V3.5 trigger semantics preserved:
        # recompute whenever bfs_path is empty (initial OR exhausted).
        if not self.bfs_path:
            from virelai_v4.library.nav_path_computation import compute_path
            if context.nav_atlas is None:
                # Substrate not ready — construction-site gating
                # (WO-CAMPAIGN3-PHASE1-05 §3) should have prevented
                # this. Defensive: set aborted; dispatch tears down on
                # next frame.
                self.aborted = True
                return GameAction.RESET
            # Use prev_grid (the most recently observed grid) as the
            # passability oracle for nav_bfs_stride. prev_grid is
            # PER_LIFE_SCRATCHPAD; populated by _perceive on every
            # NOT_FINISHED frame.
            grid = context.prev_grid
            if grid is None:
                # First frame edge case — defensive fallback.
                return GameAction.RESET
            import numpy as _np
            grid_arr = _np.asarray(grid, dtype=_np.int32)
            path = compute_path(
                nav_atlas=context.nav_atlas,
                target=self.target,
                ego_pos=context.ego_current_pos,
                grid=grid_arr,
            )
            if path is None:
                # Unreachable target. Director Ruling 2 Option α: abort.
                # Set aborted=True; emit RESET this frame; dispatch
                # tears down on next frame and falls back to reactive
                # Tier 3 NAV.
                self.aborted = True
                return GameAction.RESET
            if not path:
                # start == target: BFS returns [] for arrival. Mark
                # plan completed; dispatch teardown handles the rest.
                self.completed = True
                return GameAction.RESET
            self.bfs_path = list(path)

        # Pop the next action from the cached path (V3.5 destructive
        # consumption pattern at nav_executor.py:413).
        action_id = self.bfs_path.pop(0)

        # Lazy population maintenance: append to actions; compute expected
        # next ego position from the action's STRIDE-AWARE displacement
        # via nav_atlas.action_dirs (WO-CAMPAIGN3-PHASE1-05 upgrade —
        # supersedes the unit-stride displacement table from
        # WO-CAMPAIGN2-03-AMENDED, which was a pre-substrate placeholder
        # noted in the original comment "V4 lacks stride-aware action_dirs
        # per Step 0 findings". The substrate now has them post-WO-03
        # commit.).
        self.actions.append(action_id)
        ego_row, ego_col = context.ego_current_pos
        dr, dc = context.nav_atlas.action_dirs.get(action_id, (0, 0))
        expected = (ego_row + dr, ego_col + dc)
        self.expected_positions.append(expected)

        # δ.1 invariant maintenance: cursor advances to match len(actions)
        # after emission. Preserves the WO-CAMPAIGN2-03-AMENDED-CRASH-FIX
        # invariant — the cursor must update INSIDE next_action, not in
        # the dispatch layer. Without this line, the Frame-2 canary
        # ValueError reappears.
        self.cursor = len(self.actions)

        return GameAction.from_id(action_id)

    def handle_unmoved_ego(self, context: "VirelaiContext") -> None:
        """Surprise handler: ego did NOT move to expected_positions[-1]
        after the last emitted action.

        Increments stuck_counter; if counter reaches stuck_threshold
        (V3.5-source-verified value 5 from
        Universal_Solver_v3_5/execution/nav_executor.py:250 — pinned
        in NavPlan default), sets aborted=True. Dispatch layer will
        tear down the plan on the next is_complete() check.

        Source: V3.5 nav_executor stuck-counter pattern at
        nav_executor.py:641-651. Inheritance: PRINCIPLE PORT — V3.5
        incremented in spine loop; V4 increments via dispatch-layer
        call to this handler under δ.1.

        Behavioral note: under δ.1's dominant-axis emission (not BFS),
        "ego didn't move to expected_positions[-1]" means "Tier 3
        dominant-axis emitted action X expecting movement to position
        Y, but ego stayed at Z." Same behavioral semantics as V3.5;
        the underlying emission strategy is dominant-axis (V4 reactive
        intelligence) rather than BFS (V3.5 spine intelligence). When
        Campaign 3 ports BFS, the surprise semantic remains identical
        — only the path-emission strategy upgrades.

        Args:
            context: VirelaiContext (unused in this implementation;
                accepted for protocol consistency with future surprise
                handlers that may need context state).
        """
        del context  # unused in δ.1; protocol slot for future expansion
        self.stuck_counter += 1
        if self.stuck_counter >= self.stuck_threshold:
            self.aborted = True


# ---------------------------------------------------------------------------
# CycleProbePlan — per-lever measurement plan
# ---------------------------------------------------------------------------

@dataclass
class CycleProbePlan(PlanBase):
    """Per-lever measurement plan.

    Two use cases via parameterization:

      1. Cycle characterization (V3.5 cycle probe pattern): press the
         lever up to max_presses times, observe per-press behavior,
         terminate on saturation or cycle return. target_state remains
         None.

      2. Target-state-driven characterization (V3.5
         _execute_unified_lever_loop DIRECTIONAL pattern): press until
         grid reaches target_state hash OR saturation. target_state is
         set to the desired terminal hash.

    SOURCE LINEAGE

      - V3.5 probe_lever_cycle() at discovery/physics/cycle_probe.py
        (cycle characterization)
      - V3.5 _execute_unified_lever_loop at execution/click_traversal.py
        (DIRECTIONAL torque/saturation tracking — absorbed into
        CycleProbePlan via target_state parameterization per WO-00.7
        Ask 4 partial-V3 resolution)

    V4 AUGMENTATION

    state_history stores hashes (str), NOT raw frames. The hash fast
    path enables O(1) cycle-return detection. V3.5 stored full frames
    (raw_states list at cycle_probe.py:176); V4 trades memory for speed.
    Pixel-level fallback can be added later if hash collisions become
    a real concern.

    SURPRISE PATTERN

    Saturation_counter increments on zero-delta presses. At threshold
    (V3.5 cycle probe: 1 — immediate single-comparison), the surprise
    method runs and terminates the plan with a verdict
    (completed_with_verdict). The cycle-return case is also detected
    in the surprise method by checking state_history against the
    incoming frame_hash.
    """

    lever_coord: Tuple[int, int] = (0, 0)
    """The lever being probed (CLICK coordinate). Default (0, 0) is a
    placeholder; planners must set this at construction.
    """

    max_presses: int = 4
    """Maximum presses before forced termination. V3.5 source-verified:
    `depth = 4` at discovery/physics/cycle_probe.py:172 (function-body
    literal, hardcoded). The synthesis Fact 3 (WO-00.5 NEW finding 3)
    confirmed the value as 4, NOT 8-12 as the chamber initially inferred.
    """

    delta_history: List[object] = field(default_factory=list)
    """Per-press delta records. Used to derive cycle length, direction,
    locality. Each element is a delta object (concrete type wired in
    WO-03 / WO-04 — likely WorldDelta or a derived per-press observation).
    """

    state_history: List[str] = field(default_factory=list)
    """Per-press state hashes. V4 hash fast-path replaces V3.5 raw_states
    list (cycle_probe.py:176 stored full np.ndarray frames).

    Each hash is computed from the post-press grid (e.g., MD5 hex digest
    of the grid bytes). Cycle return is detected by checking whether a
    new frame's hash matches any prior entry in state_history.
    """

    saturation_counter: int = 0
    """Increments on zero-delta presses. Resets on any non-zero-delta
    press. At saturation_threshold, the surprise method terminates the
    plan with completed_with_verdict='SATURATED'.
    """

    saturation_threshold: int = 1
    """Consecutive zero-deltas before saturation verdict. V3.5 source-
    verified: 1 (immediate single-comparison) at
    discovery/physics/cycle_probe.py:247-258. The cycle probe is
    aggressive on saturation — one no-op press is enough to declare
    SATURATED.

    Note: V3.5's lever_history.detect_saturation uses W=2; V3.5's
    DIRECTIONAL torque uses _TORQUE_THRESHOLD=3. CycleProbePlan absorbs
    only the cycle-probe variant (threshold 1). The other two
    saturation mechanisms live elsewhere — see WO-00.7 Ask 4 for the
    structural-difference analysis.
    """

    target_state: Optional[str] = None
    """If set, parameterizes for DIRECTIONAL characterization: press
    until grid hash matches target_state OR saturation. None means pure
    cycle characterization (terminate on cycle return or saturation).

    Use case: V3.5 _execute_unified_lever_loop runs a lever until a
    specific terminal grid is reached (the win-state of an embedded
    puzzle). V4 expresses that as CycleProbePlan with target_state set
    to the desired terminal hash.
    """

    completed_with_verdict: Optional[str] = None
    """Set when plan terminates. One of:
      - 'CYCLE_FOUND'      — state_history detected a return to a prior
                             state; cycle length recorded in delta_history
      - 'SATURATED'        — saturation_counter reached saturation_threshold
      - 'TARGET_REACHED'   — target_state matched (DIRECTIONAL use case)
      - 'BUDGET_EXHAUSTED' — cursor reached max_presses without other verdict

    None means plan still running.

    V3.5 returned a TransitionProfile dict from probe_lever_cycle();
    V4 collapses the verdict into a single typed string field plus
    delta_history / state_history for the supporting data.
    """

    def is_complete(self) -> bool:
        """CycleProbePlan completes when completed_with_verdict is set."""
        return self.completed_with_verdict is not None

    def next_action(
        self,
        context: "VirelaiContext",
        library: "SemanticLibrary",
        available_actions: List[int],
        rng: random.Random,
    ) -> "GameAction":
        """Return the lever-press action.

        Concrete implementation deferred to Campaign 3 (action type
        wiring + click coordinate machinery). Shell present for the
        interface contract; raises until then.

        WO-CAMPAIGN2-03-AMENDED signature update: matches PlanBase
        abstract signature for protocol consistency. Args unused
        until Campaign 3 production logic lands.
        """
        del context, library, available_actions, rng  # unused; deferred
        raise NotImplementedError(
            "CycleProbePlan.next_action: action emission deferred to Campaign 3"
        )

    def handle_zero_delta(self, frame_hash: str) -> None:
        """Surprise method shell: a press produced no delta, OR the
        post-press grid hash matches a prior state in state_history
        (cycle return).

        Concrete implementation deferred to WO-03 / WO-04. The contract:

          - If frame_hash in state_history (cycle return):
              set completed_with_verdict='CYCLE_FOUND'
              record cycle length in delta_history
          - elif frame_hash == target_state (DIRECTIONAL terminal):
              set completed_with_verdict='TARGET_REACHED'
          - else (zero-delta press):
              increment saturation_counter
              if saturation_counter >= saturation_threshold:
                  set completed_with_verdict='SATURATED'

        Source: V3.5 cycle probe numpy frame equality at
        cycle_probe.py:247-258 (the inner-loop saturation check).

        Args:
            frame_hash: The post-press grid hash (str, e.g., MD5 hex digest).
        """
        raise NotImplementedError(
            "CycleProbePlan.handle_zero_delta: surprise wiring deferred to WO-03 / WO-04"
        )


# ---------------------------------------------------------------------------
# TraversalPlan — combinatorial enumeration plan
# ---------------------------------------------------------------------------

@dataclass
class TraversalPlan(PlanBase):
    """Combinatorial enumeration plan for FINITE_SEARCH worlds.

    Walks a sequence of lever combinations one transition per frame.
    Default: gray-code enumeration over confirmed_levers (fresh).
    Parameterizable: replay variant via replay_source field, which loads
    a precomputed sequence from prior winning state.

    SOURCE LINEAGE

      - V3.5 _execute_lever_traversal at execution/click_traversal.py:73
        (gray-code enumeration primary)
      - V3.5 _execute_lever_replay at execution/click_traversal.py:165
        (replay variant)
      - V3.5 LeverCombinationMemory primary class at
        memory/lever_combination_memory.py:94 (int bitmask representation)

    Per WO-00.7 Ask 1 verified inheritance: V4 inherits the primary
    LeverCombinationMemory class (49 tests in V3.5
    test_memory/test_lever_combination_memory.py). The secondary class
    (DepthSequenceMemory at lever_combination_memory.py:350) is Phase 2
    deferred per V2 verdict.

    SURPRISE PATTERN — LEVER-SKIP-WITH-RECOVERY (NOT plan abort)

    This is the critical V3 amendment from the synthesis. When a
    specific lever appears unresponsive (torque_counter reaches
    torque_threshold = 3 per WO-00.7 Ask 4 verification), advance
    cursor PAST that lever and continue the plan with the remaining
    lever set. The plan does NOT terminate.

    Termination occurs only on:
      - WIN_FOUND       — the gray-code traversal hit a winning configuration
      - EXHAUSTED       — all 2^n configurations tested without a win
      - BUDGET_EXHAUSTED — action budget consumed before either of the above

    Source: V3.5 click_traversal lever-skip-with-recovery at lines 723-749,
    plus the world-state-change-clears-torque-dead recovery at lines 681-690.
    """

    current_combination: int = 0
    """Current lever configuration as an int bitmask. Bit i (0-indexed)
    represents the toggle state of lever i. Source: V3.5 primary
    LeverCombinationMemory representation at
    memory/lever_combination_memory.py:159 (`current_config: int = 0`).
    """

    last_toggle_bit: int = -1
    """Bit position of the most recent toggle. -1 means no toggle yet
    (plan just constructed; current_combination still at spawn config).

    Used by the surprise method to identify which lever to mark
    unresponsive when torque_counter triggers.
    """

    torque_counter: int = 0
    """Consecutive presses producing no progress on the current lever.
    Increments on unresponsive press; resets on world-state change.
    At torque_threshold, surprise method adds the current lever's bit
    position to skipped_levers.

    Source: V3.5 lever_torque dict at click_traversal.py:680 (per-lever
    counter inside _execute_unified_lever_loop). V4 simplifies to a
    single counter on the active lever; the dict-of-counters pattern
    is internal to whatever executor walks the plan.
    """

    torque_threshold: int = 3
    """Threshold for marking a lever as unresponsive. V3.5 source-verified:
    `_TORQUE_THRESHOLD = 3` at execution/click_traversal.py:21
    (module-level constant). Three consecutive zero-world-delta presses
    on the same lever → mark it unresponsive.
    """

    skipped_levers: Set[int] = field(default_factory=set)
    """Bit positions of levers marked unresponsive. Cursor advancement
    skips these in the gray-code sequence. Cleared when world-state
    change implies previously-saturated levers may now be live (per
    V3.5 click_traversal:681-690 recovery pattern).

    Critical invariant: adding to skipped_levers does NOT terminate
    the plan. Tested in test_traversal_plan_lever_skip_does_not_complete_plan.
    """

    replay_source: Optional[object] = None
    """If set, the plan walks this precomputed sequence (replay variant)
    instead of fresh gray-code enumeration.

    None = fresh enumeration via gray-code traversal of all 2^n configs.
    Some = replay (when LeverCombinationMemory is ported in a subsequent
    Campaign 2 WO, the type tightens to
    `Optional[LeverCombinationMemory]`).

    Per WO-00.7 V2 verdict: the LeverCombinationMemory port is a
    separate Campaign 2 WO; WO-01 forward-types `replay_source` as
    `Optional[object]` and the type tightens when the class lands.
    """

    completed_with_verdict: Optional[str] = None
    """Set when plan terminates. One of:
      - 'WIN_FOUND'        — a tested configuration produced a level win
      - 'EXHAUSTED'        — all 2^n configurations tested without a win
      - 'BUDGET_EXHAUSTED' — action budget consumed before WIN_FOUND or EXHAUSTED

    None means plan still running.

    Per V3 amendment: lever-skip events do NOT set this field. Only the
    three listed verdicts terminate the plan.
    """

    def is_complete(self) -> bool:
        """TraversalPlan completes only when completed_with_verdict is set.

        Critical: lever-skip events do NOT trigger completion. The plan
        recovers from per-lever surprise (handle_lever_unresponsive)
        without terminating.
        """
        return self.completed_with_verdict is not None

    def next_action(
        self,
        context: "VirelaiContext",
        library: "SemanticLibrary",
        available_actions: List[int],
        rng: random.Random,
    ) -> "GameAction":
        """Return the next lever-press action per gray-code traversal
        (or replay_source if set).

        Concrete implementation deferred to Campaign 3 (action type
        wiring + LeverCombinationMemory integration). Shell present
        for the interface contract; raises until then.

        WO-CAMPAIGN2-03-AMENDED signature update: matches PlanBase
        abstract signature for protocol consistency. Args unused
        until Campaign 3 production logic lands.
        """
        del context, library, available_actions, rng  # unused; deferred
        raise NotImplementedError(
            "TraversalPlan.next_action: action emission deferred to Campaign 3"
        )

    def handle_lever_unresponsive(self, lever_bit: int) -> None:
        """Surprise method shell: lever at lever_bit appears unresponsive
        (torque_counter reached torque_threshold).

        Concrete implementation deferred to WO-03 / WO-04. The contract:

          - Add lever_bit to skipped_levers
          - Reset torque_counter to 0
          - DO NOT set completed_with_verdict — plan continues with
            remaining lever set

        The cursor-advancement logic in next_action (deferred WO) will
        skip lever positions in `skipped_levers` when computing the
        next gray-code transition.

        Source: V3.5 lever-skip-with-recovery at click_traversal.py:723-749
        (verified at WO-00.7 Ask 4).

        Args:
            lever_bit: The bit position of the unresponsive lever
                (0-indexed; corresponds to lever_ids[lever_bit] in the
                surrounding LeverCombinationMemory once that class is ported).
        """
        raise NotImplementedError(
            "TraversalPlan.handle_lever_unresponsive: surprise wiring deferred to WO-03 / WO-04"
        )

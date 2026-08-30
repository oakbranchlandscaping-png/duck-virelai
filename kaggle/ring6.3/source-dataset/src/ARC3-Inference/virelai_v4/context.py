"""
Virelai V4 — VirelaiContext + four-tier persistence taxonomy

Typed state object carried between choose_action calls.
One instance per game. Created in __init__. Persists across lives
(GAME_OVER → RESET preserves it). Destroyed when the game ends
(framework creates a new Agent per game).

FIELD PERSISTENCE TAXONOMY (WO-MINE-03, adapted from V3.5 Module Guide
Step 5; fourth tier added for V4 per chamber decision April 19, 2026)

Every field on VirelaiContext is classified into exactly one of four tiers:

  PERSIST_LIVES_AND_LEVELS  — Stable physics of the game. Survives life
                              advance AND level advance. Examples:
                              library, cell history, visited-state set,
                              lifecycle counters, nav atlas.

  PERSIST_LIVES_RESET_LEVEL — Knowledge of the current level's structure.
                              Survives life advance within a level; rebuilds
                              on level advance because the level's lever set
                              / object layout may differ. Examples:
                              sweep_list, lever_memory, spawn_grid,
                              grid_scan.

  PERSIST_LEVELS_RESET_LIFE — Trajectory state that accumulates across
                              levels within a life and resets on life
                              advance. Example: actions_this_life — the
                              per-life action counter reports across the
                              levels played during that life.

  PER_LIFE_SCRATCHPAD       — Trajectory / cursor / iterator / per-frame
                              state. Resets on both life and level advance.
                              Examples: sweep iterator positions, stuck
                              counters, tier3 terminator state, frame-scoped
                              fields such as frame_delta and target_state.

FIX-A LESSON (from V3.5, per V3.5 chamber synthesis): Some state is
life-persistent but level-scoped. Without PERSIST_LIVES_RESET_LEVEL the
sweep re-uses stale Level 1 data after level advance. The fourth tier
(PERSIST_LEVELS_RESET_LIFE) completes the persist-on-life × persist-on-level
matrix so every field lands in a well-defined corner.

AUTHORITY: The _PERSISTENCE_TIERS dict at the bottom of VirelaiContext is
the authoritative source. Inline per-field comments document the
classification for readers; the dict is what drives harvest_persistent_state,
reset_for_new_life, reset_for_new_level, and the enumeration test.

Slots marked 'Phase 1+' are None now. They are typed docking points
for components that transfer from V3.5: GridScan, CellHistory,
SemanticLibrary, causal links, lever memory, BFS atlas.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, MISSING
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Dict,
    FrozenSet,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING,
)

import numpy as np

# WO-CC-S1: runtime import — default_factory needs the concrete class. The
# capture package imports only stdlib + state_tracker._norm_key, so no cycle.
from virelai_v4.capture.frame_record import FrameRecordLog

if TYPE_CHECKING:
    from virelai_v4.contracts.world_delta import WorldDelta
    from virelai_v4.library.nav_atlas import NavAtlas
    from virelai_v4.library.plan import (
        CycleProbePlan,
        NavPlan,
        PlanBase,
        TraversalPlan,
    )


class PersistenceTier(Enum):
    """Four-tier field persistence taxonomy (WO-MINE-03).

    Names encode the persist-on-life × persist-on-level matrix:
    - PERSIST_LIVES_AND_LEVELS : (persist, persist)
    - PERSIST_LIVES_RESET_LEVEL: (persist, reset)
    - PERSIST_LEVELS_RESET_LIFE: (reset, persist)
    - PER_LIFE_SCRATCHPAD      : (reset, reset)
    """

    PERSIST_LIVES_AND_LEVELS = "persist_lives_and_levels"
    PERSIST_LIVES_RESET_LEVEL = "persist_lives_reset_level"
    PERSIST_LEVELS_RESET_LIFE = "persist_levels_reset_life"
    PER_LIFE_SCRATCHPAD = "per_life_scratchpad"


@dataclass
class VirelaiContext:
    """Typed state carried between choose_action calls.

    One instance per game. Created in __init__. Persists across lives
    (GAME_OVER → RESET preserves it). Destroyed when the game ends
    (framework creates a new Agent per game).

    Every field is annotated with a PersistenceTier via an inline comment
    and mapped in the _PERSISTENCE_TIERS ClassVar at the bottom of the
    class. The dict is authoritative; inline comments are documentation.

    Slots marked 'Phase 1+' are None now. They're typed docking points
    for components that transfer from V3.5: GridScan, CellHistory,
    SemanticLibrary, causal links, lever memory, BFS atlas.
    """

    # --- What happened ---
    step_count: int = 0                          # persist_lives_and_levels
    last_level_seen: int = 0                     # persist_lives_and_levels  (WO-LB-01: true last-seen level, the two-way cursor; NOT the platform's completed-count — that is latest_frame.levels_completed)
    win_levels: int = 0                          # persist_lives_and_levels
    lives_used: int = 0                          # persist_lives_and_levels
    # WO-GAME-OVER-DETECTION: set True when arc_env.step returns no frame
    # (the environment ended the game). is_done reads it to stop cleanly —
    # "the game tells us when to stop" (no self-cap on the captain).
    env_terminated: bool = False                 # persist_lives_and_levels
    # actions_this_life: NOT_FINISHED actions on the current life;
    # accumulates across level advances within a life; resets on life advance.
    actions_this_life: int = 0                   # persist_levels_reset_life
    # last_pristine_verdict: WO-A3-01 — the PristineVerdict from the end-of-life
    # weave derivation (capture/ledger.py::PristineVerdict), or None if the check
    # has not run this life. Stored so the future RND-2 friction (stage 6) can
    # stamp it (C5); written by _land_weave_roles, never rendered here. Tiered
    # reset-per-life because it grades THIS life's weave window — a stale verdict
    # from a prior life must not present as the current one.
    last_pristine_verdict: object = None         # persist_levels_reset_life

    # woven_worldlines: WO-B3-R1a — the weave window retained at the landing
    # (_land_weave_roles): the List[Worldline] weave_window/re_join produced,
    # each ### -> [(node_index, RegionClay), ...]. A diagnostic hold for the
    # teardown integration roster (Lists 1 & 2); read by _render_integration_
    # roster at cleanup, never a belief field, never mutated, lands no role.
    # PERSIST_LIVES_RESET_LEVEL — the SAME tier as the frame_record_log it is
    # derived from: survives lives (so the last life's set reaches teardown),
    # resets on level advance (so it holds THIS level's integration).
    woven_worldlines: object = None              # persist_lives_reset_level

    # woven_role_verdicts: WO-B3-R1b — the weave's infer_roles output retained
    # alongside woven_worldlines for the teardown roster's LIST 3 (role per ###).
    # {worldline_id: RoleVerdict}. A DISPLAY hold, same tier/discipline as
    # woven_worldlines: derived-not-stored, never a belief field, never mutated,
    # lands no role (the belief-rebind is halted — see the R1b build return).
    woven_role_verdicts: object = None           # persist_lives_reset_level
    # WO-ROSTER-HOLD-01 · THE COVERAGE ROSTER'S SIX INPUTS, HELD TO TEARDOWN.
    #
    # **THE ROSTER WAS RIGHT AND THE FIELD WAS EMPTY.** `coverage_roster` derives its queue
    # from `weave_sweep_cuts` and its dispositions from the drive's three coverage sets —
    # **all six `PER_LIFE_SCRATCHPAD`, all cleared together by `reset_for_new_life`**, which
    # fires from the GAME_OVER branch of `choose_action` while the render runs at
    # `cleanup()`. So the roster reported absence, correctly, of a life it had just watched.
    # Had it re-derived a queue against cleared dispositions instead, it would have
    # reconciled to *all never attempted* — false in the opposite direction, and plausible.
    #
    # **SIX, NOT FOUR, AND THE COUNT WAS READ RATHER THAN ASSUMED.** The charter named
    # `weave_sweep_cuts`, `collide_drive_reached`, `collide_drive_not_reached` and
    # `collide_drive_offered`. An AST read of every `getattr` in the roster's four functions
    # returns a different set: the worldlines and the verdicts are read too (the queue needs
    # all three to be `visual_targets`' own derivation), the unreachable set is read for the
    # dormant class — and **`collide_drive_offered` is not read at all**, deliberately, since
    # it is the cursor's per-pass set and `WO-COVERAGE-ROSTER-01` guards that it is never
    # taken for an attempt record.
    #
    # **THE TIER AND THE DISCIPLINE ARE `woven_worldlines`', TWO DECLARATIONS ABOVE.**
    # `PERSIST_LIVES_RESET_LEVEL`: the life ended without a level advance, so the level's
    # state remains valid; a level advance clears it. Plain assignment at the capture point,
    # no mutation, no belief-write, no role. **The live fields keep their own tier** — the
    # drive needs them cleared between lives, and re-tiering a working field to serve a
    # diagnostic would change the drive's behaviour to make a reading easier.
    coverage_hold_cuts: object = None            # persist_lives_reset_level
    coverage_hold_worldlines: object = None      # persist_lives_reset_level
    coverage_hold_verdicts: object = None        # persist_lives_reset_level
    coverage_hold_reached: object = None         # persist_lives_reset_level
    coverage_hold_not_reached: object = None     # persist_lives_reset_level
    coverage_hold_unreachable: object = None     # persist_lives_reset_level

    # woven_repeated_contact: WO-COMPOUND-ROLE-01 — the set of worldline ids
    # independently confirmed as LEVER by real, repeated contact this life
    # (weave.repeated_contact.confirmed_by_repeated_contact). A second,
    # separately-sourced fact alongside woven_role_verdicts's correlation-based
    # role — NOT a replacement, NOT written into any RoleVerdict, decides
    # nothing about which tag is "correct" (RULING_OBSERVERS_INTEGRATOR_v1: the
    # integrator's role verdict stays the sole decider). Same tier/discipline as
    # woven_role_verdicts: derived-not-stored, never a belief field, never
    # mutated, read only by _render_integration_roster at teardown.
    woven_repeated_contact: object = None         # persist_lives_reset_level

    # --- Three-frame model ---
    # Previous frame's grid for delta computation (numpy array).
    prev_grid: Optional[np.ndarray] = None       # per_life_scratchpad
    # Level start. Set on first frame. Never overwritten by actions.
    spawn_grid: Optional[list[list[int]]] = None  # persist_lives_reset_level
    # live grid is always the current frame — no storage needed

    # --- Visited states (State Space Theorem — Phase 0 lightweight tracker) ---
    visited: set[bytes] = field(default_factory=set)   # persist_lives_and_levels
    novel_count: int = 0                         # persist_lives_and_levels
    repeated_count: int = 0                      # persist_lives_and_levels

    # --- Perception layer (Phase 1 — WO-03) ---
    # Latest FrameDelta from compute_frame_delta().
    frame_delta: Optional[object] = None         # per_life_scratchpad
    # WO-XLEVEL-02a: Dict[TypeSignature, SlotPrior] — ghost priors captured by
    # the §2.8.5 level-advance hook (library/substrate/level_advance.py).
    xlevel_prior_snapshot: Optional[dict] = None  # persist_lives_reset_level
    # Dict[Tuple[int,int], CellHistory] — per-cell accumulator.
    cell_history: Optional[object] = None        # persist_lives_and_levels
    # StateTracker — visited set with SHA-256 hashing.
    state_tracker: Optional[object] = None       # persist_lives_and_levels
    # WO-CC-S1 · CAPTURE — append-only, interpretation-free record of the given
    # (one CaptureRecord per choose_action node, all layers, lossless). A read
    # sidecar: it records latest_frame/frames; it writes only its own log.
    # Whole-game record — survives life and level resets.
    frame_record_log: "FrameRecordLog" = field(default_factory=FrameRecordLog)  # persist_lives_and_levels

    # --- Library sync (WO-04) ---
    # Action ID returned on the previous choose_action call.
    last_action_id: Optional[int] = None         # per_life_scratchpad
    # WO-R4: the emitted Push click's target (region_id), plumbed to the record
    # sites so a composite click records (6, region_id), not (6, None).
    last_action_target: Optional[object] = None  # per_life_scratchpad
    # WO-R1-02c: the (row, col) cell the last emitted action acted on — None for
    # non-coordinate actions. Rides the same per-frame channel as
    # last_action_id: set at the emission site, read by the next frame's
    # frame_record_log.append to complete that node's record.
    last_action_cell: Optional[object] = None    # per_life_scratchpad
    # GridScan result for the current level (set on spawn).
    grid_scan: Optional[object] = None           # persist_lives_reset_level

    # --- Semantic library (WO-02) ---
    # Type: library.semantic_library.SemanticLibrary
    semantic_library: Optional[object] = None    # persist_lives_and_levels

    # --- Memory layer (WO-04) — persist across lives (Groundhog Day) ---
    # Empirical NAV spatial memory removed in WO-CLEAN-09-PHASE-1
    # (was vestigial; never wired into the V4 solver; per-frame BFS in
    # tier3_nav.py replaced its function).
    # WO-CAMPAIGN3-PHASE1-01 (May 2, 2026): NavAtlas substrate ported from
    # V3.5 canonical implementation. Held here as Optional[NavAtlas]; None
    # before the stride probe (WO-03) populates it. Field-granular
    # persistence per Halt 2 ratification:
    #   PER_GAME (preserved across level transitions):
    #       ego_class, ego_value_set, ego_spawn, action_dirs
    #   PER_LEVEL (cleared on level transition by reset_spatial()):
    #       walkable_classes, blocked_classes, visited_cells,
    #       adjacent_classes, target_candidates, contacted_sites,
    #       target_attempt_count, mutation_targets, unreachable_targets,
    #       blocked_edges, site_delta_history, step_delta_log
    # The whole-field tier is PERSIST_LIVES_AND_LEVELS (PER_GAME identity
    # survives both life and level resets); reset_for_new_level invokes
    # nav_atlas.reset_spatial() to clear the PER_LEVEL substate.
    nav_atlas: Optional["NavAtlas"] = None       # persist_lives_and_levels
    # LeverCombinationMemory — Gray code traversal for CLICK worlds.
    # Per V3.5 FIX-A: lever set changes per level, so this is level-scoped
    # even though it survives the life boundary.
    lever_memory: Optional[object] = None        # persist_lives_reset_level

    # --- Targeting layer (WO-C3-03) — recomputed every NOT_FINISHED frame ---
    target_state: object = None                  # per_life_scratchpad
    routing_directive: object = None             # per_life_scratchpad

    # --- FLAG-017: Death-frame guard (WO-C5-01) ---
    # Set True when state == GAME_OVER; cleared False on the next NOT_FINISHED
    # frame.  Passed to sync_library() so Mode B can skip contaminating
    # statistics from the death frame.  In the current architecture
    # _sync_library() is gated to NOT_FINISHED, so is_death_frame is always
    # False when sync runs; the flag is here as an architectural safety net
    # and is exercised directly in unit tests.
    is_death_frame: bool = False                 # per_life_scratchpad

    # --- HUD mask + LC-only delta counter (WO-C5-03) ---
    # hud_mask: set once when COUNTER is first detected; persists through
    # Groundhog Day.  Cells that are True belong to the life counter and are
    # excluded from world evidence.  Type annotation is `object` to avoid
    # importing numpy here; runtime value is np.ndarray (bool, grid_shape)
    # or None.
    hud_mask: object = None                      # persist_lives_and_levels

    # WO-CAMPAIGN3-PHASE3-01: ActionRealityReport accessor for cycle probe.
    # Holds the contract artifact whose ``life_counter_region`` field the
    # cycle probe reads to mask LC pixels during transition classification
    # (per V3.5 invariant cycle_probe.py:75-83). Type annotation is `object`
    # to avoid importing the contract here; runtime value is
    # virelai_v4.contracts.action_reality_report.ActionRealityReport or None.
    action_reality_report: object = None         # persist_lives_and_levels

    # WO-CAMPAIGN3-PHASE3-01-AMEND (May 3, 2026): per-frame state machine
    # for cycle probe execution. Mirrors V4 stride probe pattern at
    # library/stride_probe.py:96-138. Type annotation is `object` to avoid
    # importing CycleProbeState here (avoids circular import); runtime
    # value is virelai_v4.contracts.lever_mechanism.CycleProbeState or None.
    cycle_probe_state: object = None             # per_life_scratchpad

    # collide_sweep_state: NAV collide-with-everything (rung 2) per-life coverage
    # state — {"list", "collided", "target", "frames"}. PER_LIFE_SCRATCHPAD so the
    # collided-set resets each life (mirrors cycle_probe_state). Written only by
    # strategy/collide_sweep.collide_sweep_action under VIRELAI_COLLIDE_SWEEP;
    # no belief.
    collide_sweep_state: object = None           # per_life_scratchpad

    # lc_only_delta_count: incremented each time a raw delta has changes but
    # zero world changes (all changed cells are inside the HUD mask). Feeds
    # future torque detection.
    lc_only_delta_count: int = 0                 # persist_lives_and_levels

    # --- Background recognition (WO-C5-05) ---
    # spawn_class_frequencies: Dict[int, int] — pixel class → cell count on
    # the spawn frame. Computed once in Mode A and stored. Feeds Channel 3
    # (visual dominance) of the ignore score.
    spawn_class_frequencies: object = None       # persist_lives_and_levels

    # background_class_votes: Dict[int, int] — class → count of times that
    # class was revealed when the ego moved off a cell (NAV worlds). Feeds
    # Channel 4 (displacement residual). Initialized to {} when the library
    # is first created. Mutated in place by library_sync. Persists through
    # Groundhog Day (lives within a game share one accumulator).
    background_class_votes: object = None        # persist_lives_and_levels

    # --- Tier 3 CLICK probing (WO-02) ---
    # probe_history: Dict[int, int] mapping region_id → probe count.
    # Persists across lives within a level (Groundhog Day). Resets at
    # level advance because region_ids regenerate per level via GridScan
    # rebuild — carrying counts across the boundary attaches them to a
    # region_id that may no longer denote the same object (GAP-7 hazard,
    # closed by WO-LGTD-01 per the Library-Grounded Tool Dispatch campaign).
    # Mutated in place by action_selector.
    probe_history: dict = field(default_factory=dict)  # persist_lives_reset_level

    # last_probe_target: region_id of the object just probed on the previous
    # action. Set by action_selector, cleared after evidence recording in
    # library_sync. Used to connect intent (probing this object) to
    # observation (world delta).
    last_probe_target: Optional[int] = None      # per_life_scratchpad

    # last_probe_coord: (row, col) coordinate just probed on the previous
    # action. Set by action_selector, cleared after evidence recording.
    last_probe_coord: Optional[tuple] = None     # per_life_scratchpad

    # --- Tier 3 NAV probing (WO-03) ---
    # ego_current_pos: (row, col) centroid of ego. Updated after each
    # directional action. Initialized from ego_centroid on first confirmed
    # displacement; resets to spawn on RESET.
    ego_current_pos: Optional[tuple[int, int]] = None   # per_life_scratchpad

    # nav_probe_target: region_id of the current navigation target (object
    # to probe). Set by _select_tier3_nav_action(), cleared when target is
    # reached or skipped.
    nav_probe_target: Optional[int] = None       # per_life_scratchpad

    # nav_stuck_count: incremented each directional action toward same
    # target without displacement. Resets to 0 when target changes or
    # displacement occurs. Per-life field (reset on RESET).
    nav_stuck_count: int = 0                     # per_life_scratchpad

    # nav_last_nav_action: ID (1-4) of the last directional action taken.
    # Used to detect when agent is re-attempting same wall (consecutive
    # equal actions). Per-life field (reset on RESET).
    nav_last_nav_action: Optional[int] = None    # per_life_scratchpad

    # nav_skipped_targets: set of region_ids that were unreachable
    # (stuck >= 3 frames). Per-life field (reset on RESET).
    nav_skipped_targets: set[int] = field(default_factory=set)  # per_life_scratchpad

    # --- Stride probe substrate bootstrap (WO-CAMPAIGN3-PHASE1-03) ---
    # Per Director Ruling 1 (May 2, 2026) Option B: minimal stride probe drives
    # cardinals one per Life 1 frame to populate nav_atlas.action_dirs from
    # observed ego displacement (via library.header.ego_displacement_map
    # populated by ego_detector). See library/stride_probe.py for the state
    # machine.
    #
    # stride_probe_complete: True after the probe commits action_dirs to
    # nav_atlas. Persists across lives (nav_atlas is PERSIST_LIVES_AND_LEVELS;
    # action_dirs once populated stays populated).
    stride_probe_complete: bool = False          # persist_lives_and_levels
    # stride_probe_attempted: cardinal action IDs already attempted this life.
    # Resets at life advance so that if Life 1 ends mid-probe (before all
    # cardinals tried), Life 2 retries cleanly. The probe halts when this
    # set covers every available cardinal, even if some failed to displace.
    stride_probe_attempted: Set[int] = field(default_factory=set)  # per_life_scratchpad

    # --- Tier 3 CLICK same-target terminator (FRICTION-LC-04 Bug 3) ---
    # tier3_last_click_target: region_id of the most recent Tier 3 CLICK
    # target. Used to detect consecutive same-target selections (K=5 cap).
    # Per-life.
    tier3_last_click_target: Optional[int] = None    # per_life_scratchpad

    # tier3_consecutive_same_target: consecutive frames routed to the same
    # Tier 3 CLICK target. Resets to 0 when target changes. Per-life field.
    tier3_consecutive_same_target: int = 0       # per_life_scratchpad

    # tier3_click_skipped_targets: region_ids evicted by the K=5 same-target
    # cap. Skipped until the next RESET. Per-life field.
    tier3_click_skipped_targets: Set[int] = field(default_factory=set)  # per_life_scratchpad

    # --- Execution (Phase 2+) ---
    execution_plan: Any = None                   # per_life_scratchpad

    # --- Plan substrate (WO-CAMPAIGN2-01) ---
    # current_plan: the active plan (NavPlan, CycleProbePlan, or TraversalPlan),
    # or None for reactive mode. Strategize reads this field each frame; if not
    # None, the plan emits the next action; if None, reactive handlers run.
    # Plans live at virelai_v4/library/plan.py.
    # Persistence: PER_LIFE_SCRATCHPAD — plans do not survive Groundhog Day.
    # Library knowledge that informed the plan persists under its own tier
    # annotations; Life N+1 reconstructs plans from updated state.
    # Type: Optional[PlanBase] — typed via forward reference under TYPE_CHECKING
    # so plan.py's import does not introduce a runtime dependency on context.py
    # (plan.py is library-layer; context.py is library-adjacent; the typing
    # import direction is unidirectional — context.py imports from plan, not
    # vice versa).
    current_plan: Optional["PlanBase"] = None    # per_life_scratchpad

    # --- Ego mask (WO-02) ---
    # ego_mask: boolean np.ndarray marking cells ego arrived at
    # (current_pos) or departed (prev_pos). Set during Perceive step on
    # EMBODIED worlds. None or all-zeros on other world types.
    ego_mask: Optional[np.ndarray] = None        # per_life_scratchpad

    # prev_ego_pos: (row, col) ego centroid from the previous frame. Saved
    # at start of Perceive step to compute mask covering both arrival and
    # departure.
    prev_ego_pos: Optional[Tuple[int, int]] = None   # per_life_scratchpad

    # --- Tier 4 CLICK probe tracking (WO-02 LEVER-CATALOG) ---
    # Set by action_selector when a Tier 4 probe action is emitted.
    # Read by library_sync on the next frame after the probe has been
    # executed. Cleared to None after the ProbeOutcome has been processed.

    # last_probe_target_region_id: region_id of the object just probed
    # (Tier 4).
    last_probe_target_region_id: Optional[int] = None   # per_life_scratchpad

    # last_probe_target_cells: spawn-frame cell set of the probed region.
    # Captured at probe time so the detector compares against stable
    # geometry.
    last_probe_target_cells: Optional[FrozenSet[Tuple[int, int]]] = None  # per_life_scratchpad

    # last_probe_action_kind: "CLICK" or "NAV_CONTACT". "CLICK" is the only
    # writer in WO-02. "NAV_CONTACT" is reserved for WO-03.
    last_probe_action_kind: Optional[Literal["CLICK", "NAV_CONTACT"]] = None  # per_life_scratchpad

    # --- Physics measurement (WO-A.2b, Physics Reframe NR-01) ---
    # physics_vectors: per-lever operation evidence, keyed by lever region_id
    # -> library/physics_accumulator.LeverPhysics (vectors by operation
    # signature + bracket count). Accumulates ACROSS LIVES within a level
    # (Groundhog Day); resets at level advance with the region_ids it is
    # keyed by (same rationale as probe_history).
    # physics_verdicts: per-lever CausalVerdict name (e.g.
    # "DIRECTIONAL_DISPLACEMENT") once the operation is a confirmed
    # translation. Write-only in A.2b; the read lands at A.3.
    physics_vectors: dict = field(default_factory=dict)   # persist_lives_reset_level
    physics_verdicts: dict = field(default_factory=dict)  # persist_lives_reset_level
    # WO-C3: per-lever PENDING conserved-transfer candidate from the prior press,
    # held for the forward out-of-sample prediction gate. RUNTIME only (not
    # belief); the licensed relation is written to belief by the Substrate. Same
    # per-level tier as physics_vectors.
    conserved_transfer_candidates: dict = field(default_factory=dict)  # persist_lives_reset_level

    # --- Canonical WorldDelta (WO-02-ARCH) ---
    # Computed once at the top of sync_library and stored here.
    # Every downstream system reads from this field instead of calling
    # _compute_world_delta.  None before the first Mode B frame (i.e., on
    # spawn and Groundhog Day reset frames).
    world_delta: Optional['WorldDelta'] = None   # per_life_scratchpad

    # --- Sweep state (WO-04) — world-type-agnostic (WO-05 NAV sweep reuses these same fields) ---
    # sweep_list: ordered region_ids to probe, built by build_sweep_list().
    # sweep_index: next index into sweep_list to probe (advances each frame).
    # sweep_probed: set of region_ids already visited in this sweep.
    # sweep_consecutive_inerts: consecutive NO_EFFECT probes since last reactive.
    # sweep_reactive_found: total reactive (LEVER) discoveries in this sweep.
    # sweep_built_for_level: context.last_level_seen value when list was built;
    #     rebuild triggered when it mismatches the current last_level_seen.
    # sweep_complete: True once termination condition fires.
    sweep_list: List[int] = field(default_factory=list)    # persist_lives_reset_level
    sweep_index: int = 0                         # per_life_scratchpad
    sweep_probed: Set[int] = field(default_factory=set)    # per_life_scratchpad
    sweep_consecutive_inerts: int = 0            # per_life_scratchpad
    sweep_reactive_found: int = 0                # per_life_scratchpad
    sweep_built_for_level: Optional[int] = None  # persist_lives_reset_level
    sweep_complete: bool = False                 # per_life_scratchpad

    # --- Weave coverage-sweep state (WO-WEAVE-SWEEP-01 Phase 1) ---
    # DISTINCTLY NAMED from the sweep_* fields above on purpose (Phase 0 new
    # finding #1): those are the LEGACY click_sweep.py's own dedicated state;
    # reusing them would silently couple the new weave-native sweep to the
    # legacy system this WO is built to route around. All fields here are
    # PER_LIFE_SCRATCHPAD — the coverage sweep is a fresh, per-life question
    # (the problem it exists to fix is itself per-life), so nothing here
    # needs to survive a life boundary the way sweep_list/sweep_built_for_level
    # do for the level-scoped legacy sweep.
    #
    # weave_sweep_list: ordered worldline ids to contact, built by
    #     build_weave_sweep_list() in weave/coverage_sweep.py.
    # weave_sweep_index: next index into weave_sweep_list to probe.
    # weave_sweep_probed: set of worldline ids already contacted this sweep.
    # weave_sweep_consecutive_inerts: consecutive no-delta contacts (backstop
    #     termination only — the primary termination is a FIRM LEVER verdict).
    # weave_sweep_complete: True once either termination condition fires.
    # weave_sweep_worldlines / weave_sweep_verdicts: the cached read from the
    #     last compute_current_weave_roles() call, reused across frames
    #     between recompute ticks (WO-WEAVE-SWEEP-01 Phase 0 §0.2 cadence
    #     throttle) — None before the first recompute this life.
    # weave_sweep_last_recompute_step: ctx.step_count at the last recompute,
    #     or None before the first one; compared against
    #     WEAVE_SWEEP_RECOMPUTE_INTERVAL to decide whether a recompute is due.
    weave_sweep_list: List[int] = field(default_factory=list)        # per_life_scratchpad
    weave_sweep_index: int = 0                                       # per_life_scratchpad
    weave_sweep_probed: Set[int] = field(default_factory=set)        # per_life_scratchpad
    weave_sweep_consecutive_inerts: int = 0                          # per_life_scratchpad
    weave_sweep_complete: bool = False                               # per_life_scratchpad
    weave_sweep_worldlines: Optional[list] = None                    # per_life_scratchpad
    weave_sweep_verdicts: Optional[dict] = None                      # per_life_scratchpad
    weave_sweep_last_recompute_step: Optional[int] = None            # per_life_scratchpad
    # WO-SWEEP-FORK-01 · weave_sweep_nav_note: on a NAV world the sweep computes
    # verdicts and selects a candidate but emits nothing — the navigation
    # primitive that would drive the ego to it is not built. This carries the
    # stated absence so it is legible in the run rather than inferred from
    # silence. Display-only; no predicate reads it. PER_LIFE_SCRATCHPAD like
    # every other weave_sweep_* field.
    weave_sweep_nav_note: str = ""                                   # per_life_scratchpad
    # WO-COLLIDE-GOLDEN-01 · the cuts and the action series behind the cached read, so the
    # collide drive can take ONE owner_edge across the two most recent cuts and read the
    # ego's measured bearings without a second ledger_from_capture. Both were computed on
    # the same path already and discarded at the return.
    weave_sweep_cuts: Optional[list] = None                          # per_life_scratchpad
    weave_sweep_node_actions: Optional[list] = None                  # per_life_scratchpad
    # WO-COLLIDE-GOLDEN-01 · the drive's own state. No belief; the drive writes nothing
    # else anywhere.
    # WO-VISUAL-TARGETS-01 · `collided` IS RE-KEYED FROM WORLDLINE IDS TO SITES — the
    # anchors of the visual objects the drive has worked. A worldline id is renumbered by
    # first appearance in every window, so a checkoff keyed on one ticks off whatever now
    # holds that number; a site does not renumber. `target` stays the worldline this frame
    # steps toward (the stepper reads a footprint off a `Worldline`); `target_site` is the
    # coverage key of the same pursuit, and the two are set and cleared together.
    # WO-BLOCKER-TAG-01 · THREE STATES WHERE THERE WAS ONE SET. `collided` conflated
    # *reached* with *passed over*: a target that expired its budget was indistinguishable
    # from one the ego stood on, so it read as done and was never chosen again. Renamed to
    # say what it now holds — ARRIVED only — beside a provisional `unreachable` and the
    # blocking tags that void it. A budget expiry writes to neither: the target returns to
    # UNTRIED, because twelve frames expiring is *I ran out*, not *I cannot*.
    # WO-TARGET-THE-OBJECT-01 · THE FIVE COVERAGE FIELDS BELOW HOLD A VISUAL OBJECT'S
    # IMMORTAL KEY `(class integer, cells)`, NOT AN ANCHOR. R-1: the NW corner is a
    # reference point for navigation; the target is the object's cell-site footprint.
    # Two objects whose corners coincide are two records. The annotation is `Any` rather
    # than the key's tuple because the key's second half is a frozenset of cells and
    # spelling that here would put a capture-layer type in the context's signature.
    # **`collide_drive_target_site` keeps its name and no longer describes what it holds**
    # — the rename touches `collide_plan`, outside that rung's fence, and is CE's.
    collide_drive_reached: Set[Any] = field(default_factory=set)     # per_life_scratchpad
    # PROVISIONAL, and cleared whole whenever the blocking tags change — impassable is
    # universal and never proven, so anything that could have opened a path reopens all
    # of them. The sixth instance of this build's standing asymmetry.
    collide_drive_unreachable: Set[Any] = field(default_factory=set)  # per_life_scratchpad
    # The fingerprints of the objects presently standing where a refused press would have
    # put the ego. Re-derived every frame and stored ONLY so a change is noticeable: the
    # tag is keyed on the fingerprint and dies with it, which is what makes a blocker that
    # moves, recolours, grows or shrinks reopen the path it was closing.
    collide_drive_blockers: frozenset = frozenset()                  # per_life_scratchpad
    # WO-OPENING-PHASE-01 · THE OPENING PHASE'S ONLY STATE: `{action: presses so far}`,
    # written by the NAV arm and read by nothing else.
    #
    # **THE PHASE IS DERIVED FROM IT AND HAS NO FLAG.** *Done* is *every offered action has
    # been pressed more than once*, asked of the offered set as it stands each frame. A
    # separate `complete` boolean would be a second producer of one fact, and the two would
    # drift the first time an offered set changed mid-life.
    #
    # PER_LIFE_SCRATCHPAD, and the tier is the whole ruling on repetition: a new life is a
    # new board and a new body, so `reset_for_new_life` empties this and the phase runs
    # again. **It is not PERSIST_LIVES**: an action model earned on the last life is a claim
    # about a world that has since been rebuilt.
    nav_opening_presses: dict = field(default_factory=dict)          # per_life_scratchpad
    collide_drive_target: Optional[int] = None                       # per_life_scratchpad
    collide_drive_target_site: Optional[Any] = None                  # per_life_scratchpad
    # WO-HOLD-THE-PATH-01 · THE PLAN, HELD. `reach` returns the action sequence that puts
    # the ego's footprint on the target — blocker-aware, lattice-correct, avoiding every
    # refused transition — and `_reach_state` returned its LENGTH and dropped the sequence
    # on that line. Without it the drive re-derived a greedy step from the raw signed gap
    # every frame, with no memory of the last one, and reversed whenever it overshot a
    # component by a stride. `path_for` names the site the plan was computed for, so a
    # target change is a trigger that can be seen rather than assumed.
    collide_drive_path: tuple = ()                                   # per_life_scratchpad
    collide_drive_path_for: Optional[Tuple[int, int]] = None         # per_life_scratchpad
    # WO-OUT-OF-REACH-01 · a NON-EMPTY plan reached zero during THIS pursuit — a route
    # walked to its end. Set at `collide_plan._next_press`'s pop, which is the only line
    # that can tell a walked route from a plan that was never non-empty, and cleared in
    # `_pass_over` beside the plan it is about. **The lifetime is the rung's sharpest
    # failure mode**: a flag outliving its pursuit makes the NEXT pursuit retire on its
    # first refusal with no attempt of its own, which is the prediction gate
    # `WO-NO-PREDICTION-01` deleted, arriving through the back door.
    collide_drive_walked_out: bool = False                           # per_life_scratchpad
    collide_drive_frames: int = 0                                    # per_life_scratchpad
    # WO-PROBE-RECORD-01 · the probe's own record. `trail` is presses-remaining, one entry
    # per stepped frame of the HELD target, cleared when the target is retired — so it is a
    # trajectory for one pursuit and never carries one probe's progress into another.
    # `outcome` is (target, ARRIVED|UNREACHABLE|BUDGET) for the last retirement, which the
    # untagged `collided` set cannot say. Neither is read by any seal.
    collide_drive_trail: tuple = ()                                  # per_life_scratchpad
    collide_drive_outcome: Optional[tuple] = None                    # per_life_scratchpad
    # WO-CURSOR-AND-STUCK-01 · THE CURSOR IS A SET OF SITES, NOT AN INDEX. The candidate
    # list is a read-time derivation rebuilt every frame; it GROWS by appending, but an
    # entry BARRED mid-run shifts every position after it, so an integer index silently
    # points at a different place. `WO_VISUAL_TARGETS_01` re-keyed coverage to sites for
    # this exact reason and the cursor follows it. Holds the sites OFFERED since the last
    # full pass; it empties the moment no untried candidate is left unoffered, which is
    # the pass boundary and the only clearing condition there is.
    # WO-COVERAGE-ROSTER-01 · THE SITES PURSUED AND NOT REACHED, AND IT IS A DIFFERENT
    # FACT FROM EVERY FIELD ABOVE IT.
    #
    # `collide_drive_outcome` holds ONE tuple — the LAST retirement — so *this place was
    # worked and the pursuit ended without arrival* survived exactly until the next
    # retirement overwrote it. `collide_drive_offered` is not it either: the cursor adds a
    # site the frame it becomes the target and **empties the whole set at every pass
    # boundary**, which is the one clearing condition it has. So at the end of a life
    # nothing in this context could distinguish a site pursued to exhaustion from a site
    # never selected — and that is the distinction the coverage roster exists to state.
    #
    # **WRITTEN AT `_pass_over`, BESIDE THE RETIREMENT IT RECORDS**, so the set and the
    # outcome cannot diverge: every non-arrival retirement adds its site here in the same
    # three lines that name the outcome.
    #
    # **NOT SUBTRACTED WHEN A LATER PASS ARRIVES.** `collide_drive_reached` is existential
    # and permanent; this set is the record of attempts that ended without one. A site in
    # both was worked, failed, and later touched — TOUCHED wins **at the render**, by
    # precedence rather than by a retraction, exactly as `Transitions`' passable-wins is
    # structural rather than procedural. Un-recording an attempt that really happened
    # would be the drive editing its own history.
    collide_drive_not_reached: Set[Any] = field(default_factory=set)  # per_life_scratchpad
    # WO-CURSOR-AND-STUCK-01 · the ego anchor the presses below are counted AT, and the
    # count. Both reset when the ego moves; the count also resets when a pursuit ends.
    # WO-STUCK-IS-POSITIONAL-01 · RENAMED, AND THE RENAME IS THE FIX'S HALF.
    # `collide_drive_anchor` held the ego's anchor and `..._anchor_presses` counted presses
    # against it — but the anchor was read from the CACHED weave window, which refreshes
    # once every `WEAVE_SWEEP_RECOMPUTE_INTERVAL` actions, so it was IDENTICAL between
    # refreshes whatever the ego did. The names said *position* and the values were *the
    # same reading, re-read*. Now: `observed` is `(node_index, anchor)` — the OBSERVATION,
    # so a re-read of one window is recognisable as one observation — and `unmoved_reads`
    # counts consecutive FRESH observations in which the ego had not moved.
    collide_drive_unmoved_reads: int = 0                             # per_life_scratchpad

    # --- Mechanism-typing probe state (WO-LEVER-SUBTREE-06) ---
    # All PER_LIFE_SCRATCHPAD, same reasoning as the weave_sweep_* block above
    # — a fresh, per-life question, nothing here needs to survive a life
    # boundary.
    #
    # mechanism_probe_started: True once weave/coverage_sweep.py's
    #     _start_mechanism_probe has run this life (a FIRM lever has appeared).
    # mechanism_probe_lever_queue: FIRM lever worldline ids still waiting their
    #     turn, ascending by id (deterministic, no salience heuristic).
    # mechanism_probe_current_lever: the lever wid currently being repeat-
    #     clicked, or None once the whole campaign (every queued lever) is
    #     done.
    # mechanism_probe_pending_partners: confirmed reactive partner wids of the
    #     current lever not yet classified.
    # mechanism_probe_fingerprints: partner wid -> ordered
    #     (class_id, cells) fingerprint sequence collected so far, for the
    #     CURRENT lever's campaign only — reset by _advance_to_next_lever.
    # mechanism_probe_press_count: targeted presses issued so far toward the
    #     current lever, checked against MECHANISM_PROBE_MAX_PRESSES
    #     (weave/mechanism_classify.py).
    # mechanism_probe_results: lever wid -> {partner wid: mechanism string},
    #     accumulated across every lever this life's campaign has walked.
    mechanism_probe_started: bool = False                              # per_life_scratchpad
    mechanism_probe_lever_queue: List[int] = field(default_factory=list)  # per_life_scratchpad
    mechanism_probe_current_lever: Optional[int] = None                # per_life_scratchpad
    mechanism_probe_pending_partners: Set[int] = field(default_factory=set)  # per_life_scratchpad
    mechanism_probe_fingerprints: dict = field(default_factory=dict)   # per_life_scratchpad
    mechanism_probe_press_count: int = 0                               # per_life_scratchpad
    mechanism_probe_results: dict = field(default_factory=dict)        # per_life_scratchpad

    # WO-OCD-ACTIONLOG — sidecar action-log file path. Populated lazily in
    # Virelai.choose_action from self.recorder.filename via
    # agents.recorder.derive_action_log_path. Read by the action emitter
    # sites (strategy/tier4_click.py + strategy/action_selector.py) to
    # append one record per emitted ACTION6. None when the agent has no
    # recorder attached (e.g., unit tests without the full agent harness)
    # — the emitter sites pass None to append_action_record, which silently
    # skips. PER_GAME — set once per game; reused across lives.
    action_log_path: Optional[str] = None        # persist_lives_and_levels

    # WO-OCD-CHOKE-POINT — emitter provenance tag. Each ACTION6 emitter
    # site sets this string to identify which dispatch branch produced the
    # action (e.g., "tier4_click", "tier4_click_fallback", "tier3_click",
    # "cycle_probe"). Read at the consolidated choke-point write in
    # Virelai.choose_action just before `return action`, where it is
    # written to the sidecar action-log entry's `emitter` field. PER_LIFE
    # because it describes a transient per-frame emission, not durable
    # game knowledge. None on non-ACTION6 frames or before any emitter
    # has tagged itself; the choke-point logs it as None in those cases.
    last_emitter_path: Optional[str] = None      # per_life_scratchpad

    # WO-BLUEPRINT-06 Step 6 — the captain_cursor field RETIRED here
    # (May 20, 2026). The captain's Form B layered walk holds no
    # cursor state between calls (per Blueprint Section 3.6's
    # library-as-state read protocol). Each run_captain invocation
    # walks the library fresh; completion predicates encode
    # "this attribute has accumulated enough observations to be
    # considered filled" without the captain maintaining a cursor.
    #
    # Historical (May 13, 2026 — WO-OCD-CAPTAIN-IMPLEMENTATION):
    # the field was originally named `current_tier` and tracked the
    # captain's integer cursor (values 4, 5, 6) over the dispatch
    # table keyed on `(tier, world_type, probe_type)`. The May 19
    # name collision with `TargetState.current_tier` (assessor's
    # lowest non-GREEN tier) was resolved by renaming to
    # `captain_cursor` in WO-BLUEPRINT-06 Step 2. The cursor
    # mechanism itself retired in Step 6 once the Form B walk
    # landed.

    # ------------------------------------------------------------------
    # Persistence tier mapping — authoritative source
    # ------------------------------------------------------------------
    # Every dataclass field on VirelaiContext must appear exactly once in
    # this dict.  The enumeration test in tests/test_context_persistence.py
    # enforces completeness and validity.  The harvest / reset methods below
    # read this dict to classify fields; changing a field's tier here
    # changes its reset behavior automatically.
    _PERSISTENCE_TIERS: ClassVar[Dict[str, PersistenceTier]] = {
        # --- PERSIST_LIVES_AND_LEVELS (18) ---
        "step_count":                PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "last_level_seen":            PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "win_levels":                PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "lives_used":                PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        # WO-GAME-OVER-DETECTION: sticky game-over flag — once the environment
        # ends the game it must NOT unset on life-loss/level-advance. Same tier
        # and shape as stride_probe_complete (a sticky completion bool).
        "env_terminated":            PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "visited":                   PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "novel_count":               PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "repeated_count":            PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "cell_history":              PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "state_tracker":             PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "semantic_library":          PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "nav_atlas":                 PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "stride_probe_complete":     PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "hud_mask":                  PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "action_reality_report":     PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "cycle_probe_state":         PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_sweep_state":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        "lc_only_delta_count":       PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "spawn_class_frequencies":   PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "background_class_votes":    PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        "action_log_path":           PersistenceTier.PERSIST_LIVES_AND_LEVELS,
        # WO-CC-S1: append-only capture log — whole-game record, survives
        # both life and level resets (never reset; accumulates the given).
        # WO-R1-02c ruling 3 — the ratified ontology: worldlines accumulate across
        # LIVES (a death is a Groundhog Day replay of the same world) and RESET at
        # LEVEL (a new level is a new world — a new spawn partition; ###042 in
        # level 1 has no basis for being ###042 in level 2). The weave's window is
        # the level, which is also the library's lifetime (spawn-populated once per
        # level). Was PERSIST_LIVES_AND_LEVELS, which leaked level-1 nodes into a
        # level-2 weave — asserting identity across a discontinuity.
        "frame_record_log":          PersistenceTier.PERSIST_LIVES_RESET_LEVEL,

        # --- PERSIST_LIVES_RESET_LEVEL (7) ---
        "spawn_grid":                PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "grid_scan":                 PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-XLEVEL-02a: ghost-prior snapshot captured by the §2.8.5 hook at
        # the level boundary (keyed by TypeSignature). Cleared by the reset
        # that runs immediately BEFORE the hook re-captures it — exactly the
        # level-scoped lifecycle. Consumed by WO-XLEVEL-02b.
        "xlevel_prior_snapshot":     PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "lever_memory":              PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "sweep_list":                PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "sweep_built_for_level":     PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-LGTD-01: probe_history is Dict[int, int] keyed by region_id.
        # Region_ids regenerate per level via GridScan rebuild, so probe
        # counts attached to them must reset at level advance to avoid the
        # GAP-7 stale-evidence hazard. Acknowledged at context.py:237-239
        # as a known persistence-tier gap; closed here.
        "probe_history":             PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-A.2b: physics evidence is keyed by region_id, which regenerates
        # per level — persists across lives (Groundhog Day), resets at level
        # advance (same rationale as probe_history).
        "physics_vectors":           PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "conserved_transfer_candidates": PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "physics_verdicts":          PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-B3-R1a: the retained weave window for the teardown integration
        # roster. Same tier as frame_record_log (derived from it): survives
        # lives, resets on level advance — holds THIS level's ### integration.
        "woven_worldlines":          PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-B3-R1b: the weave role verdicts retained for the roster's LIST 3.
        # Same tier/discipline as woven_worldlines (display-only, derived).
        "woven_role_verdicts":       PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_cuts":            PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_worldlines":      PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_verdicts":        PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_reached":         PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_not_reached":     PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        "coverage_hold_unreachable":     PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
        # WO-COMPOUND-ROLE-01: the independent repeated-contact confirmation
        # set. Same tier/discipline as woven_role_verdicts (display-only,
        # derived, decides nothing).
        "woven_repeated_contact":    PersistenceTier.PERSIST_LIVES_RESET_LEVEL,

        # --- PERSIST_LEVELS_RESET_LIFE (2) ---
        "actions_this_life":         PersistenceTier.PERSIST_LEVELS_RESET_LIFE,
        "last_pristine_verdict":     PersistenceTier.PERSIST_LEVELS_RESET_LIFE,

        # --- PER_LIFE_SCRATCHPAD (47) --- (count corrected from a pre-existing
        # stale "(29)" while adding the 8 weave_sweep_* entries below — the
        # block already held 33 before this WO's addition, not 29; not this
        # WO's regression, fixed in passing since it was touched anyway)
        "prev_grid":                     PersistenceTier.PER_LIFE_SCRATCHPAD,
        "frame_delta":                   PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_action_id":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_action_target":            PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_action_cell":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "target_state":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "routing_directive":             PersistenceTier.PER_LIFE_SCRATCHPAD,
        "is_death_frame":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_probe_target":             PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_probe_coord":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "ego_current_pos":               PersistenceTier.PER_LIFE_SCRATCHPAD,
        "nav_probe_target":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "nav_stuck_count":               PersistenceTier.PER_LIFE_SCRATCHPAD,
        "nav_last_nav_action":           PersistenceTier.PER_LIFE_SCRATCHPAD,
        "nav_skipped_targets":           PersistenceTier.PER_LIFE_SCRATCHPAD,
        "stride_probe_attempted":        PersistenceTier.PER_LIFE_SCRATCHPAD,
        "tier3_last_click_target":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        "tier3_consecutive_same_target": PersistenceTier.PER_LIFE_SCRATCHPAD,
        "tier3_click_skipped_targets":   PersistenceTier.PER_LIFE_SCRATCHPAD,
        "execution_plan":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "current_plan":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "ego_mask":                      PersistenceTier.PER_LIFE_SCRATCHPAD,
        "prev_ego_pos":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_probe_target_region_id":   PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_probe_target_cells":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_probe_action_kind":        PersistenceTier.PER_LIFE_SCRATCHPAD,
        "world_delta":                   PersistenceTier.PER_LIFE_SCRATCHPAD,
        "sweep_index":                   PersistenceTier.PER_LIFE_SCRATCHPAD,
        "sweep_probed":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "sweep_consecutive_inerts":      PersistenceTier.PER_LIFE_SCRATCHPAD,
        "sweep_reactive_found":          PersistenceTier.PER_LIFE_SCRATCHPAD,
        "sweep_complete":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "last_emitter_path":             PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-WEAVE-SWEEP-01 Phase 1 — distinctly named from sweep_* above
        # (Phase 0 new finding #1); all PER_LIFE_SCRATCHPAD (see the field
        # block comment for why, including weave_sweep_list, which departs
        # from the legacy sweep_list's PERSIST_LIVES_RESET_LEVEL tier).
        "weave_sweep_list":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_index":                 PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_probed":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_consecutive_inerts":    PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_complete":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_worldlines":            PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_verdicts":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_last_recompute_step":   PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-SWEEP-FORK-01
        "weave_sweep_nav_note":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-COLLIDE-GOLDEN-01
        "weave_sweep_cuts":                  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "weave_sweep_node_actions":          PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-BLOCKER-TAG-01 — renamed from `collide_drive_collided`, plus two
        "collide_drive_reached":             PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_unreachable":         PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_blockers":            PersistenceTier.PER_LIFE_SCRATCHPAD,
        "nav_opening_presses":               PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_target":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-VISUAL-TARGETS-01
        "collide_drive_target_site":         PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-HOLD-THE-PATH-01
        "collide_drive_path":                PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_path_for":            PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-OUT-OF-REACH-01
        "collide_drive_walked_out":          PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_frames":              PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_trail":               PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_outcome":             PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-CURSOR-AND-STUCK-01 — the cursor and the anchor-press count.
        "collide_drive_not_reached":         PersistenceTier.PER_LIFE_SCRATCHPAD,
        "collide_drive_unmoved_reads":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        # WO-LEVER-SUBTREE-06 — mechanism-typing probe state, all
        # PER_LIFE_SCRATCHPAD (see the field block comment for why).
        "mechanism_probe_started":           PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_lever_queue":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_current_lever":     PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_pending_partners":  PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_fingerprints":      PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_press_count":       PersistenceTier.PER_LIFE_SCRATCHPAD,
        "mechanism_probe_results":           PersistenceTier.PER_LIFE_SCRATCHPAD,
    }

    # ------------------------------------------------------------------
    # Persistence methods (WO-MINE-03 port of V3.5 lifecycle pattern)
    # ------------------------------------------------------------------

    def harvest_persistent_state(self) -> dict:
        """Return dict of PERSIST_LIVES_AND_LEVELS field values.

        Called before life-advance reset. Level-scoped fields do NOT appear
        in the dict because reset_for_new_life does not clear them — they
        survive the life reset naturally by not being reset.

        V3.5 equivalent: _harvest_persisted() in virelai_agent.py,
        operating on the _PERSISTENT_KEYS list.

        V4 divergence: vestigial in the current architecture because
        reset_for_new_life mutates self in place rather than requiring a
        round-trip. Preserved for observability / logging / future
        serialization. Returns a dict for explicitness.

        Ordering note: enrichment hooks (sync_library on the terminal
        frame, field card render) must complete BEFORE harvest.  In V4's
        current architecture sync_library is gated to NOT_FINISHED so the
        last-NOT_FINISHED frame is the final library state; the
        _fire_diagnostic (field card render) runs inside the GAME_OVER
        branch before harvest.  No terminal-frame enrichment is pending at
        the harvest site.
        """
        cls = type(self)
        return {
            name: getattr(self, name)
            for name, tier in cls._PERSISTENCE_TIERS.items()
            if tier is PersistenceTier.PERSIST_LIVES_AND_LEVELS
        }

    def reset_for_new_life(self) -> None:
        """Clear PER_LIFE_SCRATCHPAD and PERSIST_LEVELS_RESET_LIFE fields.

        Preserves PERSIST_LIVES_AND_LEVELS (survives by definition) and
        PERSIST_LIVES_RESET_LEVEL (survives because the life ended without
        a level advance; the level's state remains valid for the next life
        on the same level).

        Called from virelai.py's GAME_OVER branch in choose_action.

        V3.5 equivalent: the side-effect of _start_new_spine constructing
        fresh AdapterEnvironment, SolverSpine, etc.

        V4 divergence: V4 mutates fields in place rather than reconstructing
        objects. The end state is equivalent to V3.5's reconstruction but
        without the object-lifecycle mechanism.
        """
        cls = type(self)
        clear = (
            PersistenceTier.PER_LIFE_SCRATCHPAD,
            PersistenceTier.PERSIST_LEVELS_RESET_LIFE,
        )
        for name, tier in cls._PERSISTENCE_TIERS.items():
            if tier in clear:
                setattr(self, name, _field_default(cls, name))

    def reset_for_new_level(self) -> None:
        """Clear PERSIST_LIVES_RESET_LEVEL and PER_LIFE_SCRATCHPAD fields.

        Preserves PERSIST_LIVES_AND_LEVELS (stable physics) and
        PERSIST_LEVELS_RESET_LIFE (lifecycle counter for the life, which
        continues across level boundaries within a life).

        WO-CAMPAIGN3-PHASE1-01 (May 2, 2026): NavAtlas honors field-granular
        persistence. The whole-field tier is PERSIST_LIVES_AND_LEVELS so the
        object survives this reset, but ``nav_atlas.reset_spatial()`` is
        invoked here to clear the object's PER_LEVEL substate
        (walkable_classes, blocked_classes, visited_cells, etc.) while
        preserving PER_GAME substate (ego_class, ego_value_set, ego_spawn,
        action_dirs). See ``library/nav_atlas.py`` for the field-granular
        taxonomy and Halt 2 ratification of WO-CAMPAIGN3-PHASE1-00.

        Called from virelai.py's Observe-phase level-advance block in
        choose_action when latest_frame.levels_completed increases.

        V3.5 equivalent: _handle_click_level_transition in
        execution/click_discovery.py (FIX-A territory).
        """
        cls = type(self)
        clear = (
            PersistenceTier.PERSIST_LIVES_RESET_LEVEL,
            PersistenceTier.PER_LIFE_SCRATCHPAD,
        )
        for name, tier in cls._PERSISTENCE_TIERS.items():
            if tier in clear:
                setattr(self, name, _field_default(cls, name))
        # WO-CAMPAIGN3-PHASE1-01: clear NavAtlas PER_LEVEL substate while
        # preserving PER_GAME substate. NavAtlas object identity persists
        # because the whole-field tier is PERSIST_LIVES_AND_LEVELS.
        if self.nav_atlas is not None:
            self.nav_atlas.reset_spatial()
        # WO-LGTD-01: clear LibraryObject per-level operational-evidence
        # fields while preserving SemanticLibrary identity. Whole-field
        # tier remains PERSIST_LIVES_AND_LEVELS (line 437) because the
        # library object itself persists; only the eight per-object
        # operational-evidence fields are zeroed. See
        # SemanticLibrary.reset_objects_for_new_level for the field list
        # and the GAP-7 hazard this closes.
        if self.semantic_library is not None:
            self.semantic_library.reset_objects_for_new_level()
            # WO-LGTD-02 Phase 4: clear per-level SDKAction Entry A
            # operational-evidence fields (operational_belief,
            # operational_confidence) and refresh declarative_belief to
            # ABSENT — the first frame of the new level repopulates
            # declarative_belief from FrameData.available_actions via
            # the library_sync substrate write. Legacy fields (status,
            # test_count, delta_cells) stay PERSIST_LIVES_AND_LEVELS
            # for backward compatibility.
            self.semantic_library.reset_sdk_actions_for_new_level()


def _field_default(ctx_class: type, field_name: str) -> Any:
    """Return the declared default value for a dataclass field.

    Supports bare defaults, default_factory callables, and fields declared
    without explicit defaults (returns None in that case, matching
    dataclass semantics for Optional types).
    """
    for f in fields(ctx_class):
        if f.name == field_name:
            if f.default is not MISSING:
                return f.default
            if f.default_factory is not MISSING:
                return f.default_factory()
            return None
    raise KeyError(
        f"Field {field_name!r} not found on {ctx_class.__name__}"
    )

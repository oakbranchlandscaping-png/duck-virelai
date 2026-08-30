"""
The captain: a Form B layered walker over the semantic library per
Blueprint Section 3.3.

On each `run_captain` call, the captain walks `library.objects` in
canonical region order (Object List layer); for each slot, descends
the imperative category priority order Ego → Lever → Gate → Reactive
→ Static → Counter (Category Priority layer per Section 3.4.2);
evaluates declarative `PrerequisitePredicate` declarations via
`is_actionable` and `CompletionPredicate` declarations via `is_filled`
(per Section 3.4.1 + 3.4.3); and dispatches the first actionable +
unfilled attribute it encounters.

The dispatch table is keyed on `(world_type, AttributeType)` per
Section 3.5. The dispatch primitive is looked up by this key and
called with `(context, library, region_id)` to produce the frame's
emission.

The captain holds NO state between calls (Section 3.6 library-as-state
read protocol). All multi-frame state lives on the library or on
`context` fields owned by substrate. Each call walks the library
fresh; completion predicates encode "this attribute has accumulated
enough observations to be considered filled" without the captain
maintaining a cursor.

Filed under WO-BLUEPRINT-06 (May 20, 2026). Replaces the cursor-based
captain (WO-OCD-CAPTAIN-IMPLEMENTATION May 13, 2026) which dispatched
on `(tier, world_type, probe_type)` keys with `context.current_tier`
(renamed to `captain_cursor` and now retired). Per Captain Migration
Path Section F: the canonical-order walk pattern survives unchanged;
the integer cursor mechanism retires; the dispatch table re-keys;
the eligibility predicates become declarative.

Sub-Phase 2 scope (this WO):
  - Object List walk (Section 3.3 Level 2) ✓
  - Category Priority within Slot (Section 3.3 Level 3 + Section 3.4.2) ✓
  - PrerequisitePredicate + CompletionPredicate evaluation ✓
  - Dispatch table re-keyed to (world_type, AttributeType) ✓

Deferred to Sub-Phase 4 per Director Section G rulings:
  - Foundation walk (Section 3.3 Level 1)
  - NAV-side dispatch primitives (Section 3.5 NAV cells)
  - Out-of-tape behavior (Section 3.7 + three-case classifier)
  - Variant Catalog descent (Section 3.3 Level 4)

Sovereignty: stdlib + arcengine (GameAction) + virelai_v4.strategy
(dispatch primitives) + virelai_v4.contracts (AttributeType +
PrerequisitePredicate + CompletionPredicate) + virelai_v4.library
(predicate_evaluators).

Public API:
    run_captain(context, library) -> Optional[GameAction]
    captain_is_active(context, library) -> bool
    captain_preconditions_met(target_state) -> bool
    TIER_K_BUDGET: Dict[int, int]   # retained as backstop only (Section 1.7)
    DISPATCH_TABLE: Dict[Tuple[str, AttributeType], Callable]
"""

from __future__ import annotations

from typing import Any, Callable, Dict, FrozenSet, Optional, Sequence, Tuple, TYPE_CHECKING

# SOV-01 Step 1: captain_legacy_fallback accepts a caller-supplied callable
# so captain.py requires no import of virelai.py or action_selector.py
# (both would create circular deps — virelai.py already imports captain.py;
# action_selector.py imports captain_is_active). The callable pattern is the
# F0.2 structural adaptation: _dispatch_action is a Virelai instance method,
# not a standalone importable function.

from virelai_v4.contracts.attribute_type import AttributeType
from virelai_v4.contracts.completion_predicate import CompletionPredicate
from virelai_v4.contracts.prerequisite_predicate import PrerequisitePredicate
from virelai_v4.library.predicate_evaluators import is_actionable, is_filled

if TYPE_CHECKING:
    from arcengine import GameAction
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary
    from virelai_v4.targeting.assessor import TargetState


# ---------------------------------------------------------------------------
# K-per-tier budget — RETAINED AS BACKSTOP ONLY per Blueprint Section 1.7.
# The K-budget no longer drives dispatch; CompletionPredicate evaluations
# determine when an attribute is filled. The constant survives for
# documentation continuity with the Per-Object Investigation Budgets
# Amendment (May 13, 2026) and as a future hard cap if any completion
# predicate evaluation produces unbounded probing.
# ---------------------------------------------------------------------------
TIER_K_BUDGET: Dict[int, int] = {
    4: 1,   # Coverage backstop — FIRST_TOUCH_PROBE
    5: 4,   # Cycle probe backstop — CYCLE_PERIOD_DETECTION_PROBE
    6: 1,   # Causal mapping backstop placeholder
}


# ---------------------------------------------------------------------------
# Category priority — the captain's only piece of strategic state per
# Blueprint Section 3.4.2. The imperative priority order is fixed in code
# (not schema-encoded). Rationale:
#   - Ego first: agent identification supports all subsequent investigation
#   - Lever before Gate: gates are surfaced through lever investigation
#   - Reactive after Lever+Gate: reactive characterization is downstream
#   - Static deferred: passive coverage-map accumulation
#   - Counter last: rarely opens on object-list slots
# ---------------------------------------------------------------------------
_PROBE_CATEGORY_PRIORITY: Tuple[str, ...] = (
    "ego",
    "lever",
    # DD gap-5: "gate" retired from the walk — it was never dispatched
    # (_attribute_declarations_for returns None for it); gate is a lever-subtree
    # frontier child, not a floor category.
    "reactive",
    "static",
    "counter",
    # WO-EFFECT-WALK-HOOK (WO2): the Tier-5 effect-characterization band.
    # Last in priority and gated on ALL_LEVERS_TYPED, so it opens only after
    # lever typing (Tier 4) is globally GREEN.
    "lever_effect",
)


# ---------------------------------------------------------------------------
# WO-PROBE-R1 — the foundational-depth ceiling.
#
# The Pull (the captain's walk) probes to FOUNDATIONAL depth only: it
# first-touches each object (role classification via accumulated deltas) and
# stops there. Sub-tree categories — lever-typing (CYCLE_PERIOD_DETECTION_PROBE)
# and effect characterization (LEVER_EFFECT_CHARACTERIZATION) — are excluded
# from the walk's actionable set at foundational scope. When every object is
# first-touched and no foundational question remains, the walk returns silent
# (coverage-complete); that silence is the handoff that fires the Push on its
# existing trigger.
#
# This is a CEILING, not a wall: the sub-tree probe machinery stays intact in
# the tree (DISPATCH_TABLE entries, _attribute_declarations_for branches, the
# probe primitives).
#
# IMPORTANT (WO-EFFECT-01.1 reconciliation): _SUBTREE_CATEGORIES gates PASS-1
# ONLY — it is subtracted from _PROBE_CATEGORY_PRIORITY by
# _foundational_actionable_categories(). The later passes (pass-2 typing, pass-3
# effect) walk THEIR OWN category tuples directly via _walk_over_categories and
# do NOT consult _SUBTREE_CATEGORIES. So a sub-tree category is admitted to the
# walk by giving it a PASS, not by removing it from this fence — and it MUST stay
# in this fence to remain excluded from the foundational pass. Removing
# lever_effect here would LEAK it into pass-1, dispatching effect BEFORE typing
# (verified by staging test A/B/C/D in test_effect_terminal.py).
# ---------------------------------------------------------------------------
_SUBTREE_CATEGORIES: FrozenSet[str] = frozenset({"lever", "lever_effect"})

# WO-DIVE-01 Build 1/2 — the deepening dive's second-pass category set (pass-2).
# Opens LEVER TYPING ("lever") after foundational silence. The "lever"
# declaration's prereq SLOT_IS_LEVER_LOCKED admits only confirmed levers; its
# completion LEVER_TYPED is a permanent fill, so each lever types once and the
# dive goes silent again (staged termination). (lever_effect is NOT in this pass
# — it is pass-3 below, re-admitted by WO-EFFECT-01, not fenced from the walk.)
_DEEPENING_DIVE_CATEGORIES: Tuple[str, ...] = ("lever",)

# WO-EFFECT-01 — the effect band's pass-3 category set. Opens after typing fills
# (pass-2 silent). Pass-3 walks "lever_effect" DIRECTLY via _walk_over_categories
# (around _SUBTREE_CATEGORIES, which gates pass-1 only); lever_effect stays in
# _SUBTREE_CATEGORIES solely to keep it out of the foundational pass. The
# declaration gates on SLOT_IS_LEVER_TYPED with the LEVER_EFFECT_CHARACTERIZED
# terminal — admits only typed levers (incl. UNDETERMINED remotes), fills
# permanently, never round-robining.
_EFFECT_DIVE_CATEGORIES: Tuple[str, ...] = ("lever_effect",)


def _foundational_actionable_categories() -> Tuple[str, ...]:
    """The walk's actionable category set under the foundational-depth ceiling:
    `_PROBE_CATEGORY_PRIORITY` minus the sub-tree categories. Single
    responsibility — return the categories the Pull may probe at foundational
    scope, in priority order. A maturation campaign lifts the ceiling by
    removing its category from `_SUBTREE_CATEGORIES`."""
    return tuple(c for c in _PROBE_CATEGORY_PRIORITY if c not in _SUBTREE_CATEGORIES)


# ---------------------------------------------------------------------------
# Dispatch primitives — each takes (context, library, region_id) and
# returns the GameAction the captain should emit for that slot. Lazy
# imports inside the wrapper functions keep this module's top-level
# import surface small.
# ---------------------------------------------------------------------------

def _dispatch_first_touch_click(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    region_id: int,
) -> "GameAction":
    """CLICK FIRST_TOUCH_PROBE primitive: one ACTION6 at the region's
    centroid. The K=1 Coverage pass."""
    from virelai_v4.strategy.tier4_click import emit_click_at_region
    return emit_click_at_region(context, library, region_id)


def _cycle_probe_mode_a(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    region_id: int,
) -> Optional["GameAction"]:
    """CLICK CYCLE_PERIOD_DETECTION_PROBE primitive (Mode A — Form B dispatch):
    dispatch the cycle probe state machine at a confirmed lever.

    SOV-02 Step 2: renamed from `_dispatch_cycle_probe_click` to
    `_cycle_probe_mode_a`.  Backward-compat alias preserved below.
    Library-read: verifies cycle_probe_state target matches region_id;
    reads target_obj from library.objects[region_id].

    INVENT #3 anchor — the May 16 variable-K cycle probe ship. Per
    Apex Q4 adjudication, UNKNOWN is treated as terminal for advancement.
    The state machine writes `cycle_length` on completion; the Form B
    walk's CYCLE_RETURN_OBSERVED completion predicate reads
    `cycle_length > 0` to determine fill status (per
    library/predicate_evaluators.py and WO-BLUEPRINT-05).

    The dispatcher delegates entirely to the cycle probe state machine's
    public interface. The dispatcher's responsibilities are limited to:
      1. Initializing cycle_probe_state when starting a new lever
      2. Forwarding the per-frame run_cycle_probe_step call
      3. Returning whatever the state machine returns
    """
    target_obj = library.objects[region_id]

    state = context.cycle_probe_state
    if state is None or state.target_object_region_id != region_id:
        if context.prev_grid is None:
            return None
        from virelai_v4.library.cycle_probe_invocation import (
            _initialize_cycle_probe_state,
        )
        context.cycle_probe_state = _initialize_cycle_probe_state(
            target_obj=target_obj,
            context=context,
            library=library,
            spawn_frame=context.prev_grid,
        )
        # WO-CP1-FIX-B: typed refusal — an empty-cells target is rejected at
        # init (logged there). Fall through to the legacy/typed-gap dispatch
        # rather than probing a (0,0) phantom.
        if context.cycle_probe_state is None:
            return None

    # WO-CP1-FIX-B (observability): record the probe target rid every Mode-A
    # dispatch frame so the canary's actions sidecar carries it (WO-DIAG-CP1
    # found cycle rows with target_region_id=None).
    context.last_probe_target_region_id = region_id

    # WO-LGTD-02 Phase 5 (6.3 / GAP-9): replace hardcoded `[6]` singleton
    # with a library-grounded read. The Affordance Layer's Entry A
    # (declarative_belief on sdk_actions) is the canonical declared-set
    # — substrate refreshes it every frame from FrameData.available_actions
    # via library_sync.refresh_affordance_declarative_belief.
    #
    # The previous hardcoded `[6]` was a fictitious singleton: it
    # asserted ACTION6 declared without checking. Under the Affordance
    # Layer, the captain's DISPATCH_TABLE gate (4.3.3) already verifies
    # the probe is in available_probes() — which itself checks ACTION6
    # is DECLARED — so reaching this dispatcher implies ACTION6 is
    # declared. The replacement reads the full declared set from the
    # library, which the cycle probe state machine may use for any
    # additional checks downstream.
    from virelai_v4.library.affordance_belief import DeclarativeBelief
    from virelai_v4.library.cycle_probe import run_cycle_probe_step
    declared_actions = [
        aid for aid, sdk in library.sdk_actions.items()
        if sdk.declarative_belief == DeclarativeBelief.DECLARED
    ]
    return run_cycle_probe_step(
        context=context,
        library=library,
        available_actions=declared_actions,
        latest_frame=context.prev_grid,
    )


def _dispatch_lever_effect_probe(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    region_id: int,
) -> "GameAction":
    """CLICK LEVER_EFFECT_CHARACTERIZATION primitive (WO-EFFECT-WALK-HOOK, WO2):
    one ACTION6 at the typed lever's centroid to drive a fresh effect
    observation. Reuses the captain's existing click primitive
    (tier4_click.emit_click_at_region) — Mine-Then-Reuse, no new emission path.

    Attribution: run_captain writes context.last_probe_target_region_id =
    region_id on the non-None return (captain.py dispatch site), so the
    next-frame substrate Path 4 records the LeverEffect on THIS lever. The
    primitive itself sets no attribution (same contract as the first-touch and
    cycle dispatchers)."""
    from virelai_v4.strategy.tier4_click import emit_click_at_region
    return emit_click_at_region(context, library, region_id)


# ---------------------------------------------------------------------------
# Dispatch table — keyed on (world_type, AttributeType) per Section 3.5.
#
# The two V4-current entries:
#   ("CLICK", AttributeType.FIRST_TOUCH_PROBE) — Coverage pass dispatch
#   ("CLICK", AttributeType.CYCLE_PERIOD_DETECTION_PROBE) — Cycle probe
#
# NAV-side entries are deferred to Sub-Phase 4 per Director Section G
# Decision 3. Absence of a key for a (world_type, AttributeType)
# combination means the captain does not own that cell; the Form B
# walk skips it; the legacy `_dispatch_action` routing tree handles
# any frame the captain doesn't claim.
# ---------------------------------------------------------------------------
DISPATCH_TABLE: Dict[Tuple[str, AttributeType], Callable] = {
    ("CLICK", AttributeType.FIRST_TOUCH_PROBE): _dispatch_first_touch_click,
    ("CLICK", AttributeType.CYCLE_PERIOD_DETECTION_PROBE): _cycle_probe_mode_a,
    # WO-EFFECT-WALK-HOOK (WO2): captain-driven effect-characterization press.
    ("CLICK", AttributeType.LEVER_EFFECT_CHARACTERIZATION):
        _dispatch_lever_effect_probe,
}


# WO-LGTD-02 Phase 4 (4.3.3): map captain AttributeType to Probe Catalog
# probe_name for the Affordance Layer read. The captain consults
# available_probes() before dispatching from DISPATCH_TABLE; a candidate
# whose mapped probe is not in the view falls through to the legacy
# dispatcher rather than firing. The map is the captain's local view of
# the catalog; AttributeType lives on the captain, probe_name lives on
# the catalog, this map bridges them.
ATTRIBUTE_TYPE_TO_PROBE_NAME: Dict[AttributeType, str] = {
    AttributeType.FIRST_TOUCH_PROBE: "click_probe",
    AttributeType.CYCLE_PERIOD_DETECTION_PROBE: "cycle_probe",
    # WO-EFFECT-DISPATCH-FIX-2 (Option B, June 11 2026): the effect band maps to
    # a DEDICATED catalog probe ("effect_probe") whose precondition
    # ("lever_confirmed") HOLDS in the post-coverage effect phase. This restores
    # the affordance gate with a phase-correct probe (satisfying the dispatch-
    # coverage invariant), superseding WO2's reuse of "click_probe" — whose
    # "unprobed_target_available" precondition is False post-coverage and nulled
    # the dispatch (DIAG-DISPATCH-WO2). The probe-name discipline (amended
    # Substrate-to-Dispatch pattern): reuse a probe_name only when its
    # preconditions hold in the new band's phase; here we author a new one.
    AttributeType.LEVER_EFFECT_CHARACTERIZATION: "effect_probe",
}


# SOV-02 Step 2: backward-compat alias — existing tests that reference
# `_dispatch_cycle_probe_click` by name continue to pass.
_dispatch_cycle_probe_click = _cycle_probe_mode_a


# ---------------------------------------------------------------------------
# Attribute declaration helper — maps (Slot, category) to the
# AttributeType + prerequisite + completion declarations for that
# (slot, category) combination.
#
# Per Captain Migration Path F.3, Sub-Phase 4+ will move these
# declarations onto the Slot itself as per-attribute fields. For WO-06
# the helper holds them as a static dispatch table over the V4-current
# dispatch surface (FIRST_TOUCH_PROBE for static; CYCLE_PERIOD_DETECTION_PROBE
# for lever).
#
# Returns None when the (slot, category) combination has no dispatch
# primitive in this Sub-Phase (e.g., ego/gate/reactive/counter — all
# deferred). The Form B walk skips combinations that return None.
# ---------------------------------------------------------------------------
def _attribute_declarations_for(
    slot: "LibraryObject",
    category: str,
) -> Optional[Tuple[
    Sequence[Tuple[PrerequisitePredicate, Dict[str, Any]]],
    Sequence[Tuple[CompletionPredicate, Dict[str, Any]]],
    AttributeType,
]]:
    """Return (prerequisites, completions, attribute_type) for a
    (slot, category) combination, or None if no Sub-Phase 2 dispatch
    primitive is wired for that combination.

    Sub-Phase 2 wiring covers two cells:

      ("CLICK", "lever") → CYCLE_PERIOD_DETECTION_PROBE
          Prerequisite: SLOT_IS_LEVER_LOCKED (Section 2 v1.1 amendment)
          Completion:   LEVER_TYPED (reads slot.lever_mechanism is not None
                        — Section 2 v1.2 amendment, May 21, 2026; replaced
                        prior CYCLE_RETURN_OBSERVED which excluded saturation)

      ("CLICK", "static") → FIRST_TOUCH_PROBE
          Prerequisite: ALWAYS_TRUE (the Coverage pass is unconditional)
          Completion:   DISTINCT_PROBES_AT_LEAST(n=1) (probed at least once)

    All other (slot, category) combinations return None per Sub-Phase 4
    deferrals (Director Section G).

    Section 2 v1.2 amendment note (WO-BLUEPRINT-06-LEVER-TYPED, May 21, 2026):
    The lever category's completion predicate migrated from
    CYCLE_RETURN_OBSERVED (`cycle_length > 0`) to LEVER_TYPED
    (`lever_mechanism is not None`). The earlier predicate excluded the
    SATURATED mechanism (saturation commits lever_mechanism = SATURATED
    but does not set cycle_length), causing the May 21 vc33 canary
    regression where R4 saturated and the Form B walk re-dispatched
    cycle probe on R4 forever without ever advancing to R5. LEVER_TYPED
    captures any committed mechanism (cycle, toggle, directional, global,
    one_shot, gated, saturated, unknown); the cursor-era equivalence the
    WO-BLUEPRINT-06 migration retired without replacement is restored
    by this amendment.
    """
    if category == "lever":
        return (
            ((PrerequisitePredicate.SLOT_IS_LEVER_LOCKED, {}),),
            ((CompletionPredicate.LEVER_TYPED, {}),),
            AttributeType.CYCLE_PERIOD_DETECTION_PROBE,
        )

    if category == "static":
        return (
            ((PrerequisitePredicate.ALWAYS_TRUE, {}),),
            ((CompletionPredicate.DISTINCT_PROBES_AT_LEAST, {"n": 1}),),
            AttributeType.FIRST_TOUCH_PROBE,
        )

    # WO-EFFECT-WALK-HOOK (WO2): the Tier-5 effect-characterization band.
    # Prerequisite: this slot is a confirmed lever (SLOT_IS_LEVER_LOCKED) AND
    # this lever's own B2 is cleared (SLOT_IS_LEVER_TYPED — per-lever typing).
    # Completion: LEVER_EFFECT_NOT_LEAST_OBSERVED — filled only when this lever
    # is not the global least-characterized, so the captain always targets the
    # least-observed typed lever and never idles (no self-cap; Director ruling
    # June 11 2026). Non-lever slots fail SLOT_IS_LEVER_LOCKED and drop out.
    #
    # WO-E6 (Per-Lever B3 Dispatch): the gate was ALL_LEVERS_TYPED (global —
    # B3 opened for every lever only once EVERY confirmed lever typed, leaving
    # a B2-cleared lever un-dispatched-at-B3 while any other lever stayed
    # untyped — the WO-E4 display/dispatch divergence). It is now
    # SLOT_IS_LEVER_TYPED: this lever's B3 opens the moment ITS B2 clears,
    # matching the display's per-lever B3 granularity. The within-B3 loop guard
    # (LEVER_EFFECT_NOT_LEAST_OBSERVED round-robin) is unchanged and still
    # bounds re-probing. Director-ratified the log-score signal (2026-06-28)
    # over a strict obj.saturated gate, which would have regressed non-saturated
    # typed levers out of B3.
    if category == "lever_effect":
        # WO-EFFECT-01: completion swapped from the LEVER_EFFECT_NOT_LEAST_OBSERVED
        # round-robin (deliberately non-terminating; the x129 re-arm) to the
        # LEVER_EFFECT_CHARACTERIZED terminal (per-region agreement OR bounded
        # exhaustion — permanent-fill). The prereq gate is unchanged: only
        # confirmed, typed levers (incl. UNDETERMINED remotes) reach the band.
        return (
            ((PrerequisitePredicate.SLOT_IS_LEVER_LOCKED, {}),
             (PrerequisitePredicate.SLOT_IS_LEVER_TYPED, {})),
            ((CompletionPredicate.LEVER_EFFECT_CHARACTERIZED, {}),),
            AttributeType.LEVER_EFFECT_CHARACTERIZATION,
        )

    # ego / gate / reactive / counter — Sub-Phase 4+ wiring per Director
    # Section G Decisions 2 + 3. The Form B walk skips these.
    return None


def _is_foundation_slot(slot: "LibraryObject") -> bool:
    """§4.3 (WO-FOUNDATION-MIGRATION-1): True iff this slot's classified
    category is a foundation role — EGO or COUNTER (the categorical
    classification the field card renders, written by the Substrate in
    sync_library). Foundation slots are excluded from lever discovery/typing
    and the first-touch coverage pass; their foundation attributes are
    dispatched by the foundation walk (-2).

    WO_CAPTAIN_READS_TAPE D4: reads the DERIVED foundation role (the nested
    taxonomy read off the captain's store), not the Store-B categorical
    `slot.role`. A one-sided categorical (an EGO/COUNTER written without its
    axis, or one whose axis was wiped) no longer gates dispatch — selection acts
    on the belief the evidence supports, not an unbacked commitment. Pure read.
    """
    from virelai_v4.library.library_roles import LibraryRole
    from virelai_v4.library.nested_read import derived_role
    return derived_role(slot) in (LibraryRole.EGO.value, LibraryRole.COUNTER.value)


# ---------------------------------------------------------------------------
# Form B walk — Section 3.3 Object List + Category Priority layers.
# ---------------------------------------------------------------------------

def _form_b_walk(
    library: "SemanticLibrary",
) -> Optional[Tuple["LibraryObject", AttributeType, int]]:
    """Walk the library per Blueprint Section 3.3 Form B layered traversal.

    For Sub-Phase 2, the walk operates at Levels 2 + 3:
      Level 2 (Object List): iterate library.objects in canonical
          region order (sorted by region_id).
      Level 3 (Category Priority): for each Slot, descend
          _PROBE_CATEGORY_PRIORITY (Ego → Lever → Gate → Reactive →
          Static → Counter); for each category, look up its dispatch
          attribute via _attribute_declarations_for; if actionable and
          unfilled, this is the target.

    Returns the first actionable + unfilled attribute encountered, as
    (slot, attribute_type, region_id). Returns None when no actionable +
    unfilled attribute exists in the walk.

    Level 1 (Foundation) is deferred to Sub-Phase 4 per Director
    Section G Decision 2. Level 4 (Variant Catalog) is deferred per
    Section G Decision 1 — variant catalogs land in Section 4+.
    """
    return compute_captain_target(library)


def compute_captain_target(
    library: "SemanticLibrary",
) -> Optional[Tuple["LibraryObject", AttributeType, int]]:
    """The captain_target derived read (WO-LGTD-AGG, north-star §3.1).

    Pure per-frame read: enumerate every eligible open question under the SAME
    per-slot belief reads as before (declarations, is_actionable, is_filled,
    the -1 §4.3 foundation guard), then order them by the library-grounded
    priority aggregation (library/priority_aggregation.py: V3.5 probe_scorer
    shape on the BBA axes, region_id tiebreak) and return the top — "the
    highest-priority open question is X for slot Y" — or None when no
    library-grounded target exists. The Form B walk consumes THIS read, and
    the field card renders THIS read: the instrument cannot diverge from
    dispatch. No side effects; deterministic given Library state.
    """
    from virelai_v4.library.priority_aggregation import top_candidate

    # WO-DIVE-01 Build 1/2 — TWO-PASS STAGING (the deepening dive).
    # Pass 1: the foundational sweep (unchanged behavior). It runs to silence —
    # returns candidates while any object has an open foundational attribute.
    candidates = _walk_over_categories(
        library, _foundational_actionable_categories()
    )
    if candidates:
        return top_candidate(candidates)
    # Pass 2: foundational coverage is COMPLETE — pass 1 produced no open
    # attribute across the whole roster (the emergent silence: the walk returns
    # nothing only when every object is foundationally filled). Only now open
    # the deepening dive on proposed levers via the "lever" typing category.
    # A confirmed-lever gate is intrinsic to the declaration: SLOT_IS_LEVER_LOCKED
    # admits only lever-locked slots, LEVER_TYPED excludes already-typed ones.
    # No proposed lever ⇒ dive_candidates == [] ⇒ top_candidate(None) ⇒ Pull
    # silent, and the keystone's needs_reinvestigation re-arms coverage on a
    # genuine state change (the resweep), bounded by the probe-count penalty. We
    # deliberately do NOT force a re-ask here — that is the retired flat
    # never-idles stall.
    dive_candidates = _walk_over_categories(library, _DEEPENING_DIVE_CATEGORIES)
    if dive_candidates:
        return top_candidate(dive_candidates)
    # Pass 3 (WO-EFFECT-01): lever typing is COMPLETE (pass 2 silent) — open the
    # effect band on typed levers via "lever_effect". The declaration gates on
    # SLOT_IS_LEVER_TYPED (admits only typed levers, incl. vc33's UNDETERMINED
    # remotes) and completes on LEVER_EFFECT_CHARACTERIZED (per-region agreement
    # OR bounded exhaustion — permanent-fill). So the band terminates and goes
    # silent instead of round-robining (the x129 fence). No typed-uncharacterized
    # lever ⇒ [] ⇒ None ⇒ silence; the keystone handles any resweep.
    effect_candidates = _walk_over_categories(library, _EFFECT_DIVE_CATEGORIES)
    return top_candidate(effect_candidates)


def _walk_over_categories(
    library: "SemanticLibrary",
    categories: Tuple[str, ...],
) -> "List[Tuple[LibraryObject, AttributeType, int]]":
    """WO-DIVE-01 — the per-slot / per-category open-question collection,
    extracted VERBATIM from compute_captain_target so the dive's second pass
    reuses the SAME per-slot belief reads (declarations, is_actionable,
    is_filled, the foundation-slot guard) as the foundational pass. Extract-
    then-call: the walk logic is unchanged; only the category set varies between
    passes. Returns the list of (slot, attribute_type, region_id) candidates.
    """
    candidates = []
    for region_id in sorted(library.objects.keys()):
        slot = library.objects[region_id]
        for category in categories:
            # WO-FOUNDATION-MIGRATION-1 (§4.3): foundation-identified slots
            # (ego, counter) are EXCLUDED from lever discovery/typing and
            # the first-touch coverage pass (the WO-CP1-FIX-B counter-
            # pollution root). Their foundation attributes dispatch in -2.
            if (category in ("lever", "static", "lever_effect")
                    and _is_foundation_slot(slot)):
                continue
            decl = _attribute_declarations_for(slot, category)
            if decl is None:
                continue
            prereqs, completions, attribute_type = decl
            if not is_actionable(prereqs, library, slot=slot):
                continue
            if is_filled(completions, library, slot=slot):
                continue
            candidates.append((slot, attribute_type, region_id))
            break  # one open attribute per slot (category priority within slot)
    return candidates


# ---------------------------------------------------------------------------
# Legacy tool name registry — SOV-02 Step 3.
#
# ---------------------------------------------------------------------------
# Captain legacy fallback — SOV-01 Step 1; SOV-02 Step 3 (provenance).
# ---------------------------------------------------------------------------

# SOV-02 Step 3: original one-liner preserved as _v1 for reference.
# The new captain_legacy_fallback adds per-tool provenance on top.
def _captain_legacy_fallback_v1(
    library: "SemanticLibrary",
    context: "VirelaiContext",
    dispatch_fn: "Callable[[], Optional[GameAction]]",
) -> Optional["GameAction"]:
    """Original SOV-01 fallback (reference copy — not called in production)."""
    return dispatch_fn()


def captain_legacy_fallback(
    library: "SemanticLibrary",
    context: "VirelaiContext",
    dispatch_fn: "Callable[[], Optional[GameAction]]",
) -> Optional["GameAction"]:
    """Captain-invoked fallback when Form B walk produces no target.

    WO-SOV03-CLEANUP §1 (supersedes the SOV-02 Step 3 guess): provenance is
    the FACTUAL ``context.last_emitter_path`` the dispatch path itself wrote;
    this function no longer predicts a tool name. An untagged path records
    "captain_legacy_fallback" (the literal fact). dispatch_fn() still owns
    routing — zero behavior change to dispatch.

    Structural invariants preserved:
      - dispatch_fn() is the sole behavioral path (no circular import)
      - provenance written only when action is non-None (SOV-01 Step 3 fix)
      - callable parameter pattern unchanged (no new imports in captain.py)

    F0.2 adaptation note: dispatch_fn is a Virelai instance method wrapper
    (lambda) — captain.py requires no import of virelai.py or
    action_selector.py.  The callable parameter achieves the identical
    architectural outcome as direct dispatch, without circular dependency.
    """
    action = dispatch_fn()
    if action is not None and getattr(context, "last_emitter_path", None) is None:
        # WO-SOV03-CLEANUP §1 (audit C-1): the emitting site's FACTUAL tag is
        # the provenance ("typed_gap" / "tier1" / "random_fallback" /
        # "cycle_probe" / "captain") — recorded POST-dispatch. Only a path
        # that left no tag records the literal fallback fact below; never a
        # guessed tool name (the old pre-dispatch heuristic stamped
        # `captain_via_cycle_probe_tool` over the (0,0) burn and steered
        # FIX-B to the wrong layer).
        context.last_emitter_path = "captain_legacy_fallback"
    return action


# ---------------------------------------------------------------------------
# Captain entry point.
# ---------------------------------------------------------------------------

def run_captain(
    context: "VirelaiContext",
    library: Optional["SemanticLibrary"],
    *,
    legacy_dispatch_fn: Optional["Callable[[], Optional[GameAction]]"] = None,
) -> Optional["GameAction"]:
    """The Form B walker entry point.

    SOV-01 Step 1: accepts an optional `legacy_dispatch_fn` callable.
    When provided (production path, virelai.py passes it), the captain
    owns ALL NOT_FINISHED frames after preconditions are met — Form B
    targets dispatch via primitive; everything else dispatches via
    captain_legacy_fallback. When absent (unit-test path, old call
    sites), behavior is identical to the pre-SOV-01 contract.

    Per Section 3.3, this is invoked once per frame. The captain walks
    the library, finds the first actionable + unfilled attribute, looks
    up its dispatch primitive in DISPATCH_TABLE under
    (library.header.world_type, attribute_type), and invokes the
    primitive. Returns the primitive's GameAction or None.

    Returns None when:
      - library is None (very early frames before sync_library)
      - the walk finds no actionable + unfilled attribute AND
        legacy_dispatch_fn is None (unit-test path; production path
        always has legacy_dispatch_fn and routes through fallback)
      - the walk finds a target whose (world_type, AttributeType) is
        not in DISPATCH_TABLE AND legacy_dispatch_fn is None
      - dispatch returns None AND legacy_dispatch_fn is None

    Captain's None return (when legacy_dispatch_fn is None) carries one
    semantic: Form B walk produced no target or no wired primitive.
    In production, this semantic never surfaces — the captain always
    produces an action via Form B or via captain_legacy_fallback.

    Side effects on dispatch (provenance — NOTE: Step 3 fixes the
    unconditional write; at Step 1 the write remains as-was):
      - context.last_probe_target_region_id = region_id (substrate
        attribution channel; read by probe_outcome_processor +
        library_sync + observability_choke_point)
      - context.last_emitter_path = "captain" (provenance tag)

    The captain holds no cursor state between calls. Each invocation
    walks the library fresh per Section 3.6's library-as-state read
    protocol.
    """
    if library is None:
        return None

    # ── WO-STEP-01 §1: in-flight probe steps to termination ─────────────
    # An ACTIVE cycle probe steps every frame, independent of the walk's
    # per-frame eligibility (FRICTION-CYCLEPROBE-ORPHAN): the revoke can
    # eject a mid-probe slot below LOCKED, which stops the walk
    # re-dispatching the typing cell — and Mode B, the legacy per-frame
    # stepper, was retired by SOV-03 without this role being absorbed.
    # The vc33 result was an orphaned probe (state non-None to GAME_OVER)
    # behind a tier4 (0,0) burn. Blueprint §5.1: one probe in flight runs
    # to termination. Non-terminal → return the press (captain provenance).
    # Terminal → run_cycle_probe_step returns None with state cleared
    # (cycle_probe.py:397/419/504) and the walk runs on this same frame.
    if context is not None and getattr(context, "cycle_probe_state", None) is not None:
        from virelai_v4.library.affordance_belief import DeclarativeBelief
        from virelai_v4.library.cycle_probe import run_cycle_probe_step
        _declared = [
            aid for aid, sdk in library.sdk_actions.items()
            if sdk.declarative_belief == DeclarativeBelief.DECLARED
        ]
        _step_action = run_cycle_probe_step(
            context=context,
            library=library,
            available_actions=_declared,
            latest_frame=context.prev_grid,
        )
        if _step_action is not None:
            # A stepped press is captain work, not a fallback.
            context.last_emitter_path = "captain"
            return _step_action

    target = _form_b_walk(library)

    if target is not None:
        slot, attribute_type, region_id = target
        world_type = library.header.world_type
        dispatch_key = (world_type, attribute_type)
        dispatch = DISPATCH_TABLE.get(dispatch_key)
        if dispatch is not None:
            # WO-LGTD-02 Phase 4 (4.3.3): Affordance Layer read. Consult
            # available_probes() before dispatching. A candidate whose
            # mapped probe is not currently available (required actions
            # not all DECLARED, or operational preconditions not met)
            # falls through to legacy_dispatch_fn rather than firing —
            # the captain dispatches library-grounded.
            #
            # AttributeTypes outside ATTRIBUTE_TYPE_TO_PROBE_NAME (none
            # currently; map covers both DISPATCH_TABLE cells) dispatch
            # unfiltered — the captain cannot ask the library about an
            # attribute that has no catalog mapping.
            probe_name = ATTRIBUTE_TYPE_TO_PROBE_NAME.get(attribute_type)
            if probe_name is not None:
                available_names = {p.probe_name for p in library.available_probes()}
                if probe_name not in available_names:
                    # Probe unavailable — skip captain dispatch; fall
                    # through to legacy_dispatch_fn below.
                    dispatch = None
        if dispatch is not None:
            action = dispatch(context, library, region_id)
            if action is not None:
                # SOV-01 Step 3 fix: provenance written only when dispatch
                # confirms a non-None action. Pre-fix: both writes were
                # unconditional, contaminating provenance on cycle-probe
                # commit frames (dispatch returns None) and any other
                # primitive that can return None.
                context.last_probe_target_region_id = region_id
                context.last_emitter_path = "captain"
                return action
            # dispatch returned None (e.g. cycle probe commit step) —
            # fall through to legacy_dispatch_fn if available.
        # No wired primitive for this (world_type, attribute_type) —
        # fall through to legacy_dispatch_fn if available.

    # Form B has no target OR dispatch returned None OR no wired primitive.
    # Route through captain_legacy_fallback when caller supplied one.
    if legacy_dispatch_fn is not None:
        # SOV-02 Step 3: provenance now owned by captain_legacy_fallback
        # (writes context.last_emitter_path = f"captain_via_{tool_name}").
        # The run_captain "captain" write that was here pre-SOV-02 has been
        # removed; captain_legacy_fallback is the sole provenance authority
        # for fallback frames (still gated on non-None action per SOV-01
        # Step 3 fix — the gate moved into captain_legacy_fallback).
        return captain_legacy_fallback(library, context, legacy_dispatch_fn)

    return None


# SOV-02 Step 1: predicates extracted to captain_predicates.py.
# SOV-03 Category B: captain_is_active removed; re-export retired.
# captain_preconditions_met re-exported for virelai.py (choose_action entrypoint).
from virelai_v4.captain_predicates import (  # noqa: F401, E402
    captain_preconditions_met,
)

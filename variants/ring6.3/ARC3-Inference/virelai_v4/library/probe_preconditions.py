"""virelai_v4/library/probe_preconditions.py — Probe precondition predicates.

Per Library Blueprint Section 5.2.3 (Available Probes — operational
preconditions). Filed under WO-LGTD-02 Phase 2 of the Library-Grounded
Tool Dispatch Campaign.

Each probe in PROBE_CATALOG declares operational_preconditions as a tuple
of predicate names referenced here. The predicate functions read
SemanticLibrary state and return bool — read-only, no side effects.

PHASE 2 STATUS: All predicates are STUBS returning False. Phase 3
implements the actual predicate logic (WO-LGTD-02 Phase 3, Section 3.3.1).
The stubs exist so Phase 2 tests can verify the wiring (catalog →
preconditions → library) before Phase 3 lands the real logic.

Calling convention:
  evaluate_precondition(name: str, library: SemanticLibrary) -> bool
The dispatch table at the bottom of this module maps precondition names
to their implementation. Adding a precondition requires:
  1. Add the function below.
  2. Register it in PRECONDITION_REGISTRY.
  3. Reference it from one or more PROBE_CATALOG entries.

Import sovereignty: typing + (Phase 3+) SemanticLibrary read-only.
"""

from __future__ import annotations

from typing import Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from virelai_v4.library.semantic_library import SemanticLibrary


# ---------------------------------------------------------------------------
# Precondition predicates (Phase 3 implementation)
# ---------------------------------------------------------------------------
#
# All predicates are READ-ONLY. They walk library state and return bool.
# No side effects, no mutations. Verified by
# tests/library/test_available_probes.py::test_precondition_predicates_read_only.

# Threshold for treating an UNKNOWN-role object as a plausible ego
# candidate based on action_independence_ratio. Mirrors the COUNTER
# rule's high-AIR signal: an object that responds to many actions is
# either ego (it moves with directionals) or counter (it ticks). The
# ego-candidate side of that disjunction is what this predicate covers
# pre-classification. The threshold is conservative — Phase 3 keeps it
# loose to avoid suppressing the stride probe early in Life 1.
_EGO_CANDIDATE_AIR_THRESHOLD: float = 0.25


def ego_candidate_exists(library: "SemanticLibrary") -> bool:
    """True iff the library holds at least one ego-candidate object.

    An object is an ego candidate if:
      - role == EGO (already identified), OR
      - role == UNKNOWN AND action_independence_ratio >= threshold
        (high-AIR plausible candidate not yet classified)

    Gating probes: stride_probe, contact_probe, tier3_nav_probe.
    """
    from virelai_v4.library.library_roles import LibraryRole
    for obj in library.objects.values():
        if obj.role == LibraryRole.EGO:
            return True
        if (
            obj.role == LibraryRole.UNKNOWN
            and obj.action_independence_ratio >= _EGO_CANDIDATE_AIR_THRESHOLD
        ):
            return True
    return False


def any_action_declared(library: "SemanticLibrary") -> bool:
    """True iff at least one SDKAction has declarative_belief == DECLARED.

    Used by tier1_channel_probe, which has empty required_actions
    because the probe operates over whatever channels the platform
    declares this frame. The precondition asserts at least one
    channel is declared.
    """
    from virelai_v4.library.affordance_belief import DeclarativeBelief
    return any(
        sdk_action.declarative_belief == DeclarativeBelief.DECLARED
        for sdk_action in library.sdk_actions.values()
    )


def unprobed_target_available(library: "SemanticLibrary") -> bool:
    """True iff at least one LibraryObject has not yet been first-touch-probed.

    Plausibility: any object with `probe_count == 0` whose role is not
    EGO. STATIC is intentionally NOT excluded — STATIC at the library
    level is a classification hypothesis, not a confirmed fact. The
    Form B walk's static-category dispatch declaration at
    `captain.py:271-276` returns FIRST_TOUCH_PROBE for any unprobed
    STATIC slot with `ALWAYS_TRUE` prerequisite and a
    `DISTINCT_PROBES_AT_LEAST(n=1)` completion predicate — the Coverage
    pass TESTS the static-ness hypothesis with a single click. Excluding
    STATIC here would prevent the Coverage pass from ever firing.

    EGO is excluded — the agent does not probe itself; the ego is its
    own object class.

    Gating probe: click_probe.

    Filed under WO-LGTD-02-FIX-01 Phase 2 (Fix B) per FRICTION-LGTD-02
    audit Section 4 and the H_other architectural finding (Phase 3
    implementation excluded STATIC under a misreading of Section 5.4;
    the captain's static-category dispatch contract requires STATIC to
    be a valid first-touch target).
    """
    from virelai_v4.library.library_roles import LibraryRole
    return any(
        obj.probe_count == 0 and obj.role != LibraryRole.EGO
        for obj in library.objects.values()
    )


def lever_confirmed(library: "SemanticLibrary") -> bool:
    """True iff at least one slot's lever AXIS reads >= LEVER_LOCKED_THRESHOLD.

    Gating probe: cycle_probe (must have a confirmed lever to type).

    WO-XLEVEL-LOOP-02 (PRIMITIVES-00 verdict (a)): migrated from the
    categorical `lever_locked` field to the v1.3 two-threshold axis read —
    the same language as the walk's SLOT_IS_LEVER_LOCKED
    (predicate_evaluators.py:191, same constant). The categorical field is
    dead in the predicate layer (v1.3 retired it; 02b never writes it on
    inherited slots), so the old form kept the wired cycle probe closed on
    every post-advance level while the walk targeted it — the L2 typed-gap
    tail. Floor co-timing (LOOP-02 §0(b)): probe_outcome_processor.py:153
    writes lever_locked=True in the same outcome block as the damped 0.7
    accumulate (:172, sigmoid 0.700 >= 0.6) — the axis form opens at the
    same L1 event the categorical form did, and the gate is only consulted
    after the walk (axis >= LOCKED) selects the attribute.
    """
    from virelai_v4.library.constants import LEVER_LOCKED_THRESHOLD

    return any(
        obj.sigmoid_confidence("lever") >= LEVER_LOCKED_THRESHOLD
        for obj in library.objects.values()
    )


def not_yet_saturated(library: "SemanticLibrary") -> bool:
    """True iff at least one confirmed lever has not yet been TYPED on the axis.

    A lever is "not yet saturated" when its lever axis is in the locked
    band: >= LEVER_LOCKED_THRESHOLD and < LEVER_TYPED_THRESHOLD — the same
    completion language as the walk's LEVER_TYPED
    (predicate_evaluators.py:322, same constant).

    Gating probe: cycle_probe (already-typed levers do not need re-probing).

    WO-XLEVEL-LOOP-02: migrated from `lever_locked AND mechanism
    None/UNKNOWN`. The mechanism enum is no longer a gate — it is a
    HYPOTHESIS, never a precondition: an inherited mechanism (02b carries
    TOGGLE across the level boundary) must not block its own behavioral
    re-confirmation (the 02b §0 staleness trap, closed here in affordance
    language). Floor co-timing: cycle_probe terminal commits write the
    mechanism AND the un-damped 1.0 accumulate in the same commit
    (sigmoid 0.98 >= 0.95) — the axis form stops re-offering at the same
    L1 event the enum form did.
    """
    from virelai_v4.library.constants import (
        LEVER_LOCKED_THRESHOLD,
        LEVER_TYPED_THRESHOLD,
    )

    return any(
        LEVER_LOCKED_THRESHOLD
        <= obj.sigmoid_confidence("lever")
        < LEVER_TYPED_THRESHOLD
        for obj in library.objects.values()
    )


# ---------------------------------------------------------------------------
# Registry — name → predicate function
# ---------------------------------------------------------------------------

PRECONDITION_REGISTRY: Dict[str, Callable[["SemanticLibrary"], bool]] = {
    "ego_candidate_exists": ego_candidate_exists,
    "any_action_declared": any_action_declared,
    "unprobed_target_available": unprobed_target_available,
    "lever_confirmed": lever_confirmed,
    "not_yet_saturated": not_yet_saturated,
}


def evaluate_precondition(name: str, library: "SemanticLibrary") -> bool:
    """Resolve a precondition name to its predicate function and call it.

    Returns False (conservative) if the name is not in the registry —
    a typo'd precondition name fails closed rather than opening.

    Phase 2: every registered predicate returns False stub, so every
    probe with non-empty operational_preconditions evaluates as
    unavailable in this phase. Phase 3 enables the catalog.
    """
    predicate = PRECONDITION_REGISTRY.get(name)
    if predicate is None:
        return False
    return predicate(library)


__all__ = [
    "ego_candidate_exists",
    "any_action_declared",
    "unprobed_target_available",
    "lever_confirmed",
    "not_yet_saturated",
    "PRECONDITION_REGISTRY",
    "evaluate_precondition",
]

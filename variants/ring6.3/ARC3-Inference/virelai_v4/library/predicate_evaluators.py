"""
virelai_v4/library/predicate_evaluators.py — Predicate evaluators.

Per Blueprint Section 3.4.1 (`is_actionable`) + Section 3.4.3 (`is_filled`).
The two evaluator functions read PrerequisitePredicate / CompletionPredicate
declarations against library state and produce boolean verdicts.

Per the WO-BLUEPRINT-05 scope: evaluator FUNCTIONS exist; the captain does
NOT yet consume them. WO-BLUEPRINT-06 (Form B walk) wires them into the
captain's walk.

Parameter binding model:
    A predicate declaration is a (predicate, parameters) pair where:
      - predicate: PrerequisitePredicate or CompletionPredicate enum value
      - parameters: dict[str, Any] supplying threshold, axis, category, etc.

    Example (Blueprint Section 3.4.1 notation):
        (PrerequisitePredicate.CATEGORY_CONFIDENCE_ABOVE_THRESHOLD,
         {"axis": "lever", "threshold": 0.7})

    The evaluator dispatches on the enum value and reads its parameters
    via dict lookup. Missing required parameters raise ValueError; this
    discipline prevents silent mis-evaluation.

The `library` parameter is expected to expose `library.foundation`,
`library.objects`, and `library.header` per Blueprint Section 2's
structural layers. For Sub-Phase 2's V4-current state (pre-foundation-
layer-split), `library.header` carries foundation-equivalent fields
(world_type_confidence, ego_mode_confidence, world_type) per
WO-BLUEPRINT-04-DIAG Section A.2.

The `slot` parameter is a LibraryObject (V4 nomenclature for Section 2's
Slot). Reads `slot.<category>_log_score` via the sigmoid_confidence
accessor added in WO-BLUEPRINT-04 + V4-current fields (probed, lever_locked,
etc.).

Filed under WO-BLUEPRINT-05, May 19, 2026.

Import sovereignty: imports from contracts/ + library/semantic_library only.
No imports from perception/, strategy/, captain/, or targeting/.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

from virelai_v4.contracts.completion_predicate import CompletionPredicate
from virelai_v4.contracts.prerequisite_predicate import PrerequisitePredicate
from virelai_v4.library.constants import (
    CONFIRMATION_THRESHOLD,
    LEVER_LOCKED_THRESHOLD,
    LEVER_TYPED_THRESHOLD,
)


# ---------------------------------------------------------------------------
# is_actionable — PrerequisitePredicate evaluator
# ---------------------------------------------------------------------------

def evaluate_prerequisite(
    predicate: PrerequisitePredicate,
    parameters: Dict[str, Any],
    library: Any,
    slot: Optional[Any] = None,
) -> bool:
    """Evaluate a single PrerequisitePredicate value against library state.

    Per Blueprint Section 3.4.1.

    Args:
        predicate: The PrerequisitePredicate enum value (the discriminator).
        parameters: Dict supplying the predicate's bound parameters (threshold,
            axis, category, etc.).
        library: The SemanticLibrary instance (for foundation + header reads).
        slot: Optional LibraryObject (for Slot-state predicates). May be None
            for foundation-only predicates.

    Returns:
        True if the predicate evaluates True against current state.

    Raises:
        ValueError: if `predicate` is an unrecognized value or if required
            parameters are missing.
    """
    if predicate is PrerequisitePredicate.ALWAYS_TRUE:
        return True

    # Foundation-state predicates
    if predicate is PrerequisitePredicate.WORLD_TYPE_CONFIDENCE_ABOVE_THRESHOLD:
        threshold = _required_param(parameters, "threshold", predicate)
        return getattr(library.header, "world_type_confidence", 0.0) > threshold

    if predicate is PrerequisitePredicate.EGO_MODE_CONFIDENCE_ABOVE_THRESHOLD:
        threshold = _required_param(parameters, "threshold", predicate)
        return getattr(library.header, "ego_confidence", 0.0) > threshold

    if predicate is PrerequisitePredicate.COUNTER_IDENTIFIED:
        # WO-BLUEPRINT-08 migration: read the COUNTER axis via
        # `sigmoid_confidence("counter")` instead of the categorical
        # `obj.role == COUNTER` check. Per coexistence audit §3.3:
        # the COUNTER axis accumulates evidence via WO-07's accumulator
        # hook at classification_pass.py:186 on every classifier verdict
        # naming LibraryRole.COUNTER. The categorical `obj.role` field
        # continues to be written during Sub-Phase 3 coexistence; this
        # predicate no longer reads it.
        return any(
            obj.sigmoid_confidence("counter") >= CONFIRMATION_THRESHOLD
            for obj in library.objects.values()
        )

    # Slot-state predicates
    if predicate is PrerequisitePredicate.SLOT_PROBED:
        if slot is None:
            return False
        # V4-current: slot.actions_attempted dict — any action attempted
        # means the Slot has been probed at least once.
        return bool(getattr(slot, "actions_attempted", {}))

    if predicate is PrerequisitePredicate.CATEGORY_CONFIDENCE_ABOVE_THRESHOLD:
        axis = _required_param(parameters, "axis", predicate)
        threshold = _required_param(parameters, "threshold", predicate)
        if slot is None:
            return False
        # Use the sigmoid_confidence accessor added in WO-BLUEPRINT-04.
        return slot.sigmoid_confidence(axis) > threshold

    if predicate is PrerequisitePredicate.SUBLIBRARY_OPEN:
        category = _required_param(parameters, "category", predicate)
        if slot is None:
            return False
        # Section 2.5: sub-library is open when parent log-score crosses 0.7.
        # For Sub-Phase 2 we use the sigmoid_confidence read as the gate.
        return slot.sigmoid_confidence(category) > 0.7

    if predicate is PrerequisitePredicate.VARIANT_CONFIDENCE_ABOVE_THRESHOLD:
        # Variant catalogs land in Section 4+; this predicate is a
        # forward-declaration. For Sub-Phase 2 the evaluator returns False
        # (variant catalogs not yet populated). Sub-Phase 4+ refines.
        _required_param(parameters, "category", predicate)
        _required_param(parameters, "variant", predicate)
        _required_param(parameters, "threshold", predicate)
        return False

    # Lifecycle predicate
    if predicate is PrerequisitePredicate.CURRENT_LEVEL_AT_LEAST:
        min_level = _required_param(parameters, "min_level", predicate)
        return getattr(library.header, "level", 1) >= min_level

    # World-type predicates
    if predicate is PrerequisitePredicate.WORLD_TYPE_IS:
        world_type = _required_param(parameters, "world_type", predicate)
        return getattr(library.header, "world_type", "UNKNOWN") == world_type

    if predicate is PrerequisitePredicate.WORLD_TYPE_IS_ONE_OF:
        world_types = _required_param(parameters, "world_types", predicate)
        return getattr(library.header, "world_type", "UNKNOWN") in world_types

    # Action-availability predicate
    if predicate is PrerequisitePredicate.ACTION_IS_AVAILABLE:
        action = _required_param(parameters, "action", predicate)
        # V4-current: sdk_actions on library tracks per-action LIVE/INERT status.
        sdk_action = library.sdk_actions.get(action)
        if sdk_action is None:
            return False
        return getattr(sdk_action, "status", "") == "LIVE"

    # v1.1 amendment — WO-BLUEPRINT-08 migration to BBA Layer One read.
    if predicate is PrerequisitePredicate.SLOT_IS_LEVER_LOCKED:
        if slot is None:
            return False
        # WO-BLUEPRINT-08-TWO-THRESHOLD (Section 2 v1.3 amendment, Apex
        # ratified May 22, 2026): SLOT_IS_LEVER_LOCKED reads the LOW
        # threshold on the lever-axis log-score. A slot crosses this
        # threshold when the captain has sufficient evidence to treat
        # it as a confirmed lever and dispatch probing of its mechanism
        # (but the mechanism has not yet been characterized).
        #
        # The damped LEVER_LOCAL accumulator at `probe_outcome_processor.py`
        # (confidence=0.7) drives lever_log_score above LEVER_LOCKED_THRESHOLD
        # but NOT above LEVER_TYPED_THRESHOLD — preserving the asymmetry
        # the captain's Form B walk requires between "lever confirmed,
        # not yet typed" and "lever typed, walk advances."
        #
        # Categorical `slot.lever_locked` field continues to be written
        # by `probe_outcome_processor.py:152` during Sub-Phase 3
        # coexistence; this predicate no longer reads it. The
        # `classification_pass.py:143` skip-guard reader of
        # `lever_locked` remains operational (FM 1 mitigation; see
        # audit §5.1).
        return slot.sigmoid_confidence("lever") >= LEVER_LOCKED_THRESHOLD

    # WO-EFFECT-WALK-HOOK (WO2): Tier-4 (lever typing) globally GREEN gate.
    if predicate is PrerequisitePredicate.ALL_LEVERS_TYPED:
        levers = [
            o for o in library.objects.values()
            if o.sigmoid_confidence("lever") >= LEVER_LOCKED_THRESHOLD
        ]
        if not levers:
            return False  # no confirmed levers -> effect band cannot open
        return all(
            o.sigmoid_confidence("lever") >= LEVER_TYPED_THRESHOLD
            for o in levers
        )

    # WO-E6 (Per-Lever B3 Dispatch): the per-lever decomposition of
    # ALL_LEVERS_TYPED — THIS slot's B2 is cleared when its lever-axis
    # log-score crosses LEVER_TYPED_THRESHOLD (the same HIGH threshold the
    # global gate and the LEVER_TYPED completion read; saturation accumulates
    # the axis to 1.0, so a saturated lever passes too). Reads the clean
    # log-score, never the lever_mechanism field — no de-collapse premise.
    if predicate is PrerequisitePredicate.SLOT_IS_LEVER_TYPED:
        if slot is None:
            return False
        return slot.sigmoid_confidence("lever") >= LEVER_TYPED_THRESHOLD

    raise ValueError(
        f"evaluate_prerequisite: unrecognized PrerequisitePredicate {predicate!r}"
    )


def is_actionable(
    prerequisite_declarations: Sequence[Tuple[PrerequisitePredicate, Dict[str, Any]]],
    library: Any,
    slot: Optional[Any] = None,
) -> bool:
    """Evaluate whether an attribute slot is currently actionable per Section 3.4.1.

    The captain calls this against each Slot's prerequisite predicate
    declarations to determine walk-order actionability. Short-circuits on
    the first False per Section 3.4.1.

    Args:
        prerequisite_declarations: Tuple of (predicate, parameters) pairs.
            Empty sequence is treated as "no prerequisites" → always True.
        library: SemanticLibrary instance for foundation + header reads.
        slot: Optional LibraryObject for Slot-state predicates.

    Returns:
        True iff every predicate evaluates True. False on first failure.
    """
    for predicate, parameters in prerequisite_declarations:
        if not evaluate_prerequisite(predicate, parameters, library, slot):
            return False
    return True


# ---------------------------------------------------------------------------
# is_filled — CompletionPredicate evaluator
# ---------------------------------------------------------------------------

def evaluate_completion(
    predicate: CompletionPredicate,
    parameters: Dict[str, Any],
    library: Any,
    slot: Optional[Any] = None,
) -> bool:
    """Evaluate a single CompletionPredicate value against library state.

    Per Blueprint Section 3.4.3. INVENT #3 anchor — the May 16 variable-K
    cycle probe's empirical patterns formalized as typed evaluation.

    The CYCLE_RETURN_OBSERVED and DISTINCT_PROBES_AT_LEAST evaluations
    read state that V4's existing `library/cycle_probe.py` already
    maintains (per WO-BLUEPRINT-05 Step 1.c pre-audit anchor):

      CYCLE_RETURN_OBSERVED:
          The cycle probe's state_hashes accumulator (cycle_probe.py:370-388)
          maintains observed state hashes; recurrence is detected when
          state_hashes[i] equals state_hashes[j] for j < i-1. For Sub-Phase
          2's WO-05 scope, the evaluator reads slot.cycle_length > 0 as
          a post-commit signal that recurrence was observed and classification
          ran. Sub-Phase 3+ refines to read the substrate-managed
          observed_states catalog directly.

      DISTINCT_PROBES_AT_LEAST:
          The variable-K cycle probe (cycle_probe.py:88-96, 390-394, 509)
          tracks consecutive_press_count on CycleProbeState. The evaluator
          for Sub-Phase 2 reads slot.actions_attempted dict length as the
          V4-current proxy for distinct-probes-on-this-slot count.
          Sub-Phase 3+ refines to read slot.probe_history (the ProbeEvent
          log added in WO-BLUEPRINT-04).

    Args:
        predicate: The CompletionPredicate enum value (the discriminator).
        parameters: Dict supplying bound parameters.
        library: SemanticLibrary instance.
        slot: Optional LibraryObject; required for Slot-scoped predicates.

    Returns:
        True if the predicate evaluates True against current state.

    Raises:
        ValueError: if `predicate` is unrecognized or required parameters
            are missing.
    """
    # Cycle-specific (INVENT #3 anchor)
    if predicate is CompletionPredicate.CYCLE_RETURN_OBSERVED:
        if slot is None:
            return False
        # V4 cycle_probe.py:370-388 commits classification when state recurrence
        # detected; the post-commit signal is cycle_length > 0 (TOGGLE has
        # cycle_length==2; FINITE_CYCLE has cycle_length>=3). PROVISIONAL_DRIFT
        # commits with cycle_length=0; saturation commits with cycle_length=0
        # AND saturated=True (so cycle_length>0 captures "cycle recurrence
        # observed" specifically, excluding saturation). The captain's lever
        # category completion uses the broader LEVER_TYPED predicate (per
        # Section 2 v1.2) which captures saturation as well; this predicate
        # remains for mechanism-specific contexts (diagnostic surfacing,
        # variant catalog completion checks).
        return getattr(slot, "cycle_length", 0) > 0

    # Lever-typing aggregate — WO-BLUEPRINT-08-TWO-THRESHOLD HIGH-threshold read.
    if predicate is CompletionPredicate.LEVER_TYPED:
        if slot is None:
            return False
        # WO-BLUEPRINT-08-TWO-THRESHOLD (Section 2 v1.3 amendment, Apex
        # ratified May 22, 2026): LEVER_TYPED reads the HIGH threshold
        # on the lever-axis log-score. A slot crosses this threshold
        # when its mechanism is characterized enough to stop probing.
        #
        # Saturation preservation (v1.2 semantic carried forward):
        # cycle_probe terminal commits fire `accumulate_role_evidence`
        # at confidence=1.0 (un-damped) — driving lever_log_score above
        # LEVER_TYPED_THRESHOLD regardless of which mechanism the commit
        # represents (CYCLE, TOGGLE, DIRECTIONAL, GLOBAL, ONE_SHOT,
        # GATED, SATURATED, UNKNOWN). The May 21 vc33 regression site at
        # cycle_probe.py:375 (SATURATED) fires the accumulator alongside
        # the categorical `lever_mechanism = SATURATED` write; the
        # log-score crosses LEVER_TYPED_THRESHOLD; the walk advances.
        #
        # Two-threshold asymmetry: the damped LEVER_LOCAL accumulator at
        # probe_outcome_processor.py (confidence=0.7) drives the score
        # above LEVER_LOCKED_THRESHOLD (P13 fires) but below
        # LEVER_TYPED_THRESHOLD (C2 does NOT fire). The captain
        # dispatches the cycle_probe; the cycle_probe terminal commit
        # at confidence=1.0 pushes the score above LEVER_TYPED_THRESHOLD;
        # C2 fires; the walk advances. The May 16 anchor mechanism is
        # preserved.
        #
        # The §3.4 regression-anchor test at
        # `tests/library/test_predicate_evaluators.py::test_lever_typed_returns_true_after_cycle_probe_saturation`
        # pins this end-to-end (accumulator → predicate) under the new
        # HIGH threshold.
        #
        # Parameterless per v1.2 spec — `parameters` dict is ignored.
        return slot.sigmoid_confidence("lever") >= LEVER_TYPED_THRESHOLD

    # Observation-count (INVENT #3 anchor)
    if predicate is CompletionPredicate.DISTINCT_PROBES_AT_LEAST:
        n = _required_param(parameters, "n", predicate)
        if slot is None:
            return False
        # V4-current: actions_attempted dict tracks per-action probe attempts
        # on this slot. Each key represents a distinct probe action.
        # Sub-Phase 3+ refines to read len(slot.probe_history).
        return len(getattr(slot, "actions_attempted", {})) >= n

    if predicate is CompletionPredicate.STATES_OBSERVED_COUNT_AT_LEAST:
        n = _required_param(parameters, "n", predicate)
        if slot is None:
            return False
        # V4-current proxy: transition_count tracks distinct state
        # transitions observed on this Slot. Section 2.5.2 specifies
        # observed_states list; Sub-Phase 4+ refines.
        return getattr(slot, "transition_count", 0) >= n

    # Saturation predicates
    if predicate is CompletionPredicate.SUBLIBRARY_SATURATION_ABOVE:
        category = _required_param(parameters, "category", predicate)
        threshold = _required_param(parameters, "threshold", predicate)
        if slot is None:
            return False
        # V4-current: sigmoid_confidence reads the log-score for the
        # category. Saturation threshold above the opening threshold
        # (0.7) indicates saturated sub-library state.
        return slot.sigmoid_confidence(category) > threshold

    if predicate is CompletionPredicate.VARIANT_SATURATION_ABOVE:
        # Variant catalogs are Section 4+; forward declaration.
        _required_param(parameters, "category", predicate)
        _required_param(parameters, "variant", predicate)
        _required_param(parameters, "threshold", predicate)
        return False

    # Causal-link predicate
    if predicate is CompletionPredicate.CAUSAL_LINK_CONFIDENCE_ABOVE:
        target_slot_id = _required_param(parameters, "target_slot_id", predicate)
        threshold = _required_param(parameters, "threshold", predicate)
        if slot is None:
            return False
        # V4-current: slot.causes is the tuple of region_ids causally linked
        # to this slot. The threshold-aware evaluation requires per-link
        # confidence which Section 4+ supplies; for Sub-Phase 2, return
        # True iff target_slot_id is in slot.causes (binary causal link).
        # The threshold parameter is read for future refinement.
        _ = threshold  # noqa: F841 (forward-binding placeholder)
        return target_slot_id in getattr(slot, "causes", ())

    # Coverage predicate
    if predicate is CompletionPredicate.COVERAGE_SATURATION_ABOVE:
        threshold = _required_param(parameters, "threshold", predicate)
        if slot is None:
            return False
        # V4-current proxy: static_log_score sigmoid-read as coverage
        # proxy (high static confidence indicates accumulated coverage).
        # Section 2.5.1 specifies a per-condition coverage_map; Sub-Phase
        # 4+ refines.
        return slot.sigmoid_confidence("static") > threshold

    # WO-EFFECT-WALK-HOOK (WO2): least-observed frontier. "Filled" (skip) when
    # this typed lever is NOT the global minimum-effort typed lever. effort =
    # the smallest observation_count across the lever's discovered subjects
    # (0 when none discovered). The unique/global-min lever stays unfilled, so
    # the captain always has exactly one open effect question and round-robins
    # toward the least-observed — never idling while typed levers exist. No
    # self-cap by construction (Director ruling, June 11 2026).
    if predicate is CompletionPredicate.LEVER_EFFECT_NOT_LEAST_OBSERVED:
        if slot is None:
            return False
        typed = [
            o for o in library.objects.values()
            if o.sigmoid_confidence("lever") >= LEVER_TYPED_THRESHOLD
        ]
        if not typed:
            return True  # nothing to characterize -> treat as filled
        global_min = min(_lever_effort(o) for o in typed)
        return _lever_effort(slot) > global_min

    if predicate is CompletionPredicate.LEVER_EFFECT_CHARACTERIZED:
        # WO-EFFECT-01 — the effect-band TERMINAL (permanent-fill; the x129
        # fence). Fills on either arm; both only ever increase, so once filled it
        # stays filled and the effect question does not re-open.
        if slot is None:
            return False
        effects = getattr(slot, "lever_effects", ())
        # (a) per-region AGREEMENT: a dominant effect (same subject_region +
        # operation_kind) has recurred >= threshold times — the lever reliably
        # drives that region (the effect is stable-not-shifting).
        dominant = max((e.observation_count for e in effects), default=0)
        if dominant >= _EFFECT_AGREEMENT_THRESHOLD:
            return True
        # (b) bounded EXHAUSTION (parallel to the dive's UNDETERMINED-at-cap): a
        # shifting or null lever that never stabilizes still terminates, so the
        # band can never round-robin. total = all effect observations + null
        # presses this lever has absorbed.
        total = (sum(e.observation_count for e in effects)
                 + getattr(slot, "effect_null_presses", 0))
        return total >= _EFFECT_PROBE_CAP

    raise ValueError(
        f"evaluate_completion: unrecognized CompletionPredicate {predicate!r}"
    )


def is_filled(
    completion_declarations: Sequence[Tuple[CompletionPredicate, Dict[str, Any]]],
    library: Any,
    slot: Optional[Any] = None,
) -> bool:
    """Evaluate whether an attribute slot is filled per Section 3.4.3.

    The captain calls this against each attribute slot's completion
    predicate declarations to determine fill status. An attribute is
    filled when all completion predicates evaluate True (Section 3.4.3).

    Args:
        completion_declarations: Tuple of (predicate, parameters) pairs.
            Empty sequence is treated as "no completion criteria" → always
            False (un-filled by default; single-observation attributes use
            a separate "value is set" check per Section 3.4.3).
        library: SemanticLibrary instance.
        slot: Optional LibraryObject.

    Returns:
        True iff every completion predicate evaluates True AND the
        sequence is non-empty.
    """
    if not completion_declarations:
        return False
    for predicate, parameters in completion_declarations:
        if not evaluate_completion(predicate, parameters, library, slot):
            return False
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# WO-EFFECT-01 — the effect TERMINAL thresholds (parallel to LEVER_TYPED's HIGH
# gate). AGREEMENT: a dominant per-region effect observed this many times ==
# characterized. CAP: total effect presses (obs + null) beyond which a
# never-stabilizing lever terminates anyway (bounded, x129-safe). The June-11
# soft-target was N=5; kept conservative here — CE-tunable.
_EFFECT_AGREEMENT_THRESHOLD = 3
_EFFECT_PROBE_CAP = 8


def _lever_effort(obj: Any) -> int:
    """Effort = the least-observed discovered subject's observation_count
    (WO-EFFECT-WALK-HOOK, WO2). The least-effort typed lever is the captain's
    open effect question.

    WO-E6 (loop guard): when the lever has NO discovered effects the default is
    `effect_null_presses` — the count of silent (zero-delta) effect-probes the
    lever has absorbed — NOT a fixed 0. This is the load-bearing loop guard:
    a genuinely-saturated lever produces only null presses, records no effect,
    and without this would sit at effort 0 forever (perpetually least-observed
    -> re-probed every frame). Counting each null press as an observation lets
    the least-observed round-robin de-prioritize it (studied-when-nothing-
    better, not looped-every-frame). §0.3 confirmed at b38e582 that null presses
    do NOT increment observation_count natively (physics_accumulator
    ZERO_DELTA_SILENT returns without record_lever_effect); this restores the
    guard. Levers WITH effects are unaffected — the default is never reached."""
    effects = getattr(obj, "lever_effects", ())
    null_floor = getattr(obj, "effect_null_presses", 0)
    return min((e.observation_count for e in effects), default=null_floor)


def _required_param(parameters: Dict[str, Any], key: str, predicate: Any) -> Any:
    """Read a required parameter from the parameters dict.

    Raises ValueError if missing. Section 3.4.1's parameter discipline:
    bound parameters live in the parameters dict; the evaluator dispatches
    on the predicate kind and reads the kind's required parameters.

    Missing parameters indicate a malformed declaration; raise rather than
    silently returning False to surface declaration errors during build.
    """
    if key not in parameters:
        raise ValueError(
            f"Predicate {predicate!r} requires parameter {key!r}; "
            f"received {parameters!r}"
        )
    return parameters[key]

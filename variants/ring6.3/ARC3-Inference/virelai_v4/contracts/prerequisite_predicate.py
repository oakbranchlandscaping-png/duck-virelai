"""
virelai_v4/contracts/prerequisite_predicate.py — PrerequisitePredicate enum.

Per Blueprint Section 3.4.1 specification — the typed discriminator enum
the captain evaluates at walk time to determine whether an attribute slot
is currently actionable.

A Slot's `prerequisite_predicates` attribute is a tuple of (predicate,
parameters) declarations. The captain reads each predicate, dispatches
on the enum value to the corresponding evaluator, and short-circuits on
the first False.

Per Section 3.4.1:

    An attribute is *actionable* when:
      1. The attribute is unfilled (or has been invalidated by revocation
         per Section 1.7), AND
      2. All prerequisite predicates evaluate to True against the current
         library state.

The enum's 12 values cover the foundation-state, Slot-state, lifecycle,
world-type, and action-availability categories per Section 3.4.1, plus
the v1.1 amendment's `SLOT_IS_LEVER_LOCKED` from Section 2 v1.1
Carry-Forward Item 6.

Parameters (threshold, axis, category, variant, world_type, etc.) are
bound at attribute-slot declaration time, NOT inside the enum value
itself. Section 3.4.1 examples:

    # CYCLE catalog opens when:
    open_prerequisite = [
        (PrerequisitePredicate.CATEGORY_CONFIDENCE_ABOVE_THRESHOLD,
         {"axis": "lever", "threshold": 0.7}),
        (PrerequisitePredicate.VARIANT_CONFIDENCE_ABOVE_THRESHOLD,
         {"category": "lever", "variant": "CYCLE", "threshold": 0.7}),
    ]

The exact wiring of attribute-slot declarations to predicate sequences
lands in WO-BLUEPRINT-06 (captain Form B walk) per the Captain Migration
Path. For this WO, the enum + evaluator dispatch table is the deliverable.

Filed under WO-BLUEPRINT-05, May 19, 2026.
Sibling of INVENT #3 anchor (CompletionPredicate enum).
"""

from __future__ import annotations

from enum import Enum, auto


class PrerequisitePredicate(Enum):
    """Declarative prerequisite predicates per Blueprint Section 3.4.1.

    Twelve discriminator values across five categories:

    Foundation-state predicates (3):
      WORLD_TYPE_CONFIDENCE_ABOVE_THRESHOLD: parameter `threshold: float`
          Evaluates `library.foundation.world_type_confidence > threshold`.
          Gate for object-list sub-library opening per Section 2.3.4.

      EGO_MODE_CONFIDENCE_ABOVE_THRESHOLD: parameter `threshold: float`
          Evaluates `library.foundation.ego_mode_confidence > threshold`.
          Gate for EgoSubLibrary opening per Section 2.3.4.

      COUNTER_IDENTIFIED: no parameters
          Evaluates `library.foundation.counter is not None`.
          Gate for `DeltaSummary.is_lc_only` filtering per Section 2.3.4.

    Slot-state predicates (4):
      SLOT_PROBED: no parameters
          Evaluates `slot.probed` (the Slot has been first-touch probed).
          Gate for downstream sub-library work per Section 2.12.

      CATEGORY_CONFIDENCE_ABOVE_THRESHOLD: parameters `axis: str, threshold: float`
          Evaluates `slot.sigmoid_confidence(axis) > threshold`.
          Gate for category sub-library opening per Section 2.7.

      SUBLIBRARY_OPEN: parameter `category: str`
          Evaluates `slot.<category>_sublibrary is not None and slot.<category>_sublibrary.is_open()`.
          Gate for variant-level work within a category per Section 3.3.

      VARIANT_CONFIDENCE_ABOVE_THRESHOLD:
          parameters `category: str, variant: str, threshold: float`
          Evaluates the variant's distribution confidence within its sub-library.
          Gate for variant catalog opening per Section 2.7.

    Lifecycle predicates (1):
      CURRENT_LEVEL_AT_LEAST: parameter `min_level: int`
          Evaluates `library.header.current_level >= min_level`.
          Gate for win-state-hypothesis attributes per Section 4+ work.

    World-type predicates (2):
      WORLD_TYPE_IS: parameter `world_type: str`
          Evaluates `library.foundation.world_type == world_type`.
          Pins category-axis applicability per Section 2.6.4.

      WORLD_TYPE_IS_ONE_OF: parameter `world_types: frozenset[str]`
          Evaluates `library.foundation.world_type in world_types`.
          Pins category-axis applicability for multiple world types.

    Action-availability predicates (1):
      ACTION_IS_AVAILABLE: parameter `action: int`
          Evaluates whether the SDK action is currently usable.
          Implementation reads `library.sdk_actions[action].status == "LIVE"`
          (live evaluator at predicate_evaluators.py:159-165). A prior
          docstring referenced `library.header.available_action_set` —
          that header field does not exist (WO-00 GAP-10 finding).
          Corrected under WO-LGTD-02 Phase 1 (May 28, 2026). Per WO-LGTD-02
          Phase 4 the Affordance Layer's Entry A
          (sdk_action.declarative_belief == DECLARED) becomes the canonical
          availability signal; status-based read remains for backward
          compatibility during the transition.
          Gate for primitives requiring specific actions.

    v1.1 amendment additions (1):
      SLOT_IS_LEVER_LOCKED: no parameters
          Evaluates `slot.lever_locked` per Section 2.4.2 v1.1.
          Gate for cycle-probe targeting (confirmed-flag semantic).
          The composite confirmed-flag + demotion-guard semantics per
          Section 2.4.2 v1.1 are accommodated; this predicate reads
          the field as-is.

    A 13th convenience value:
      ALWAYS_TRUE: no parameters
          Evaluates True unconditionally. Used for unconditional attribute
          slots and as a base case for predicate chain construction.
    """
    # Convenience
    ALWAYS_TRUE = auto()

    # Foundation-state (3)
    WORLD_TYPE_CONFIDENCE_ABOVE_THRESHOLD = auto()
    EGO_MODE_CONFIDENCE_ABOVE_THRESHOLD = auto()
    COUNTER_IDENTIFIED = auto()

    # Slot-state (4)
    SLOT_PROBED = auto()
    CATEGORY_CONFIDENCE_ABOVE_THRESHOLD = auto()
    SUBLIBRARY_OPEN = auto()
    VARIANT_CONFIDENCE_ABOVE_THRESHOLD = auto()

    # Lifecycle (1)
    CURRENT_LEVEL_AT_LEAST = auto()

    # World-type (2)
    WORLD_TYPE_IS = auto()
    WORLD_TYPE_IS_ONE_OF = auto()

    # Action-availability (1)
    ACTION_IS_AVAILABLE = auto()

    # v1.1 amendment (1)
    SLOT_IS_LEVER_LOCKED = auto()

    # WO-EFFECT-WALK-HOOK (WO2): gate the effect-characterization band on
    # Tier-4 (lever typing) being globally GREEN — no effect probing opens
    # while any confirmed lever remains untyped. Evaluated against the
    # lever-axis HIGH threshold for every locked lever.
    ALL_LEVERS_TYPED = auto()

    # WO-E6 (Per-Lever B3 Dispatch): the PER-LEVER decomposition of
    # ALL_LEVERS_TYPED. True iff THIS slot's lever-axis log-score has crossed
    # LEVER_TYPED_THRESHOLD — i.e. this lever's B2 (intrinsic typing) is
    # cleared, including saturation (which accumulates the LEVER axis to 1.0).
    # Replaces ALL_LEVERS_TYPED as the effect-band gate so a lever's B3 opens
    # the moment ITS B2 clears, not when every lever is typed. Reads the clean
    # log-score axis (NOT the lever_mechanism field — the WO-E7 de-collapse is
    # not a premise of this gate; Director-ratified 2026-06-28 over a strict
    # `obj.saturated` gate, which would have regressed non-saturated typed
    # levers out of B3 entirely).
    SLOT_IS_LEVER_TYPED = auto()

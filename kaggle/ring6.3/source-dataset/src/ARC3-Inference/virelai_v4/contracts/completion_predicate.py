"""
virelai_v4/contracts/completion_predicate.py — CompletionPredicate enum.

INVENT #3 anchor per Blueprint Section 1.7 + Section 3.4.3 specification.

The May 16, 2026 vc33 Level 1 WIN under variable-K cycle probe is the
empirical anchor. The cycle probe's existing termination conditions are
formalized as typed enum values here. The patterns were already
operational in V4 (at `library/cycle_probe.py`); this enum is the
formal extraction.

Per Blueprint Section 1.7:

    Substrate-driven termination beats budget-driven termination. When
    the captain is filling an attribute that requires multiple
    observations (cycle period detection, saturation testing, mechanism
    characterization), the completion signal must come from the
    substrate's evidence — not from a fixed budget counter.

Per Blueprint Section 3.4.3:

    An attribute is *filled* when:
      1. Its single-observation value is set, OR
      2. All its completion predicates evaluate to True against the
         current library state.

INVENT #3 ANCHOR VERIFICATION (Inheritance Pre-Audit Pattern v3):

The two cycle-probe-specific predicates map to V4 code locations as
follows:

    CYCLE_RETURN_OBSERVED:
        V4 code: library/cycle_probe.py:370-388
        Existing behavior: when state hash[i] equals state hash[j] for
        j < i-1, the cycle probe computes cycle_length = (len-1)-j,
        classifies the lever as TOGGLE (cycle_length==2) or
        FINITE_CYCLE (cycle_length>=3), and calls _commit_classification.
        This is the "state recurrence" termination — the cycle returned
        to a previously-observed state.

    DISTINCT_PROBES_AT_LEAST:
        V4 code: library/cycle_probe.py:88-96, 390-394, 509
        Existing behavior: variable-K cycle probe with _PROBE_CAP=20
        safety backstop. state.consecutive_press_count tracks distinct
        probes; cap commits classification regardless of recurrence.
        For DISTINCT_PROBES_AT_LEAST(n=20), this is the V4 anchor.

    (Adjacent: SUBLIBRARY_SATURATION_ABOVE corresponds to the per-press
     saturation at cycle_probe.py:365 — `obj.saturated = True` when
     hash[i]==hash[i-1]. Documented but not directly enumerated as a
     starting CompletionPredicate value per Section 3.4.3 list.)

Filed under WO-BLUEPRINT-05, May 19, 2026.
INVENT anchor: #3 — Completion predicate enum (the May 16 variable-K
cycle probe formalized as typed predicate).
"""

from __future__ import annotations

from enum import Enum, auto


class CompletionPredicate(Enum):
    """Substrate-driven completion signals per Blueprint Section 3.4.3.

    Eight discriminator values: 7 from Section 3.4.3's starting set
    (WO-BLUEPRINT-05) + LEVER_TYPED added in Section 2 v1.2
    (WO-BLUEPRINT-06-LEVER-TYPED, May 21, 2026). Each value's parameters
    are bound at attribute-slot declaration time; Section 4+ variant
    catalog work refines parameter bindings.

    Saturation predicates (2):
      SUBLIBRARY_SATURATION_ABOVE: parameters `category: str, threshold: float`
          Evaluates `slot.<category>_sublibrary.saturation > threshold`.
          The sub-library has accumulated enough evidence to consider
          it "saturated" at the category level.

      VARIANT_SATURATION_ABOVE:
          parameters `category: str, variant: str, threshold: float`
          Evaluates the variant catalog's saturation.

    Observation-count predicates (2):
      STATES_OBSERVED_COUNT_AT_LEAST: parameter `n: int`
          Evaluates `len(slot.<category>_sublibrary.observed_states) >= n`.
          Used for reactive sub-library state-catalog filling.

      DISTINCT_PROBES_AT_LEAST: parameter `n: int`
          Evaluates `len(distinct_probes_in_slot.probe_history) >= n`.
          V4 anchor: cycle_probe.py:88-96, 390-394, 509 (the variable-K
          cap-driven termination). INVENT #3 anchor.

    Cycle-specific (1):
      CYCLE_RETURN_OBSERVED: no parameters
          Evaluates True when the substrate has observed the Slot's
          state recurring to a previously-observed configuration.
          V4 anchor: cycle_probe.py:370-388 (state hash recurrence loop).
          INVENT #3 anchor.

    Lever-typing aggregate (1, added in Section 2 v1.2):
      LEVER_TYPED: no parameters
          Evaluates True when the Slot's `lever_mechanism` field carries
          any non-None value — TOGGLE, CYCLE, DIRECTIONAL, GLOBAL,
          ONE_SHOT, GATED, SATURATED, or any UNKNOWN value the cycle
          probe state machine commits as a terminal classification.
          The broader sibling of CYCLE_RETURN_OBSERVED:
          CYCLE_RETURN_OBSERVED True ⟹ LEVER_TYPED True. LEVER_TYPED
          can be True while CYCLE_RETURN_OBSERVED is False (saturation
          commits lever_mechanism = SATURATED but does not set
          cycle_length). Formalizes the cursor-era equivalence the
          WO-BLUEPRINT-06 migration retired without replacement.
          Added by Section 2 v1.2 amendment (Apex ratified May 20, 2026).

    Causal-link predicates (1):
      CAUSAL_LINK_CONFIDENCE_ABOVE: parameters `target_slot_id: int, threshold: float`
          Evaluates `slot.reactive_sublibrary.driver_distribution[target_slot_id] > threshold`.
          Used for reactive driver identification (Section 2.5.2).

    Coverage predicates (1):
      COVERAGE_SATURATION_ABOVE: parameter `threshold: float`
          Evaluates `slot.static_sublibrary.coverage_map saturation > threshold`.
          Static coverage_map filling per Section 2.5.1 — gates when
          enough condition signatures have been probed without producing
          a delta.
    """
    # Saturation predicates (2)
    SUBLIBRARY_SATURATION_ABOVE = auto()
    VARIANT_SATURATION_ABOVE = auto()

    # Observation-count predicates (2)
    STATES_OBSERVED_COUNT_AT_LEAST = auto()
    DISTINCT_PROBES_AT_LEAST = auto()         # INVENT #3 anchor — cycle probe variable-K

    # Cycle-specific (1)
    CYCLE_RETURN_OBSERVED = auto()             # INVENT #3 anchor — state recurrence

    # Lever-typing aggregate (1) — Section 2 v1.2 (May 21, 2026)
    LEVER_TYPED = auto()                       # cursor-era equivalence; reads slot.lever_mechanism

    # Causal-link (1)
    CAUSAL_LINK_CONFIDENCE_ABOVE = auto()

    # Coverage (1)
    COVERAGE_SATURATION_ABOVE = auto()

    # Lever-effect characterization frontier (1) — WO-EFFECT-WALK-HOOK (WO2).
    # "Filled" (skip) when this lever is NOT the least-characterized typed
    # lever. The captain keeps exactly one open effect question — the global
    # minimum-effort typed lever — so it round-robins toward the least-observed
    # and NEVER goes idle while typed levers exist. A deliberately
    # NON-terminating completion (no self-cap): the game stops the probing, not
    # a threshold (Director ruling, June 11 2026). A soft target of N=5
    # observations is the deferred Phase-2 hand-off marker; intentionally not
    # used as a cap here.
    LEVER_EFFECT_NOT_LEAST_OBSERVED = auto()

    # WO-EFFECT-01: the effect-band TERMINAL (replaces the round-robin above as
    # the lever_effect completion). Fills PERMANENTLY when the lever's effect is
    # characterized — per-region agreement (a dominant lever_effect observed
    # >= threshold times) OR bounded exhaustion (total effect presses >= cap, so
    # a shifting/null lever still terminates). Parallel to LEVER_TYPED: fills and
    # STOPS, so the effect band goes silent instead of round-robining (the x129
    # fence). NOTE (ruling supersession): this reverses the June-11 2026 Director
    # ruling that the effect completion is "deliberately non-terminating (the game
    # stops the probing, not a threshold)"; WO-EFFECT-01 makes it terminate.
    LEVER_EFFECT_CHARACTERIZED = auto()

"""
virelai_v4/contracts/attribute_type.py — AttributeType enum.

Per Blueprint Section 3.5.1 specification — the classification dimension
that joins with `world_type` in the dispatch table key
`dict[(WorldType, AttributeType), ProbePrimitive]`.

Replaces V4's current `probe_type` field in `captain.py`'s
`DISPATCH_TABLE: Dict[Tuple[int, str, str], Callable]` keyed on
`(tier, world_type, probe_type)`. Per the Captain Migration Path Section F
critical path, the dispatch table re-keys to `(world_type, AttributeType)`
in WO-BLUEPRINT-06.

Per Section 3.5.1 the starting set covers foundation establishment,
slot-level root attributes, sub-library variant-level attributes, and
the out-of-tape sentinel. Phase 2+ variants (gated lever, directional
effect, etc.) are deferred per Blueprint Section 4 + Director Section G
rulings (NAV-side cells defer to Sub-Phase 4 per the May 19 ruling).

Filed under WO-BLUEPRINT-05, May 19, 2026.
Captain Migration Path Section F reference: WO-BLUEPRINT-06 will populate
the dispatch table using these values.
"""

from __future__ import annotations

from enum import Enum, auto


class AttributeType(Enum):
    """Attribute classification per Blueprint Section 3.5.1.

    Eleven starting values across four categories plus one sentinel.

    Foundation attributes (3):
      WORLD_TYPE_PROBE: Detect whether the world is CLICK / NAV / GLOBAL /
          HYBRID via the Rover Gambit pattern (WO-00 B.1 inheritance).

      EGO_MODE_PROBE: For NAV/HYBRID worlds, identify the ego region via
          directional probe coherence (WO-00 B.2 inheritance).

      COUNTER_IDENTIFICATION_PROBE: Identify the life counter / HUD region
          (WO-00 B.3 inheritance). Note: V4 substrate handles this passively
          per WO-V4-AUDIT A.6; this dispatch cell may be NOT_APPLICABLE
          (Director may rule at Sub-Phase 4).

    Slot-level root attributes (3):
      FIRST_TOUCH_PROBE: Initial click sweep — V4's current cursor=4
          dispatch (per `captain.py` DISPATCH_TABLE entry `(4, "CLICK",
          "click")`). The Coverage pass per Sub-Phase 2 keystone.

      EGO_CONFIRMATION_PROBE: Re-confirm ego region after Foundation
          establishment (NAV/HYBRID worlds; deferred per Director Section G
          decision 3).

      LEVER_CONFIRMATION_PROBE: Re-probe a candidate lever to disambiguate
          between LEVER / REACTIVE / STATIC roles (Section 2.5.3 sub-library
          opening prerequisite).

    Sub-library variant-level attributes (4):
      LEVER_MECHANISM_DISCRIMINATION_PROBE: Distinguish TOGGLE vs CYCLE vs
          DIRECTIONAL vs OTHER lever mechanism (per Section 2.5.3 variant
          catalog work).

      CYCLE_PERIOD_DETECTION_PROBE: The cycle probe — V4's current cursor=5
          dispatch (per `captain.py` DISPATCH_TABLE entry `(5, "CLICK",
          "cycle")`). The variable-K cycle probe ship (WO-00 C.3).
          INVENT #3 sibling — operates against CompletionPredicate.
          CYCLE_RETURN_OBSERVED + DISTINCT_PROBES_AT_LEAST.

      TOGGLE_STATE_OBSERVATION_PROBE: For TOGGLE-mechanism levers,
          accumulate observed states across presses (Section 2.5.3
          variant catalog).

      DIRECTIONAL_EFFECT_PROBE: For DIRECTIONAL-mechanism levers,
          accumulate per-direction effects (Section 2.5.3 variant catalog).

    Sentinel (1):
      OUT_OF_TAPE: The captain emits this sentinel when it cannot find
          an actionable attribute. Used by the Section 3.7 out-of-tape
          behavior + three-case classifier (Sub-Phase 4 work). The
          sentinel allows the dispatch table to record "no attribute
          to fill" rather than returning None.

    Future variants per Section 4 deferred work:
      LEVER_TYPING (post-mechanism), CAUSAL_LINK_MAPPING (post-typing),
      EGO_NAVIGATION (NAV-side dispatch — Sub-Phase 4 per Director ruling),
      WIN_STATE_HYPOTHESIS (Section 5+ goal-pursuit), etc.

    Not enumerated here per Section 4 deferral. WO-BLUEPRINT-06 wires the
    11 starting values into the dispatch table; Phase 2+ adds variants.
    """
    # Foundation attributes (3)
    WORLD_TYPE_PROBE = auto()
    EGO_MODE_PROBE = auto()
    COUNTER_IDENTIFICATION_PROBE = auto()

    # Slot-level root attributes (3)
    FIRST_TOUCH_PROBE = auto()
    EGO_CONFIRMATION_PROBE = auto()
    LEVER_CONFIRMATION_PROBE = auto()

    # Sub-library variant-level attributes (4)
    LEVER_MECHANISM_DISCRIMINATION_PROBE = auto()
    CYCLE_PERIOD_DETECTION_PROBE = auto()        # INVENT #3 sibling
    TOGGLE_STATE_OBSERVATION_PROBE = auto()
    DIRECTIONAL_EFFECT_PROBE = auto()

    # Causal-map / effect band (1) — WO-EFFECT-WALK-HOOK (WO2), June 11 2026.
    # Per CE Ruling 5: carries effect/transform semantics, NOT "causal link".
    # Supersedes the deferred CAUSAL_LINK_MAPPING name in the docstring above.
    # The captain emits this once LEVER_TYPING saturates, driving directed
    # presses that fill the WO1 LeverEffect store.
    LEVER_EFFECT_CHARACTERIZATION = auto()

    # Sentinel (1)
    OUT_OF_TAPE = auto()

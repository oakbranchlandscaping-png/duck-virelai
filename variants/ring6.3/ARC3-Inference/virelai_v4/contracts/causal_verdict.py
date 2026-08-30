"""
virelai_v4/contracts/causal_verdict.py — The BBA causal evidence taxonomy.

Per Blueprint Section 2.4.5 specification — the 8-value typed enum that
classifies each ProbeEvent's causal context. Each verdict is one of the
discriminating contexts that determines the LLR for a given probe per
BBA Layer One (Section 2.6.2).

NAME COLLISION NOTICE (WO-BLUEPRINT-04 Inheritance Pre-Audit Pattern v2):

V4 has an existing `CausalVerdict` frozen dataclass at
`virelai_v4/falsification/prediction_comparator.py:32` (V3.5-ported in
WO-01.A; CJ-01 "scientific kernel"). The V3.5 type measures match QUALITY
(outcome string + match_ratio / magnitude_ratio / spurious_px / etc.)
across 5 outcome strings: CONFIRMED, PARTIAL, FALSIFIED, SATURATED,
NO_PREDICTION.

This file ships the Blueprint Section 2.4.5 8-value typed Enum that
classifies causal CONTEXT (probe-caused vs autonomous vs spontaneous
vs zero-delta-under-various-preconditions). Different axis.

Per WO-00 A.5 inventory recommendation: "V4 needs both. The V3.5 outcome
remains as a quality measure inside ProbeEvent's match_quality field;
the new 8-value enum classifies causal context." The rename of V3.5's
`CausalVerdict` to `CausalMatchQuality` is deferred to Sub-Phase 5
vocabulary migration (per the WO-BLUEPRINT-04 "no urge to also fix"
discipline).

Import disambiguation: until the Sub-Phase 5 rename:
  from virelai_v4.contracts.causal_verdict import CausalVerdict   # Blueprint enum
  from virelai_v4.falsification.prediction_comparator import CausalVerdict  # V3.5 dataclass

Filed under WO-BLUEPRINT-04, May 19, 2026.
INVENT anchor: #2 family (BBA Layer One causal evidence taxonomy).
"""

from __future__ import annotations

from enum import Enum, auto


class CausalVerdict(Enum):
    """The 8-value causal evidence taxonomy per Blueprint Section 2.4.5.

    Each verdict is one of the discriminating contexts that determines the
    LLR for a given probe per BBA Layer One (Section 2.6.2). The LLR table
    is keyed on (CausalVerdict × log_score_axis) and supplies the per-axis
    log-score update on each ProbeEvent.

    Per Section 2.4.5 the 8 values split into three groups:

    High-discriminating (5 values) — strong evidence one way or the other:
        PROBE_CAUSED_CHANGE_ON_TARGET — Acted on this Slot; this Slot changed.
            Strong positive evidence for LEVER (target) or REACTIVE/STATIC
            depending on follow-up.

        PROBE_CAUSED_CHANGE_ON_OTHER — Acted on this Slot; another Slot
            changed. Strong evidence for LEVER (this Slot caused change
            elsewhere) and REACTIVE (the other Slot reacts).

        AUTONOMOUS_CHANGE — Slot changed; the agent took no action this
            frame. Strong evidence for REACTIVE.

        DIRECTIONAL_DISPLACEMENT — Slot translated rigidly under a
            directional action. Strong evidence for EGO.

        ZERO_DELTA_UNDER_CONFIRMED_PRECONDITIONS — Acted on this Slot
            with preconditions known to be met; no change resulted.
            Strong evidence for STATIC (or against LEVER under known
            conditions).

    Low-discriminating (2 values) — weak evidence requiring caution:
        SPONTANEOUS_TERMINAL_CHANGE — Slot changed at end-of-life. May
            be game-state-driven rather than agent-driven; weak evidence.

        ZERO_DELTA_UNDER_UNCONFIRMED_PRECONDITIONS — Acted on this Slot,
            preconditions unknown; no change resulted. Could be STATIC
            or LEVER-with-unmet-preconditions; weak in either direction.

    No verdict possible (1 value):
        NO_PROBE_THIS_FRAME — Used for autonomous-change observations
            (the agent didn't probe this Slot this frame; the change
            occurred without a probe to compare against).
    """
    # High-discriminating (5 values)
    PROBE_CAUSED_CHANGE_ON_TARGET = auto()
    PROBE_CAUSED_CHANGE_ON_OTHER = auto()
    AUTONOMOUS_CHANGE = auto()
    DIRECTIONAL_DISPLACEMENT = auto()
    ZERO_DELTA_UNDER_CONFIRMED_PRECONDITIONS = auto()

    # Low-discriminating (2 values)
    SPONTANEOUS_TERMINAL_CHANGE = auto()
    ZERO_DELTA_UNDER_UNCONFIRMED_PRECONDITIONS = auto()

    # No verdict possible (1 value)
    NO_PROBE_THIS_FRAME = auto()


class PreconditionStatus(Enum):
    """Whether preconditions for a probe were known at probe time.

    Per Blueprint Section 2.4.4 (ProbeEvent.preconditions_satisfied field).
    Read by the BBA Layer Two Confounding Suppression Bridge (deferred to
    Section 4) to dampen LLR contributions of unconfirmed-precondition
    observations.

    Three values:
        KNOWN_TRUE: preconditions confirmed met at probe time.
        KNOWN_FALSE: preconditions confirmed unmet at probe time.
        UNKNOWN: precondition status indeterminate.

    Section 2.4.4 notes: present in the scaffold's data model but consumed
    only when BBA Layer Two is implemented in Section 4. Section 1.12 BBA
    absorption discipline — "record raw observations; do not store only
    the derived label" — operationalizes here.
    """
    KNOWN_TRUE = auto()
    KNOWN_FALSE = auto()
    UNKNOWN = auto()

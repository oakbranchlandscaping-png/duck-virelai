"""
virelai_v4/contracts/probe_event.py — The structured per-probe event record.

Per Blueprint Section 2.4.4 specification — the structured per-event log
that LibraryObject.probe_history collects. Each ProbeEvent is a frozen
record of one probe interaction's outcome, including the Segment-binding-
at-probe-time, the world-state hash, the observed delta, the causal
verdict, and the precondition status.

Per WO-00 A.5 inheritance evidence:
    V3.5 had no ProbeEvent equivalent — only CellHistory's per-cell
    action attribution + falsification/evidence_accumulator's per-lever
    causal records. ProbeEvent is the V4 structured-per-event log
    (anticipated INVENT #4 family) that absorbs both V3.5 sources into
    a unified structured record.

Filed under WO-BLUEPRINT-04, May 19, 2026.
INVENT anchor: #4 — Class-change revocation + Segment/Slot factoring.

Note on ProbeOutput vs ProbeEvent:
    V4 has an existing ProbeOutcome class at contracts/probe_types.py.
    ProbeEvent is distinct — it records the FULL probe interaction
    (action + Segment binding + delta + verdict + preconditions) for
    BBA Layer One consumption. ProbeOutcome (V4-existing) is a smaller
    type used elsewhere. No conflict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from virelai_v4.contracts.causal_verdict import CausalVerdict, PreconditionStatus
from virelai_v4.contracts.delta_summary import DeltaSummary
from virelai_v4.contracts.segment import Segment


@dataclass(frozen=True)
class ProbeEvent:
    """A frozen record of one probe interaction's structured outcome.

    Per Blueprint Section 2.4.4:

        @dataclass(frozen=True)
        class ProbeEvent:
            frame: int
            action: GameAction
            target_coord: Optional[tuple[int, int]]
            segment_at_probe: Segment
            world_state_hash: int
            delta_observed: DeltaSummary
            causal_verdict: CausalVerdict
            preconditions_satisfied: PreconditionStatus

    Stored in LibraryObject.probe_history (PERSIST_LIVES_AND_LEVELS per
    Section 2.10). Appended once per probe by the substrate after the
    captain dispatches and the post-action frame is observed.

    Fields:
        frame: The frame index at which the probe fired.
        action: The action ID dispatched (int — V4 represents GameAction
              via integer enum value to avoid arcengine top-import in
              this contract module).
        target_coord: (row, col) for ACTION6 clicks; None for directional
              actions or actions without coordinates.
        segment_at_probe: The Layer-1 Segment binding for the target Slot
              at the moment of dispatch. Frozen — captures the Slot's
              shape-in-position state when the probe fired.
        world_state_hash: A canonical hash of the world state at probe
              time. For BBA Layer Two cross-Slot precondition learning
              (deferred to Section 4).
        delta_observed: The DeltaSummary derived from the post-action
              FrameDelta from this Slot's perspective.
        causal_verdict: The 8-value typed classification from
              Section 2.4.5 — the discriminating context the BBA
              Layer One LLR table uses.
        preconditions_satisfied: KNOWN_TRUE / KNOWN_FALSE / UNKNOWN per
              Section 2.4.4. Consumed by BBA Layer Two for LLR damping
              (deferred to Section 4).
    """
    frame: int
    action: int                              # GameAction enum value
    target_coord: Optional[Tuple[int, int]]
    segment_at_probe: Segment
    world_state_hash: int
    delta_observed: DeltaSummary
    causal_verdict: CausalVerdict
    preconditions_satisfied: PreconditionStatus

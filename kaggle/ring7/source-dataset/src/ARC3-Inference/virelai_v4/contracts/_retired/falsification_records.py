"""
contracts/falsification_records.py

Immutable data contracts for the Falsification Primitive layer.

Carried forward verbatim from V3 (grade A). Pure frozen dataclasses
and enums. Zero logic. Zero imports from outside contracts/.

These types are the shared language between:
    crucible/falsification/primitives.py  (producers)
    tests/test_contracts/                 (consumers)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Primitive Registry
# ──────────────────────────────────────────────────────────────────────────────

@unique
class PrimitiveID(Enum):
    """
    Registry of all 13 falsification primitives across three families.

    Family A — Binary (immediate falsification, PASS/FAIL only):
        A1  ReactivityPresent
        A2  ConsistencyAboveFloor
        A3  CausalLinkExists
        A4  KingdomAssigned
        A5  AnchorPresent

    Family B — Continuous (scored, PASS/FAIL/INCONCLUSIVE):
        B1  ReactivityDeltaInRange
        B2  CausalStrengthAbove
        B3  ConsistencyVarianceBelow
        B4  ProbeCountSufficient
        B5  NeighborCoherenceAbove

    Family C — Rank-only (PASS/INCONCLUSIVE, never falsifies):
        C1  TopQuartileReactivity
        C2  TopCausalLink
        C3  LocalTensionPeak
    """

    # Family A
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"

    # Family B
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    B5 = "B5"

    # Family C
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


FAMILY_A: frozenset = frozenset({
    PrimitiveID.A1, PrimitiveID.A2, PrimitiveID.A3,
    PrimitiveID.A4, PrimitiveID.A5,
})

FAMILY_B: frozenset = frozenset({
    PrimitiveID.B1, PrimitiveID.B2, PrimitiveID.B3,
    PrimitiveID.B4, PrimitiveID.B5,
})

FAMILY_C: frozenset = frozenset({
    PrimitiveID.C1, PrimitiveID.C2, PrimitiveID.C3,
})


# ──────────────────────────────────────────────────────────────────────────────
# Outcome
# ──────────────────────────────────────────────────────────────────────────────

@unique
class PrimitiveOutcome(Enum):
    """
    Result classification for a single primitive evaluation.

    PASS:         Criterion met — hypothesis survives this check.
    FAIL:         Criterion violated — falsification triggered.
    INCONCLUSIVE: Insufficient ledger evidence to evaluate.
    """
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


# V3.5 re-export alias for WO spec naming
PrimitiveVerdict = PrimitiveOutcome


# ──────────────────────────────────────────────────────────────────────────────
# Evidence Records
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Witness:
    """
    A concrete counterexample produced when a primitive fails.

    Invariant: populated ONLY on FAIL outcomes.
    """
    primitive_id: PrimitiveID
    step: int
    observed_value: float
    expected_value: float


@dataclass(frozen=True)
class PrimitiveResult:
    """
    Return value of every primitive function.

    Invariant: witness is None unless outcome == FAIL.
    """
    primitive_id: PrimitiveID
    outcome: PrimitiveOutcome
    witness: Optional[Witness] = None


# V3.5 re-export alias for WO spec naming
FalsificationResult = PrimitiveResult


# ──────────────────────────────────────────────────────────────────────────────
# Test Plan
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TestPlan:
    """
    Immutable test specification. Constructed once. Never mutated.
    """
    primitive_ids: Tuple[PrimitiveID, ...]
    expected_outcomes: Tuple[PrimitiveOutcome, ...]


__all__ = [
    "PrimitiveID",
    "PrimitiveOutcome",
    "PrimitiveVerdict",
    "FAMILY_A",
    "FAMILY_B",
    "FAMILY_C",
    "Witness",
    "PrimitiveResult",
    "FalsificationResult",
    "TestPlan",
]

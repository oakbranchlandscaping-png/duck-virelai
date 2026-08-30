"""
contracts/hypothesis_bundle.py

V3.5-native WinHypothesisBundle — Phase 2 output artifact.

Carried forward from V3 (grade A). All 10 invariants enforced.

Schema version: "3.5"

Design invariants:
    - Frozen dataclasses throughout (hashable, immutable)
    - CrucibleGate enforces <= 2 survivors (competition constraint)
    - world_model_hash binds this bundle to exactly one WorldModel
    - cycle_id traces back to the episode step that produced it
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

HYPOTHESIS_SCHEMA_VERSION = "3.5"
ACCEPTED_HYPOTHESIS_SCHEMA_VERSIONS = frozenset(["3.5"])

# All hypothesis types — generator must attempt all.
# WO-FORGE-05: LEVER_ENUMERATION and LEVER_REPLAY added for machine-aware search.
HYPOTHESIS_TYPES = frozenset([
    "NAV_TO_TARGET",
    "CONTACT_WIN",
    "COUNTER_TO_ZERO",
    "FILL_WIN",
    "SYMMETRY_WIN",
    "CLEAR_WIN",
    "STATE_MATCH_WIN",
    "EXPLORATION_PRIOR",
    # FORGE-05: machine-aware enumeration (Gray code, FINITE_SEARCH)
    "LEVER_ENUMERATION",    # Activate a specific subset of levers
    "LEVER_REPLAY",         # Replay a banked winning lever subset (confidence=1.0)
    # FORGE-GATE-02: depth sequence enumeration (DIRECTIONAL machines)
    "DEPTH_ENUMERATION",    # Click levers N times from spawn (DIRECTIONAL / VC33)
    "DEPTH_REPLAY",         # Replay a banked winning depth sequence (confidence=1.0)
])


@dataclass(frozen=True)
class WinHypothesis:
    """
    A single falsifiable hypothesis about the game's winning condition.

    Fields map to the WO spec:
        type              — one of HYPOTHESIS_TYPES
        goal_predicate    — what must be true for a win
        progress_metric   — how progress toward the goal is measured
        terminal_signature — observable signal that the goal is achieved
        minimal_falsifier — cheapest action sequence that would disprove this
        expected_signal   — what the solver expects to see if hypothesis is correct
        confidence        — P(winning | WorldModel_evidence), in [0, 1]
    """
    type: str
    goal_predicate: str
    progress_metric: str
    terminal_signature: str
    minimal_falsifier: str
    expected_signal: str
    confidence: float
    evidence_count: int = 0
    target_value: Optional[int] = None
    falsification_criteria: Tuple[str, ...] = ()
    supporting_criteria: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.type not in HYPOTHESIS_TYPES:
            raise ValueError(f"Unknown hypothesis type: {self.type!r}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Hypothesis confidence {self.confidence} out of [0, 1]"
            )
        if self.evidence_count < 0:
            raise ValueError(
                f"evidence_count must be non-negative, got {self.evidence_count}"
            )


@dataclass(frozen=True)
class WinHypothesisBundle:
    """
    Phase 2 output: ranked, falsified set of hypotheses.

    Invariants enforced in __post_init__:
        1. artifact_name == "WinHypothesisBundle"
        2. schema_version in ACCEPTED_HYPOTHESIS_SCHEMA_VERSIONS
        3. world_model_hash non-empty
        4. hypotheses non-empty
        5. len(hypotheses) <= 2  (competition constraint)
        6. Each hypothesis has required fields (enforced by WinHypothesis)
        7. confidence in [0, 1] (enforced by WinHypothesis)
        8. hypotheses[0].confidence >= hypotheses[-1].confidence (ranked)
        9. No hypothesis with confidence == 0 survives
       10. cycle_id non-empty
    """
    artifact_name: str
    schema_version: str
    world_model_hash: str
    hypotheses: Tuple[WinHypothesis, ...]
    cycle_id: str

    # Diagnostics (informational)
    candidates_before_crucible: int = 0
    crucible_rejections: int = 0

    # V3.5 addition: lever data flows Phase 2 → Phase 3 → Phase 4
    # LeverRegistry records pass this tuple to ExecutionProtocol.confirmed_levers
    confirmed_levers: Tuple = ()

    def __post_init__(self) -> None:
        # Inv-1: artifact_name
        if self.artifact_name != "WinHypothesisBundle":
            raise ValueError(
                f"artifact_name must be 'WinHypothesisBundle', "
                f"got {self.artifact_name!r}"
            )
        # Inv-2: schema_version
        if self.schema_version not in ACCEPTED_HYPOTHESIS_SCHEMA_VERSIONS:
            raise ValueError(
                f"schema_version {self.schema_version!r} not in "
                f"{ACCEPTED_HYPOTHESIS_SCHEMA_VERSIONS}"
            )
        # Inv-3: world_model_hash
        if not self.world_model_hash:
            raise ValueError("world_model_hash must be non-empty")
        # Inv-4: hypotheses non-empty
        if not self.hypotheses:
            raise ValueError("hypotheses must be non-empty (K >= 1)")
        # Inv-5: K <= 2
        if len(self.hypotheses) > 2:
            raise ValueError(
                f"hypotheses must contain <= 2 entries, "
                f"got {len(self.hypotheses)}"
            )
        # Inv-8: confidence ordering
        if (
            len(self.hypotheses) == 2
            and self.hypotheses[0].confidence < self.hypotheses[1].confidence
        ):
            raise ValueError(
                "hypotheses[0].confidence must be >= hypotheses[1].confidence"
            )
        # Inv-9: no zero-confidence survivors
        for i, h in enumerate(self.hypotheses):
            if h.confidence == 0.0:
                raise ValueError(
                    f"hypotheses[{i}] has confidence == 0.0; "
                    f"zero-confidence hypotheses must not survive Crucible"
                )
        # Inv-10: cycle_id
        if not self.cycle_id:
            raise ValueError("cycle_id must be non-empty")


__all__ = [
    "WinHypothesis",
    "WinHypothesisBundle",
    "HYPOTHESIS_SCHEMA_VERSION",
    "ACCEPTED_HYPOTHESIS_SCHEMA_VERSIONS",
    "HYPOTHESIS_TYPES",
]

"""
contracts/action_reality_report.py

ActionRealityReport — V3.5 Phase 1 sub-artifact produced by OpeningRoverGambit.

Carried forward from V3 contracts/action_reality_report.py (252 lines, grade B).

DELTA INVARIANT — enforced throughout Phase 1:
    StepDelta: Frame_t+1 - Frame_t (the only admissible delta for inference)
    SpanDelta: Frame_t+k - Frame_t (telemetry only, never classification)

Design notes:
  - baseline_signature stored as tuple-of-tuples (np.ndarray not hashable).
  - displacement_map stored as tuple of (action_id, dx, dy) triples.
  - eq=False on mutable-field containers; frozen=True still enforced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# ActionClassification enum
# ---------------------------------------------------------------------------

class ActionClassification(str, Enum):
    NOOP = "NOOP"
    COHERENT_DISPLACEMENT = "COHERENT_DISPLACEMENT"
    LOCALIZED_DELTA = "LOCALIZED_DELTA"
    GLOBAL_DELTA = "GLOBAL_DELTA"


# ---------------------------------------------------------------------------
# ActionProbeRecord — frame-native probe record
# ---------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class ActionProbeRecord:
    """
    Frame-native probe record for one action_id from OpeningRoverGambit.

    step_delta_1 = frame_after_1 - frame_before_1 (StepDelta)
    step_delta_2 = frame_after_2 - frame_before_2 (StepDelta)

    Frames stored as tuple-of-tuples for frozen compatibility.
    """
    action_id: int
    frame_before_1: tuple
    frame_after_1: tuple
    step_delta_1: tuple
    frame_before_2: tuple
    frame_after_2: tuple
    step_delta_2: tuple


# ---------------------------------------------------------------------------
# AgentStructure — multi-class geometric agent description
# ---------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class AgentStructure:
    """
    Complete geometric description of the moving agent.

    Represents the agent as a multi-class footprint rather than a single
    scalar class identity.
    """
    footprint_mask: Optional[frozenset]     # frozenset of (row, col) at spawn
    agent_value_set: frozenset              # all class_ids in footprint
    primary_class_id: Optional[int]         # class_id with most pixels
    action_translation_map: Tuple[Tuple[int, int, int], ...]  # (action_id, dr, dc)
    layout_coherence: Optional[float]       # mean layout preservation [0, 1]
    footprint_pixel_count: int
    detection_method: str                   # GEOMETRY | VALUE_FALLBACK | BLOCKED_AT_SPAWN | DEFORMABLE_MOVER
    vote_margins: Tuple[Tuple[int, float], ...] = ()    # (action_id, margin)
    overlap_ratios: Tuple[Tuple[int, float], ...] = ()  # (action_id, ratio)


# ---------------------------------------------------------------------------
# EgoPartition — SelfLocalization bootstrap output
# ---------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class EgoPartition:
    """
    Output of SelfLocalization bootstrap.
    Defines the EGO/WORLD channel boundary.
    """
    agent_value_set: frozenset
    convergence_status: str     # STABLE | CONVERGENCE_UNSTABLE | BOOTSTRAP_CONTRADICTION | SINGLE_PASS | EMPTY
    iteration_count: int


# ---------------------------------------------------------------------------
# SelfModel — empirical agent identity (NAV worlds only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class SelfModel:
    """
    Empirically identified agent entity.

    displacement_map:          tuple of (action_id, dx, dy) triples
    localization_confidence:   fraction of confirmed directional actions [0, 1]
    agent_structure:           full AgentStructure or None
    agent_value_set:           canonical multi-class identity
    provisional_agent_value_set: candidates before confirmation
    """
    displacement_map: Tuple[Tuple[int, int, int], ...]
    localization_confidence: float
    agent_structure: Optional[AgentStructure] = None
    agent_value_set: frozenset = frozenset()
    provisional_agent_value_set: frozenset = frozenset()


# ---------------------------------------------------------------------------
# ActionRealityReport — top-level Gambit output
# ---------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class ActionRealityReport:
    """
    Top-level output of OpeningRoverGambit.

    baseline_signature:     tuple-of-tuples encoding ambient-drift region.
    life_counter_region:    (row_min, row_max, col_min, col_max) or None.
    action_liveness_map:    tuple of (action_id, classification) pairs.
    world_type:             "NAV" | "CLICK" | "GLOBAL" | "UNKNOWN".
    regime_confidence:      fraction confirming the winning regime [0, 1].
    self_model:             SelfModel if NAV world; None otherwise.
    probe_evidence_log:     tuple of evidence dicts.
    probe_actions_consumed: total env steps consumed during Gambit.
    """
    baseline_signature: Tuple
    life_counter_region: Optional[Tuple[int, int, int, int]]
    action_liveness_map: Tuple[Tuple[int, str], ...]    # (action_id, classification)
    world_type: str
    regime_confidence: float
    self_model: Optional[SelfModel]
    probe_evidence_log: Tuple
    probe_actions_consumed: int

    # Delta fingerprints from Gambit probe pairs
    action_delta_signatures: Tuple[Tuple[int, Optional[Tuple]], ...] = ()

    # Per-action reproducibility
    reproducibility_confirmed: Tuple[Tuple[int, bool], ...] = ()

    # Life counter detection
    life_counter_type: Optional[str] = None
    geometric_life_counter: Optional[Tuple] = None

    # Per-probe StepDelta trace (telemetry)
    sequential_probe_trace: Tuple = ()

    # CohesiveUnitDiscovery v2 probe records
    action_probes: Tuple = ()

    # Final AgentStructure after detection
    agent_structure: Optional[AgentStructure] = None

    # HUD pixel mask (WO-HUD-MASK-FLOW-01): boolean array from detect_hud_mask().
    # True = HUD pixel, exclude from delta measurements.
    # Set by gambit.run() when edge-aligned HUD bar is detected.
    # NOTE: stored as-is (numpy array); eq=False on the class prevents hash issues.
    hud_mask: Optional[object] = None


__all__ = [
    "ActionClassification",
    "ActionProbeRecord",
    "AgentStructure",
    "EgoPartition",
    "SelfModel",
    "ActionRealityReport",
]

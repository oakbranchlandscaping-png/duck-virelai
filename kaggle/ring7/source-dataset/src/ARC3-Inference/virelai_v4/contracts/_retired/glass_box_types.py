"""
contracts/glass_box_types.py

Auxiliary frozen types for GlassBoxDossier.

Split from glass_box_dossier.py to keep both files under 300 lines.
All dataclasses are frozen (V3 had mutable EntropySnapshot — fixed here).
No behavior beyond __post_init__ validation. No methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GLASS_BOX_SCHEMA_VERSION = "1.0"

# EntropySnapshot weights (fixed — never inferred at runtime)
W1_HYPOTHESIS = 0.5
W2_ROLE = 0.3
W3_GOAL = 0.2


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TerminalStatus(Enum):
    """How the session ended."""
    TERMINAL = "TERMINAL"
    ABORT = "ABORT"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


class QSPIMode(Enum):
    """Qwen state during this session."""
    ACTIVE = "ACTIVE"
    STUB = "STUB"
    UNAVAILABLE = "UNAVAILABLE"


class AuditVerdict(Enum):
    """WorldReportAudit Tier 1 gate verdict."""
    CLEAN = "CLEAN"
    DEGRADED = "DEGRADED"
    CORRUPT = "CORRUPT"


class FailureBucket(Enum):
    """Top-level failure bucket."""
    GOVERNANCE = "GOVERNANCE"
    EPISTEMIC = "EPISTEMIC"
    MECHANICAL = "MECHANICAL"


# ---------------------------------------------------------------------------
# EntropySnapshot (FROZEN — was mutable in V3, fixed for V3.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EntropySnapshot:
    """
    Entropy state at one step. Logged at computation time,
    never inferred post-hoc.

    global_uncertainty = W1*hypothesis_entropy + W2*role_entropy + W3*goal_entropy
    """
    timestamp: int
    cycle_id: int
    hypothesis_entropy: float
    role_entropy: float
    goal_entropy: float
    global_uncertainty: float
    horizon_limit: int
    commitment_threshold: float


# ---------------------------------------------------------------------------
# Section A — Phase Timeline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PhaseTransitionEvent:
    """DERIVED from SessionEvent PHASE_TRANSITION events."""
    step_index: int
    from_phase: str
    to_phase: str
    timestamp: float
    guard_condition: Optional[str] = None
    entropy_snapshot: Optional[EntropySnapshot] = None


# ---------------------------------------------------------------------------
# Section B — Artifact Snapshots
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArtifactSnapshotRecord:
    """DERIVED from artifact boundary events."""
    world_model_hash: str = ""
    hypothesis_bundle_hash: str = ""
    execution_protocol_hash: str = ""
    snapshot_step_indices: Tuple[Tuple[str, int], ...] = ()


# ---------------------------------------------------------------------------
# Section C — QSPI Transcript
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QSPITranscript:
    """DERIVED. Required for VALID dossier."""
    qspi_mode: QSPIMode
    wib_hash: str = ""
    rosetta_dsl_version: Optional[str] = None
    qwen_output_verbatim: Optional[str] = None
    qwen_output_hash: Optional[str] = None
    rosetta_validation: Optional[str] = None
    compile_result: str = "SKIPPED"
    rejection_cause: Optional[str] = None
    falsifier_extracted: Optional[str] = None
    falsifier_executed: Optional[bool] = None
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Section D — Step Trace
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StepTrace:
    """DERIVED from EXECUTION phase events. One per Phase 4 action step."""
    step_index: int
    phase: str
    action_id: Optional[int] = None
    progress_metric_type: Optional[str] = None
    progress_metric_available: bool = False
    progress_metric_value_before: Optional[float] = None
    progress_metric_value_after: Optional[float] = None
    progress_metric_delta: Optional[float] = None
    friction: Optional[float] = None
    levels_completed: int = 0


# ---------------------------------------------------------------------------
# Section E — Hypothesis Lifecycle
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HypothesisEvent:
    """DERIVED from hypothesis lifecycle events."""
    step_index: int
    hypothesis_id: str
    event_type: str         # PROPOSED | ACCEPTED | REJECTED
    confidence: float
    entropy_before: Optional[float] = None
    entropy_after: Optional[float] = None
    rejection_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Section F — WorldReportAudit
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorldReportAudit:
    """DERIVED. Tier 1 gate. Runs before any downstream analysis."""
    agent_detected: bool
    agent_detection_confidence: float
    agent_detection_method: str
    click_sites_detected: int
    click_sites_evidence_basis: str
    classes_with_causal_evidence: int
    classes_appearance_only: int
    world_type_classification: str
    world_type_confidence: float
    reachability_coverage: float
    topology_stable_during_t1: bool
    audit_verdict: AuditVerdict
    degradation_reasons: Tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Artifact Grades
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArtifactGrade:
    """Grade for one artifact. Mean of binary criteria scores."""
    artifact_type: str
    grade: float
    criteria_scores: Tuple[Tuple[str, bool], ...] = ()


@dataclass(frozen=True)
class ArtifactGradeRecord:
    """Per-artifact quality scores."""
    world_model: ArtifactGrade
    hypothesis_bundle: ArtifactGrade
    execution_protocol: ArtifactGrade
    execution_outcome: ArtifactGrade


# ---------------------------------------------------------------------------
# CycleSummary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CycleSummary:
    """One per compression cycle. Enables WANDERING detection."""
    cycle_id: int
    entropy_at_start: EntropySnapshot
    entropy_at_end: EntropySnapshot
    hypotheses_pruned: int
    hypotheses_surviving: int
    memory_adjustments_applied: int
    falsification_events: int
    terminal_state: str
    entropy_delta: float


# ---------------------------------------------------------------------------
# FailureClassification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FailureClassification:
    """DERIVED. Typed failure classification with evidence references."""
    final_classification: str
    failure_bucket: Optional[FailureBucket] = None
    triggered_at_step: Optional[int] = None
    evidence_references: Tuple[int, ...] = ()
    runtime_tags: Tuple[str, ...] = ()
    analytic_tags: Tuple[str, ...] = ()
    classification_source: str = "UNKNOWN"


__all__ = [
    "GLASS_BOX_SCHEMA_VERSION",
    "W1_HYPOTHESIS",
    "W2_ROLE",
    "W3_GOAL",
    "TerminalStatus",
    "QSPIMode",
    "AuditVerdict",
    "FailureBucket",
    "EntropySnapshot",
    "PhaseTransitionEvent",
    "ArtifactSnapshotRecord",
    "QSPITranscript",
    "StepTrace",
    "HypothesisEvent",
    "WorldReportAudit",
    "ArtifactGrade",
    "ArtifactGradeRecord",
    "CycleSummary",
    "FailureClassification",
]

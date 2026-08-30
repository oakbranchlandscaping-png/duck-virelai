"""
contracts/glass_box_dossier.py

GlassBoxDossier — first-class diagnostic artifact.

AUTHORITY: GLASS_BOX_DOSSIER_SPEC v1.0 / Section 3

First-class artifact alongside WorldModel, WinHypothesisBundle, ExecutionProtocol.
No behavior. Schema only. Every solver session that reaches any terminal state
must produce a schema-valid GlassBoxDossier or raise a hard fault.

Architecture:
  - GlassBoxDossier is the top-level container.
  - SessionEventStream (primary source of truth) is stored verbatim.
  - All other sections are DERIVED from the stream post-session.
  - If any derived field contradicts the stream, the stream wins.

Auxiliary types live in glass_box_types.py (companion file).
Both files stay under 300 lines.

V3.5 change: ALL dataclasses are frozen (V3 had mutable EntropySnapshot).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .glass_box_types import (
    ArtifactGradeRecord,
    ArtifactSnapshotRecord,
    CycleSummary,
    FailureClassification,
    HypothesisEvent,
    PhaseTransitionEvent,
    QSPITranscript,
    StepTrace,
    TerminalStatus,
    WorldReportAudit,
)


@dataclass(frozen=True)
class GlassBoxDossier:
    """
    GlassBoxDossier — primary diagnostic artifact.

    No behavior. Schema only. First-class alongside WorldModel and
    WinHypothesisBundle. Every session must produce a schema-valid dossier
    or raise a hard fault.

    Fields marked DERIVED are computed from event_stream post-session.
    If any derived field contradicts the stream, the stream wins.
    """
    session_id: str
    level_id: str
    schema_version: str
    terminal_status: TerminalStatus
    terminal_reason: Optional[str]

    # Primary source of truth — typed as tuple for frozen compatibility
    event_stream: tuple

    # DERIVED sections
    phase_timeline: Tuple[PhaseTransitionEvent, ...]
    artifact_snapshots: ArtifactSnapshotRecord
    qspi_transcript: QSPITranscript
    step_trace: Tuple[StepTrace, ...]
    hypothesis_lifecycle: Tuple[HypothesisEvent, ...]
    world_report_audit: WorldReportAudit
    artifact_grades: ArtifactGradeRecord
    cycle_summaries: Tuple[CycleSummary, ...]
    failure_classification: FailureClassification


__all__ = ["GlassBoxDossier"]

"""
contracts/discovery_dossier.py

Phase 1 telemetry artifact. Flows to diagnostics only — does NOT flow to Phase 2.
The WorldModel is the sole cross-phase artifact from Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ProbeStatistics:
    actions_consumed: int
    deltas_observed: int
    novelty_rate: float  # fraction of probes that produced novel deltas


@dataclass(frozen=True)
class GateScore:
    gate_name: str
    passed: bool
    score: float
    threshold: float


@dataclass(frozen=True)
class CensusSummary:
    ego_identified: bool
    world_type: str
    reactive_class_count: int
    inert_class_count: int


@dataclass(frozen=True)
class DiscoveryDossier:
    rover_gambit_classification: str
    census_summary: CensusSummary
    probe_statistics: ProbeStatistics
    gate_scores: Tuple[GateScore, ...]
    budget_consumed: int
    budget_total: int


__all__ = [
    "ProbeStatistics",
    "GateScore",
    "CensusSummary",
    "DiscoveryDossier",
]

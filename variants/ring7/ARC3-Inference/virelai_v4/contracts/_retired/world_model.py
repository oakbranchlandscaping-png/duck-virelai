"""
contracts/world_model.py

WorldModel — V3.5 Phase 1 boundary artifact.

Unified from V3 contracts/world_model.py + contracts/artifacts.py.
This is the sole cross-phase artifact from Phase 1.
All fields are immutable (frozen dataclass).

SCHEMA_VERSION must match between builder and validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .object_class import ObjectClass
from .lever_artifact import LeverCensus

SCHEMA_VERSION = "3.5"
ACCEPTED_SCHEMA_VERSIONS = frozenset(["3.5"])


# ── Sub-contracts ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SelfModel:
    """Empirical agent identity (NAV worlds only)."""
    agent_class_id: int
    displacement_map: tuple         # ((action_id, dx, dy), ...)
    localization_confidence: float  # [0, 1]


@dataclass(frozen=True)
class ClickSignature:
    """Click affordance signature (CLICK worlds only)."""
    baseline_click_delta: tuple     # flattened delta fingerprint
    active_cell_count: int
    click_confidence: float         # [0, 1]


@dataclass(frozen=True)
class BaselineSignature:
    """Ambient drift measurement at spawn."""
    delta_px_mean: float
    delta_obj_mean: float
    delta_counter_mean: float
    sample_count: int               # must be >= 1


@dataclass(frozen=True)
class TransitionSignature:
    """One observed state-transition pattern."""
    trigger_type: str
    delta_signature: tuple
    repro_count: int


@dataclass(frozen=True)
class ReachabilitySummary:
    """Coverage and block statistics."""
    coverage_ratio: float   # [0, 1]
    block_rate: float       # [0, 1]
    confidence: float       # [0, 1]


@dataclass(frozen=True)
class DSMSOverlay:
    """Frozen snapshot of Dynamic Semantic Memory System state."""
    roles: tuple            # ((pixel_value, role_name), ...)
    update_count: int


# ── WorldModel ─────────────────────────────────────────────────────────────

_VALID_WORLD_TYPES = frozenset({"NAV", "CLICK", "HYBRID"})


@dataclass(frozen=True)
class WorldModel:
    """
    V3.5 Phase 1 artifact: mechanical world description.

    Produced by discovery/, validated at phase boundary.
    All fields are immutable (frozen dataclass).

    __post_init__ enforces 10 rejection criteria.
    """
    # ── Identity & versioning ──
    artifact_name: str              # must be "WorldModel"
    schema_version: str             # must be in ACCEPTED_SCHEMA_VERSIONS
    frame_hash: str                 # sha256[:16] of spawn frame
    cycle_id: str

    # ── Interaction regime ──
    world_type: str                 # "NAV" | "CLICK" | "HYBRID"
    world_type_confidence: float    # [0, 1]
    world_type_evidence_count: int  # >= 1

    # ── Self / control substrate (conditional) ──
    self_model: Optional[SelfModel]             # required if NAV or HYBRID
    click_signature: Optional[ClickSignature]   # required if CLICK or HYBRID

    # ── Object ontology ──
    object_classes: Tuple[ObjectClass, ...]      # must be non-empty

    # ── Baseline separation ──
    baseline_signature: BaselineSignature

    # ── Transition signatures ──
    transition_signatures: Tuple[TransitionSignature, ...]  # >= 1 entry

    # ── Reachability ──
    reachability_summary: ReachabilitySummary

    # ── Invariants ──
    invariant_set: Tuple[str, ...] = ()          # may be empty

    # ── DSMS overlay ──
    dsms: DSMSOverlay = None  # type: ignore[assignment]

    # ── FORGE lever census (WO-FORGE-01) ──
    # Populated by FORGE-02 and later. None in pre-FORGE builds.
    # Default None preserves backward compatibility with all existing tests and dumps.
    lever_census: Optional[LeverCensus] = None

    def __post_init__(self) -> None:
        # RC-2: world_type must be valid
        if self.world_type not in _VALID_WORLD_TYPES:
            raise ValueError(
                f"world_type must be one of {_VALID_WORLD_TYPES}, "
                f"got {self.world_type!r}"
            )
        # RC-3: transition_signatures non-empty
        if not self.transition_signatures:
            raise ValueError("transition_signatures must contain >= 1 entry")
        # RC-4: baseline sample_count > 0
        if self.baseline_signature.sample_count == 0:
            raise ValueError("baseline_signature.sample_count must be >= 1")
        # RC-5: object_classes non-empty
        if not self.object_classes:
            raise ValueError("object_classes must be non-empty")
        # RC-6: NAV/HYBRID requires self_model
        if self.world_type in {"NAV", "HYBRID"} and self.self_model is None:
            raise ValueError(
                f"world_type={self.world_type!r} requires self_model"
            )
        # RC-7: CLICK/HYBRID requires click_signature
        if self.world_type in {"CLICK", "HYBRID"} and self.click_signature is None:
            raise ValueError(
                f"world_type={self.world_type!r} requires click_signature"
            )
        # RC-8: world_type_confidence in [0, 1]
        if not (0.0 <= self.world_type_confidence <= 1.0):
            raise ValueError(
                f"world_type_confidence must be in [0, 1], "
                f"got {self.world_type_confidence}"
            )
        # RC-9: world_type_evidence_count >= 1
        if self.world_type_evidence_count < 1:
            raise ValueError(
                f"world_type_evidence_count must be >= 1, "
                f"got {self.world_type_evidence_count}"
            )
        # RC-10: schema_version non-empty
        if not self.schema_version:
            raise ValueError("schema_version must be non-empty")


__all__ = [
    "SCHEMA_VERSION",
    "ACCEPTED_SCHEMA_VERSIONS",
    "SelfModel",
    "ClickSignature",
    "BaselineSignature",
    "TransitionSignature",
    "ReachabilitySummary",
    "DSMSOverlay",
    "WorldModel",
]

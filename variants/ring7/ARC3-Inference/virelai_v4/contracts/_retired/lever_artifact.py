"""
contracts/lever_artifact.py

LeverArtifact schema — FORGE campaign Phase 1 contract.

Introduces the vocabulary for representing levers (independently
controllable world mechanisms) discovered during Phase 1 DISCOVERY.

Objects (in order):
    ActivationMethod      — physical mechanism enum
    TransitionClass       — measured dynamic behavior enum
    EffectLocality        — spatial effect classification enum
    TransitionProfile     — measured lever transition dynamics (frozen dataclass)
    LeverArtifact         — single lever in the world (frozen dataclass)
    LeverCensus           — all levers from one Phase 1 run (frozen dataclass)
    LeverState            — observed state of one lever at a moment (frozen dataclass)
    GoalConfiguration     — target state the machine must reach to win (frozen dataclass)
    WorldMachine          — complete state machine description (frozen dataclass)

Zone: ARTIFACT_WORLD_MODEL (same zone as WorldModel)
WO-FORGE-01, WO-FORGE-04
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


# ── Enums ─────────────────────────────────────────────────────────────────────

class ActivationMethod(str, Enum):
    """Physical mechanism by which a lever is triggered."""
    CLICK = "click"
    CONTACT = "contact"
    ADJACENCY = "adjacency"


class TransitionClass(str, Enum):
    """Measured dynamic behavior class of a lever's state over time.

    Names are empirical classifications — no game-specific vocabulary.
    """
    FINITE_CYCLE = "finite_cycle"
    SATURATING = "saturating"
    PROVISIONAL_DRIFT = "provisional_drift"


class EffectLocality(str, Enum):
    """Classification of where a lever's effect occurs relative to its
    activation coordinate.

    Resolves FORGE Finding F1 (LOCAL/REMOTE disagreement between V3 and V3.5)
    by giving it a first-class name in the schema.
    """
    LOCAL = "local"     # effect pixels near activation coord
    REMOTE = "remote"   # effect pixels far from activation coord
    GLOBAL = "global"   # effect spans entire grid


# ── TransitionProfile ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TransitionProfile:
    """Measured dynamics of a single lever's state transitions.

    Default state is UNPROBED: all fields indicate 'not yet measured'.
    observation_depth=0 means unprobed. observation_depth=4 means cycle
    probe complete (FORGE-03).

    Validation rules:
    - FINITE_CYCLE requires cycle_length >= 2 and states_observed >= cycle_length
    - Non-FINITE_CYCLE requires cycle_length is None
    - observation_depth >= 0
    - states_observed >= 0
    """
    transition_class: TransitionClass = TransitionClass.PROVISIONAL_DRIFT
    cycle_length: Optional[int] = None
    states_observed: int = 0
    deterministic: bool = False
    observation_depth: int = 0
    drift_pixel_count: int = 0  # WO-FORGE-03-PATCH-D: monotonically-drifting pixels
    mechanic_class: str = "UNKNOWN"  # WO-FORGE-GATE-02: TOGGLE/DIRECTIONAL/SATURATED/UNKNOWN
    direction_vector: Optional[Tuple[int, int]] = None  # WO-KNIFE-11: (delta_row, delta_col) per click
    direction_label: Optional[str] = None  # WO-KNIFE-11: "UP"/"DOWN"/"LEFT"/"RIGHT"/None

    def __post_init__(self) -> None:
        _valid_mc = ("TOGGLE", "DIRECTIONAL", "SATURATED", "UNKNOWN")
        if self.mechanic_class not in _valid_mc:
            raise ValueError(
                f"mechanic_class must be one of {_valid_mc}, "
                f"got {self.mechanic_class!r}"
            )
        if self.drift_pixel_count < 0:
            raise ValueError(
                f"drift_pixel_count must be >= 0, got {self.drift_pixel_count}"
            )
        if self.observation_depth < 0:
            raise ValueError(
                f"observation_depth must be >= 0, got {self.observation_depth}"
            )
        if self.states_observed < 0:
            raise ValueError(
                f"states_observed must be >= 0, got {self.states_observed}"
            )
        if self.transition_class == TransitionClass.FINITE_CYCLE:
            if self.cycle_length is None:
                raise ValueError(
                    "transition_class=FINITE_CYCLE requires cycle_length to be set"
                )
            if self.cycle_length < 2:
                raise ValueError(
                    f"transition_class=FINITE_CYCLE requires cycle_length >= 2, "
                    f"got {self.cycle_length}"
                )
            if self.states_observed < self.cycle_length:
                raise ValueError(
                    f"transition_class=FINITE_CYCLE requires states_observed >= "
                    f"cycle_length ({self.cycle_length}), got {self.states_observed}"
                )
        else:
            if self.cycle_length is not None:
                raise ValueError(
                    f"transition_class={self.transition_class!r} must have "
                    f"cycle_length=None, got {self.cycle_length}"
                )


# ── LeverArtifact ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LeverArtifact:
    """One lever in the world — one independently controllable mechanism.

    Contains: location, activation method, effect region, and (after
    FORGE-03) transition dynamics.

    lever_id format: "LEVER_{world_type}_{class_id}_{row}_{col}"
    e.g. "LEVER_CLICK_9_24_60"
    Stable. Derived from representative coordinate. Not random.

    Validation rules:
    - lever_id must be non-empty
    - control_location must be a tuple of exactly 2 non-negative ints
    - effect_region_count must equal len(effect_region)
    - confidence must be in [0.0, 1.0]
    - If effect_region is non-empty and delta_hash is None: ValueError
    """
    lever_id: str
    control_location: Tuple[int, int]
    activation_method: ActivationMethod
    source_cluster_id: Optional[str]
    effect_region: Tuple[Tuple[int, int], ...]
    effect_region_count: int
    effect_locality: EffectLocality
    transition_profile: TransitionProfile
    delta_hash: Optional[str]
    confidence: float

    def __post_init__(self) -> None:
        if not self.lever_id:
            raise ValueError("lever_id must be a non-empty string")
        if (
            len(self.control_location) != 2
            or not all(isinstance(v, int) and v >= 0 for v in self.control_location)
        ):
            raise ValueError(
                f"control_location must be a tuple of exactly 2 non-negative ints, "
                f"got {self.control_location!r}"
            )
        if self.effect_region_count != len(self.effect_region):
            raise ValueError(
                f"effect_region_count ({self.effect_region_count}) must equal "
                f"len(effect_region) ({len(self.effect_region)})"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if self.effect_region and self.delta_hash is None:
            raise ValueError(
                "effect_region is non-empty but delta_hash is None — "
                "effect region present but not hashed is inconsistent"
            )


# ── LeverCensus ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LeverCensus:
    """Summary container grouping all levers discovered in a single Phase 1 run.

    Embedded in WorldModel. Thin wrapper providing grouping and aggregate
    statistics.

    Levers are ordered by lever_id lexicographically.

    Validation rules:
    - lever_count must equal len(levers)
    - all_profiled is True only if every lever has observation_depth >= 4
    - If all_profiled: state_space_bound must not be None
    - If not all_profiled: state_space_bound must be None
    """
    levers: Tuple[LeverArtifact, ...]
    lever_count: int
    activation_method: ActivationMethod
    all_profiled: bool
    state_space_bound: Optional[int]
    world_machine: Optional["WorldMachine"] = None  # WO-FORGE-04: attached after probing

    def __post_init__(self) -> None:
        if self.lever_count != len(self.levers):
            raise ValueError(
                f"lever_count ({self.lever_count}) must equal "
                f"len(levers) ({len(self.levers)})"
            )
        actual_all_profiled = all(
            lever.transition_profile.observation_depth >= 4
            for lever in self.levers
        )
        if self.all_profiled and not actual_all_profiled:
            raise ValueError(
                "all_profiled=True but not all levers have observation_depth >= 4"
            )
        if self.all_profiled and self.state_space_bound is None:
            raise ValueError(
                "all_profiled=True requires state_space_bound to be set"
            )
        if not self.all_profiled and self.state_space_bound is not None:
            raise ValueError(
                f"all_profiled=False requires state_space_bound=None, "
                f"got {self.state_space_bound}"
            )


# ── LeverState ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LeverState:
    """Observed state of a single lever at a given moment.

    Records which pixel value the lever is showing, and how it was observed.
    Used both for current-state snapshots (from spawn frame) and post-action
    observations.

    WO-FORGE-04
    """
    lever_id: str
    # References LeverArtifact.lever_id.
    current_pixel_value: int
    # Dominant pixel value in the lever's effect_region at the time of
    # observation. This is the state label.
    observation_source: str
    # "spawn_frame"  — read directly from spawn frame
    # "post_probe"   — read after a probe cycle
    # "post_click"   — read after an execution click


# ── GoalConfiguration ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GoalConfiguration:
    """The target configuration the machine must reach to win.

    Also reused to represent the current configuration (with
    extraction_method="spawn_frame") so current and goal are
    comparable via the same schema.

    Validation:
    - confidence in [0.0, 1.0]
    - display_component_count >= 0
    - lever_goals must be a tuple

    WO-FORGE-04
    """
    lever_goals: Tuple[Tuple[str, int], ...]
    # Tuple of (lever_id, target_pixel_value) pairs, ordered by lever_id
    # lexicographically. Each pair says: lever X must be in pixel state Y.
    extraction_method: str
    # "display_region_match" — read from inert display components
    # "spawn_frame"          — read directly from spawn frame (current state)
    # "unknown"              — could not extract goal state
    confidence: float
    # Confidence in the goal reading. 1.0 = unambiguously mapped.
    # 0.0 = not found. Partial = n_mapped / n_levers.
    display_component_count: int
    # Number of inert display components found and mapped.
    # For FT09: should equal lever_count (8). 0 if not applicable.

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if self.display_component_count < 0:
            raise ValueError(
                f"display_component_count must be >= 0, "
                f"got {self.display_component_count}"
            )
        if not isinstance(self.lever_goals, tuple):
            raise ValueError(
                f"lever_goals must be a tuple, got {type(self.lever_goals).__name__}"
            )


# ── WorldMachine ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WorldMachine:
    """Complete state machine description for one FORGE-probed world.

    Combines lever topology (FORGE-03), current state (spawn frame), and
    goal state (display region analysis) into a single machine description.
    Phase 2 uses this to compute the minimum click sequence.

    Validation:
    - lever_count >= 0
    - len(state_variables) == lever_count
    - machine_class in ("FINITE_SEARCH", "DIRECTIONAL", "UNKNOWN")

    WO-FORGE-04
    """
    lever_count: int
    # Number of levers. Matches lever_census.lever_count.
    state_variables: Tuple[str, ...]
    # Lever IDs in lexicographic order — each is one state dimension.
    reachable_state_bound: Optional[int]
    # Product of all cycle_lengths when all_profiled=True, else None.
    current_state: Optional[GoalConfiguration]
    # Lever states at spawn. None if spawn frame reading failed.
    goal_state: Optional[GoalConfiguration]
    # Target configuration from display regions. None if unreadable.
    levers_requiring_action: Optional[Tuple[str, ...]]
    # Lever IDs where current_state ≠ goal_state.
    # None if current_state or goal_state is None.
    # Empty tuple () if machine is already at goal (win at spawn).
    machine_class: str
    # "FINITE_SEARCH" — all levers FINITE_CYCLE, goal readable
    # "DIRECTIONAL"   — levers are PROVISIONAL_DRIFT (VC33 type)
    # "UNKNOWN"       — cannot classify

    def __post_init__(self) -> None:
        if self.lever_count < 0:
            raise ValueError(
                f"lever_count must be >= 0, got {self.lever_count}"
            )
        if len(self.state_variables) != self.lever_count:
            raise ValueError(
                f"len(state_variables) ({len(self.state_variables)}) must equal "
                f"lever_count ({self.lever_count})"
            )
        valid_classes = ("FINITE_SEARCH", "DIRECTIONAL", "UNKNOWN")
        if self.machine_class not in valid_classes:
            raise ValueError(
                f"machine_class must be one of {valid_classes}, "
                f"got {self.machine_class!r}"
            )


# ── Public exports ────────────────────────────────────────────────────────────

__all__ = [
    "ActivationMethod",
    "TransitionClass",
    "EffectLocality",
    "TransitionProfile",
    "LeverArtifact",
    "LeverCensus",
    "LeverState",         # WO-FORGE-04
    "GoalConfiguration",  # WO-FORGE-04
    "WorldMachine",       # WO-FORGE-04
]

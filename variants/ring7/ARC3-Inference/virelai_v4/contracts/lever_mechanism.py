"""
virelai_v4/contracts/lever_mechanism.py — Cycle probe verdict contracts.

WO-CAMPAIGN3-PHASE3-01 — Cycle Probe Port (May 3, 2026).

Per V3.5 inheritance from ``Universal_Solver_v3_5/discovery/physics/cycle_probe.py``
and the Inheritance Diagnostic — Lever Typing (May 3, 2026), this module
declares the contracts the cycle probe consumes and produces:

    LeverMechanism      — categorical verdict per lever
    ActivationMode      — CLICK vs NAV_OCCUPANCY activation harness selection
    TransitionProfile   — per-lever cycle probe verdict (V3.5-faithful shape)
    LeverCensus         — aggregate of per-lever profiles for a level/game

V3.5 source citations:
    - TransitionProfile shape: cycle_probe.py:225-287
    - mechanic_class field values: cycle_probe.py:232 (DIRECTIONAL),
      cycle_probe.py:257 (SATURATED), cycle_probe.py:265 (TOGGLE/DIRECTIONAL)
    - LeverCensus state_space_bound semantics: cycle_probe.py:402-407

Naming discipline (per Apex Campaign Naming Discipline):
    - LeverMechanism (per-lever cycle probe verdict) is distinct from
      MechanicMemory.mechanic_type (level-wide classification at
      contracts/mechanic_memory.py:149). Coexistent; no rename per
      WO-PHASE3-01 Step 0 audit Recommendation 4.

Import sovereignty: contracts/ depends on stdlib only. No imports from
perception, library, targeting, strategy, or memory packages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class LeverMechanism(str, Enum):
    """Categorical cycle probe verdict for a single lever's mechanism class.

    V3.5 source: ``cycle_probe.py:232, 257, 265`` — mechanic_class field
    on TransitionProfile.

    Values:
        TOGGLE       — binary state oscillation (cycle_length == 2)
        CYCLE        — multi-step cycle (cycle_length > 2)
        DIRECTIONAL  — monotonic state change (no cycle, no saturation)
        SATURATED    — state stops responding after one or more activations
        UNKNOWN      — insufficient evidence YET; transient, more probing
                       resolves it ("keep going")
        UNDETERMINED — cap-exhausted; the lever's dynamics are not a function
                       of the masked frame (probed to the bound P and the
                       predicted pattern never settled). Terminal-for-this-
                       entry-state; more probing from the same E will not
                       resolve it (hidden/unrendered state). Distinct from
                       UNKNOWN — this one says "stop, the masked frame can't
                       capture this." (WO-DIVE-01 R1 / CE type-vocabulary
                       ruling.)
    """

    TOGGLE = "TOGGLE"
    CYCLE = "CYCLE"
    DIRECTIONAL = "DIRECTIONAL"
    SATURATED = "SATURATED"
    UNKNOWN = "UNKNOWN"
    UNDETERMINED = "UNDETERMINED"


class ActivationMode(str, Enum):
    """Activation harness selection for cycle probe.

    V3.5 source: ``cycle_probe.py:113-136`` (CLICK pattern via
    ``_adapter_click``).

    NAV_OCCUPANCY mode is V4 invention per WO-PHASE3-01 §6.1 — V3.5's
    5-game roster contained no NAV-world ego-occupancy levers, so V3.5
    has no equivalent activation harness.

    Values:
        CLICK          — V3.5-direct ACTION6 click at lever coordinate
        NAV_OCCUPANCY  — V4-extension cardinal navigation to lever cell
                         followed by step-on activation
    """

    CLICK = "CLICK"
    NAV_OCCUPANCY = "NAV_OCCUPANCY"


@dataclass(frozen=True)
class TransitionProfile:
    """Per-lever cycle probe verdict.

    V3.5 source: ``cycle_probe.py:225-287`` (TransitionProfile shape;
    V3.5 uses the name ``TransitionProfile`` from
    ``contracts/lever_artifact.py``). V4 declaration is V3.5-faithful
    with the V4 ``LeverMechanism`` enum substituted for V3.5's
    ``mechanic_class: str`` field.

    Attributes
    ----------
    mechanism : LeverMechanism
        Categorical verdict; see LeverMechanism docstring.
    cycle_length : Optional[int]
        Period of the detected cycle; None unless mechanism is TOGGLE
        (cycle_length == 2) or CYCLE (cycle_length > 2).
    states_observed : int
        Number of distinct toggle-pixel states observed during the probe;
        always <= observation_depth.
    deterministic : bool
        True when the probe reached a deterministic verdict (FINITE_CYCLE
        or SATURATING per V3.5 TransitionClass); False when verdict
        is PROVISIONAL_DRIFT (insufficient evidence within budget).
    observation_depth : int
        Number of activations performed; equal to V3.5 invariant 4.
    drift_pixel_count : int
        Number of monotonically-changing pixels observed; populated by
        the per-pixel sign-reversal classifier (V3.5 cycle_probe.py:209-221).
    direction_vector : Optional[Tuple[int, int]]
        Estimated (dr, dc) displacement vector when mechanism is
        DIRECTIONAL; None otherwise.
    direction_label : Optional[str]
        Human-readable direction label when direction_vector is present;
        None otherwise.
    """

    mechanism: LeverMechanism
    cycle_length: Optional[int]
    states_observed: int
    deterministic: bool
    observation_depth: int
    drift_pixel_count: int
    direction_vector: Optional[Tuple[int, int]]
    direction_label: Optional[str]


@dataclass(frozen=True)
class LeverCensus:
    """Aggregate of per-lever transition profiles for a level/game.

    V3.5 source: ``cycle_probe.py:292-459`` (probe_all_levers
    orchestrator; LeverCensus from ``contracts/lever_artifact.py``).

    Attributes
    ----------
    profiles : Dict[Tuple[int, int], TransitionProfile]
        Per-lever verdict, keyed by lever coordinate (row, col). Coordinate
        is the lever's kernel coordinate as established by Phase 2 contact
        reactivity (NavLeverCandidate.coordinate).
    state_space_bound : Optional[int]
        Product of cycle_lengths across all FINITE_CYCLE levers, or None
        when any lever has PROVISIONAL_DRIFT verdict (census incomplete).
        V3.5 source: ``cycle_probe.py:402-407``.
    all_profiled : bool
        True when every lever in the census has a deterministic verdict;
        False when any lever is UNKNOWN. V3.5 source: ``cycle_probe.py:407``.
    """

    profiles: Dict[Tuple[int, int], TransitionProfile]
    state_space_bound: Optional[int]
    all_profiled: bool


@dataclass
class CycleProbeState:
    """Per-frame state machine for cycle probe execution.

    WO-CAMPAIGN3-PHASE3-01-AMEND (May 3, 2026): integration adaptation per
    Director framing — port the intelligence; adapt the integration.

    Mirrors V4 stride probe pattern at ``library/stride_probe.py:96-138``.
    V3.5's synchronous probe API was the integration pattern V3.5 used
    because V3.5 had synchronous discovery phases. V4's
    ``choose_action(frames, latest_frame) -> GameAction`` has no env
    access; the framework owns ``env.step()``. The classification
    primitive (pure function on raw frames at ``cycle_probe.py:181-287``)
    transcends the container; the activation harness adapts.

    Per V3.5 invariant (``cycle_probe.py:169``): budget = 4 activations.
    Per WO-PHASE3-02 Step 0 Recommendation 2 ratified May 3, 2026:
    Interpretation (a) — budget at activation layer; navigation overhead
    acceptable for NAV_OCCUPANCY mode.

    State machine progression:
        Initialization → activation iteration (4×) → classification commit →
        verdict writeback → state clearance.

    Attributes
    ----------
    target_lever_coord : Tuple[int, int]
        (row, col) of the lever cell to activate; sourced from the
        ``NavLeverCandidate.coordinate`` produced by Phase 2 contact
        reactivity.
    target_object_region_id : int
        ``LibraryObject.region_id`` of the lever; used for verdict
        writeback at ``_commit_classification``.
    iteration : int
        Activation count (0-4). Classification fires at ``iteration == 4``
        per V3.5 budget invariant.
    accumulated_frames : List[np.ndarray]
        Spawn frame + post-activation frames. Length 5 when probe complete
        (1 spawn + 4 post-activation). Passed verbatim to V3.5
        ``_classify_transition`` at commit.
    mode : ActivationMode
        CLICK or NAV_OCCUPANCY; selects the activation harness.
    nav_path : Optional[List[int]]
        NAV_OCCUPANCY mode only. Cardinal action sequence computed by
        BFS from current ego position to lever cell (or off-lever for
        reset). None when not in active navigation.
    nav_path_index : int
        NAV_OCCUPANCY mode only. Cursor into ``nav_path``; advances per
        cardinal action emitted.
    nav_in_reset : bool
        NAV_OCCUPANCY mode only. False = navigating TO lever; True =
        navigating OFF lever to enable re-activation.
    """

    target_lever_coord: Tuple[int, int]
    target_object_region_id: int
    iteration: int
    accumulated_frames: List[np.ndarray]
    mode: ActivationMode
    nav_path: Optional[List[int]] = None
    nav_path_index: int = 0
    nav_in_reset: bool = False
    # WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): session-scoped
    # consecutive press counter. Distinct from `iteration` (which is
    # incremented during the V3.5 fixed-budget flow and remains as
    # backwards-compatible state-machine progression). Each fresh
    # captain dispatch of a target lever resets consecutive_press_count
    # to 0 via _initialize_cycle_probe_state.
    consecutive_press_count: int = 0
    # WO-OCD-CYCLE-PROBE-VARIABLE-K: HUD-masked grid hashes recorded
    # per press. Used for cycle detection — the post-press hash is
    # compared against earlier hashes in this session; a match
    # signals a cycle of period = (current_index - match_index).
    # state_hashes[0] is the spawn-frame hash (pre-press baseline).
    state_hashes: List[bytes] = field(default_factory=list)
    # WO-DIVE-01.1 — the 2-confirm falsification loop (frame-spanning state).
    # A detected recurrence does NOT commit a type on first sight; it enters
    # CONFIRMING, presses 2 more, and commits only when the predicted
    # continuation HOLDS (R4: confirmed, not first-seen). This state persists on
    # the CycleProbeState across frames — one press per frame, never a
    # within-frame loop (§4 permanent law: one frame in, one action out).
    #   confirming          — True while awaiting the 2 confirm presses.
    #   confirm_predictions — the masked hashes the next presses must reproduce
    #                         (self-loop: [last, last]; cycle: [h[j+1], h[j+2]]).
    #   confirm_index       — how many predicted transitions have held (0..2).
    #   pending_*           — the tentative verdict, committed iff both hold.
    confirming: bool = False
    confirm_predictions: List[bytes] = field(default_factory=list)
    confirm_index: int = 0
    pending_mechanism: Optional[LeverMechanism] = None
    pending_cycle_length: Optional[int] = None
    pending_saturation: bool = False


__all__ = [
    "LeverMechanism",
    "ActivationMode",
    "TransitionProfile",
    "LeverCensus",
    "CycleProbeState",
]

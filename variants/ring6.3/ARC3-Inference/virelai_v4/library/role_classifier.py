"""
virelai_v4/library/role_classifier.py — Role classifier for semantic objects.

Transplanted with refactor from V3.5 observer/knife/role_classifier.py.
V4 changes:
  - Returns LibraryRole instead of ObjectRole.
  - type_map is Optional (default None). When None, label-based rules skip.
  - CellEvidence dataclass carries CellHistory-derived behavioral evidence.
  - CellHistory evidence takes priority over type_map labels (Law 6).
  - INERT and OBSTACLE both map to LibraryRole.STATIC (V4 taxonomy collapse).

Public API:
    classify_role(region, grid_area, hud_class_ids, type_map=None, ...)
        -> Tuple[LibraryRole, float]
    classify_state_role(...) -> str
    classify_layer(state_role) -> str
    extract_hud_class_ids(grid_scan) -> Set[int]

Import sovereignty: virelai_v4.library.library_roles and stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Optional, Sequence, Set, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.counter_march import is_counter_march  # WO-E09-v2 D2


# ---------------------------------------------------------------------------
# CellEvidence
# ---------------------------------------------------------------------------

@dataclass
class CellEvidence:
    """CellHistory-derived behavioral evidence for one LibraryObject.

    Populated from per-cell CellHistory observations for an object's cells.
    Passed to classify_role() and classify_state_role() to enable
    CellHistory evidence priority over type_map labels (Law 6).

    CellHistory-primary fields:
        change_count    — count of the object's cells that changed at all
        cells_changed   — number of distinct cells with >= 1 change
        any_toggle      — any cell confirmed as binary toggle (is_toggle)
        total_changes   — cumulative change events across all object cells
        inert_depth     — consecutive actions with zero change (negative evidence)

    ClassEvidence-compatible fields used by confidence helpers:
        regime_confidence, observation_depth, lever_confidence,
        cell_observation_depth, effect_pixel_count, contact_count,
        all_profiled, cell_inert_depth
    """
    # CellHistory-primary
    change_count:   int   = 0
    cells_changed:  int   = 0
    any_toggle:     bool  = False
    total_changes:  int   = 0
    inert_depth:    int   = 0

    # Confidence-computation (ClassEvidence-compatible)
    regime_confidence:      float = 0.5
    observation_depth:      int   = 0
    lever_confidence:       float = 0.0
    cell_observation_depth: int   = 0
    effect_pixel_count:     int   = 0
    contact_count:          int   = 0
    all_profiled:           bool  = False
    cell_inert_depth:       int   = 0

    # Action Independence Metric (WO-C5-01/02) — populated from LibraryObject
    # action_independence_ratio: fraction of observed actions on which this object changed.
    # Near 1.0 → Life Counter candidate. Between → lever. Near 0.0 → background.
    actions_observed:          int   = 0
    action_independence_ratio: float = 0.0


# ---------------------------------------------------------------------------
# Label sets
# ---------------------------------------------------------------------------

_AGENT_LABELS: frozenset = frozenset({"AGENT", "EGO"})
_CONTROL_LABELS: frozenset = frozenset({
    "CONDITIONAL_LOCAL", "CONDITIONAL", "CONDITIONAL_GLOBAL", "RECEPTIVE",
})
_EFFECT_LABELS: frozenset = frozenset({
    "REACTIVE", "UNKNOWN_REACTIVE", "DISPLACEMENT",
})
_INERT_LABELS: frozenset = frozenset({
    "INERT_PROVISIONAL", "CONFIRMED_INERT", "SATURATED",
})
_STATIC_LABELS: frozenset = frozenset({"STATIC"})

# Coverage thresholds
_INERT_COVERAGE_THRESHOLD: float = 0.25   # CONFIRMED_INERT above this → STATIC canvas
_INERT_DOMINANT_THRESHOLD: float = 0.35   # any class above this → dominant background
_OBSTACLE_MAX_COVERAGE:    float = 0.10   # small static objects
_OBSTACLE_MIN_COMPACTNESS: float = 0.40   # compactness floor for obstacle classification


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def extract_hud_class_ids(grid_scan: Any) -> Set[int]:
    """Return class_ids that appear in full_width_strip HUD zones."""
    hud_values: Set[int] = set()
    for zone in grid_scan.zones:
        if zone.zone_type == "full_width_strip":
            hud_values.update(int(v) for v in zone.values)
    return hud_values


# ---------------------------------------------------------------------------
# Confidence helpers (CellEvidence-aware)
# ---------------------------------------------------------------------------

def _confidence_ego(ev: Optional[CellEvidence]) -> float:
    """EGO confidence: 0.70 base, boosted by regime_confidence. Range 0.70–0.95."""
    return 0.70 + 0.25 * (ev.regime_confidence if ev else 0.5)


def _confidence_lever(ev: Optional[CellEvidence]) -> float:
    """LEVER confidence: 0.50 base, boosted by observation depth. Range 0.50–0.95.

    CellEvidence.any_toggle adds +0.15 (Law 6: CellHistory priority).
    """
    if ev and ev.observation_depth > 0:
        depth_factor = min(1.0, ev.observation_depth / 4.0)
        confidence = 0.50 + 0.45 * depth_factor
    else:
        confidence = 0.50 + 0.30 * (ev.lever_confidence if ev else 0.0)
    if ev and ev.cell_observation_depth > 0:
        obs_factor = min(1.0, ev.cell_observation_depth / 20.0)
        confidence = min(0.95, confidence + 0.10 * obs_factor)
    if ev and ev.any_toggle:
        confidence = min(0.95, confidence + 0.15)
    return confidence


def _confidence_target(ev: Optional[CellEvidence]) -> float:
    """TARGET confidence: 0.55 base, boosted by effect/contact evidence. Range 0.55–0.95."""
    if ev:
        effect_factor = min(1.0, ev.effect_pixel_count / 100.0)
        contact_factor = min(1.0, ev.contact_count / 5.0)
        return min(0.95, 0.55 + 0.40 * max(effect_factor, contact_factor))
    return 0.55


def _confidence_static(ev: Optional[CellEvidence]) -> float:
    """STATIC confidence: 0.35 base, grows with inert evidence. Range 0.35–0.90."""
    if ev and ev.all_profiled:
        confidence = 0.60
    elif ev and ev.regime_confidence > 0.8:
        confidence = 0.50
    else:
        confidence = 0.35
    if ev and ev.observation_depth >= 2 and confidence < 0.70:
        confidence = min(0.70, 0.60 + 0.05 * ev.observation_depth)
    if ev and ev.cell_inert_depth > 0:
        inert_boost = min(0.25, ev.cell_inert_depth / 200.0)
        confidence = min(0.90, confidence + inert_boost)
    return confidence


# ---------------------------------------------------------------------------
# classify_role
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# COUNTER detection calibration (WO-C5-02)
# ---------------------------------------------------------------------------

_COUNTER_MIN_OBSERVATIONS: int   = 5     # Minimum actions observed before COUNTER can fire
_COUNTER_RATIO_THRESHOLD:  float = 0.80  # action_independence_ratio must exceed this
_COUNTER_MAX_COVERAGE:     float = 0.25  # Object must be < 25% of grid area (not the background)
# WO-E09-v2 D2: march recognizer. Required consecutive same-sign non-zero
# per-sync cell-count deltas. Set equal to the accumulator's obs-floor (the
# proven sibling threshold), not tuned to any game — the one tunable. The
# substrate keeps _COUNTER_MARCH_WINDOW + 1 counts of history (D1).
_COUNTER_MARCH_WINDOW:     int   = _COUNTER_MIN_OBSERVATIONS
_COUNTER_MARCH_CONFIDENCE: float = 0.70  # candidacy floor (matches _confidence_counter min)


def _confidence_reactive_active(active_frame_count: int) -> float:
    """REACTIVE confidence scaled by active_frame_count (WO-RM-04).

    0.70 at threshold (active_frame_count=2), 0.95 at active_frame_count >= 20.
    Linear interpolation between the two anchor points.
    """
    factor = min(1.0, (active_frame_count - 2) / 18.0)
    return 0.70 + 0.25 * factor


def _confidence_reactive_change(ev: Optional[CellEvidence]) -> float:
    """REACTIVE confidence based on V3.5 foundational principle (WO-CLEAN-10).

    Floor 0.55 represents single-change evidence (suggestive but minimal).
    Grows to 0.95 ceiling at change_count >= 20 (rich evidence).

    Per V3.5 chamber consultation (April 26 2026): any cell-level class change
    is sufficient evidence for REACTIVE; this helper scales confidence based on
    evidence richness rather than gating REACTIVE entry behind a threshold.
    """
    if ev is None or ev.change_count == 0:
        return 0.55  # shouldn't fire (rule guards on cell_active)
    return min(0.95, 0.55 + 0.40 * min(1.0, ev.change_count / 20.0))


def _confidence_static_observed(total_actions: int, ignore_score: float = 0.0) -> float:
    """STATIC confidence scaled by total observation frames (WO-RM-04).

    20 frames → 0.70, 50 frames → 0.85, 100+ frames → 0.95.
    Piecewise linear interpolation; ignore_score >= 0.60 adds +0.10 boost.
    """
    if total_actions >= 100:
        conf = 0.95
    elif total_actions >= 50:
        conf = 0.85 + (total_actions - 50) / 50.0 * 0.10
    else:
        conf = 0.70 + (total_actions - 20) / 30.0 * 0.15
    if ignore_score >= 0.60:
        conf = min(0.95, conf + 0.10)
    return min(0.95, conf)


def _confidence_counter(ratio: float) -> float:
    """COUNTER confidence: linear scale from 0.70 at threshold to 0.90 at 1.0.

    confidence = 0.70 + (ratio - 0.80) * 2.0, clamped to [0.70, 0.90].
    At ratio 0.80: 0.70. At ratio 0.90: 0.90. At ratio 1.0: 0.90 (clamped).
    """
    return max(0.70, min(0.90, 0.70 + (ratio - _COUNTER_RATIO_THRESHOLD) * 2.0))


def classify_role(
    region: Any,
    grid_area: int,
    hud_class_ids: Set[int],
    type_map: Optional[Dict[int, str]] = None,
    region_is_hud: bool = False,
    lc_class_id: Optional[int] = None,
    hud_mask_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    cell_evidence: Optional[CellEvidence] = None,
    ego_body_cells: Optional[FrozenSet[Tuple[int, int]]] = None,
    region_current_role: "LibraryRole" = None,
    lever_confidence: float = 0.0,
    is_active: bool = False,
    active_frame_count: int = 0,
    total_actions: int = 0,
    ignore_score: float = 0.0,
    cell_count_history: Sequence[int] = (),  # WO-E09-v2 D2: march recognizer input
) -> Tuple["LibraryRole", float]:
    """Classify the semantic role of one Region → (LibraryRole, confidence).

    Priority chain:
      Demotion  If lever_confidence > 0, skip reclassification (preserve role)
      Pre       CellEvidence.any_toggle + not HUD                → REACTIVE (WO-RM-01: world delta change)
      A         Action independence >= 0.80 + not EGO            → COUNTER (WO-C5-02)
      Pre-B     is_active=True + active_frame_count >= 2 + not EGO/COUNTER → REACTIVE (WO-RM-04)
      0         LC class + HUD pixel overlap           → COUNTER (V3.5 compat)
      1         AGENT/EGO label + not HUD              → EGO
      2         CONTROL/CONDITIONAL labels             → LEVER (causal direction in type_map)
      3         EFFECT/REACTIVE labels                 → TARGET
      4         HUD zone                               → SIGNAL
      5-9       STATIC/INERT labels + coverage         → STATIC
      10        Fallthrough                            → UNKNOWN
    """
    # Demotion guard (WO-02): if lever_confidence > 0, skip reclassification.
    # Prevents the FRICTION-007 pattern where upstream classifiers (ignore_score)
    # lock out evidence-based classification. Once Tier 3 probing identifies a lever,
    # preserve that evidence-based role across frames.
    if lever_confidence > 0.0 and region_current_role is not None:
        # Return current role with lever_confidence as the backing confidence
        return region_current_role, lever_confidence

    class_id = region.value
    label = (type_map or {}).get(class_id, "")
    coverage = region.area / max(grid_area, 1)
    region_cells: FrozenSet = getattr(region, "cells", frozenset())

    # CellHistory pre-checks (Law 6: CellHistory evidence takes priority)
    cell_active = cell_evidence is not None and cell_evidence.change_count > 0
    cell_toggle = cell_evidence is not None and cell_evidence.any_toggle

    # Toggle → REACTIVE before any type_map rule (WO-RM-01: world-delta change = REACTIVE,
    # not LEVER; LEVER requires causal direction evidence from Tier 4)
    if cell_toggle and not region_is_hud:
        return LibraryRole.REACTIVE, _confidence_lever(cell_evidence)

    # Rule A-march (WO-E09-v2 D2): monotonic-regular cell-count march → COUNTER.
    # Additive sibling to Rule A (whichever fires first wins); Rule A is byte-
    # unchanged below. Coverage/EGO fence is inherited: the substrate maintains
    # cell_count_history ONLY for coverage-bounded non-EGO candidates, so a
    # non-candidate's history is empty and is_counter_march returns False. The
    # explicit coverage / not-HUD / not-EGO guards below are defense-in-depth,
    # mirroring Rule A. Crosses in single-digit syncs where the ratio crawls.
    if (
        is_counter_march(cell_count_history, _COUNTER_MARCH_WINDOW)
        and coverage < _COUNTER_MAX_COVERAGE
        and not region_is_hud
        and region_current_role != LibraryRole.EGO
    ):
        return LibraryRole.COUNTER, _COUNTER_MARCH_CONFIDENCE

    # Rule A: Action Independence Metric → COUNTER (WO-C5-02)
    # Fires BEFORE Pre-B (REACTIVE) because the life counter is is_active=True on every
    # frame (it ticks with every action) and would otherwise be preempted by Pre-B before
    # accumulating the 5 observations needed for Rule A to fire.  Requires:
    #   - Sufficient observation depth (actions_observed >= 5)
    #   - High action_independence_ratio (>= 0.80: changed on 80%+ of all actions)
    #   - Not a HUD-zone object (already handled by toggle pre-check or HUD rule)
    #   - Not already classified EGO (region_current_role guard)
    #   - Object is small relative to grid (< 25% coverage) — prevents misclassifying
    #     large animated backgrounds that flicker on every step
    if (
        cell_evidence is not None
        and cell_evidence.actions_observed >= _COUNTER_MIN_OBSERVATIONS
        and cell_evidence.action_independence_ratio >= _COUNTER_RATIO_THRESHOLD
        and coverage < _COUNTER_MAX_COVERAGE
        and not region_is_hud
        and region_current_role != LibraryRole.EGO   # EGO objects never reclassified COUNTER
    ):
        return LibraryRole.COUNTER, _confidence_counter(cell_evidence.action_independence_ratio)

    # Rule Pre-A: V3.5 foundational principle — any cell-level change → REACTIVE
    # (WO-CLEAN-10-PHASE-1). Per V3.5 chamber consultation (April 26 2026):
    # change_count > 0 is sufficient evidence for REACTIVE. The cell_active variable
    # was extracted at L261 but never wired positively to role assignment; this rule
    # restores the V3.5 principle to V4's architecture. EGO/COUNTER exclusions
    # mirror Pre-B (higher-priority classifications). Runs AFTER Rule A so life
    # counter candidates are correctly classified COUNTER before Pre-A can preempt
    # them (same precedent as Pre-B). Pre-B preserved below as confidence-boost
    # path for sustained activity (active_frame_count >= 2).
    if (
        cell_active
        and not region_is_hud
        and region_current_role not in (LibraryRole.EGO, LibraryRole.COUNTER)
    ):
        return LibraryRole.REACTIVE, _confidence_reactive_change(cell_evidence)

    # Rule Pre-B: world-delta activity → REACTIVE (WO-RM-04).
    # Fires when the object appeared in the world delta on >= 2 separate frames.
    # Threshold = 2 prevents single-frame noise from producing false REACTIVE.
    # EGO and COUNTER exemptions mirror the _classify_objects caller guards
    # (defense-in-depth for callers that invoke classify_role directly).
    # Runs AFTER Rule A so life counter candidates are correctly classified COUNTER
    # before Pre-B can preempt them (WO-RM-04-FIX).
    if (
        is_active
        and active_frame_count >= 2
        and not region_is_hud
        and region_current_role not in (LibraryRole.EGO, LibraryRole.COUNTER)
    ):
        return LibraryRole.REACTIVE, _confidence_reactive_active(active_frame_count)

    # Rule 0: geometric life counter — HUD-pixel-overlapping instance
    if lc_class_id is not None and int(class_id) == lc_class_id:
        if region_cells and hud_mask_cells and (region_cells & hud_mask_cells):
            return LibraryRole.COUNTER, 0.90

    # Rule 1: EGO label — spatial check primary, class fallback
    if label in _AGENT_LABELS and not region_is_hud:
        if ego_body_cells and region_cells:
            if region_cells & ego_body_cells:
                return LibraryRole.EGO, _confidence_ego(cell_evidence)
        else:
            return LibraryRole.EGO, _confidence_ego(cell_evidence)

    # Rule 2: LEVER label
    if label in _CONTROL_LABELS:
        return LibraryRole.LEVER, _confidence_lever(cell_evidence)

    # Rule 3: TARGET label
    if label in _EFFECT_LABELS:
        return LibraryRole.TARGET, _confidence_target(cell_evidence)

    # Rule 4: HUD zone → SIGNAL
    if region_is_hud:
        return LibraryRole.SIGNAL, 0.40

    # Rules 5-9: STATIC — skipped when CellEvidence confirms activity (Law 6)
    if not cell_active:
        # Observation-count STATIC confirmation (WO-RM-04): object never appeared in
        # world delta across >= 20 frames of observation. Converges with ignore_score
        # boost when structural background evidence is also present.
        if not is_active and total_actions >= 20:
            return LibraryRole.STATIC, _confidence_static_observed(total_actions, ignore_score)

        if label == "CONFIRMED_INERT":
            return LibraryRole.STATIC, _confidence_static(cell_evidence)

        if coverage > _INERT_DOMINANT_THRESHOLD:
            return LibraryRole.STATIC, _confidence_static(cell_evidence)

        if label in (_STATIC_LABELS | _INERT_LABELS):
            return LibraryRole.STATIC, _confidence_static(cell_evidence)

    # Rule 10: fallthrough
    return LibraryRole.UNKNOWN, 0.20


# ---------------------------------------------------------------------------
# classify_state_role  (string-returning intermediate helper)
# ---------------------------------------------------------------------------

_SR_ACTIVE_LABELS: frozenset = frozenset({
    "CONDITIONAL_LOCAL", "CONDITIONAL", "CONDITIONAL_GLOBAL", "RECEPTIVE",
})
_SR_REACTIVE_LABELS: frozenset = frozenset({
    "REACTIVE", "UNKNOWN_REACTIVE", "DISPLACEMENT",
})
_SR_INERT_LABELS: frozenset = frozenset({"CONFIRMED_INERT", "SATURATED"})
_SR_STATIC_LABELS: frozenset = frozenset({"STATIC", "INERT_PROVISIONAL"})


def classify_state_role(
    class_id: int,
    ego_classes: Set[int],
    type_map_label: str,
    lever_census: Set[int],
    region_is_hud: bool,
    hud_class_ids: Set[int],
    reactive_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    region_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    contact_footprint_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    lc_class_id: Optional[int] = None,
    hud_mask_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    cell_evidence: Optional[CellEvidence] = None,
    lever_control_cells: FrozenSet[Tuple[int, int]] = frozenset(),
    ego_body_cells: Optional[FrozenSet[Tuple[int, int]]] = None,
    conditional_local_cells: Optional[FrozenSet[Tuple[int, int]]] = None,
) -> str:
    """Classify state-machine participation role → ACTIVE|REACTIVE|INERT|LIFE_COUNTER|UNKNOWN."""
    if lc_class_id is not None and class_id == lc_class_id:
        if region_cells and hud_mask_cells and (region_cells & hud_mask_cells):
            return "LIFE_COUNTER"
    if ego_body_cells and region_cells and (region_cells & ego_body_cells) and not region_is_hud:
        return "ACTIVE"
    if not ego_body_cells and class_id in ego_classes and not region_is_hud:
        return "ACTIVE"
    if type_map_label in _SR_ACTIVE_LABELS:
        if type_map_label == "CONDITIONAL_LOCAL" and conditional_local_cells is not None:
            if region_cells and (region_cells & conditional_local_cells):
                return "ACTIVE"
        else:
            return "ACTIVE"
    if lever_control_cells and region_cells and (region_cells & lever_control_cells):
        return "ACTIVE"
    if lever_census and class_id in lever_census and not lever_control_cells:
        return "ACTIVE"
    if contact_footprint_cells and region_cells and (region_cells & contact_footprint_cells):
        return "ACTIVE"
    if type_map_label in _SR_REACTIVE_LABELS:
        return "REACTIVE"
    if reactive_cells and region_cells and (region_cells & reactive_cells):
        return "REACTIVE"
    if type_map_label in _SR_INERT_LABELS:
        return "INERT"
    if region_is_hud:
        return "INERT"
    if type_map_label in _SR_STATIC_LABELS:
        return "INERT"
    return "UNKNOWN"


def classify_layer(state_role: str) -> str:
    """Derive FOREGROUND / BACKGROUND layer from state_role."""
    if state_role in ("INERT", "LIFE_COUNTER"):
        return "BACKGROUND"
    return "FOREGROUND"


__all__ = [
    "CellEvidence",
    "classify_role",
    "classify_state_role",
    "classify_layer",
    "extract_hud_class_ids",
]

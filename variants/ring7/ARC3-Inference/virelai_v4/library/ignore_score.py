"""
virelai_v4/library/ignore_score.py — Background Recognition / Ignore Score (WO-C5-05).

Extracted from library_sync.py in WO-C5-06 (Red tier decomposition binding).

Computes per-object ignore scores from three evidence channels and applies the
BACKGROUND tag when the composite score crosses a threshold.

Channel 1 (universal):  zero world delta — object never changed across N actions.
Channel 3 (universal):  visual dominance — most frequent class in spawn frame.
Channel 4 (NAV only):   displacement residual — class revealed under ego movement.

WO_IGNORE_SCORE_SIZE_STRIP (2026-07-10): the former Channel 2 (size/coverage —
"large objects are likely background") is REMOVED. Background is earned by
BEHAVIOR (never-changed) and identity (dominant/residual class), never by extent.
Size-demotion was the no-null-class breach flagged by the Phase-0 sweep. Channel
numbers 1/3/4 are kept stable; the composite is now their sum, threshold unchanged.

Threshold: ignore_score >= IGNORE_THRESHOLD (0.60) → is_background = True.
Defeasibility: handled in delta_updater._update_from_delta (unexpected change clears tag).
EGO and COUNTER objects are exempt — their scores are held at 0.0.

Import sovereignty: imports from library/ types only. No imports from
targeting/, strategy/, perception/, or memory/.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import SemanticLibrary

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Calibration constants
# ---------------------------------------------------------------------------

IGNORE_THRESHOLD: float = 0.60
"""Composite score at which an object is tagged BACKGROUND."""

# Channel 1 — zero world delta contributions (by observation count tier)
CHAN1_5OBS:  float = 0.20
CHAN1_20OBS: float = 0.35
CHAN1_50OBS: float = 0.45

# Channel 2 (size / coverage) REMOVED — WO_IGNORE_SCORE_SIZE_STRIP.
# Background is earned by behavior + identity, never by extent.

# Channel 3 — visual dominance contributions
CHAN3_DOMINANT: float = 0.20
CHAN3_SECOND:   float = 0.10

# Channel 4 — displacement residual contributions
CHAN4_DOMINANT:   float = 0.20
CHAN4_SECONDARY:  float = 0.10

# STATIC confidence boost formula: min(MAX_CONF, BASE_CONF + score * SCALE)
STATIC_CONF_BASE:  float = 0.70
STATIC_CONF_SCALE: float = 0.30
STATIC_CONF_MAX:   float = 0.95


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def compute_ignore_scores(
    library: SemanticLibrary,
    grid_shape: Tuple[int, int],
    spawn_class_frequencies: Optional[Dict[int, int]],
    background_class_votes: Optional[Dict[int, int]],
) -> None:
    """Compute per-object ignore scores from four independent evidence channels.

    Mutates library objects in place — updates ignore_score, ignore_channels,
    is_background, and (on threshold crossing) role and confidence.

    Channel 1 (universal):  zero world delta — never changed across N actions.
    Channel 3 (universal):  visual dominance — most frequent class in spawn frame.
    Channel 4 (NAV only):   displacement residual — class revealed under moving ego.
    (Former Channel 2, size/coverage, removed — background is not earned by extent.)

    Threshold: ignore_score >= IGNORE_THRESHOLD → is_background = True.
    Defeasibility: unexpected world change clears is_background (in delta_updater._update_from_delta).
    EGO and COUNTER objects are exempt — their scores are held at 0.0.

    WO-01b: EGO anchoring — objects with ego evidence (class_id in ego_value_set)
    are protected from UNKNOWN→STATIC promotion even if they meet background criteria.
    This prevents ego detection from being blocked by premature background tagging.
    """
    rows, cols = grid_shape
    grid_area = rows * cols
    if grid_area == 0:
        return

    # Channel 3 prep: dominant and second-most-frequent class at spawn
    dominant_class: Optional[int] = None
    second_class: Optional[int] = None
    if spawn_class_frequencies:
        sorted_cls = sorted(spawn_class_frequencies.items(), key=lambda x: x[1], reverse=True)
        if sorted_cls:
            dominant_class = sorted_cls[0][0]
        if len(sorted_cls) > 1:
            second_class = sorted_cls[1][0]

    # Channel 4 prep: most-voted background class from displacement residuals
    residual_dominant: Optional[int] = None
    residual_secondary: Set[int] = set()
    if background_class_votes:
        sorted_votes = sorted(background_class_votes.items(), key=lambda x: x[1], reverse=True)
        if sorted_votes:
            residual_dominant = sorted_votes[0][0]
        residual_secondary = {c for c, _ in sorted_votes[1:]}

    for obj in library.objects.values():
        # EGO and COUNTER are exempt — never tagged background
        if obj.role in (LibraryRole.EGO, LibraryRole.COUNTER):
            obj.ignore_score = 0.0
            continue

        score = 0.0
        channels: List[str] = []

        # Channel 1: zero world delta
        if obj.actions_observed >= 50 and obj.actions_with_change == 0:
            score += CHAN1_50OBS
            channels.append("zero_change")
        elif obj.actions_observed >= 20 and obj.actions_with_change == 0:
            score += CHAN1_20OBS
            channels.append("zero_change")
        elif obj.actions_observed >= 5 and obj.actions_with_change == 0:
            score += CHAN1_5OBS
            channels.append("zero_change")

        # Channel 2 (size / coverage) REMOVED — size no longer influences the
        # background tag. A region earns "quiet" by behavior, never by extent.

        # Channel 3: visual dominance at spawn
        if dominant_class is not None and obj.class_id == dominant_class:
            score += CHAN3_DOMINANT
            channels.append("dominant")
        elif second_class is not None and obj.class_id == second_class:
            score += CHAN3_SECOND
            channels.append("dominant2")

        # Channel 4: displacement residual (NAV worlds only)
        if residual_dominant is not None and obj.class_id == residual_dominant:
            score += CHAN4_DOMINANT
            channels.append("residual")
        elif residual_secondary and obj.class_id in residual_secondary:
            score += CHAN4_SECONDARY
            channels.append("residual2")

        obj.ignore_score = round(score, 3)
        obj.ignore_channels = "+".join(channels)

        # Threshold: tag as BACKGROUND
        if obj.ignore_score >= IGNORE_THRESHOLD:
            if not obj.is_background:
                obj.is_background = True
                logger.info(
                    "[IGNORE] BACKGROUND tag set on region %d (class %d, "
                    "score %.2f, channels: %s)",
                    obj.region_id, obj.class_id, obj.ignore_score, obj.ignore_channels,
                )
            # WO-01b: STATIC promotion through ignore_score was blocking ego assignment.
            # Only promote objects that are already STATIC (confidence boost).
            # UNKNOWN objects should stay UNKNOWN and be promoted through the classification
            # system (classify_role), which respects the full role transition graph and
            # allows UNKNOWN→EGO if ego evidence emerges.
            if obj.role == LibraryRole.STATIC:
                obj.confidence = min(
                    STATIC_CONF_MAX,
                    STATIC_CONF_BASE + obj.ignore_score * STATIC_CONF_SCALE,
                )


# ----------------------------------------------------------------------
# Channel 4 — Background class votes accumulator (mutation in place)
# ----------------------------------------------------------------------

def accumulate_background_class_votes(
    background_class_votes: Dict[int, int],
    prev_grid: np.ndarray,
    curr_grid: np.ndarray,
    agent_values: Set[int],
) -> None:
    """Accumulate Channel 4 displacement-residual votes into background_class_votes.

    For each cell where the previous frame held an agent_value (ego) and the current
    frame holds a non-agent value, increment the background_class_votes counter for
    the new value. This is the producer half of the Channel 4 attribution pipeline;
    compute_ignore_scores in this same module is the consumer.

    MUTATION CONTRACT:
        Mutates background_class_votes IN PLACE. Returns None.
        Inputs prev_grid, curr_grid, agent_values are not mutated.

    Args:
        background_class_votes: Dict[int, int] — class value -> vote count, mutated in place.
        prev_grid: numpy 2D array of the previous frame's grid.
        curr_grid: numpy 2D array of the current frame's grid.
        agent_values: Set[int] — class values currently held by ego.

    Returns:
        None. background_class_votes is mutated in place.

    Extracted from sync_library's body (L314-L333 post-Phase-1) in WO-CLEAN-12-PHASE-2
    as part of the Hard cap decomposition campaign per Apex Q4 ruling
    (Stop B Green-tier-V3.5-match target).

    Transform pipeline applied per FRICTION-WO-12 + FRICTION-WO-13: gate-strip + re-indent
    (strip-4 per post-gate-strip min depth = 8) + rename (grid -> curr_grid).
    """
    for r in range(curr_grid.shape[0]):
        for c in range(curr_grid.shape[1]):
            prev_val = int(prev_grid[r, c])
            curr_val = int(curr_grid[r, c])
            if prev_val in agent_values and curr_val not in agent_values:
                background_class_votes[curr_val] = (
                    background_class_votes.get(curr_val, 0) + 1
                )

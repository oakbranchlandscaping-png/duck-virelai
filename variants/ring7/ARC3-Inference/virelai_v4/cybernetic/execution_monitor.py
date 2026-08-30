"""
cybernetic/execution_monitor.py — WO-CYBERNETIC-01

Pure function: given pre/post grids and an optional predicted effect,
compute an ActionMatchResult describing how well the prediction held.

Imports: numpy, dataclasses, typing, falsification.prediction_comparator.
No imports from execution/, discovery/, observer/, spine/, crucible/.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from virelai_v4.falsification.prediction_comparator import compare_prediction


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PredictedEffect:
    """Compact prediction payload handed to the monitor."""
    effect_region: frozenset   # frozenset of (r, c) tuples expected to change
    delta_pixels: int          # expected pixel-change count


@dataclass(frozen=True)
class ActionMatchResult:
    """Single-action monitoring result."""
    lever_id: str
    observed_delta_px: int
    predicted_delta_px: Optional[int]   # None when no prediction
    match_ratio: Optional[float]        # None when no prediction
    spurious_px: int
    step_number: int
    magnitude_ratio: Optional[float] = None   # observed / predicted (None = no prediction)
    verdict: Optional[str] = None              # CONFIRMED / REFINED / CONTRADICTED / None


# ── Verdict Helpers ───────────────────────────────────────────────────────────

def _compute_click_verdict(
    match_ratio: Optional[float],
    magnitude_ratio: Optional[float],
    observed_delta_px: int,
    predicted_delta_px: Optional[int],
) -> Optional[str]:
    """Derive three-tier verdict for CLICK actions."""
    if match_ratio is None or magnitude_ratio is None:
        return None
    if observed_delta_px == 0 and predicted_delta_px is not None and predicted_delta_px > 0:
        return "CONTRADICTED"
    if magnitude_ratio < 0.5 or magnitude_ratio > 2.0:
        return "CONTRADICTED"
    if match_ratio >= 0.7 and 0.8 <= magnitude_ratio <= 1.2:
        return "CONFIRMED"
    if 0.5 <= magnitude_ratio <= 1.5 and observed_delta_px > 0:
        return "REFINED"
    return "CONTRADICTED"


def _compute_nav_verdict(match_ratio: float) -> str:
    """Derive verdict for NAV actions (displacement-based)."""
    if match_ratio >= 0.7:
        return "CONFIRMED"
    if match_ratio == 0.0:
        return "CONTRADICTED"
    return "REFINED"


# ── Pure Function ─────────────────────────────────────────────────────────────

def record_action(
    lever_id: str,
    pre_grid: np.ndarray,
    post_grid: np.ndarray,
    predicted_effect: Optional[PredictedEffect],
    step_number: int,
) -> ActionMatchResult:
    """Record one action's outcome by comparing grids and prediction.

    Args:
        lever_id:         string identifier for the lever acted on.
        pre_grid:         grid snapshot before the action (int32).
        post_grid:        grid snapshot after the action (int32).
        predicted_effect: optional prediction; None means unpredicted action.
        step_number:      monotone step counter within this execution run.

    Returns:
        Frozen ActionMatchResult with observed vs predicted metrics.
    """
    observed_delta_px = int(np.count_nonzero(pre_grid != post_grid))

    if predicted_effect is None:
        return ActionMatchResult(
            lever_id=lever_id,
            observed_delta_px=observed_delta_px,
            predicted_delta_px=None,
            match_ratio=None,
            spurious_px=0,
            step_number=step_number,
        )

    # Convert frozenset → tuple for compare_prediction's signature.
    region_tuple = tuple(sorted(predicted_effect.effect_region))
    cmp = compare_prediction(
        predicted_effect_region=region_tuple,
        pre_grid=pre_grid,
        post_grid=post_grid,
    )

    pred_px = predicted_effect.delta_pixels
    mag = (observed_delta_px / pred_px) if pred_px and pred_px > 0 else None
    verdict = _compute_click_verdict(cmp.match_ratio, mag, observed_delta_px, pred_px)

    return ActionMatchResult(
        lever_id=lever_id,
        observed_delta_px=observed_delta_px,
        predicted_delta_px=pred_px,
        match_ratio=cmp.match_ratio,
        spurious_px=cmp.spurious_px,
        step_number=step_number,
        magnitude_ratio=mag,
        verdict=verdict,
    )


# ── NAV World Match ──────────────────────────────────────────────────────────

def compute_nav_match(
    action_id: int,
    ego_before: Tuple[int, int],
    ego_after: Tuple[int, int],
    expected_displacement: Tuple[int, int],
    observed_delta_px: int,
    expected_delta_px: int,
    step_number: int,
) -> ActionMatchResult:
    """Compute an ActionMatchResult for one NAV step.

    NAV prediction is ego displacement, not lever effect regions.

    Match ratio:
      1.0 — ego moved exactly as predicted (or NOOP and stayed put)
      0.5 — ego moved but not by the expected displacement
      0.0 — ego didn't move when it should have, or moved on a NOOP

    Args:
        action_id:             integer action that was taken.
        ego_before:            (row, col) ego position before step.
        ego_after:             (row, col) ego position after step.
        expected_displacement: (dr, dc) from step_vectors[action_id].
        observed_delta_px:     HUD-excluded pixel change count.
        expected_delta_px:     replacement_mask_size (expected move delta).
        step_number:           monotone step counter.
    """
    actual_dr = ego_after[0] - ego_before[0]
    actual_dc = ego_after[1] - ego_before[1]
    exp_dr, exp_dc = expected_displacement

    is_noop = (exp_dr == 0 and exp_dc == 0)
    actually_moved = (actual_dr != 0 or actual_dc != 0)

    if is_noop:
        match_ratio = 1.0 if not actually_moved else 0.0
    elif not actually_moved:
        match_ratio = 0.0
    elif actual_dr == exp_dr and actual_dc == exp_dc:
        match_ratio = 1.0
    else:
        match_ratio = 0.5

    spurious_px = abs(observed_delta_px - expected_delta_px)
    mag = (observed_delta_px / expected_delta_px) if expected_delta_px > 0 else None
    verdict = _compute_nav_verdict(match_ratio)

    return ActionMatchResult(
        lever_id=f"nav_action_{action_id}",
        observed_delta_px=observed_delta_px,
        predicted_delta_px=expected_delta_px,
        match_ratio=match_ratio,
        spurious_px=spurious_px,
        step_number=step_number,
        magnitude_ratio=mag,
        verdict=verdict,
    )

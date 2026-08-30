"""
falsification/prediction_comparator.py — WO-FALSIFICATION-08

Pure function: takes a predicted effect region (from LeverArtifact) and
an observed delta (pre/post grids from probe_executor), returns a
structured CausalVerdict.

Five outcomes:
  CONFIRMED  — match_ratio >= 0.7, predicted region matches observed delta
  PARTIAL    — match_ratio 0.3–0.7, some overlap but mapping imprecise
  FALSIFIED  — match_ratio < 0.3 (or zero delta with no prior reactivity)
  SATURATED  — zero delta at a lever that was previously reactive (state-full)
  NO_PREDICTION — empty predicted effect region (nothing to compare)

Phase Sovereignty: imports numpy only.  No imports from discovery/,
crucible/, execution/, or observer/.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


# ── Thresholds ──
_CONFIRMED_THRESHOLD = 0.70
_PARTIAL_THRESHOLD = 0.30


@dataclass(frozen=True)
class CausalVerdict:
    """Result of comparing predicted effect region against observed delta."""
    outcome: str                # CONFIRMED, SATURATED, PARTIAL, FALSIFIED, NO_PREDICTION
    match_ratio: float          # |predicted ∩ observed| / |predicted|, 0.0–1.0
    magnitude_ratio: float      # observed_delta_px / predicted_effect_count
    spurious_px: int            # pixels changed OUTSIDE predicted region
    predicted_px: int           # |predicted effect region|
    observed_px: int            # |observed delta|
    overlap_px: int             # |predicted ∩ observed|


def compare_prediction(
    predicted_effect_region: Tuple[Tuple[int, int], ...],
    pre_grid: np.ndarray,
    post_grid: np.ndarray,
    hud_mask: Optional[np.ndarray] = None,
    prior_reactive: bool = False,
) -> CausalVerdict:
    """Compare a lever's predicted effect region against observed delta.

    Args:
        predicted_effect_region: (row, col) tuples from LeverArtifact.effect_region.
        pre_grid:  grid immediately before the click (np.ndarray int32).
        post_grid: grid immediately after the click (np.ndarray int32).
        hud_mask:  optional boolean mask — True where life counter lives.
                   Those pixels are excluded from observed delta.
        prior_reactive: has this lever EVER produced delta > 0 in a previous test?

    Returns:
        CausalVerdict with outcome classification and metrics.
    """
    predicted_coords = set(predicted_effect_region)
    predicted_px = len(predicted_coords)

    if predicted_px == 0:
        return CausalVerdict(
            outcome="NO_PREDICTION", match_ratio=0.0, magnitude_ratio=0.0,
            spurious_px=0, predicted_px=0, observed_px=0, overlap_px=0,
        )

    # Compute observed delta with HUD masking
    raw_delta = (pre_grid != post_grid)
    if hud_mask is not None:
        raw_delta = raw_delta & ~np.asarray(hud_mask, dtype=bool)
    observed_coords = set(zip(*np.where(raw_delta)))
    observed_px = len(observed_coords)

    # Overlap and spurious
    overlap = predicted_coords & observed_coords
    overlap_px = len(overlap)
    spurious_px = len(observed_coords - predicted_coords)

    match_ratio = overlap_px / predicted_px
    magnitude_ratio = observed_px / predicted_px

    # Classify outcome
    if observed_px == 0:
        if prior_reactive:
            outcome = "SATURATED"
        else:
            outcome = "FALSIFIED"
    elif match_ratio >= _CONFIRMED_THRESHOLD:
        outcome = "CONFIRMED"
    elif match_ratio >= _PARTIAL_THRESHOLD:
        outcome = "PARTIAL"
    else:
        outcome = "FALSIFIED"

    return CausalVerdict(
        outcome=outcome,
        match_ratio=match_ratio,
        magnitude_ratio=magnitude_ratio,
        spurious_px=spurious_px,
        predicted_px=predicted_px,
        observed_px=observed_px,
        overlap_px=overlap_px,
    )

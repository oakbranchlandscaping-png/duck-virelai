"""
virelai_v4/perception/live_region_mask.py — the SHARED live-region mask.

WO-CP1-FIX-A. Single definition of "mask the live regions out of a grid before
hashing it for novelty/termination." The live counter ticks every action; any
state signature computed over raw pixels reads every frame as novel (the
WO-DIAG-CP1 instrument lie) and defeats per-press saturation detection (the
cycle-probe budget burn). Consumers hash `mask_live_regions(grid, ...)` instead
of the raw grid.

FOUNDATIONAL, not display-local: this is the one mask definition. The future
§5.3 abstracted-belief novelty tracker / deepening gradient (Stage 3/4) must
consume this same util, or counter-poisoning reappears in the behavioral path.
WO-CP1-FIX-B's cycle-probe termination hash consumes it.

Scope note: this masks live regions for HASH INTEGRITY. It does not build the
§5.3 abstracted-state tracker — signatures remain (masked) pixels, not belief.

Inputs are EXPLICIT — no invented coordinates. Sources today:
  - hud_mask:   context.hud_mask (built when COUNTER is first detected;
                None until then — virelai.py "WO-C5-03").
  - lc_region:  action_reality_report.life_counter_region (r0, r1, c0, c1) —
                may be None (the arr chain is hollow; WO-TIER-A carry-forward).
  - extra_cells: any further live cells the caller knows (e.g. the library's
                COUNTER-classified slots' cells — the robust source when the
                arr is hollow).

Pure; stdlib + numpy only; no state.
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import numpy as np


def mask_live_regions(
    grid: np.ndarray,
    hud_mask: Optional[np.ndarray] = None,
    lc_region: Optional[Tuple[int, int, int, int]] = None,
    extra_cells: Optional[Iterable[Tuple[int, int]]] = None,
) -> np.ndarray:
    """Return a copy of `grid` with all known live regions zeroed.

    Zeroes, in order: the lc_region rectangle (r0..r1, c0..c1 inclusive — the
    V3.5 `_mask_lc` convention), every True cell of hud_mask, and every
    (row, col) in extra_cells. Unknown/None inputs are skipped — masking is
    best-effort over what the caller knows.
    """
    out = np.asarray(grid, dtype=np.int32).copy()
    if lc_region is not None:
        r0, r1, c0, c1 = lc_region
        out[r0:r1 + 1, c0:c1 + 1] = 0
    if hud_mask is not None:
        out[np.asarray(hud_mask, dtype=bool)] = 0
    if extra_cells:
        h, w = out.shape[:2]
        for (r, c) in extra_cells:
            if 0 <= r < h and 0 <= c < w:
                out[r, c] = 0
    return out


__all__ = ["mask_live_regions"]

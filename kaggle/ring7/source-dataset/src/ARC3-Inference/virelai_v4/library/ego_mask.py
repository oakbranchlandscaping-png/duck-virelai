"""
ego_mask.py — Ego mask computation for DELTA-SPLIT.

Computes a boolean numpy array marking the cells the ego currently
occupies (arrival) and just vacated (departure). Used by
_compute_world_delta to filter ego traversal noise from the world delta.
"""
from __future__ import annotations

import numpy as np
from typing import Optional, Tuple


def compute_ego_mask(
    ego_body_cells: frozenset,
    current_pos: Optional[Tuple[int, int]],
    prev_pos: Optional[Tuple[int, int]],
    grid_shape: Tuple[int, int],
) -> np.ndarray:
    """
    Build a boolean mask of ego arrival + departure cells for one frame.

    Args:
        ego_body_cells: Class-pure frozenset of (row, col) spawn-frame
                        ego coordinates (set at spawn, never updated).
        current_pos:    Current ego centroid (row, col). None on first frame.
        prev_pos:       Previous ego centroid (row, col). None before first move.
        grid_shape:     (rows, cols) of the game grid.

    Returns:
        Boolean numpy array of grid_shape. True where ego arrived or departed.
    """
    mask = np.zeros(grid_shape, dtype=bool)

    if not ego_body_cells or current_pos is None:
        return mask

    # Compute spawn centroid — reference point body was defined at
    rows_s = [r for r, _ in ego_body_cells]
    cols_s = [c for _, c in ego_body_cells]
    spawn_r = int(round(sum(rows_s) / len(rows_s)))
    spawn_c = int(round(sum(cols_s) / len(cols_s)))

    def _translate_and_clamp(target_pos: Tuple[int, int]) -> list:
        dr = target_pos[0] - spawn_r
        dc = target_pos[1] - spawn_c
        result = []
        for r, c in ego_body_cells:
            tr = max(0, min(grid_shape[0] - 1, r + dr))
            tc = max(0, min(grid_shape[1] - 1, c + dc))
            result.append((tr, tc))
        return result

    # Arrival cells — where ego is now
    for r, c in _translate_and_clamp(current_pos):
        mask[r, c] = True

    # Departure cells — where ego was last frame
    if prev_pos is not None:
        for r, c in _translate_and_clamp(prev_pos):
            mask[r, c] = True

    return mask

"""
virelai_v4/library/region_geometry.py — Region geometry helpers.

Provides coordinate utilities for working with cell sets (frozenset or set
of (row, col) tuples). Used by action_selector.py for probe target selection.

Import sovereignty: stdlib only. No imports from other virelai_v4 packages.
Tier target: file ≤ 100 lines (Green). Function body ≤ 40 lines (Green).

WO-02 LEVER-CATALOG
"""

from __future__ import annotations

from typing import Set, Tuple


def representative_coordinate(
    cells: Set[Tuple[int, int]],
) -> Tuple[int, int]:
    """Return a coordinate guaranteed to be within the cell set.

    Prefers the centroid (rounded); falls back to the cell closest to the
    centroid by Manhattan distance if the centroid is not in the cell set.
    This handles irregular shapes (L-shapes, diagonals, thin strips) where
    the geometric centroid falls in empty space.

    Parameters
    ----------
    cells : Set[Tuple[int, int]]
        Non-empty set of (row, col) coordinate pairs.

    Returns
    -------
    Tuple[int, int]
        A (row, col) coordinate guaranteed to be in cells.

    Raises
    ------
    ValueError
        If cells is empty.
    """
    if not cells:
        raise ValueError("representative_coordinate: cells must be non-empty")

    cell_list = list(cells)

    # Compute centroid
    avg_row = sum(r for r, _ in cell_list) / len(cell_list)
    avg_col = sum(c for _, c in cell_list) / len(cell_list)
    centroid_row = round(avg_row)
    centroid_col = round(avg_col)

    # If centroid is in the cell set, return it directly
    if (centroid_row, centroid_col) in cells:
        return (centroid_row, centroid_col)

    # Otherwise, find the cell with minimum Manhattan distance to the centroid
    nearest = min(
        cell_list,
        key=lambda cell: abs(cell[0] - centroid_row) + abs(cell[1] - centroid_col),
    )
    return nearest

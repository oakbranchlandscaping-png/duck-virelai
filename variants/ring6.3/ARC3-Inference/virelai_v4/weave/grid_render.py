"""WO_CLAIM_DECOMPOSER · B4 — a small, stdlib-only grid renderer.

Renders a 2-D grid to text, one glyph per cell, with an optional masked-cell
overlay. Serves the fork mask-overlay (B2) and the contact sheet (B3). No oracle,
no belief, no scipy — a clean re-write of the cell→glyph concept, NOT an import of
the oracle-tangled ``diagnostics/render_stages`` path.
"""

from __future__ import annotations

from typing import Any, FrozenSet, Tuple

Cell = Tuple[int, int]
_GLYPH = "0123456789abcdefghijklmnopqrstuvwxyz"


def glyph(v: int) -> str:
    """One compact glyph per cell value (0-9 → digits, 10+ → letters)."""
    v = int(v)
    return _GLYPH[v] if 0 <= v < len(_GLYPH) else "?"


def render_grid(grid: Any, mask: "FrozenSet[Cell]" = frozenset()) -> str:
    """The grid as text: one glyph per cell. A masked cell is UPPERCASED (or ``*``
    if its glyph is a digit), so the recorded HUD mask's footprint is visible over
    the actual values."""
    lines = []
    for r, row in enumerate(grid or []):
        out = []
        for c, v in enumerate(row):
            g = glyph(v)
            if (r, c) in mask:
                g = g.upper() if g.isalpha() else "*"
            out.append(g)
        lines.append("".join(out))
    return "\n".join(lines)


def diff_cells(g1: Any, g2: Any) -> "FrozenSet[Cell]":
    """The cells where two grids differ (shape-guarded to the overlap)."""
    diffs = set()
    for r, (row1, row2) in enumerate(zip(g1 or [], g2 or [])):
        for c, (a, b) in enumerate(zip(row1, row2)):
            if int(a) != int(b):
                diffs.add((r, c))
    return frozenset(diffs)


def render_diff_overlay(g1: Any, g2: Any, mask: "FrozenSet[Cell]") -> str:
    """Where g1 and g2 differ, marked against the recorded mask — the fork's
    distinction as fact: ``M`` = differing AND in the mask, ``X`` = differing and
    NOT in the mask, ``.`` = identical. No judgement: it renders the collision
    between two independently-recorded artifacts (the grids' difference, the mask)."""
    diffs = diff_cells(g1, g2)
    lines = []
    for r, row in enumerate(g1 or []):
        out = []
        for c, _ in enumerate(row):
            if (r, c) in diffs:
                out.append("M" if (r, c) in mask else "X")
            else:
                out.append(".")
        lines.append("".join(out))
    return "\n".join(lines)

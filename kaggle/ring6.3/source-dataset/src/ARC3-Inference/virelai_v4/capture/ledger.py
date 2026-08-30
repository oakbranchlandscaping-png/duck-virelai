"""WO_SIGHTING_LEDGER · the fidelity gate — the rung-0 exit.

Proves the *cut* is lossless: a node's visible grid, rebuilt FROM ITS SIGHTINGS
(paint each cell-set by class), must equal the captured visible grid byte-equal,
every node. This is distinct from S1's sealed *record* round-trip (which rebuilds
from stored layers) and from ``FrameRecordLog.reconstruct`` — the gate must
reconstruct from the atoms, or it proves the wrong thing.

Fidelity, not correctness: passing proves the record is faithful (disjoint ∧
covering — the round-trip passing IS the completeness proof), not that the
objects are the right objects. Correctness is a later grade the Ledger enables.

Pure and dependency-light: stdlib only. Reads sightings + the capture record's
visible layer; writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple

# Sentinels used by the sightings reconstruction to localize gaps/overlaps.
_UNPAINTED = -1     # covering break: a cell no sighting claimed
_CONFLICT = -2      # disjointness break: a cell two sightings claimed


def reconstruct_from_sightings(
    regions: Iterable[Any], grid_shape: Tuple[int, int]
) -> List[List[int]]:
    """Repaint a node's visible grid from its sightings alone.

    Each ``region`` (duck-typed: ``.class_id`` + ``.cells``) paints its cell-set
    at its class value. A cell no sighting claims stays ``_UNPAINTED`` (covering
    break); a cell two sightings claim becomes ``_CONFLICT`` (disjointness break).
    Independent of any stored layers — proves the cut, not the record.
    """
    h, w = int(grid_shape[0]), int(grid_shape[1])
    grid = [[_UNPAINTED] * w for _ in range(h)]
    for region in regions:
        cls = int(region.class_id)
        for (r, c) in region.cells:
            if 0 <= r < h and 0 <= c < w:
                grid[r][c] = cls if grid[r][c] == _UNPAINTED else _CONFLICT
    return grid


@dataclass(frozen=True)
class PristineVerdict:
    n_nodes: int
    n_pass: int
    # (node_index, first differing cells) or None if all nodes round-trip.
    first_fail: Optional[Tuple[int, List[Tuple[int, int]]]]


def _diff_cells(expected: List[List[int]], got: List[List[int]]) -> List[Tuple[int, int]]:
    """The cells where the sightings reconstruction diverges from the captured
    grid — the completeness/disjointness localizer. Shape mismatch -> []."""
    if len(expected) != len(got):
        return []
    diffs: List[Tuple[int, int]] = []
    for r, (erow, grow) in enumerate(zip(expected, got)):
        if len(erow) != len(grow):
            return diffs or [(r, -1)]
        for c, (ev, gv) in enumerate(zip(erow, grow)):
            if ev != gv:
                diffs.append((r, c))
    return diffs


def grade_pristine(cuts: Iterable[Any], capture: Any) -> PristineVerdict:
    """Per node: ``reconstruct_from_sightings(present(i)) == capture.reconstruct(i)[-1]``
    byte-equal. ``cuts`` carry ``regions`` + ``grid_shape`` + ``node_index``;
    ``capture`` is a ``FrameRecordLog`` (duck-typed ``reconstruct``)."""
    cut_list = sorted(cuts, key=lambda c: c.node_index)
    n_nodes = len(cut_list)
    n_pass = 0
    first_fail: Optional[Tuple[int, List[Tuple[int, int]]]] = None

    for cut in cut_list:
        recon = reconstruct_from_sightings(cut.regions, cut.grid_shape)
        captured = capture.reconstruct(cut.node_index)[-1]   # the VISIBLE layer
        captured = [[int(c) for c in row] for row in captured]
        if recon == captured:
            n_pass += 1
        elif first_fail is None:
            first_fail = (cut.node_index, _diff_cells(captured, recon))

    return PristineVerdict(n_nodes=n_nodes, n_pass=n_pass, first_fail=first_fail)


def format_pristine(v: PristineVerdict) -> str:
    """The verdict block printed at the seal site."""
    if v.first_fail is None and v.n_pass == v.n_nodes:
        return f"SIGHTING-LEDGER PRISTINE: {v.n_nodes} nodes, {v.n_pass} round-trip PASS"
    node, cells = v.first_fail if v.first_fail else (-1, [])
    shown = ", ".join(f"({r},{c})" for r, c in cells[:8])
    more = " …" if len(cells) > 8 else ""
    return (f"SIGHTING-LEDGER PRISTINE: FAIL at node {node} — cells {{{shown}{more}}} "
            f"({v.n_pass}/{v.n_nodes} nodes passed)")

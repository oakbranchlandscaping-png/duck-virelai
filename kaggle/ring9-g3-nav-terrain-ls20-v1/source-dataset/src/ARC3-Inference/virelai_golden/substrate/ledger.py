"""SUBSTRATE · ledger — every node cut into objects, and the two exact checks on every edge.

Ladder step 5 (record) / rung 2 of the ontology. Canon: 01 §3 totality; 02 §5 the partition;
the conservation invariant (00: "net-per-class sums to zero every transition — a check that
can only fail if the recording is wrong"). FIDELITY column only: PRISTINE proves the cut is
lossless, never that the objects are the right objects.

Transcription origin (R-C): virelai_v4/capture/ledger.py @ oracle-v4 (99 lines, read whole) —
`reconstruct_from_sightings`, `grade_pristine`, `PristineVerdict`; capture/ledger_build.py
:140-153 `ledger_from_capture` (the cut loop) and :106-113 `regions_of`; capture/clay.py (456,
read whole) — `RegionClay.fingerprint` = (class, cells) and `collapse_fingerprints` (the
distinct-object count X). What it proved: `SIGHTING-LEDGER PRISTINE: n nodes, n round-trip
PASS` on every canary since WO_SIGHTING_LEDGER; X = 158 (run 1) and 81 (run 2) in the golden
logs of 2026-09-05.

NOT transcribed: `RegionClay` (golden's `scan.Region` already carries class, cells, anchor and
the fingerprint; a second geometry type would be a copy), `NodeCut.node_hash` / `layered_hash`
/ `NodeId` (address hashes whose readers are the v3 node map and a fork-witness — no ladder
consumer, R-E), `node_map` / `Arrival` (edge paths; the recording is action-blind), `bbox`,
`present_list` / `render_master_list` / `render_node_map`.

NEW here (labeled): `conservation` — the per-transition joint signed per-class vector
Δ_c = count_c(after) − count_c(before). Under totality Σ_c Δ_c = 0 exactly whenever the two
grids share a shape; a non-zero sum means the recording changed shape mid-game. The vectors
are kept: they are the joint, press-indexed, signed record later rungs read (00: "scalar delta
records" is a named reflex; this is the alternative).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

import numpy as np

from virelai_golden.substrate.grid import Grid
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell, Region, scan_grid

Fingerprint = Tuple[int, FrozenSet[Cell]]

_UNPAINTED = -1  # covering break: a cell no object claimed
_CONFLICT = -2   # disjointness break: a cell two objects claimed


@dataclass(frozen=True)
class Cut:
    """One node's partition into objects. Geometry and class only; no identity across nodes."""

    node: int
    shape: Tuple[int, int]
    regions: Tuple[Region, ...]

    @property
    def fingerprints(self) -> FrozenSet[Fingerprint]:
        return frozenset(r.fingerprint for r in self.regions)


def cuts(record: Record) -> Tuple[Cut, ...]:
    """Scan every node's settled grid (INTERIM_O8). Whole game, in order."""
    out = []
    for node in record.nodes:
        g = node.settled
        out.append(Cut(node.index, (int(g.shape[0]), int(g.shape[1])), scan_grid(g)))
    return tuple(out)


def reconstruct_from_sightings(regions: Tuple[Region, ...], shape: Tuple[int, int]) -> Grid:
    """Repaint a grid from its objects alone. Proves the cut, not the record."""
    grid = np.full(shape, _UNPAINTED, dtype=np.int16)
    for r in regions:
        for (row, col) in r.cells:
            grid[row, col] = r.value if grid[row, col] == _UNPAINTED else _CONFLICT
    return grid


@dataclass(frozen=True)
class PristineVerdict:
    n_nodes: int
    n_pass: int
    first_fail: Optional[Tuple[int, Tuple[Cell, ...]]]  # (node, first differing cells)

    @property
    def passed(self) -> bool:
        return self.first_fail is None and self.n_pass == self.n_nodes


def grade_pristine(record: Record, node_cuts: Tuple[Cut, ...]) -> PristineVerdict:
    """Every node: repaint from sightings == the settled grid, cell for cell."""
    n_pass = 0
    first_fail = None
    for node, cut in zip(record.nodes, node_cuts):
        settled = node.settled
        recon = reconstruct_from_sightings(cut.regions, cut.shape)
        if recon.shape == settled.shape and bool(np.array_equal(recon, settled)):
            n_pass += 1
        elif first_fail is None:
            if recon.shape != settled.shape:
                first_fail = (node.index, ((-1, -1),))
            else:
                diff = np.argwhere(recon != settled)
                first_fail = (node.index, tuple((int(r), int(c)) for r, c in diff[:8]))
    return PristineVerdict(len(node_cuts), n_pass, first_fail)


@dataclass(frozen=True)
class Transition:
    """The joint signed per-class delta from node `before` to node `after`."""

    before: int
    after: int
    delta: Tuple[Tuple[int, int], ...]  # ((class, Δcount), ...) for every class that moved
    changed_cells: int                   # cells whose class differs; 0 = the board held

    @property
    def closes(self) -> bool:
        return sum(d for _, d in self.delta) == 0


def _counts(grid: Grid) -> Dict[int, int]:
    values, counts = np.unique(grid, return_counts=True)
    return {int(v): int(c) for v, c in zip(values, counts)}


def conservation(record: Record) -> Tuple[Transition, ...]:
    """One Transition per edge, whole game (a life or level boundary is still an edge)."""
    out: List[Transition] = []
    prev = None
    for node in record.nodes:
        g = node.settled
        if prev is not None:
            pg, pi = prev
            a, b = _counts(pg), _counts(g)
            delta = tuple(sorted((c, b.get(c, 0) - a.get(c, 0)) for c in set(a) | set(b)
                                 if b.get(c, 0) != a.get(c, 0)))
            changed = int(np.count_nonzero(pg != g)) if pg.shape == g.shape else -1
            out.append(Transition(pi, node.index, delta, changed))
        prev = (g, node.index)
    return tuple(out)


def distinct_objects(record: Record, node_cuts: Tuple[Cut, ...]) -> Dict[int, int]:
    """Distinct fingerprints per life — v4's X (`collapse_fingerprints` over a life's stream)."""
    seen: Dict[int, set] = {}
    for node, cut in zip(record.nodes, node_cuts):
        seen.setdefault(node.life, set()).update(cut.fingerprints)
    return {life: len(s) for life, s in sorted(seen.items())}

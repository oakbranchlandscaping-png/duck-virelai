"""WEAVE · provenance — who owned each cell, and who gave which cell to whom across an edge.

Canon: 01 §3 totality (every cell has an owner; no background, no NONE owner for an interior
cell); 02 §5 the partition; rung 5 (mechanics) reads only rungs 3–4 (worldlines, verbs).
"Quiet is earned per edge from the cells, never assumed by size, class or position."

Transcription origin (R-C): virelai_v4/weave/provenance.py @ oracle-v4 (177 lines, read whole)
— `worldline_owner_index`, `cell_owners`, `is_total`, `owner_edge`, `complement_verdict`,
`window_owner_edges`. What it proved: the reactive complement on the embodied canary (the floor
earning its quiet as the ego crossed it), and the crossing account `crossing.py` reads. Read
whole at G0-04 and deferred to here under R-E; its golden readers are `roles.counter` (owner edges, the complement), `roles.ground` (the owner maps) and `roles.ego_pointer`; `crossing.py` was retired at G3-01 with the field read (R-M).

Kept verbatim: `cell_owners` RAISES on a cell owned twice — a real invariant on PRISTINE cuts.
An owner-owner EXCHANGE requires both endpoints CONTINUING (present at both nodes); a change
into a born worldline or out of a dying one is a boundary event, not an exchange, and is
INTRINSIC (loud). A complement has `intrinsic == ∅`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Sequence, Tuple

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.scan import Cell, Region
from virelai_golden.weave.worldline import Worldline


@dataclass(frozen=True)
class OwnerEdge:
    """Every cell whose owner changed across (prev → now), plus the worldlines present at both."""

    prev_node: int
    now_node: int
    exchanges: Tuple[Tuple[Cell, int, int], ...]  # (cell, owner@t, owner@t+1)
    continuing: FrozenSet[int]


@dataclass(frozen=True)
class ComplementVerdict:
    worldline_id: int
    is_reactive_complement: bool
    intrinsic_cells: FrozenSet[Cell]   # churn NOT owner-owner accounted (loud)
    exchange_cells: FrozenSet[Cell]    # churn that IS owner-owner exchange
    partners: Dict[int, FrozenSet[Cell]]


def worldline_owner_index(worldlines: Sequence[Worldline]) -> Dict[Tuple[int, Region], int]:
    """(node, region) → worldline id, total over every step of every worldline."""
    return {(node, region): wl.id for wl in worldlines for node, region in wl.steps}


def cell_owners(cut: Cut, owner_index: Dict[Tuple[int, Region], int]) -> Dict[Cell, int]:
    """cell → worldline id at this cut. Raises on a cell owned twice (disjointness)."""
    owners: Dict[Cell, int] = {}
    for region in cut.regions:
        wid = owner_index[(cut.node, region)]
        for cell in region.cells:
            if cell in owners:
                raise AssertionError(f"cell {cell} owned by two regions at node {cut.node}")
            owners[cell] = wid
    return owners


def is_total(owners: Dict[Cell, int], cut: Cut) -> bool:
    """Every grid cell owned — the covering half of the partition."""
    h, w = cut.shape
    return bool(h and w) and len(owners) == h * w


def owner_edge(cut_t: Cut, cut_t1: Cut, worldlines: Sequence[Worldline]) -> OwnerEdge:
    index = worldline_owner_index(worldlines)
    o_t, o_t1 = cell_owners(cut_t, index), cell_owners(cut_t1, index)
    changed = tuple((cell, o_t[cell], o_t1[cell]) for cell in o_t
                    if o_t1.get(cell) is not None and o_t1[cell] != o_t[cell])
    present = {wl.id: frozenset(n for n, _ in wl.steps) for wl in worldlines}
    continuing = frozenset(wid for wid, nodes in present.items()
                           if cut_t.node in nodes and cut_t1.node in nodes)
    return OwnerEdge(cut_t.node, cut_t1.node, changed, continuing)


def complement_verdict(worldline: Worldline, edge: OwnerEdge) -> ComplementVerdict:
    """Is this worldline a reactive complement over `edge`: continuing, churn non-empty, and
    every churned cell an owner-owner exchange (intrinsic == ∅)."""
    wid, cont = worldline.id, edge.continuing
    lost, gained, exchange, intrinsic = set(), set(), set(), set()
    partners: Dict[int, set] = {}
    for cell, giver, receiver in edge.exchanges:
        if giver == wid:
            lost.add(cell)
            if giver in cont and receiver in cont:
                exchange.add(cell)
                partners.setdefault(receiver, set()).add(cell)
            else:
                intrinsic.add(cell)
        elif receiver == wid:
            gained.add(cell)
            if giver in cont and receiver in cont:
                exchange.add(cell)
                partners.setdefault(giver, set()).add(cell)
            else:
                intrinsic.add(cell)
    churn = lost | gained
    return ComplementVerdict(wid, (wid in cont) and bool(churn) and not intrinsic,
                             frozenset(intrinsic), frozenset(exchange),
                             {k: frozenset(v) for k, v in partners.items()})


def window_owner_edges(window: Sequence[Cut], worldlines: Sequence[Worldline]) -> List[OwnerEdge]:
    return [owner_edge(window[i], window[i + 1], worldlines) for i in range(len(window) - 1)]

"""WO_WEAVE_R2B · owner-provenance + reactive-complement — cell-exact, owner-grain.

At each worldline edge, account for EVERY cell's ownership across the transition:
cell -> (owner@t, owner@t+1), where owner = the ### worldline that holds the cell's
region at that node. A worldline is a REACTIVE COMPLEMENT over an edge iff ALL its
churn is site-exact EXCHANGE — every cell it lost was gained by another *continuing*
owner and every cell it gained was lost by another; none of its delta is intrinsic.
It originates nothing; it only absorbs others' motion. The cells that are NOT
owner-owner exchange are INTRINSIC — the "loud"/unexplained residual (reveals from a
newborn owner, vanishes into a dying one). A complement has intrinsic_cells == ∅.

STRUCTURAL RELATIONSHIPS (stated at the point of code, per Director):
  * PARALLEL to library/conserved_transfer_author.py (COUNT grain) — this is the
    cell-exact owner-grain sibling. NOT an extension, NOT an import. The relationship
    is CROSS-CHECK ONLY (tests/weave/test_provenance.py::C3): Σ our per-cell
    exchanges == its conserved quantity on the same transition.
  * DISTINCT from library/ego_detector.py (frame-diff / value / centroid grain). R2b
    does not detect an ego; it produces the owner substrate a later pass could feed
    to ego reasoning. No overlap, no call.
  * DISTINCT from weave/induced_map.py (whole-grid STATE topology). R2b is beneath
    the state graph, at cell/owner grain.
  * ONTOLOGY: every cell has an owner. There is NO background, NO is_background, NO
    FLOOR here. "Quiet" (a complement) is EARNED per edge from the cells, never
    assumed by size, class, or position.

Pure over the atoms + edge.py/worldline.py: stdlib only. Site-exact (set equality on
frozensets); robust to multi-cell jumps (no adjacency or 1-cell-swap assumption).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Tuple

Cell = Tuple[int, int]
# Owner is a ### worldline id (int). There is no NONE owner for an interior cell:
# the per-node partition is disjoint ∧ covering (grade_pristine), so every cell at
# every node has exactly one owner. "Boundary" is a worldline's birth/death, captured
# by the `continuing` set, not by a NONE owner.


@dataclass(frozen=True)
class OwnerEdge:
    """Every cell whose owner changed across an adjacent (prev -> now) pair, plus the
    set of worldlines CONTINUING across the edge (present at both nodes). An
    owner-owner EXCHANGE requires both endpoints continuing; a change into a born
    worldline (or out of a dying one) is a boundary event, not an exchange."""

    prev_node: int
    now_node: int
    exchanges: Tuple[Tuple[Cell, int, int], ...]     # (cell, owner@t, owner@t+1)
    continuing: FrozenSet[int]                        # worldline ids present at both nodes


@dataclass(frozen=True)
class ComplementVerdict:
    worldline_id: int
    is_reactive_complement: bool
    intrinsic_cells: FrozenSet[Cell]                  # churn NOT owner-owner accounted (loud)
    exchange_cells: FrozenSet[Cell]                   # churn that IS owner-owner exchange
    partners: Dict[int, FrozenSet[Cell]]              # other worldline id -> cells exchanged


# ---------------------------------------------------------------------------
# Owner maps
# ---------------------------------------------------------------------------

def worldline_owner_index(worldlines) -> Dict[Tuple[int, Any], int]:
    """(node_index, region) -> worldline id, total over every region at every node
    in the window (weave_window seeds/continues/births every region into exactly one
    worldline)."""
    index: Dict[Tuple[int, Any], int] = {}
    for wl in worldlines:
        for (node_index, region) in wl.steps:
            index[(node_index, region)] = wl.id
    return index


def cell_owners(cut, owner_index) -> Dict[Cell, int]:
    """Invert cut.regions to a per-cell owner map (cell -> worldline id). Enforces
    DISJOINTNESS (no cell owned twice). Totality (every grid cell owned) is the P2
    partition invariant on real ledger cuts — check it with ``is_total`` where the
    cut is a genuine PRISTINE partition (the live guard); synthetic test cuts may be
    intentionally sparse."""
    owners: Dict[Cell, int] = {}
    for region in cut.regions:
        wid = owner_index[(cut.node_index, region)]
        for cell in region.cells:
            if cell in owners:
                raise AssertionError(f"cell {cell} owned by two regions at node {cut.node_index}")
            owners[(int(cell[0]), int(cell[1]))] = wid
    return owners


def is_total(owners: Dict[Cell, int], cut) -> bool:
    """True iff every cell of the grid is owned — the covering half of the P2 partition
    (holds on PRISTINE ledger cuts; asserted on live data in the guard)."""
    h, w = cut.grid_shape
    return bool(h and w) and len(owners) == h * w


def _present_nodes(worldlines) -> Dict[int, FrozenSet[int]]:
    return {wl.id: frozenset(s[0] for s in wl.steps) for wl in worldlines}


# ---------------------------------------------------------------------------
# The edge account + the complement verdict
# ---------------------------------------------------------------------------

def owner_edge(cut_t, cut_t1, worldlines) -> OwnerEdge:
    """Site-exact owner change across (cut_t -> cut_t1). For every cell whose owner
    changed, record (cell, owner@t, owner@t+1). `continuing` = worldlines with a step
    at BOTH nodes — the ones eligible for owner-owner exchange."""
    index = worldline_owner_index(worldlines)
    o_t = cell_owners(cut_t, index)
    o_t1 = cell_owners(cut_t1, index)
    changed = tuple(
        (cell, o_t[cell], o_t1[cell])
        for cell in o_t
        if o_t1.get(cell) is not None and o_t1[cell] != o_t[cell]
    )
    present = _present_nodes(worldlines)
    tnode, t1node = cut_t.node_index, cut_t1.node_index
    continuing = frozenset(
        wid for wid, nodes in present.items() if tnode in nodes and t1node in nodes
    )
    return OwnerEdge(tnode, t1node, changed, continuing)


def complement_verdict(worldline, edge: OwnerEdge) -> ComplementVerdict:
    """Is this worldline a reactive complement over `edge`? A cell is an owner-owner
    EXCHANGE iff both its giver and receiver are continuing. lost/gained cells that
    are not exchanges are INTRINSIC (loud). Complement <=> continuing, churn nonempty,
    intrinsic == ∅."""
    wid = worldline.id
    cont = edge.continuing

    def is_exchange(giver: int, receiver: int) -> bool:
        return giver in cont and receiver in cont

    lost, gained = set(), set()
    exchange, intrinsic = set(), set()
    partners: Dict[int, set] = {}
    for (cell, giver, receiver) in edge.exchanges:
        if giver == wid:
            lost.add(cell)
            if is_exchange(giver, receiver):
                exchange.add(cell)
                partners.setdefault(receiver, set()).add(cell)
            else:
                intrinsic.add(cell)
        elif receiver == wid:
            gained.add(cell)
            if is_exchange(giver, receiver):
                exchange.add(cell)
                partners.setdefault(giver, set()).add(cell)
            else:
                intrinsic.add(cell)

    churn = lost | gained
    is_rc = (wid in cont) and bool(churn) and not intrinsic
    return ComplementVerdict(
        worldline_id=wid,
        is_reactive_complement=is_rc,
        intrinsic_cells=frozenset(intrinsic),
        exchange_cells=frozenset(exchange),
        partners={k: frozenset(v) for k, v in partners.items()},
    )


def window_owner_edges(cuts_in_window, worldlines) -> List[OwnerEdge]:
    """owner_edge for each adjacent pair in the window — the provenance substrate for
    the dossier."""
    return [
        owner_edge(cuts_in_window[i], cuts_in_window[i + 1], worldlines)
        for i in range(len(cuts_in_window) - 1)
    ]

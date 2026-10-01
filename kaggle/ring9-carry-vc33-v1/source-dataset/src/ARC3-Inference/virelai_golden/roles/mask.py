"""ROLES · mask — the sealed counters subtracted, retroactively, and the masked state address.

Canon: 02 §6.3 COUNTER, position — "identified, its rate becomes a subtraction term removed
from every subsequent delta read"; the two-counter point (fill + empty = the whole bar, a
footprint that holds while the bar ticks); 04 R-B — "σ is the address, not the picture"; 03 §9
(the map converges only once the counter is masked); R-H (the record persists; masking is
re-derivation, never un-storing). Director's given fact (2026-09-06): retroactive counter
masking is what isolates levers — a v4 discovery.

NEW — no single v4 origin. v4 masked at the map (`weave/induced_map.py`, "masked address") and
subtracted the counter at the lever witness; both are Rung 3–5 consumers here. What this module
does is the substrate of both: per node, the union of cells owned by any sealed counter
worldline; the address of a node with those cells quotiented out; the delta of a press with
those cells removed. Applied to EVERY node and press of the record, whole game (R-H) — the
"retroactive" is automatic because roles are derived on each call and nothing was stored.

Typed silence: the mask token is an ADDRESS construction, never a class of the world (01 §3
totality is untouched — the cells still hold their values; the address is a quotient of the
picture, and R-B says the address is what a state IS). A world with no sealed counter has the
identity mask, and its addresses are the pictures.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Sequence, Tuple

import numpy as np

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.worldline import Worldline, region_at

MASK = -1  # outside the platform's class range 0–15; an address token, not a class


def counter_cells(window: Sequence[Cut], worldlines: Sequence[Worldline],
                  counter_ids: FrozenSet[int]) -> Dict[int, FrozenSet[Cell]]:
    """node → the union of cells owned by sealed-counter worldlines at that node."""
    by_id = {w.id: w for w in worldlines if w.id in counter_ids}
    out: Dict[int, FrozenSet[Cell]] = {}
    for c in window:
        cells: set = set()
        for w in by_id.values():
            r = region_at(w, c.node)
            if r is not None:
                cells |= r.cells
        out[c.node] = frozenset(cells)
    return out


def masked_grid(grid: np.ndarray, cells: FrozenSet[Cell]) -> np.ndarray:
    g = grid.copy()
    for r, c in cells:
        g[r, c] = MASK
    return g


def address(grid: np.ndarray, cells: FrozenSet[Cell]) -> str:
    """The state address: sha256 over the masked picture. Two nodes share it iff every unmasked
    cell agrees — the counter's tick is quotiented out."""
    return hashlib.sha256(masked_grid(grid, cells).tobytes() + bytes(grid.shape)).hexdigest()[:16]


@dataclass(frozen=True)
class StateMap:
    addresses: Tuple[str, ...]            # per node, in window order
    visits: Dict[str, Tuple[int, ...]]    # address → nodes
    masked_cells: int                     # size of the mask at node 0 (a reading)

    @property
    def distinct(self) -> int:
        return len(self.visits)

    @property
    def revisits(self) -> int:
        return sum(len(n) - 1 for n in self.visits.values())


def state_map(record: Record, window: Sequence[Cut], cells_by_node: Dict[int, FrozenSet[Cell]]) -> StateMap:
    addrs: List[str] = []
    visits: Dict[str, List[int]] = {}
    for c in window:
        a = address(record.nodes[c.node].settled, cells_by_node.get(c.node, frozenset()))
        addrs.append(a)
        visits.setdefault(a, []).append(c.node)
    first = window[0].node if window else 0
    return StateMap(tuple(addrs), {k: tuple(v) for k, v in visits.items()},
                    len(cells_by_node.get(first, frozenset())))


def masked_delta(changed: FrozenSet[Cell], before: FrozenSet[Cell], after: FrozenSet[Cell]) -> FrozenSet[Cell]:
    """A press's changed cells with the counter's cells (at either end) removed."""
    return changed - before - after

"""ROLES · ego (POINTER) — on a null-locus world, the site-selecting action itself.

Canon: 04 R3 v1.1 / R-F — "POINTER: on a null-locus world, the site-selecting action itself,
sealed on the first press that produces a delta anywhere (an ∃-witness), with no worldline
footprint"; 02 §6.3 EGO, null-locus modality — "covariance between actions and
world-changes-at-selected-sites"; R-K (binary seal; coverage is parallax).

NEW — no v4 origin. v4 never emitted a pointer verdict (`role_read.py:1049-1053` rendered a
click-world mover as "EGO out-of-input; Band 2 ∅"). The only transcribed piece is the wiring
law of `virelai_v4/weave/action_roster.py` `acted_on` (:200-243): a targeted press that produced
node t is resolved against cut t−1 — the frame the captain saw — never against t, where the
clicked object may already have moved; an unowned cell reads EMPTY, never snapped.

What this reads, per targeted press: the site pressed, the worldline that owned it at t−1, and
the cells whose class changed t−1 → t. The changed set is reported RAW and UNATTRIBUTED, per
worldline pressed, with its size range. A first draft subtracted an "always-part" (cells changed
on every press) to isolate the site-specific response; withdrawn on the Director's given facts
(2026-09-06): vc33's tick lands on new cells each press (intersection empty), and ft09's counter
ticks only on lever clicks — an instrument that assumes the counter's schedule is the wrong
evidence class. Attribution waits for Rung 2's COUNTER seal, and then applies RETROACTIVELY over
the whole record (v4's discovery: retroactive counter masking is what isolates levers) — free
here by construction, since roles are derived from the record on every call and nothing is
stored to un-store. The Director's name for this ego kind is "god mode"; rendered beside POINTER.
Typed silence: with one distinct site pressed, site-dependence is unaskable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.provenance import cell_owners, worldline_owner_index
from virelai_golden.weave.worldline import Worldline


@dataclass(frozen=True)
class PointerPress:
    node: int                       # the node this press produced
    action: int
    site: Cell                      # (row, col) pressed
    owner_before: Optional[int]     # worldline owning the site at t−1; None = EMPTY (out of bounds)
    changed: FrozenSet[Cell]        # every cell whose class differs t−1 → t


@dataclass(frozen=True)
class PointerRead:
    presses: Tuple[PointerPress, ...]


@dataclass(frozen=True)
class PointerVerdict:
    kind: str                       # "POINTER"
    witness: PointerPress           # the first delta-producing targeted press (R-F)
    sites_pressed: int
    delta_presses: Tuple[PointerPress, ...]  # presses that changed something (UNATTRIBUTED)
    basis: str
    parallax: str


def _changed_cells(a: np.ndarray, b: np.ndarray) -> FrozenSet[Cell]:
    if a.shape != b.shape:
        return frozenset((int(r), int(c)) for r in range(max(a.shape[0], b.shape[0]))
                         for c in range(max(a.shape[1], b.shape[1])))
    return frozenset((int(r), int(c)) for r, c in np.argwhere(a != b))


def pointer_read(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline]) -> PointerRead:
    """Every targeted press in the window, resolved at t−1, with its changed-cell set."""
    by_node = {c.node: c for c in window}
    index = worldline_owner_index(worldlines)
    presses: List[PointerPress] = []
    for node in record.nodes:
        act = node.action
        if act is None or act[1] is None or node.index not in by_node or node.index - 1 not in by_node:
            continue
        prev = record.nodes[node.index - 1]
        try:
            owner = cell_owners(by_node[node.index - 1], index).get(act[1])
        except (AssertionError, KeyError):
            owner = None
        presses.append(PointerPress(node.index, act[0], act[1], owner,
                                    _changed_cells(prev.settled, node.settled)))
    return PointerRead(tuple(presses))


def pointer_seal(read: PointerRead) -> Optional[PointerPress]:
    """R-F: the first targeted press that produced a delta anywhere. None = no such press."""
    for p in read.presses:
        if p.changed:
            return p
    return None


def infer_ego_pointer(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline]
                      ) -> Tuple[Optional[PointerVerdict], PointerRead]:
    read = pointer_read(record, window, worldlines)
    w = pointer_seal(read)
    if w is None:
        return None, read
    sites = {p.site for p in read.presses}
    with_delta = tuple(p for p in read.presses if p.changed)
    basis = (f"WITNESSED: press A{w.action} at {w.site} (node {w.node}) changed {len(w.changed)} cell(s) "
             f"→ the site-selecting action produces deltas; {len(read.presses)} targeted press(es) over "
             f"{len(sites)} distinct site(s); {len(with_delta)} changed something — UNATTRIBUTED: the "
             f"COUNTER's tick is inside these until Rung 2 names it and masks it retroactively")
    if len(sites) <= 1:
        parallax = "1 site pressed: site-dependence is unaskable; reopens as coverage arrives"
    else:
        parallax = ("no number separates a tick from a response here and none is introduced; the "
                    "lever hunt (R-G) reads these deltas after the counter is masked (Rung 2)")
    return PointerVerdict("POINTER", w, len(sites), with_delta, basis, parallax), read


def deltas_by_owner(verdict: PointerVerdict) -> List[Tuple[str, int, int, int]]:
    """(owner label, presses, min changed, max changed) per worldline pressed — a reading."""
    acc: Dict[Optional[int], List[int]] = {}
    for p in verdict.delta_presses:
        acc.setdefault(p.owner_before, []).append(len(p.changed))
    rows = []
    for o, sizes in sorted(acc.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
        rows.append(("EMPTY" if o is None else f"###{o:03d}", len(sizes), min(sizes), max(sizes)))
    return rows

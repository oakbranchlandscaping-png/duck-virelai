"""CAPTAIN · sweep (click arm) — press every worldline the pointer can reach, once; stop when the
enumeration is complete, never on the first lever and never on a run of inerts.

Canon: 03 §5 (the opening is generative: touch everything once — exhaustive by enumeration, so
the world is forced to reveal itself and the opening terminates); 03 §7 (the lever hunt is over
what the ego can reach — R-G); R-H (the record is whole-game: what was attempted in life 1 is
attempted in life 2; the enumeration carries across lives); R-A (the sweep runs after the ego
and counter seal — the opening IS that probe, and this policy runs it first). 02 §6.2: LEVER is
∃ (one witness) and INERT is ∀ (never provable) — so neither a witnessed lever nor any number of
null presses is a reason to stop; only the exhaustion of the enumeration is.

Transcription origin (R-C): virelai_v4/weave/coverage_sweep.py:676-731 (the CLICK arm of
`coverage_sweep`; WO_COVERAGE_SWEEP — "enumeration complete, never first-lever, never 8 inerts",
one log line per press). What it proved: `NEVER ATTEMPTED 0` on the click canary in the golden
logs of 2026-09-05. NOT carried: v4's queue over the master object list (a per-life structure —
R-H); the "8 inerts" early-stop that the origin itself retired.

Golden's form. The enumeration is over WORLDLINES of the whole-game weave, re-derived from the
record on every press (roles derived, never stored — the same discipline at the captain). A
worldline is ATTEMPTED iff some targeted press in the record resolved to it at the press's left
node (the wiring law). The next press is the lowest-numbered worldline PRESENT at the current
node and not yet attempted, clicked at its NW-most member cell (a member, never the bbox corner —
a click on a non-member cell is a click on someone else). Lowest-numbered is first-appearance
order, then the visual-object sort: deterministic, and a labeled convention — canon 03 §5 says
"exhaustive by enumeration" and fixes no order. A worldline that is never present on its turn is
reported NOT REACHED by the coverage roster; the sweep does not wait for it. ENUMERATION_COMPLETE
is the only terminal: no present worldline is un-attempted.

The policy protocol grows one argument: `next(available, frame0, givens)` — the record so far.
`Opening` ignores it. The adapter passes it to every policy.
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from virelai_golden.captain.opening import CLICK, Action, Opening
from virelai_golden.substrate.ledger import Cut, cuts
from virelai_golden.substrate.record import Given, Record, build
from virelai_golden.weave.provenance import cell_owners, worldline_owner_index
from virelai_golden.weave.rejoin import re_join
from virelai_golden.weave.worldline import Worldline, region_at, weave_window


def record_so_far(givens: Sequence[Given]) -> Record:
    return build(list(givens), origin="live", action_channel="LIVE", source="captain")


def woven(record: Record) -> Tuple[List[Cut], List[Worldline]]:
    window = cuts(record)
    return window, re_join(weave_window(window), window)


def attempted(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline]) -> Dict[int, int]:
    """worldline id → presses that resolved to it (targeted presses, resolved at the left node)."""
    index = worldline_owner_index(worldlines)
    by_node = {c.node: c for c in window}
    out: Dict[int, int] = {}
    for n in record.nodes:
        if n.action is None or n.action[1] is None or n.index - 1 not in by_node:
            continue
        try:
            o = cell_owners(by_node[n.index - 1], index).get(n.action[1])
        except (AssertionError, KeyError):
            o = None
        if o is not None:
            out[o] = out.get(o, 0) + 1
    return out


def member_anchor(cells: FrozenSet[Tuple[int, int]]) -> Tuple[int, int]:
    return min(cells)


class Sweep:
    """Opening first (the ego/counter probe), then the enumeration. State is the record."""

    def __init__(self) -> None:
        self.opening = Opening()
        self.complete_reason: Optional[str] = None
        self.last: Optional[str] = None
        self.presses = 0

    def next(self, available: Sequence[int], frame0_layers: Any,
             givens: Optional[Sequence[Given]] = None) -> Optional[Action]:
        if self.opening.complete_reason is None:
            a = self.opening.next(available, frame0_layers)
            if a is not None:
                self.last = self.opening.note(a)
                return a
        if CLICK not in available or not givens:
            self.complete_reason = (self.opening.complete_reason or "") + "; no site-selecting action offered: the click sweep is unaskable"
            return None
        record = record_so_far(givens)
        window, wls = woven(record)
        done = attempted(record, window, wls)
        now = window[-1].node
        present = [w for w in wls if region_at(w, now) is not None]
        todo = [w for w in present if w.id not in done]
        if not todo:
            absent = [w for w in wls if w.id not in done and region_at(w, now) is None]
            self.complete_reason = (f"ENUMERATION_COMPLETE: {len(done)} worldline(s) attempted, "
                                    f"{len(present)} present at node {now} all attempted, "
                                    f"{len(absent)} not reached (never present on their turn); "
                                    f"{self.presses} sweep press(es)")
            return None
        w = todo[0]
        r = region_at(w, now)
        cell = member_anchor(r.cells)
        self.presses += 1
        self.last = (f"sweep · press {self.presses} · ###{w.id:03d} (class {r.value}, {r.area} cells) at {cell} · "
                     f"attempted {len(done)} of {len(present)} present, {len(todo) - 1} to go")
        return CLICK, cell

    def note(self, action: Action) -> str:
        return self.last or "sweep"

"""WEAVE · worldline — thread edges into persistent ### worldlines.

Canon: 02 §4 — the worldline is the object; identity is constructed, lives on the worldline
and is never a per-frame label. Rung 3 reads only rung 2 (regions) through the matcher.

Transcription origin (R-C): virelai_v4/weave/worldline.py @ oracle-v4 (134 lines, read whole)
— `Worldline`, `region_at`, `weave_window`, `window_edges`. What it proved: worldlines seed and
number from the visual-object sort, so ### numbers are independent of region-list order; the
LIST 2 rosters of 2026-09-05 (Y = 26 / 27) are its output after rejoin.

Kept verbatim: window-start regions SEED (initial state, not BIRTH); continue-verbs extend;
BIRTH seeds mid-window; DEATH / DEFORM / AMBIGUOUS terminate — SPLIT / MERGE are never decided
here (INTERIM_O9, edge.py). Numbering: first-appearance node, then (|cells|, class, anchor).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.scan import Region
from virelai_golden.weave.edge import WeaveEdge, visual_order, weave_edge
from virelai_golden.weave.verbs import Verb

CONTINUE = frozenset({Verb.STILL, Verb.RECOLOR, Verb.MOVE, Verb.GROW, Verb.SHRINK})


@dataclass(frozen=True)
class Worldline:
    """One persistent ### object: (node, region) steps and the stitch-verbs between them."""

    id: int
    steps: Tuple[Tuple[int, Region], ...]
    edges: Tuple[WeaveEdge, ...]  # len(steps) − 1

    @property
    def first_node(self) -> int:
        return self.steps[0][0]

    @property
    def last_node(self) -> int:
        return self.steps[-1][0]

    @property
    def first_region(self) -> Region:
        return self.steps[0][1]

    @property
    def last_region(self) -> Region:
        return self.steps[-1][1]

    @property
    def verbs(self) -> Tuple[Verb, ...]:
        return tuple(e.verb for e in self.edges)


def region_at(worldline: Worldline, node: int) -> Optional[Region]:
    """The region this worldline holds AT `node`, or None — never `first_region`."""
    for n, region in worldline.steps:
        if n == node:
            return region
    return None


class _Builder:
    __slots__ = ("steps", "edges")

    def __init__(self, node: int, region: Region) -> None:
        self.steps: List[Tuple[int, Region]] = [(node, region)]
        self.edges: List[WeaveEdge] = []


def weave_window(window: Sequence[Cut]) -> List[Worldline]:
    """Thread a window of cuts into numbered worldlines."""
    if not window:
        return []
    builders: List[_Builder] = []
    active: Dict[Region, _Builder] = {}
    c0 = window[0]
    for r in visual_order(c0.regions):
        b = _Builder(c0.node, r)
        builders.append(b)
        active[r] = b
    for t in range(len(window) - 1):
        ct, cn = window[t], window[t + 1]
        next_active: Dict[Region, _Builder] = {}
        for e in weave_edge(ct.regions, cn.regions):
            if e.verb in CONTINUE:
                b = active.get(e.prev)
                if b is None:  # origin's defensive branch, kept: a prev not tracked seeds late
                    b = _Builder(ct.node, e.prev)
                    builders.append(b)
                b.steps.append((cn.node, e.now))
                b.edges.append(e)
                next_active[e.now] = b
            elif e.verb is Verb.BIRTH:
                b = _Builder(cn.node, e.now)
                builders.append(b)
                next_active[e.now] = b
        active = next_active
    ordered = sorted(builders, key=lambda b: (b.steps[0][0], b.steps[0][1].area,
                                              b.steps[0][1].value, b.steps[0][1].anchor))
    return [Worldline(i + 1, tuple(b.steps), tuple(b.edges)) for i, b in enumerate(ordered)]


def window_edges(window: Sequence[Cut]) -> List[Tuple[int, int, WeaveEdge]]:
    """Every edge verdict across the window as (from_node, to_node, edge)."""
    out: List[Tuple[int, int, WeaveEdge]] = []
    for t in range(len(window) - 1):
        for e in weave_edge(window[t].regions, window[t + 1].regions):
            out.append((window[t].node, window[t + 1].node, e))
    return out

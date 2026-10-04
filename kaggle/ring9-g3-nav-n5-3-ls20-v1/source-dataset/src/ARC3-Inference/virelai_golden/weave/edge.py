"""WEAVE · edge — the pairwise matcher: which region at t corresponds to which at t+1.

═══ INTERIM_O9 ═══ This matcher is ANCHOR-FIRST (site footprint → held class + licensed
transform → residual). CANON_4 O-9 — is correspondence cardinality-first or anchor-first? — is
OPEN (ADR-0007, D-2). This file transcribes v4's proven side so the golden run has a weave;
it does not rule the fork. SPLIT / MERGE are never decided here: a contest surfaces as
AMBIGUOUS and is handed up. Anyone answering O-9 replaces this file; nothing above it may
depend on which side it took.

Canon: 02 §6 (verbs on stitches), rung 3 (worldlines read only visual objects).

Transcription origin (R-C): virelai_v4/weave/edge.py @ oracle-v4 (204 lines, read whole) —
`Anchor`, `WeaveEdge`, `weave_edge` and its three passes, `_norm`, `_translation`,
`_classify_class_anchored`, `_visual_order`, `_delta_for`. What it proved: order-independent
edges (walk over the visual-object sort) on every canary since WO_WEAVE_S2; the LIST 2 counts
Y = 26 / 27 in the golden logs of 2026-09-05 rest on it.
"""
from __future__ import annotations

import enum
from functools import lru_cache
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from virelai_golden.substrate.scan import Cell, Region
from virelai_golden.weave.verbs import TransitionSignature, Verb, transition_signature

INTERIM_O9 = "correspondence: anchor-first (site → class → residual); CANON_4 O-9 is OPEN (ADR-0007)"


class Anchor(enum.Enum):
    SITE = "SITE"    # matched on exact footprint
    CLASS = "CLASS"  # matched on held class + a licensed transform
    NONE = "NONE"    # unmatched (birth/death/deform/ambiguous)


@dataclass(frozen=True)
class WeaveEdge:
    """One region's correspondence verdict between adjacent nodes."""

    prev: Optional[Region]
    now: Optional[Region]
    verb: Verb
    anchor: Anchor
    delta: Any = None  # RECOLOR:(c0,c1) · GROW/SHRINK:int · MOVE:(dr,dc) · else None
    signature: Optional[TransitionSignature] = None  # None for residual verbs by construction


@lru_cache(maxsize=4096)
def _norm(cells: FrozenSet[Cell]) -> FrozenSet[Cell]:
    """Shape modulo position: the cell-set shifted so its NW corner is the origin."""
    if not cells:
        return frozenset()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _translation(prev_cells: FrozenSet[Cell], now_cells: FrozenSet[Cell]) -> Optional[Tuple[int, int]]:
    """(dr, dc) if `now` is `prev` translated by a non-zero offset; else None."""
    if len(prev_cells) != len(now_cells) or _norm(prev_cells) != _norm(now_cells):
        return None
    pr, pc = min(r for r, _ in prev_cells), min(c for _, c in prev_cells)
    nr, nc = min(r for r, _ in now_cells), min(c for _, c in now_cells)
    off = (nr - pr, nc - pc)
    return off if off != (0, 0) else None


def _classify_class_anchored(prev: Region, now: Region) -> Optional[Verb]:
    """The single licensed class-anchored verb for a same-class pair, or None (combined,
    rotated or reflected — the R2a limit)."""
    p, n = prev.cells, now.cells
    if n > p:
        return Verb.GROW
    if n < p:
        return Verb.SHRINK
    if _translation(p, n) is not None:
        return Verb.MOVE
    return None


def visual_order(regions: Sequence[Region]) -> List[Region]:
    """|cells| asc, then class asc, then anchor — the deterministic walk order."""
    return sorted(regions, key=lambda r: (r.area, r.value, r.anchor))


def _delta_for(verb: Verb, prev: Region, now: Region) -> Any:
    if verb is Verb.RECOLOR:
        return (prev.value, now.value)
    if verb in (Verb.GROW, Verb.SHRINK):
        return now.area - prev.area
    if verb is Verb.MOVE:
        return _translation(prev.cells, now.cells)
    return None


def weave_edge(prev_regions: Sequence[Region], now_regions: Sequence[Region]) -> List[WeaveEdge]:
    # Immutable inputs and verdicts: cache exact adjacent frames, never model beliefs.
    # Return a fresh list so callers cannot mutate the cached result.
    return list(_cached_weave_edge(tuple(prev_regions), tuple(now_regions)))


@lru_cache(maxsize=256)
def _cached_weave_edge(prev_regions: Tuple[Region, ...], now_regions: Tuple[Region, ...]) -> Tuple[WeaveEdge, ...]:
    """One WeaveEdge per region across an adjacent (prev → now) pair.

    1. SITE  — exact footprint: STILL if class held, else RECOLOR.
    2. CLASS — class held + one licensed transform (MOVE / GROW / SHRINK);
               ≥ 2 licensed candidates → AMBIGUOUS (consume nothing);
               none licensed → DEFORM if a same-class partner exists, else DEATH.
    3. residual now-regions → BIRTH.
    """
    prevs = visual_order(prev_regions)
    nows = visual_order(now_regions)
    consumed: set = set()
    edges: List[WeaveEdge] = []

    by_cells: Dict[FrozenSet[Cell], int] = {}
    for i, q in enumerate(nows):
        by_cells.setdefault(q.cells, i)
    unmatched_prev: List[Region] = []
    for p in prevs:
        i = by_cells.get(p.cells)
        if i is not None and i not in consumed:
            q = nows[i]
            verb = Verb.STILL if q.value == p.value else Verb.RECOLOR
            consumed.add(i)
            edges.append(WeaveEdge(p, q, verb, Anchor.SITE, _delta_for(verb, p, q),
                                   transition_signature(p, q)))
        else:
            unmatched_prev.append(p)

    by_class: Dict[int, List[int]] = {}
    for i, q in enumerate(nows):
        by_class.setdefault(q.value, []).append(i)
    for p in unmatched_prev:
        pool = [i for i in by_class.get(p.value, []) if i not in consumed]
        licensed = [(i, v) for i, v in ((i, _classify_class_anchored(p, nows[i])) for i in pool)
                    if v is not None]
        if len(licensed) == 1:
            i, verb = licensed[0]
            q = nows[i]
            consumed.add(i)
            edges.append(WeaveEdge(p, q, verb, Anchor.CLASS, _delta_for(verb, p, q),
                                   transition_signature(p, q)))
        elif len(licensed) >= 2:
            edges.append(WeaveEdge(p, None, Verb.AMBIGUOUS, Anchor.NONE))
        else:
            edges.append(WeaveEdge(p, None, Verb.DEFORM if pool else Verb.DEATH, Anchor.NONE))

    for i, q in enumerate(nows):
        if i not in consumed:
            edges.append(WeaveEdge(None, q, Verb.BIRTH, Anchor.NONE))
    return tuple(edges)

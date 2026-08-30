"""WO_WEAVE_S2_EDGE_MATCHER · the pairwise edge-matcher — match + classify as one act.

Given two adjacent per-node object-lists (``prev_regions``, ``now_regions`` — each a
list of ``RegionClay``, the unmatched ρ-input from the Sighting Ledger), assign to
every region a single licensed ``WeaveEdge`` carrying its verb, its matching anchor,
and a verb-specific delta. This is the raw correspondence R2 owes: the two key-sets
become two indices, and a three-pass cascade (SITE footprint → CLASS-held transform →
residual) emits ``(stitch, verb)`` per region.

Pure geometry over the atoms: stdlib only, ``RegionClay`` in, ``WeaveEdge`` out. No
perception (no ``scan_grid``/scipy), no belief, no threading into worldlines (Step 3),
no scored contest resolution and no SPLIT/MERGE (Step 4). SPLIT/MERGE surface here only
as ``AMBIGUOUS`` (a contest handed up), never as a verdict.

Determinism: regions are walked in visual-object order (``|cells|`` asc, then
``class_id`` asc), so the emitted edge set is independent of input list order.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

Cell = Tuple[int, int]


class Verb(enum.Enum):
    STILL = "STILL"          # same footprint, same class
    RECOLOR = "RECOLOR"      # same footprint, class changed
    MOVE = "MOVE"            # same class, same shape, translated
    GROW = "GROW"            # same class, now ⊃ prev
    SHRINK = "SHRINK"        # same class, now ⊂ prev
    BIRTH = "BIRTH"          # residual now-region, no prev partner
    DEATH = "DEATH"          # prev-region, no same-class partner at all
    DEFORM = "DEFORM"        # same-class partner exists but no single licensed verb
    AMBIGUOUS = "AMBIGUOUS"  # ≥2 licensed same-class candidates — a contest (Step 4)


class Anchor(enum.Enum):
    SITE = "SITE"      # matched on exact footprint
    CLASS = "CLASS"    # matched on held class value + a licensed transform
    NONE = "NONE"      # unmatched (birth/death/deform/ambiguous)


# WO-SPLIT-AND-SHOW-01: the transition signature and the verb-naming it supports were
# EXTRACTED VERBATIM to weave/transition_signature.py. This module is the pairwise
# edge-MATCHER, as its own docstring says; the arithmetic that names an edge is a
# separate concern and now lives in a separate file. Re-exported below so every
# existing importer of `edge` keeps working unchanged.


from virelai_v4.weave.transition_signature import (          # noqa: E402  (see above)
    TransitionSignature,
    transition_signature,
    verb_from_signature,
)

__all__ = ["Verb", "Anchor", "WeaveEdge", "weave_edge",
           "TransitionSignature", "transition_signature", "verb_from_signature"]


@dataclass(frozen=True)
class WeaveEdge:
    """One region's correspondence verdict between adjacent nodes."""

    prev: Optional[Any]      # RegionClay | None
    now: Optional[Any]       # RegionClay | None
    verb: Verb
    anchor: Anchor
    delta: Any = None        # RECOLOR:(c0,c1) · GROW/SHRINK:int · MOVE:(dr,dc) · else None
    # WO-VERB-FROM-TRANSITIONS-01 — the class-labelled account of what this pair's own
    # cells did. Defaulted so every existing construction site keeps working unchanged;
    # `None` for residual verbs by construction (one endpoint absent).
    signature: Optional[TransitionSignature] = None


# ---------------------------------------------------------------------------
# Pure geometry helpers
# ---------------------------------------------------------------------------

def _norm(cells) -> FrozenSet[Cell]:
    """Cell-set shifted so its top-left is the origin — shape modulo position."""
    cells = frozenset(cells)
    if not cells:
        return frozenset()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _translation(prev_cells, now_cells) -> Optional[Tuple[int, int]]:
    """The (dr, dc) offset if ``now`` is ``prev`` translated (same size, same shape,
    nonzero offset); else ``None``."""
    prev_cells = frozenset(prev_cells)
    now_cells = frozenset(now_cells)
    if len(prev_cells) != len(now_cells):
        return None
    if _norm(prev_cells) != _norm(now_cells):
        return None
    pr = min(r for r, _ in prev_cells); pc = min(c for _, c in prev_cells)
    nr = min(r for r, _ in now_cells); nc = min(c for _, c in now_cells)
    off = (nr - pr, nc - pc)
    return off if off != (0, 0) else None


def _classify_class_anchored(prev: Any, now: Any) -> Optional[Verb]:
    """The single licensed class-anchored verb for a (prev, now) same-class pair,
    or ``None`` when no single verb fits (combined/rotated/reflected — R2a limit)."""
    p = frozenset(prev.cells)
    n = frozenset(now.cells)
    if n > p:
        return Verb.GROW
    if n < p:
        return Verb.SHRINK
    if _translation(p, n) is not None:
        return Verb.MOVE
    return None


def _visual_order(regions) -> List[Any]:
    """|cells| asc, then class_id asc, then anchor — the deterministic walk order."""
    return sorted(regions, key=lambda r: (r.cell_count, r.class_id, r.anchor))


def _delta_for(verb: Verb, prev: Any, now: Any) -> Any:
    if verb is Verb.RECOLOR:
        return (prev.class_id, now.class_id)
    if verb in (Verb.GROW, Verb.SHRINK):
        return now.cell_count - prev.cell_count
    if verb is Verb.MOVE:
        return _translation(prev.cells, now.cells)
    return None


# ---------------------------------------------------------------------------
# The matcher
# ---------------------------------------------------------------------------

def weave_edge(prev_regions, now_regions) -> List[WeaveEdge]:
    """Assign one ``WeaveEdge`` per region across an adjacent (prev → now) pair.

    Three passes, highest-priority first:
      1. SITE  — exact footprint match (STILL if class held, else RECOLOR);
      2. CLASS — value held + a single licensed transform (MOVE/GROW/SHRINK);
                 ≥2 licensed candidates → AMBIGUOUS (contest, consume nothing);
                 no licensed candidate → DEFORM if a same-class partner exists, else DEATH;
      3. residual now-regions → BIRTH.
    Order-independent: the walk is over the visual-object sort.
    """
    prevs = _visual_order(prev_regions)
    nows = _visual_order(now_regions)
    consumed: set = set()          # indices into ``nows`` already stitched
    edges: List[WeaveEdge] = []

    # ---- PASS 1 · SITE (exact footprint) ----
    by_cells: Dict[FrozenSet[Cell], int] = {}
    for i, q in enumerate(nows):
        by_cells.setdefault(frozenset(q.cells), i)   # partition: cell-set unique
    unmatched_prev: List[Any] = []
    for p in prevs:
        key = frozenset(p.cells)
        i = by_cells.get(key)
        if i is not None and i not in consumed:
            q = nows[i]
            verb = Verb.STILL if q.class_id == p.class_id else Verb.RECOLOR
            consumed.add(i)
            edges.append(WeaveEdge(prev=p, now=q, verb=verb, anchor=Anchor.SITE,
                                   delta=_delta_for(verb, p, q),
                                   signature=transition_signature(p, q)))
        else:
            unmatched_prev.append(p)

    # ---- PASS 2 · CLASS (value held, licensed transform) ----
    by_class: Dict[int, List[int]] = {}
    for i, q in enumerate(nows):
        by_class.setdefault(q.class_id, []).append(i)

    for p in unmatched_prev:
        pool = [i for i in by_class.get(p.class_id, []) if i not in consumed]
        cands = [(i, _classify_class_anchored(p, nows[i])) for i in pool]
        licensed = [(i, v) for i, v in cands if v is not None]
        if len(licensed) == 1:
            i, verb = licensed[0]
            q = nows[i]
            consumed.add(i)
            edges.append(WeaveEdge(prev=p, now=q, verb=verb, anchor=Anchor.CLASS,
                                   delta=_delta_for(verb, p, q),
                                   signature=transition_signature(p, q)))
        elif len(licensed) >= 2:
            edges.append(WeaveEdge(prev=p, now=None, verb=Verb.AMBIGUOUS,
                                   anchor=Anchor.NONE, delta=None))
        else:
            verb = Verb.DEFORM if pool else Verb.DEATH
            edges.append(WeaveEdge(prev=p, now=None, verb=verb,
                                   anchor=Anchor.NONE, delta=None))

    # ---- PASS 3 · residual now → BIRTH ----
    for i, q in enumerate(nows):
        if i not in consumed:
            edges.append(WeaveEdge(prev=None, now=q, verb=Verb.BIRTH,
                                   anchor=Anchor.NONE, delta=None))

    return edges

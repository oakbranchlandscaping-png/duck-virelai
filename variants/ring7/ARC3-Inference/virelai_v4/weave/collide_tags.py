"""WO-COLLIDE-EXTRACT-01 · THE TAG LAYER, LIFTED OUT OF THE DRIVE — VERBATIM.

**A MOVE, NOT A REFACTOR.** Every function below is byte-identical to the body it had in
`collide_drive.py` at `c61eb04`. No predicate, no threshold, no verdict and no ordering
changed; the extraction's whole correctness claim is that nothing did, and it is proved by
a byte-identity oracle over the drive's decisions and both renderers rather than by a
passing suite.

**WHY IT LEFT.** `collide_drive.py` stood at 378 executable lines doing at least four
jobs, and seven consecutive returns recommended this split while the file kept growing.
*Single responsibility: before adding code to a function — or a module — name what it
does; if the answer needs an "and", decompose first.*

**THE CHAIN THIS LAYER OWNS IS ONE-DIRECTIONAL: site → object → tag.** R1's record stays
keyed on `(site, action)` because that is what `reach` looks up by integer offset; this
layer is where *what refused me* becomes sayable at all. **A RECORD, NEVER A
GENERALISATION** — the key is the fingerprint, and there is no class term here to spell
the model with.

**THIS MODULE IS THE LOWER OF THE TWO, AND IT HOLDS `_region_at_last` AND THE THREE TYPE
ALIASES FOR THAT REASON.** `_region_at_last` is a two-line `Worldline` accessor used by
all four of the drive's responsibilities — the tag layer, the plan layer, the queue and
the aim — so wherever it lands, three callers import it. **It belongs one stratum down, in
`weave/worldline.py` beside `region_at`, and that file is outside this rung's fence.**
Recorded here rather than moved, so the next rung that opens `worldline.py` can take it.
Placing it in this module keeps a single producer and an acyclic import graph
(`collide_tags` ← `collide_plan` ← `collide_drive`, and `collide_tags` ← `collide_drive`);
duplicating it would have made two producers of one fact, which is how they drift.

Stdlib plus `capture.clay` only — the same import surface these functions already had.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple

from virelai_v4.capture.clay import master_object_list

# WO-NAV-CLEANUP-01 · THE MODULE DOCSTRING ABOVE ARGUES FOR ONE PRODUCER, AND THESE THREE
# LINES ARE A THIRD COPY. `Cell` and `Bearing` are already declared in `weave/reachable.py`
# and `weave/ego_read.py`; `Site` in `ego_read.py`. The argument made above about
# `_region_at_last` — *"duplicating it would have made two producers of one fact, which is
# how they drift"* — applies to these and was not applied to them.
#
# **STATED, NOT FIXED, AND THE REASON IS THE FENCE.** Collapsing them means choosing the
# one module they live in, and the only honest home is `weave/worldline.py` beside
# `region_at` — the same destination `_region_at_last` is already recorded as owing.
# `worldline.py` is outside this rung's fence, and `reachable.py` states its own
# duplication of `Transition` with a reason while this file stated none. **The two debts
# are one debt and should move together**, in the rung that opens `worldline.py`.
Cell = Tuple[int, int]
Bearing = Tuple[int, int]
Site = Tuple[int, int]              # a visual object's anchor — the drive's coverage key


def _region_at_last(worldline):
    return worldline.steps[-1][1]


def _present(cuts) -> Tuple[Any, ...]:
    """The master-list entries the LAST cut still holds — the objects on the board now.

    A window's master list spans everything ever seen, and a blocking tag is a claim about
    something that is THERE. An entry whose trail ends before the last node is an object
    that has gone; it can block nothing, and tagging it would be a belief about a
    fingerprint that no longer exists."""
    if not cuts:
        return ()
    last = cuts[-1].node_index
    return tuple(e for e in master_object_list(cuts).entries
                 if e.trail[-1].node_index == last)


def _holders(cuts) -> Dict[Cell, Any]:
    """`{cell: fingerprint}` over the objects presently on the board.

    A cut is a DISJOINT PARTITION — `provenance.cell_owners` raises otherwise — so one
    cell has at most one holder and a dict is exact rather than a choice. Built once per
    call so the tag walk is a lookup per cell instead of an intersection per object."""
    out: Dict[Cell, Any] = {}
    for entry in _present(cuts):
        for cell in entry.fingerprint[1]:
            out[cell] = entry.fingerprint
    return out


def _landing(cells, anchor: Cell, site: Site, bearing: Bearing) -> FrozenSet[Cell]:
    """Where this footprint would have come to rest: its shape, re-anchored at `site` and
    translated by `bearing`. Integer, exact, and no centroid anywhere in it."""
    dr = site[0] - anchor[0] + bearing[0]
    dc = site[1] - anchor[1] + bearing[1]
    return frozenset((r + dr, c + dc) for (r, c) in cells)


def blocking_tags(cuts, by_id, ego: int, bmap, refused) -> FrozenSet[Any]:
    """**THE TAG: the fingerprints of the objects standing where a refused press would
    have put the ego.**

    Director's ruling: *it must be the visual object that is listed as a blocker, not the
    site footprint. The site starts the chain, but the visual object gets the blocking
    tag.* The chain is one-directional — **site → object → tag** — and each layer keeps
    its own job. R1's record stays keyed on `(site, action)` because that is what `reach`
    can look up by integer offset at expansion, and this layer is where *what refused me*
    becomes sayable at all.

    **A RECORD, NEVER A GENERALISATION.** The key is the fingerprint. *This object blocks*
    is a fact; *objects of this class block* is the model five prior mines flagged and
    every generation before this one built — `blocked_classes` promoted a whole integer
    class on one observation and fed centroids. **One fingerprint's tag says nothing about
    another's**, and there is no class term in this function to say it with.

    **DERIVED EVERY FRAME, STORED ONLY SO A CHANGE IS NOTICEABLE.** No decay, no timer, no
    invalidation trigger, no world-state key. The tag dies when its fingerprint is not on
    the board — and a blocker that moves, recolours, grows or shrinks mints a NEW
    fingerprint, so the old tag simply is not derivable any more. That is what makes the
    reopening structural rather than experimental: a site-keyed record reopens only when
    the ego bumps the wall again and succeeds; an object-keyed tag reopens the moment the
    object stops being that object.

    THE EGO IS NOT ITS OWN BLOCKER. A refused landing usually overlaps ground the ego
    already holds, and tagging its own footprint would make every refusal reopen on the
    ego's next step. Compared on CELLS, which is what a footprint is.

    Returns an empty set when the premises are absent — no cuts, no ego in the window, no
    measured map. **Absence, not an assertion that nothing blocks.**"""
    e = by_id.get(ego)
    if not cuts or e is None or not refused:
        return frozenset()
    region = _region_at_last(e)
    holders = _holders(cuts)
    tags = set()
    for (site, action) in refused:
        for bearing in bmap.get(action, ()):
            for cell in _landing(region.cells, region.anchor, site, bearing):
                fingerprint = holders.get(cell)
                if fingerprint is not None and fingerprint[1] != region.cells:
                    tags.add(fingerprint)
    return frozenset(tags)


__all__ = ["Bearing", "Cell", "Site", "blocking_tags"]

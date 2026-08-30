"""WO-REACHABLE-01 · TOUCHING IS OCCUPATION, AND THE SEARCH IS THE LATTICE.

The ego strides. Its anchor plus any integer combination of its observed bearings is where
it can be, and **a target off that set cannot be reached by any sequence of presses.** The
drive did not know that: it chased a coordinate no combination produces, spent its whole
frame budget discovering it, and did so again for the next target and the next.

════════════════════════════════════════════════════════════════════════════════════════
THE LATTICE IS NOT COMPUTED — IT IS TRAVERSED.

`WO_LATTICE_MINE_00_RETURN` §4.1 established as an exhaustive negative that **no modulo is
applied to a coordinate anywhere in this repository** — and none is needed. `nav_bfs_
stride` expands `nr, nc = r + dr, c + dc` over the observed vectors themselves, so every
position it reaches is the start plus a sum of bearings: **the reachable set IS the search
space.** *Is the target reachable* is *does this search terminate on it*. A residue rule
would be a second, unfalsifiable statement of the same fact — and would be wrong the
moment the bearings are not axis-aligned.

**PORTED IN SHAPE from `library/nav_bfs.nav_bfs_stride`** — the frontier, the visited set,
the sorted expansion, the in-bounds guard, and the ordering of the arrival test. That
module is READ and never imported: it takes a numpy grid, a class-membership passability
oracle and a tolerance, none of which may cross into `weave/`.

════════════════════════════════════════════════════════════════════════════════════════
ARRIVAL IS OVERLAP, AND OVERLAP IS THE SAME EVENT `arrived` MEASURES FROM THE OTHER SIDE.

**Director's ruling: touching is occupation, not adjacency.** *Adjacent* is two footprints
side by side with no cell in common. **Touching is the ego's footprint covering cells the
target held** — and that is exactly what `provenance.OwnerEdge.exchanges` records after the
fact, as a transfer whose giver is the target. One event, two sides:

    before  ·  the ego's cells, TRANSLATED by a candidate offset, INTERSECT the target's
    after   ·  the exchange record shows the ego took cells whose giver was the target

**This deletes the tolerance.** `nav_bfs` accepts a landing within `max(1, stride // 2)` of
the target — two tuned numbers defended by a comment, *"agent footprint covers the rest"*,
**justifying them with a footprint the function never receives.** With overlap as the
predicate the footprint is not invoked, it is USED: the cell set is the test. No tolerance,
no divisor, no floor, and **no scalar stride at all** — `max(_strides)` existed only to
feed the tolerance, so the per-axis collapse `WO_LATTICE_MINE_00_RETURN` §2.1 flagged for
amendment does not arise here rather than being fixed here.

**And it explains legacy's `collide_sweep.collision_detected`.** That test asked exactly
this question — `bool(frozenset(ego_cells) & frozenset(target_cells))` — and asked it of
SPAWN-FROZEN cells, which is why `WO_COLLIDE_GOLDEN_01` found it structurally unaskable
against a disjoint partition. **The concept was right; the substrate was stale.**

════════════════════════════════════════════════════════════════════════════════════════
THE CLAIM IS COVERAGE-BOUNDED AND REOPENS, LIKE EVERY OTHER SEAL IN THIS BUILD.

With two observed bearings the reachable set is a line and most of the grid is off it.
That is not a fact about the world — it is a fact about what has been pressed. So the
verdict is **not reachable under the bearings observed so far**, a newly observed bearing
voids every prior refusal, and the search is re-run every frame rather than cached. The
`INERT` certificate, the marginal seals' denominators and `ego_parallax`'s coverage bound
are the same discipline; this is the fourth.

**THE BOUND IS PERMISSIVE, DELIBERATELY.** Only the translated ANCHOR is required to lie
on the grid — the footprint may hang off an edge — and no passability oracle constrains
the walk, so every cell is enterable. Both choices over-generate the reachable set. **That
is the safe direction for a refusal**: the search says *no* only when even a search that
believes the world is empty finds nothing, which makes an exhausted search a claim about
arithmetic rather than about the world. Distinguishing *blocked* needs a record of presses
that did not move the ego, and that record does not exist.

════════════════════════════════════════════════════════════════════════════════════════
THAT RECORD NOW EXISTS, AND THE WALK CONSULTS IT — WO-BLOCKED-RECORD-01.

**`refused` IS EVIDENCE, NOT A MAP.** It is a set of `(site, action)` pairs the ego was
observed to press without moving, rebuilt from the window's own edges every frame by
`ego_read._transitions`. There is no cache here and therefore no invalidation trigger: a
newly recorded success removes the pair at the source, and the next search simply does not
see it. **The lineage's `PassabilityMap.update_world_state` needs a world-state identifier
because it persists; this needs none because it does not** — the plan is re-derived from
the evidence every frame, which is what this module already did for the bearings.

**THE GATE IS AT EXPANSION, AND THAT IS THE PORT.** `WO_BLOCKED_MINE_00_RETURN` §Q3 named
the ordering as its one ordering finding: v3 refused the edge inside the search; v3.5
popped known-blocked actions off the head of a path the planner had already produced, and
the replay is what wall-crawling by post-hoc filtering looks like. The refusal is tested
where the neighbour is generated, so a refused transition is never enqueued, never walked
through, and never the head of a returned path.

**ARRIVAL STILL COMES FIRST, AND HERE IT IS LOAD-BEARING RATHER THAN CONVENTIONAL.** The
ported ordering exists so *a goal cell that is itself a wall still ends the search*, and
under this build's ontology that case is not an edge case — **it is contact with an
immovable object.** An object that cannot be pushed registers no transfer; what it
registers is a press that did not move the ego. If the refusal were tested before arrival,
the first contact with such an object would delete it from the plan forever and the drive
could never touch it again. So the refusal prunes TRANSIT and never ARRIVAL: the search
will still walk into what it has been refused by, and will not walk THROUGH it.

**A REFUSAL IS A ∀ AND IT DIES TO ONE COUNTEREXAMPLE.** `passable` wins at construction in
`ego_read`, so the pruning here can only ever be as provisional as the record. The claim
this function returns is unchanged in kind: *not reachable under the bearings observed so
far, avoiding the transitions refused so far.* Both halves reopen on evidence.

Pure and stdlib-only. Computes nothing about any role, writes no belief, and decides
nothing about any tag. **No constant, no tolerance, no threshold, no modulo, no direction
table, no class literal, no float.**
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, FrozenSet, Iterable, Optional, Tuple

Cell = Tuple[int, int]
Bearing = Tuple[int, int]
Offset = Tuple[int, int]
# Structurally identical to `ego_read.Transition`, and NOT imported from it. This module
# takes stdlib types and returns stdlib types; importing the producer to name a tuple
# would couple the search to the record's module for no behaviour at all.
Transition = Tuple[Cell, Any]


def overlaps(cells: Iterable[Cell], offset: Offset, target_cells) -> bool:
    """Does this cell set, translated by `offset`, cover any cell the target holds?

    **THE WHOLE ARRIVAL PREDICATE, AND IT IS EXACT.** Integer cells, integer offset, set
    membership — no distance, no tolerance, no rounding, and nothing that could be tuned.
    An empty cell set on either side covers nothing, which is absence rendered as absence
    rather than a special case."""
    dr, dc = offset
    return any((r + dr, c + dc) in target_cells for (r, c) in cells)


def within(cells: Iterable[Cell], offset: Offset, grid_shape) -> bool:
    """Does this cell set, translated by `offset`, lie WHOLLY on the grid?

    **THE BODY, WHERE THE BOUNDS TEST ASKED ABOUT A POINT — WO-PAIR-AND-BODY-01.** Nine
    lines below, `overlaps` tests the whole footprint for arrival; the bounds test tested
    the translated ANCHOR, so a plan could land the ego's body off the edge of the board
    and the search would not notice. `WO_LATTICE_MINE_00_RETURN` found `nav_bfs`'s
    tolerance defended by *"agent footprint covers the rest"* in a function with no
    footprint parameter, and `WO_PLANNER_MINE_00_RETURN` Q3 found the only function in the
    whole lineage that actually had one was never imported by anything.

    **Integer cells, integer offset, membership. No tolerance, no radius, no inflation, no
    constant** — the grid's extent comes from `NodeCut.grid_shape` and the footprint from
    `RegionClay.cells`, both already in hand. **This is the cheapest and least-assuming
    member of the footprint-aware family**, and deliberately the only one taken: every
    external technique the mine examined — obstacle inflation, swept-volume checking —
    assumes a KNOWN STATIC map and carries at least one tuned parameter.

    **AND IT IS NOT THE SWEPT REGION.** CE ruled the destination footprint; the region
    traversed BETWEEN two lattice points is not tested and is not well-defined on this
    substrate — with a stride wider than the body, there is no contiguous corridor to
    sweep. **Recorded as absent rather than approximated.**

    An empty cell set lies wholly on any grid: `all(...)` over nothing is `True`, which is
    absence rendered as absence — `reach` has already refused an empty footprint above."""
    rows, cols = grid_shape
    dr, dc = offset
    return all(0 <= r + dr < rows and 0 <= c + dc < cols for (r, c) in cells)


def _expansions(bmap: Dict[Any, FrozenSet[Bearing]]) -> Tuple[Tuple[Any, Bearing], ...]:
    """Every `(action, bearing)` the record offers, in a deterministic order.

    Actions ascending by `str`, and each action's OBSERVED bearings ascending — the same
    two orderings `bearing_map`'s consumers already use. **An action seen to produce more
    than one bearing contributes each of them**, because the ∃ the map became
    (`WO_EGO_OBSERVED_01`) is a claim that the button has gone each of those ways, and a
    search that used only one would be re-imposing the ∀ that rung removed.

    No tally is consulted and none exists: `ActionObserved.bearings` is a set."""
    return tuple((a, b) for a in sorted(bmap, key=str) for b in sorted(bmap[a]))


def reach(ego_cells, ego_anchor: Cell, target_cells, bmap, grid_shape,
          refused: FrozenSet[Transition] = frozenset()) -> Optional[Tuple[Any, ...]]:
    """The `(action, bearing)` sequence that puts the ego's footprint onto the target, or
    `None` when the search exhausts.

    **WO-NAV-CLEANUP-01 · this line said "the action sequence".** `WO-PAIR-AND-BODY-01`
    made each element the PAIR the expansion used, precisely so the vector the note prints
    is the vector the search computed the offset with, and `_next_press` unpacks both. The
    annotation `Optional[Tuple[Any, ...]]` says neither, and is left alone rather than
    narrowed to a type this module would then have to import a name for.

    `()` — the empty sequence — is **already touching**, and is distinct from `None`. The
    caller must test for `None` rather than for falsity; `WO_LATTICE_MINE_00_RETURN` §7
    found `cycle_probe.py:723` conflating exactly these two with `if path is None or
    len(path) == 0`, and both routed to one verdict.

    `None` is the rung's own verdict and it means: **no integer combination of the
    bearings observed so far, avoiding the transitions refused so far, puts this footprint
    on this target within the grid.** It is still not a claim that the world is closed —
    see this module's header on why the bound stays permissive everywhere else.

    `refused` DEFAULTS TO EMPTY, and an empty set restores the function exactly: no pair
    is ever in it, the `continue` never fires, and every existing caller and every prior
    assertion holds unchanged. **Absence of a record is absence, not an assumption that
    everything is passable** — the two coincide in behaviour here only because
    *everything is touchable until proven otherwise* is what this search already believed."""
    if not ego_cells or not target_cells:
        return None
    if overlaps(ego_cells, (0, 0), target_cells):
        return ()
    steps = _expansions(bmap)
    if not steps:
        return None
    seen = {(0, 0)}
    queue: deque = deque([((0, 0), ())])
    while queue:
        (dr, dc), path = queue.popleft()
        site = (ego_anchor[0] + dr, ego_anchor[1] + dc)   # where the press would be MADE
        for action, (br, bc) in steps:
            nxt = (dr + br, dc + bc)
            if nxt in seen:
                continue
            # THE BODY, NOT THE POINT — WO-PAIR-AND-BODY-01. The line here read
            # `0 <= ego_anchor[0] + nxt[0] < rows and 0 <= ego_anchor[1] + nxt[1] < cols`,
            # which admitted any landing whose ANCHOR was on the board however far the
            # footprint hung off it. `overlaps` nine lines below has always used the whole
            # cell set; this now asks the same question of the same set.
            if not within(ego_cells, nxt, grid_shape):
                continue
            # ARRIVAL BEFORE ANY OTHER TEST — the ported ordering. `nav_bfs_stride` checks
            # arrival before passability so a goal cell that is itself a wall still ends
            # the search, and here that case is CONTACT WITH AN IMMOVABLE OBJECT, which
            # this campaign exists to make happen. The ordering also preserves that a
            # position is judged the moment it is generated rather than when it is popped,
            # so the returned path is shortest in presses.
            if overlaps(ego_cells, nxt, target_cells):
                return path + ((action, (br, bc)),)
            # …AND PASSABILITY SECOND, AT EXPANSION. A refused transition is not enqueued,
            # so nothing is ever planned THROUGH it. `nxt` is deliberately NOT added to
            # `seen`: the refusal is a fact about this EDGE, and the same position stays
            # reachable by another action or from another site.
            if (site, action) in refused:
                continue
            seen.add(nxt)
            queue.append((nxt, path + ((action, (br, bc)),)))
    return None


__all__ = ["overlaps", "reach", "within"]

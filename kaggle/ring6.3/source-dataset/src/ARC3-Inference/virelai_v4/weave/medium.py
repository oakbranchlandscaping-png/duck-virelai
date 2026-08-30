"""WO-MEDIUM-01 · THE MEDIUM — the ground a mover moves through, and the weave already
names it.

THE RULE, in the Director's words:

    The background is the large amorphous area that just deforms on every move. It is
    required by logical necessity — it must exist if an embodied ego exists. Its home is
    under the passively-reactive archetype, as a SUB-CLASS.

**THE MENU STAYS CLOSED AT SIX.** This module emits no seventh Band-2 value. It refines
`REACTIVE-DRIVEN` — the passively-reactive archetype — by naming *which mover* a worldline
is the medium for and *what its own stream did* while being crossed.

════════════════════════════════════════════════════════════════════════════════════════
TWO FACTS, EACH DOING ONE JOB, AND NEITHER IS A THRESHOLD:

    1. THE ENTAILMENT — it is the crossing partner of a worldline whose own footprint
       occupied more than one anchor across the window. **A mover moves THROUGH
       something.** Under No-null-class every cell has an owner, so the cells a translating
       worldline vacates and the cells it occupies belong to someone; `crossings()` already
       names that someone, on both sides, and `displacement()` already says which of the
       two translated. Nothing is re-derived here.

    2. THE VERB — on at least one edge of that crossing, its OWN stream licensed nothing.
       `edge.py`: `DEFORM = "same-class partner exists but no single licensed verb"`. The
       cascade tried an exact footprint, a translation, a subset and a superset, and none
       fit. **A footprint whose extent holds while its interior churns is exactly that**,
       and the verb has printed on the roster all along.

**NEITHER READS SIZE, POSITION OR CLASS.** No proportion, no ratio, no tolerance, and a
test in this module's suite forbids one from appearing.

════════════════════════════════════════════════════════════════════════════════════════
WHY THE VERB CONJUNCT IS EXISTENTIAL, AND WHY A ∀ WOULD BE WRONG.

**The background grows and shrinks.** A field losing cells to a growing figure, or gaining
a row of its own, emits `GROW` or `SHRINK` on those edges — a licensed verb. Requiring
*every* edge of the crossing to be unlicensed is a PURITY requirement, and softening it to
*most* edges is a proportion, which is a threshold. **So one witness earns it and no later
licensed edge unearns it** — the same existential shape `LEVER` carries, for the same
reason: the claim is ∃, and a rate is the wrong instrument for an ∃-claim.

**The entailment carries what a proportion would have had to.** A worldline that licenses
nothing on one edge but is nobody's medium types nothing here; the discrimination is done
by conjunct 1, not by counting conjunct 2.

WHAT WAS DELIBERATELY NOT REACHED FOR, recorded because both were proposed and both are
size priors:

  * legacy's `area_before == area_after` fence — **a background that grows fails an exact
    conservation test exactly as a mover does.**
  * `coupling._form_stability` — `|A∩B| / |A∪B|` is dominated by extent: a large field
    gaining a few cells scores high while a small object gaining the same few scores low.
    Its own docstring says it abstains on figure/ground, and it does.

Pure and stdlib-only. Reads the crossing account and the worldlines it is handed; computes
nothing else, writes nothing, and decides nothing about any other tag.
"""

from __future__ import annotations

from typing import Any, Dict, NamedTuple, Optional, Sequence, Tuple

from virelai_v4.weave.edge import Verb


class MediumWitness(NamedTuple):
    """One mover this worldline was measured to be the medium for.

    `crossing_edges` and `unlicensed` are COVERAGE and travel with the claim; they are
    never compared to each other and never converted into a rate. `node` and `action`
    locate the witnessing edge so the claim can be checked at the frame that earned it."""
    mover: int
    node: int
    action: Any
    crossing_edges: int
    unlicensed: int


def verb_at(worldline, node: int) -> Optional[Verb]:
    """The verb of the edge that PRODUCED `node`, or `None` if this worldline had no
    transition into it.

    `Worldline.edges[i]` spans `steps[i][0] → steps[i+1][0]` and `len(edges) == len(steps)
    - 1` — worldline.py's own invariant, read rather than assumed. `None` is an honest
    absence: a worldline may be present in a window without spanning every node of it."""
    steps, edges = worldline.steps, worldline.edges
    for i in range(min(len(edges), len(steps) - 1)):
        if steps[i + 1][0] == node:
            return edges[i].verb
    return None


def _witness_for(worldline, crossing) -> Optional[Tuple[int, Any, int]]:
    """The first edge of `crossing` on which this worldline's own stream licensed nothing,
    with the coverage the search ran over. `None` when every accounted edge carried a
    licensed verb."""
    first: Optional[Tuple[int, Any]] = None
    unlicensed = 0
    for e in crossing.per_edge:
        if verb_at(worldline, e.node) is Verb.DEFORM:
            unlicensed += 1
            if first is None:
                first = (e.node, e.action)
    if first is None:
        return None
    return (first[0], first[1], unlicensed)


def medium_witnesses(worldlines, field) -> Dict[int, Tuple[MediumWitness, ...]]:
    """`{worldline_id: (MediumWitness, …)}` — every mover this worldline is the medium for.

    `field` is `ego_field.FieldRead`: its `crossings` account and its `displaced` map are
    both consumed as computed, so the account is read once per `infer_roles` call and the
    displacement fact is not re-derived. Multi-medium is the default, exactly as multi-ego
    is: a field crossed by two movers witnesses both, with no election and no tie-break."""
    by_id = {w.id: w for w in worldlines}
    out: Dict[int, Tuple[MediumWitness, ...]] = {}
    for wid, crossing_list in sorted(field.crossings.items()):
        wl = by_id.get(wid)
        if wl is None:
            continue
        found = []
        for c in crossing_list:
            if not field.displaced.get(c.partner):
                continue                    # nobody translated through it on this crossing
            hit = _witness_for(wl, c)
            if hit is None:
                continue                    # its own stream licensed a verb on every edge
            node, action, unlicensed = hit
            found.append(MediumWitness(mover=c.partner, node=node, action=action,
                                       crossing_edges=len(c.per_edge),
                                       unlicensed=unlicensed))
        if found:
            out[wid] = tuple(found)
    return out


def medium_seal(ws: Optional[Sequence[MediumWitness]]) -> bool:
    """Both conjuncts, over any one mover. No threshold, no fraction, no tolerance — the
    witnesses only exist where both already held."""
    return bool(ws)


def medium_basis(ws: Sequence[MediumWitness]) -> str:
    """The verdict's evidence sentence — which movers, and what its own stream did."""
    movers = " · ".join(
        f"###{w.mover:03d} (licensed nothing of its own on {w.unlicensed} of "
        f"{w.crossing_edges} exchanged edges, first at node {w.node} under {w.action})"
        for w in ws)
    return (f"the medium {'these movers move' if len(ws) > 1 else 'a mover moves'} through: "
            f"{movers} → REACTIVE-DRIVEN (medium) — it is the ground of a worldline that "
            f"translated, and its own footprint could license no verb where it was crossed")


def medium_parallax(ws: Sequence[MediumWitness]) -> str:
    """What the claim does not establish."""
    return (f"coverage: {len(ws)} mover{'' if len(ws) == 1 else 's'} witnessed. **A "
            f"SUB-CLASS OF REACTIVE-DRIVEN, not a seventh role** — the Band-2 menu is "
            f"unchanged. The claim is EXISTENTIAL: a later edge on which it licensed GROW "
            f"or SHRINK does not unearn it, because a background grows and shrinks. No "
            f"size, position or class decided it — only that a partner translated and that "
            f"the cascade could license nothing here")

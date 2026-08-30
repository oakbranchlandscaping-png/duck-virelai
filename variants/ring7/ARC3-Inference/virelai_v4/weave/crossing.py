"""WO-EGO-02 · THE CROSSING — who exchanged ground with whom, under which button.

**ACCUMULATION AND ORIENTATION ONLY. THIS MODULE DECIDES NOTHING.** It answers one
question over a window — *which pairs of worldlines handed cells to each other cleanly,
and what did each take under each button* — and hands the account up. The role read that
consumes it lives in `ego_field.py`; the separation is deliberate, because the account is
a fact about the frame and the verdict is a claim about a worldline.

════════════════════════════════════════════════════════════════════════════════════════
NOTHING HERE IS NEW EVIDENCE. Every fact this module reads was already computed, by golden
code written to the golden run's own laws:

  `provenance.owner_edge`         every cell whose owner changed across an adjacent pair,
                                  as `(cell, giver, receiver)`, plus `continuing` — the
                                  worldlines present at BOTH nodes.
  `provenance.complement_verdict` splits that churn into EXCHANGE (both endpoints
                                  continuing) and INTRINSIC (loud), and names
                                  `partners: {worldline → cells exchanged}`.

**A figure crossing a ground is exactly a two-party exchange with `intrinsic == ∅`**,
repeated. `complement_verdict` has computed that per edge all along and its only
production consumer was a renderer; `rejoin.py` names the same phenomenon in its first
line — *"thread the swept ground without fusing the figures"* — and spends it on avoiding
a mistake. **The belief path had no reader. This is the first.**

ORIENTATION IS DERIVED, NOT ADDED. `OwnerEdge.exchanges` is already public and already
carries `(cell, giver, receiver)`, so `giver == wid` is a loss and `receiver == wid` a
gain. **`provenance.py` is READ and never modified.**

THE ACCOUNT IS SYMMETRIC AND SAYS SO. A complement verdict is a *complement* verdict: the
same relation read from either end. Both endpoints of one crossing appear here, each
naming the other. **Nothing in this module distinguishes a figure from the ground it
crosses, and nothing in this module should** — that asymmetry is one stratum up and is
`ego_field.py`'s to carry.

Pure and stdlib-only. Reads the provenance edges and the action series it is handed;
computes nothing else, writes nothing, and decides nothing about any tag.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, NamedTuple, Optional, Sequence, Tuple

from virelai_v4.weave.provenance import complement_verdict, owner_edge

Cell = Tuple[int, int]


class EdgeExchange(NamedTuple):
    """ONE accounted edge between this worldline and ONE partner, in BOTH directions.

    `node` is the node the edge PRODUCED and `action` is the button attributed to that
    node — the wiring law, carried rather than re-derived. `gained` and `given` are the
    cells that changed hands each way across that single edge.

    **BOTH DIRECTIONS OR NEITHER.** An edge on which this worldline only gave is an edge of
    the account exactly as much as one on which it only took. The fold that stood here
    skipped an edge whose `gained` was empty, and that skip discarded every DEPARTURE —
    the cells a crosser released and the partner that received them. Legacy reaches for
    that same fact at grid grain and has to be told where the ego was first
    (`ignore_score.accumulate_background_class_votes`); here it is already at worldline
    grain, named on both sides, and it was being thrown away at a union.

    An empty side is an empty frozenset because the direction was accounted and carried
    nothing — NOT because it was unobserved. An edge that could not be accounted, or on
    which nothing changed hands either way, has no record at all."""
    node: int
    action: Any
    gained: FrozenSet[Cell]
    given: FrozenSet[Cell]


class Crossing(NamedTuple):
    """One partner this worldline repeatedly exchanged ground with — the per-edge record,
    and the pooled view derived from it.

    `per_edge` is the record: every accounted edge with this partner, in node order, both
    directions. **Per-edge identity is preserved there and nowhere else** — the pooled view
    below unions across edges, so an offset measured at the moment of one exchange is
    unrecoverable from it.

    `gained_by_action` and `edges` are DERIVED from `per_edge` and hold exactly the values
    they held before this record existed: `gained_by_action` holds ONLY actions actually
    observed to have gained something — an action never pressed has no entry, and neither
    does one that only ever gave — and `edges` counts the edges on which this worldline
    GAINED from this partner. `edges` is the coverage the claim rests on and travels with
    it; it is never converted into a score."""
    partner: int
    edges: int
    gained_by_action: Dict[Any, FrozenSet[Cell]]
    per_edge: Tuple[EdgeExchange, ...]


def action_at(node_actions: Sequence[Any], node_index: int) -> Optional[Any]:
    """The action that PRODUCED `node_index` — the wiring law, read at the right node.

    Out of range is `None` rather than an error: a window may legitimately end before the
    action series does."""
    if not (0 <= node_index < len(node_actions)):
        return None
    aid, _target = node_actions[node_index]
    return aid


def _accumulate(acc, edge, aid, by_id) -> None:
    """Fold one accounted edge into the running record. Extracted so `crossings` states
    the walk and this states the fold — one responsibility each.

    Records BOTH directions per partner. A partner with which nothing changed hands either
    way contributes no record; `complement_verdict.partners` already names a partner it
    only gave to, so the outer loop reached those edges all along — only the fold dropped
    them."""
    for wid in by_id:
        try:
            verdict = complement_verdict(by_id[wid], edge)
        except Exception:
            continue
        if verdict.intrinsic_cells or not verdict.partners:
            continue                                   # not a clean crossing on this edge
        for partner in verdict.partners:
            gained = frozenset(cell for (cell, giver, receiver) in edge.exchanges
                               if receiver == wid and giver == partner)
            given = frozenset(cell for (cell, giver, receiver) in edge.exchanges
                              if giver == wid and receiver == partner)
            if not (gained or given):
                continue                               # nothing changed hands either way
            acc.setdefault(wid, {}).setdefault(partner, []).append(
                EdgeExchange(node=edge.now_node, action=aid,
                             gained=gained, given=given))


def _pooled_gains(per_edge) -> Dict[Any, FrozenSet[Cell]]:
    """`gained_by_action`, DERIVED from the per-edge record rather than accumulated beside
    it. An edge that gained nothing contributes no entry — absence stays absence, and an
    action seen only on a give-only edge does not acquire an empty set."""
    out: Dict[Any, set] = {}
    for e in per_edge:
        if not e.gained:
            continue
        out.setdefault(e.action, set()).update(e.gained)
    return {a: frozenset(c) for a, c in sorted(out.items(), key=lambda kv: str(kv[0]))}


def _gain_edges(per_edge) -> int:
    """The coverage `edges` has always reported: the edges on which this worldline GAINED
    from this partner. Derived, so the count cannot drift from the record it summarises."""
    return sum(1 for e in per_edge if e.gained)


def crossings(worldlines, cuts, node_actions) -> Dict[int, Tuple[Crossing, ...]]:
    """`{worldline_id: (Crossing, …)}` — every clean exchange partnership in the window.

    An edge contributes only when the worldline's churn across it is ENTIRELY owner-owner
    exchange (`intrinsic_cells == ∅`). Intrinsic churn means something appeared or vanished
    rather than changing hands, and a crossing is precisely the case where nothing did.

    The population is every adjacent cut pair, in node order. `cell_owners` enforces
    disjointness, so a cell has exactly one giver and one receiver and the account cannot
    double-book."""
    ordered = sorted(cuts, key=lambda c: c.node_index)
    by_id = {w.id: w for w in worldlines}
    acc: Dict[int, Dict[int, list]] = {}

    for t in range(len(ordered) - 1):
        # NON-FATAL BY CONSTRUCTION. `cell_owners` RAISES when a cut is not a disjoint
        # partition — a real invariant on real ledger cuts, and one `provenance.py` says
        # synthetic cuts may legitimately break. **A role read must never be taken down by
        # an accounting invariant it only consults**, so an edge that cannot be accounted
        # contributes NO crossing rather than an exception. Absence is absence; nothing is
        # inferred for that edge, and the coverage the seal rests on shrinks honestly.
        try:
            edge = owner_edge(ordered[t], ordered[t + 1], worldlines)
        except Exception:
            continue
        aid = action_at(node_actions, ordered[t + 1].node_index)
        if aid is None:
            continue                                   # no button to attribute it to
        _accumulate(acc, edge, aid, by_id)

    out: Dict[int, Tuple[Crossing, ...]] = {}
    for wid, partners in acc.items():
        out[wid] = tuple(
            Crossing(partner=p,
                     edges=_gain_edges(per_edge),
                     gained_by_action=_pooled_gains(per_edge),
                     per_edge=tuple(per_edge))
            for p, per_edge in sorted(partners.items()))
    return out

"""WO-ACTED-ON-NAV-02 · the cell the ego arrived at.

A click names a cell and `action_roster.acted_on` resolves it to the ### that owned it.
A directional press names none, so `acted_on` returns `NON_TARGETED` and every downstream
seal loses its subject. This module supplies the missing cell and calls the SAME resolver:
**a cell the ego GAINED across the edge the press produced**, which at `cut[t-1]` was owned
by whoever gave it. `acted_on` then names that giver. Nothing here resolves anything itself.

WHY A GAIN, AND NOT A DESTINATION. A destination must be computed from a bearing, and a
bearing can be completed, assumed or tabled. A gain is recorded: `provenance.owner_edge`
already holds `(cell, giver, receiver)` for every cell whose owner changed. The attributor
reads the record and chooses among what is already there.

THE EGO IS SEAL-DERIVED, AND IT MUST BE (RULING · R-2). The `EGO` verdict cannot precede
this attribution -- `verdicts` -> `_ladder` -> `lever_witnesses` -> `acted_press` -> `verdicts`
is a cycle -- and `WO_COUNTER_MINE_00_RETURN` §4 rules do-not-port on any exclusion built
from a verdict it feeds. Both seals are used, never one: `ego_seal` needs a MOVE verb;
`ego_field_seal` reads the exchange record and reaches crossers the first cannot. The
excess over the verdict set is *worldlines an earlier branch would have taken*, and it is
recorded here rather than discovered later.

THE MEDIUM IS A PRECEDENCE, NOT AN EXCLUSION (RULING · R-3, ported from
`physics_accumulator._resolve_subject`'s `prefer_figure`). The ego takes ground from the
medium on every step, so subtracting the medium would discard the one giver always present
and leave nothing to record on a genuinely uneventful press. Instead the medium LOSES: if
any non-medium worldline gave, it is the subject; the medium is the subject only when
nothing else gave. Recorded either way, never silently dropped.

NO SNAPPING, AND NO PLURALITY. `action_roster` refuses to snap an unowned click to a nearest
###; a press whose non-medium gains name more than one giver would be that snap taken by
majority, so it resolves to none and says AMBIGUOUS. No threshold, no proportion, no
proximity, no size, no class literal and no direction table appears in this module -- the
press is selected by the absence of a target cell and the presence of a recorded gain, never
by an action id.

Read-only over the weave. Writes no belief. Stdlib only.
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, NamedTuple, Optional, Sequence, Tuple

from virelai_v4.weave.action_roster import (OUT_OF_WINDOW, RESOLVED, acted_on,
                                            is_boundary_pre)
from virelai_v4.weave.ego_field import ego_field_seal
from virelai_v4.weave.ego_read import ego_seal
from virelai_v4.weave.medium import medium_witnesses
from virelai_v4.weave.provenance import owner_edge

Cell = Tuple[int, int]

AMBIGUOUS = "AMBIGUOUS"        # non-medium gains name more than one giver; resolves to none
NO_EGO = "NO_EGO"              # no worldline satisfies either seal in this window
NO_GAIN = "NO_GAIN"            # the press produced no owner change into the ego
BOUNDARY = "BOUNDARY"          # the pre-action node is a life boundary
UNACCOUNTED = "UNACCOUNTED"    # the cut is not disjoint; consulted, never fatal


class NavTarget(NamedTuple):
    """One directional press's attribution attempt, and why it landed where it did."""
    node: int
    cell: Optional[Cell]
    worldline_id: Optional[int]
    status: str
    givers: Tuple[int, ...]        # every non-ego giver on the edge, medium included
    medium_givers: Tuple[int, ...]  # those of them the medium pass witnessed


def _abstain(node: int, status: str) -> NavTarget:
    """An attempt that took no step. Named rather than dropped, per status."""
    return NavTarget(node, None, None, status, (), ())


def sealed_egos(worldlines, ego_of, field) -> FrozenSet[int]:
    """Every worldline satisfying EITHER seal (R-2). Not the verdict, which cannot exist
    here, and deliberately the wider set -- its excess is named in this module's header."""
    return frozenset(
        w.id for w in worldlines
        if (w.id in ego_of and ego_seal(ego_of[w.id])) or ego_field_seal(field, w.id)
    )


def _gains(edge, egos: FrozenSet[int]) -> Dict[int, Tuple[Cell, ...]]:
    """`{giver: cells}` for every cell an ego GAINED from a non-ego across this edge.
    An ego is never its own subject, and one ego taking from another attributes to none."""
    out: Dict[int, list] = {}
    for (cell, giver, receiver) in edge.exchanges:
        if receiver in egos and giver not in egos:
            out.setdefault(giver, []).append((int(cell[0]), int(cell[1])))
    return {g: tuple(sorted(c)) for g, c in out.items()}


def _elect(gains: Dict[int, Tuple[Cell, ...]], media: FrozenSet[int]):
    """R-3's precedence. Non-medium givers first; the medium only when nothing else gave.
    Exactly one candidate resolves; more than one is AMBIGUOUS and resolves to none."""
    non_medium = {g: c for g, c in gains.items() if g not in media}
    candidates = non_medium or gains
    if len(candidates) != 1:
        return None, None
    giver = next(iter(candidates))
    return giver, candidates[giver][0]


def nav_target(left: int, right: int, cut_by_idx, worldlines,
               aid: Any, egos: FrozenSet[int], media: FrozenSet[int]) -> NavTarget:
    """One press. Abstains loudly at every step it cannot take."""
    if is_boundary_pre(cut_by_idx, right):
        return _abstain(right, BOUNDARY)
    if not egos:
        return _abstain(right, NO_EGO)
    try:
        cut_l, cut_r = cut_by_idx[left], cut_by_idx[right]
    except (KeyError, TypeError):
        # The window may legitimately not contain the pre-action node. `acted_on` calls
        # that OUT_OF_WINDOW and surfaces it; reaching for the cut before asking would
        # turn a wiring fact into a crash.
        return _abstain(right, OUT_OF_WINDOW)
    try:
        edge = owner_edge(cut_l, cut_r, worldlines)
    except AssertionError:
        return _abstain(right, UNACCOUNTED)
    gains = _gains(edge, egos)
    seen = tuple(sorted(gains))
    med = tuple(sorted(g for g in gains if g in media))
    if not gains:
        return _abstain(right, NO_GAIN)
    giver, cell = _elect(gains, media)
    if giver is None:
        return NavTarget(right, None, None, AMBIGUOUS, seen, med)
    res = acted_on(right, aid, cell, cut_by_idx, worldlines)
    wid = res.worldline_id if res.status == RESOLVED else None
    return NavTarget(right, cell, wid, res.status, seen, med)


def nav_targets(cuts, node_actions, worldlines, ego_of, field) -> Dict[int, NavTarget]:
    """`{left_node: NavTarget}` for every CELL-LESS press, keyed exactly as
    `role_read._acted_by_press` keys its own walk. A press carrying a target cell is the
    click lane and is not touched here."""
    egos = sealed_egos(worldlines, ego_of, field)
    media = frozenset(medium_witnesses(worldlines, field))
    ordered = sorted(cuts, key=lambda c: c.node_index)
    nodes = [c.node_index for c in ordered]
    cbi = {c.node_index: c for c in cuts}
    out: Dict[int, NavTarget] = {}
    for left, right in zip(nodes, nodes[1:]):
        aid, target = node_actions[right] if 0 <= right < len(node_actions) else (None, None)
        if aid is None or target is not None:
            continue
        out[left] = nav_target(left, right, cbi, worldlines, aid, egos, media)
    return out


def with_directional(acted_press: Dict[int, Any], cuts, node_actions,
                     worldlines, ego_of, field) -> Dict[int, Any]:
    """`acted_press` with directional attributions filled in where it holds `None`.

    ADDITIVE BY CONSTRUCTION: a press the click lane already resolved is never overwritten,
    and a press carrying a target cell is never visited. On a world whose every press
    carries a coordinate this returns an equal mapping."""
    found = nav_targets(cuts, node_actions, worldlines, ego_of, field)
    return {k: (v if v is not None else
                (found[k].worldline_id if k in found else None))
            for k, v in acted_press.items()}

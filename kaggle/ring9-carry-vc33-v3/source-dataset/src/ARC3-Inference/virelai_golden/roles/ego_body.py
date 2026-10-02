"""ROLES · ego (BODY) — the worldline that moves as the direct result of an action button.

Canon: 02 §6.3 EGO (action-covariance, per-action, stable mapping; first, absolutely); 04 R3
v1.1 / R-F (BODY kind; determined at the worldline, never by footprint; a SET); R-A (the ego
observable is a per-action covariance over the channel that can see the action); R-K (the seal
is binary; coverage is parallax, never strength); R-L (lockstep worldlines are one composite
ego; congruence not required; unison from the anchor walk).

Transcription origin (R-C): virelai_v4/weave/ego_read.py @ oracle-v4 (471 lines, read whole)
— `EgoMap` and its five fields, `_observe`, `_transitions`, `action_bearings`, `ego_seal`,
`channel_a_witness`, `ego_witness`; virelai_v4/weave/action_roster.py:86-140
`life_boundary_edges`. What it proved: `EGO` on the two body parts of ls20 in both golden logs
of 2026-09-05, no threshold anywhere.

NOT carried: the `PROVISIONAL` rendering (R-K); `heart_boundary_edges` (needs a sealed COUNTER —
Rung 2); `ego_basis` / `ego_parallax` prose (re-written under R-K, labeled).
NEW (labeled, R-L): `lockstep`, `composite_egos`, `EgoVerdict`.

RETIRED at G3-01 under R-M (labeled): v4's second observer, the FIELD READ (ego_field.py —
a clean exchange with a stationary partner, different cells gained under different buttons),
transcribed at G1-01 as an alternative seal route. It read the ego off the ground; R-M reads
the ground off the ego ("the necessary inverse"), and the ground is fragments until then —
as an ego observer it became circular, and on the un-folded weave it measured nothing. The
seal is the bearing read alone: the worldline's OWN MOVE edges keyed on the action that
produced the edge's right node; ∃ one witnessed press, refused by the channel law when ≥ 2
actions observed produce ONE bearing (THAT-ANY action: a schedule). The per-button exchange
table now renders as GROUND's parallax (`roles/ground.py`), where its evidence lives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Set, Tuple

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.verbs import Verb
from virelai_golden.weave.worldline import Worldline

Bearing = Tuple[int, int]
Transition = Tuple[Cell, int]  # (the anchor pressed FROM, the action pressed)
HELD = frozenset({Verb.STILL, Verb.RECOLOR})  # the frame proving non-motion: the same cells


class ActionBearing(NamedTuple):
    action: int
    bearing: Bearing
    presses: int  # coverage, part of the claim, never a score


class ActionObserved(NamedTuple):
    """Every DISTINCT bearing one action produced — a set, so 'how often' is unavailable and
    no majority rule can be written against it."""

    action: int
    bearings: FrozenSet[Bearing]


class Transitions(NamedTuple):
    """`passable` is ∃ and permanent; `refused` is ∀, provisional, and unconstructible for a
    (site, action) that ever passed. Neither is the third state: never pressed."""

    passable: FrozenSet[Transition]
    refused: FrozenSet[Transition]


class EgoMap(NamedTuple):
    bearings: Tuple[ActionBearing, ...]       # actions whose every press agreed (∀), ascending
    still: Tuple[int, ...]                    # actions observed to produce no translation
    inconsistent: Tuple[int, ...]             # actions that produced more than one bearing
    observed: Tuple[ActionObserved, ...]      # every action that ever moved it, every bearing (∃)
    transitions: Transitions


def life_boundaries(record: Record) -> FrozenSet[int]:
    """The RIGHT node of every edge crossing a life boundary: a death's displacement is not
    evidence about a button (origin: action_roster.life_boundary_edges — full_reset on the
    arrival node OR GAME_OVER on the departure node; here: the node that opens a life)."""
    return frozenset(n.index for n in record.nodes if n.opens_life and n.index > 0)


def action_series(record: Record) -> List[Optional[int]]:
    """index = node; the action id that produced it (None at node 0 and where unknown)."""
    return [None if n.action is None else n.action[0] for n in record.nodes]


def body_action_series(record: Record) -> List[Optional[int]]:
    """The BODY read's channel: NON-SITE-SELECTING presses only. A press carrying a target cell
    is the pointer's act (R-F: POINTER is "the site-selecting action itself"); a worldline that
    moves when the pointer acts on it is what the ego acts on (R-G), never the self. Targeted
    presses read as None here — absent, not still. DIVERGES FROM THE ORACLE: v4's `ego_read`
    counted them and typed click-moved objects EGO (its own comment: "has_directional is NOT
    consulted"); recorded in G1-01's return as a canon-side departure."""
    return [None if n.action is None or n.action[1] is not None else n.action[0] for n in record.nodes]


def _observe(wl: Worldline, action_at: Sequence[Optional[int]], boundaries: FrozenSet[int]) -> EgoMap:
    seen: Dict[int, List[Bearing]] = {}
    still: List[int] = []
    passable: Set[Transition] = set()
    refused: Set[Transition] = set()
    for i, e in enumerate(wl.edges):
        right = wl.steps[i + 1][0]
        if right in boundaries:
            continue  # disregarded, not severed: the worldline still spans it
        aid = action_at[right] if 0 <= right < len(action_at) else None
        if aid is None:
            continue
        site = wl.steps[i][1].anchor
        if e.verb is Verb.MOVE and e.delta is not None:
            seen.setdefault(aid, []).append(tuple(e.delta))
            passable.add((site, aid))
        else:
            still.append(aid)
            if e.verb in HELD:
                refused.add((site, aid))
    by_action = sorted(seen.items(), key=lambda kv: str(kv[0]))
    return EgoMap(
        bearings=tuple(ActionBearing(a, v[0], len(v)) for a, v in by_action if len(set(v)) == 1),
        still=tuple(sorted(set(still), key=str)),
        inconsistent=tuple(a for a, v in by_action if len(set(v)) > 1),
        observed=tuple(ActionObserved(a, frozenset(v)) for a, v in by_action),
        transitions=Transitions(frozenset(passable), frozenset(refused) - frozenset(passable)),
    )


def action_bearings(worldlines: Sequence[Worldline], action_at: Sequence[Optional[int]],
                    boundaries: FrozenSet[int] = frozenset()) -> Dict[int, EgoMap]:
    """{worldline id: EgoMap} for every worldline with at least one observation. A worldline
    with nothing to say is absent, never present-and-empty."""
    out: Dict[int, EgoMap] = {}
    for wl in worldlines:
        m = _observe(wl, action_at, boundaries)
        if m.bearings or m.still or m.inconsistent:
            out[wl.id] = m
    return out


def ego_seal(m: Optional[EgoMap]) -> bool:
    """∃ one witnessed press; refused by the channel law where askable (R-K: binary)."""
    if m is None or not m.observed:
        return False
    if len(m.observed) > 1 and len({b for ao in m.observed for b in ao.bearings}) == 1:
        return False  # channel (b): keys on THAT-ANY action — a schedule
    return True


def channel_a_witness(m: Optional[EgoMap]) -> bool:
    """More than one action observed to move it, more than one bearing among them."""
    if m is None or len(m.observed) <= 1:
        return False
    return len({b for ao in m.observed for b in ao.bearings}) > 1


def ego_witness(m: EgoMap) -> Optional[Tuple[int, Bearing]]:
    for ao in m.observed:
        for b in sorted(ao.bearings):
            return ao.action, b
    return None


# ── R-L · unison from the anchor walk ─────────────────────────────────────────────────────

def _steps_by_node(wl: Worldline) -> Dict[int, Cell]:
    return {n: r.anchor for n, r in wl.steps}


def lockstep(a: Worldline, b: Worldline, boundaries: FrozenSet[int]) -> Tuple[bool, int, int]:
    """(in lockstep, shared presses observed, shared presses on which they moved).
    ∀ over shared presses: same anchor displacement, both or neither. Vacuous (no shared
    moving press) is NOT lockstep — absence is not evidence."""
    sa, sb = _steps_by_node(a), _steps_by_node(b)
    shared = moved = 0
    for t in sorted(set(sa) & set(sb)):
        if t - 1 not in sa or t - 1 not in sb or t in boundaries:
            continue
        da = (sa[t][0] - sa[t - 1][0], sa[t][1] - sa[t - 1][1])
        db = (sb[t][0] - sb[t - 1][0], sb[t][1] - sb[t - 1][1])
        shared += 1
        if da != db:
            return False, shared, moved
        if da != (0, 0):
            moved += 1
    return moved > 0, shared, moved


def composite_egos(sealed: Sequence[int], worldlines: Sequence[Worldline],
                   boundaries: FrozenSet[int]) -> List[Tuple[int, ...]]:
    """Partition the sealed ids into composite egos by pairwise lockstep (union over pairs)."""
    by_id = {w.id: w for w in worldlines}
    parent = {i: i for i in sealed}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    ids = sorted(sealed)
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            if lockstep(by_id[x], by_id[y], boundaries)[0]:
                parent[find(y)] = find(x)
    groups: Dict[int, List[int]] = {}
    for x in ids:
        groups.setdefault(find(x), []).append(x)
    return [tuple(sorted(g)) for g in sorted(groups.values())]


# ── the verdict ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EgoVerdict:
    members: Tuple[int, ...]   # one composite ego; a set (R3)
    kind: str                  # "BODY"
    basis: str
    parallax: str


def _basis(wid: int, m: Optional[EgoMap]) -> Tuple[str, str]:
    parts: List[str] = []
    if m is not None and ego_seal(m):
        a, b = ego_witness(m)  # type: ignore[misc]
        table = " · ".join(f"A{x.action}→({x.bearing[0]:+d},{x.bearing[1]:+d})×{x.presses}" for x in m.bearings)
        parts.append(f"bearing: WITNESSED under A{a} moving it ({b[0]:+d},{b[1]:+d}); "
                     f"{len(m.observed)} action(s) observed to move it — {table}"
                     + (f"; still under {', '.join(f'A{s}' for s in m.still)}" if m.still else "")
                     + (f"; INCONSISTENT under {', '.join(f'A{s}' for s in m.inconsistent)} (more than one "
                        f"bearing observed — recorded, not averaged)" if m.inconsistent else ""))
    parallax: List[str] = []
    if m is not None and ego_seal(m) and len(m.observed) == 1:
        parallax.append("1 action observed: distinguishability unaskable; reopens as coverage arrives")
    parallax.append("actions never pressed have no entry and are never inferred from their opposite")
    return " ‖ ".join(parts), "; ".join(parallax)


def infer_ego_body(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                   boundaries: Optional[FrozenSet[int]] = None) -> Tuple[List[EgoVerdict], Dict[int, EgoMap]]:
    """Every EGO(BODY) verdict over the window — a list of composite egos — with the bearing maps.
    `boundaries` defaults to the life boundaries; `roles.infer` re-derives the read with the sealed
    counters' events added (G3-03: the in-life respawn is a structural boundary, read retroactively)."""
    boundaries = life_boundaries(record) if boundaries is None else boundaries
    action_at = body_action_series(record)
    maps = action_bearings(worldlines, action_at, boundaries)
    sealed = [wl.id for wl in worldlines if ego_seal(maps.get(wl.id))]
    verdicts: List[EgoVerdict] = []
    for members in composite_egos(sealed, worldlines, boundaries):
        bases, paras = zip(*(_basis(w, maps.get(w)) for w in members))
        basis = " ⟨+⟩ ".join(f"###{w:03d}: {b}" for w, b in zip(members, bases))
        if len(members) > 1:
            basis = f"composite of {len(members)} (R-L: lockstep on every shared press) — " + basis
        verdicts.append(EgoVerdict(members, "BODY", basis, " ; ".join(sorted(set(paras)))))
    return verdicts, maps

"""ROLES · ground — what the ego walks on: the fold of the floor, read off the sealed ego.

Canon: 02 §6.3 GROUND (v1.2) — "deformation fully accounted by a sealed ego's displacement";
(1) every deformation is on a press the ego's own displacement produced, (2) the churn is
pure owner-owner exchange with the ego — intrinsic churn empty, (3) non-empty; "never
observed to deform is absence, not evidence"; no ego is ever ground, excluded before the
predicate. R-I (ego-relative; embodied worlds only; a GROUND worldline's deltas are the
ego's, never lever evidence; never masked). R-M (2026-09-07): "labeling the ground is the
necessary inverse of finding an embodied ego with movement" — deciding which worldline the
floor IS cannot precede EGO(BODY) and is never a number; the DEFORM fold retired from the
weave (F-0003) lands HERE as an exact predicate.

Transcription origin (R-C): virelai_v4/weave/ground_read.py @ oracle-v4 (the three conjuncts
over `complement_verdict`; what it proved: one worldline typed on 132 cuts, three near-misses
carrying intrinsic churn — WO_GROUND_01_RETURN_v1); virelai_v4/weave/rejoin.py pass 1 (the
fold's SHAPE: a terminated worldline and its successor at t+1, unique) with its number
removed. v4 ran the conjuncts over a floor its weave had already folded at 0.80; here the
conjuncts ARE the fold.

The predicate, per press (left → right) that is not a life boundary and on which a sealed
ego member displaced (its anchor at right ≠ at left): a non-ego worldline A holding region
A_l at left and a same-class non-ego worldline B holding B_r at right are one ground step iff
    every cell of A_l \\ B_r is owned by an ego member at right   (the ego stepped onto it)
    every cell of B_r \\ A_l was owned by an ego member at left   (the ego stepped off it)
    A_l ≠ B_r                                                      (something was exchanged)
and B is A's unique such successor and A is B's unique such predecessor. B == A is the
continuing case (the matcher kept the floor through a SHRINK/GROW); B ≠ A is the fold — and
then A is absent at right and B at left, which INTERIM_O9 guarantees (a DEFORM terminates).
Conjunct 1 holds on every step by construction; conjunct 2 is the two ∀s; conjunct 3 is
"at least one step". A worldline whose churn on a walk press is not the ego's takes no step
on that press — it is reported, never folded (the Director's stated consequence: a floor
tile that also recolors stands as its own worldline there).

GROUND is a verdict over a SET (roles derived, never stored — R-L's shape): the connected
components of the step graph. Nothing is merged in the weave; LIST 2 keeps the fragments;
LIST 3 prints one GROUND line naming members. NOT carried from v4: `ego_field`'s crossing
account as an ego OBSERVER — under R-M reading the ego off the ground is circular; the
per-button exchange table is rendered here instead, as the ground's parallax (the inverse of
the ego's bearing table). Typed silence: on a POINTER world GROUND is unaskable (R-I), and an
action-blind record cannot seal the ego it needs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from virelai_golden.roles.ego_body import life_boundaries
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell, Region
from virelai_golden.weave.provenance import cell_owners, worldline_owner_index
from virelai_golden.weave.worldline import Worldline


@dataclass(frozen=True)
class GroundStep:
    left: int
    right: int
    action: Optional[int]
    giver: int                 # the worldline at left
    taker: int                 # the worldline at right (== giver when the matcher continued it)
    to_ego: FrozenSet[Cell]    # cells the ground yielded to the ego
    from_ego: FrozenSet[Cell]  # cells the ground took back from the ego


@dataclass(frozen=True)
class GroundVerdict:
    members: Tuple[int, ...]
    steps: Tuple[GroundStep, ...]
    basis: str
    parallax: str


@dataclass(frozen=True)
class GroundRead:
    verdicts: List[GroundVerdict]
    typed: str
    presses: int       # presses in the window that are not life boundaries
    walked: int        # of those, presses on which an ego member displaced
    stepped: int       # walk presses carrying at least one ground step
    ambiguous: int     # walk presses on which a candidate had two exact partners (no fold)
    unmeasured: int    # presses whose cuts were not a partition (owner map undefined)


def _steps_at(worldlines: Sequence[Worldline]) -> Dict[int, Dict[int, Region]]:
    """node → {worldline id → region held at that node}."""
    out: Dict[int, Dict[int, Region]] = {}
    for w in worldlines:
        for n, r in w.steps:
            out.setdefault(n, {})[w.id] = r
    return out


def ego_displaced(at_l: Dict[int, Region], at_r: Dict[int, Region], ego: FrozenSet[int]) -> bool:
    """Some ego member present at both ends with a different anchor — the anchor walk (R-L)."""
    return any(m in at_l and m in at_r and at_l[m].anchor != at_r[m].anchor for m in ego)


def exact_exchange(a: Region, b: Region, owners_l: Dict[Cell, int], owners_r: Dict[Cell, int],
                   ego: FrozenSet[int]) -> Optional[Tuple[FrozenSet[Cell], FrozenSet[Cell]]]:
    """(to_ego, from_ego) if A→B is accounted entirely by the ego's exchange, else None."""
    if a.value != b.value or a.cells == b.cells:
        return None
    lost, gained = a.cells - b.cells, b.cells - a.cells
    if all(owners_r.get(c) in ego for c in lost) and all(owners_l.get(c) in ego for c in gained):
        return frozenset(lost), frozenset(gained)
    return None


def press_steps(left: Cut, right: Cut, action: Optional[int], at_l: Dict[int, Region],
                at_r: Dict[int, Region], owners_l: Dict[Cell, int], owners_r: Dict[Cell, int],
                ego: FrozenSet[int]) -> Tuple[List[GroundStep], int]:
    """Every ground step across one press, plus the count of ambiguous candidates (not folded)."""
    pairs: Dict[int, List[Tuple[int, FrozenSet[Cell], FrozenSet[Cell]]]] = {}
    for a_id, a in at_l.items():
        if a_id in ego:
            continue
        for b_id, b in at_r.items():
            if b_id in ego:
                continue
            if b_id != a_id and (a_id in at_r or b_id in at_l):
                continue  # both continuing: a SPLIT/MERGE question, closed (R8) — not a fold
            ex = exact_exchange(a, b, owners_l, owners_r, ego)
            if ex is not None:
                pairs.setdefault(a_id, []).append((b_id, ex[0], ex[1]))
    taken: Dict[int, int] = {}
    for a_id, cands in pairs.items():
        for b_id, _, _ in cands:
            taken[b_id] = taken.get(b_id, 0) + 1
    steps: List[GroundStep] = []
    ambiguous = 0
    for a_id, cands in sorted(pairs.items()):
        if len(cands) != 1 or taken[cands[0][0]] != 1:
            ambiguous += 1
            continue
        b_id, to_ego, from_ego = cands[0]
        steps.append(GroundStep(left.node, right.node, action, a_id, b_id, to_ego, from_ego))
    return steps, ambiguous


def ground_steps(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                 ego: FrozenSet[int]) -> Tuple[List[GroundStep], Dict[str, int]]:
    boundaries = life_boundaries(record)
    index = worldline_owner_index(worldlines)
    at = _steps_at(worldlines)
    counts = dict(presses=0, walked=0, stepped=0, ambiguous=0, unmeasured=0)
    out: List[GroundStep] = []
    for left, right in zip(window, window[1:]):
        node = record.nodes[right.node]
        if right.node in boundaries or node.ends_life:
            continue
        counts["presses"] += 1
        at_l, at_r = at.get(left.node, {}), at.get(right.node, {})
        if not ego_displaced(at_l, at_r, ego):
            continue
        counts["walked"] += 1
        try:
            owners_l, owners_r = cell_owners(left, index), cell_owners(right, index)
        except (AssertionError, KeyError):
            counts["unmeasured"] += 1
            continue
        aid = None if node.action is None else node.action[0]
        steps, amb = press_steps(left, right, aid, at_l, at_r, owners_l, owners_r, ego)
        counts["ambiguous"] += amb
        if steps:
            counts["stepped"] += 1
        out.extend(steps)
    return out, counts


def components(steps: Sequence[GroundStep]) -> List[Tuple[int, ...]]:
    parent: Dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for s in steps:
        parent[find(s.taker)] = find(s.giver)
    groups: Dict[int, List[int]] = {}
    for x in parent:
        groups.setdefault(find(x), []).append(x)
    return sorted(tuple(sorted(g)) for g in groups.values())


def button_table(steps: Sequence[GroundStep]) -> str:
    """Per action: cells yielded / taken back, and presses — the inverse of the bearing table."""
    acc: Dict[Optional[int], List[int]] = {}
    for s in steps:
        a = acc.setdefault(s.action, [0, 0, 0])
        a[0] += len(s.to_ego)
        a[1] += len(s.from_ego)
        a[2] += 1
    return " · ".join(f"A{a}: yielded {y}, took back {t} over {n} press(es)"
                      for a, (y, t, n) in sorted(acc.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)))


def infer_ground(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                 ego: FrozenSet[int]) -> GroundRead:
    if record.action_channel.startswith("BLIND"):
        return GroundRead([], "GROUND unmeasured: action-blind record, no ego can seal", 0, 0, 0, 0, 0)
    if not ego:
        return GroundRead([], "GROUND unaskable: no EGO(BODY) sealed (R-I: ego-relative, embodied worlds only)",
                          0, 0, 0, 0, 0)
    steps, c = ground_steps(record, window, worldlines, ego)
    verdicts: List[GroundVerdict] = []
    for members in components(steps):
        mine = tuple(s for s in steps if s.giver in members)
        folds = sum(1 for s in mine if s.giver != s.taker)
        cont = len(mine) - folds
        basis = (f"{len(members)} fragment(s) folded over {len(mine)} ego-walk press(es): {folds} fold(s), "
                 f"{cont} continuing exchange(s); every step exact — each cell lost went to the ego, "
                 f"each cell gained came from it; {button_table(mine)}")
        parallax = (f"Band 1 of the fold is REACTIVE by the ego's path, not its own behaviour (02 §6.3); "
                    f"its deltas are the ego's and never lever evidence (R-I); never masked, never a walk-to target; "
                    f"{c['walked'] - c['stepped']} walk press(es) in the window carried no ground step for any "
                    f"worldline (recorded, not folded)")
        verdicts.append(GroundVerdict(members, mine, basis, parallax))
    typed = (f"GROUND asked over {c['presses']} press(es): ego displaced on {c['walked']}, ground stepped on "
             f"{c['stepped']}, ambiguous {c['ambiguous']}, unmeasured {c['unmeasured']}")
    return GroundRead(verdicts, typed, c["presses"], c["walked"], c["stepped"], c["ambiguous"], c["unmeasured"])

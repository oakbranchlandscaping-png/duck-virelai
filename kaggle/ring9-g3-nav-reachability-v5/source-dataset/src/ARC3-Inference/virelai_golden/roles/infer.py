"""ROLES · infer — the typing ladder in lawful order: EGO → GROUND → WALL → COUNTER → LEVER.

Canon: 04 R-A (lawful order ego → counter → levers), R-F (every world seals exactly one ego
kind, BODY or POINTER, before anything else is typed), 02 §6.2 (Band 1 = self-state; Band 2 =
the role; set-valued; derived, never stored; UNKNOWN is a bucket still filling, ∅ is none
earned). R-K (binary seal). R-I / 02 §6.3 GROUND, position: "with the counter, immediately
after the ego seals, and before the lever hunt opens". R-M: the ground is read off the ego.

Transcription origin (R-C): virelai_v4/weave/role_read.py:1106 `infer_roles` — the SKELETON only
(one verdict per worldline, basis + parallax carried, roles derived each call); :205-270
`_settled_revisits`, `_band1_self_state` (Band 1: one fingerprint over ≥ 2 steps is STATIC, more
is REACTIVE; coverage travels with the tag; a single-step worldline has no tag). The ladder at
:809 is NOT copied: v4 typed EGO last ("below every measured verdict") and its own comment
records the cost — the counter seal captured the avatar (H1). R-F forbids that order.
Deviation from BUILD_OUTLINE_v1 (which named `weave/infer.py`): this module reads `roles.*`,
so it lives in `roles/` — the import direction test allows nothing else.

Where GROUND sits (a reading of "with the counter", labeled): GROUND is typed before COUNTER
because the counter's ego-exchange subtraction (G2-01, third correction) is GROUND's second
conjunct one altitude down — the ground informs what the counter must not count; the counter
never informs the ground. The order is EGO → GROUND → COUNTER; R-A's `ego → counter → levers`
is unchanged in what it forbids (no counter before the ego, no lever before both). WALL sits
with GROUND (02 §6.3 WALL, position) and after it: the ground is excluded from the landing
before the wall predicate runs ("the ground never becomes a wall" — a construction under R-M).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from virelai_golden.roles.counter import CounterVerdict, counter_events, infer_counters
from virelai_golden.roles.ego_body import EgoVerdict, body_action_series, infer_ego_body, life_boundaries
from virelai_golden.roles.ego_pointer import PointerVerdict, infer_ego_pointer
from virelai_golden.roles.ground import GroundRead, GroundVerdict, infer_ground
from virelai_golden.roles.lever import LeverRead, infer_levers
from virelai_golden.roles.wall import WallRead, infer_walls
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.weave.worldline import Worldline, region_at

BAND1_STATIC = "STATIC"
BAND1_REACTIVE = "REACTIVE"
EGO = "EGO"
GROUND = "GROUND"
WALL = "WALL"
COUNTER = "COUNTER"
LEVER = "LEVER"


@dataclass(frozen=True)
class RoleVerdict:
    worldline_id: int
    band1: str              # STATIC / REACTIVE / "" (single step: not observed)
    coverage: int           # steps observed
    revisits: int           # steps that returned to a fingerprint already held (a count, not a tag)
    band2: Optional[str]    # EGO / GROUND / COUNTER, or None = ∅ (none earned at this rung)
    ego_kind: Optional[str] = None      # BODY / POINTER when band2 == EGO
    members: Tuple[int, ...] = ()       # the composite this worldline belongs to (R-L; GROUND fold)
    basis: str = ""
    parallax: str = ""


@dataclass(frozen=True)
class RoleRead:
    verdicts: Dict[int, RoleVerdict]
    bodies: List[EgoVerdict]
    pointer: Optional[PointerVerdict]
    typed: str  # the rungs this read typed, as a positive claim
    counters: Dict[int, CounterVerdict] = None  # type: ignore[assignment]
    ground: Optional[GroundRead] = None
    walls: Optional[WallRead] = None
    levers: Optional[LeverRead] = None
    boundaries: FrozenSet[int] = frozenset()   # life boundaries ∪ in-life respawns (G3-03), right nodes


def settled_revisits(fps: Sequence[Tuple[int, frozenset]]) -> int:
    seen, revisits = set(), 0
    for fp in fps:
        if fp in seen:
            revisits += 1
        seen.add(fp)
    return revisits


def band1_self_state(wl: Worldline) -> Tuple[str, int, int]:
    """(band1, coverage, revisits). One fingerprint over ≥ 2 steps is STATIC; more is REACTIVE."""
    if len(wl.steps) < 2:
        return "", len(wl.steps), 0
    fps = [r.fingerprint for _, r in wl.steps]
    return (BAND1_STATIC if len(set(fps)) == 1 else BAND1_REACTIVE), len(wl.steps), settled_revisits(fps)


def respawn_edges(events: Dict[int, List[int]], worldlines: Sequence[Worldline], ego: FrozenSet[int],
                  action_at: Sequence[Optional[int]]) -> FrozenSet[int]:
    """The in-life respawn: a sealed counter's event press across which an ego member displaced by a
    vector that button NEVER produced on a non-event press. A HELD press on an event is not a respawn
    (ls20's A2 refused at the spawn wall on the press the bar starts is a refusal, not a boundary);
    an ordinary walk that happens to fall on a reversal press keeps its ordinary bearing and is
    not one either. Set membership, no number. Right nodes."""
    by_id = {w.id: w for w in worldlines}
    ordinary: Dict[Tuple[int, int], set] = {}
    steps = {m: dict(by_id[m].steps) for m in ego if m in by_id}
    for m, st in steps.items():
        for right in st:
            a = action_at[right] if 0 <= right < len(action_at) else None
            if right in events or a is None or right - 1 not in st:
                continue
            p, q = st[right - 1].anchor, st[right].anchor
            ordinary.setdefault((m, a), set()).add((q[0] - p[0], q[1] - p[1]))
    out = set()
    for right in events:
        a = action_at[right] if 0 <= right < len(action_at) else None
        for m, st in steps.items():
            if right not in st or right - 1 not in st:
                continue
            p, q = st[right - 1].anchor, st[right].anchor
            d = (q[0] - p[0], q[1] - p[1])
            if d != (0, 0) and d not in ordinary.get((m, a), set()):
                out.add(right)
    return frozenset(out)


def infer_roles(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline]) -> RoleRead:
    """One verdict per worldline. Lawful order: EGO, then GROUND off the ego, then COUNTER."""
    bodies, _maps = infer_ego_body(record, window, worldlines)
    pointer, _read = infer_ego_pointer(record, window, worldlines)
    member_of: Dict[int, EgoVerdict] = {m: v for v in bodies for m in v.members}
    blind = record.action_channel.startswith("BLIND")
    counters: Dict[int, CounterVerdict] = {}
    boundaries = life_boundaries(record)
    if not blind:
        counters, _ = infer_counters(record, window, worldlines, frozenset(member_of))
        # retroactive (G3-03): the sealed counters' events are structural boundaries for the ego's
        # bearing read — the in-life respawn. The seal itself is unchanged; only the map is re-derived.
        events = counter_events(record, window, worldlines, frozenset(counters))
        respawns = respawn_edges(events, worldlines, frozenset(member_of), body_action_series(record))
        if respawns:
            boundaries = boundaries | respawns
            bodies, _maps = infer_ego_body(record, window, worldlines, boundaries)
            member_of = {m: v for v in bodies for m in v.members}
    ground = infer_ground(record, window, worldlines, frozenset(member_of))
    ground_of: Dict[int, GroundVerdict] = {m: v for v in ground.verdicts for m in v.members}
    walls = infer_walls(record, window, worldlines, _maps, frozenset(member_of), frozenset(ground_of), boundaries)
    levers = infer_levers(record, window, worldlines, frozenset(member_of), frozenset(ground_of),
                          frozenset(counters), walls.refusals)
    verdicts: Dict[int, RoleVerdict] = {}
    for wl in worldlines:
        b1, cov, rev = band1_self_state(wl)
        ev = member_of.get(wl.id)
        gv = ground_of.get(wl.id)
        if ev is not None:
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, EGO, ev.kind, ev.members, ev.basis, ev.parallax)
        elif gv is not None:
            lv = levers.verdicts.get(wl.id)   # 02 §6.3: GROUND+LEVER is legal ONLY on an exogenous third-worldline effect
            band2 = GROUND if lv is None else f"{GROUND}+{LEVER}"
            basis = gv.basis if lv is None else f"{gv.basis} ‖ {lv.basis}"
            par = gv.parallax if lv is None else f"{gv.parallax} ‖ {lv.parallax}"
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, band2, None, gv.members, basis, par)
        elif wl.id in walls.verdicts:
            wv = walls.verdicts[wl.id]
            lv = levers.verdicts.get(wl.id)   # set-valued (02 §6.2): a door is WALL+LEVER on an exogenous effect
            band2 = WALL if lv is None else f"{WALL}+{LEVER}"
            basis = wv.basis if lv is None else f"{wv.basis} ‖ {lv.basis}"
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, band2, basis=basis, parallax=wv.parallax)
        elif wl.id in counters:
            cv = counters[wl.id]
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, COUNTER, basis=cv.basis, parallax=cv.parallax)
        elif wl.id in levers.verdicts:
            lv = levers.verdicts[wl.id]
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, LEVER, basis=lv.basis, parallax=lv.parallax)
        else:
            par = ("action-blind record: Band 2 cannot be measured" if blind else
                   "∅ at Rung 3: no lever witness" + (f"; {levers.nulls[wl.id]} attributed press(es) with no effect "
                                                       f"(INERT unfalsified, never proven)" if wl.id in levers.nulls else ""))
            verdicts[wl.id] = RoleVerdict(wl.id, b1, cov, rev, None, parallax=par)
    typed = ("EGO, then GROUND and WALL off the ego, then COUNTER, then LEVER over the residue" if not blind
             else "nothing: action-blind record")
    return RoleRead(verdicts, bodies, pointer, typed, counters, ground, walls, levers, boundaries)

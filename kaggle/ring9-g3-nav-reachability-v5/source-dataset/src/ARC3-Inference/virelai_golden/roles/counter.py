"""ROLES · counter — the bookkeeper: it ticks because a press was spent, not because of WHICH.

Canon: 02 §6.3 COUNTER — "schedule-autonomy with monotone structure … it ticks because time
passed or actions were spent — not because of *which* action"; position second, after the ego,
"until identified every lever probe reads its tick as an effect"; the two-counter point (the
fill and the empty, an opposed GROW/SHRINK pair). 01 §3 channel law: a worldline whose
arithmetic keys on THAT-ANY action (channel b). R-A: after EGO, before levers.

Transcription origin (R-C): virelai_v4/weave/role_read.py:310-338 `_marginal_counter_seal` and
weave/coupling.py:136-140 `_cc`, :336-370 `_action_marginal`, :371-390 (press indexing,
acted-on per press resolved at the LEFT cut — the wiring law). What it proved: `COUNTER/FIRM` on
ls20's yellow bar and on vc33's fill in both golden logs of 2026-09-05; H1 (the seal captured
the avatar) is closed here by ORDER — sealed egos are excluded before the predicate (R-A/R-F),
which v4 could not do because it typed EGO last.

The seal, transcribed: over every press this worldline was LIVE for (present at both ends — see the fourth correction),
(1) every press fired an action (coverage certificate — the ∀ ranges over its whole life);
(2) at least one press was un-targeted (not a click on this worldline);
(3) on EVERY un-targeted press its own arithmetic changed — v4's `action_independence == 1.0`
is this ∀ written as a ratio; no threshold;
(4) it is not a member of a sealed ego.

CORRECTED FROM THE ORACLE (labeled, cited to v4's own text): v4 tested (3) on the signed CELL
COUNT delta (`coupling._cc`), a scalar. On ls20 the counter is ONE worldline: a neutral fill
grows for 42 presses, RECOLORS to yellow at the refill (84 cells change class, count unchanged),
then empties for 42. The refill press reads 0 under the count and v4's own log types that
worldline REACTIVE-DRIVEN, not COUNTER. `coupling._change_magnitude`'s docstring states the
rule v4's seal did not use: "labelling by the region's class makes a recoloured cell differ
from itself." So the tick here is: the worldline's (class, cells) at `right` differs from its
(class, cells) at `left` — the Grounding Law's own "did the arithmetic change" (00: "scalar delta
records" is a named reflex). The signed count delta is kept for the rate and sign structure only.
Second correction: the press that ends a life (right node GAME_OVER) is a structural boundary
(02 §6.3: "resetting at structural boundaries") and joins the respawn edge as disregarded —
on ls20 the bar is full, the frame is the death frame, and nothing ticks.
Third (R-I, 02 §6.3 GROUND conjunct 2): a change that is PURE OWNER-OWNER EXCHANGE WITH A
SEALED EGO — intrinsic churn empty, every partner an ego member — is the ego's delta, not this
worldline's; it is not a tick. Measured on the 8-press opening record: the floor (###019)
re-mints on every press the body crosses it and sealed COUNTER without this. GROUND itself is
typed at Rung 3 (G3-01); only its evidence is subtracted here, which is where the canon places it
("with the counter, immediately after the ego seals").

NOT a conjunct, REPORTED (labeled): the sign structure — runs of one sign and the reversals
between them. The canon names "monotone structure"; v4's seal never had it, and the one
reversal in the corpus (ls20 node 86, the bar refilling as the body returned to spawn) is the
heart-loss boundary v4 later discovered by exactly this reversal. Requiring monotonicity across
it would unseal the counter on the world that taught the rule. An oscillator would seal with
runs of length 1 — visible in the report; that becomes a ruling with evidence, not a conjunct
invented here. The rate is a subtree coefficient (02 §6.3), reported as the multiset of deltas.
Typed silence: a counter that ticks only on some presses (the Director's given fact: ft09 ticks
on lever clicks only) does not seal here — its schedule keys on a lever, and that is Rung 3's.
`counter_events` (G3-03): the presses on which a sealed counter RECOLORED or reversed sign — the
refill. Two readers: `roles.lever` LABELS a witness that falls on one; `roles.infer` hands them
to the ego read as STRUCTURAL BOUNDARIES (02 §6.3 "resetting at structural boundaries"; the
transcription of v4's `heart_boundary_edges`, action_roster.py, keyed here on the sealed
counter's own event rather than on the heart, which no per-press seal covers — measured: 4 of 4
heart changes in the corpus fall on these presses). The ego's displacement across such a press
is the respawn's, not a button's; disregarded, not severed (G1-01's law for the life boundary).
Fourth correction (G3-01, exposed by R-M): a worldline is LIVE for a press only when it is
present at BOTH ends. G2-01 counted presence at either end, so a birth or a death was a tick;
once the weave stopped folding the floor (F-0003 closed) every one-press floor fragment sealed
COUNTER on the strength of being born and dying. Birth and death are boundary events of the
worldline, not its arithmetic (provenance.py: "a change into a born worldline or out of a
dying one is a boundary event, not an exchange"); the tick is a change in a persisting thing.
The corpus reads unchanged: the bar and the fill/empty are continuing worldlines throughout.
"""
from __future__ import annotations

from collections import Counter as _Counter
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from virelai_golden.roles.ego_body import life_boundaries
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.weave.provenance import OwnerEdge, cell_owners, complement_verdict, owner_edge, worldline_owner_index
from virelai_golden.weave.worldline import Worldline, region_at

MIN_REPEATED_PROCESS_WITNESS = 8  # ported from Ring 8's frozen clock-detector gate


@dataclass(frozen=True)
class Press:
    left: int                 # the node the press was made from
    right: int                # the node it produced
    action: Optional[int]     # None = not fired / unknown
    acted_on: Optional[int]   # worldline id the click landed on (resolved at `left`), else None
    boundary: bool            # right opens OR ends a life: the respawn / death edge, disregarded
    edge: Optional[OwnerEdge] = None  # who gave which cell to whom across this press


def presses(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline]) -> List[Press]:
    boundaries = life_boundaries(record)
    index = worldline_owner_index(worldlines)
    out: List[Press] = []
    for left, right in zip(window, window[1:]):
        try:
            edge: Optional[OwnerEdge] = owner_edge(left, right, worldlines)
        except AssertionError:
            edge = None
        node = record.nodes[right.node]
        aid = None if node.action is None else node.action[0]
        acted = None
        if node.action is not None and node.action[1] is not None:
            try:
                acted = cell_owners(left, index).get(node.action[1])
            except (AssertionError, KeyError):
                acted = None
        out.append(Press(left.node, right.node, aid, acted,
                         right.node in boundaries or node.ends_life, edge))
    return out


def count_deltas(wl: Worldline, ps: Sequence[Press]) -> List[int]:
    """Signed cell-count delta per press (0 when absent on both ends). The RATE channel — never
    the tick test; `marginal` reads it only on continuing presses."""
    def cc(n: int) -> int:
        r = region_at(wl, n)
        return r.area if r is not None else 0
    return [cc(p.right) - cc(p.left) for p in ps]


def ticked(wl: Worldline, p: Press, ego_members: FrozenSet[int] = frozenset()) -> bool:
    """The worldline's OWN arithmetic changed across the press: (class, cells) at right ≠ at left,
    and the change is not pure exchange with a sealed ego (R-I: that delta is the ego's)."""
    a, b = region_at(wl, p.left), region_at(wl, p.right)
    fa = None if a is None else a.fingerprint
    fb = None if b is None else b.fingerprint
    if fa == fb:
        return False
    if ego_members and p.edge is not None:
        v = complement_verdict(wl, p.edge)
        if v.is_reactive_complement and set(v.partners) <= set(ego_members):
            return False  # the floor announcing the ego's path — not its own tick
    return True


@dataclass(frozen=True)
class Marginal:
    wid: int
    live: int          # presses the worldline was present for (BOTH ends — continuing)
    fired: int         # of those, presses that carried an action
    untargeted: int    # fired presses not clicking this worldline
    untargeted_moved: int
    targeted: int
    targeted_moved: int
    deltas: Tuple[int, ...]  # signed count delta per un-targeted fired press (rate channel)

    @property
    def covered(self) -> bool:
        return self.fired == self.live

    @property
    def independent(self) -> bool:
        return self.untargeted > 0 and self.untargeted_moved == self.untargeted


def marginal(wl: Worldline, ps: Sequence[Press], ego_members: FrozenSet[int] = frozenset()) -> Marginal:
    live_nodes = {n for n, _ in wl.steps}
    deltas = count_deltas(wl, ps)
    live = fired = un = un_m = tg = tg_m = 0
    seq: List[int] = []
    for p, d in zip(ps, deltas):
        if p.left not in live_nodes or p.right not in live_nodes:
            continue  # born or dying across this press: a boundary event, not a tick (G3-01)
        if p.boundary:
            continue  # a death's edge is not a tick and not a non-tick: disregarded
        live += 1
        if p.action is None:
            continue
        fired += 1
        moved = ticked(wl, p, ego_members)
        if p.acted_on == wl.id:
            tg += 1
            tg_m += moved
        else:
            un += 1
            un_m += moved
            seq.append(d)
    return Marginal(wl.id, live, fired, un, un_m, tg, tg_m, tuple(seq))


def sign_runs(deltas: Sequence[int]) -> List[Tuple[int, int]]:
    """[(sign, length), …] over the non-zero deltas, in order — the monotone structure, reported."""
    runs: List[Tuple[int, int]] = []
    for d in deltas:
        s = (d > 0) - (d < 0)
        if s == 0:
            continue
        if runs and runs[-1][0] == s:
            runs[-1] = (s, runs[-1][1] + 1)
        else:
            runs.append((s, 1))
    return runs


@dataclass(frozen=True)
class CounterVerdict:
    wid: int
    marginal: Marginal
    runs: Tuple[Tuple[int, int], ...]
    basis: str
    parallax: str
    seal_kind: str = "FULL_LIFE_INDEPENDENCE"


def counter_seal(m: Marginal, ego_members: FrozenSet[int]) -> bool:
    return (
        m.wid not in ego_members
        and m.covered
        and m.independent
        and m.untargeted >= MIN_REPEATED_PROCESS_WITNESS
    )


def repeated_process_witness(
    wl: Worldline,
    ps: Sequence[Press],
    ego_members: FrozenSet[int],
) -> Tuple[Press, ...]:
    """Longest qualifying suffix seen anywhere: consecutive, untargeted, changing presses.

    This is the object-level form of Ring 8's frozen clock gate.  A run must contain at least
    two distinct action keys; a targeted click, structural boundary, absence, missing action,
    or non-change breaks it.  The test is existential over a literal witnessed run and never
    converts a percentage into a verdict.
    """
    live_nodes = {node for node, _ in wl.steps}
    # The fallback repairs embodied worlds where a structural-like hold interrupts an
    # otherwise action-diverse ticker.  In POINTER worlds, an interrupted run may instead be
    # a target-dependent lever effect (ft09); only the strict full-history seal is honest.
    if not ego_members:
        return ()
    eligible = [
        press
        for press in ps
        if press.left in live_nodes
        and press.right in live_nodes
        and not press.boundary
        and press.action is not None
        and press.acted_on != wl.id
    ]
    action_ids = {press.action for press in eligible}
    # In a POINTER world, reject a process whose on/off outcome is exactly separated by the
    # repeatedly targeted object.  That is a lever-dependent response, not action autonomy.
    if len(action_ids) == 1 and any(press.acted_on is not None for press in eligible):
        by_target: Dict[Optional[int], List[bool]] = {}
        for press in eligible:
            by_target.setdefault(press.acted_on, []).append(ticked(wl, press, ego_members))
        repeated_tick = {
            target for target, outcomes in by_target.items()
            if target is not None and len(outcomes) >= 2 and all(outcomes)
        }
        repeated_flat = {
            target for target, outcomes in by_target.items()
            if target is not None and len(outcomes) >= 2 and not any(outcomes)
        }
        if repeated_tick and repeated_flat:
            return ()

    best: Tuple[Press, ...] = ()
    run: List[Press] = []
    for press in ps:
        qualifies = (
            press.left in live_nodes
            and press.right in live_nodes
            and not press.boundary
            and press.action is not None
            and press.acted_on != wl.id
            and ticked(wl, press, ego_members)
        )
        if qualifies:
            run.append(press)
            if len(run) > len(best):
                best = tuple(run)
        else:
            run = []
    if len(best) < MIN_REPEATED_PROCESS_WITNESS:
        return ()
    action_keys = {
        (press.action, record_cell)
        for press in best
        for record_cell in [None if press.action is None else press.acted_on]
    }
    # BODY worlds diversify by action id.  POINTER worlds have one action id but target
    # different worldlines; `acted_on` is the record-grounded site key available here.
    if len(action_keys) < 2:
        return ()
    return best


def target_controls_direction(wl: Worldline, ps: Sequence[Press]) -> bool:
    """True when different clicked objects deterministically select opposite signs.

    That is a controlled state variable (vc33 level 2's shared panel), not a process keyed on
    THAT-ANY action.  Only repeated target/sign mappings count; isolated presses stay silent.
    """
    by_target: Dict[int, List[int]] = {}
    for press, delta in zip(ps, count_deltas(wl, ps)):
        if press.boundary or press.acted_on is None or delta == 0:
            continue
        by_target.setdefault(press.acted_on, []).append((delta > 0) - (delta < 0))
    settled_signs = {
        signs[0]
        for signs in by_target.values()
        if len(signs) >= 2 and len(set(signs)) == 1
    }
    return len(settled_signs) >= 2


def infer_counters(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                   ego_members: FrozenSet[int]) -> Tuple[Dict[int, CounterVerdict], Dict[int, Marginal]]:
    ps = presses(record, window, worldlines)
    margins = {wl.id: marginal(wl, ps, ego_members) for wl in worldlines}
    verdicts: Dict[int, CounterVerdict] = {}
    for wid, m in margins.items():
        wl = next(item for item in worldlines if item.id == wid)
        strict = counter_seal(m, ego_members)
        repeated = repeated_process_witness(wl, ps, ego_members)
        if not ego_members and target_controls_direction(wl, ps):
            strict = False
            repeated = ()
        if not strict and not repeated:
            continue
        runs = tuple(sign_runs(m.deltas))
        hist = " ".join(f"{d:+d}×{n}" for d, n in sorted(_Counter(m.deltas).items(), key=lambda kv: -kv[1]))
        reversals = max(0, len(runs) - 1)
        if strict:
            basis = (f"ticked on EVERY un-targeted press it was live for: {m.untargeted_moved}/{m.untargeted}, "
                     f"coverage {m.fired}/{m.live} presses fired → keys on THAT-ANY action (channel b); "
                     f"deltas {hist}")
            seal_kind = "FULL_LIFE_INDEPENDENCE"
        else:
            actions = sorted({press.action for press in repeated if press.action is not None})
            basis = (f"ticked on {len(repeated)} consecutive un-targeted presses across action keys "
                     f"{actions}; frozen repeated-process witness ≥{MIN_REPEATED_PROCESS_WITNESS}; "
                     f"whole-life coverage {m.untargeted_moved}/{m.untargeted}; deltas {hist}")
            seal_kind = "REPEATED_PROCESS_WITNESS"
        parallax = (f"sign structure: {len(runs)} run(s), {reversals} reversal(s) — reported, not required; "
                    f"a reversal is a boundary candidate (the bar refilled), never a non-tick"
                    + ("" if m.targeted == 0 else f"; also clicked directly {m.targeted}× (moved {m.targeted_moved})"))
        verdicts[wid] = CounterVerdict(wid, m, runs, basis, parallax, seal_kind)
    return verdicts, margins


def counter_events(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                   counters: FrozenSet[int]) -> Dict[int, List[int]]:
    """right node → sealed counters that RECOLORED (the refill: ls20's bar turns yellow, count delta 0)
    or whose signed count delta reversed on that press — G2-01's 'boundary candidate'. Read here so a
    lever witness coinciding with one is LABELED, never silently subtracted."""
    ps = presses(record, window, worldlines)
    out: Dict[int, List[int]] = {}
    by_id = {w.id: w for w in worldlines}
    for cid in counters:
        last = 0
        for p, d in zip(ps, count_deltas(by_id[cid], ps)):
            a, b = region_at(by_id[cid], p.left), region_at(by_id[cid], p.right)
            if a is not None and b is not None and a.value != b.value:
                out.setdefault(p.right, []).append(cid)
            sgn = (d > 0) - (d < 0)
            if sgn == 0:
                continue
            if last and sgn != last:
                out.setdefault(p.right, []).append(cid)
            last = sgn
    return {k: sorted(set(v)) for k, v in out.items()}

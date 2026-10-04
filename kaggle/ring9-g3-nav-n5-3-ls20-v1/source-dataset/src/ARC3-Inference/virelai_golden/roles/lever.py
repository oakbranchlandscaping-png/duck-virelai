"""ROLES · lever — the cause: a press attributed to this worldline changed a THIRD worldline.

Canon: 02 §6.3 LEVER — "attributed exogenous effect. With ego and counter identified and
excluded, a press attributed to this worldline correlates with deltas on OTHER worldlines — an
effect that survives subtraction of the ego's own motion and the counter's tick. The lever is
the archetype that cannot be soundly identified first; its observable is defined over the
residue the foundation roles leave"; a remote lever is STATIC, a reactive lever changes while
causing — self-delta is irrelevant. 02 §6.2 the ∃/∀ law: "LEVER is existential — one witness
proves it, and later silence cannot retract it." R-G: levers are what the ego acts on — the
ego's contact or press producing an effect on a third worldline. R-I: a GROUND worldline's
deltas are the ego's and never lever evidence; the refusal that typed a WALL is a contact.
R-A: after EGO and COUNTER (here: after GROUND and WALL as well, which the residue needs).

Transcription origin (R-C): virelai_v4/weave/lever_witness.py @ oracle-v4 (256, read whole) —
`witnessed_levers` / `no_effects`: a press attributed to `a`, some other worldline moved on it,
movers that are sealed counters DISREGARDED (recorded, never erased), the first witness cited,
every partner named, no quantifier over the partner ("the retired form demanded the partner be
silent on every unattended press … it fails on the ordinary two-lever case"); what it proved:
LEVER/FIRM on vc33's ###004/###005 in the golden logs. virelai_v4/weave/contact_line.py — the
BODY-world attribution: a worldline that GAVE CELLS to a sealed ego on the press is what the
ego touched. NOT carried: `repeated_contact.py`'s `REPEATED_CONTACT_THRESHOLD = 2` (a chosen
number, and a ∀-shaped bar on an ∃-claim — R-K's reasoning applies: one witness seals, the
count is parallax); `pair_classify.py` / `mechanism_classify.py` (what a lever DOES — Rung 4).

Golden's form. The RESIDUE of a press is its changed cells minus every ego member's cells at
both ends (the ego's own motion, and the ground's exchange with it — R-I) minus every sealed
counter's cells at both ends (the tick, `roles.mask.masked_delta`). A press is ATTRIBUTED to
`a` (not ego, not ground, not counter) iff (POINTER worlds) the press targeted a cell `a` owned
at the left node, or (BODY worlds) `a` gave cells to an ego member across the press, or `a`
held a refused landing on it (WALL's contact). `a` is WITNESSED on a press iff the press is
attributed to `a` and the residue has an owner other than `a` (at either end) that is not
ego, ground or counter. One witness seals LEVER; the first is cited, all are counted.
Recorded beside it, never subtracted silently: presses attributed to `a` whose residue was
EMPTY (a null press — not a witness, not a retraction) and presses whose residue has NO
attribution at all (nothing was pressed or touched, yet a third worldline changed: a schedule
the counter seal did not cover — ls20's hearts — or a mechanism; Rung 4's).

CORRECTED FROM THE ORACLE (labeled): v4's mover channel was a per-worldline scalar magnitude
(`coupling._cc` count deltas — 00 names "scalar delta records" as a reflex) so a RECOLOR mover
read 0; here a mover is any owner of a residue cell, which is the Grounding Law's "did the
arithmetic change". Typed silence: a BODY world where the ego never touched a non-ground
worldline has no attributed press — LEVER is unasked there, and the count of unattributed
residue presses says what the record holds instead.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

import numpy as np

from virelai_golden.roles.counter import counter_events
from virelai_golden.roles.ego_body import life_boundaries
from virelai_golden.roles.mask import counter_cells, masked_delta
from virelai_golden.roles.wall import Refusal
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.provenance import cell_owners, worldline_owner_index
from virelai_golden.weave.worldline import Worldline, region_at


@dataclass(frozen=True)
class LeverPress:
    left: int
    right: int
    action: Optional[int]
    attributed: Tuple[int, ...]        # worldlines the press is attributed to (target / givers / refusers)
    residue: FrozenSet[Cell]
    partners: Dict[int, int]           # residue owner (either end, not ego/ground/counter) → cells
    counter_event: Tuple[int, ...] = ()  # sealed counters that RECOLORED or reversed sign on this press (the refill)


@dataclass(frozen=True)
class LeverVerdict:
    wid: int
    witness: LeverPress                # the first
    witnesses: int
    nulls: int                         # attributed presses with an empty residue
    basis: str
    parallax: str


@dataclass(frozen=True)
class LeverRead:
    verdicts: Dict[int, LeverVerdict]
    presses: Tuple[LeverPress, ...]    # every non-boundary press
    typed: str
    attributed: int                    # presses attributed to at least one candidate
    unattributed_residue: Tuple[LeverPress, ...]   # residue with no attribution: a schedule or a mechanism
    nulls: Dict[int, int]              # candidate → attributed presses with empty residue (the INERT-so-far record)
    self_only: Dict[int, int]          # candidate → attributed presses whose residue lay on itself alone (reactive, not lever)


def _changed(a: np.ndarray, b: np.ndarray) -> FrozenSet[Cell]:
    return frozenset((int(r), int(c)) for r, c in np.argwhere(a != b))


def _cells(ids: FrozenSet[int], by_id: Dict[int, Worldline], node: int) -> FrozenSet[Cell]:
    out: Set[Cell] = set()
    for i in ids:
        r = region_at(by_id[i], node)
        if r is not None:
            out |= r.cells
    return frozenset(out)


def attribution(record: Record, left: Cut, right: Cut, owners_l: Dict[Cell, int], owners_r: Dict[Cell, int],
                ego: FrozenSet[int], refusals: Sequence[Refusal]) -> Set[int]:
    node = record.nodes[right.node]
    out: Set[int] = set()
    if node.action is not None and node.action[1] is not None:       # the pointer's act
        o = owners_l.get(node.action[1])
        if o is not None:
            out.add(o)
    if ego:                                                             # the body's contact: gave cells to the ego
        for cell, o in owners_l.items():
            if o not in ego and owners_r.get(cell) in ego:
                out.add(o)
        for r in refusals:                                              # or refused it (R-I: the contact)
            if r.left == left.node:
                out |= set(r.holders)
    return out


def lever_presses(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline], ego: FrozenSet[int],
                  ground: FrozenSet[int], counters: FrozenSet[int], refusals: Sequence[Refusal]) -> List[LeverPress]:
    by_id = {w.id: w for w in worldlines}
    index = worldline_owner_index(worldlines)
    boundaries = life_boundaries(record)
    cc = counter_cells(window, worldlines, counters)
    excluded = ego | ground | counters          # never a PARTNER: their deltas are explained (R-I, the tick)
    # A GROUND fragment is contacted on ordinary locomotion by definition.  Treating that
    # exchange as lever attribution makes every step inherit any unrelated scheduled delta.
    # A localized pressure plate remains a distinct non-ground worldline and is still askable.
    actors_out = ego | ground | counters
    events = counter_events(record, window, worldlines, counters)
    out: List[LeverPress] = []
    for left, right in zip(window, window[1:]):
        node = record.nodes[right.node]
        if right.node in boundaries or node.ends_life:
            continue
        try:
            owners_l, owners_r = cell_owners(left, index), cell_owners(right, index)
        except (AssertionError, KeyError):
            continue
        changed = _changed(record.nodes[left.node].settled, node.settled)
        residue = masked_delta(changed, cc.get(left.node, frozenset()), cc.get(right.node, frozenset()))
        residue = residue - _cells(ego, by_id, left.node) - _cells(ego, by_id, right.node)
        touched: Dict[int, Set[Cell]] = {}
        for cell in residue:
            for o in {owners_l.get(cell), owners_r.get(cell)}:
                if o is not None and o not in excluded:
                    touched.setdefault(o, set()).add(cell)
        partners = {o: len(cs) for o, cs in touched.items()}   # a cell counts once per owner it touched
        attributed = attribution(record, left, right, owners_l, owners_r, ego, refusals) - actors_out
        aid = None if node.action is None else node.action[0]
        out.append(LeverPress(left.node, right.node, aid, tuple(sorted(attributed)), residue, partners,
                              tuple(sorted(events.get(right.node, ())))))
    return out


def infer_levers(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline], ego: FrozenSet[int],
                 ground: FrozenSet[int], counters: FrozenSet[int], refusals: Sequence[Refusal]) -> LeverRead:
    if record.action_channel.startswith("BLIND"):
        return LeverRead({}, (), "LEVER unmeasured: action-blind record", 0, (), {}, {})
    ps = lever_presses(record, window, worldlines, ego, ground, counters, refusals)
    first: Dict[int, LeverPress] = {}
    count: Dict[int, int] = {}
    nulls: Dict[int, int] = {}
    self_only: Dict[int, int] = {}
    unattributed: List[LeverPress] = []
    for p in ps:
        if not p.attributed and p.residue:
            unattributed.append(p)
        for a in p.attributed:
            third = {w: n for w, n in p.partners.items() if w != a}
            if third:
                count[a] = count.get(a, 0) + 1
                first.setdefault(a, LeverPress(p.left, p.right, p.action, p.attributed, p.residue, third))
            elif not p.residue:
                nulls[a] = nulls.get(a, 0) + 1
            else:
                self_only[a] = self_only.get(a, 0) + 1
    verdicts: Dict[int, LeverVerdict] = {}
    for a, w in sorted(first.items()):
        named = ", ".join(f"###{b:03d} by {n} cell(s)" for b, n in sorted(w.partners.items()))
        basis = (f"WITNESSED: press A{w.action} at {w.left}→{w.right} attributed to it changed {named} — "
                 f"a third worldline, after the ego's and the counter's cells are subtracted → LEVER (∃; permanent)")
        on_reversal = [p for p in ps if a in p.attributed and any(b != a for b in p.partners) and p.counter_event]
        caution = ("" if not on_reversal else
                   f"; {len(on_reversal)} of the witnesses fall on a press where a sealed counter RECOLORED or reversed "
                   f"({', '.join(f'###{c:03d}' for c in sorted({c for p in on_reversal for c in p.counter_event}))}) — "
                   f"a schedule the per-press counter seal does not cover (the per-event counter, owed) is the "
                   f"alternative reading; if it seals, this witness dies with it (the death condition attaches to the witness)")
        parallax = (f"witnessed on {count[a]} attributed press(es); {nulls.get(a, 0)} attributed press(es) with an "
                    f"empty residue (null presses: not retractions); {self_only.get(a, 0)} with residue on itself only"
                    f"{caution}; what the effect IS is Rung 4's; "
                    f"self-delta not read (a remote lever is STATIC, a reactive one changes while causing)")
        verdicts[a] = LeverVerdict(a, w, count[a], nulls.get(a, 0), basis, parallax)
    attributed = sum(1 for p in ps if p.attributed)
    typed = (f"LEVER asked over {len(ps)} press(es): {attributed} attributed to a candidate, "
             f"{len(unattributed)} with residue and no attribution (a schedule the counter seal did not cover, "
             f"or a mechanism — Rung 4's), {sum(1 for p in ps if not p.residue)} with no residue at all")
    return LeverRead(verdicts, tuple(ps), typed, attributed, tuple(unattributed), nulls, self_only)

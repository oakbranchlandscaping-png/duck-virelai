"""WO-REMOTE-WITNESS-01 · A LEVER IS WITNESSED, NOT RATED — AND SOME LEVERS NEVER MOVE.

THE ASYMMETRY, ratified. `LEVER` and `INERT` are the two poles of one claim and they die
in opposite directions:

    LEVER   ∃ a press on it that produced an effect. ONE witness proves it, and no later
            evidence unproves it. A subsequent null press says the lever clamped or the
            state changed; it does not erase what was observed. ONCE WITNESSED, PERMANENT.

    INERT   ∀ presses, no effect. Never provable, only unfalsified so far. One
            counterexample kills it. PERMANENTLY PROVISIONAL.

**A RATE IS THEREFORE THE WRONG INSTRUMENT AT ITS ROOT, NOT BY CALIBRATION.** `on_rate` is
the shape of a ∀-claim — *does it always act* — and lever-ness is not a ∀-claim. The rate
path's strengths are correct measurements of a quantity that answers a different
question; lowering its bar would admit noise and hide the shape error. Nothing here reads
it.

THE REMOTE LEVER, and why this module had to change a second time.
**A remote lever's own arithmetic is EMPTY. That is not a defect — it is what "remote"
means.** The object never changes; the world changes when you press it. Every seal in the
weave reads a worldline's OWN stream — the marginal's two ∀-witnesses, the local-lever
seal, Band 1 itself — so all of them are structurally blind to it, and no threshold
anywhere would help. The evidence for a remote lever is CROSS-STREAM and this module is
the only place that reads it: a press attributed to `a`, and some other worldline moving
on that press.

WHAT WAS RETIRED HERE, and why it was wrong rather than merely strict.
The first form of this rule required the partner to be QUIET ON EVERY UNATTENDED PRESS
(`_quiet_when_unattended`, with `_unattended_presses` building its population). Both are
gone. **That test is a ∀-claim about the PARTNER standing guard over an ∃-claim about the
LEVER**, and it fails on the ordinary case rather than on an exotic one: a reactive region
driven by two levers — or by a lever and a schedule — moves on presses that are not this
lever's, and the ∀ reads that as "the partner moves on its own" and discards witnesses
that were never in doubt. It also carried a ∀-over-∅ guard that abstained the whole module
whenever every press happened to be attributed.

**The replacement is a LABEL, not a quantifier.** A mover that is a SEALED COUNTER is
disregarded — its tick is already explained by its own role — and it is RECORDED, never
erased. Everything else that moved is world delta, and world delta once is a lever.

TWO FILTERS, TWO SIDES OF THE PRESS — do not conflate them, and do not let one absorb the
other:

    exclude     filters the ACTOR.  A worldline the marginal already sealed as
                schedule-autonomous is not a cause, so it never enters candidacy.
                Channel exclusivity BY CONSTRUCTION (WO-W2-C-02), unchanged by this rung.
    disregard   filters the MOVERS. A sealed counter that ticked on this press did not
                tick BECAUSE of this press, so its motion is not evidence of an effect.

`role_read` passes the same sealed set to both because on the worlds seen so far those
two questions have the same answer — but they are different questions, and a future rung
that widens one must decide the other on its own merits.

THE DEATH CONDITION ATTACHES TO THE WITNESS, NOT THE TAG — stated here because a future
chamber will otherwise add a decay. If the observation that established the lever turns
out to be misattributed — the press was not really on this worldline, or the delta was not
really the partner's — the lever dies with it. **What cannot kill it is subsequent
silence.** Falsification still governs; it simply attaches to the evidence rather than to
the label.

THE PERMANENCE IS STRUCTURAL, NOT ENFORCED. The rule below is an ∃ over presses. A null
press is not a witness, and a non-witness cannot subtract from an existential. There is no
retraction path to defend because there is no arithmetic for one to live in.

Pure and stdlib-only. Reads the per-press magnitude channel and the click-attribution
channel this module is handed; computes nothing else, writes nothing, and decides nothing
about any other tag.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple


class LeverWitness(NamedTuple):
    """The single observation that earned the tag, carried so the verdict can cite it.

    `press` is the position in the press series (the same index `magnitude` rows are keyed
    by) and `node` the left node index it began at. `partners` are EVERY worldline that
    moved on that press and was not disregarded — plural because one press can move
    several, and naming only the first would discard observed evidence. `disregarded`
    names the sealed counters that also moved and were attributed to their own role
    instead: recorded on the finding, never erased from it."""
    press: int
    node: int
    partners: Tuple[int, ...]
    magnitudes: Tuple[float, ...]
    disregarded: Tuple[int, ...]


class NoEffect(NamedTuple):
    """A press attributed to a worldline on which SOMETHING moved, but every mover was a
    sealed counter — so there was no world delta and no witness.

    THIS IS AN OBSERVATION, NOT AN ABSENCE, and it is recorded for the same reason the
    coverage certificates are: "nothing happened" and "something happened and was
    attributed elsewhere" are different claims, and a reader who cannot tell them apart
    cannot grade the verdict."""
    press: int
    node: int
    disregarded: Tuple[int, ...]
    magnitudes: Tuple[float, ...]


def _movers_on(magnitude: Mapping[int, Sequence[float]], i: int, actor: int) -> List[int]:
    """Every worldline other than `actor` whose magnitude channel is non-zero at press `i`.

    `actor` is skipped because the LOCAL case belongs to `_marginal_local_lever_seal`,
    which sits ABOVE this branch in the ladder and carries the richer basis for it. **This
    is a division of labour, not a disqualification** — the clicked object's own change is
    world delta too, and `"minus the clicked object"` as a statement of the RULE is struck.
    A worldline whose only effect is on itself is a lever; it is simply not THIS path's
    lever.

    Deterministic order: ascending worldline id, so a multi-partner witness cites its
    partners in a stable sequence rather than in dict order."""
    return [b for b in sorted(magnitude)
            if b != actor and i < len(magnitude[b]) and magnitude[b][i] != 0]


def _attributed_presses(press_left: Sequence[int],
                        acted_press: Mapping[int, Optional[int]],
                        exclude: frozenset) -> Iterator[Tuple[int, int, int]]:
    """`(press_index, left_node, actor)` for every press attributed to a candidate.

    One walk, shared by `witnessed_levers` and `no_effects`, so the two can never
    disagree about which presses they are talking about. `exclude` is applied HERE — at
    the source — which is what makes channel exclusivity a property of construction
    rather than of branch order."""
    for i, left in enumerate(press_left):
        a = acted_press.get(left)
        if a is None or a in exclude:
            continue
        yield i, left, a


def witnessed_levers(
    magnitude: Mapping[int, Sequence[float]],
    press_left: Sequence[int],
    acted_press: Mapping[int, Optional[int]],
    *,
    exclude: frozenset = frozenset(),
    disregard: frozenset = frozenset(),
) -> Dict[int, LeverWitness]:
    """`{worldline_id: LeverWitness}` — every worldline with at least one clean witness.

    THE RULE, threshold-free and per-press:

        a is witnessed at press i  iff
            the press was attributed to a          acted_press[press_left[i]] == a
            a is not itself a sealed counter       a not in exclude
            some other worldline b moved on it     magnitude[b][i] != 0,  b != a
            and at least one such b is not a
            worldline already explained by its
            own role                               b not in disregard

    **NO QUANTIFIER OVER THE PARTNER, and that is the whole change.** The retired form
    demanded the partner be silent on every unattended press; see this module's header
    for why that discarded correct witnesses on the ordinary two-lever case. A partner
    moving at OTHER times says nothing about whether it moved when THIS lever was pressed.

    NO THRESHOLD IS INVENTED, per the rung's own instruction, and none is possible: the
    test is `!= 0` against a recorded channel and a set-membership check. There is no
    rate, no fraction and no tolerance anywhere in this module.

    THE FIRST witness wins, in press order. Deterministic by construction: an ∃-claim is
    satisfied by its earliest evidence, and citing a later one would imply the earlier
    press was somehow insufficient."""
    out: Dict[int, LeverWitness] = {}
    for i, left, a in _attributed_presses(press_left, acted_press, exclude):
        if a in out:
            continue                               # ∃ is satisfied; the first wins
        movers = _movers_on(magnitude, i, a)
        if not movers:
            continue                               # nothing moved — not evidence either way
        held = tuple(b for b in movers if b in disregard)
        effect = tuple(b for b in movers if b not in disregard)
        if not effect:
            continue                               # every mover explained by its own role
        out[a] = LeverWitness(
            press=i, node=left, partners=effect,
            magnitudes=tuple(float(magnitude[b][i]) for b in effect),
            disregarded=held)
    return out


def no_effects(
    magnitude: Mapping[int, Sequence[float]],
    press_left: Sequence[int],
    acted_press: Mapping[int, Optional[int]],
    *,
    exclude: frozenset = frozenset(),
    disregard: frozenset = frozenset(),
) -> Dict[int, NoEffect]:
    """`{worldline_id: NoEffect}` — the FIRST press, per actor, on which something moved
    and every mover was disregarded.

    The mirror of `witnessed_levers` over the same walk, and the reason the disregarded
    tick is never a silent subtraction. A worldline that appears here and NOT in
    `witnessed_levers` was probed, produced motion, and that motion was attributed to
    another worldline's own role — which a reader must be able to see in order to grade
    the verdict, or to notice that a counter was mis-sealed."""
    out: Dict[int, NoEffect] = {}
    for i, left, a in _attributed_presses(press_left, acted_press, exclude):
        if a in out:
            continue
        movers = _movers_on(magnitude, i, a)
        if not movers:
            continue
        if any(b not in disregard for b in movers):
            continue                               # this press had a world delta
        out[a] = NoEffect(press=i, node=left, disregarded=tuple(movers),
                          magnitudes=tuple(float(magnitude[b][i]) for b in movers))
    return out


def _named(ids: Sequence[int], mags: Sequence[float]) -> str:
    """`###00b moved by +n`, one clause per partner — every mover named, never just the
    first. A witness that cites one of three partners has discarded two observations."""
    return ", ".join(f"###{b:03d} moved by {m:+.0f}" for b, m in zip(ids, mags))


def witness_basis(w: LeverWitness) -> str:
    """The verdict's evidence sentence — the observation, what moved, and what was set
    aside, so a reader can grade the claim without leaving the line."""
    held = (f"; {len(w.disregarded)} sealed counter tick"
            f"{'' if len(w.disregarded) == 1 else 's'} disregarded "
            f"({', '.join(f'###{b:03d}' for b in w.disregarded)})") if w.disregarded else ""
    return (f"witnessed: press {w.press} (node {w.node}) targeted it and "
            f"{_named(w.partners, w.magnitudes)}{held} → LEVER (∃-witness; one "
            f"observation earns it)")


def witness_parallax(w: LeverWitness) -> str:
    """The asymmetry, restated where the verdict renders it, because the alternative is a
    future chamber reading a permanent tag as an unretracted one."""
    first = w.partners[0]
    return (f"LEVER is existential and INERT is universal — they die in opposite "
            f"directions. This tag is PERMANENT once witnessed: a later press that moves "
            f"###{first:03d} by nothing says the lever clamped or the state moved on, and "
            f"does not erase press {w.press}. The death condition attaches to the WITNESS, "
            f"not the tag — if that press or that delta is ever shown misattributed, the "
            f"lever dies with it; subsequent silence cannot kill it")


def no_effect_note(n: NoEffect) -> str:
    """The recorded tick, named on the finding it did not earn.

    Ported discipline: observed and recorded, attributed to its role, never erased. If a
    counter here was mis-sealed, this line is where that shows."""
    return (f"NO_EFFECT: press {n.press} (node {n.node}) targeted it and the only motion "
            f"was {_named(n.disregarded, n.magnitudes)} — each already sealed as "
            f"schedule-autonomous, so the tick is that worldline's own arithmetic and not "
            f"this press's effect. Recorded, not erased: a mis-sealed counter would hide "
            f"a real effect here")

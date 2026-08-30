"""WO-COUNTER-EXCHANGE-01 · A CLOCK TRADES WITH ITS DISPLAY.

**THE CONJUNCT.** A worldline may seal COUNTER through the PAIR path only if some single
counterparty GROWs on the edges that worldline SHRINKs. Not correlation — conservation,
read at the verb.

**WHY THE VERB AND NOT THE CELL.** `WO_COUNTER_MINE_01` measured the exchange two ways
over twenty-one records. Read at the CELL, the strongest exchange on the board is the
ground the ego walks across — one worldline trading with the ego on eighty-seven edges,
a single counterparty, perfectly recurring, and exactly the thing that must not be a
counter. Read at the VERB it is excluded, and structurally rather than luckily:

    on all twenty-one records, both tones, the ego's GROW/SHRINK count is 0/0.
    The ego MOVEs and DEFORMs. **It never grows.**

So an object the ego walks over can never satisfy *a partner GROWs where I SHRINK* — the
partner is the ego, and the ego does not grow. That is a fact about the verb stream, not
a bar anyone chose.

**THE QUANTIFIER, AND WHY IT IS EXACT RATHER THAN NEARLY EXACT.** The seal is a ∀ over the
worldline's OWN SHRINK edges against one partner's GROWs. `WO_COUNTER_MINE_01` §5 reported
the relay members as *"SHRINK 41 · partner GROWs on 40"* and that one-edge shortfall is
**an error in that return's denominator, corrected here**: on every relay member the single
unmatched edge is the partner's BIRTH node — the partner is present at the right node and
absent at the left, so it has no edge there at all. `provenance.py:43-46` already rules
that case: *"a change into a born worldline (or out of a dying one) is a boundary event,
not an exchange."* Scoped to the edges the partner actually spans, the ∀ is **41 of 41**.

The scope is therefore DERIVED from the record — the partner's own edge set — and not
chosen. There is no tolerance here and no fraction: one SHRINK edge the partner spanned
and did not GROW on kills the seal, which is the bucket-drain law this module inherits
from `_marginal_counter_seal`.

**COVERAGE IS REPORTED, NEVER CONVERTED INTO CONFIDENCE** — the same discipline the
marginal seal carries. `exchange_note` travels the counts so a reader sees how much the ∀
ranged over, including the boundary edges it could not range over.

**EVERY COUNTERPARTY IS TESTED, NOT THE MOST FREQUENT.** `WO_COUNTER_MINE_01` §10 records
its own first read naming the wrong partner on a 40-versus-40 tie broken by insertion
order — and a tie is exactly the shape a three-member conserved relay produces. The loop
below returns on the FIRST partner that satisfies the ∀ and visits all of them.

**WO-COUNTER-EXCHANGE-02 · WHERE THIS PREDICATE MAY BE ASKED.** The 0/0 measurement above
is a fact about a WALKING ego on DIRECTIONAL records. It is not a law about every world:
on a click world the acted worldline is named by a target cell and never has to translate,
so a legitimate counter there may have a partner that never grows — and a short fixture may
have no verb stream to show one at all. `role_read` therefore consults this predicate ONLY
where `has_directional` holds, which is exactly where the evidence for it was gathered. The
predicate itself is unconditional and knows nothing about that scope; the caller owns it,
because the scope is a statement about the WORLD and this module reads a worldline.

**IT READS AN ACCOUNT THAT ALREADY EXISTS.** `FieldRead.crossings` is built once per
`infer_roles` call (`ego_field.field_read`) and every `Crossing.per_edge` is an edge whose
churn was ENTIRELY owner-owner exchange (`crossing.py:150-159`). This module measures
nothing new; it asks a verb question of a record the weave already keeps, which is why it
adds no pass over the cuts.

Pure and stdlib-only. Writes no belief, reads no library, and types nothing.
"""

from __future__ import annotations

from typing import Any, FrozenSet, Optional

from virelai_v4.weave.edge import Verb


def _right_nodes(worldline, verb: Optional[Verb] = None) -> FrozenSet[int]:
    """The node each of this worldline's edges PRODUCED, optionally filtered by verb.

    With `verb=None` this is the set of edges the worldline SPANS — which is exactly the
    scope the ∀ may range over for a partner, because an edge the partner does not span
    is one it did not exist across (`provenance.py:43-46`'s boundary event)."""
    return frozenset(worldline.steps[i + 1][0]
                     for i, e in enumerate(worldline.edges)
                     if verb is None or e.verb is verb)


def _partner(worldlines, wid: int):
    return next((w for w in worldlines if w.id == wid), None)


def exchange_partner(field, worldlines, wid: int) -> Optional[int]:
    """The counterparty that GROWs on every SHRINK edge it spanned, or `None`.

    Non-emptiness is a logical guard, not a dwell time: ∀ over ∅ is vacuously true, so a
    worldline that never SHRANK — and a partner that spanned none of its SHRINK edges —
    earns nothing here. That is the same guard `_marginal_counter_seal` states for its own
    un-targeted set."""
    subject = _partner(worldlines, wid)
    if subject is None:
        return None
    shrinks = _right_nodes(subject, Verb.SHRINK)
    if not shrinks:
        return None
    for c in (field.crossings.get(wid) or ()):
        other = _partner(worldlines, c.partner)
        if other is None:
            continue
        scope = shrinks & _right_nodes(other)
        if scope and scope <= _right_nodes(other, Verb.GROW):
            return c.partner
    return None


def exchange_seal(field, worldlines, wid: int) -> bool:
    """The conjunct. See this module's header for the quantifier and its scope."""
    return exchange_partner(field, worldlines, wid) is not None


def exchange_note(field, worldlines, wid: int, pair: Any = None) -> str:
    """The PAIR arm's witness, carried on the verdict so the seal's evidence travels with
    it rather than living only in this module. Counts and worldline ids only.

    **ONLY A POSITIVE WITNESS IS EVER WRITTEN, AND THAT IS A CORRECTNESS RULE RATHER THAN
    A RENDER CONVENIENCE.** A worldline sealed through the MARGINAL arm did not need an
    exchange witness and was never asked for one; one on a NON-DIRECTIONAL world was not
    asked either (`WO-COUNTER-EXCHANGE-02` scopes the conjunct to `has_directional`).
    Writing *"no exchange witness"* onto either would report a test it never took as a
    test it failed. The first build did exactly that and the committed byte-identity pin
    (`tests/weave/test_infer_roles_extract.py`) caught it on a click fixture whose counter
    seals marginally — the ROLE CENSUS was unchanged and only that sentence differed. The
    absence of a note is the honest signal: no witness was recorded here."""
    subject = _partner(worldlines, wid)
    pid = None if (pair is None or subject is None) else \
        exchange_partner(field, worldlines, wid)
    if pid is None:
        return ""
    shrinks = _right_nodes(subject, Verb.SHRINK)
    other = _partner(worldlines, pid)
    scope = shrinks & _right_nodes(other)
    return (f"; exchange witness: SHRINK on {len(shrinks)} edge(s), ###{pid:03d} GROWs on "
            f"all {len(scope)} it spanned ({len(shrinks) - len(scope)} boundary edge(s) "
            f"outside the partner's life, excluded)")

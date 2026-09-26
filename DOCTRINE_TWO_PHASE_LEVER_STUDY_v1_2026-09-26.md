# Doctrine: two-phase lever study — deepen alone, then combine

**Type:** `DOCTRINE_TWO_PHASE_LEVER_STUDY` · **v1** · **2026-09-26**
**Status:** LOCKED strategy, Director-ruled 2026-09-26. Governs the whole G4 CLICK branch and
its NAV/HYBRID equivalents. Game-free by construction: it names levers, periods, and classes —
never any world's name, color, position, or mechanic. Highest version wins; amend, never edit.

## The probe grammar (Director's words, binding)

1. **Broad.** Find every lever we can (G3 sweep).
2. **List.** Build the target roster (the G3 inventory).
3. **Deepen, one by one.** Push each lever to its limit with **consecutive same-lever presses**
   (AAAA…) until a masked null or an exact recurrence appears. Read the **period**. **Classify
   the lever** (toggle / cycle / directional / uniform / unknown).
4. **Advance.** Move to the next lever on the list and deepen it.
5. **Append.** If new visual objects appear during deepening, log them to the list and deepen
   them in turn.
6. **Only then, combine.** After the whole list is individually deepened, look at **patterns of
   lever presses** — sequences across levers (ABA, ABC…) — to find the true mechanics of the
   world.

## The phase boundary (the load-bearing law)

**Phase 1 — single-lever deepening.** One lever, consecutive presses, alone. Goal: period +
classification, for every lever. Nothing in Phase 1 presses a second lever. The lever queue is
**dynamic** — objects born mid-deepening append to it (step 5). Phase 1 is complete only when
every lever on the list has a period and a class **and** the queue holds no un-deepened entry
(no pending lever, no unprocessed newborn). Completion is an explicit signal.

**Phase 2 — multi-lever sequences.** Gated on the Phase-1-complete signal. Only here do we press
**combinations** of levers. Everything that requires a second press belongs here: **reversal**
(does lever B undo lever A — the literal ABA), **persistence** (does A's endpoint survive an
intervening control press), **couplings** (do two levers move a connected resource), and the
**world-mechanics synthesis** (the natural-language world law, each clause licensed by a lever
law). Phase 2 reads the finished per-lever dossiers; it never runs while any lever is still
un-deepened.

The boundary is single-lever-alone (Phase 1) versus lever-sequences (Phase 2). "AAAA, BBBB,
CCCC, then ABA, ABC." A press that touches a second lever is Phase 2 by definition.

## Why this order

You cannot say "these two levers move a connected resource" until both are individually known.
Classification from consecutive presses is the cheapest true statement a lever affords, and it
is the vocabulary every later clause is written in. Deepening alone first also gives the best
partial-budget outcome per the world-model goal: a shallow-but-complete model of every lever
beats a deep model of one lever and nothing on the rest. Reversal, persistence, and coupling are
relationships, not properties, so they wait until the properties are in hand.

## Consequences already on the board

- The current `G4.3-LEVER-LIMITS` gate straddles this boundary: its endpoint confirmation is
  single-lever (Phase 1), but its persistence (control press) and reversal (inverse press) are
  multi-lever (Phase 2). Under this doctrine G4.3's cross-lever work re-homes behind the
  Phase-1-complete signal. See `BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1`.
- Classification is a Phase-1 product. `virelai_semantic/typing.py::classify_effect_channel`
  consumes exactly the orbit's uninterrupted single-lever step sequence, so classification is
  earned from Phase-1 data alone.
- The counter is the ignored baseline (`DESIGN`/institutional-memory 2026-09-26); Phase 1 does
  not manage budget. Counter-aware feasibility, when built, informs *which* lever to deepen
  next, never whether to cross into Phase 2 early.

*Locked. The build plan implements Phase 1 first; Phase 2 machinery is later slices.*

# Build plan: G4 CLICK branch, from here to G4 exit

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v1** · **2026-09-27**
**Author:** Claude (Alpha build seat), signed
**Scope ruling (Director, 2026-09-27):** NAV is shelved; G4 work is CLICK only. Cross-level work
is G9. ft09 is the primary CLICK canary; vc33 is the secondary one (its second lever ends level 1).
**True as of:** source `8cfb782`; package `7778750`; Kaggle run `taaf-virelai-ring9-g4-ft09-phase1-v1`
v1 **in flight, output not yet seen**.
**Governing documents:** `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1` (LOCKED),
`BUILD_PLAN_G4_LEVER_REACTION_GATE_2026-09-25`, `MINE_G4_LEVER_SUBTREES_2026-09-25`,
`BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1`, `FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27`.

## 1 · Where we sit

```
G3 inventory ─► G4.0 bind ─► G4.1 anatomy ─► ┃ PHASE 1 (one lever alone) ┃ ─► PHASE 2 (lever sequences) ─► G4.6 law + demo ─► G4 EXIT
                  LIVE         LIVE          ┃ G4.2 orbit  ◄── WE ARE HERE ┃     G4.3r · G4.4 · G4.5
                                             ┃ + endpoint/recurrence tail  ┃     not built / not live
```

We are in **Phase 1**. The per-lever orbit works live for a null stop (vc33 E0004, twice). The
drain across levers works live for the hold. The ft09 run now in flight is the first live test of:
a full drain; a recurrence stop; boundary release on a same-level boundary, if one occurs; and the
G4.3 recurrence branch. Phase 2 does not exist yet as its own engine. What exists is the old
G4.3, which mixes Phase-1 and Phase-2 work and has a confirmed continuity defect.

## 2 · Status of every G4 CLICK component

Tags: **LIVE** confirmed on Kaggle or served runs · **OFFLINE** built and tested, not live ·
**BUILT\*** built with a known defect · **SPEC** specified, not built · **NAMED** named only.

| # | Component | Phase | Tag | Evidence / gap |
|---|---|---|---|---|
| 1 | G4.0 bind G3 levers, reject scoped nulls | — | LIVE | vc33 OpenRouter + Kaggle drain v1 |
| 2 | G4.1 effect anatomy + Duck explanation | — | LIVE | both vc33 levers accepted on Kaggle Qwen |
| 3 | G4.2 orbit, null stop | 1 | LIVE | vc33 E0004 → `NULL_AT_OBSERVED_STATE` (09-26 OpenRouter, 09-27 Kaggle) |
| 4 | G4.2 orbit, recurrence stop + period | 1 | OFFLINE | ft09 is the first live test |
| 5 | S1 drain / return edge (hold G4.2 while a lever is pending) | 1 | LIVE (hold) | Kaggle drain v1; full drain to empty queue not yet seen live |
| 6 | Boundary release (`8cfb782`) | 1 | OFFLINE | 4 tests + replay of the real vc33 segment |
| 7 | Classification | 1 | BUILT\* | `_lever_class` uses stop + period only (ABSORBING/TOGGLE/CYCLE/RECURRENT); the S1 plan named `typing.classify_effect_channel` over orbit steps (directional/uniform); not ported |
| 8 | Endpoint confirmation (second null) | 1 by doctrine | BUILT\* | lives inside G4.3 and runs after the drain → continuity defect |
| 9 | Recurrence re-confirmation (one more period) | 1 by doctrine | BUILT\* | same; works only if the world is still at that lever's endpoint |
| 10 | Newborn append (objects born mid-orbit join the queue) | 1 | SPEC | S1 exit item 5; not built. vc33 Kaggle saw 37 new segment ids, recorded, not queued |
| 11 | Persistence (does the endpoint survive a control press) | 2 | BUILT\* | inside G4.3; anchored to a stored endpoint; never run live |
| 12 | Reversal (does lever B undo A; ABA) | 2 | BUILT\* | same |
| 13 | Phase-2 sequence engine (ABA/ABC generator) | 2 | SPEC | S2 |
| 14 | G4.4 conditions (outcome ledger, split outcomes, discriminating prediction) | 2 | SPEC | subtree mine §G4.4 |
| 15 | G4.5 couplings (joint edges, conserved transfer) | 2 | SPEC | S3 |
| 16 | G4.6 human explanation + frozen prediction → `LeverReactionLaw` | exit | SPEC | subtree mine §G4.6 |
| 17 | Full newborn reopen (born object → G3 → G4.1 → queue) | 1 | SPEC | S4 |
| 18 | Target journal persisted to run artifacts | infra | NAMED | grading currently reads answers/events only |
| 19 | Reset-during-orbit guard; retry backoff; clean stop after level close | infra | NAMED | backlog |

Suite at `8cfb782`: 377 passed, 1 skipped (cloud); 366 on the Director's Mac command, which
ignores two files.

## 3 · The ordered build, from now to G4 exit

Each slice follows the same rhythm: read-only audit → failing test → fix → offline suite green →
one-world Kaggle checkpoint with preregistered criteria (Director runs) → signed review.
The Phase-2 slices do not start until the Phase-1 slices have passed live.

### Phase 1: finish single-lever deepening

**P1 · Read the ft09 run (in flight).** Grade P, C1–C7, I1–I4. Check the continuity prediction
filed before output: C5 passes only if every completed lever returns to its own start state. This
result sets what P2 must cover.

**P2 · Phase-1 tail: move endpoint and recurrence confirmation into the orbit.** Fixes the
continuity finding. After a lever's G4.2 stop, while the world is still there:
- null stop → one more press; a second null gives `SATURATED_AT_OBSERVED_STATE`;
- recurrence stop → one more full period; `EXACT_RECURRENCE_RECONFIRMED` or `RECURRENCE_DIVERGED`.

The lever is Phase-1-done only after this tail. Old G4.3 keeps only persistence and reversal,
which become Phase 2. Tests first: the two failing mixes from the finding (absorbing+toggle,
toggle+absorbing) must fail on `8cfb782`. Kaggle: ft09. Add vc33 if ft09 shows no absorbing lever.

**P3 · Classification from the orbit's own steps.** Port `classify_effect_channel` as the S1 plan
specified. The class then reads the step effects (directional, uniform, toggle, cycle, unknown),
not just how the orbit stopped. Pure offline slice: replay the vc33 and ft09 orbits from
artifacts. No new live run is needed unless the class feeds a gate decision.

**P4 · Newborn append.** An object first seen during an orbit step joins the lever queue as a
Phase-1 obligation. Phase-1-complete then means "every lever and every newborn is done". This needs
a segmentation-churn guard first. The 37 vc33 ids came from a transforming board, not from proven
new objects, so the append must admit only objects that pass the G3 entity lifecycle's birth rule.
The full G3 reopen (S4) follows as P4b. Kaggle: whichever world produced births.

**Phase 1 exit (live, one Kaggle run):** on ft09, every G3 lever reaches stop + tail + class, the
queue empties, `phase1_status = COMPLETE`, and no prior lever is invalidated.

### Phase 2: lever sequences

**P5 · Phase-2 sequence engine (S2), with persistence and reversal re-homed.** A deterministic
ABA/ABC generator over the finished dossiers. Its first consumers are the persistence and reversal
probes now inside G4.3. These are anchored to the **current observed masked state**. That anchoring
is the pending Director decision; see §4. Kaggle: vc33 is the natural reversal test (two opposed
levers), and ft09 tests persistence across toggles.

**P6 · G4.4 conditions.** Outcome ledger keyed by (lever, intervention, masked address) → outcome
set. A split outcome is recorded as a missing condition, never averaged. A conditional law is
accepted only after a frozen discriminating prediction is supported.

**P7 · G4.5 couplings (S3).** Joint edges kept separate from per-lever laws: opposed controls,
relays, conserved transfer. Licensed only by exact conservation plus an out-of-sample prediction.

### Exit

**P8 · G4.6 explanation and demonstration.** Duck explains each lever in ordinary language:
operation, responders, exact arithmetic, repetition, limits, conditions, unknowns. It freezes one
novel prediction; a later action grades it; on support, G4 emits a versioned `LeverReactionLaw`.

**G4 CLICK exit (proposed; needs ruling):** on ft09 and vc33, every G3 lever holds a supported
`LeverReactionLaw`, with Phase-1 and Phase-2 products live-confirmed on Kaggle Qwen. Each world's
explanation meets the quality bar of the vc33 example in the subtree mine.

### Infrastructure, fitted between slices (small, no live run of its own)

- Persist the target journal to run artifacts, before P5, so Phase-2 grading can read product
  history.
- Clean early stop after a level closes, before any vc33 Kaggle run, so the run does not idle out
  its deadline.
- Reset-during-orbit guard; retry backoff.

## 4 · Decisions owed to the Director

1. **Phase-2 anchoring.** Should persistence and reversal probes start from the board as it is now
   (recommended), or should the machine first try to restore a stored endpoint? Restoring requires
   reversal knowledge, which is Phase 2 itself.
2. **Classification vocabulary.** Should the class come from the orbit's step effects
   (`classify_effect_channel`, as the S1 plan specified) or stay stop + period?
3. **G4 CLICK exit definition.** Is the §3 exit right: which worlds, and does it require every
   lever or a stated floor?
4. **P2 timing.** Recommended: write the failing tests now, then wait for the ft09 output before
   finalizing P2, so its evidence folds in.

## 5 · Honest ledger for this plan

- ft09 has never completed a G4 study live; everything past component 5 on ft09 is unobserved.
- G4.3 has never run live in any form.
- The ft09 upload doc called the G4.3 recurrence branch "built". It is built, but had no gate-level
  test, and the S1 order change broke its premise (see the finding).
- S1 shipped without two of its planned exit items: step-based classification and newborn append.
  Both are in this plan as P3 and P4.
- NAV is shelved, not solved. Under `DOCTRINE_NAV_WORLD_AXIOMS_v1`, G3/G4 cannot graduate to fully
  LIVE CONFIRMED on CLICK alone. This plan's exit is a CLICK-branch exit.

— Claude, Alpha build seat, 2026-09-27

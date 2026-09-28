# Technical institutional memory — Cybernetic Duck (2026-09-28)

**Date:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md`. That
file remains the reference for the 2026-09-27 rulings and evidence; this file does not repeat them.
**Builder method:** `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`, as amended by its banners
**Governing doctrine:** `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md` (A1–A6; supersedes v1)
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## The rulings of the day (Director, 2026-09-28)

1. **The ranked list stays.** "The ranked list ensures an exhaustive search with no thought
   needed." The ordered roster on the G2 and G3 cards is kept on purpose. It is recorded as part of
   A5: a stated target may carry an exhaustive ranked search; Duck's freedom is in how it executes
   and in what it concludes, not in reordering a search that must be exhaustive.
2. **Proceed with the other factors** from the guided-v1 review: the bounded card (new axiom A6)
   and the trigger label (A1 v2).
3. **Label every build revision.** The revision ledger (`R9-Rnn` for build revisions, `R9-Inn` for
   harness and infrastructure) now lives in `BUILD_PLAN_G4_CLICK_COMPLETION_v4_2026-09-28.md` §1.
   Each label appears in its slice document, its commit message and the Kaggle package that
   carries it.

## Where things stand

| Area | State | Record |
|---|---|---|
| R9-R03 (`3c89c21`): G2 counter axiom, no-legal-move guard | Committed; Mac 385 passed | `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md` |
| Package `ring9-g4-ft09-guided-v1` (`b68228a`) | Uploaded and run on Kaggle | `UPLOAD_STATUS_G4_FT09_GUIDED_V1_2026-09-27.md` |
| **ft09 guided v1 run** | **Reviewed. G2 closed live under A1 — the first live closure of a stated-target gate.** Then the G3 card was 67,939 characters against a 24,000 budget, and the run crashed at G3 entry. P not met; G4 ungraded. | `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md` |
| **R9-R04: G3 bounded card (A6), counter trigger label (A1 v2)** | **Built and offline-green (cloud 404 passed, 1 skipped). Written to the Mac; awaiting Mac pytest and commit.** | `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md` |
| Plan | v4 is current, with the revision ledger | `BUILD_PLAN_G4_CLICK_COMPLETION_v4_2026-09-28.md` |
| Next live test | `ring9-g4-ft09-guided-v2`, carrying R9-R04; same world and budget as v1 | to be packaged after the R9-R04 commit |

## Revision ledger (copy of plan v4 §1; the plan is authoritative)

| Label | Commit | What | Live status |
|---|---|---|---|
| R9-R01 | `8cfb782` | Boundary release (A3) | Offline and replay |
| R9-R02 | `fcc7f11` | G4-A guided lever study (A4, A5) | Not reached live |
| R9-R03 | `3c89c21` | G2 counter axiom; no-legal-move guard (A1, A2) | G2 closed live on ft09 |
| R9-R04 | *pending* | G3 bounded card (A6); counter trigger label (A1 v2) | Next: guided v2 |
| R9-R05 | planned | G4-B: `predict` tool, frame grading, prediction ledger | — |
| R9-R06 | planned | G4-C and the G4 CLICK exit | — |
| R9-I01 | planned | Target journal persisted to run artifacts | — |
| R9-I02 | planned | Clean planned stop after a declared end (A2 open item) | — |

## Direct evidence added today

- **ft09 guided v1** (57 actions in about 31 minutes, then the crash):
  - Duck's 56 G2 search clicks were identical, in order, to the scripted run's clicks. It followed
    the ranked list, as the card presented it.
  - The counter candidate formed on the two control clicks, as before. Duck's frozen
    `COUNTER_REWRITE` prediction on a control click at (36,36) was `SUPPORTED` at transition 57.
    The counter model locked as the mask baseline.
  - Purity was recomputed from the artifacts: every footprint change in 57 transitions is 12→11.
  - The counter has ticked on 3 of 3 effective clicks and 0 of 54 dead clicks: an observation that
    supports an effective-move counter, not a law.
  - Duck's label said the bar counts every action "regardless of which grid cell is clicked". The
    record contradicts that, and the controller accepted it. R9-R04 closes that hole.
  - The crash: `binding gate context exceeds its 24000-character budget`. Reproduced exactly offline
    from the real replay (67,939 characters). Large pieces: `inherited_frontier` 29,634,
    `entity_ledger` 18,494, `lifecycle_journal` 8,861, `source_frontier` 8,528.
- **R9-R04 offline:** the ft09 G3 entry card is now about 10,061 characters; the peak across a full
  64-object G3 sweep is about 13,501; the completion card is about 8,204.
- **Test counts.** Cloud full suite: 396 at `3c89c21`; 404 (+1 skipped) with R9-R04. Mac (protocol
  command, two suites ignored): 385 at `3c89c21`; **393 expected** with R9-R04 (8 new tests).

## What a new builder must understand

- **Axiom A6: the card is bounded regardless of world size.** Detail is queried, never pushed. The
  G3 card carries the scheduler window (current target plus 5 ahead), up to 8 notable entities,
  role-bound and pending entities, counts, and query handles (`virelai('inventory', offset, limit)`).
  `snapshot()` stays lossless; the card is a view, not the record. Any new card field that grows
  with the world must be windowed the same way, with a test on the largest recorded world.
- **Axiom A1 v2: the label must agree with the record.** `CounterGateMachine.record_trigger()`
  classifies the record as `EVERY_TRANSITION`, `EFFECTIVE_TRANSITIONS_ONLY`, `IRREGULAR`, or `OPEN`
  (either simple class still admissible). The G2 answer must carry a structured `trigger` that is
  admissible; a disagreeing claim is refused with the counts that contradict it. The record's own
  class is always admissible, so this cannot deadlock (A2).
- **The size guard is correct behaviour.** `_GATED_GATE_CONTEXT_MAX_CHARS = 24000` fails fast rather
  than send an oversized card. A crash with that message is a card-design defect, not a model
  failure.
- **Two gate modes still coexist** (stated targets for G2 CLICK and G4-A; scripted G0, G1, G3). The
  ranked list on a stated-target card is by ruling, not a lapse into scripting.
- **The G3 re-sweep repeats G2's clicks by design**, because G3 attributes under the mask. On ft09
  that is 64 more actions, about 35 minutes at the observed pace. Budget: 200 actions and 10,800 s,
  so both fit.
- **Mac file bridge.** The shell bridge from Cowork (`device_bash`) is still broken ("failed to
  create bridge sockets"). Staging and committing files works at the source depth used here
  (`…/ARC3-Inference/inference/framework/`). Run artifacts still need copying up (for example to
  `virelai-review/ft09v2/`).

## Immediate handoff actions

1. Mac pytest (expect 393), then commit R9-R04 with explicit paths and the label in the message.
2. The Director exports the new commit with `git archive`; the builder packages
   `ring9-g4-ft09-guided-v2` from the committed guided-v1 package. Preregister the v1 criteria plus
   G2-3 (the trigger agrees with the record) and A6-1 (no card overflow in any gate).
3. Upload and run on Kaggle (`-r skip`, wait for `ready`, push with the RTX Pro 6000 accelerator),
   check the receipt is byte-identical, then grade. Route every friction through the axioms first.
4. Then R9-R05 (G4-B) offline, R9-I01, R9-R06.
5. Director-owned and still open: rotate the OpenRouter and ARC keys; delete or confirm private the
   four G3-era Kaggle datasets; the G4 CLICK exit definition; whether an unstudied newborn object
   blocks G4-A closure.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md`
3. this file
4. `BUILD_PLAN_G4_CLICK_COMPLETION_v4_2026-09-28.md`
5. `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md`
6. `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`
7. `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md`, then
   `BUILD_SLICE_G4A_GUIDED_LEVER_STUDY_2026-09-27.md`
8. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md` (the 2026-09-27 rulings and evidence)
9. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat, 2026-09-28

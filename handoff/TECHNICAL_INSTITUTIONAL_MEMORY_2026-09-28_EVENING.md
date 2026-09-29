# Technical institutional memory — Cybernetic Duck (evening, 2026-09-28)

**Date:** 2026-09-28, evening
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_PM.md`. The morning and
afternoon files remain the reference for their own rulings and evidence.
**Governing now:**
- `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md` (RATIFIED)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `BUILD_PLAN_G4_CLICK_COMPLETION_v6_2026-09-28.md`

## What happened since the afternoon memory

1. **R9-R05 committed** (`4329185`). The package `ring9-g4-ft09-guided-v2` was built on it, verified
   8/8 against the Director's export, uploaded and run on Kaggle.
2. **The v2 run** (`REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md`):
   - The receipt was identical.
   - G2 closed live again. The trigger check refused a first answer that lacked `trigger`; Duck
     corrected it.
   - G3 witnessed and confirmed **five** levers, so R9-R05 held live.
   - At the fifth dossier the G3 card reached 25,502 characters and the guard ended the run.
     P was not met, so G4 is ungraded.
   - Both gates clicked strictly in rank order. Duck's G2 "new" prediction site was simply rank 57.
   - G3 re-clicked 54 objects G2 had already found totally null.
3. **Prior-art survey** (`MINE_AGENT_MEMORY_PRIOR_ART_v1_2026-09-28.md`):
   - Internally, this was the fourth overflow, each fixed by trimming.
   - We had already specified the right design (the Duck Turn Contract, 09-23) and only half-built
     it.
   - Externally, the survey found budget-filled working sets, deterministic compaction,
     harness-injected recall, and controller-certified memory as our differentiator.
   - Duck made zero recall queries in 121 actions.
4. **Constraints measured:**
   - The context window (65,536 tokens) does not bind; wall time does. Each Duck turn is about
     1,300 generated tokens, about 36 s.
   - Scripted G3 steps each cost a full turn.
   - Scoring is (human ÷ our actions)² per level, with levels weighted, so later levels carry the
     score and memory across levels is where it is earned.
5. **Director rulings:**
   - "The controller should execute scripted moves when possible."
   - Build a comprehensive memory design, not piecemeal.
   - **D1–D7 all ratified:**
     - the memory laws M1–M10 as doctrine;
     - G0–G3 run by the controller, with Duck's first turn the orientation turn;
     - in G4-A the controller runs each lever and Duck explains;
     - lever studies continue across lives;
     - G3 inherits G2's nulls;
     - an UNCERTIFIED lane for Duck's notes;
     - a Kaggle throughput run before budgets are set.
6. **R9-R06 built** (memory stage M-0, the instruments):
   - the replay harness and real v2 record fixture;
   - the record index;
   - the read-only memory store;
   - the turn ledger;
   - the shared gate-action recording path.

   The cloud suite is 420 passed, 1 skipped. Written to the Mac; **awaiting Mac pytest (expect
   409) and commit.**

## What a new builder must understand

- **The design is the plan.** `DESIGN_VIRELAI_MEMORY_v1` §12 stages M-0 to M-6 are one design built
  in order. Do not patch the card field by field again: that is the pattern the design exists to
  end.
- **Three tiers:**
  - the record: lossless, and only the controller writes it;
  - the world model: gate-certified products, shown as a grouped digest;
  - the card: built from slots with budgets.

  Recall is injected first and pulled second. No summaries are written by a model.
- **The executor (M-2) is not built yet.** Until it is, Duck still spends a turn on every action.
- **Replay first.** Any live crash reproduces offline with
  `tools/record_from_artifacts.py ARTIFACTS STEM OUT --replay`. Stage every fix against both real
  ft09 records before any Kaggle run.
- **Artifact names** are derived from the state file's name. See the R9-R06 slice for the edge case
  now guarded in the ledger.

## Immediate handoff actions

1. Mac pytest (expect 409), then commit R9-R06, the v2 review, the prior-art survey, the design,
   doctrine v3, plan v6 and these handoff docs, with explicit paths.
2. Build M-1 (R9-R07): the card builder, slots, grouped digest and preflight, against T1, T3, T5, T7,
   T10 and T11 and the amended T2 anchor.
3. Director-owned and still open:
   - the A7 ruling ("an object has one worldline"), which was not part of D1–D7;
   - confirming the 2026 Kaggle runtime limit and the number of games;
   - key rotation and cleanup of the G3-era datasets.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
3. `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md`
4. this file
5. `BUILD_PLAN_G4_CLICK_COMPLETION_v6_2026-09-28.md`
6. `BUILD_SLICE_MEMORY_M0_INSTRUMENTS_2026-09-28.md`
7. `REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md`, then `MINE_AGENT_MEMORY_PRIOR_ART_v1_2026-09-28.md`
8. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat, 2026-09-28

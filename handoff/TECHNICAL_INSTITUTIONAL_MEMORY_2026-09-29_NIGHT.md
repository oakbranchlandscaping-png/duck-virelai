# Technical institutional memory — Cybernetic Duck (2026-09-29, night)

**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_EVENING.md`,
which is kept in place. The `_PM` and `_EVENING` files' test commands and builder notes still apply.
**Governing now:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `BUILD_PLAN_G4_CLICK_COMPLETION_v10_2026-09-29.md`

## Where things stand

| Stage | Label | State |
|---|---|---|
| M-0 to M-3 | R9-R06 to R9-R09 | Committed, through `e2c2b06` (Mac 461) |
| M-4 G4 economy and lives | R9-R10 | **Built; cloud 469 passed, 1 skipped; awaiting Mac pytest (expect 470) and commit** |
| M-5 Kaggle package and D7 throughput run | — | next |
| M-6 G9 design | — | after M-5 |

## What a new builder must know (additions)

- **Who owns each step.** The executor owns every step it can compute, from G0 to G4-A. Duck owns:
  - the orientation turn, which is due at G4.1 close;
  - each orbit explanation;
  - every stop-and-wake condition.
  The whole G4-A policy is in `controller_executor._orbit_step`.
- **The lives rule is in `g4_guided.restudy_next_life`.** The gate calls it once, in
  `_LeverStudyTarget._route_action`. Its cap is `MAX_LIFE_RESTUDIES`.
- **Budget wakes fire on crossing, not on level.** A new budget must follow the same pattern:
  `wake_signals` then `_crossed`.
- **`tests/test_memory_m4.py`'s `CardDuck` and `LivesRun`** are the production-path acceptance
  harness: a card-only model, and ft09 with an injectable death. Use them for M-5's preflight.

## Immediate handoff actions

1. Mac pytest (expect 470 passed), then commit R9-R10 with explicit paths.
2. Build M-5:
   - the package `ring9-memory-ft09-v1` from the current source, stamped R9-R10;
   - T10 preflight enforced in the packager;
   - the preregistration;
   - the D7 throughput configuration.
   Follow the Kaggle procedure in the bootstrap.
3. Director-owned:
   - rule on R9-R08 deviations 1, 2, 4 and 5;
   - the A7 ruling;
   - confirm the Kaggle runtime and game count;
   - key rotation and G3-era dataset cleanup.

— Claude, Alpha build seat, 2026-09-29

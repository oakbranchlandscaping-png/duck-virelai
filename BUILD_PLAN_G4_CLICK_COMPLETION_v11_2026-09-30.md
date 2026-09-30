# Build plan: G4 CLICK branch, now built on Virelai memory

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v11** · **2026-09-30** (supersedes v1–v10)
**Author:** Claude (Alpha build seat), signed
**Governing documents:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`

## Rulings to date

- NAV is shelved; cross-level work is G9; Kaggle is the test venue.
- Every friction sharpens an axiom; the ranked list stays; every build revision is labelled.
- The controller executes scripted moves; the memory design is built as one plan.
- D1–D7 are ratified.
- **2026-09-29:**
  - The time and action budget wakes are built in M-4.
  - We keep building rather than stop at the ladder's end; G4-B comes first.
  - The clean stop (R9-I02) is added. **The controller owns the end.** This settles R9-R08
    deviation 4.
- **2026-09-30, the G4 CLICK exit (the decision owed since v3):**
  1. **What closes the CLICK branch of G4:** both **ft09 and vc33** finish level 1's G4 with a
     supported `LeverReactionLaw` set. That means:
     - every lever studied alone (G4-A);
     - relations tested by graded predictions (G4-B);
     - one new prediction supported (G4-C).
  2. **G4-C is its own thin gate**, after G4-B:
     - Duck freezes one new prediction drawn from its accepted description, and the controller
       takes it.
     - If it is SUPPORTED, the gate emits the `LeverReactionLaw` set.
     - If it is CONTRADICTED, **G4-B reopens**: Duck tests more and revises the description.
  3. **"New" means an untested action and board.** No graded prediction may already have tested
     the prediction's action from the current counter-masked board. The prediction must name
     the relations of the description it relies on.

**What changed from v10:**
- R9-R10 and R9-R11 are committed.
- M-5 ran live: G4-A was SATISFIED on ft09, and L-1 was answered (an empty bar ends the life).
- R9-R12 (G4-B and the clean stop) is committed (`e1636b1`, Mac 481). Its live test,
  `ring9-g4b-ft09-v1`, is in flight.
- The exit is now defined.

## 1 · Revision ledger

| Label | Commit | What | Live status |
|---|---|---|---|
| R9-R01 to R9-R05 | `8cfb782` to `4329185` | Boundary release, G4-A, G2 axiom, G3 roster, G3 identity | See v10 |
| R9-R06 to R9-R10 | `1a4b6bd`, `ee826ab`, `2941f53`, `e2c2b06`, `3f29fd0` | Memory M-0 to M-4 | **Live (M-5):** G4-A SATISFIED on ft09 |
| R9-R11 | `8ca9fc9` | Live-readiness prompt line | Live (M-5) |
| R9-R12 | `e1636b1` | G4-B levers together; clean stop; M-5 fixes | `ring9-g4b-ft09-v1` in flight |
| **R9-R13** | next | **G4-C: the `LeverReactionLaw` set; a contradiction reopens G4-B** | — |

## 2 · Order of work to the exit

1. **Grade `ring9-g4b-ft09-v1`.** Route every friction through the axioms doctrine first.
2. **Build R9-R13, G4-C, offline** against the rulings above. Its acceptance test runs the offline
   ft09 world through a supported law set, including a contradiction that reopens G4-B.
3. **One package with ft09 and vc33**, both worlds run one after the other, same budget per world.
   It is the first vc33 run on the memory stack; expect fixes.
4. **The exit run:** both worlds end with a supported `LeverReactionLaw` set.

## 3 · Decisions still owed (Director)

- R9-R08 deviations 1, 2 and 5:
  - an OPEN trigger is Duck's;
  - the counter-REOPEN wake is inert;
  - the observer's actor label stays DUCK.

  Deviation 1 matters if vc33's counter trigger is OPEN.
- The A7 ruling ("an object has one worldline").
- D7: drop the model-only sweep, per `FINDING_D7_THROUGHPUT_FROM_ARCHIVE_2026-09-29.md`.
- The real Kaggle runtime and game count, from the competition rules.

## 4 · Honest ledger

- Everything from G4-B on is offline until the in-flight run is graded.
- vc33 has not run on the memory stack. Its levers are not simple self-toggles.
- **The preflight bounds one request, not a turn with many requests** (F4 of the M-5 review).
- **Closing G4 does not score.** It establishes understanding of level 1's levers. Nothing yet
  turns that understanding into solving a level.

— Claude, Alpha build seat, 2026-09-30

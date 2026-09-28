# Build plan: G4 CLICK branch as stated targets

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v4** · **2026-09-28** (supersedes v1–v3)
**Author:** Claude (Alpha build seat), signed
**Governing doctrine:** `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md` (A1–A6);
`DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`.

**Rulings to date:**
- NAV is shelved.
- Cross-level work is G9.
- Kaggle is the test venue.
- A stated target is the goal when possible (G3 scripted; G2 CLICK and G4 stated).
- Every friction sharpens an axiom.
- The ranked list stays (2026-09-28).

## 1 · Revision ledger (labels for the build team)

Every build revision gets an `R9-Rnn` label. It appears in the slice document, the commit message,
and the Kaggle package that carries it.

| Label | Commit | What | Axioms | Live status |
|---|---|---|---|---|
| R9-R01 | `8cfb782` | Boundary release: interrupted levers leave pending; a level change closes the study | A3 | Offline and replay |
| R9-R02 | `fcc7f11` | G4-A guided lever study; G4.3 retired from the ladder | A4, A5 | Not reached live |
| R9-R03 | `3c89c21` | G2 counter axiom (purity, not isolation); no-legal-move guard | A1, A2 | **G2 closed live** (ft09 guided v1); guard not exercised |
| **R9-R04** | *pending* | **G3 bounded card; counter trigger label** | A6, A1 v2 | This build |
| R9-R05 | planned | G4-B: `predict` tool, frame grading, prediction ledger | A5, A1 | — |
| R9-R06 | planned | G4-C: plain-language mechanics and a new prediction; G4 CLICK exit | A5 | — |
| R9-I01 | planned | Target journal persisted to run artifacts | — | — |
| R9-I02 | planned | Clean planned stop after a declared end | A2 (open item) | — |

## 2 · Where we sit

```
G0 ─► G1 ─► G2 counter ─► G3 levers ─► G4.0/4.1 ─► G4-A ─► G4-B ─► G4-C ─► EXIT
LIVE  LIVE  LIVE (R9-R03)  CRASHED AT    live on     built   planned  planned
            stated target  ENTRY on ft09 vc33 only   (R9-R02)
                           → fixed in R9-R04
```

The next live test is `ring9-g4-ft09-guided-v2`. It carries R9-R04 and has the same world and
budget as v1. It is the first chance to reach G3 on ft09, and then G4-A.

## 3 · The targets

These are unchanged from v3, except that A1 now requires a trigger claim that agrees with the
record.

- **G2 (A1):** find, label and mask the counter, and prove purity. Done when the label's trigger
  agrees with the record, and one frozen footprint-scoped prediction on a Duck-chosen action is
  supported. The search follows the ranked list (ruling).
- **G3 (scripted):** the exhaustive ranked sweep under the mask. The card is bounded (A6).
- **G4-A:** each lever is pressed repeatedly to a confirmed end point and explained.
- **G4-B:** how the levers affect each other; every prediction is declared before its test.
- **G4-C:** the level's lever mechanics in plain language, plus one new supported prediction.
- **G4 CLICK exit (proposed):** a supported `LeverReactionLaw` set on both ft09 and vc33.

## 4 · Order of work

1. Mac pytest, then commit R9-R04.
2. Package `ring9-g4-ft09-guided-v2` at the R9-R04 commit. Preregister the v1 criteria plus two
   more:
   - G2-3: the label's trigger agrees with the record;
   - A6-1: no card overflow.
3. Grade it. Route every friction through the axioms doctrine first.
4. Build R9-R05 (G4-B) offline, then run it live. Then R9-I01, then R9-R06.

## 5 · Decisions owed

- The G4 CLICK exit definition.
- Whether an unstudied newborn object should block G4-A closure.

## 6 · Honest ledger

- **G2** has closed live once, on ft09.
- **G3** has never run on ft09; its bounded card is proven offline only.
- **G4-A**, the A2 watchdog and G4.1 on ft09 are all live-unobserved. The G4.1 and G4-A card
  sizes on real ft09 anatomies are unmeasured.
- **Evaluator:** the G2 evaluator does not yet grade the trigger claim.
- **Counter reading:** ft09's counter ticked on 3 of 3 effective clicks and 0 of 54 dead clicks.
  That supports an effective-move counter, but it is an observation, not a law.
- **Scope:** CLICK only; NAV is shelved.

— Claude, Alpha build seat, 2026-09-28

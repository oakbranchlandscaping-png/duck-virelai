# Build plan: G4 CLICK branch as stated targets

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v5** · **2026-09-28** (supersedes v1–v4)
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
- Every build revision is labelled.

**What changed from v4:**
- R9-R04 is committed (`8319853`).
- A new revision, R9-R05, repairs G3 entity identity. It was found offline before the next live
  run; without it ft09's G3 would close with zero levers.
- The planned labels move up by one.

## 1 · Revision ledger

**Label rule.** Labels are assigned in build order, and a label is fixed once its commit exists.
Labels on planned rows are provisional and may move when an unplanned repair is needed first, as
happened here. Every label appears in its slice document, its commit message and the Kaggle
package that carries it.

| Label | Commit | What | Axioms | Live status |
|---|---|---|---|---|
| R9-R01 | `8cfb782` | Boundary release: interrupted levers leave pending; a level change closes the study | A3 | Offline and replay |
| R9-R02 | `fcc7f11` | G4-A guided lever study; G4.3 retired from the ladder | A4, A5 | Not reached live |
| R9-R03 | `3c89c21` | G2 counter axiom (purity, not isolation); no-legal-move guard | A1, A2 | **G2 closed live** (ft09 guided v1) |
| R9-R04 | `8319853` | G3 bounded card; counter trigger label | A6, A1 v2 | Offline; next live |
| **R9-R05** | *pending* | **G3 entity identity survives recolour in place; ambiguity abstains; ft09 ladder offline** | contract §1; proposed A7 | This build |
| R9-R06 | planned | G4-B: `predict` tool, frame grading, prediction ledger (was R9-R05 in v4) | A5, A1 | — |
| R9-R07 | planned | G4-C: plain-language mechanics and a new prediction; G4 CLICK exit (was R9-R06) | A5 | — |
| R9-I01 | planned | Target journal persisted to run artifacts | — | — |
| R9-I02 | planned | Clean planned stop after a declared end | A2 (open item) | — |

## 2 · Where we sit

```
G0 ─► G1 ─► G2 counter ─► G3 levers ─► G4.0/4.1 ─► G4-A ─► G4-B ─► G4-C ─► EXIT
LIVE  LIVE  LIVE (R9-R03)  ft09: offline  offline     offline  planned  planned
                           (R9-R04 card,  on ft09     on ft09
                            R9-R05 identity)
```

**Offline evidence for ft09** (`tests/test_ft09_ladder_offline.py`):
- The real G2 record, then the recorded control law continued by hypothesis.
- G3 finds 2 levers, and G4-A is satisfied at transition 131 of 200.
- Every card is under 24,000 characters.

The next live test is `ring9-g4-ft09-guided-v2`. It carries R9-R04 and R9-R05, with the same
world and budget as v1.

## 3 · The targets

These are unchanged from v4.

- **G2 (A1):** find, label and mask the counter, and prove purity. The label's trigger must agree
  with the record. The search follows the ranked list, by ruling.
- **G3 (scripted):** an exhaustive ranked sweep under the mask. The card is bounded (A6).
- **G4-A:** each lever is pressed repeatedly to a confirmed endpoint and explained.
- **G4-B:** how the levers affect each other; every prediction is declared before its test.
- **G4-C:** the level's lever mechanics in plain language, plus one new supported prediction.
- **G4 CLICK exit (proposed):** a supported `LeverReactionLaw` set on both ft09 and vc33.

## 4 · Order of work

1. Mac pytest (expect 400), then commit R9-R05.
2. Package `ring9-g4-ft09-guided-v2` at the R9-R05 commit. Preregister the v1 criteria plus:
   - G2-3: the trigger agrees with the record;
   - A6-1: no card overflow;
   - G3-1: both control tiles are witnessed as levers, recorded as a prediction from the offline
     ladder.
3. Grade the run. Route every friction through the axioms first.
4. Build R9-R06 (G4-B) offline, then run it live. Then R9-I01, then R9-R07.

## 5 · Decisions owed (Director)

- The G4 CLICK exit definition.
- Whether an unstudied newborn object should block G4-A closure.
- **New:** whether to ratify A7, "an object has one worldline" (see the R9-R05 slice).

## 6 · Honest ledger

- **G2** has closed live once, on ft09.
- **G3 and G4** have never run on ft09. Their passage is proven offline only, and only under a
  toggle law extrapolated from three observed clicks.
- **The bar:** the counter bar allows about 32 effective clicks, and the offline ladder uses 15.
  What ft09 does when the bar empties is unknown. Duck's broken runs in G4-A spend that margin.
- **Evaluator:** the G2 evaluator does not grade the trigger claim; the review recomputes it.
- **Identity:** R9-R05 changes how every world's entity ledger matches continuity. The full suite
  (NAV ego, vc33 replays, continuity shadow) passes, but no NAV world has run live on it.
- **Scope:** CLICK only; NAV is shelved.

— Claude, Alpha build seat, 2026-09-28

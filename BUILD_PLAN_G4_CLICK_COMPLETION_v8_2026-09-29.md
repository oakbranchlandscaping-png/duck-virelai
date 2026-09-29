# Build plan: G4 CLICK branch, now built on Virelai memory

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v8** · **2026-09-29** (supersedes v1–v7)
**Author:** Claude (Alpha build seat), signed
**Governing documents:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`: RATIFIED; the build plan for memory and the executor
  is its §12.
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`: A1–A6 and the memory laws M1–M10.
- `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`.

**Rulings to date:**
- NAV is shelved.
- Cross-level work is G9.
- Kaggle is the test venue.
- Every friction sharpens an axiom.
- The ranked list stays.
- Every build revision is labelled.
- 2026-09-28 (evening): the controller executes scripted moves; the memory design is built as one
  plan; D1–D7 are ratified.

**What changed from v7:**
- R9-R07 is committed (`ee826ab`, Mac 431: the full suite, now counted in full).
- R9-R08 (M-2, the controller executor) is built. The production agent carries ft09 from G0 to G3
  closure with **zero model calls in 72 actions**; the v2 live run took 121 actions and did not
  close G3.
- Five deviations from DESIGN v2 are recorded for ratification (slice R9-R08, "Deviations").

## 1 · Revision ledger

Labels are assigned in build order and fixed once committed. Labels on planned rows are
provisional.

| Label | Commit | What | Governs | Live status |
|---|---|---|---|---|
| R9-R01 | `8cfb782` | Boundary release | A3 | Offline and replay |
| R9-R02 | `fcc7f11` | G4-A guided lever study | A4, A5 | Not reached live |
| R9-R03 | `3c89c21` | G2 counter axiom; no-legal-move guard | A1, A2 | G2 closed live (ft09 v1 and v2) |
| R9-R04 | `8319853` | G3 bounded roster; counter trigger label | A6 v1, A1 v2 | Trigger check fired live and was corrected (v2) |
| R9-R05 | `4329185` | G3 identity survives recolour; ft09 ladder offline | contract §1 | Held live: 5 levers confirmed (v2) |
| R9-R06 | `1a4b6bd` | Memory M-0: replay harness, record index, memory store, turn ledger, shared recording path | M1, M10; T2 | Offline (both ft09 records) |
| R9-R07 | `ee826ab` | Memory M-1: the slot-built card, grouped digest, certified fields, preflight | M3, M4, M5, M7; A6 v2 | Offline |
| **R9-R08** | *pending* | **Memory M-2: the controller executor for G0–G3; G3 inherits G2's total nulls; recording protocol on every envelope** | M8; D2, D5; T6 | This build |
| R9-R09 | planned | Memory M-3: orientation turn, UNCERTIFIED lane, injected recall, `virelai('memory', …)` | M6; D6 | — |
| R9-R10 | planned | Memory M-4: the G4.1 split, the G4-A split, the lives rule, and the time and action wake conditions | M8, M9; D3, D4 | — |
| package | planned | M-5: `ring9-memory-ft09-v1` and the D7 throughput run | — | — |
| later | planned | G4-B, G4-C, and the G9 design (M-6) | A5 | — |

**Harness.** R9-I01 was folded into the turn ledger. **R9-I02 (clean planned stop) stays open.**
v7 had placed it with the executor's END ownership, but R9-R08 did not build END: the solver loop
already stops on boundaries.

## 2 · Where we sit

```
G0 ─► G1 ─► G2 ─► G3 ─► G4.0/4.1 ─► G4-A ─► G4-B ─► G4-C
      controller, offline: 72 actions,          offline  planned  planned
      0 model calls (live: G2 ×2, G3 5 levers)
```

## 3 · Honest ledger

- **The executor is proven offline on one world.** ft09's continuation beyond the recorded tiles
  is a hypothesis. The live test is M-5.
- **The card overflow is fixed by construction (R9-R07)**, but offline only.
- **Time.** The executor takes 72 steps through G3 at a fraction of a second each, offline. Wall
  time with a real environment, and Duck's turns from G4 on, are **not yet measured**: that is the
  D7 run.
- **Kaggle limits.** The 12 h runtime and 55 games are assumptions.
- **Level 1 cost.** ft09 level 1 now costs 72 actions to G3 closure, against a human baseline of
  43 for the whole level. That is repaid only through G9.
- **The bar.** It allows about 32 effective clicks per life. The executor wakes Duck when two ticks
  remain; D4 (M-4) carries lever studies across lives.
- **Design deviations** awaiting ratification: an OPEN trigger is Duck's; the counter-REOPEN wake
  is inert; there is no time or action wake yet; there is no END owner; the observer's actor label
  stays DUCK.

— Claude, Alpha build seat, 2026-09-29

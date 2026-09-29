# Build plan: G4 CLICK branch, now built on Virelai memory

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v7** · **2026-09-29** (supersedes v1–v6)
**Author:** Claude (Alpha build seat), signed
**Governing documents:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`: RATIFIED (v2 records the M-1 design revisions); the
  build plan for memory and the executor is its §12.
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`: A1–A6 and the memory laws M1–M10.
- `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`.

**Rulings to date:**
- NAV is shelved.
- Cross-level work is G9.
- Kaggle is the test venue.
- Every friction sharpens an axiom.
- The ranked list stays.
- Every build revision is labelled.
- **2026-09-28 (evening):**
  - "The controller should execute scripted moves when possible, which in theory should get us to
    gate 3 without needing the Duck."
  - The memory design is built as one comprehensive plan, not piecemeal.
  - D1–D7 are all ratified.

**What changed from v6:**
- R9-R06 is committed (`1a4b6bd`, Mac 409).
- R9-R07 (M-1, the slot-built card) is built. The v2 crash card went from 25,502 to about 4,700
  characters. A card-only Duck completes stress worlds with 2, 8 and 20 levers, and every card is
  flat in the lever count.

**What changed from v5:**
- R9-R05 is committed (`4329185`).
- The ft09 guided v2 run is reviewed (`REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md`):
  - G2 closed live again;
  - G3 confirmed five levers, so R9-R05 held live;
  - the card overflowed at the fifth dossier, 25,502 characters.
- Memory and the controller executor are now the path to G4. G4-B and G4-C move after them.

## 1 · Revision ledger

Labels are assigned in build order and fixed once committed. Labels on planned rows are
provisional.

| Label | Commit | What | Governs | Live status |
|---|---|---|---|---|
| R9-R01 | `8cfb782` | Boundary release | A3 | Offline and replay |
| R9-R02 | `fcc7f11` | G4-A guided lever study | A4, A5 | Not reached live |
| R9-R03 | `3c89c21` | G2 counter axiom; no-legal-move guard | A1, A2 | G2 closed live (ft09 v1 and v2) |
| R9-R04 | `8319853` | G3 bounded roster; counter trigger label | A6 v1, A1 v2 | Trigger check fired live and was corrected (v2) |
| R9-R05 | `4329185` | G3 identity survives recolour; ft09 ladder offline | contract §1 | **Held live**: 5 levers confirmed (v2) |
| R9-R06 | `1a4b6bd` | Memory M-0: replay harness, record index, memory store, turn ledger, shared recording path | M1, M10; T2 | Offline (both ft09 records) |
| **R9-R07** | *pending* | **Memory M-1: the slot-built card, grouped digest, certified fields, preflight** | M3, M4, M5, M7; A6 v2 | This build |
| R9-R08 | planned | Memory M-2: the controller executor for G0–G3, inherited G2 nulls, controller G2 prediction and structured labels | M8; D2, D5 | — |
| R9-R09 | planned | Memory M-3: orientation turn, UNCERTIFIED lane, injected recall, `virelai('memory', …)` | M6; D6 | — |
| R9-R10 | planned | Memory M-4: the G4.1 split, the G4-A split, the lives rule | M8, M9; D3, D4 | — |
| package | planned | M-5: `ring9-memory-ft09-v1` and the D7 throughput run | — | — |
| later | planned | G4-B, G4-C, and the G9 design (M-6) | A5 | — |

Harness items from v5 are folded in:
- R9-I01 (target journal persisted to artifacts) becomes the turn ledger (R9-R06) plus the record
  index.
- R9-I02 (clean planned stop) becomes the executor's END ownership (R9-R08).

## 2 · Where we sit

```
G0 ─► G1 ─► G2 ─► G3 ─► G4.0/4.1 ─► G4-A ─► G4-B ─► G4-C
live  live  live  live: 5 levers   offline  offline  planned  planned
            (×2)  confirmed, then card overflow
```

The next live test waits for M-0 through M-4 and ships as M-5. No Kaggle run goes out before the
offline acceptance tests (DESIGN §10) pass. Every earlier stage is validated by replaying both real
ft09 records.

## 3 · Honest ledger

- **Card overflow.** It is fixed by construction in R9-R07, but offline only: the v2 crash card is
  now about 4,700 characters, and every card is flat from 2 to 20 levers. It is not yet run live.
- **Time.** Controller execution (M-2) is designed but unbuilt. The estimated effect on ft09 level
  1 is about 3–12 Duck turns and about 5–10 minutes, **not measured**.
- **Kaggle limits.** The 12 h runtime and 55 games are assumptions. D7 measures throughput.
- **Level 1 cost.** Even with G2's nulls inherited, level 1 still costs more actions than the human
  baseline. The design repays that only through G9.
- **The bar.** It allows about 32 effective clicks per life, a figure the G2 product itself now
  derives. D4 carries lever studies across lives.

— Claude, Alpha build seat, 2026-09-28

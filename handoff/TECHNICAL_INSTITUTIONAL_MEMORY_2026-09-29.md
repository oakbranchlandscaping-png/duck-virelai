# Technical institutional memory — Cybernetic Duck (2026-09-29)

**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_EVENING.md`. That file
remains the reference for the v2 run, the survey, the measured constraints and the D1–D7 rulings.
**Governing now:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED; v2 records the M-1 design revisions)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `BUILD_PLAN_G4_CLICK_COMPLETION_v7_2026-09-29.md`

## Where things stand

| Stage | Label | State |
|---|---|---|
| M-0 instruments | R9-R06 | **Committed `1a4b6bd`**; Mac 409 passed |
| M-1 slot-built card | R9-R07 | **Built, offline-green (cloud 430 passed, 1 skipped); written to the Mac; awaiting Mac pytest (expect 419) and commit** |
| M-2 controller executor | R9-R08 | next |
| M-3 recall and orientation | R9-R09 | planned |
| M-4 G4 economy and lives | R9-R10 | planned |
| M-5 Kaggle package and throughput run | — | after M-4 |

## What a new builder must understand (additions)

- **The card is built, not trimmed** (`inference/framework/card_builder.py`).
  - Each slot is a whitelisted projection of the gate's public view.
  - A new gate field reaches Duck only if someone adds it to a slot on purpose, and T3 guards
    this.
  - Budgets and the certified-field lists are constants at the top of that module.
- **Certified fields.** Templates show controller-certified data as `CERTIFIED`, and the controller
  fills it in `CyberneticGateMachine.submit_answer`. Anything Duck writes is still validated as
  written.
- **The card-only Duck** (`tests/card_duck.py`) is the acceptance instrument for every later stage.
  If a change makes a gate need something the card does not show, this Duck stops. Keep it
  passing at 2, 8 and 20 levers.
- **Replay any live run offline** with `tools/record_from_artifacts.py ARTIFACTS STEM OUT --replay`.
  The harness now also replays with answers written from the card (`answer_source="card"`).

## Immediate handoff actions

1. Mac pytest (expect 419), then commit R9-R07 with explicit paths.
2. Build M-2 (R9-R08), the controller executor:
   - `next_step_owner()`;
   - controller execution of G0–G3 through the shared recording path (`_gate_probe_begin` /
     `_gate_probe_record`);
   - G3 inheriting G2's total nulls (D5);
   - the controller's G2 prediction and structured labels (D2);
   - stop-and-wake conditions;
   - test T6: ft09 G0 to G3 closure with zero model calls.
3. Director-owned and still open:
   - the A7 ruling;
   - confirming the 2026 Kaggle runtime and game count;
   - key rotation and G3-era dataset cleanup.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
3. `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`
4. this file, then `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_EVENING.md`
5. `BUILD_PLAN_G4_CLICK_COMPLETION_v7_2026-09-29.md`
6. `BUILD_SLICE_MEMORY_M1_SLOT_CARD_2026-09-29.md`, then `BUILD_SLICE_MEMORY_M0_INSTRUMENTS_2026-09-28.md`
7. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat, 2026-09-29

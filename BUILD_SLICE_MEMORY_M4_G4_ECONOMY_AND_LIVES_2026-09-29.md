# Build slice R9-R10: memory stage M-4, the G4 economy and lives

**Revision label:** `R9-R10`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Governing design:** `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` §5.5 (the G4.1 and G4-A rows), §6
(lives), §10 (T8).
**Rulings:**
- D3: the controller runs each lever to its endpoint, Duck explains, and Duck may ask for an
  extra run.
- D4: a lever study continues across a death on the same level.
- 2026-09-29: build the time and action budget wakes here (deviation 3 of R9-R08).

**Base:** `e2c2b06` (R9-R09). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## The result in one line

On ft09 offline, the production agent now goes from G0 to a **satisfied G4-A in 92 actions and 7
Duck turns**:
- 1 orientation turn;
- 5 orbit explanations;
- 1 step when the counter bar crossed two ticks left.

The controller takes every other step, including all 5 G4.1 anatomy answers and every lever run.
The whole run replays offline from its own artifacts. A death in the middle of G4-A is re-studied
in the next life, and nothing learned is lost.

## What was built

| File | What |
|---|---|
| `controller_executor.py` | **The controller now owns G4.1 and G4-A.** For G4.1 it renders each anatomy answer from the certified channels (every channel id and exact rewrite named, so the gate's check passes). For G4-A it presses, one press per step, the lever whose run is RUNNING or CONFIRMING, then one whose run ended, then one not yet started. As soon as a run is confirmed, the step is Duck's: the explanation is Duck's. An extra run Duck asks for (up to 8 presses) comes before everything else. The orientation turn is checked first, so no controller step runs while it is due. |
| same, `wake_signals` / `wake_reason` | **Budget wakes (ruling 2026-09-29).** Counter ticks (≤ 2), actions remaining (≤ 10) and seconds remaining (≤ 120) each wake Duck **once, on crossing**. The counter's crossing re-arms each life. The thresholds are provisional until D7 measures real budgets. |
| `controller_turn.py` | Keeps the last step payload, for the budget crossings. `request_rerun` validates Duck's `virelai('rerun', id=…, presses=N)`: G4-A only, a lever the controller can press, 1 to 8 presses. When the extra run is done, Duck is woken. |
| `memory_queries.py` | Routes `rerun`. |
| `g4_guided.py`, `restudy_next_life` | **D4, the lives rule.** A run cut off by a death on the same level returns its lever to the study, whose status becomes RUN_ENDED_RESTART_NEEDED. It is not released. A level change is still G9's. After `MAX_LIFE_RESTUDIES` = 2 re-studies, the next death releases the lever as before (8cfb782), so Phase 1 cannot deadlock on a lever that keeps killing. The G4-A product records `life_restudies`. |
| `virelai_gates.py` | Applies the lives rule in `_route_action` (a condition, no new branch). The G4-A rule text now describes the executor and the rerun request. **Removed:** the unused `monitor_counter_transition` alias, whose one test now calls `apply_counter_baseline`, and the `_cell_bbox` indirection. |
| `annotation_lane.py` | **The orientation turn moves from G3 close to G4.1 close.** The controller now certifies the anatomy too, so Duck's first turn reads G3 and G4.1 together; that single turn is the design's "Duck explains (1 turn)" for G4.1. |
| `recall.py` | Keys on the lever whose answer is due. Recalled transitions are compact (full rows are one pull away). The "certified lever" line is no longer repeated for the G4 products. |
| `solver.py` | The step payload carries `actions_remaining` (from `max_actions_per_game`). |
| `record_replay.py`, `tools/record_from_artifacts.py` | Records now keep the G4.1 and G4-A answers. Replay answers a roster that probing closed in the middle of a record. |

## Found: ft09's bar does not cover the full protocol for five levers

On the continued-law ft09 world, G0–G3 spend 14 counter ticks and G4-A needs 4 presses per lever.
The fifth lever's run crosses **two ticks left**; the bar ends at zero ticks as that lever's run
completes. On this world an empty bar costs nothing. Live, it probably ends the life (the v2
review noted the bar is exhausted under the full protocol). The executor now:
- stops and hands that step to Duck (the one "act" turn above);
- re-studies a lever cut off by the resulting death in the next life (D4).

Whether an empty ft09 bar is lethal is **unverified**, and is a question for the M-5 run.

## Measured (ft09, offline, production path)

| | Live v2 (R9-R05) | R9-R08 | **R9-R10** |
|---|---|---|---|
| Furthest gate | G3, not closed | G3 closed | **G4-A satisfied** |
| Actions | 121 | 72 | **92** |
| Model calls | ≈ 130 | 0 to G3 | **7 Duck turns in all** |
| Gate answers | 5 (Duck) | 9 (controller) | 14 controller + 5 Duck + 1 orientation |

Largest cards (stress world, 2 → 20 levers):
- G2: 5,790 → 5,791
- G3: 4,389 → 4,281
- G4.1: 4,909 → 4,878
- G4-A: 6,778 → 7,651

All are within the 16,200 budget, and each grows less than 1,000 characters from 2 levers to 20.

## Tests

`tests/test_memory_m4.py` has 8 new tests: 4 production-path tests, plus 4 parametrised
budget-wake cases. Duck is a model that reads only the card.

- **ft09 to a satisfied G4-A.**
  - Duck's turns are exactly `orient, explain ×4, act, explain`, and the log names the budget wake.
  - The 5 anatomy answers are the controller's; the 5 orbit answers are Duck's.
  - 92 actions, of which one is Duck's.
- **An extra run.** Duck asks for 2 presses before its first explanation. The controller presses
  exactly 2 more times than without the request. Both presses are on the record as
  PRESS_AFTER_CONFIRMED_RUN, and the confirmed run is not rewritten.
- **T8, lives.** A game over on the second G4-A press, then the harness reset.
  - The lever is re-studied.
  - G4-A completes with all 5 levers and none released.
  - `life_restudies` totals 1.
  - The G3 product and Duck's notes persist.
- **The action and time budgets** each wake once, on crossing, and never re-fire.
- **The whole G0-to-G4-A run replays offline:** 92 steps, 17 answers, satisfied.

Amended:
- `test_g4_phase1_boundary`: the pre-D4 same-level release test becomes two tests:
  - a death returns the lever to the study, and the lever then completes;
  - a lever that dies three times is released, and the rest drains (no deadlock).
- `test_memory_m2`:
  - T6 now expects the first model call to be the orientation at G4-A, and 14 controller answers;
  - the budget-wake test checks it fires once, on crossing.
- `test_memory_m3`: orientation and recall are exercised at G4-A. The notes-on-an-answer test
  explains a lever the controller ran.
- `test_counter_gate`: calls `apply_counter_baseline` directly, because the alias was removed.

**Suite:** cloud **469 passed, 1 skipped** (470 tests). Ruff is clean on every changed file.
**Mac expected: 470 passed.**

## Ratchet

| | R9-R09 | R9-R10 |
|---|---|---|
| `virelai_gates.py` | 5,800 | **5,799** |
| `_LeverStudyTarget._route_action` | 68 | 68 |
| `tool_agent.py` | 2,777 | 2,777 |
| `ToolAgent.analyze` | 414 | 414 |

## What this does not do

- **Duck's orbit explanations are still one turn per lever.** That is the design (D3), and it is
  the bulk of Duck's G4 cost.
- **The budget thresholds are guesses** (2 ticks, 10 actions, 120 s) until the D7 throughput run.
- **Everything here is offline.** The next step is the M-5 package, `ring9-memory-ft09-v1`, with
  the D7 throughput run: the first live test of R9-R06 through R9-R10.

— Claude, Alpha build seat, 2026-09-29

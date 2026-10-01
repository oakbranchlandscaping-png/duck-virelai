# Build slice R9-R15: replay fidelity and actor provenance (G4 solidified)

**Revision label:** `R9-R15`
**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed
**Base:** `d2bf323` (R9-R14).
**Source of the findings:** `REVIEW_RING9_G4_EXIT_KAGGLE_V1_2026-09-30.md`, findings F-R1 and F-R2. F-R3 was found while mining the win-capsule output for the cross-level work.
**Altitude:** all three are code-level. None changes gate logic or a contract.

## Why this slice comes first

The replay is the instrument every live grade is checked against ("replay is gospel"). The exit run showed it diverging from the live run in two ways. Cross-level and cross-death work will lean on it harder than G4 did: levels change, and Duck acts on its own turn. So the instrument gets fixed before anything is built on top of it.

## F-R1: a completed level stays in the record

**Problem:** `tools/record_from_artifacts.py` kept a step's boundary only when its state was not `NOT_FINISHED`. A completed level reports `NOT_FINISHED` with `level_completed: true`, so the vc33 record lost its level change.

**Fix:** `_boundary_kept` also keeps the boundary when `level_completed` is set or the level number changed.

## F-R2: replay matches each answer to the lever the gate asks about

**Problem:** live, Duck pressed E0057 on its own turn after the death at transition 88. So E0057 was studied, and answered, before E0056. The record keeps answers in acceptance order, and replay handed them over in that order. Replay therefore refused E0057's answer at the moment the machine asked about E0056.

**Fix:** `record_replay._answer_index` takes the recorded answer whose `entity_id` matches the template's. Answers with no entity are still taken oldest first.

## F-R3: the controller's actions are labelled CONTROLLER

**Problem:** `solver.step_env` never passed an actor, so every live transition was labelled `DUCK`. The vc33 win capsule therefore credited Duck with the controller's winning press.

**Fix:**
- The controller now sends `"actor": "CONTROLLER"` with its action (`controller_turn.py`).
- `step_env` accepts that one value. Anything else, or nothing, stays `DUCK`.
- Duck's own action path builds its request without an actor, so Duck cannot claim to be the controller.

## Changed

| File | Change |
|---|---|
| `tools/record_from_artifacts.py` | `_boundary_kept` (F-R1) |
| `inference/framework/record_replay.py` | `_answer_index` (F-R2) |
| `inference/framework/solver.py` | `step_env` passes the actor (F-R3). A call was folded, so the file is net −2 lines. |
| `inference/agent/controller_turn.py` | The controller's request carries `actor` (F-R3) |
| `tests/test_r9_r15_replay_fidelity.py` (new) | 5 tests (see below) |
| `tests/fixtures/ft09_kaggle_exit_v1_record.json.gz` (new) | The live exit-run record for ft09: 118 transitions, 36 answers |
| `tests/fixtures/vc33_kaggle_exit_v1_record.json.gz` (new) | The live exit-run record for vc33: 26 transitions, 7 answers, including the level win |

**Tests.** Four failed before their fix; the fifth pins behaviour:
1. A completed level keeps its boundary in the record (F-R1).
2. vc33 replays to the live stop "the level changed during G4…", with E0005 interrupted at the level 1→2 change. This one passes either way, because the fixture already carries the boundary. It pins the replay at a level change for the G9 work.
3. ft09 replays through G4-C (F-R2). Its G4-A answers are out of the machine's order, as they were live. It reproduces:
   - P1–P8 SUPPORTED, frozen at 109–116 and graded at 110–117;
   - L1 SUPPORTED at 118;
   - a COMPLETE law set.
4. `step_env` labels CONTROLLER only when asked, and defaults to DUCK. A forged value stays DUCK (F-R3).
5. The production controller sends `actor: CONTROLLER` with every action (F-R3).

**Fail-first check:** I reverted the four code changes. Tests 1, 3, 4 and 5 then failed; test 2 passed. With the fixes restored, all 5 pass.

**Suite:** cloud **491 passed, 1 skipped** (492 tests). Ruff is clean. **Mac expected: 492 passed.**

## Ratchet (non-blank, non-comment lines)

| File | R9-R14 | R9-R15 |
|---|---|---|
| `solver.py` | 1,376 | **1,374** |
| `controller_turn.py` | 176 | 176 |
| `record_replay.py` | 220 | 229 |
| `tools/record_from_artifacts.py` | 134 | 138 |

`virelai_gates.py` and `tool_agent.py` are untouched.

## What this does not do

- **The earlier review needs a correction.** It said "the controller is deterministic across live runs". That holds only until Duck takes an action on its own turn. The replay now handles that case; it does not prevent it.
- **The win capsule already written for vc33 still says `DUCK`.** Artifacts are not rewritten; the fix applies from the next run.

— Claude, Alpha build seat, 2026-09-30

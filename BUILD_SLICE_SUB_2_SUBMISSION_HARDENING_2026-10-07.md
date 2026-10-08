# Build slice SUB-2: submission hardening after the dry run (D-1, D-2, D-3)

**Date:** 2026-10-07
**Author:** Claude (Alpha build seat, click line), signed
**Director's rulings (2026-10-07):**
- D-3: **free play** (a controlled stop rests the level in normal play rather than ending the game);
- held-out masking: not required;
- SUB-2: **built as described**.

**Governs:** `REVIEW_RING9_SUBMISSION_DRYRUN_V1_KAGGLE_2026-10-07.md` §4. The review's evidence is cited, not repeated, here.
**Base:** `ring9-unified` @ `2cfdbf1`. Its runtime source is the `c5e8ff6` floor: 619 passed, 1 skipped. The commits after it change documents and a packager only.
**Altitude:** code-level, under the ruling. Three shared files get small changes, announced here and to Sol:
- `action_names.py` and `solver.py`, from the Duck harness;
- `controller_turn.py`, shared by the CLICK and NAV lines.

## 0 · In one paragraph

Three changes, each tested to fail before the fix:
- **D-1.** ACTION7 becomes a harness action. The engine had it, but the action-name table did not, so every press of it was refused.
- **D-2.** The controller can no longer spin. After three consecutive turns in which it executes nothing, the level rests in normal play (axiom A2). The solver loop also waits a little before repeating a turn that did nothing.
- **D-3.** In submission mode, a controlled stop rests the level in normal play, as the Director ruled. Canaries keep the old behaviour, ending the game, which gives a cleaner diagnosis. A second controlled stop while already in play still ends the game.

## 1 · Changes

| File | Change | Lines |
|---|---|---|
| `ARC3-Inference/inference/agent/action_names.py` | `"ACTION7": "ACTION7"` added to `ENGINE_TO_MODEL_ACTION`. The label is opaque on purpose: what ACTION7 does is for each world to show, not for the harness to name. | +3 |
| `ARC3-Inference/inference/agent/controller_turn.py` | `ControllerSession.stalled` counts consecutive controller turns that executed no action, from either a gate refusal or an environment refusal. Any executed action resets it to 0. The new `rest_if_stalled()` is called once per turn, beside `rest_if_no_legal_move()`. At `MAX_STALLED_CONTROLLER_TURNS = 3` it calls `play_gate.rest_in_play()`, with a reason naming the gate and the last refusal. No new logic sits inside an existing function body; the hook is a single call. | +27 |
| `ARC3-Inference/inference/framework/solver.py` | `HarnessSolver.rest_on_controlled_stop: bool = False`. `_HarnessGameSession._rest_after_controlled_stop()` rests the level in normal play once, when the flag is set, the stop is not fatal, and the gate is not already `PLAY-NORMAL`. It also writes the reason to the transcript. `_idle_backoff()` waits 0.05 s × n after the second consecutive turn that executed nothing, up to 1 s. Each is hooked by one line into the session loop. | +38 |
| `tools/package_ring9_submission_v1.py` | The submission run cell and the benchmark pickle set `rest_on_controlled_stop = True`. Four SUB-2 markers are checked, so the packager refuses source without them. The dry-run package is now `ring9-submission-dryrun-v2`, so it cannot collide with v1's dataset. | +15 / −2 |
| `ARC3-Inference/tests/test_sub2_submission_hardening.py` | New: 8 tests (§2) | +191 |

**Resting is not closing.** `rest_in_play` is R9-R24 D22's existing mechanism for a gate with no legal move. The gate's products stand, the level's ladder rests, and Duck plays freely with everything certified. Every transition is still recorded and receipted FREE_PLAY. A new level builds new adapters, so the next level's ladder starts again from G0.

## 2 · Tests: fail-first, then pass

`tests/test_sub2_submission_hardening.py` has 8 tests. Against the base source all 8 fail; with SUB-2 all 8 pass.

| Test | Shows |
|---|---|
| `test_d1_action7_is_a_harness_action_with_an_opaque_label` | `to_engine_action("ACTION7") == "ACTION7"`; the model label is `ACTION7` |
| `test_d1_the_solver_accepts_an_action7_step` | `_normalize_actions` builds `GameAction.ACTION7` and no longer says "Unknown action" |
| `test_d2_a_refused_controller_probe_rests_the_level_instead_of_spinning` | The dry run's own sequence. The environment refuses the probe, and replaying its consumed token is refused too. After 3 stalled turns the level rests in play, the next turn is Duck's, and the refused action reached the environment exactly once. |
| `test_d2_an_executed_action_resets_the_stall_count` | Interleaved refusals and executions never trigger the rest |
| `test_d2_the_solver_loop_backs_off_on_turns_that_execute_nothing` | The first idle turn costs nothing; repeats wait longer each time, capped at 1 s |
| `test_d3_in_submission_mode_a_controlled_stop_rests_the_level_in_play_once` | The level rests, with the reason in the gate and the transcript. A second stop while in play is not rested, so the game ends. |
| `test_d3_outside_submission_mode_a_controlled_stop_still_ends_the_game` | With the flag off, the behaviour is unchanged (`_turn_ends_game` still ends) |
| `test_d3_an_ordinary_turn_is_untouched` | A turn with no controlled stop is never rested |

## 3 · Verification

| Check | Result |
|---|---|
| The SUB-2 tests | 8 failed against the base source; 8 passed with the fix |
| Full suite on the SUB-2 tree | **627 passed, 1 skipped** (619 + 8 new), 19 min |
| **Director's Mac floor** (worktree, 2026-10-08) | **627 passed, 1 skipped**, 14 warnings (matplotlib and pyparsing deprecations only), 876 s |
| ruff on the changed files | clean |
| Trial dry-run package from the SUB-2 tree | Builds; secret guard clean; 230 source files; the SUB-2 markers pass |
| Submission mount simulation, both branches (zip) | Dry run: 110 unique ids, concurrency 10, soft end at launch + 2 h. Rerun: soft end at start + 8 h 35 min. `rest_on_controlled_stop = True` is in the run cell and in the pickled solver. |
| Rebuilt base | Each file changed since `d751a5b` was taken from the worktree and checked against its git blob at `2cfdbf1`. All 5 match. |

## 4 · What SUB-2 does not change

- **The canary packager.** Canaries keep `rest_on_controlled_stop = False`: a canary is a diagnosis, and a clean stop is its evidence.
- **G1's coverage logic.** A world that offers an action the environment then refuses still costs up to 3 stalled turns. After that the level rests in play rather than spinning. With D-1 fixed, the dry run's only trigger is gone.
- **The cause of the G1 contract stop** (Duck's click-only explanation, rejected twice before any action; sb26 in the dry run). Under D-3 that game now plays freely instead of ending at 0 actions. Whether the explanation turn should precede the first action at all is an architecture question for the click line. It is recorded, not built.

## 5 · Next

1. The Director commits SUB-2 on `ring9-unified` (explicit paths), fast-forwards `main`. The Mac floor already passed on the worktree: 627 passed, 1 skipped, which is 619 + 8.
2. **The scored package:** `ring9-submission-v1`, from `main` with SUB-2 and Sol's `4970953`. Kaggle's interactive save run of that notebook is its rehearsal: 110 clones, 2,700-s slices, the dry-run path.
3. **A separate `ring9-submission-dryrun-v2`** is optional. It is built and verified on request.

— Claude, Alpha build seat (click line), 2026-10-07

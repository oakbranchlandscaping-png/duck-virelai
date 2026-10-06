# Build slice SUB-1: submission mode for the first scored submission

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat), signed
**Governs:** `DIRECTIVE_COMPETITION_ENDGAME_v2` D-2 (play every hidden game inside the run, slice the time per game, hold a hard guard on the deadline), D-3 (Qwen3.6-27B through the first submission), D-4 (first scored submission by about 12 October).
**Plan:** `BUILD_PLAN_PORTS_AND_PILLARS_v1` §1 Track S, as replanned below; `RECORD_RING9_SINGLE_TREE_AGREEMENT_v1` §4 step 4″ (submission mode in new files, by Claude).
**Base:** `main` @ `232a502` (source identical to `b06fa68`); `ring9-unified` @ `d0635e7` (documents only beyond `main`).
**Altitude:** code-level, under existing rulings. It needs no edit to a shared source file, so no gate-machine hook (Sol's ownership review) is on this slice's path.

## 0 · In one paragraph

A diagnostic of the source, the harness and the packaged notebook found three things:
- **Most of submission mode already exists in the Duck harness.** That covers concurrent games on a thread pool, a soft end with per-game stops, the competition rerun's gateway path, and a local competition-arcade simulator.
- **The track plan's S-5 and S-7 are already delivered by R9-R24:** normal play receipted `FREE_PLAY`, and the harness-labelled refusal of known no-ops.
- **One defect would have failed the first submission outright.** Every Ring 9 notebook so far checks the game list against a fixed world allowlist. In a competition rerun the games come from the gateway, so that check, and the receipt check after it, would raise before the first action.

This slice fixes the defect in the packaged notebook, adds two test files that pin concurrency and the deadline, and packages a dry run and the submission. A local rehearsal (no GPU, stand-in model) ran the real submission path end to end.

## 1 · Diagnostic (read-only, before any change)

| Item | Found | Where |
|---|---|---|
| Concurrent games | The harness runs games on a `ThreadPoolExecutor` sized to `concurrency`, behind an `asyncio.Semaphore` | `inference/framework/solver.py:1142-1197` |
| Run deadline, per-game slice, action cap | `should_stop()` stops on the soft end, the per-game runtime (`max_runtime_s_per_game`) and the action cap; `request_timeout_seconds()` cuts a model request to the nearest limit | `solver.py:399-460` |
| Rerun path | `KAGGLE_IS_COMPETITION_RERUN` sets `TRUE_SUBMISSION`, waits for the gateway and builds the games from the live competition Arcade | packaged notebook, cells 2 and 14 |
| Local competition simulator | `CompetitionArcadeServer`: the 25 public games cloned to 110 runs, on a local gateway-shaped server with one scorecard and hidden baselines | `tufa-arc-agi-framework/src/taaf/competition_arcade.py` |
| Context guard | Every request is trimmed to the context budget, oldest history first | `inference/agent/tool_agent.py:2830-2848` |
| Turn clock | 60 s per Duck turn on Kaggle (`LOCAL_ANALYZER_YIELD_SECONDS`) | `inference/framework/kaggle.py:115` |
| S-5 free play, S-7 known no-ops | Delivered by R9-R24: `PLAY-NORMAL`, `FREE_PLAY` receipts, and R-8's harness-labelled refusal. v8 exercised them live. | `play_gate.py` |
| **Defect** | In a rerun the run cell compares the gateway's games with the checkpoint's world allowlist (`actual_worlds != expected_worlds`), then binds `"worlds": actual_worlds` into the receipt check. **Both raise before the first action.** Every packaged notebook since `ring9-g4-exit-v1` carries this. | run cell (14) |
| Soft end | Fixed at "now plus the behaviour window" after model setup. A rerun's wall clock starts with the notebook, so setup time must count against it. | run cell (14) |
| Settings | `concurrency = 1`, one world, budgets per world | run cell (14) and the benchmark pickle |

**Correction to `REVIEW_RING9_CARRY_VC33_V8` F-v8-3.** The 57,193-token play prompt was not unguarded. `_trim_messages_for_context` drops the oldest history whenever a request would exceed the context budget. Overflow is prevented by design; what remains is only that a long play turn loses its early history. No code change is needed for the first submission.

## 2 · What is built (new files only)

| File | What |
|---|---|
| `ARC3-Inference/tests/test_s1_concurrent_replay.py` | **S-1.** Five live records (ft09 ×3, vc33 ×2) are replayed one after another, then all at once on a thread pool with the order interleaved. Each game's digest (record rows, products, gate, step counts) must be identical. **Fail-first:** a module-level cache injected only in the test (the first game to decode a board wins for every game) makes at least two games differ. 2 passed. |
| `ARC3-Inference/tests/test_s2_run_deadline.py` | **S-2.** With fixed clocks: a game with time and actions left stops at the run's soft end; a game stops at its own slice and at its action cap; a model request is cut to the nearest of the three limits, with a floor of 0.1 s. 5 passed. These pin existing behaviour; there was no defect to fail first. |
| `tools/package_ring9_submission_v1.py` | The canary packager with a submission run cell: `VIRELAI_SUBMISSION_MODE=dryrun` or `submit` (§3, §4) |
| `tools/simulate_kaggle_submission_mounts.py` | The mount simulation, run through the submission run cell in either branch, with the Arcade stubbed by clones (`SIM_GAMES`; `SIM_TRUE_SUBMISSION=1` for the rerun branch) |

### The submission run cell

The packager rewrites six places in the base run cell. Each base text must occur exactly once, and the result must no longer contain the old allowlist code.

| # | Change |
|---|---|
| 1 | **The world allowlist becomes a contract.** It reads `checkpoint["submission"]` instead. |
| 2 | **The dry run's game list** is a `CompetitionArcadeServer` (110 clones) started on the competition dataset's `environment_files`, then the same `_competition_games()` a rerun uses. |
| 3 | **The world check becomes a count check:** a non-empty list with no repeated id; in the dry run, exactly 110. |
| 4 | **Concurrency:** `bm.solver.concurrency = 10`. |
| 5 | **Receipt worlds:** `"COMPETITION"`. |
| 6 | **Soft end.** In a rerun: the notebook's start + 32,400 s − 1,500 s. In the dry run: 2 h after setup. The notebook prints it. |

## 3 · Settings: proposed, for the Director to rule

| Setting | Submission | Dry run | Basis |
|---|---|---|---|
| Concurrency | **10** | 10 | The model server's own figure: 10.12 concurrent requests at the full 65k context (DIAG_R5 §1). Games spend almost all their time in Duck turns (v6: 647 of 659 s). |
| Per-game slice | **2,700 s (45 min)** | 600 s | 110 games × 45 min ÷ 10 = 495 min. The rerun's window after about 9 min of setup and a 25-min exit margin is about 506 min. |
| Action cap per game | **400** | 400 | High enough that the slice, not the cap, ends a game. v8 used 200 actions in 47.5 min with one game on the GPU. |
| Run wall / exit margin | 9 h / **25 min** | — | D-2's 9-hour run (**the Kaggle runtime limit is still to be confirmed**). The margin covers teardown and scoring. |
| Model admission (S-3) | **Not in SUB-1** | — | With 10 concurrent games, the server's own batching is the admission. Franzen's priority gate is an optimisation for a later weekly submission. |

## 4 · Verification so far

| Check | Result |
|---|---|
| S-1, S-2 on the unified source (cloud) | 2 + 5 passed |
| Trial packages from the `b06fa68` export | dry run and submit both build, secret guard clean, 230 source files |
| Submission mount simulation, `zip` layout, both packages × both branches | All four reach the benchmark launch: manifest verified (230 files); `competition games verified: 110 unique ids`; receipt verified; concurrency 10; gated; Qwen3.6. Dry run: soft end = launch + 2 h. Rerun branch: soft end = notebook start + 8 h 35 min. |
| **Local rehearsal** (no GPU) | Details below. |

**The local rehearsal:**
- **Setup.** The dry-run package's own benchmark pickle and solver ran under a real `CompetitionArcadeServer`, with 2 public games (`ft09-0d8bbf25`, `ls20-9607627b`) cloned to 6 runs. The notebook's `_competition_games()` was used verbatim. Concurrency 3, slice 45 s, window 240 s, with a stand-in model that answers instantly with no tool call.
- **Result.** It finished in 105 s with no harness error. All 6 clones (`k000`–`k005`) started, played and were finished by the harness.
  - The ft09 clones stopped at their slice (`gave_up`).
  - The ls20 clones were ended by the harness's own guard after 2 tool-less model replies, which is the stand-in's doing. A real model calls tools.
- **Separation.** Each clone has its own 8 artifacts. None names another clone.
- **Environment files.** They came from the Director's disk (`Universal_Solver_v3_5/environment_files`). They were used only as the arcade's environment directory and were not opened or read.

## 5 · The dry run (Director runs it; GPU about 2.3 h)

- **Package:** `ring9-submission-dryrun-v1`, built from the commit that lands this slice.
- **Settings:** 110 clones, concurrency 10, 600-s slices, a 2-h window.
- **Criteria:** C-1 to C-7, preregistered in the package (`RUN.md`):
  - no crash;
  - every game receipted GATED or FREE_PLAY;
  - no cross-game mixing;
  - the run ends before the soft end with no request in flight;
  - turns cut by the clock reported under 10-way contention;
  - prompt tokens under the window;
  - vc33 clones clearing level 1, as v8 did.

The dry run tests the machinery under contention. Its scores mean little: a 10-minute slice ends most games early in the ladder.

## 6 · Then the submission

- **Package:** `ring9-submission-v1`, from the same commit, if the dry run passes.
- **Settings:** the 45-min slice and the rerun's own deadline.
- **Submitting:** the Director submits the notebook version to `arc-prize-2026-arc-agi-3`. The exact Kaggle submission step, and the four open Kaggle facts (runtime limit, submissions per day, quota, whether reruns count), are checked before that push.

— Claude, Alpha build seat, 2026-10-06

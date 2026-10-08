# Upload status: ring9-submission-v1 (the first scored ARC-AGI-3 submission)

**Date:** 2026-10-08
**Author:** Claude (Alpha build seat, click line), signed
**Packager:** `tools/package_ring9_submission_v1.py` with `VIRELAI_SUBMISSION_MODE=submit`. Its provenance text is amended in this delivery (§3).
**Governs:**
- `DIRECTIVE_COMPETITION_ENDGAME_v2`: D-2 (play every hidden game, slice the time, guard the deadline), D-3 (Qwen3.6-27B) and D-4 (first scored submission by about 12 October);
- `BUILD_SLICE_SUB_1_SUBMISSION_MODE`;
- `BUILD_SLICE_SUB_2_SUBMISSION_HARDENING`;
- the Director's rulings of 2026-10-07: D-3 free play, and SUB-2 built.

**Source:** `main` = `ring9-unified` @ `419f4fda8756ee276e158fe415565300581fddc7`. Its runtime source is SUB-2 `a2200c2`, which adds documents only on top. Mac floor at that source: **627 passed, 1 skipped**.

## 1 · Identity

| | |
|---|---|
| Package | `kaggle/ring9-submission-v1` (237 files; 230 source files) |
| Package manifest sha256 | `2762159d3af7fdc904520f42568ed13965804cdb687483234e85f3a94a34ca32` |
| Source manifest sha256 | `ba1ab5d5a2bb1cea0b59658baed17e21ba5463fd5ae655999cadee4fae7c733f` |
| Execution receipt sha256 | `a650390feb461cd61774e0bd8f800fb4856c9817542bfe4692b2c593f987b221` |
| Source export | `runs/_cowork_xfer/unify/export_419f4fd.tar.gz`, sha256 `a729f680…6934dad2` (Director's `git archive`; matches the cloud copy) |
| Delivery | `runs/_cowork_xfer/unify/sub_v1/ring9-submission-v1.tar.gz`, sha256 `410e53cc…6ccd459d` |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-submission-v1` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-submission-v1`. Competition source `arc-prize-2026-arc-agi-3`; offline; GPU `NvidiaRtxPro6000`; pinned Python 3.12 image. |
| Dependencies | `stephenkaskin/virelai-vllm-wheelhouse-v3`; `stephenkaskin/virelai-qwen3-6-27b-fp8` (`vrfai/Qwen3.6-27B-FP8`) |

**What the notebook does in each branch:**
- **In a competition rerun** (`KAGGLE_IS_COMPETITION_RERUN`): it plays the live competition Arcade at the Kaggle gateway, 10 games at a time. Each game is stopped at 2,700 s or 400 actions. The soft end is the notebook's start + 32,400 s − 1,500 s (8 h 35 min).
- **Run interactively** (Kaggle's save run): it plays the competition-arcade simulator, 110 clones of the 25 public games, with the same slices, inside a 2-h window. This is the rehearsal.
- **In both branches:**
  - gated mode with the controller executor on;
  - `rest_on_controlled_stop = True` (D-3: a controlled stop rests the level in free play once);
  - the SUB-2 stall guard;
  - ACTION7 mapped.

## 2 · Verification (cloud)

| Check | Result |
|---|---|
| Export against the tested SUB-2 tree | File for file identical (the only difference is a ruff cache in the cloud copy) |
| `main`'s `verify_kaggle_package.py --source-export export_419f4fd` | **9/9**, 0 differences from the commit export |
| Packager guards | Secret guard clean. Single-tree and SUB-2 markers present (ACTION7, `rest_if_stalled`, `_rest_after_controlled_stop`, the solver flag). Six run-cell edits, each base text found once. |
| Submission mount simulation | **5/5:** rehearsal branch in zip, nested and direct layouts; rerun branch in zip and nested. All of them show `source manifest verified (230 files)`, `competition games verified: 110 unique ids`, concurrency 10, 400 actions, 2,700 s, gated, Qwen3.6. The rehearsal's soft end is launch + 2 h; the rerun's is notebook start + 8 h 35 min. |
| D-3 setting | `bm.solver.rest_on_controlled_stop = True` in the run cell, and `True` in the pickled solver |
| Full suite at the source | Cloud 627 passed, 1 skipped; Mac 627 passed, 1 skipped |

**The rerun's time budget:**
- **Planned play:** 110 × 2,700 s ÷ 10 = 8 h 15 min, if every game uses its whole slice.
- **Available:** about 8 h 23 min, between about 12 min of setup and the soft end at 8 h 35 min.
- **The guard:** the soft end stops any game still running, so the notebook ends inside the 9 h limit with 25 min to spare.
- **The effect of D-3:** games play on instead of ending early, so more of them will use their whole slice than in the dry run.

## 3 · Change to the packager (provenance text only)

The submission packager's `REVISIONS` and `TEST_RESULTS` now name everything this package carries:
- Sol's cell-site targeting (`4970953`, with its 619 floor at `c5e8ff6`);
- the dry run's findings;
- SUB-2 (`a2200c2`), with its tests and the 627 floor.

No logic changed relative to the SUB-2 commit. The amended packager must be committed with this record.

## 4 · Preregistered criteria (in the package's `RUN.md` and `checkpoint-preflight.json`)

The criteria are the dry run's: C-1 to C-7, R, I0, I2, I3, I5, I8, I11 and U-SRC.

**For the rehearsal (the save run)**, graded as the dry run was, with three additions:
- **D-1:** no "Unknown action" in any game.
- **D-2:** no game with more than 3 consecutive stalled controller turns.
- **D-3:** controlled stops are counted with the gate they rested.

**For the scored rerun:** the competition returns only the score. What counts there is that the rerun completes and posts a score.

## 5 · Director's steps (on the Mac)

1. Unpack the package into `kaggle/` and the export into `runs/_cowork_xfer/unify/export_419f4fd` (with its `.source-commit` stamp). Never stage `kaggle/`.
2. Verify the package with `main`'s `tools/verify_kaggle_package.py --source-export`. Expect 9/9.
3. Commit this record and the amended packager on `ring9-unified`, push, then fast-forward `main`.
4. Upload:
   1. `kaggle datasets create -p kaggle/ring9-submission-v1/source-dataset -r skip`;
   2. wait for `ready`;
   3. `kaggle kernels push -p kaggle/ring9-submission-v1/kernel`.

   That starts the save run, which is the rehearsal: about 2.3 GPU-hours.
5. **Gate on two things before submitting:**
   - **(a)** the rehearsal completes and its output passes the checks above;
   - **(b)** Sol's ls20 cell-site canary has been graded.

   Then confirm the Kaggle facts on the Rules tab: the runtime limit, submissions per day, and whether a failed rerun counts.
6. **Submit** that notebook version, either:
   - from the notebook page ("Submit to Competition"), or
   - with CLI 2.2.2: `~/.venvs/kaggle222/bin/kaggle competitions submit arc-prize-2026-arc-agi-3 -k stephenkaskin/taaf-virelai-ring9-submission-v1 -v <version> -m "<message>"`.

   The CLI 2.2.2 `-k` and `-v` options were checked against its `competitions submit -h`.

— Claude, Alpha build seat (click line), 2026-10-08

## Upload log (2026-10-08, Director's terminal)

| Step | Result |
|---|---|
| Unpacked on the Mac | `kaggle/ring9-submission-v1` from `sub_v1/ring9-submission-v1.tar.gz`. The export went to `runs/_cowork_xfer/unify/export_419f4fd`, stamped `419f4fda8756…`. |
| Mac verify (`main`'s verifier, `--source-export export_419f4fd`) | **9/9:** source manifest 230 files, package manifest 237, `src.zip` 221 files, output-cap encoding `server_default` on both sides, secret scan clean, 0 differences from the commit export |
| Commit | `eac248f` on `ring9-unified`: this record and the amended packager, explicit paths, 2 files, +105 −1. Pushed `419f4fd..eac248f`. `main` fast-forwarded `419f4fd..eac248f` and pushed. The runtime source is unchanged, so the 627 floor stands. |
| `kaggle datasets create -p kaggle/ring9-submission-v1/source-dataset -r skip` | 12 files uploaded: `src.zip` 968 KB, `source-manifest.json` 28 KB, `setup_commands.json` 10 KB, `checkpoint-preflight.json` 6 KB, and 8 small files. Private. |
| `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-submission-v1` | `ready` |

**CLI notes (expected):** "Skipping folder: src" (the source travels as `src.zip`), and the 2.0.0 version warning.

| Step | Result |
|---|---|
| `kaggle kernels push -p kaggle/ring9-submission-v1/kernel` | `Kernel version 1 successfully pushed`. The save run (the rehearsal) is running at `stephenkaskin/taaf-virelai-ring9-submission-v1`. |

**Next:**
1. When the save run completes, download the output without the replay movies (CLI 2.2.2, `--file-pattern '^(?!movies/).*'`).
2. Grade the rehearsal (§4).
3. Submit version 1 only after the rehearsal passes, Sol's ls20 canary is graded, and the Kaggle Rules tab is checked.

## Amendment under RULINGS_CONSOLIDATION_v1_2026-10-08 (Director-ratified 2026-10-08)

Ruling 8 replaces the gate in §5 and in "Next" item 3. **Sol's ls20 canary is not a blocker.** The submission now gates on two things only:
1. the rehearsal (save run, kernel version 1) passes §4;
2. the Director confirms the Kaggle facts on the Rules tab: the runtime limit, submissions per day, and whether a failed rerun counts.

Ruling 10 also applies. The rehearsal grade reads the run's logs and receipts against §4. No report compiler runs on the save-run output until the Director's 25 answer keys are committed.

— Claude, Alpha build seat (click line), 2026-10-08

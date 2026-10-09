# Upload status: ring9-submission-v2 (the second scored ARC-AGI-3 submission)

**Date:** 2026-10-09
**Author:** Claude (Alpha build seat, click line), signed
**Packager:** `tools/package_ring9_submission_v2.py`, committed in `fc152e6`, run with `VIRELAI_SUBMISSION_MODE=submit`. This delivery amends its provenance text only (§3).
**Governs:**
- `BUILD_SLICE_SUB_3_FREE_PLAY_OUTCOME_2026-10-09.md`;
- the Director's choice of option B (cap 1,000);
- `RULINGS_CONSOLIDATION_v2_2026-10-08` (ruling 13 sets the timing; the noted item asks for at least 20 minutes of margin);
- Kaggle facts confirmed by the Director on 2026-10-09: 2 submissions per 24 hours, and a failed run does not count.

**Source:** `main` = `ring9-unified` @ `fc152e6e581dd2257aa466e2cf35cdcc15566d2a`. This is SUB-3 on top of SUB-2's runtime. Mac floor at that source: **630 passed, 1 skipped**.

## 1 · Identity

| | |
|---|---|
| Package | `kaggle/ring9-submission-v2`: 237 manifest files, 230 source files |
| Package manifest sha256 | `00117417bbcda33c56ef35a7da08ccd30222859c475260625e50b87efd3f657f` |
| Source manifest sha256 | `8875e8e0c44c038380f5383b60853bd010344b47b8d1e184b3c4edefd6cdda6c` |
| Execution receipt sha256 | `edda02b928e695b8667bf8a20759f30189d73fc02c4c2cf8c9bde3f95964e5ea` |
| Source export | `runs/_cowork_xfer/unify/export_fc152e6.tar.gz`, sha256 `92fe322a…26fbdc3dc` (made with `git archive` on the Director's Mac) |
| Delivery | `runs/_cowork_xfer/unify/sub_v2/ring9-submission-v2.tar.gz`, sha256 `cac19cde…6589dc799` |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-submission-v2` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-submission-v2`. Same image, GPU, wheelhouse and model as v1. |

**Settings compared with v1:**

| Setting | v1 | v2 |
|---|---|---|
| Action cap | 400 | **1,000** |
| Per-game slice | 2,700 s | **2,550 s** |
| Concurrency | 10 | 10 |
| Rerun soft end | start + 8 h 35 min | start + 8 h 35 min |
| D-3 free play | on | on |

**Rerun time budget:**
- Worst case: all 110 games use their full slice, in 11 waves of (2,550 + 45 s), about 28,545 s.
- Play can start after 843 s of setup (the rehearsal's measurement), and the soft end is at 30,900 s. That leaves 30,057 s.
- So the margin is about 25 minutes, against v1's 8.

## 2 · Verification (cloud)

| Check | Result |
|---|---|
| Export against the tested SUB-3 tree | Identical file for file |
| `main`'s `verify_kaggle_package.py --source-export export_fc152e6` (`main`'s copy, sha256 `a14b9206…`) | **9/9**, 0 differences from the commit export |
| Packager guards | Secret guard clean. Single-tree, SUB-2 and SUB-3 markers present. |
| Submission mount simulation | **5/5:** the rehearsal branch in zip, nested and direct layouts; the rerun branch in zip and nested. Each shows `source manifest verified (230 files)`, 110 unique ids, concurrency 10, 1,000 actions, 2,550 s, gated mode, and Qwen3.6. The rehearsal's soft end is launch + 2 h; the rerun's is start + 8 h 35 min. |
| Pickled solver | `max_actions_per_game` 1,000; `max_runtime_s_per_game` 2,550.0; `rest_on_controlled_stop` True. The run cell sets it too. |
| Full suite at the source | Cloud: 630 passed, 1 skipped. Mac: 630 passed, 1 skipped. |

## 3 · Packager provenance (text only)

`REVISIONS` now names `SUB-3 fc152e6`. `TEST_RESULTS` adds the cloud and Mac floors at `fc152e6`. No logic changed. The amended packager must be committed with this record.

## 4 · Preregistered criteria (from `RUN.md`)

The criteria are the v1 set, with these changes:
- **C-4, reworded.** The 2-h rehearsal cannot fit 110 games of 2,550 s, so it now checks three things: any game still playing at the soft end is cancelled cleanly with its artifacts written; the benchmark closes within 5 minutes of the soft end; and the notebook ends within the exit margin.
- **D-1 to D-3, carried forward from v1:**
  - no "Unknown action";
  - no more than 3 consecutive stalled turns;
  - controlled stops counted with the gate they rested.
- **S-3, new:**
  - no executed free-play action is reported to Duck as failed;
  - free-play turns are ledgered as executed;
  - every `sandbox host hid` line in the kernel log is counted by type and site.
- **W, new:** output size per world, and the 110-game rerun's projected working-directory use (size per world × clone count). The 1,000-action cap must not put the rerun at risk of filling the disk.

## 5 · Director's steps (on the Mac)

1. Unpack the package into `kaggle/` and the export into `runs/_cowork_xfer/unify/export_fc152e6`, with its `.source-commit` stamp. Never stage `kaggle/`.
2. Verify with `main`'s `tools/verify_kaggle_package.py --source-export`. Expect 9/9.
3. Commit this record and the amended packager on `ring9-unified` with explicit paths, push, and fast-forward `main`.
4. Upload:
   1. `kaggle datasets create -p kaggle/ring9-submission-v2/source-dataset -r skip`;
   2. wait for `ready`;
   3. `kaggle kernels push -p kaggle/ring9-submission-v2/kernel`.

   The push starts the save run, which is the rehearsal (about 2.3 GPU-hours).
5. Grade the rehearsal against §4. If it passes, submit version 1 of the notebook. A failed scored run does not count against the two per day.

— Claude, Alpha build seat (click line), 2026-10-09

## Upload log (2026-10-09, Director's terminal)

| Step | Result |
|---|---|
| Unpack on the Mac | `kaggle/ring9-submission-v2` from `sub_v2/ring9-submission-v2.tar.gz`. The export went to `runs/_cowork_xfer/unify/export_fc152e6`, stamped `fc152e6e581d…`. |
| Mac verify (`main`'s verifier, `--source-export export_fc152e6`) | **9/9.** Source manifest 230 files; package manifest 237; `src.zip` 221 files; output-cap encoding `server_default` on both sides; secret scan clean; 0 differences from the commit export. |
| Commit | `e917f75` on `ring9-unified`: this record and the amended packager, staged by explicit paths (2 files, +96 −2). Pushed `fc152e6..e917f75`; `main` fast-forwarded to `e917f75` and pushed. The runtime source is unchanged, so the 630 floor stands. |
| `kaggle datasets create -p kaggle/ring9-submission-v2/source-dataset -r skip` | 12 files uploaded: `src.zip` 968 KB, `source-manifest.json` 28 KB, `setup_commands.json` 10 KB, `checkpoint-preflight.json` 6 KB, and 8 small files. Private. |
| `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-submission-v2` | `ready` |

**CLI notes (expected):** "Skipping folder: src", because the source travels as `src.zip`; and the version warning from CLI 2.0.0.


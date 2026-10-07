# Upload status: ring9-submission-dryrun-v1 (submission mode under contention, 110 clones)

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_submission_v1.py` with `VIRELAI_SUBMISSION_MODE=dryrun`. Its provenance text is amended in this delivery (§3).
**Plan:** `BUILD_SLICE_SUB_1_SUBMISSION_MODE_2026-10-06.md` §5, with the settings the Director ratified on 2026-10-06.
**Source:** `main` = `ring9-unified` @ `d751a5bce79eb76603403b7721034536d4fe145d`. That is the merge `501a6e6`, plus F1 `fa9617b`, plus Sol's step 4′ (`b04ad10..e8d1f92`), plus SUB-1 `d751a5b`.

## 1 · Identity

| | |
|---|---|
| Package | `kaggle/ring9-submission-dryrun-v1` (237 files; 230 source files) |
| Package manifest sha256 | `4ffb774b7f5d3f4673da256adad18a410c3fb6d765d3cfae43a0148d994ba37f` |
| Source manifest sha256 | `d367b3a1f5e8d27623f463a44ce48cd72ba403d1a272ee651d9ba334966ecbaa` |
| Source export | `runs/_cowork_xfer/unify/export_d751a5b.tar.gz`, sha256 `17cf5663…8e08ea11` (Director's `git archive`; the cloud copy's hash matches) |
| Delivery | `runs/_cowork_xfer/unify/sub1dry/ring9-submission-dryrun-v1.tar.gz`, sha256 `a8b38034…353357e` |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-submission-dryrun-v1` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-submission-dryrun-v1` (competition source `arc-prize-2026-arc-agi-3`; offline; GPU `NvidiaRtxPro6000`; pinned image `sha256:37c64f7d…`) |
| Dependencies | `stephenkaskin/virelai-vllm-wheelhouse-v3`, `stephenkaskin/virelai-qwen3-6-27b-fp8` (`vrfai/Qwen3.6-27B-FP8`) |
| Settings | 110 clones of the 25 public games on the harness's competition-arcade simulator; 10 at a time; each game stopped at 600 s or 400 actions; soft end 2 h after model setup; gated mode; controller executor on |
| Expected GPU | About 2.3 GPU-hours: about 14 min of setup, the 2-h window, then teardown. 110 × 600 s ÷ 10 = 6,600 s of play fits inside the 7,200-s window, so every clone should get its slice. |

## 2 · Verification (cloud)

| Check | Result |
|---|---|
| Full suite on the `d751a5b` export, cloud Python 3.12 | **617 passed, 1 skipped** (618 collected). It ran in two parts: a session time limit killed the first run after 471 passed and 1 skipped, and the remaining 146 then ran and all passed. This matches the Director's Mac floor at `d751a5b`. |
| Export against `b06fa68` | The only source differences are Sol's step 4′ files (`g3_inventory.py`, `memory_store.py`, `record_replay.py`, `virelai_gates.py`, `tools/record_from_artifacts.py`, the tests and the ls20 fixture), plus the SUB-1 tests. |
| `main`'s `verify_kaggle_package.py --source-export export_d751a5b` | **9/9**: manifests re-derive (230 and 237 files), receipts identical, `src.zip` byte-identical (221 files), offline GPU kernel, secret scan clean, output-cap encoding `server_default`, 0 differences from the commit export |
| Packager guards | Secret guard clean. All unified-tree markers and the six run-cell rewrites applied, each base text found exactly once. No bytecode in the package. |
| Submission mount simulation, dry-run branch | **3/3 layouts** (zip, nested, direct): `source manifest verified (230 files)`; dry-run competition arcade started; `competition games verified: 110 unique ids`; receipt verified; concurrency 10; 400 actions, 600 s; gated; Qwen3.6; soft end = launch + 2 h |
| Same, rerun branch (`KAGGLE_IS_COMPETITION_RERUN` set) | zip layout: 110 unique ids from the gateway path; soft end = notebook start + 8 h 35 min |
| Request preflight (T10) | Worst case for one request: 33,161 tokens, against the 65,536-token window |

## 3 · Change to the packager (provenance text only)

The committed packager's `TEST_RESULTS` text said the Mac pytest at `f86d6ef` was "same source as this commit". For a `d751a5b` package that is false. Its `REVISIONS` line also left out step 4′ and SUB-1.

The amended packager changes two things:
- **`REVISIONS`:** now names `step 4' NAV record b04ad10..e8d1f92, SUB-1 d751a5b`.
- **`TEST_RESULTS`:** keeps the `f86d6ef` floor as history, and adds step 4′, the SUB-1 tests, and the floor at `d751a5b` (Mac and cloud, 617 passed, 1 skipped).

No logic changed. The diff against `d751a5b`'s packager is these two constants only. The package was built with the amended file, so the amended file must be committed with this record.

## 4 · Preregistered criteria

These are in the package's `RUN.md` and `checkpoint-preflight.json`, and are graded from artifact state.
- **C-1:** no crash. Every game starts, plays until its own stop, and is finished by the harness.
- **C-2:** every game has a gate record, and every transition is receipted GATED or FREE_PLAY. The review tabulates where each game's ladder rested.
- **C-3:** no artifact of one game carries another game's identity or evidence.
- **C-4:** the run ends before the soft end with no model request in flight, and the notebook ends within the exit margin.
- **C-5:** turns cut by the clock under 10-way contention are reported, per game and overall.
- **C-6:** the largest prompt per turn stays under 65,536 tokens.
- **C-7:** vc33 clones clear at least level 1, as v8 did.
- **R (reported):** per game, the gate where the ladder rested, actions, Duck turns and seconds, and levels cleared; overall, the engine score.
- **Infrastructure:** I0, I2, I3, I5, I8, I11 and U-SRC, as in the canaries.

**Reading the score.** The dry run's score is not a forecast. A 10-minute slice ends most games early in the ladder. It tests the machinery under contention.

## 5 · Director's steps (on the Mac)

1. Unpack the package into `kaggle/` in the main checkout, and the export into `runs/_cowork_xfer/unify/export_d751a5b` with its `.source-commit` stamp. Never stage `kaggle/`.
2. Verify the package with `main`'s `tools/verify_kaggle_package.py --source-export`. Expect 9/9.
3. In the worktree, on `ring9-unified`, commit the amended packager and this record (explicit paths) and push. Then fast-forward `main` and push. The solver source doesn't change, so the floor stands.
4. Run `kaggle datasets create -p kaggle/ring9-submission-dryrun-v1/source-dataset -r skip`. Wait for `ready`, then run `kaggle kernels push -p kaggle/ring9-submission-dryrun-v1/kernel`.

**What the log should show if it works:**
- `source manifest verified (230 files)`, Python 3.12 paths, the 174-wheel install, and vLLM serving `vrfai/Qwen3.6-27B-FP8`;
- `TRUE_SUBMISSION=False`, `dry-run competition arcade at http://127.0.0.1:…`, `competition games verified: 110 unique ids`, `G0-G4 execution receipt verified`, `controller executor on`;
- `soft end …` about 2 h after setup;
- 10 games in flight at a time, each ending on its slice, its action cap or a win;
- the notebook ending soon after the soft end.

## 6 · After the dry run

- **I grade it against C-1 to C-7.**
- **If it passes,** I build `ring9-submission-v1` from the same commit: a 2,700-s slice, and the rerun's own deadline.
- **Before the submission,** the Kaggle facts must be confirmed on the competition's Rules tab: the runtime limit (9 h assumed), submissions per day, the GPU quota, and whether a failed rerun counts against the day.

— Claude, Alpha build seat, 2026-10-06

## Upload log (2026-10-06, Director's terminal)

| Step | Result |
|---|---|
| Unpacked on the Mac | `kaggle/ring9-submission-dryrun-v1` from `sub1dry/ring9-submission-dryrun-v1.tar.gz`. The export went to `runs/_cowork_xfer/unify/export_d751a5b` with its `.source-commit` stamp (`d751a5bce79eb76603403b7721034536d4fe145d`). |
| Mac verify (`main`'s verifier, `--source-export export_d751a5b`) | **9/9:** source manifest 230 files, package manifest 237, `src.zip` 221 files, output-cap encoding `server_default` on both sides, secret scan clean, 0 differences from the commit export |
| Commit | `b1a4d71` on `ring9-unified`: this record and the amended packager, explicit paths, 2 files, +94 −3. Pushed `d751a5b..b1a4d71`. `main` fast-forwarded `d751a5b..b1a4d71` and pushed. The solver source is unchanged, so the floor (617 passed, 1 skipped at `d751a5b`) stands. |
| `kaggle datasets create -p kaggle/ring9-submission-dryrun-v1/source-dataset -r skip` | 12 files uploaded: `src.zip` 965 KB, `source-manifest.json` 28 KB, `setup_commands.json` 10 KB, `checkpoint-preflight.json` 5 KB, `execution_receipt.json`, `benchmark_initial.pkl`, `deploy_target.pkl` and 5 small files. Private. |
| `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-submission-dryrun-v1` | `ready` |

**CLI notes, both expected:**
- "Skipping folder: src": the source travels as `src.zip`, which the notebook checks against the manifest before it imports anything.
- "outdated kaggle version (installed 2.0.0, latest 2.2.2)": no upgrade is needed.

| Step | Result |
|---|---|
| `kaggle kernels push -p kaggle/ring9-submission-dryrun-v1/kernel` | Pushed by the Director. The notebook `stephenkaskin/taaf-virelai-ring9-submission-dryrun-v1` is **running** (Director's report, 2026-10-06; the push output was not pasted). |

**Expected:** about 2.3 GPU-hours (about 14 min of setup, the 2-h window, then teardown).

**Graded after download:**
- C-1 to C-7, I0 to I11 and U-SRC, per §4;
- per clone: the gate where its ladder rests, and its product;
- whether the NAV and HYBRID clones end with `G3_ROUTE_RETRY_EXHAUSTED`. That is the G1 bearing defect from the unified ls20 canary (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE`; `REVIEW_SOL_SINGLE_TREE_REPORT_v1` §4). This package predates the fix, so here it is measured, not graded as a regression.

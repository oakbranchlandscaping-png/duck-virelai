# Upload status: ring9-unified-vc33-v1 and ring9-unified-ls20-v1 (the single tree's first canaries)

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_unified_canary_v1.py` (`VIRELAI_CANARY=vc33` or `ls20`)
**Plan:** `RECORD_RING9_SINGLE_TREE_AGREEMENT_v1_2026-10-05.md`, §4 step 4 and §5 (Director-approved)
**Source:** `main` = `ring9-unified` @ `b06fa68d956de2c61a508f8a6500561d6293cda4`
- That is the merge `501a6e6`, plus F1 `fa9617b`, plus the document corrections `f86d6ef` and `b06fa68`.
- Mac test floor 607 passed, 1 skipped (at `f86d6ef`, whose source is identical).

## Director's rulings behind these packages (2026-10-05/06)

| Ruling | Content |
|---|---|
| F2a | CLICK G3 records the first witness and moves on (no confirmation repeat), as NAV does |
| Branch rule | All work commits to `ring9-unified`; `main` only fast-forwards after a Mac floor passes; canaries and submissions are packaged from `main` |
| ls20 budget | 160 actions and 2,700 s (Claude's figure, over Sol's 120 and 1,800 s) |
| Model | **Keep Qwen3.6.** Both canaries serve `vrfai/Qwen3.6-27B-FP8` from the Director's own datasets, on the pinned Python 3.12 image (directive D-3; the 2026-10-01 rule against depending on third-party datasets) |

**Finding behind the model ruling.**
- The NAV line's packages since 2026-10-03 served `Qwen/Qwen3.8-27B-FP8`, from third-party mounts (`mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3`, `mikedan7/qwen3-8-27b-fp8-official`), on an unpinned image. This was read from the committed `kaggle/ring9-g3-nav-n5-3-ls20-v1` setup commands and checkpoint.
- So the ls20 canary is the NAV line's first run on the Qwen3.6 model.
- Its gate machinery is comparable with N5.x; Duck's turns are not.
- The question of whether Qwen3.8 was a deliberate choice goes to Sol.

## Identity

| | vc33 (CLICK) | ls20 (NAV) |
|---|---|---|
| Package | `kaggle/ring9-unified-vc33-v1` (237 files; source 230) | `kaggle/ring9-unified-ls20-v1` (237 files; source 230) |
| Package manifest sha256 | `32900588d6580c41d7461dbcdd763648292de184c617ae68b6d2dd8f8deefba9` | `225250a25db585decddf6a4e970d34d9335ef04d845c42214735de5d2d77b5a7` |
| Source manifest sha256 | `ba766e813f5635e3bc4f807ee1d3b94b357e7da44e070b988e53d36da27d3d8f` | `4456de184fe1adb886b6a9677b464f3c50b3dd910b1f5535c6371f3267c32682` |
| World | `vc33-5430563c` | `ls20-9607627b` |
| Budget | 200 actions, 3,600 s | 160 actions, 2,700 s |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-unified-vc33-v1` | `stephenkaskin/taaf-duck-virelai-ring9-unified-ls20-v1` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-unified-vc33-v1` | `stephenkaskin/taaf-virelai-ring9-unified-ls20-v1` |
| Expected GPU | about 1.25 GPU-hours (about 14 min setup plus a 60-min window) | about 1.0 GPU-hour (about 14 min setup plus a 45-min window) |

**Shared by both packages:**
- the source export `runs/_cowork_xfer/unify/export_b06fa68.tar.gz`, sha256 `29d45b49…3a742d71`;
- the pinned image `gcr.io/kaggle-private-byod/python@sha256:37c64f7d…`;
- the wheelhouse `stephenkaskin/virelai-vllm-wheelhouse-v3` and the model `stephenkaskin/virelai-qwen3-6-27b-fp8`.

**Delivery:** both packages travel as `runs/_cowork_xfer/unify/ring9-unified-canaries-v1.tar.gz`, sha256 `54402c50…62db2cb0`.

## How the packager differs from v8

It is `package_ring9_carry_vc33_v8.py` with three changes:
1. **The source is the single tree.** `VIRELAI_SOURCE_COMMIT` is required and must be a full 40-character hash; there is no default.
2. **The world, budgets and criteria are the canary's.** The base notebook's budget lines (200 actions, 10,800 s) are checked once each, then replaced.
3. **Seven new marker checks** refuse any source that isn't the unified tree:
   - the "Unified G3 law" branch;
   - the legacy-replay flag;
   - F1's bounded set, which includes `PRESUMED_UNREACHABLE`;
   - the discovery schema;
   - `record_replay`'s protocol key;
   - `nav_route`;
   - the flag's GAME persistence tier.

All of v8's checks still apply: the secret scan, the world-name scan, the request size check, and the R9-R06 to R9-R24 markers.

## Preregistered criteria (full text in each package's `RUN.md` and `checkpoint-preflight.json`)

**vc33 (12 live criteria):**
- **U-G3:** every lever is found on its first witness, with no `CONFIRM_LEVER_WITNESS` probe. G3 actions per level are reported against v7's (v7 spent 13 confirmation actions over three levels).
- **U-L12:** whether levels 1 and 2 clear, and how. This is reported, not presumed. The first point where this run's actions diverge from v7's is named.
- **M5-1, M5-2:** card size, and zero model calls through G4.1.
- **X-1, X-3, L-1:** the level freeze and the life record.
- **I12, I13:** the mu bucket.
- **I14, I15, I16:** G4-B from the record, Duck's budget of 3 G4 turns, and normal play.
- **U-REPLAY:** the live record, replayed with legacy mode off, reproduces the live action sequence exactly, and then becomes a test fixture.
- **R:** reported figures.

**ls20 (8 live criteria):**
- **N-1 to N-6** are Sol's: the first witness, a bounded release, reopening only on a signature change, the roster completing, G3 closing and G4 opening, and no false rest in play.
- A run that hits its budget before the roster completes is diagnostic only.

**Both packages share 7 infrastructure criteria:** I0, I2, I3, I5, I8, I11 and U-SRC.

## Verification (cloud)

| Check | vc33 | ls20 |
|---|---|---|
| `verify_kaggle_package.py --source-export export_b06fa68` | 8/8 (0 differences from the commit export) | 8/8 (0 differences) |
| Mount simulation, three layouts | 3/3: 200 actions, 3,600 s, gated, Qwen3.6 | 3/3: 160 actions, 2,700 s, gated, Qwen3.6 |
| Secret check | clean | clean |
| Tamper test (one byte appended to `virelai_gates.py`) | — | refused (4 FAIL) |
| Bytecode in the package | none | none |

**Other checks:**
- The R9-R24 pre-flight on the packaged source (v7 record, 141) exits 0. Its output is byte-identical to the merge's.
- `test_ring9_unified_presumed_unreachable.py` and `test_g3_scheduler.py`, run against the packaged source: 18 passed.
- The export matches the source used for the dry run file for file. Its sha256 matches the Director's.

## Director's steps (on the Mac)

1. Unpack both packages into `kaggle/` in the main checkout. Never stage `kaggle/`.
2. Run `tools/verify_kaggle_package.py --source-export` on both packages against the unpacked export.
3. Commit this record and the packager on `ring9-unified` (in the worktree), push, then fast-forward `main` and push. The source doesn't change, so the floor stands.
4. For each canary, run `kaggle datasets create -p kaggle/<package>/source-dataset -r skip`. Wait for `ready`, then run `kaggle kernels push -p kaggle/<package>/kernel`.

v8 (on `c9b246b`) is still running. The canaries queue behind it, or beside it, as the quota allows.

— Claude, Alpha build seat, 2026-10-06

## Upload log (2026-10-06, Director's terminal)

| Step | Result |
|---|---|
| Unpacked on the Mac | `kaggle/ring9-unified-vc33-v1` and `kaggle/ring9-unified-ls20-v1` from the canary archive. The export was unpacked to `runs/_cowork_xfer/unify/export_b06fa68` with its `.source-commit` stamp. |
| Mac verify (`main`'s verifier, `--source-export export_b06fa68`) | **vc33 9/9, ls20 9/9:** source manifest 230 files, package manifest 237, `src.zip` 221 files, output-cap encoding `server_default` on both sides, secret scan clean, 0 differences from the commit export |
| Commit | `232a502` on `ring9-unified` (the packager and this record, explicit paths). Pushed; `main` fast-forwarded `b06fa68..232a502` and pushed. |
| `kaggle datasets create -p kaggle/ring9-unified-vc33-v1/source-dataset -r skip` | 12 files uploaded; `src.zip` 964 KB, `source-manifest.json` 28 KB, `checkpoint-preflight.json` 7 KB, `setup_commands.json` 10 KB. Private; "being created". |
| `kaggle datasets create -p kaggle/ring9-unified-ls20-v1/source-dataset -r skip` | 12 files uploaded; `src.zip` 964 KB, `source-manifest.json` 28 KB, `checkpoint-preflight.json` 5 KB (fewer criteria), `setup_commands.json` 10 KB. Private; "being created". |

**CLI notes, both expected:**
- "Skipping folder: src": the source travels as `src.zip`, which the notebook checks against the manifest before importing anything.
- "outdated kaggle version (installed 2.0.0, latest 2.2.2)": no upgrade is needed.

`src.zip` is 964 KB, against v8's 922 KB. The difference is the NAV line's modules, now in the single tree.

**Next, for each dataset:**
1. `kaggle datasets status` until it says `ready`.
2. `kaggle kernels push -p kaggle/<package>/kernel`.

**What the logs should show if the canaries work:**
- **Setup, both:** `source manifest verified (230 files)`, Python 3.12 paths, the 174-wheel install, and vLLM serving `vrfai/Qwen3.6-27B-FP8`.
- **vc33:**
  - G3 probes with no `CONFIRM_LEVER_WITNESS` purpose, each lever reported as `LEVER_FOUND` on its first witness;
  - G4-B answered by the controller on any level that reaches it, and at most 3 Duck G4 turns;
  - `PLAY-NORMAL` with `FREE_PLAY` receipts;
  - the run ending on 200 actions or 3,600 s.
- **ls20:**
  - G0 to G2 under the controller;
  - in G3, `LEVER_FOUND` on the first positive contact, and reachability releases as `PRESUMED_UNREACHABLE`;
  - if the roster completes inside 160 actions and 2,700 s, a G3 inventory or coverage report, then G4 opening;
  - no `PLAY-NORMAL` caused by G3 having no legal move.

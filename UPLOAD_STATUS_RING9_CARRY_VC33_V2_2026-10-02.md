# Upload status: ring9-carry-vc33-v2 (self-hosted dependencies)

**Date:** 2026-10-02
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v2.py`
**Record of the datasets:** `RECORD_SELF_HOSTED_DEPENDENCIES_v1_2026-10-02.md` (committed `dcd04fa`)

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v2` (224 files; source 217 files) |
| Package manifest sha256 | `065a455423d8c38ff527138a8051f292eb299020f189f512ba430a8d32d97e50` |
| Source manifest sha256 | `af52d2a6dd79af966572f2f4588b470ef29a7af1a8b553ed191ea29011eb231c` |
| Source commit | `fbbc7f4a9f1decc669d2aa599dc37903a4431e90` (R9-R06 to R9-R18), the same as v1, built from a `git archive` export |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v2` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v2` |
| Mounts | the dataset above, `stephenkaskin/virelai-vllm-wheelhouse-v3`, `stephenkaskin/virelai-qwen3-6-27b-fp8` |

**The source is frozen at `fbbc7f4`.** Later commits on `main` by other seats (the G3 NAV work, `bcc02aa` and before) and any uncommitted changes in the working tree are not in this package. That is deliberate: the run must test R9-R15 to R9-R18 exactly as v1 would have.

## What changed from v1

Only where the vLLM wheelhouse and the model come from. The world (vc33), budgets (200 actions, 10,800 s), source, criteria and served model (`vrfai/Qwen3.6-27B-FP8`) are v1's.

There are two additions:
- Two preregistered infrastructure criteria:
  - **I5 (self-hosted setup):** the setup log names both datasets' paths, pip installs from the wheelhouse with no index, and vLLM serves the model at about 33.7 GiB.
  - **I6 (comparability):** level 1 repeats the exit run's actions until Duck's first own action. A difference before that is the environment's, and gets named in the review.
- The `Dependencies` record, written into the checkpoint and both receipts.

**Finding: the datasets are named in five places, not the two my plan said.** Packaging v2 turned up three more. All five are rewritten from one record:

| # | Where | v1 (driessmit1) | v2 |
|---|---|---|---|
| 1 | `kernel-metadata.json` `dataset_sources` | both third-party refs | both self-hosted refs |
| 2 | `setup_commands.json` | 4 lines: owners and slugs | the same 4 lines, nothing else |
| 3 | notebook cell 6 `DATASET_SOURCES` (maps each mount for setup) | both refs | both refs |
| 4 | `deploy_target.pkl` `additional_dataset_sources` | both refs | both refs |
| 5 | `benchmark_initial.pkl` solver `kaggle_wheelhouse_dataset_source`, `kaggle_model_dataset_source` | both refs | both refs |

I diffed the packages file by file:
- No `src/` file differs.
- Notebook: only the title cell, `DATASET_SOURCES` and the label differ.
- Solver pickle: only the label and the two fields differ.
- Deploy-target pickle: only `additional_dataset_sources` differs.

## Guards built into the packager

The build is refused unless all of these hold:

- **Each edit matches exactly once.** Every one of the five edits must find its target exactly once.
- **The two routes to the setup command agree.** The solver's own setup-command generator is run with the old and the new dataset fields. The lines it changes must equal the lines the record's edit changed in the shipped setup command: the same 4 lines, word for word.
- **No old owner where it's read.** No package file outside the frozen source, `src.zip` and `RUN.md` (which explains v1's failure) may contain `driessmit1`. The shipped source still names driessmit1 in `inference/framework/kaggle.py`, as defaults the pickled solver overrides. That's the later code slice.
- **Same model.** The served model name must be identical in the old and new records.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` | **8/8**: both manifests re-derive, receipts bind them, `src.zip` byte-identical, offline GPU kernel leading with the v2 dataset, secret scan clean, source byte-identical to the `fbbc7f4` export |
| Mount simulation (new `tools/simulate_kaggle_preflight_mounts.py`) | **All three layouts pass:** nested, zip and direct |
| Negative control: the same simulation on **v1** | Fails with `FileNotFoundError: Missing attached dataset path(s): /kaggle/input/arc3-vllm-h100-wheelhouse-v3, /kaggle/input/vrfai-qwen3-6-27b-fp8-hf-snapshot`, which is exactly the live v1 failure. The simulation reproduces the real failure, and v2 clears it |
| Tamper: one byte appended to a source file | Refused: 3 checks FAIL (source manifest, package manifest, `src.zip`) |
| Tamper: setup command edited back to driessmit1 | Refused (both manifests FAIL) |
| Kit tests (`tools/kaggle_kit`) | 7 passed. New test: the v2 package mounts and records only the Director's datasets |
| ruff | clean |

**What the mount simulation covers.** It runs the notebook's real cells 2, 6, 8, 10, 12 and the start of 14. Dependency datasets are mounted at Kaggle's `/kaggle/input/datasets/OWNER/SLUG` layout, which is what the exit run's log showed. Between cells 8 and 10, it runs the setup command's own Python up to the vLLM start: the mount map, `resolve_kaggle_dataset_path`, and the check that stopped v1. In all three layouts:
- the wheelhouse resolves to `…/stephenkaskin/virelai-vllm-wheelhouse-v3`, with `requirements.lock` present;
- the model resolves to `…/stephenkaskin/virelai-qwen3-6-27b-fp8`;
- the source manifest verifies (217 files);
- the checkpoint world verifies (`vc33-5430563c`);
- the receipt verifies;
- the budgets are 200 actions and 10,800 s;
- the mode is gated.

**Not verifiable here:** the GPU install of the 174 wheels and the vLLM model load. Those are criterion I5, graded from the live log.

## Observation for the Chief Engineer (not changed)

Every Ring 9 package's shipped setup command is inherited from the base lineage. It is not what today's source would generate. With the same solver fields, the current generator differs in two lines of the analyzer environment:
- `LOCAL_ANALYZER_MAX_OUTPUT` is `'2048'` against the shipped `'0'`;
- the generator adds `LOCAL_ANALYZER_MAX_NO_TOOL_RESPONSES`.

v2 keeps the shipped command unchanged except for the 4 dependency lines, so it stays comparable with the exit run. Whether those analyzer settings matter to Duck's turns is an open question, and it's architectural, so it goes to the Chief Engineer, not this package.

## Director's steps

1. Put the delivered package and tools in place, then run the Mac checks:
   - `verify_kaggle_package.py`, which should print 8/8;
   - the kit tests, which should print 7 passed.
2. Commit, staging explicit paths only.
3. `kaggle datasets create -p kaggle/ring9-carry-vc33-v2/source-dataset -r skip`
4. `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v2`, until it says `ready`.
5. `kaggle kernels push -p kaggle/ring9-carry-vc33-v2/kernel`

— Claude, Alpha build seat, 2026-10-02

## Upload log (2026-10-02)

**Committed:** `43e083b` (232 files: the 227-file package, the v2 packager, the mount simulator, the two kit files and this document).

**Dataset upload:** `kaggle datasets create -p kaggle/ring9-carry-vc33-v2/source-dataset -r skip`

| Field | Value |
|---|---|
| Files uploaded | 12 |
| Sizes | `src.zip` 901 KB, `setup_commands.json` 10 KB, `source-manifest.json` 26 KB, the rest small |
| Visibility | private |
| Kaggle at upload end | "being created" |

The CLI printed "Skipping folder: src". That is expected: the source travels as `src.zip`, and the notebook verifies the extracted files against the manifest before any import. The simulator's `zip` and `nested` layouts cover both ways Kaggle has delivered it.

**Next:**
1. `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v2` until it says `ready`.
2. `kaggle kernels push -p kaggle/ring9-carry-vc33-v2/kernel`

**What the first minutes of the log should show if v2 works:**
- `vLLM wheelhouse path: /kaggle/input/datasets/stephenkaskin/virelai-vllm-wheelhouse-v3`, or `/kaggle/input/virelai-vllm-wheelhouse-v3`.
- `Qwen model path: …/virelai-qwen3-6-27b-fp8`.
- A no-index pip install of the 174 wheels.
- vLLM loading weights at about 33.7 GiB.
- The server smoke test's real model output.
- `source manifest verified (217 files)`, `checkpoint worlds verified: ['vc33-5430563c']` and `G0-G4 execution receipt verified`.

These lines are criterion I5. If the install or the model load fails, it fails before any model call, and the failure is about the datasets, not the solver.

**v1's pre-run risks still apply unchanged:**
- Duck may change level 1's path.
- Level 2 is unknown.
- The 200-action budget may end the run inside level 2.
- There is one extra Duck turn at level entry.
- Level 2 may be won by accident.
- F4 is still open.

I6 adds one check: any difference before Duck's first own action is the environment's, and the review names it.

— Claude, Alpha build seat, 2026-10-02

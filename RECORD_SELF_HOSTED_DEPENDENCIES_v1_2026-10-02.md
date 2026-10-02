# Record: self-hosted Kaggle dependencies (wheelhouse and model), v1

**Date:** 2026-10-02
**Author:** Claude (Alpha build seat), signed
**Executed by:** the Director (every Mac command, Kaggle push and upload)
**Governing plan:** `PLAN_SELF_HOSTED_DEPENDENCIES_AND_MODEL_v1_2026-10-01.md`
**Kit:** `tools/kaggle_kit/`, committed `86fa9ed`

This record supersedes the plan's model size estimate (~28 GB). The measured size is in section 2.

## 0. Status at a glance

| Dependency | Dataset (private, Director's account) | Uploaded | Kaggle status | Contents verified on Kaggle |
|---|---|---|---|---|
| vLLM wheelhouse | `stephenkaskin/virelai-vllm-wheelhouse-v3` | yes | `ready` | **yes**: 177 files; every wheel's name and byte size match the lock |
| Model | `stephenkaskin/virelai-qwen3-6-27b-fp8` | yes, 11 files | "being created" at upload end | **pending**: needs `status` = `ready`, then a file listing |

Every Ring 9 run so far depended on two datasets owned by driessmit1. Both returned 403 on 2026-10-01. A run no longer needs either of them once the model dataset passes its two pending checks and the package is retargeted (section 4).

## 1. Wheelhouse

### Build 1: Kaggle notebook (evidence only)

The notebook `stephenkaskin/virelai-build-vllm-wheelhouse-v3`, version 1 (no GPU, internet on), produced this report:

| Field | Value |
|---|---|
| Wheels | 174 |
| `all_digests_verified` | true |
| Bytes | 5,185,992,159 |
| Build time | 52.5 s |

I checked the downloaded output (`runs/kaggle-wheelhouse-v3-build/`):
- `SHA256SUMS` equals the lock, file for file and digest for digest.
- `requirements.lock` equals the lock's 174 `name==version` lines, in the same order.

This output was **not** turned into the dataset. Kaggle's CLI has no command to make a dataset from a notebook's output, and the Director chose an all-terminal route.

### Build 2: Mac, uploaded

The same script and lock, run on the Mac into `~/kaggle-datasets/virelai-vllm-wheelhouse-v3`, gave an identical report: 174 wheels, all digests verified, 5,185,992,159 bytes, 149.2 s. It was uploaded with `kaggle datasets create -p . -r skip`; Kaggle status `ready`.

The Kaggle file listing (`runs/kaggle-wheelhouse-v3-build/dataset_files.txt`), checked against `wheelhouse_v3.lock.json`:

| Check | Result |
|---|---|
| Files | 177: the 174 wheels plus `requirements.lock`, `SHA256SUMS` and `BUILD_REPORT.json` |
| Wheel names | Equal to the lock's set |
| Wheel sizes | 0 mismatches; 5,185,992,159 bytes in total |
| `requirements.lock` | 3,636 bytes, equal in size to the notebook build's copy, which was checked line by line |

Kaggle's listing gives names and sizes only, not digests. The digests were enforced when the wheels were built, and the size of every one of the 174 files matches.

### Setup compatibility

I read the carry package's `setup_commands.json`:
- Setup resolves the wheelhouse by owner and slug.
- It requires `requirements.lock` at the dataset root.
- It installs with `pip --no-index --find-links <root> -r requirements.lock`.

The dataset has exactly that layout.

The only side effect of the new slug is setup's install marker: it becomes `.virelai-vllm-wheelhouse-v3` instead of `.arc3-vllm-h100-wheelhouse-v3`.

**Not yet verified:** an offline install of these wheels on Kaggle's GPU image. The first retargeted run's setup is that test. It fails before any model call if anything is wrong.

## 2. Model

### The source

| Field | Value |
|---|---|
| Repository | `vrfai/Qwen3.6-27B-FP8` |
| Pinned commit | `70462b01826175b3f45fa80065184167ddc973fb` |
| License | Apache-2.0 |
| Excluded pattern | `original/*` |
| Bytes | **35,943,227,820** (about 35.9 GB, 33.47 GiB) |

Evidence: `runs/kaggle-wheelhouse-v3-build/model_plan.txt`.

That size is consistent with the exit run's vLLM log, which showed the model taking 33.66 GiB.

### Comparability with every earlier run

The repository's full commit history (`runs/kaggle-wheelhouse-v3-build/model_commits.txt`):

| Commit | Date (UTC) | Change |
|---|---|---|
| `e4b0d8b78e88` | 2026-04-24 | initial commit |
| `076636763143` | 2026-04-25 | weights added (W8A8 FP8, llm-compressor) |
| `70462b018261` | 2026-06-06 | README update |

**Conclusion:** the weights have had exactly one version. Any snapshot taken after 2026-04-25 holds the same weight files, and every Ring 9 run came months later. So the mirror's weights are byte-identical to what earlier runs loaded.

**Remaining assumption:** driessmit1's dataset ("…-hf-snapshot") was a verbatim copy of the repository. The vc33 run's level-1 path is the end-to-end check (section 4).

### Download (Mac, `mirror_model.py`, pinned to the commit)

| Field | Value |
|---|---|
| Files fetched | 10 |
| Time | 11 min 13 s |
| Transferred | 33.5 GB (the Hub's newer transfer format compresses and deduplicates) |
| Rebuilt on disk | 35.9 GB |
| Checksums | every LFS file verified against the Hub's published sha256; the script prints its final `mirrored …@70462b01…` line only after all pass |

The hidden `.cache` bookkeeping folder was removed. The folder held exactly these files:

| File | Bytes |
|---|---|
| `model.safetensors` | 35,923,194,376 |
| `tokenizer.json` | 19,989,424 |
| `config.json` | 24,718 |
| `chat_template.jinja` | 7,764 |
| `README.md` | 7,042 |
| `.gitattributes` | 1,570 |
| `processor_config.json` | 1,191 |
| `tokenizer_config.json` | 1,165 |
| `recipe.yaml` | 357 |
| `generation_config.json` | 213 |
| **Model files total** | **35,943,227,820**, equal to the plan's byte count |
| `MIRROR.json` (ours) | 1,187: repo, commit, and every file with size and digest |
| `dataset-metadata.json` (ours) | 122: id, title, `apache-2.0` |

### Upload

Command: `caffeinate -i kaggle datasets create -p . -r skip`

- `model.safetensors`: 33.5 GiB in 1 h 55 min 28 s, at 5.18 MB/s (about 41 Mbit/s).
- The other 10 files uploaded in seconds.
- Kaggle ended with: "Your private Dataset is being created."

## 3. What this means for later models

The Mac upload rate (about 5.2 MB/s) sets the cost of the all-terminal route:

| Candidate (plan §5) | Approximate size | Mac upload time |
|---|---|---|
| A. Qwen3.8-27B-FP8 | about 28–36 GB | about 1.5–2 h |
| B. ~120B mixture-of-experts at 4-bit (e.g. Qwen3.5-122B-A10B-NVFP4) | about 75 GB | about 4 h; also over the Mac's current free disk once these mirrors are kept |

For a B-class model, the Kaggle-notebook route (`kernels/model-…`, secrets added once in the browser) avoids both the home upload and the Mac disk. `mirror_model.py --plan-only` gives the exact size and commit first, without downloading the weights.

## 4. Remaining steps

1. **Director:** run `kaggle datasets status stephenkaskin/virelai-qwen3-6-27b-fp8` until it says `ready`. Then list the files, the same check as the wheelhouse: 11 files, and `model.safetensors` at 35,923,194,376 bytes.
2. **Claude:** repackage the vc33 carry run against `SELF_HOSTED_V3`.
   - The slugs in `dependencies.py` already match both datasets.
   - The served name stays `vrfai/Qwen3.6-27B-FP8`.
   - Record the `Dependencies` record in the checkpoint and receipt.
   - Re-verify (the full verify set, three layouts, tamper) before upload.
3. **Run vc33 and review it.** Review against the preregistered X-1, X-2, X-3 and L-1 criteria. Add a comparability check: until Duck's first action of its own, level 1 should repeat the exit run's path (E0004 explained, then the 6th E0005 press wins at transition 26).
4. **Later code slice:** change the `DEFAULT_*` values in `inference/framework/kaggle.py` (still driessmit1) to the self-hosted datasets.
5. **Disk:** `~/kaggle-datasets/` holds about 41 GB of local copies. They can be deleted once the vc33 run has installed and served from the Kaggle datasets. Until then, they are the fastest way to re-upload.

## 5. Rulings

| Ruling | Status |
|---|---|
| R1, self-hosting | Acted on by the Director on 2026-10-02 (both datasets uploaded) |
| R2, model sequence | Open |
| R3, GPU quota and time budget before the deadline | Open. The 2 November deadline still needs confirming on the Kaggle page |

— Claude, Alpha build seat, 2026-10-02

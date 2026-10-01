# Plan: self-hosted Kaggle dependencies, and the path to the strongest model Kaggle allows

**Date:** 2026-10-01
**Author:** Claude (Alpha build seat), signed

**Director's direction (2026-10-01):**
- "We don't want to depend on anyone if possible."
- "Prep to run the most advanced model possible allowed by Kaggle."

**Altitude:**
- **Code-level:** self-hosting the dependencies.
- **Plan-level (yours and Apex's):** the choice of model. Changing Duck's model changes the system under study.

## 1. What happened

`ring9-carry-vc33-v1` failed in setup before the solver started: "Missing attached dataset path(s)". Nothing in R9-R15 to R9-R18 ran.

The cause is the two third-party datasets every Ring 9 run has used: the vLLM wheelhouse `driessmit1/arc3-vllm-h100-wheelhouse-v3` and the model `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`.
- **Last night** (`ring9-g4-exit-v1`) both mounted at `/kaggle/input/datasets/driessmit1/…`.
- **Today** neither mounted.
- **`kaggle datasets files`** returns **403 Forbidden** for both.
- **The owner's public listing** now shows only a different model (`qwen3-8-27b-fp8-hf-017b9c7a`).

Our package and our own dataset were fine; the source manifest was verified, 217 files.

## 2. Self-hosting: the kit (`tools/kaggle_kit/`)

### The wheelhouse can be rebuilt byte for byte (verified)

The exit run's log records every wheel pip installed from the old wheelhouse: `requirements.lock` lines 1 to 174, with exact filenames. I checked every file against PyPI:
- **All 174 exist on PyPI under the identical filename.** That includes `torch-2.10.0-3-…`, which has a build tag, and the development build `nvidia_cutlass_dsl-4.5.0.dev0`.
- **Each is pinned with PyPI's sha256** in `wheelhouse_v3.lock.json`.
- **Total:** 5.19 GB.
- **The lock is complete:** pip's resolver, run on Python 3.12 / Linux x86-64 from the pinned `requirements.lock`, resolves exactly these 174 wheels, with nothing missing and nothing extra.

**`build_wheelhouse.py`** (standard library only) downloads each pinned file and refuses any byte that doesn't match its digest. It then writes:
- the wheels;
- `requirements.lock` (`name==version`, in the original order);
- `SHA256SUMS`;
- `BUILD_REPORT.json`.

I tested it end to end on a subset: download, digest check, then an offline `pip install --no-index --find-links` from the result. The same files with the same lock produce the same install, so this is the same wheelhouse, not an approximation.

### The model: mirror a pinned Hugging Face revision into your own private dataset

**`mirror_model.py`** works in five steps:
1. It resolves the revision to an exact commit and records it.
2. It refuses to start if the disk can't hold the files.
3. It downloads the snapshot and checks every large file against the sha256 the Hub publishes.
4. It writes `MIRROR.json`.
5. With `--publish`, it creates the private dataset (or a new version of it) through the Kaggle CLI. It never prints a credential.

It runs on your Mac, or inside a Kaggle notebook with internet on, using your Kaggle key as notebook secrets.

**One gap I can't close from here:** I don't know which revision of `vrfai/Qwen3.6-27B-FP8` Dries snapshotted. A fresh mirror may differ slightly from the weights every earlier run used. Section 4 handles that.

**`make_kernels.py`** generates the two Kaggle notebooks:
- `kernels/wheelhouse-v3/`: internet on, no GPU; writes the wheelhouse to `/kaggle/working`.
- `kernels/model-virelai-qwen3-6-27b-fp8/`: internet on; writes to `/tmp` and publishes with your secrets.

### Pointing a package at the new datasets: `dependencies.py`

The model and wheelhouse appear in two places, and both must agree:
- the kernel's `dataset_sources` (what Kaggle mounts);
- the setup command, which holds the owner and slug of each dataset, the served model name, the context length, the install stamp, and vLLM's tool-call and reasoning parsers.

`retarget` rewrites both from one `Dependencies` record. Each edit must match exactly once, or the whole edit is refused.

On the carry package, `SELF_HOSTED_V3` changes exactly 4 lines of the setup command (two owners and two slugs) plus the two mount references. A model swap becomes one reviewed record that the packager writes into the checkpoint and the receipt.

**Kit tests:** 6/6 pass and ruff is clean. They cover:
- the lock is exactly the exit run's 174 wheels;
- tampered bytes are refused;
- retargeting changes exactly the intended lines;
- a malformed setup command is refused;
- the mirror pins the commit, skips excluded files and refuses a digest mismatch.

## 3. Your steps to self-host (once the kit is committed)

1. **Wheelhouse (about 10 to 20 minutes on Kaggle, no GPU quota):**
   - push the `wheelhouse-v3` kernel;
   - when it finishes, open it on Kaggle → **Output** → **New Dataset**;
   - title it `virelai-vllm-wheelhouse-v3` and keep it private.
2. **Model** (about 28 GB for the current model; I'll confirm in its first log):
   - push the model-mirror kernel;
   - open it on Kaggle and add the secrets **KAGGLE_USERNAME** and **KAGGLE_KEY** (Add-ons → Secrets);
   - then **Save & Run All**. It publishes `stephenkaskin/virelai-qwen3-6-27b-fp8` itself.
   - If Kaggle's scratch disk is too small, the script stops before downloading. The fallback is the same script run on your Mac.
3. **I repackage the vc33 run against `SELF_HOSTED_V3`**, re-verify, and you upload and push as before.

## 4. Comparability: the vc33 run doubles as the check

The controller is deterministic until Duck acts on its own turn. So with the self-hosted copies, vc33's level 1 should repeat the exit run's path: E0004 explained, then the 6th E0005 press wins at transition 26.

- **It matches:** the copies behave the same for our purposes.
- **It differs before Duck's first action:** the cause is the environment, not Duck. I'll name that in the review rather than let it pass as variation.

## 5. The most capable model Kaggle allows (plan-level)

### Constraints as I could verify them

| Constraint | What I found | Source |
|---|---|---|
| Hardware | One **NVIDIA RTX PRO 6000 Blackwell Server Edition**, 96 GB, as our runs logged | Run logs |
| Memory in use now | The current model takes 33.7 GiB; vLLM then had 43.6 GiB for the KV cache (177,968 tokens) at 0.90 utilisation | Run logs |
| Internet | Off during evaluation | ARC Prize docs |
| Third-party models | No restriction found, but **prizes require open-sourced code and methods**; API models can't be used | ARC Prize docs |
| Final deadline | **2 November 2026** | A secondary source only; please confirm on the Kaggle page |
| Runtime per submission | Not on the pages I could read. Tufa's committed target used a 9-hour cap. | Please confirm |

### Candidates (vendor or third-party claims, not measured by us)

**A. Qwen3.8-27B-FP8: the drop-in upgrade.**
- Dense, 27B, Apache-2.0, open weights from about mid-August 2026.
- About 28 GB in FP8, the same weight class as now.
- 262K native context.
- The vLLM recipe lists vLLM 0.17 or later, so the wheelhouse we are rebuilding (0.19.0) may serve it unchanged. That has to be checked in a dry run.
- The recipe's tool-call parser is `qwen3_xml`; ours is `qwen3_coder`.
- **Cost:** mirror one model and change one record.

**B. A ~120B mixture-of-experts model at 4-bit: the largest class that fits one card.** Listed for a 96 GB card:
- Qwen3.5-122B-A10B: 10B active. A vLLM-ready NVFP4 checkpoint exists (RedHatAI, about 75 GB) and uses our current parsers.
- gpt-oss-120b: MXFP4, about 65 GB, Apache-2.0. Its chat format is different, which is a bigger integration change.
- Nemotron 3 Super and Mistral Small 4: about 120B, 4-bit.

At around 75 GB of weights, little memory is left for the KV cache. That is probably fine for our single 65K-context stream, but it has to be measured.

**C. Doesn't fit one card:** Qwen3.8-Flash-Next (its FP8 checkpoint is 173 GiB, and one single-GPU NVFP4 attempt under vLLM never came up), DeepSeek V4-Flash (284B), GLM-5.x, Kimi K3 and the Qwen3.8 flagship.

**Caveat:** these rankings are vendor claims and third-party summaries. One of the sources says its speeds are estimates, not measurements. A bigger model is not automatically better for *our* loop, where Duck answers a few demanding, tool-heavy turns. A model that fails tool calls costs us more than raw benchmark points gain.

### Proposed sequence

1. **Self-host the current model and run vc33.** This restores the baseline and tests R9-R15 to R9-R18 live.
2. **Mirror Candidate A and repeat the same run, unchanged except for the model.** It runs the same controller path, so the comparison is clean: orientation turns, accepted answers, tool-call failures, minutes per gate, and G4-B quality where reached.
3. **Mirror the best Candidate B checkpoint** (Qwen3.5-122B-A10B NVFP4 is my lean; it uses the same parsers we use now). First a load-only dry run (does it load, how much KV cache is left), then the same run.
4. **You and Apex choose the model** for the 2 November work from those measured runs.

**Rulings this needs:**
- **R1:** go ahead with self-hosting (steps 2 and 3 of section 3).
- **R2:** the model sequence above, or a different order.
- **R3:** the budget for GPU quota and time: two to three extra runs before 2 November.

— Claude, Alpha build seat, 2026-10-01

**Sources:**
- [ARC Prize 2026 docs](https://docs.arcprize.org/arc-prize-2026)
- [ARC-AGI-3 competition](https://arcprize.org/competitions/2026/arc-agi-3)
- [Competition README, deadlines](https://github.com/Reasonofmoon/kaggle-growth-lab/blob/main/competitions/arc-prize-2026-arc-agi-3/README.md)
- [vrfai/Qwen3.6-27B-FP8](https://huggingface.co/vrfai/Qwen3.6-27B-FP8)
- [Qwen3.8-27B vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)
- [Qwen 3.8 27B specs](https://www.yottalabs.ai/post/qwen-3-8-27b-specs-hardware-requirements-how-to-run-2026)
- [Qwen3.8-Flash-Next recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next)
- [Qwen3.8-Flash-Next on one RTX PRO 6000](https://blog.kubesimplify.com/running-qwen3-8-flash-next-on-dgx-spark-and-rtx-pro-6000)
- [RedHatAI Qwen3.5-122B-A10B-NVFP4 thread](https://forums.developer.nvidia.com/t/redhatai-qwen3-5-122b-a10b-nvfp4-seems-to-be-the-best-option-for-a-single-spark/363815)
- [96 GB model list](https://localllm.in/blog/best-local-llms-96gb-vram)
- [RTX PRO 6000 fit estimates](https://modelfit.io/gpu/rtx-6000-pro/)
- [Top open models, Sept 2026](https://www.thundercompute.com/blog/best-open-source-llms)

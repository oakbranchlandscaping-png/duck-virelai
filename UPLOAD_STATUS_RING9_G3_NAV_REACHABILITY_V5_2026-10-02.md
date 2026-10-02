# Upload status: Ring 9 G3 NAV reachability v5

**Author:** Sol (Alpha build seat), signed

**Date:** 2026-10-02

**Status:** Kaggle notebook version 1 running

## Private Kaggle artifacts

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v5`
- Notebook: `stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v5`
- Dataset URL: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v5>
- Notebook URL: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v5>
- Source commit: `728f81bb461b02e9524c101b960c9745f218b114`
- Package commit: `ef84f21`
- Package-manifest SHA-256: `d5a37c625e886f1652c54b25200a95dba2c9b9e066147ae31d668433d8663bfd`
- Source-manifest SHA-256: `62442a8cdd80b243afa3de2ae6a80a7c75a9d99f2e19c5d91ac4cb5cc9fa4766`

## Checkpoint profile

- one world: `ls20-9607627b`;
- one pass and concurrency one;
- 96 environment actions maximum;
- 2,700 seconds of behavior time after model setup;
- pinned Qwen3.8-27B-FP8 model and vLLM runtime;
- server-default model output length;
- extended thinking enabled;
- temperature 0.6;
- duplicate read-only correction after two identical calls;
- broad read-only correction after eight calls without progress;
- private offline GPU notebook on `NvidiaRtxPro6000`.

## Validation before launch

- Full Ring 9 suite: **534 passed**;
- focused guard/tool/prompt suite: **43 passed**;
- Ruff: passed;
- OpenRouter native tool and result-visibility canary: passed;
- package verifier against the committed source export: **8/8 passed**;
- embedded notebook code compiled;
- receipt/runtime parameter assertions passed;
- secret scan, including `src.zip`: clean;
- bundled source matches the committed export with zero diffs.

## Review rubric

1. Repeated read-only inspection must recover after the single corrective prompt or end promptly
   as `controlled_stop: no_progress_tool_loop`; it must not consume the outer time cap.
2. A real action or accepted gate transition must reset the guard.
3. G0-G2 should open G3 with a demonstrated NAV control map and total counter mask.
4. A failed `APPROACH` should become a refused `(stand, action)` edge and should not be selected
   again in the unchanged world state.
5. Pending NAV confirmation should remain `ROUTING` and ungraded until terminal contact.
6. Reachability exhaustion, if reached, should produce an evidence-bound
   `PRESUMED_UNREACHABLE` explanation, release the target without an inertness claim and advance.
7. A non-counter, non-ego world delta should invalidate prior-state refusals and reopen provisional
   reachability conclusions.
8. The run should end at a planned stop, controlled no-progress stop or explicit cap without a
   harness crash.

Unreached G3 criteria remain ungraded. Score and level completion are outside this checkpoint.

## Upload note

The first dataset command used directory-zip mode. Because the frozen bundle already contains its
verified `src.zip`, the CLI generated a second path with the same name and Kaggle rejected the
creation. No dataset was created by that attempt. The successful retry used directory-skip mode,
uploading the intended top-level files and single verified archive. Kernel version 1 was then
pushed and immediately reported `KernelWorkerStatus.RUNNING`.

Download completed outputs into:

`runs/kaggle-ring9-g3-nav-reachability-v5-v1/output/`

— **Sol**

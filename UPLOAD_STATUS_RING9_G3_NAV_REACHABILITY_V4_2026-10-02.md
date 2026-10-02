# Upload status: Ring 9 G3 NAV reachability v4

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** Kaggle notebook version 1 running

## Private Kaggle artifacts

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v4`
- Notebook: `stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v4`
- Dataset URL: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v4>
- Notebook URL: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v4>
- Source commit: `2b2a3d6da901ddcecb16e90b51f5ac9dc9ea75f5`
- Package-manifest SHA-256: `ffd7dc6a158b0f0146667fc55f54e583e0f41dc6b3f1824edc821b65b7c33a86`
- Source-manifest SHA-256: `c8e8b586c7637a66c24c6e07120779854598d6b28a6289d0eb90de7f8b412cac`

## Efficient checkpoint parameters

- one world: `ls20-9607627b`;
- one pass and concurrency one;
- 96 environment actions maximum;
- 2,700 seconds of behavior time after model setup;
- same pinned Qwen3.8-27B-FP8 model and vLLM runtime as v3;
- 2,048 output tokens per Duck turn;
- extended thinking disabled;
- temperature 0.2;
- private offline GPU notebook on `NvidiaRtxPro6000`.

This is an infrastructure canary. It does not grade score, level completion or the full gate stack.
Unreached criteria remain ungraded.

## Validation before upload

- Ring 9 suite: **527 passed**;
- dedicated NAV foundations: **17 passed**;
- Ruff: passed;
- package verifier with committed source export: **8/8 passed**;
- embedded notebook code compiled;
- receipt/runtime parameter assertions passed;
- secret scan, including `src.zip`: clean;
- bundled source matches the committed export with zero diffs.

## Review rubric

1. G0-G2 should open G3 with a demonstrated NAV control map and total counter mask.
2. A failed `APPROACH` should become a refused `(stand, action)` edge, and that unchanged edge
   should not be selected again immediately.
3. Pending NAV confirmation should remain `ROUTING` and ungraded until terminal contact.
4. If reachable-component exhaustion occurs, Duck should explain `PRESUMED_UNREACHABLE`, make no
   inertness claim, and advance to the next ranked target.
5. A non-counter, non-ego world delta should invalidate prior-state refusals and reopen provisional
   reachability conclusions.
6. The run should end at its planned stop or explicit action/time cap without crashing.

## Retrieval after completion

Download outputs into:

`runs/kaggle-ring9-g3-nav-reachability-v4-v1/output/`

The run was confirmed `KernelWorkerStatus.RUNNING` immediately after the push. No polling is
required; review begins after the user reports completion.

— **Sol**

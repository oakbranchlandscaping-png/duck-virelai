# Upload status: Ring 9 G3 target ledger ls20 v1

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-03  
**Status:** PACKAGE VERIFIED; UPLOAD PENDING

## Frozen identities

- Source commit: `8606448e0755974ee9cb045b71c276bd43dae8b2`
- Package: `kaggle/ring9-g3-target-ledger-ls20-v1`
- Package-manifest SHA-256: `7af1c36afc214380dd99da1c906c3789ab7cc5d8b4820ffb8ce3ea7e2e9b7f32`
- Source-manifest SHA-256: `1e893d9094c97b34b74921e76bc4da57795a1a937606cecc4a84c9e2e81e33e0`
- Intended private dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-target-ledger-ls20-v1`
- Intended private notebook: `stephenkaskin/taaf-virelai-ring9-g3-target-ledger-ls20-v1`
- World: `ls20-9607627b`
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Runtime: pinned successful Python 3.12 image
- Behavior safety limits: 96 actions, 1200 seconds, concurrency 1
- Inference limits: 4096 output tokens, 600-second request timeout, thinking enabled

## Verification

- Active source: 553 tests passed.
- Focused target-ledger suites: 40 tests passed.
- Ruff and Python compilation: passed for all changed source and tests.
- Package verification against the committed source export: 9/9 checks passed.
- Packaged source: byte-identical to commit `8606448`.
- Source and package manifests: re-derived successfully.
- Inner and outer receipts: identical and bound to both manifests.
- `src.zip`: byte-identical to the expanded source tree.
- Notebook code cells: compiled by the packager.
- Kernel: private, offline, GPU-enabled, and led by the new dataset.
- Secret scan, including `src.zip`: clean.
- Root-level `dataset-metadata.json`: present and covered by the source manifest.

The package was derived from the successful controller-first v2 package. The run changes the action
cap from 16 to 96 while retaining the 1200-second behavior cap and the same pinned runtime. Success
is governed by the preregistered target-ledger criteria, not by consuming all 96 actions.

## Canonical grading contract

`CHECKPOINT_G3_TARGET_LEDGER_LS20_V1_2026-10-03.md`

— Sol

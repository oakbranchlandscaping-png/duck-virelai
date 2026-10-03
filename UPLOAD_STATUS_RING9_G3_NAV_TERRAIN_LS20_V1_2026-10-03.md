# Upload status: Ring 9 G3 NAV terrain ls20 v1

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-03  
**Status:** private Kaggle notebook version 1 running

## Frozen identities

- Source commit: `c9fbc469ccdd30ee5a00c27c52d3f7011e1a95ca`
- Package commit: `225415a`
- Package: `kaggle/ring9-g3-nav-terrain-ls20-v1`
- Package-manifest SHA-256: `d94dc5fd203f63c63ed24532e345cc450c0fa33e48f098dad2e822046fd0839f`
- Source-manifest SHA-256: `2a74db52adca79d657913f194b394beeef9446d00d5cd3884847754bfee89b00`
- Private dataset: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-terrain-ls20-v1>
- Private notebook: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-terrain-ls20-v1>

## Checkpoint bounds

- World: `ls20-9607627b`
- Passes: 1
- Environment-action cap: 64
- Behavior-time cap: 900 seconds
- Concurrency: 1
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Output cap: 4096 tokens per model turn
- Purpose: validate G3 NAV floor/wall inference, full-footprint mapping, target-conditioned falsification, and target-ledger lifecycle repairs

This is not a score, level-completion, G4, or win checkpoint.

## Local validation before upload

- Focused NAV/G3 regression set: 95 passed
- Ruff: passed
- Persistence declaration audit: no undeclared fields
- Read-only replay of the prior ls20 artifact: floor `3`, wall `4`, 5×5 ego, four learned five-cell action vectors, no palette limitation
- Package manifest: 229 entries, zero missing, zero mismatches
- Secret guard: clean

## Launch record

- Private dataset creation accepted.
- Private notebook version 1 pushed.
- Immediate Kaggle status: `KernelWorkerStatus.RUNNING`.

The completed output must be reviewed against the preregistered criteria in `source-dataset/checkpoint-preflight.json`. Direct observations, controller products, Duck explanations, and evaluator judgments must remain distinct.

— Sol

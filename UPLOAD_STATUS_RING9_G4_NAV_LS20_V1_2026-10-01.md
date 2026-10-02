# Upload status: R9-R19 G4 NAV ls20 checkpoint

**Builder:** Sol (Alpha build seat), signed  
**Package:** `kaggle/ring9-g4-nav-ls20-v1/`  
**Commit:** `793564d`  
**Verification:** 8/8 package checks passed; source export matched `72adbe3` byte for byte.

## Current state

The private dataset was created and became ready. Notebook version 1 ran and failed during setup:
Kaggle no longer permitted either `driessmit1` runtime dataset to be attached. The source manifest
verified and the requested RTX PRO 6000 was allocated, but the wheelhouse and Qwen3.6 paths were
absent. No model request or game action occurred. See
`REVIEW_RING9_G4_NAV_LS20_KAGGLE_V1_2026-10-01.md`.

Version 2 is frozen at `kaggle/ring9-g4-nav-ls20-v2/`. It preserves source commit `72adbe3` and the
behavioral rubric, while using an accessible, checksum-identical wheelhouse mirror and a pinned
Qwen3.8 Kaggle model source. The model difference is explicit in the receipt.

## Version 2 launch

- Private source dataset created and reported `ready`.
- Private notebook `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v2`, version 1, was accepted with
  no invalid-source warnings.
- Requested accelerator: one NVIDIA RTX PRO 6000.
- Initial status after push: `RUNNING`.
- Behavioral evidence remains pending until the notebook completes and its receipt-bound output is
  downloaded and reviewed.

Version 2 then failed before model startup because Kaggle normalized the attached model's mount
directory while the notebook constructed the case-preserving `PyTorch` path. The source and exact
wheelhouse mounted successfully. Version 3 is frozen at `kaggle/ring9-g4-nav-ls20-v3/`; it changes
only model mount discovery and passes all seven package checks.

## Version 3 launch

- Private dataset `stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v3` reported `ready` on
  2026-10-02.
- Private notebook `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v3`, version 1, was accepted.
- Requested accelerator: one NVIDIA RTX PRO 6000.
- Initial status after push: `QUEUED`.
- No runtime or behavioral conclusion is warranted until the notebook starts. The first checkpoint
  is successful model-mount resolution; gameplay grading begins only after model startup and game
  actions are present in the receipt-bound output.

## Resume commands

The old resume commands below are historical; do not rerun v1 or v2. Version 3 is already uploaded
and queued. Check it with:

```text
kaggle kernels status stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v3
```

When it completes, review the downloaded execution receipt against the package receipt before
grading any gameplay artifacts.

— **Sol**

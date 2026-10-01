# Upload status: R9-R19 G4 NAV ls20 checkpoint

**Builder:** Sol (Alpha build seat), signed  
**Package:** `kaggle/ring9-g4-nav-ls20-v1/`  
**Commit:** `793564d`  
**Verification:** 8/8 package checks passed; source export matched `72adbe3` byte for byte.

## Current state

The private Kaggle upload was attempted on 2026-10-01 but did not execute. The escalated upload
was rejected by the environment's automatic approval layer because the session had reached its
tool-usage limit. A normal sandbox retry reached the Kaggle client but could not resolve
`api.kaggle.com`. No dataset version, notebook version, or gameplay run was created by these
attempts.

## Resume commands

From `duck-virelai/`, after Kaggle network access is available:

```text
kaggle datasets create -p kaggle/ring9-g4-nav-ls20-v1/source-dataset -r skip
kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v1
kaggle kernels push -p kaggle/ring9-g4-nav-ls20-v1/kernel --accelerator NvidiaRtxPro6000
```

Wait for the dataset status to be `ready` before pushing the notebook. Review the downloaded
execution receipt against the package receipt before grading any gameplay artifacts.

— **Sol**

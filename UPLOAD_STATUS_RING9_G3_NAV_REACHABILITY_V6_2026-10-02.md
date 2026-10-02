# Upload status: Ring 9 G3 NAV reachability v6

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** Kaggle notebook version 1 running

## Private Kaggle artifacts

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v6`
- Notebook: `stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v6`
- Dataset URL: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v6>
- Notebook URL: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v6>
- Source commit: `728f81bb461b02e9524c101b960c9745f218b114`
- Package commit: `a68043e`
- Package-manifest SHA-256: `52db8d706ad6069eaac9384839287390d38c0fe607466890390a7f8738301093`
- Source-manifest SHA-256: `666fee4a9887aadb24fb1d72d775f61094e6045080ea691eeb12cc3c8453f57c`

## Delta from v5

V6 changes only the frozen receipt encoding for the output-token setting. Runtime value `0` means
that no explicit cap is sent to vLLM; the receipt now records that meaning as `"server_default"`.
The shared verifier derives the semantic runtime value and requires it to equal the receipt.

The world, model, source commit, reasoning settings, action budget, behavior window and grading
rubric are unchanged from v5.

## Validation and launch

- V5 negative regression: **7/8**, failing only the newly added semantic receipt check;
- V6 package integrity: **8/8**;
- V6 plus committed-source comparison: **9/9**, zero source diffs;
- notebook code cells compile;
- secret scan, including `src.zip`: clean;
- dataset upload completed in directory-skip mode;
- kernel version 1 pushed successfully;
- immediate Kaggle status: `KernelWorkerStatus.RUNNING`.

The run should be graded against the unchanged v5 criteria only after lossless artifacts are
downloaded. Infrastructure success alone does not prove G3 NAV behavior.

— **Sol**

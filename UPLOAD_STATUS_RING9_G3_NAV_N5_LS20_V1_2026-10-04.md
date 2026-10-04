# Upload status — Ring 9 N5 bounded G3 NAV ls20 v1

**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Status:** private notebook version 1 completed and reviewed; partial checkpoint pass

- Source commit: `c636ba7`
- Package commit before upload record: `a54e0c6`
- Package: `kaggle/ring9-g3-nav-n5-ls20-v1`
- Package-manifest SHA-256: `1afcbe631ad82b0af18100a881d3015c515a8f8045a906f53a683684fb3cde59`
- Source-manifest SHA-256: `d23f91d0bdd937c86e32b6938d6f61854941c6d026cb8db63e5f8d907db16cbd`
- World: `ls20-9607627b`
- Budget: 80 actions, 1,200 behavior seconds, one pass, one worker
- Private dataset: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-ls20-v1>
- Private notebook: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-n5-ls20-v1>

The user explicitly approved this exact source payload and both private destinations. Dataset
creation uploaded the 12 intended root files, including the verified 936 KB `src.zip`, and skipped
the redundant expanded `src/` directory. Kaggle reported the dataset `ready`. Kernel version 1 was
accepted with the requested `NvidiaRtxPro6000` accelerator and initially reported
`KernelWorkerStatus.QUEUED`.

Notebook completion is not a behavioral pass. On completion, download artifacts and grade only the
N5 criteria: G0-G2 closure and mask, roster accounting, controller ownership, target dispositions,
terrain evidence, stable unreachable rows, and the explicit G3 completion or bounded-stop product.
Do not grade G4 comprehension, score, or win discovery.

## Completion update

The notebook completed in 20m 2s with 49 controller-owned environment actions and stopped at the
1,200-second behavior boundary. The run passed G0-G2 closure and masking, roster creation,
controller ownership, physical-contact initiation, floor evidence, and explicit bounded-stop
reporting. It did not complete the roster or accept the first semantic reachability checkpoint.

Review: `REVIEW_RING9_G3_NAV_N5_LS20_V1_2026-10-04.md`.

— **Sol**

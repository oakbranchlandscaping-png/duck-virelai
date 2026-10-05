# Upload status — Ring 9 G3 NAV N5.3 ls20 v1

**Type:** `UPLOAD_STATUS`  
**Package:** `ring9-g3-nav-n5-3-ls20-v1`  
**Source commit:** `aa799b5`  
**Package commit:** `cb34861`  
**Author:** Sol (Alpha build seat)  
**Date:** 2026-10-05  
**Status:** private Kaggle notebook version 1 queued

The private dataset was created successfully and Kaggle reported it `ready`. The upload contains
the intended top-level files and verified `src.zip`; the expanded `src/` directory was skipped.

Private notebook version 1 was accepted. The first status check returned
`KernelWorkerStatus.QUEUED`.

- dataset: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-3-ls20-v1>
- notebook: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-n5-3-ls20-v1>
- world: `ls20-9607627b`;
- boundary: 60 actions and 700 behavior seconds;
- package-manifest SHA-256:
  `52dec940c7ed32873159ba7021fe163fc731124415b464488734f660f246ed0d`;
- source-manifest SHA-256:
  `f333eab06e96702584e4fc18afdc983cff02bd421a27682ab7d363bcbb0c62f1`.

The checkpoint passes when the first attributed positive NAV contact emits `LEVER_FOUND`, becomes
G4-ready without a pending G3 confirmation, and advances to the next ranked target. Full roster
completion and completed G4 typing are outside this checkpoint.

No behavioral result is claimed until the executed artifacts are downloaded and graded.

— **Sol**

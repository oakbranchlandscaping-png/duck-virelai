# Ring 9 G4 Phase-1 drain v1 upload status

**Prepared:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed; upload commands executed by the Director
**Status:** private dataset created and `ready`; notebook version 1 pushed and running. Output not
yet downloaded; behavior ungraded.

> **2026-09-27 result (Claude, signed):** notebook version 1 completed (2 h 0 m 42 s, 25 actions,
> level 1 cleared). Output downloaded to `runs/kaggle-ring9-g4-phase1-drain-v1/output/`; receipt
> byte-identical to the frozen package. G3 closed on the exact model for the first time; the S1
> return edge held G4.2 and moved to E0005 as designed; E0005's orbit crossed a level boundary and the
> S1 hold then deadlocked for ~90 minutes. Full grading: `REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md`.

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-phase1-drain-v1` (private)
- Notebook: `stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1` (private), version 1,
  accelerator `NvidiaRtxPro6000`, internet off
- Package: `kaggle/ring9-g4-phase1-drain-v1/`, committed `777dc39`
- Source commit: `f8a967e909049577885bf7f9b473c98bd45b20f7`
- Package manifest SHA-256: `a827ab849f5789cb6c230ff9866347ff660d3cf4b466277bc0993e1f267a2538`
- Source manifest SHA-256: `9241ba8cd5f41b4e6c6a30ec53ede67f96c5da25110af7d5a3988a5b28ea419c`
- Transfer archive SHA-256 (packager + package): `85086e46744cc67d0ad598422f63831193e92c7f72725b909f7b45900d5d43b4`
- Model: `vrfai/Qwen3.6-27B-FP8` via local vLLM
- World: `vc33-5430563c`, one pass, concurrency 1
- Budget: 160 environment actions and 7,200 seconds of behavior time after model setup
- Validation: see `INFRASTRUCTURE_G4_PHASE1_DRAIN_KAGGLE_CHECKPOINT_2026-09-27.md`

## Upload log

1. Authentication confirmed with `kaggle kernels list --mine --page-size 1`. Kaggle CLI 2.0.0 was
   left in place because it uploaded every earlier ring9 package.
2. `kaggle datasets status` on the new slug returned 403. For a dataset in your own namespace,
   Kaggle returns 403 for "does not exist"; the harness's `_dataset_exists` treats it the same way.
3. First `kaggle datasets create ... -r zip` **failed**: "Path must be unique". The CLI zipped
   `src/` into a second `src.zip` beside the packager's own. No dataset was created.
4. `kaggle datasets create ... -r skip` **succeeded**: the eleven top-level files and the
   packager's `src.zip` (822 KB), `src/` skipped. Private dataset reported `ready`.
5. `kaggle kernels push ... --accelerator NvidiaRtxPro6000`: "Kernel version 1 successfully pushed."

## Next action

When `kaggle kernels status` reports `complete`, download the output into
`runs/kaggle-ring9-g4-phase1-drain-v1/output/`, confirm the downloaded receipt is byte-identical to
the frozen one, then grade against `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md`.

— Claude, Alpha build seat, 2026-09-27

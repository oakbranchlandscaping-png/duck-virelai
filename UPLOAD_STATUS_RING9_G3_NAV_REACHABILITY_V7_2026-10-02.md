# Upload status: Ring 9 G3 NAV reachability v7

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** notebook version 1 failed before benchmark; version 2 running

## Frozen identities

- Source commit: `0a2e4dcb2749bcc93d8632499e04db0b90743a35`
- Package commit: `dc63216`
- Package: `kaggle/ring9-g3-nav-reachability-v7`
- Package-manifest SHA-256: `42199149aa4a640af04273bb01419b8429f159d8da7d4ede1930034eda36d6bd`
- Source-manifest SHA-256: `a2a45dc09db60e4153fa159f09d64f82c0727ae225bfd07e1f857fe9abefd562`
- Intended private dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v7`
- Intended private notebook: `stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v7`

## Validation

- Full source suite: 542 passed;
- focused gate, card, evaluator and repair suite: 58 passed;
- bridge plus guard integration suite: 35 passed;
- package verification: 9/9;
- source export: byte-identical to the committed source;
- notebook code cells: compiled by the packager;
- secret scan, including `src.zip`: clean;
- receipt setup semantics: matched;
- v6 immutable run artifacts: preserved.

## Behavioral checkpoint

V7 keeps the same ls20 world, pinned Qwen3.8-27B-FP8 model, reasoning settings and behavior limits
as v6. It passes this slice if the strict eight-action G1 probe leads to an accepted, controller-bound
ego explanation, one joined prospective demonstration and entry into G2 without a no-progress or
contract-repair stop. G2 and G3 results are recorded but do not determine this slice's grade.

## Upload decision

The automated approval reviewer initially rejected the upload because a new source bundle would be
sent to third-party Kaggle and prior run approvals were not considered explicit approval for this
exact payload and destination. The user then explicitly approved the named v7 upload.

## Launch record

- Private dataset creation accepted:
  <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v7>
- Private notebook version 1 pushed:
  <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v7>
- Immediate status after launch: `KernelWorkerStatus.RUNNING`.

The run should be reviewed after completion against the behavioral checkpoint above. Its live output
must remain distinct from the frozen package and the prior v6 artifacts.

## Version 1 failure

Version 1 selected a new Kaggle Python 3.13 Docker image. The attached wheelhouse is CPython 3.12,
so offline setup failed at `aiohttp==3.13.5` before vLLM, Duck or the game started. See
`REVIEW_RING9_G3_NAV_REACHABILITY_V7_V1_FAILURE_2026-10-02.md`.

Version 2 preserves the frozen dataset and notebook bytes and pins the exact Docker image digest
recorded by Kaggle for the successful v6 Python 3.12 run.

## Version 2 launch

- Repair commit: `acf0307`;
- frozen notebook SHA-256: `7a65fc93e210975b3b942797bc19c70a2a053fde6ab38a9d6c19d7e20659cb86`;
- pinned Docker image digest: `37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`;
- Kaggle notebook version: 2;
- immediate status: `KernelWorkerStatus.RUNNING`;
- pulled Kaggle metadata confirms the intended Docker image pin.

— **Sol**

# Upload status: Ring 9 G3 NAV reachability v7

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** frozen and verified; Kaggle upload awaiting explicit approval

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

The automated approval reviewer rejected the upload attempt because a new source bundle would be
sent to third-party Kaggle and prior run approvals were not considered explicit approval for this
exact v7 payload and destination. No upload occurred. Resume only after fresh user approval.

— **Sol**

# Build record — N5.1 Kaggle checkpoint package

**Type:** `BUILD_RECORD`
**Parent:** `BUILD_N5_1_BOUNDED_G3_SEMANTIC_SEAM_2026-10-04.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Status:** locally validated; private Kaggle version 1 queued

## Purpose

Freeze the committed N5.1 semantic-seam repair into one short, receipt-bound `ls20` checkpoint.
This package tests G3 progression at the exact point where N5 stalled. It does not test G4, score or
world completion.

## Frozen identity

- source commit: `14f6459`;
- package: `ring9-g3-nav-n5-1-ls20-v1`;
- private dataset destination:
  `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-1-ls20-v1`;
- private notebook destination:
  `stephenkaskin/taaf-virelai-ring9-g3-nav-n5-1-ls20-v1`;
- world: `ls20-9607627b`;
- model: `Qwen/Qwen3.8-27B-FP8`, pinned revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`;
- one pass, one worker;
- 60 environment actions;
- 700 behavior seconds;
- package-manifest SHA-256:
  `0443fc06b337c87d7e13b4ed7edf29723e0d6c016ced24df85ec0d4957013c3f`;
- source-manifest SHA-256:
  `fdd4dfbb5a1719aba660be43767c0efbfcad27531ccf1257db518277decaa6a7`.

## Local validation

- all 223 source-manifest entries match their files;
- all 230 package-manifest entries match their files;
- `src.zip` passes its archive integrity check with 214 entries;
- root and dataset execution receipts are byte-identical;
- the four changed runtime files are byte-identical to the committed source;
- the packaged runtime passes 59 focused G3, NAV and provider tests with 14 existing dependency
  deprecation warnings;
- dataset, kernel, receipt and preflight JSON parse and name the N5.1 package;
- the explicit ARC key marker from project history is absent;
- the packager's secret guard passes;
- the new packager and signed records pass whitespace checks. The frozen source retains four
  pre-existing whitespace findings from commit `14f6459` so the package remains byte-identical to
  its declared source.

## Live grading contract

G0-G2 must close and install the counter mask. The eligible roster must populate before target
execution, and every controller-computable action must remain controller-owned. At the first bound
reachability checkpoint, Duck may make at most two completed model requests across all solver
turns. An accepted compact explanation must terminalize the target and permit controller-only reuse
for a matching sibling semantic key.

If no answer is accepted, the run must stop cleanly with `G3_SEMANTIC_RETRY_EXHAUSTED`. That product
must name the pending target, its latest lifecycle evidence and the exact eligible roster count. A
clean bounded failure is evidence that the control boundary works; it is not G3 completion.

## External status

The private dataset upload succeeded with the 12 intended mounted files. The expanded `src/`
directory was skipped because the verified `src.zip` is the runtime payload. Kaggle reported the
dataset `ready`. Private notebook version 1 was then accepted and reported
`KernelWorkerStatus.QUEUED`.

- dataset: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-1-ls20-v1>
- notebook: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-nav-n5-1-ls20-v1>

The output has not yet been downloaded or graded.

— **Sol**

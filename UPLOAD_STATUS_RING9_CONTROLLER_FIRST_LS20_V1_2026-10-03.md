# Upload status: Ring 9 controller-first ls20 v1

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** private dataset created; notebook version 1 queued

## Frozen identities

- Source commit: `0b1a5e4ce45f837ad0da921d3ac308c9ba9e56dd`
- Package: `kaggle/ring9-controller-first-ls20-v1`
- Package-manifest SHA-256: `af2de4fb56543be79a875ee81e92feed0cb85f3bae82d0ff81c9d0b381b6d296`
- Source-manifest SHA-256: `ea4af6b4456ba32660b828846a2d394b39e09c46d6b7420afaf557a275bdf83a`
- Private dataset: `stephenkaskin/taaf-duck-virelai-ring9-controller-first-ls20-v1`
- Private notebook: `stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v1`
- World: `ls20-9607627b`
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Runtime image: pinned successful Python 3.12 image digest
- Behavior budget: one pass, 16 environment actions, 1200 seconds, concurrency 1
- Inference budget: 4096 output tokens per request; 600-second request timeout; thinking enabled

## Validation

- Active committed source: 546 tests passed.
- Focused G1/G2/NAV source suites: 50 tests passed.
- Frozen package verification: 9/9 checks passed.
- Packaged source: byte-identical to the committed source export.
- Notebook code cells: compiled by the packager.
- Package and source manifests: re-derived successfully.
- Receipt: identical inside and outside the dataset and bound to both manifests.
- Secret scan, including `src.zip`: clean.
- Kernel: offline, private, GPU-enabled, and pinned to the Python 3.12 image used by the successful
  v7 run.

The deployment payload intentionally excludes the source test tree. The failed attempt to invoke
tests from the frozen dataset therefore says nothing about the package's code; test evidence comes
from the exact committed source exported into the package.

## Preregistered live criteria

1. G0 closes through the controller with zero model requests.
2. The eight Delphi actions are controller actions in strict order:
   `ACTION1x2`, `ACTION2x2`, `ACTION3x2`, `ACTION4x2`.
3. Duck receives the evidence and explains the embodied ego and its movement laws.
4. The accepted model and frozen prediction remain in the demonstration card.
5. The controller executes the prospective demonstration and G1 closes from its scoped comparison.
6. G2 opens and the deterministic route planner executes at least one `PILOT_TO_CONTACT` action.
7. A remote board delta does not by itself erase observed ego movement or refusal evidence.
8. The run ends at the explicit cap or another controlled stop without crashing.

This checkpoint does not require score, level completion, G2 closure, counter explanation, G3
entry, or lever discovery.

## Launch record

- The first dataset command used directory mode `zip`. Kaggle generated a second archive for the
  expanded `src/` directory, which collided with the package's explicit verified `src.zip`; dataset
  creation stopped with `Path must be unique`. No package bytes were changed.
- The retry used directory mode `skip`, uploading the verified `src.zip` exactly once and omitting
  the redundant expanded tree.
- Private dataset creation accepted:
  <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-controller-first-ls20-v1>
- Private notebook version 1 pushed:
  <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v1>
- Immediate status: `KernelWorkerStatus.QUEUED`.

Review after completion against only the preregistered criteria above. Do not infer behavior from
the active source, package plan, or notebook status.

— Sol

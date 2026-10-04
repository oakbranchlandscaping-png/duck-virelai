# Build record — N5 validation and package

**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Source:** `c636ba7` (`Build bounded NAV G3 closure through N4`)
**Package:** `kaggle/ring9-g3-nav-n5-ls20-v1`

## Plan review

N5 remains the correct validation rung, with one provenance correction: N1-N4 had to become a real
source commit before packaging. Reusing the older packager's hard-coded `f985410` identity would
have produced a manifest that did not describe the tested code. Commit `c636ba7` contains only the
Ring 9 N0-N4 source, tests, and Sol-signed build records; unrelated dirty-tree work was excluded.

The grade remains limited to G0-G3. G4 comprehension, score, and win discovery are outside this
checkpoint.

## Source validation

The complete Ring 9 source suite passed:

- 575 passed;
- 14 pre-existing matplotlib/pyparsing deprecation warnings;
- 553.92 seconds;
- no test failures or skips reported.

## OpenRouter rehearsal

Configuration:
`variants/ring9-cybernetic-gates/ARC3-Inference/configs/g3-nav-n5-ls20-openrouter-fast.json`.

Run artifact:
`variants/ring9-cybernetic-gates/ARC3-Inference/runs/20261004_010704_ring9-g3-nav-n5-ls20-openrouter-fast-v1`.

Direct observations:

- G0 and the deterministic opening executed eight environment actions before Duck was needed.
- At action 9, OpenRouter rejected every request with HTTP 402 `weight_exceeds_budget` because the
  request's maximum cost exceeded the account's available credits.
- No model response or model token was produced.
- Sol stopped the retry loop; the harness finalized the interrupted run with eight actions.

This is infrastructure evidence only. It does not pass or fail N1-N4 behavior.

## Frozen Kaggle package

The package derives from the last executed ls20 Kaggle environment and changes the committed source,
budget, identity, and N5 grading contract. It retains the pinned Python 3.12 image and the existing
Qwen3.8-27B-FP8 setup.

- private dataset destination:
  `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-ls20-v1`;
- private notebook destination:
  `stephenkaskin/taaf-virelai-ring9-g3-nav-n5-ls20-v1`;
- world: `ls20-9607627b`;
- one pass, one worker;
- 80 environment actions;
- 1,200 behavior seconds;
- package-manifest SHA-256:
  `1afcbe631ad82b0af18100a881d3015c515a8f8045a906f53a683684fb3cde59`;
- source-manifest SHA-256:
  `d23f91d0bdd937c86e32b6938d6f61854941c6d026cb8db63e5f8d907db16cbd`.

Verification passed:

- all 222 source-manifest entries match their files;
- all 229 package-manifest entries match their files;
- critical N1-N4 source files are byte-identical to commit `c636ba7`;
- root and dataset execution receipts are byte-identical;
- packaged-copy focused suite: 115 passed, 14 existing dependency warnings;
- dataset, kernel, receipt and preflight JSON parse;
- secret guard clean.

## External status

No package bytes were uploaded. Automatic approval review rejected the private Kaggle dataset create
because this exact N5 source payload and destination had not been explicitly approved. The safe next
step is one explicit approval for the named private dataset and private notebook; after that, upload
the dataset, wait for `ready`, push the notebook, and let the user initiate by terminal if that remains
the preferred queue path.

— **Sol**

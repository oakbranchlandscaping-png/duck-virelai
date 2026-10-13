# Duck–Virelai build rhythm

## Current Ring 9 amendment — 2026-10-12

The active development loop is **interface → fail first → narrow build → T0 → T1 → review → T2 once → explicit-path commit → live evidence when required**.

Test tiers protect both speed and coverage:

- **T0, change-focused:** the smallest meaningful contract and regression set; expected under 90 seconds.
- **T1, slice floor:** all tests for the changed subsystem and its shared boundaries; expected under 5 minutes, target near 3.
- **T2, full acceptance:** the full accepted suite, run once after Sol accepts the source and before packaging, release, or a shared runtime merge; goal under 15 minutes.

WO-TEST-RHYTHM is accepted at `5fdac9a`. On the four-core Mac, directed-G3 T0 is 19 passed in 56.8 seconds, directed-G3 T1 is 143 passed in 272.1 seconds with four workers, and the exact 817-test T2 is 816 passed, 1 skipped in 534.4 seconds with four workers. The golden is unchanged. See `RECORD_RING9_TEST_FLOOR_v3_2026-10-13.md`.

The present product loop is library-centered: a gate exposes an actionable question, Duck chooses where needed, the controller acts, receipts capture the result, deterministic code certifies it, and the library revision becomes the next target. The ordinary world description must exist before a win can be explained in that language. See `START_HERE.md` and build plan v4.

## Standing rule

Do not spend a full 25-game Kaggle run to debug a narrow mechanism.

Use the smallest run that can falsify the proposed fix.

## Stage 1 — Local contract

Test the exact code boundary locally with fixtures, captured requests, and
failure-path tests.

Examples:

- Did the report enter the final provider payload?
- Did a retry preserve or duplicate it?
- Did the action bridge produce valid TAAF actions?
- Did a marker describe a completed fact rather than an intention?

Local success proves only that the code path works under controlled inputs.

## Stage 1B — Deployment artifact preflight

Build the exact Kaggle dataset and notebook through TAAF's dry-run path. Treat
that generated bundle, not the development checkout, as the product.

Before upload:

- reject `__pycache__`, `.pyc`, `.DS_Store`, virtual environments, and
  space-suffixed duplicate directories in both source and bundle;
- import every notebook entry point from the isolated packaged snapshot;
- compile every generated notebook code cell;
- execute any replaced or generated orchestration cell with external services
  stubbed, because compilation does not detect missing runtime names;
- verify the requested games resolve and that zero games or zero actions is a
  hard failure;
- verify provider, network, accelerator, game mode, runtime, and concurrency;
- confirm dataset, kernel, benchmark, ring, and output labels agree.

The full incident history and checklist are recorded in
`variants/ring8.0/KAGGLE_INFRASTRUCTURE_POSTMORTEM_2026-09-04.md`.

## Stage 2 — OpenRouter live slice

Run one selected ARC Online world through OpenRouter before paying the Kaggle startup and
45-minute notebook cost. Use the smallest action and wall-clock budget that can expose the active
slice. This is the default live engineering loop for gate logic, model-facing instructions,
answer repair, tool calling, stopping, retries, and handoffs.

Use two named profiles:

- **fast infrastructure:** the approved same-generation sparse Qwen proxy;
- **Kaggle rehearsal:** the same dense Qwen checkpoint family, context, sampling, reasoning mode,
  tool schema, and output budget as the next Kaggle package.

Every run records the requested model, actual routed provider and quantization when available,
reasoning settings, budgets, world, and source revision. An OpenRouter pass is live behavioral
evidence for the tested controller slice. It is not evidence that the Kaggle package or local-vLLM
serving path works.

## Stage 3 — Kaggle milestone smoke

Run one selected game on Kaggle when a gate milestone already passes through OpenRouter and the
question is whether the frozen package, mount, local-vLLM profile, exact checkpoint, and notebook
runtime preserve that behavior. Add 2–3 games only when the milestone depends on multiple world
types.

Choose games that exercise the relevant paths. For the Ring 6 handshake this
means nonzero Captain action counts and, when practical, more than one world
type.

Grade only the proposed mechanism. A handshake smoke run passes when every
included handoff-eligible game proves:

- exact report persisted;
- exact report present once in the first Duck provider payload;
- fingerprint matched;
- report-bearing request received a valid model response;
- Duck subsequently acted;
- no transport or audit failure occurred.

If the smoke run fails, repair and repeat at smoke scale. Do not escalate to a
full suite.

## Stage 4 — Full 25-game canary

Run the complete suite only after the mechanism passes locally and on Kaggle.

The full run answers broader questions:

- Does the mechanism remain reliable across all worlds?
- How does Duck respond to different report shapes?
- What are the fallback, timeout, and boundary cases?
- Does behavior or score change?

Separate grading into:

1. mechanism reliability;
2. model use;
3. game outcome.

## Stage 5 — Comparison run

Use repeated or controlled full runs only when estimating performance effects.
A single 25-game run can reveal failure shapes and direction, but it does not
by itself establish causality.

## Promotion rule

```text
local contract passes
  -> deployment artifact preflight passes
  -> one-world OpenRouter live slice passes
  -> one-world Kaggle milestone passes
  -> 2–3 world-type Kaggle smoke when required
  -> 25-game canary
  -> controlled comparison if justified
```

Failure at any stage returns the build to that same stage or lower. It does
not justify spending more games.

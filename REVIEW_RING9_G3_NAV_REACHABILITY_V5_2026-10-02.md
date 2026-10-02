# Review: Ring 9 G3 NAV reachability v5

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Verdict:** Infrastructure failure before benchmark start; behavioral criteria ungraded

## Direct observations

- Kaggle ended notebook version 1 with `KernelWorkerStatus.ERROR`.
- The expected RTX Pro 6000 was available.
- vLLM 0.19.0 loaded `Qwen/Qwen3.8-27B-FP8`, opened the local API and returned HTTP 200 for the
  real-model smoke request.
- The generated smoke answer was `2 + 2 equals 4.`
- The notebook constructed and verified the requested world list: `['ls20-9607627b']`.
- The notebook then raised `RuntimeError: Execution receipt mismatch before benchmark start`.
- The sole mismatch was `max_output_tokens_per_turn`: live value `"server_default"`, frozen receipt
  value `0`.
- The server log contains no benchmark inference request after the smoke request, and the run
  produced no benchmark receipt or behavioral artifacts.

The source for these observations is the downloaded output plus the Kaggle session stream saved at
`runs/kaggle-ring9-g3-nav-reachability-v5-v1/kaggle-session-log.json`.

## What the evidence supports

The GPU, wheelhouse, model mount, vLLM startup, Qwen runtime, source mount, manifest validation and
offline ls20 selection all worked. The failure is a package-contract encoding defect. Runtime uses
integer `0` as the control value for an omitted model output cap, then records its meaning as
`"server_default"`. The v5 generator wrote the raw control value into the expected receipt.

The strict receipt check behaved correctly by preventing an unbound run. V5 spent zero ARC actions.
Therefore it says nothing about G0-G3 progression, terrain learning, refused edges, target release,
world-delta reopening or the no-progress guard.

## Correction

V5 remains frozen as failure evidence. V6 preserves its model, world, action budget, behavior time,
thinking profile, sampling profile and source commit. It changes the expected receipt value to
`"server_default"`.

The shared package verifier now derives the semantic value from the runtime setup and compares it
with the receipt. As a negative regression, V5 now fails that check with setup
`'server_default'` versus receipt `0`. V6 passes with both sides equal to `'server_default'`.

— **Sol**

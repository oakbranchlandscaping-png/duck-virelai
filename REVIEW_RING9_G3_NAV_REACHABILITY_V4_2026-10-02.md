# Review: Ring 9 G3 NAV reachability v4

**Author:** Sol (Alpha build seat), signed

**Date:** 2026-10-02

**Evidence:** `runs/kaggle-ring9-g3-nav-reachability-v4-v1/output/`

**Verdict:** valid completed execution; G3 NAV behavior ungraded because the run stalled in G1

## Direct observations

- Kaggle completed the kernel without an infrastructure crash.
- The packaged and downloaded `execution_receipt.json` files have the same SHA-256:
  `6c7172f313e525e118142951d44924cebe7b6960cbc975d195cb1211aa2a1b86`.
- The behavior runner stopped at its planned 2,700-second cap after 45 minutes and 1 second.
- G0 passed and opened G1.
- Duck executed one real environment action: the first prescribed `ACTION1` ego probe.
- That action changed 52 cells. Fifty formed a coherent translation of the candidate embodied
  object; two cells belonged to the changing lower display region.
- G1 remained active because `ACTION1` had only one of its two required observations and
  `ACTION2` through `ACTION4` had none.
- The run produced 699 model responses and the solver reported 107,958 generated tokens.
- Of 696 assistant Python calls recoverable from the request trace, 687 were the exact same
  read-only request to print the candidate object's before/after ASCII regions.
- The turn ledger contains 43 consecutive `turn_time_budget` turns after the first action, followed
  by `stop_requested`. None of those turns executed an environment step.
- G2 and G3 never opened. No floor/wall label, refused edge, routing search, unreachable-target
  explanation, or world-state reopening behavior was exercised.

`summary.txt` reports 704 tokens. That figure covers the action-associated summary path and is not
the total model use. The solver note and request ledger support the 107,958-token total.

## Preregistered rubric grade

| Criterion | Grade | Evidence-supported conclusion |
|---|---|---|
| G0-G2 open G3 | Not achieved | G0 passed; G1 remained active after one action. |
| Failed approach becomes a refused edge | Ungraded | G3 never opened. |
| Pending confirmation remains routing | Ungraded | No G3 approach occurred. |
| Reachability exhaustion produces `PRESUMED_UNREACHABLE` and advances | Ungraded | No target routing occurred. |
| World delta reopens provisional reachability | Ungraded | No G3 refusal or reopening occurred. |
| Bounded ending without crash | Passed | The run ended cleanly at the configured behavior cap. |

The result supplies no evidence for or against the correctness of the new NAV terrain and
reachability slice. Treating unreached criteria as failures would conflate model-control friction
with gate behavior.

## Friction exposed

The existing time budget bounds a single Duck turn, but it does not detect repeated no-progress
tool use. At each timeout, the next turn restored enough context for Duck to repeat the same
inspection again. The outer behavior cap therefore limited duration while permitting 687 redundant
calls.

This run used Qwen3.8-27B-FP8 with a 2,048-token output limit, temperature 0.2, and extended thinking
disabled. The stall occurred under that profile. Because several inference settings changed
together, the evidence does not establish that any one setting caused the loop.

## Required next slice

Build a no-progress tool-loop breaker in the Duck runtime before spending another Kaggle run:

1. Canonicalize Python tool requests and track whether an environment step or accepted gate answer
   occurred between calls.
2. Reject an identical read-only call after a small consecutive threshold and return a focused
   correction: the observation is already recorded; execute the binding probe or submit the gate
   answer.
3. Bound read-only tool calls within a turn. If the correction is ignored, end the turn with an
   explicit `no_progress_tool_loop` outcome rather than waiting for the wall-clock budget.
4. Carry the loop state across consecutive turns so a timeout cannot reset the guard.
5. Add deterministic tests for duplicate detection, reset after a real action, reset after an
   accepted gate answer, and persistence across turn boundaries.
6. Validate locally with a model-backed canary before repackaging Kaggle.

For the next Kaggle checkpoint, retain one-world scope and a 30-45 minute outer cap, restore the
previously productive reasoning profile, and keep unreached gate criteria ungraded. Action limits
alone cannot control this failure because only one action was taken.

— **Sol**

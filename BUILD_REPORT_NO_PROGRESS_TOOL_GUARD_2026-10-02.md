# Build report: no-progress tool-loop guard

**Author:** Sol (Alpha build seat), signed

**Date:** 2026-10-02

**Source:** `variants/ring9-cybernetic-gates/ARC3-Inference`

**Status:** implemented and locally validated; Kaggle retry preparation follows

## Triggering evidence

The completed Ring 9 G3 NAV reachability v4 run was valid but never reached G3. After one G1
environment action, Duck repeated one exact before/after ASCII inspection 687 times. Forty-three
successive turns ended at their per-turn time budget and resumed the same semantic state. The run
made 699 model requests, generated 107,958 reported completion tokens and ended at the 2,700-second
outer cap.

This establishes an architectural robustness gap: time was bounded, but progress was not. It does
not establish a defect in G3 NAV terrain or reachability, which the run never exercised. The stall
occurred under the thinking-off fast profile, but simultaneous inference changes prevent assigning
causality to one setting.

## Implemented correction

The production `ToolAgent` now maintains a no-progress guard scoped to the current runtime,
environment step, level and gate.

- Python calls receive stable fingerprints after line-ending and trailing-space normalization.
- An environment action or accepted gate transition resets the guard.
- A new world step, level or gate also resets cross-turn state.
- Two identical read-only calls trigger one concise correction.
- Eight distinct read-only calls without progress trigger the same correction.
- The correction requires the next call to execute the binding probe, submit the gate answer or,
  outside gated mode, execute an environment action.
- Another read-only call after that correction ends the run with the explicit
  `no_progress_tool_loop` diagnostic.
- The stop is controlled rather than reported as an analyzer crash.
- State survives ordinary turn boundaries, so a timeout cannot erase the warning.
- If one model response contains an inspection followed by a real action, the action still runs
  and clears the guard.

The gated prompt now tells Duck to ask a new concrete question with every added inspection and to
act once the relevant observation is available. The historical Ring 0/observer prompt is unchanged.

## Files changed

- `inference/agent/prompts.py`
- `inference/agent/tool_agent.py`
- `inference/framework/solver.py`
- `tests/test_tool_agent_no_tool_circuit_breaker.py`
- `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`

## Validation

- Focused tool, gated bridge, rate-limit and prompt-compatibility tests: **43 passed**.
- Full Ring 9 suite: **534 passed**, 14 third-party deprecation warnings, no failures.
- Ruff on changed Python files: **passed**.
- OpenRouter native tool canary: **passed** using `qwen/qwen3.6-35b-a3b` routed through
  AtlasCloud; the model issued a native Python call and correctly consumed its returned value.

The first full-suite pass exposed that the initial prompt edit had changed the frozen Ring 0 model
surface. The implementation was corrected to apply the new instruction only in gated mode, and the
full suite was rerun cleanly. This friction is retained here because it proves the compatibility
boundary was tested rather than assumed.

## Next live test

Repackage the same one-world ls20 G3 NAV checkpoint from this committed source. Restore the
reasoning-enabled profile that previously progressed through the gates; retain the 45-minute outer
cap and one-world scope. Grade the guard independently:

1. no identical read-only request may recur beyond the correction and one final violation;
2. recovery through an environment action or gate transition must reset the guard;
3. persistent repetition must end promptly with `controlled_stop: no_progress_tool_loop`;
4. if G3 opens, resume the preregistered NAV terrain/reachability criteria unchanged.

— **Sol**

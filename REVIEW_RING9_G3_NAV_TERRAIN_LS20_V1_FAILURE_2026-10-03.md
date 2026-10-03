# Review: Ring 9 G3 NAV terrain ls20 v1

**Type:** `LIVE_RUN_REVIEW`  
**Disposition:** infrastructure failure before G1 closure; G3 terrain slice not evaluated  
**Author:** Sol (Alpha build seat)  
**Date:** 2026-10-03

## Direct observations

- Kaggle worker status: complete.
- Behavior window: 15 minutes.
- Environment actions: 8.
- Gate events: eight `G1-EGO` action-pair probes.
- Gate answers: G0 only.
- G2 and G3 events: zero.
- Benchmark token accounting: zero generated tokens.
- Turn ledger: 8 controller turns and 689 Duck turns.
- Requests recorded: 695.
- Score: zero; levels cleared: zero. Neither grades this checkpoint.

The eight controller actions completed the intended two probes for each of `ACTION1` through `ACTION4`. The run then reached the G1 explanation handoff and never produced an admissible model answer.

## Failure mechanism

The model returned a native `python` tool call whose arguments ended mid-string:

```text
{"code": "# Verify ego node identity: O node 10px, b node 15px at rows47-49, glyphs separate\nfor
```

The local dispatcher correctly treated that as an empty/invalid call. The harness then appended the provider's malformed `function.arguments` string to assistant history.

vLLM reparses all prior assistant tool calls before serving the next completion. Every subsequent request therefore failed before inference with HTTP 400:

```text
Unterminated string starting at: line 1 column 10 (char 9)
```

The poisoned history survived every outer retry, producing 687 repeated failures until the behavior deadline.

## What the evidence supports

- G1's deterministic probe scheduler still executed exactly eight controller-owned actions.
- The inference server started and successfully answered earlier calls in the same G1 turn.
- A malformed provider tool call can poison all later vLLM requests if stored verbatim.
- The v1 run did not exercise `nav_terrain.py`, the G3 terrain palette, footprint routing, target falsifiers, or terrain-ledger typing.

## What the evidence does not support

- It does not show that floor/wall inference failed.
- It does not test reachable or unreachable target predictions.
- It does not test the G3 lifecycle repairs.
- It does not justify changing the G3 terrain design.

## Repair

The native-tool boundary now validates that `function.arguments` decodes to a JSON object before adding the assistant message to history.

- Valid tool calls are unchanged.
- Malformed raw calls remain visible in the response diagnostic.
- The persisted history receives the valid empty object `{}`.
- Dispatch returns the ordinary missing-argument error.
- Duck can then submit a complete replacement call without vLLM rejecting the conversation itself.

A regression test reproduces the exact sequence: truncated native arguments followed by a valid environment action. It asserts that the second request contains parseable prior arguments and that the malformed diagnostic remains recorded.

Validation after repair: **108 passed**, including the malformed-history test and the 95-test NAV/G3 regression set. Ruff passed.

## Retest decision

The preregistered terrain checkpoint remains entirely open because v1 stopped before its subject. A repaired v2 should preserve the same world, model, 64-action cap, 900-second cap, and grading criteria so the runs remain comparable.

— Sol

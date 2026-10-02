# Review: Ring 9 G3 NAV reachability v6

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Evidence:** downloaded Kaggle v1 output, frozen receipt, lossless gate artifacts, transcript

## Result

V6 proves that the strict G1 probe controller and the reasoning-enabled local model can identify and
explain the ls20 ego. It does not prove G1 closure, G2 counter masking, G3 lever discovery, or NAV
reachability behavior.

## Direct observations

- Kaggle completed in 19m 23s with 8 environment actions, 31,664 generated tokens, zero levels
  cleared and no harness crash.
- The executed action sequence was ACTION1 ×2, ACTION2 ×2, ACTION3 ×2, ACTION4 ×2.
- Eight G1 probe envelopes, events, outcomes and paired before/after frame records were persisted.
- Duck identified the only directly controlled subject as the 25-cell blue/orange compound body.
- It described ACTION1/2/3/4 as rigid translations up/down/left/right by five cells, with the full
  footprint invariant.
- It distinguished the changing edge strip as an off-target progress-bar candidate and deferred its
  meaning to G2.
- Duck submitted a detailed embodied-ego explanation and a prospective PATTERN_TRANSLATION test.
- The first evidence reference in the submitted answer was mistyped. The observed ID is
  `E-4736281dd82481b9`; Duck supplied `E-4736281dd8281b9`.
- The gate rejected the answer. The runtime then stopped with `no_progress_tool_loop` because the
  rejected answer arrived after the guard's earlier correction.
- The updated evaluator accepts the v6 receipt and world binding. It correctly reports no accepted
  G1 answer and no joined prospective demonstration.

## What the evidence supports

The model used the eight controlled transitions to form a stable, human-readable ego model. The
controller enforced the intended action order and persisted adequate lossless evidence. The failure
was at the interaction contract between a semantically useful answer and an opaque identifier, then
at the guard's classification of the rejected submission.

## What the evidence does not support

The submitted G1 answer was never accepted, and its future prediction was never executed. Therefore
the run does not establish a certified EgoLaw. No counter candidate was tested or masked. No terrain,
reachability, collision, lever sweep or G4 behavior occurred. Zero levels cleared is outside this
checkpoint's immediate aim but must not be restated as a G3 result.

## Engineering consequence

The next source slice must distinguish observation, environment action, gate transition and contract
repair. A rejected answer gets a bounded correction turn and makes correction the next binding
operation. Controller-owned evidence identifiers must use the existing certified-field mechanism so
Duck does not transcribe hashes. Explicit wrong identifiers remain wrong and must be rejected; the
controller must never silently rewrite a claim.

— **Sol**

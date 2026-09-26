# G1 closure local pilot review: `ls20` v2

**Date:** 2026-09-22  
**Run:** `variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260922_174250_ring9-g1-closure-local-ls20-v2/`  
**Model:** `Qwen/Qwen3.6-27B` through OpenRouter  
**Checkpoint verdict:** **G1 PASS; G2 ENTRY CONFIRMED; G2 CLOSURE BLOCKED BY CONTROLLER CONTRADICTION**

## Claim boundary

This run grades G0 and G1 only. Its zero game score does not grade the checkpoint. The run ended
at the experiment deadline after 11 admitted actions. It supplies no level win and no completed
G2 counter product.

## Direct observations

- G0 recorded `ACTION1` through `ACTION4`, all without coordinates, and made no semantic action
  claim before observation.
- G1 admitted exactly the ordered Delphi sequence `1,1,2,2,3,3,4,4`.
- Every opening action produced a 50-cell translation ledger for one 25-cell two-color composite
  plus a spatially separate two-cell rewrite at the bottom bar.
- Duck explained the controlled subject as the joined 10-cell orange and 15-cell blue composite.
- Duck inferred exact opaque laws: `ACTION1` up five, `ACTION2` down five, `ACTION3` left five,
  and `ACTION4` right five.
- Two G1 submissions were rejected for exact footprint/scope mismatches. Both reasons were visible;
  Duck corrected them on the next submission and the third answer was accepted.
- Duck froze a new-state `PATTERN_TRANSLATION` prediction for the entire 25-cell composite under
  `ACTION1`.
- Transition 9 observed the predicted displacement `[-5, 0]`. The verifier recorded `SUPPORTED`,
  kept the two remote bar cells separate, created the `EgoLaw`, and closed G1.
- G2 opened with the demonstrated 25-cell post-action ego footprint and ranked the first non-ego
  visual object as a one-cell target at `[32,20]`.
- G2 admitted two approach actions. Their spatially separate bottom-bar rewrites supported a
  scheduled bookkeeping candidate: a connected two-row bar, rewrite `11→3`, two cells per action,
  witnessed under two different opaque actions.

## What the evidence supports

The active controller can force the served Duck through the intended G1 sequence, require an
explanation rather than accept raw movement, and demand a future full-body prediction before
advancing. The resulting `EgoLaw` is grounded in eight discovery transitions and one prospective
demonstration. G2 receives the demonstrated complete ego footprint rather than a single-color
fragment, and its ranked collision opening starts in the specified object order.

The evidence also supports the practical value of visible correction payloads. Duck recovered
from two geometry errors instead of repeating an opaque rejection indefinitely.

## What the evidence does not support

- It does not establish G1 repeatability across another seed, game, model, or controller type.
- It does not test CLICK or HYBRID G1 branches.
- It does not establish boundary collision behavior for the embodied ego.
- It does not establish the counter's terminal consequence, reversible mask, or full G2 product.
- It does not establish a lever, environmental force, inert object, winning condition, or level
  transfer law.

## G2 contradiction exposed by the run

After transitions 10 and 11, G2 entered `ANSWER_REQUIRED`. The controller then rejected further
actions with “submit its explanation before another action.” The explanation path simultaneously
failed with “no unused intervention available for prospective confirmation,” even when Duck
declared a prediction under an action not used by the candidate witnesses. The gate view supplied
no answer template.

This is a controller defect, not a failure to recognize the counter. Duck had already described
the candidate as a two-row bar depleted by two cells per action and proposed a fresh `ACTION2`
recolor prediction. The protocol gave it no legal transition from explanation to demonstration.

Source tracing identifies the exact cause. NAV/HYBRID piloting intentionally leaves
`_probe_actions` empty because Duck chooses approach controls. G2 correctly selected the blocked
`ACTION3` transition as its counter-only demonstration action and stored it in
`_counter_only_action`. During `submit_answer`, however, `_current_action()` exposes that stored
action only after status is already `DEMONSTRATION_REQUIRED`; the call occurs while status is
still `ANSWER_REQUIRED`. It therefore falls through to the intentionally empty `_probe_actions`
list and raises the false “no unused intervention” error. The repair is to validate the stored
counter-only action directly before changing status, then let `next_probe()` expose it after the
transition to `DEMONSTRATION_REQUIRED`.

## Engineering decision

G1 is promoted to **LIVE CONFIRMED on one `ls20` local pilot**. Development moves to G2. The next
slice must make the G2 state machine internally consistent:

1. `ANSWER_REQUIRED` must accept an evidence-bound explanation and freeze its novel prediction.
2. The accepted answer must move to `DEMONSTRATION_REQUIRED` and expose the predicted unused
   action as the next authorized probe.
3. The demonstration result must be scoped to the declared counter cells while preserving ego
   motion and other remote changes separately.
4. A supported recurrence may establish the bookkeeping mechanism, but G2 must remain open until
   it observes the min/max consequence or records the bounded pending-boundary state required by
   the gate thesis.
5. Only then may it emit a reversible `MaskLaw` and open G3.

The two G1 geometry rejections are residual friction. A follow-up normalization should derive
`scope.cells` from `before_footprint` when one is omitted, and should canonicalize equivalent cell
ordering. That improvement is secondary to the blocking G2 contradiction.

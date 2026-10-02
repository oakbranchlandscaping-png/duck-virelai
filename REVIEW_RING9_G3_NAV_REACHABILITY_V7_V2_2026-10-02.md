# Review: Ring 9 G3 NAV reachability v7, Kaggle version 2

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** G1 checkpoint passed; G2 opened; run ended at the behavior time cap

## Frozen execution identity

- Source commit: `0a2e4dcb2749bcc93d8632499e04db0b90743a35`.
- Package SHA-256: `42199149aa4a640af04273bb01419b8429f159d8da7d4ede1930034eda36d6bd`.
- Source-manifest SHA-256: `a2a45dc09db60e4153fa159f09d64f82c0727ae225bfd07e1f857fe9abefd562`.
- Model: `Qwen/Qwen3.8-27B-FP8`, pinned revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.
- World: `ls20-9607627b`, one pass, one concurrent game.
- Behavior limits: 96 environment actions and 2,700 seconds.
- Execution receipt: PASS; SHA-256
  `90c55a34a32cba764c51ab79582606cb43111e0a59723329aec5f9432fbcfc42`.

## Direct observations

The run completed its intended G1 sequence in nine actions:

1. `ACTION1` twice;
2. `ACTION2` twice;
3. `ACTION3` twice;
4. `ACTION4` twice;
5. one prospective `ACTION1` demonstration.

Duck identified the same rigid 25-cell orange/blue body across the eight controlled probes. It
described the action laws as five-cell translations: up for `ACTION1`, down for `ACTION2`, left for
`ACTION3`, and right for `ACTION4`. Its explanation cited all eight probe outcomes, rejected two
alternatives, supplied a falsifier and limitations, and kept the recurrent HUD-bar delta outside the
ego mechanism.

The controller accepted the explanation and changed G1 to `DEMONSTRATION_REQUIRED`. Before the
ninth action, it froze a prediction that `ACTION1` would move the complete 25-cell footprint five
rows upward without deformation. The resulting frame matched that prediction. A separate two-cell
bar delta was present and was not attributed to ego motion. The controller then recorded G1 as
`CLOSED`.

The next automatically supplied card was G2-COUNTER. It carried the established world model entry
`[G1-EGO] ego: EMBODIED_EGO`, armed the `COLLIDE_WITH_EVERYTHING` opening sweep, ranked a one-cell
visual object as the first target, and supplied a `PILOT_TO_CONTACT` probe. No G2 action was executed:
the following model request timed out as the 45-minute behavior budget expired.

The benchmark recorded 45 minutes, nine actions, 68,674 generated tokens, zero levels cleared and
score zero. Per-action generation was highly uneven; the prospective demonstration consumed 24,864
generated tokens. The solver ledger separately reports 72,258 tokens, so token totals should not be
treated as identical across accounting surfaces.

## Evaluation

I reviewed all eight cited transitions and the prospective demonstration directly from the saved
before/after grids. The frame evidence supports the declared ego identity, all four action laws, the
prospective nature and novelty of the demonstration, its declared scope, and the separation of the
HUD-bar change from ego motion. The receipt-bound human review covers all nine evidence IDs.

The complete evaluator result is PASS:

| Grade | Result |
|---|---|
| Execution receipt | PASS |
| Human frame review | PASS |
| Protocol | PASS |
| Coverage | PASS |
| Explanation | PASS |
| Prediction | PASS |
| Demonstration | PASS |
| Correctness | PASS |
| Overall G1 checkpoint | **PASS** |

Evaluator SHA-256: `3a44c8e57f169e3d7e8a84241f7cfaea9f60d72d84d4d942f789c57a8bafb833`.

## What the evidence supports

The bounded gate-contract repair worked on this live NAV world. Duck did not merely name an ego. It
systematically probed all four controls, explained the controlled object and its movement grammar,
made a new scoped prediction, demonstrated it, recognized closure, and received the next gate. This
meets the preregistered purpose of v7.

The run also shows that controller closure is operational: success was recognized after the required
demonstration, and the next target was issued without asking Duck to keep studying G1.

## What the evidence does not support

- It does not establish G2 counter identification, masking or closure; G2 issued a target but no G2
  action occurred.
- It does not exercise G3 NAV reachability or G4 lever typing.
- It does not show level completion, game completion or competitive score.
- It does not establish behavior on CLICK or HYBRID worlds.
- It does not establish that the current model/runtime combination is efficient enough for a full
  gate stack.

## Engineering consequence

V7 should be accepted as a successful G1 checkpoint rather than rerun for more G1 evidence. The next
live checkpoint can begin from the now-proven G1-to-G2 handoff. Before spending another Kaggle window,
the inference cadence needs a bounded-effort repair: nine simple environment actions consumed the
entire 45-minute budget and 68,674 generated tokens. That repair must preserve the successful gate
contract, evidence records and controller ordering. Its purpose is to let the model execute the
already-supplied G2 pilot step promptly; it must not weaken G2 into a broader world-understanding
requirement or make counter monitoring block the later lever sweep.

The request timeout is therefore runtime friction after checkpoint success, not evidence that G1 or
the gate architecture failed.

— **Sol**

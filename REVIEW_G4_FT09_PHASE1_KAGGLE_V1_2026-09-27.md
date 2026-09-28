# Review: G4 ft09 Phase-1 Kaggle checkpoint, notebook version 1

**Reviewed:** 2026-09-27
**Author:** Claude (Alpha build seat), signed
**Run:** notebook `stephenkaskin/taaf-virelai-ring9-g4-ft09-phase1-v1` v1. Output is at
`runs/kaggle-ring9-g4-ft09-phase1-v1/output/`; a review copy is at `virelai-review/ft09v1/`.
**Package:** `ring9-g4-ft09-phase1-v1` (`7778750`), built from source `8cfb782`.
**World / model:** `ft09-0d8bbf25`; `vrfai/Qwen3.6-27B-FP8` via local vLLM.
**Graded against:** the frozen `checkpoint-preflight.json`, with P, C1–C7 and I1–I4.

## Verdict

**The run stalled in G2, before G3, on a controller defect.** Precondition P was not met. Under the
preregistered rule, the G4 criteria are **ungraded, not failed**.

G2 found a real counter candidate, but it demanded a prospective test on a "counter-only" action.
No such action exists in ft09, because every counter tick in this world comes with a control
effect. The card said `SUBMIT_GATE_ANSWER`, but its answer template was null, and every answer was
rejected. This is the third "no legal move" deadlock: ls20 G2 on 09-22, vc33 G4.2 on 09-27, and now
ft09 G2.

| Item | Grade |
|---|---|
| Integrity | **PASS.** The downloaded `execution_receipt.json` is byte-identical to the package receipt. |
| I1: CLICK routing from metadata | **PASS.** G0 answered ACTION6 with coordinates; G1 closed `POINTER_GOD_MODE`. |
| I2: G2 closes, does not stall | **FAIL.** G2 stalled in `ANSWER_REQUIRED` with no admissible exit. |
| I3: G3 click sweep | **NOT REACHED** |
| I4: no ticker contamination | **NOT REACHED**, though see the counter finding below. |
| P: G3 closes with ≥ 2 levers | **NOT MET**, so C1–C7 are ungraded. |
| Continuity prediction (filed before output) | **UNTESTED**, because G4 was never reached. |

## Timeline (benchmark history and kernel log)

- Benchmark start was at about 588 s. The G0-G4 receipt was verified.
- Actions 1–56 all fell between about 51 s and 1,492 s of benchmark time. All 56 were G2 probes
  (`G2-COUNTER:PROBE:1..56`), and each clicked a different coordinate.
- After action 56, **no further action was taken for about 2.5 hours**. The run ended `cancelled`
  at the 10,800 s deadline with score 0 and 0 of 6 levels.
- Tokens: 365,776 in total, of which 53,491 are attributed to actions. Duck kept working the whole
  time.

## What ft09 showed (direct observation)

- **54 of the 56 clicks changed nothing at all**, including no counter tick.
- Clicks 55, at (36,36), and 56, at (44,36), each changed 38 cells:
  - a 36-cell block at the clicked site, rewritten 9→8 (a 6×6 control);
  - 2 cells of a bottom bar (row 63), rewritten 12→11.
- G2 correctly built the candidate `COUNTER-CANDIDATE-52a9fae8c5c551c9`: a horizontal bar on row 63
  of 64 cells, with rewrite 12→11 at 2 cells per transition.
- **The bar ticks only on effective clicks.** It did not move on any of the 54 null clicks. The
  historical note described ft09's bar as an "independent ticker"; this run gives two supporting
  and 54 negative data points against the "independent" reading, at least for this opening.
  - If this holds, masking the bar is enough to take the ticker out of orbit fingerprints, and
    the I4 risk shrinks. That is a two-point observation, not yet a law.

## The defect

`CounterGateMachine._select_counter_only_action` (`virelai_gates.py:1083`) looks for a witness
transition whose changed cells all lie inside the bar footprint. In ft09 both witnesses also
changed the clicked control, so the function returned `None`. What followed:

- The status was set to `ANSWER_REQUIRED` anyway (L1456–1458).
- `answer_template()` returned `None`, because it needs the counter-only action.
- `submit_answer` rejected every answer with "G2 has no isolated counter-only intervention for
  prospective confirmation" (197 occurrences). The correction text told Duck to "use
  answer_template as the exact object shape", which was null (311 null-template cards).
- `next_probe` offered no action.

Duck's reasoning in the transcript reached the right diagnosis by itself: "the G2 counter gate
CANNOT be completed in the normal way because there's no counter-only action." It had no way to act
on that diagnosis.

**Triage:** this is a lifecycle defect. The first broken layer is G2's closure path, which assumes
a counter-only intervention exists. That holds in worlds with a clicked counter object, such as
vc33, and fails in worlds where the counter counts effective moves.

## Repair options (for the Director)

1. **Footprint-scoped demonstration on a witness action (recommended).** When no counter-only
   witness exists, use the latest witness intervention. The frozen prediction is scoped to the bar
   footprint only: "this click rewrites exactly 2 bar cells 12→11". Changes outside the footprint
   are allowed and recorded. The prediction is still frozen before the action and graded against
   the frame. Grading stays conservative: any extra 12→11 rewrite anywhere counts as a
   contradiction, so a world effect cannot produce false support. The cost is one more press of a
   control during G2. It flips back, and it is recorded.
2. **Close G2 without prospective confirmation** when no counter-only witness exists, as a
   provisional mask, following the 09-23 provisional-close ruling. This is cheaper but weaker
   evidence.
3. **Also, independent of 1 or 2: a no-legal-move guard.** This is the third deadlock of the same
   shape. The design's controller rules (§7.12) already require "an explicit degraded state on
   controller failure". Proposal:
   - an invariant test, which asserts that every reachable gate state offers an admissible probe,
     an answer path with a template, or an explicit terminal state;
   - a runtime watchdog, which ends gated work with a recorded `CONTROLLER_NO_LEGAL_MOVE` state
     instead of idling to the deadline.

## What this run does not establish

- Anything about G3 or G4 on ft09, the Phase-1 drain, the boundary release, or the continuity
  prediction.
- Whether the guided G4-A target (`G4-A`, committed after this package was built) works live. This
  run used the scripted `8cfb782`. The same G2 defect would stop a guided run too, so G2 must be
  repaired first.

— Claude, Alpha build seat, 2026-09-27

# Review: Ring 9 controller ownership ls20 v2

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-03  
**Verdict:** **FULL PASS — 9/9 preregistered criteria**  
**Executed source:** `4e1be00f59c1c430391603c572bfd1dcaa4f87cb`  
**Executed evidence:** `runs/kaggle-ring9-controller-first-ls20-v2/`

## What this checkpoint asked

Could the ownership-parity build carry the NAV world `ls20-9607627b` from metadata through a
certified counter mask and into G3 while the controller selected every environment action and Duck
was used only where semantic synthesis was needed?

The answer is **yes**. The notebook completed without a crash in 3 minutes 33 seconds. It used 16
environment actions and stopped at the explicit action cap. Score and level completion were zero,
which were explicitly outside this checkpoint's success criteria.

## Preregistered result

| # | Criterion | Result | Executed evidence |
|---|---|---|---|
| 1 | G0 closes through the controller with no model request | **PASS** | G0 answer is `G0-CONTROLLER`; the first model request occurs only at G1's semantic boundary. |
| 2 | All eight Delphi actions run through the controller in strict order | **PASS** | Actions 1–8 are `A1,A1,A2,A2,A3,A3,A4,A4`; every probe envelope says `CONTROLLER`. |
| 3 | Duck supplies an accepted human-readable ego explanation and movement law | **PASS** | Duck identifies the orange-and-blue 5×5 embodied ego and the exact five-cell translations for A1–A4, with eight evidence references, limitations and a falsifier. |
| 4 | The controller executes a supported prospective demonstration and closes G1 | **PASS** | Action 9 is controller-owned A1; its observed translation is `[-5,0]`, the comparison is `SUPPORTED`, and G1 closes. |
| 5 | Deterministic G2 pursuit forms the recurrent counter candidate without a Duck action | **PASS** | Controller actions 10–11 produce the same 84-cell candidate, `COUNTER-CANDIDATE-3fce209a36a83900`, with two cells rewritten `11→3` per transition. |
| 6 | The controller submits the certified G2 answer and executes its demonstration | **PASS** | The controller records the recurrent trigger, mechanism and footprint; action 12 is controller-owned and its counter comparison is `SUPPORTED`. |
| 7 | G2 installs the complete counter mask and enters G3 | **PASS** | The G2 product is `LOCKED_AS_MASK_BASELINE`; mask law `MASK-V1-615ca9b230ffa5bf` covers the full 84-cell footprint, and actions 13–16 are G3 events. |
| 8 | Every environment action is controller-owned; Duck calls occur only at semantic boundaries | **PASS** | All 16 probe envelopes name `CONTROLLER`. The 19-row turn ledger has 16 controller action rows and three Duck rows, all attached to the same G1 explanation boundary. |
| 9 | The run ends at a controlled boundary without crashing | **PASS** | Final state is `gave_up` at the configured 16-action cap; the notebook status is complete and the artifacts contain no runtime failure. |

## What the run directly shows

The controller owns the mechanical ladder through G2. Duck never selected an environment action.
Its seven model requests were all confined to the G1 semantic explanation at analysis step 9. The
accepted explanation says what the ego is, how it moves, why the evidence supports that law, what
remains uncertain, and what future observation would falsify it.

The counter gate performs its intended narrow job. Two deterministic pursuit transitions expose a
stable, recurrent 84-cell HUD process across rows 61–62 and columns 13–54. Each transition changes
two cells from color 11 to color 3. The controller certifies this as a mask baseline, demonstrates
the prediction once, closes G2, and stops asking Duck to reason about the counter.

The four remaining actions prove that G3 actually started and that the mask is being used. The
controller targets the first ranked object and records both refused wall-edge moves and traversed
floor moves. Counter-only change is attributed separately from ego motion. The active counter
policy is `MASK_AND_IGNORE_AFTER_G2`, so the recurring HUD delta does not become a new visual target
or wake Duck.

## Comparison with v1

| Measure | v1 | v2 |
|---|---:|---:|
| Runtime | about 20 minutes | 3 minutes 33 seconds |
| Environment actions | 11 | 16 |
| Duck-selected environment actions | 1 | 0 |
| Ledger tokens | 44,370 | 8,514 |
| G2 outcome | stalled on semantic answer | certified, demonstrated and closed |
| Furthest gate reached | G2 | G3, with four controller actions |

This is strong evidence that the ownership repair removed the architectural friction seen in v1.
Deterministic mechanics proceed without model delay, while Duck still performs the semantic work
that code cannot supply.

## What this run does not establish

It does not establish G3 closure, lever discovery, G4 entry, live G4 NAV parity, a win, score,
cross-death memory, or cross-level transfer. The ordinary ego-motion events in G3 remain
conservatively labeled `AMBIGUOUS_EGO_MASKED`; this did not block routing in the bounded run, but it
should be observed during the longer G3 sweep rather than declared solved from four actions.

The executed receipt is byte-identical to the packaged receipt, so these findings apply to the
frozen v2 package. They should not be projected onto later source changes without a new package and
run.

## Decision and next rung

Close this checkpoint. Repeating the same run would add little evidence.

The next checkpoint should extend **the action budget, not the model's authority**, and test the G3
NAV contact sweep on ls20. Its target is to finish ranked contact attempts or find the first positive
lever while preserving these invariants:

1. every approach, collision, refusal and abandonment action is controller-owned;
2. the complete counter footprint stays masked and does not re-enter the target list;
3. floor, wall and temporarily unreachable labels update from observed movement and world deltas;
4. a target can be abandoned after the controller exhausts its reachable contact plan;
5. Duck wakes only when a positive or structurally ambiguous effect needs a human-readable account.

The Director subsequently tightened this exit criterion: the next run must expose the complete
prepopulated visual-object roster and execute every row. Each eligible object must end as
`REACHABLE`, with contact evidence and a physics type, or
`UNREACHABLE_IN_CURRENT_WORLD_STATE`, with an exhausted-route certificate and explicit reopen
conditions. Build record: `BUILD_SLICE_G3_TARGET_EXECUTION_LEDGER_2026-10-03.md`.

After a lever is confirmed, the following checkpoint should exercise the G4 NAV study cycle: repeat
activation until null or a proven cycle, then ask Duck to describe the lever's trigger,
transformation and consequences in the project's physics grammar.

— Sol

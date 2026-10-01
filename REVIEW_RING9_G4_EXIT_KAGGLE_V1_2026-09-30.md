# Review: Ring 9 G4 CLICK exit, Kaggle v1 (ft09 + vc33)

**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed

**Run:**
- **Notebook:** `stephenkaskin/taaf-virelai-ring9-g4-exit-v1`, version 1.
- **Package:** `ring9-g4-exit-v1` (`10b1310`), source `d2bf323` (R9-R06 to R9-R14).
- **Outputs:** `runs/kaggle-ring9-g4-exit-v1/output/`.
- **Timing:** started 00:43 UTC; the behaviour window took 18 min 44 s.

**Graded against:** the criteria frozen in the package's `RUN.md`, all read from the run's artifacts.

## Verdict

**EXIT is not met. The CLICK branch of G4 stays open.**

**ft09 passed everything, through G4-C:**
- G4-B: Duck froze 8 predictions, and all 8 were SUPPORTED.
- Duck's description was accepted on the first submission.
- G4-C: one law test on a board not tested before, SUPPORTED. This certified the `LeverReactionLawSet` (COMPLETE).
- The run then ended with a planned stop.
- Both live fixes worked:
  - **F1:** the orientation was accepted on Duck's first turn. Last time it took 5 turns and 6 minutes.
  - **F2:** every freeze stamp now matches the current transition (109 to 117). Last time they were all stuck at 57.

**vc33 never reached G4-B. The study pressing one of its levers finished level 1.**
- vc33 has 2 levers.
- While mapping the second lever (E0005), the controller pressed it 6 times. The 6th press completed level 1 (1 to 2, score 0.26).
- That closed the study with status CLOSED_BY_LEVEL_BOUNDARY, and the run ended cleanly ("the level changed during G4").

This is risk 2 from the upload status, now observed. It is a real result about the ladder, not a code defect:
- **The goal is on a lever's path.** vc33's level-1 goal is one of the states E0005 passes through when pressed repeatedly.
- **So the exit can't be met here.** Pressing E0005 until its sequence of states repeats or stops changing, which is what the study does, reaches that goal before the study can finish. A complete G4 on vc33's level 1 is therefore out of reach for the ladder as built.

## What vc33 showed (from the frames)

- **G2:** the counter is a 64-cell bar on row 0, rewritten 7→4 on every transition. The controller labelled it EVERY_TRANSITION. The trigger class was **not OPEN**, so deviation 1 did not come up.
- **G3:** 10 click probes and 2 confirmations found **2 levers**. Each press rewrites about 264 cells, all of them away from the lever itself.
- **E0004 (G4-A):** 3 presses moved the board through 3 new states. Further presses changed only the counter. Duck explained this as an end state that further presses don't change, and the explanation was accepted.
- **E0005 (G4-A):** its states were `4a29 → 55db → c412 → 3c6a`, which is **exactly E0004's run in reverse**. It then went on to 2 more new states, and the next press completed the level.
  - So the two levers move one shared quantity in opposite directions, and the top end of that range is the level goal.
- **Duck had already said this.**
  - Its orientation note: *"E0005 reverses this. They may be inverse operations on the same region."*
  - Its E0004 competing model: *"the absorbing state may be reversible by pressing E0005."*
  - The record now contains the evidence. But no frozen prediction came before it, so under the falsification law it cannot be certified. It would have been G4-B's first test.

## Criteria

| Criterion | ft09 | vc33 |
|---|---|---|
| I2 receipt | PASS (byte-identical) | (same run) |
| M5-1 cards | PASS. Largest card 11,748 characters against the 16,200 budget; guard never fired. Largest request 16,788 tokens. | PASS. Largest card 10,993 characters; largest request 16,323 tokens. |
| M5-2 | PASS. G0–G4.1 had 75 controller rows and 0 requests. Orientation accepted on turn 1 (43 s); its note subject was the current gate, the exact F1 case. | PASS. 15 controller rows; orientation accepted on turn 1 (28 s). |
| G2 / G3 | PASS, same as the earlier runs (8 levers) | PASS. Counter EVERY_TRANSITION (not OPEN); 2 levers; none UNRESOLVED. |
| A (G4-A) | PASS. All 8 levers explained. Same-level death at transition 88; E0056 was re-studied. | PASS as preregistered ("or interrupted / CLOSED_BY_LEVEL_BOUNDARY"). E0004 explained; E0005 interrupted by the level change. |
| B (G4-B) | PASS. 8 envelopes, all CONTROLLER; each action equals its frozen prediction. Stamps 109–116, each graded one transition later. All levers pressed. Description accepted first time. `open_conditions` = [] = recorded. | Not reached (ungraded) |
| B-2 replay | PASS. All 8 grades and observations re-derive exactly at `d2bf323`, using a corrected replay (see F-R2). | n/a |
| C (G4-C) | PASS. L1 was untested (the novelty check accepted it) and cites relation 0. The CONTROLLER took it at stamp 117 and graded it at 118: SUPPORTED. The `LeverReactionLawSet` is COMPLETE; replay certifies the same L1. | Not reached (ungraded) |
| E (clean stop) | PASS. `planned_stop: … through G4-C`; no request afterwards. | PASS. `planned_stop: the level changed during G4…`; no request after transition 20. |
| **EXIT** | ft09 COMPLETE | vc33 CLOSED_BY_LEVEL_BOUNDARY → **NOT MET** |
| N-1 | PASS | PASS |
| I1 / I3 / I4 | PASS. Every envelope carries `g3_inherits_g2_nulls: true`, and the memory artifacts were written. | PASS |

## Reported figures (R)

**ft09 (118 actions, 1 reset, 15.8 min):**

| Phase | Duck turns | Requests | Time |
|---|---|---|---|
| Orientation | 1 | 4 | 0.7 min |
| Rest of G4-A | 11 | 23 | 9.3 min |
| G4-B | 9 | 16 | 4.6 min |
| G4-C | 1 | 3 | 0.7 min |

- G4-B ran about 20 s per prediction. The description turn made 3 `gate_audit` queries first, then submitted, and it was accepted. The previous run had invented two levers (E0058 and E0059).
- **Description (verbatim):** "The 8 levers (E0053-E0057, E0060-E0062) are independent TOGGLE switches… No lever affects any other lever's region, and no lever causes changes outside its own 36-cell area."
- **Law test L1:** press E0053 from a board where every lever has been pressed once since G4-A. Duck expected E0053 to step and nothing else to change, and that is what happened.
- **Weaknesses, as before:**
  - G4-C on ft09 is easy, as preregistered.
  - The "competing model" restates the claim instead of offering a rival.

**vc33 (26 actions, 3.0 min):**
- 3 Duck turns: the orientation, then E0004's explanation, which went over its time budget once before being accepted.
- 2 levers, both of the same class: each press rewrites a large region away from the lever.
- After the level change, 14 new visual entities appeared. Level 2 was never studied.

## Findings

**F-R1. The record builder drops level completions (code; replay tooling).**
- `tools/record_from_artifacts.py` keeps a step's boundary only when `state` is not `NOT_FINISHED`.
- A completed level reports `NOT_FINISHED` with `level_completed: true`.
- So the vc33 record lost its level change. Replay then disagreed with the live run: it stayed in G4-A with PROBE_REQUIRED.
- **Fix (verified on a scratch copy):** also keep the boundary when `level_completed` is set or the level number changed. With that change, replay matches the live run exactly: G4-A closed at the level boundary, and `ladder_end` gives the same message.

**F-R2. Replay submits G4-A answers in the order the machine asks for them, not the order they were recorded (code; replay tooling).**
- At transition 88, after the death, Duck used its turn to press E0057 itself. Its stated intent: "test if game accepts actions after game_over".
- So E0057 was studied before E0056, and Duck answered in that order. The live gate accepts either order.
- Replay submitted the recorded queue in order. At the end the machine asked for E0056's answer first, the next recorded answer was E0057's, and replay failed with "intervention must exactly match".
- **Fix (verified on a scratch copy):** match each queued answer to the lever the template names. With that change, ft09 replays to G4-C SATISFIED and reproduces all 9 grades.
- This is also the action where the controller-determinism claim from the last review stops holding. This run matches `ring9-g4b-ft09-v1` for 88 actions, not 108, because Duck took an action on its own turn.

**F-A1. A G4-A falsifier is prose; nothing checks it (architecture; for the Chief Engineer).**
- Duck's accepted E0004 explanation gives as one of its falsifiers: "pressing E0005 reverses the E0004 orbit back through the recorded states."
- The controller's next run did exactly that.
- The explanation stays accepted, with nothing flagged.
- The falsifier was itself mis-specified: what it describes would confirm Duck's competing model, not contradict its claim. But the general point holds:
  - G4-A falsifiers are text.
  - Only G4-B and G4-C predictions are checked against outcomes.
- I'm recording this, not proposing a fix.

## The exit question (plan-level; for you and Apex)

The ruled exit was a COMPLETE law set on level 1 of both worlds. vc33 shows that for some click worlds, the study's own experiments finish the level. No build fixes that inside level 1 without either knowing the goal in advance (which universality forbids) or stopping lever studies early.

Options, with my reading:

1. **Build the next slice so the study continues across the level change (G9 for CLICK).**
   - On level 2, the study re-identifies the levers and continues into G4-B and G4-C.
   - **Lean: this one.** It is the ladder's own next rung, and the evidence fits it: Duck's hypothesis that the two levers are inverses is still untested and would be G4-B's first prediction.
   - **Cost:** a real slice. The 14 new entities on level 2 need identity carry from level 1.
2. **Cap the length of a lever's study run in G4-A on level 1**, then move to G4-B with that lever's states partly mapped.
   - This lowers the chance of finishing the level but doesn't remove it.
   - It also weakens the study (the full range of states each lever moves through).
3. **Amend the exit so CLOSED_BY_LEVEL_BOUNDARY counts for vc33.**
   - **I recommend against this for this run.** Changing the criterion after seeing the result is the move preregistration exists to prevent.
   - If you want it, it should be a new ruling for a future run, and it would claim less: "the ladder runs until the world ends the level," not "the levers were described."

**Code work available now (no ruling needed):** F-R1 and F-R2 as a small tooling slice. Each would get a regression test that fails first, using these two records as fixtures.

— Claude, Alpha build seat, 2026-09-30

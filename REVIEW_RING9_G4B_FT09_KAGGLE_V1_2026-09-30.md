# Review: Ring 9 G4-B, ft09, Kaggle v1

**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed
**Run:**
- Notebook `stephenkaskin/taaf-virelai-ring9-g4b-ft09-v1`, version 1.
- Package `ring9-g4b-ft09-v1`, source `e1636b1` (R9-R06 to R9-R12).
- Outputs are in `runs/kaggle-ring9-g4b-ft09-v1/output/`.

**Graded against:** the criteria frozen in the package's `RUN.md` before the run, all read from
artifacts.

## Verdict

**The G4-B and clean-stop criteria all pass (B-1 to B-3, E-1); the orientation step carried a
defect.**

- **G4-B worked live.** Duck froze 8 predictions and the controller took all 8. All 8 were
  SUPPORTED, and the gate's grades re-derive exactly from the frames. Duck's description was
  accepted, and the ladder ended with a **planned stop**, not a crash. G4-B took 9 Duck turns and
  3.5 minutes.
- **Duck did the minimum, as predicted.** It pressed each lever once and predicted "only its own
  tile steps". It then described the levers as eight independent toggles. For ft09 that is
  correct and fully supported.
- **The orientation cost 5 turns and 6 minutes, because of a defect.** Duck's first orientation
  was refused, but the refusal message came after the whole card in the reply. That put it past
  the tool-output limit, so it was cut off and Duck never saw why. See F1.

**The live run repeated the previous live run exactly.** Its first 108 actions match
`ring9-memory-ft09-v1` action for action, including the death at transition 88 and the re-study of
E0056. The controller is deterministic across live runs.

## Duck's description of the lever set (verbatim)

> Each of the 8 toggle levers (E0053, E0054, E0055, E0056, E0057, E0060, E0061, E0062) is
> independent. Pressing a lever causes only that lever to step between its two states (S0↔S1). No
> lever's press affects any other lever, and no cross-lever interactions exist. The board outside
> the lever regions remains unchanged regardless of which lever is pressed.

- **Relation:** "Each lever is an independent toggle: pressing it steps only its own state with no
  effect elsewhere." It covers all 8 levers and cites P1–P8, all SUPPORTED.
- **Falsifier:** "A future graded prediction where pressing one lever causes a second lever to
  change state, or causes any cell outside the pressed lever's own region to change."
- **Limitations:** it holds for the boards tested on level 1, and there were no simultaneous
  multi-lever presses.
- **Weaknesses:**
  - The "competing model" restates the claim instead of offering a rival.
  - "No cross-lever interactions exist" is stated more universally than 8 tests support; the
    limitations line softens it.
  - Duck's first submission named levers E0058 and E0059, which don't exist (it filled in the 3x3
    pattern). The validator refused it, and Duck corrected it in the same turn.

## Criteria

| Criterion | Grade | Evidence |
|---|---|---|
| I2 receipt | PASS | Byte-identical to the package receipt |
| M5-1 | PASS | Largest card 11,132 characters, against a 16,200 budget; the 24,000 guard never fired |
| M5-2 | PASS, with F1 | G0–G4.1: 75 controller rows, 0 requests, about 6 s. Duck's first turn was the orientation, but it took 5 turns (F1). |
| G2, G3 | PASS | Identical to memory v1: the same counter, the same 8 levers, re-derived by replay |
| A-1 to A-3 | PASS | G4-A COMPLETE with 8 levers explained. A same-level death at transition 88 was re-studied (`life_restudies {E0056: 1}`). |
| **B-1** | PASS | G4-B opened after G4-A COMPLETE. All 8 G4-B envelopes carry executor CONTROLLER, and each action equals its frozen prediction. Every prediction was graded on a later transition. Duck took no G4-B action. **The freeze stamp is stale** (`declared_at_transition` 57 on all 8; F2). The ordering holds, but the stamp is wrong. |
| **B-2** | PASS | Replaying the run's own record at R9-R13 reproduces all 8 grades and observations exactly |
| **B-3** | PASS | All 8 levers were pressed. The description was accepted, and its one relation cites only SUPPORTED predictions that pressed its levers. `open_conditions` = [] = the recorded missing conditions. |
| **E-1** | PASS | `solver_note`: "planned_stop: every built gate is satisfied, through G4-B; …". The state is `gave_up` (the harness's label for a clean early finish), not crashed. There was no model request after G4-B closed. |
| N-1 | PASS | No gate idled |

## Reported figures

- **Actions:** 117, which is the 108 of memory v1, plus 8 G4-B presses, plus the reset.
- **Bar:** 4 ticks left at the end.
- **Duck turns and time by phase:**

  | Phase | Duck turns | Requests | Time |
  |---|---|---|---|
  | Orientation | 5 | 17 | 6.0 min |
  | Rest of G4-A | 15 | 32 | 12.9 min |
  | G4-B | 9 | 11 | 3.5 min |

  In G4-A, 6 of the explanations took two turns each, because Duck analysed first and answered on
  the next turn.
- **Largest request:** 45,671 tokens, during the orientation loop (F1). About 22k in G4-A, and 11k
  in G4-B.
- **Relation tests beyond single-lever runs:** 7 of the 8 predictions pressed a lever while
  earlier-pressed levers were away from their start state. That happened by construction, from the
  order Duck chose, not by design; it is still evidence of independence across boards.
- **Orientation notes accepted:** 1 (WORLD NAME: "3x3 lever grid at bottom-right, 8 toggle
  levers").

## Findings

**F1 — A refusal can be cut off before Duck reads it (code).**
- The memory and orientation replies put `data`, the full card at about 8–12k printed characters,
  before `error`. The tool output limit cut the reply and dropped the error.
- Duck's first orientation was refused because one note's subject was `G4.2-LEVER-ORBITS`, a gate
  not yet certified. Duck never saw the reason. It tried actions, got "The orientation turn is
  due" back each time, and took 5 turns to stumble onto a note set that passed.
- **Fix:** on a refusal, send the error first with a compact state (gate, next operation, the
  allowed note subjects), not the full card. Also accept the current gate's id as a note subject,
  since it is the natural subject of a note about the current study.

**F2 — The machine's observed step stops advancing after G2 (code).**
- `CyberneticGateMachine.observed_through_step` is the larger of the G1 and G2 counters, and
  nothing after G2 advances it. It stayed at 57 while the game reached 117.
- It is used as a freeze stamp in G3, G4-A, G4-B and G4-C, and for note timestamps. The ordering
  check still held, because every grade came after 57, but it could not catch a mis-ordered
  grade.
- **Fix:** advance a machine-level high-water mark on every recorded outcome and reset.

**F3 — Duck does the minimum when the minimum passes (behaviour, as predicted).** Nothing to fix
in G4-B. G4-C (built, R9-R13) now tests the description on an untested board, and vc33's levers
are a harder world.

## What this means for the exit

ft09 has now passed everything up to G4-B live. With R9-R13 (G4-C) and the F1 and F2 fixes, the
next run can be the ft09 + vc33 run the exit ruling asks for.

— Claude, Alpha build seat, 2026-09-30

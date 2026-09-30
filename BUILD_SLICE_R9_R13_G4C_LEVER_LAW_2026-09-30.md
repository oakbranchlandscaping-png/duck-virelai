# Build slice R9-R13: G4-C, the lever law set

**Revision label:** `R9-R13`
**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed
**Base:** `e1636b1` (R9-R12). This was built while `ring9-g4b-ft09-v1` runs live; that run uses
`e1636b1` and is unaffected.
**Governing rulings (Director, 2026-09-30; `BUILD_PLAN_G4_CLICK_COMPLETION_v11`):**
- The CLICK exit is a supported `LeverReactionLaw` set on **both ft09 and vc33**.
- G4-C is **its own thin gate**, and a contradiction **reopens G4-B**.
- **"New" means an untested action and board.**

## What G4-C does, in plain terms

G4-B ends with Duck's plain-language description of the lever set. G4-C checks whether that
description predicts something it has not seen.

1. **Duck freezes one new prediction** (`answer_kind: LAW_PREDICTION`). It has the same shape as a
   G4-B prediction, plus `from_relations`: the numbers of the description's relations it relies on.
   The card lists the relations by number.
2. **New is checked mechanically.** A prediction is refused if a graded prediction (G4-B or G4-C)
   has already taken the same action from the same counter-masked board.
3. **The controller takes it,** and the gate grades it exactly as in G4-B, on the same shared record
   of the level.
4. **SUPPORTED:** the gate emits the `LeverReactionLawSet`. It holds:
   - the description and its relations;
   - the open conditions;
   - the law test;
   - every test made.

   The ladder is then complete, and the controller ends the run cleanly.
5. **CONTRADICTED:**
   - G4-B's product is invalidated and its description withdrawn.
   - The contradicted prediction joins G4-B's record; it cannot be cited, but it stays.
   - Duck's card says which test contradicted the description.
   - Duck tests more, submits a revised description, and G4-C asks for a new test again.
6. **A level change** during G4-B or G4-C closes the study (G9 is not built), and the run ends
   cleanly.

## Changed

| File | Change |
|---|---|
| `inference/framework/g4c_gate.py` (new) | The G4-C adapter and contract. `later_contracts` and `later_adapters` register G4-B and G4-C in ladder order. |
| `inference/framework/g4b_gate.py` | `take`, the grading step shared with G4-C (extracted from `record_outcome`); `reopen`; the card note after a reopen |
| `inference/framework/g4_relations.py` | `LAW_KIND`; `validate_prediction(kind=…)`; `Prediction.from_relations`; `OutcomeRecord.tested` |
| `inference/framework/virelai_gates.py` | `LAW_GATE_ID`, `G4_GATE_IDS`; registration through `g4c_gate`; view guards include G4-C |
| `inference/framework/controller_executor.py` | `PREDICTION_GATES` (G4-B, G4-C): the controller takes each frozen prediction. `ladder_end`: through G4-C, and a level change in G4-B closes too. |
| `inference/agent/controller_turn.py` | A wake waits while either gate's frozen prediction is taken |
| `inference/framework/card_builder.py` | The G4-C index |
| `tools/record_from_artifacts.py` | G4-C fields; predictions are recorded with only the expectations Duck wrote |
| `tests/test_g4c_law.py` (new) | Supported certifies and ends the ladder; contradicted reopens G4-B, keeps the record and closes on a new test; the novelty and relation-number rules |
| `tests/test_g4b_relations.py`, `tests/card_duck.py`, `tests/test_memory_m1.py` | The end-to-end run and the card-only ladder now go through G4-C |

**The end-to-end test,** on the production ToolAgent with a card-only Duck:
- The controller repeats the live ft09 run.
- G4-B makes 8 supported predictions and gets a description.
- G4-C makes one new test, which is SUPPORTED.
- The law set is COMPLETE.
- A planned stop follows, with no model call after it.

**The run replays from its own artifacts,** through G4-C.

**The card-only ladder** (stress worlds with 2, 8 and 20 levers) completes through G4-C, and the
card stays flat.

**Suite:** cloud **483 passed, 1 skipped** (484 tests). Ruff is clean on every changed file.
**Mac expected: 484 passed.**

## Ratchet (non-blank, non-comment lines)

| | R9-R12 | R9-R13 |
|---|---|---|
| `virelai_gates.py` | 5,432 | **5,428** |
| `tool_agent.py` / `analyze` | 2,781 / 414 | 2,781 / 414 |
| `solver.py` | 1,376 | 1,376 |
| `controller_executor.py` | 323 | 330 |
| `card_builder.py` | 488 | 489 |

## What this does not do

- **On ft09, "new" is easy to satisfy.** Every press changes the masked board, so almost any action
  from the current board is untested. The test is real, but on independent toggles it is not
  hard.
- **G4-C cannot check that a prediction follows from the relations it names.** It checks that the
  numbers are valid and grades the outcome. Whether the reasoning matches is for review.
- **vc33 has not run on the memory stack.** Its first run is the next exit step.

— Claude, Alpha build seat, 2026-09-30

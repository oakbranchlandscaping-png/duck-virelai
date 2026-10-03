# Review: ring9-carry-vc33-v5 (Kaggle, 2026-10-03)

**Author:** Claude (Alpha build seat), signed
**Run:** notebook `stephenkaskin/taaf-virelai-ring9-carry-vc33-v5`
- **Version 1** failed at start: the source dataset had not been created.
- **This review is of version 2.**

**Package:** `24603b22…3ec6`, source `623ad58` (fbbc7f4 + R9-R20 + R9-R21), pinned image.
**Output:** `runs/kaggle-ring9-carry-vc33-v5/output2/`

## Verdict

**R9-R21 worked as designed:**
- **D6:** no Duck turn at level entry; the controller took G0, G1 and G2.
- **D4:** the contradicted levers were bounded, and **Duck's G3 coverage report was accepted** (`G3_BOUNDED_COVERAGE_REPORT`).

**But the ladder still did not reach G4.** After an accepted *bounded* coverage report, G3 is designed to stay UNRESOLVED with `next_operation: WAIT_FOR_DISCRIMINATING_EVIDENCE`. That evidence can only come from a reset, rebind, new action or new object, none of which can happen without a move. The run idled about 2.7 hours (163 hand-offs reading "G3-LEVERS offers no probe and no answer").

**This third stall has two parts:**
- **Architectural:** G3 has no path to G4 when it holds both certified levers and bounded ambiguities. That needs a Chief Engineer ruling.
- **Code-level:** axiom A2 still missed the stall, because my R9-R20 fix listed waiting operations by name instead of stating the rule.

## Grades

| Criterion | Result | Evidence |
|---|---|---|
| I8 pinned image | PASS | Only `python3.12` paths. Model 33.66 GiB, KV cache 43.62 GiB; weight loading took 134 s |
| I5 setup | PASS | As before |
| I6 comparability | PASS | The first 26 gate events are byte-identical to v4 (and so to v2 and the exit run) |
| **I7 / D6 level entry** | **PASS** | Ledger t26 to t28: G0 and G1 answered by the controller (`G0-CONTROLLER`, `G1-1`), then G2's clicks. No Duck turn at level entry |
| X-1 level freeze | PASS | As before |
| **X-2 carry** | **PASS: 4/4 RECONFIRMED** (repeat) | All 47 actions and their effects are identical to v4's |
| X-3 | PASS | Level-2 levers E0006 and E0007 certified by G3 dossiers from level-2 evidence |
| **I9 / D4 G3 on level 2** | **Partial** | The bounded ambiguity was recorded and Duck's coverage report accepted. But "**the ladder moves to G4**" is **not met**: G3 waits for evidence no move can bring |
| **N-1 (A2)** | **FAIL** | `WAIT_FOR_DISCRIMINATING_EVIDENCE` with no probe and no answer was called legal |
| E ending | Time budget | 47 of 200 actions |

## My miss, stated plainly

1. **The pre-flight stopped one step too early.** `check_level_two_g3_from_record.py` proved the coverage report is accepted. It never asked what the gate does next. Had it called `next_owned_step` and `legal_move_status` after acceptance, it would have shown this exact wait before the run. I preregistered "the ladder moves to G4" without testing it.
2. **D2 (R9-R20) fixed a symptom, not the rule.** I added one waiting operation name to A2's list. A2's rule is general: a gate state is legal only if it offers a probe, asks for an answer it can accept, or declares an end. Any "wait" that offers neither probe nor answer, in a world where nothing changes without a move, is a deadlock, whatever it is called. Stated that way, it would have ended this run, and v4's, within one Duck turn.

## Altitude

1. **Code-level (mine, R9-R22):** restate A2 as the general rule. The legal moves are:
   - an admissible probe;
   - an answer the gate can accept;
   - a declared end (CLOSED, closed by the level boundary, or a planned stop).

   Everything else is no legal move. The test is the v5 record at its final state, plus every existing replay (the ls20, ft09 and vc33 records) staying legal throughout. This alone saves about 3 GPU-hours per stall.

2. **Architectural (Chief Engineer ruling needed before the next vc33 run can reach G4).** When G3 has certified levers (E0006, E0007) and bounded ambiguities (E0004, E0005), what is G3's end state? Three options:
   - **(a) Close G3 as partial.** Certified levers go to G4. Bounded ambiguities stay open questions with their retry condition, and are revisited if a reset or new action ever occurs.
   - **(b) Certify state-dependent levers as their own class.** The confirmation press "responded but not repeatably" becomes evidence of state dependence, and G4-A studies all four levers. This is the question already raised in R9-R21's slice doc. On vc33, level 1's win came from studying such a lever.
   - **(c) Keep G3 waiting, but end the run cleanly as a planned stop.** That is honest, but the ladder stops at G3 on every level with a stateful lever.

   **My recommendation is (a) now and (b) as the next design step.** (a) is the smallest change that lets the ladder continue on evidence already certified, and it claims nothing about E0004 or E0005. (b) changes what G3 claims, so it needs the ruling.

## What v5 settles

- The cross-level chain works through G3 on level 2, live.
- Level 2's entry is fully controller-owned.
- A stateful lever is recorded honestly (bounded, no inertness claim).
- The carry result reproduced exactly: 4/4 RECONFIRMED.

The remaining blocker is a design question about G3's end state, not a bug in the machinery built so far.

**Budget note:** three consecutive vc33 runs each spent about 2.7 to 3 hours idle. Until R9-R22's general A2 rule is in, a shorter behaviour window for diagnostic runs (for example 1 hour) would cut the cost of the next surprise. That is the Director's call, as part of R3.

— Claude, Alpha build seat, 2026-10-03

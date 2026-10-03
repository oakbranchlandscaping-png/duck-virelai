# Build slice R9-R22: G3 discovers levers, G4 types them (D7–D11)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Trigger:**
- the Director's direction, 2026-10-03: "levers do something different" is the point of G4, which exists to fully type each lever and find the nuances of its mechanics;
- `DIAGNOSTIC_G3_G4_LEVER_TYPING_BOUNDARY_v1_2026-10-03.md` (read-only, filed with this slice);
- `REVIEW_RING9_CARRY_VC33_V5_KAGGLE_2026-10-03.md` (committed `01a1d8d`).

**Director ruling, 2026-10-03:** diagnostic first, then build. An attributed positive witness certifies a lever. A repeat press that differs is typing evidence for G4, never an ambiguity.
**Base:** `623ad58` (fbbc7f4 + R9-R20 + R9-R21), branch `r9-r20-level-entry`.
**Supersedes:** R9-R21's D4, which filed a differing repeat as a bounded ambiguity. D5 and D6 stand.
**Altitude:** architectural, ruled by the Director. The code changes are code-level against existing law: `FOUNDATIONAL_ARCHETYPES_v2` §3, `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`, the `lever_attribution` witness law, and Apex's mechanism vocabulary as ported by v4 WO-E7.

## What it fixes

**D7: a repeat press types the lever and never retracts its witness.** This applies in the click lane, outside a boundary.
- The repeat press is still graded against its frozen prediction (SUPPORTED or CONTRADICTED) and recorded unchanged.
- The lever is certified either way, and the controller writes its dossier.
- The repeat is read in G4-A's own orbit vocabulary, over the attributed residue cells:
  - `NULL_AT_OBSERVED_STATE`: it moved, then held;
  - `OBSERVED_STATE_RECURRENCE`: the repeat exactly undid the witness;
  - `NOVEL_STATE_REVEALED`: a third state.
- The reading is kept per lever in `_LeverTarget._repeat_readings`, declared at level tier. It is kept out of the confirmation records, so memory pulls keep their size.
- The controller's dossier now states the repeat as observed. The old text claimed "the prospective repeat reproduced that residue" for every lever.
- A certified repeat no longer wakes Duck, because G3 stays scripted. A boundary-deferred repeat still wakes Duck.
- **Where the code went:** the grading moved, unchanged, out of `virelai_gates.py` into the new `lever_repeat.py`, beside the reading. `_bound_contradicted` (R9-R21 D4) is gone.

**D8: G4 intake accepts every certified lever.** G4.1's `_seed` asks `certified(record, readings)`, which accepts SUPPORTED or a read repeat. The status no longer has to be SUPPORTED.

**D9: G3's pair travels into G4-A.**
- `g3_pairs()` on the G4-A gate gives, for each lever, the witness and confirmation evidence refs, the repeat disposition and the prediction status, with entry state `G3_WITNESS_BEFORE_STATE`.
- It appears on Duck's G4-A card (`g3_repeat` per lever) and in the `LeverOrbitSet` product (`g3_pairs`).
- G4-A's own runs start from a later board, so this pair is the only record of how the lever behaved from its first state.

**D10: mechanism and condition are reported separately.** `LeverRun.typing()` gives `{mechanism, condition, effective_presses}` in the ruled vocabulary:
- moved, then held: UNIFORM;
- never moved from this entry state: UNKNOWN with condition SATURATED;
- TOGGLE and CYCLE as before;
- everything else UNKNOWN.

`lever_class()` is unchanged, so G4-B, G9, the carry and the level model read what they read before. DIRECTIONAL stays reserved for the effect subtree (WO-DIVE-01 R1). The typing is on the card (`typing` per lever) and in the product (`lever_typing`).

**D11: axiom A2 is stated as the rule.** A gate state is legal only if it:
- offers a probe;
- asks for an answer the gate can accept; or
- declares an end. The ends are named once in `DECLARED_ENDS`: next target, next G4 slice, next slice, level closed, controller takes the prediction.

Everything else is no legal move, whatever the operation is called. `NO_MOVE_OPERATIONS` (R9-R20 D2) is gone. The v5 state, `WAIT_FOR_DISCRIMINATING_EVIDENCE` with no probe, is now caught within the watchdog's three checks.

## Tests

**New:** `tests/test_r9_r22_lever_typing.py`, 8 tests. Level 2 is driven as it was live (the v4 run's own record, the controller's own answers).

| Test | Pins |
|---|---|
| `test_a_repeat_press_is_typing_evidence_and_never_retracts_the_witness` | D7: grades kept (E0004 and E0005 CONTRADICTED, E0006 and E0007 SUPPORTED); repeat readings are E0004 held, the other three a third state; all four certified and G4-READY; no bounded ambiguity |
| `test_level_two_inventory_lists_all_four_levers_and_g4_opens` | D7 + D8: the controller's inventory is accepted with four levers, and G4 seeds all four |
| `test_each_lever_reaches_g4a_with_its_g3_pair` | D9 |
| `test_mechanism_and_condition_are_reported_separately` | D10, on synthetic runs: held, never moved, toggle, cycle, diverged, open |
| `test_a_state_that_offers_no_move_is_illegal_whatever_it_is_called` | D11: the v5 wait and an unnamed wait are illegal; the declared ends are legal |
| `test_every_recorded_run_ends_in_a_legal_state` | D11: all six replay fixtures end legal under the general rule |
| `test_the_controller_dossier_states_each_repeat_as_observed` | D7 dossier text |
| `test_a_repeat_that_certifies_its_lever_does_not_wake_duck` | D7 wake |

**Amended, with the supersession stated in each file:**
- `test_r9_r21_g3_contradicted.py`: D4's two tests are retired. D5's test now rebuilds the unbounded state by reporting the two live ambiguities as the v4 code held them.
- `test_r9_r20_level_entry.py`: D2's test asserts the general rule's reason text.

**Fail-first:**
- Before any fix, 5 of the first 6 tests failed. The fixture test passes before and after, which is the point of that test.
- **Each fix reverted alone,** in separate copies:

| Fix reverted | R9-R22 tests that fail |
|---|---|
| D7 | 4 |
| D8 | 4 |
| D9 | 1 |
| D10 | 1 |
| D11 | 1 |
| Controller dossier and wake | 2 |

So every fix is independently necessary.

**Suite (cloud, Python 3.12):** 523 passed, 1 skipped, 0 failed. That's 517 at `623ad58`, minus 2 retired, plus 8 new. ruff on the changed files is clean; the 8 findings elsewhere were already there at `623ad58`.

**Two things the suite caught during the build, both fixed:**
- the new G3 field needed its persistence tier;
- `certified()` accepted a record with no confirmation ref.

**Fragility noted, not changed:** `test_memory_m3` t4 fits a subject pull about 190 characters under the tool's 1,024-token output budget. Adding two fields to each confirmation record pushed it over. That is why the readings live outside the records. `PULL_CHARS` (1,800) and the tool budget are not reconciled. That is a memory-design item, not this slice's.

**Ratchet (non-blank, non-comment lines):**

| File | Before | After | Note |
|---|---|---|---|
| `virelai_gates.py` | 5,411 | 5,391 | −20; confirmation grading extracted to `lever_repeat.py` |
| `controller_executor.py` | 334 | 342 | |
| `g4_guided.py` | 190 | 212 | |
| `life_record.py` | 112 | 113 | |
| `lever_repeat.py` | new | 81 | |

## Pre-flight (the step the v5 pre-flight skipped)

`tools/check_level_two_g4_entry_from_record.py` replays the v4 record past G3, through every answer the controller owns. It reports where the machine rests, the legal-move status, G3's inventory, and G4-A's lever queue with each lever's G3 repeat.

- **R9-R22:** rests at G4-A, legal (PROBE), Duck's turn. G3's inventory lists levers E0004–E0007, with nothing ambiguous. G4-A queues the same four: E0004 held, the other three a third state. Exit 0.
- **`623ad58` (v5's source), negative control:** rests at G3 waiting for Duck's bounded-coverage report, with no inventory. Exit 1.

## What the next vc33 run should show

- Level 1 as before.
- Level 2: G0–G3 by the controller, as in v5, with no Duck turn at E0004's or E0005's repeat. Then G4-A on all four levers, starting with an orientation turn.

**Hypotheses, not findings:**
- From the board G4-A starts on, E0004 may type `UNKNOWN` + SATURATED at that state. Its G3 pair says it moved once, then held, from its first state.
- E0005 may keep revealing new states until it holds.
- The action budget is the likely limit: 47 of 200 actions were used through G3.

## Out of scope (for the Chief Engineer)

- G3's end state when a *genuine* bounded ambiguity remains, such as ego-masked or budget stops. D11 now ends such a state cleanly instead of idling.
- The UNIFORM / `UNIFORM_TRANSFORM` name clash, and the two typing readers.
- Locating the Apex vocabulary ruling document.

## Files (the patch applies cleanly to `623ad58`; verified byte-for-byte)

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_gates.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/g4_guided.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/controller_executor.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/life_record.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/lever_dossier.py` (error text only)
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/lever_repeat.py` (new)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r22_lever_typing.py` (new)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r21_g3_contradicted.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r20_level_entry.py`

Patch: `R9_R22_LEVER_TYPING.patch`, sha256 `397b91809ca59f6416c8a9904e1091a5226e2f14f8fe834338214ecb8da89917`.

— Claude, Alpha build seat, 2026-10-03

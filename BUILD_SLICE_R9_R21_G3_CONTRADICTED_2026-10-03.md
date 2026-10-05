# Build slice R9-R21: level-2 G3 stall (D4–D6)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Trigger:**
- `REVIEW_RING9_CARRY_VC33_V4_KAGGLE_2026-10-03.md` (committed `0ae1c7c`);
- `DIAGNOSTIC_G3_CONTRADICTED_CONFIRMATION_v1_2026-10-03.md`.

**Base:** `fbea80c` (fbbc7f4 + R9-R20), branch `r9-r20-level-entry`, so v5 differs from v4 only by this slice.
**Director ruling 2026-10-03:** build D4, D5 and D6 now. The stateful-lever classification goes to the Chief Engineer separately.
**Altitude:** code-level. The architecture already had the declared class (bounded ambiguity) and the Duck-owned coverage report; one branch failed to use them.

## What it fixes

**D4: a contradicted confirmation now records a bounded ambiguity.**

In G3's confirmation branch, a witness the repeat press does not reproduce moved the entity to AMBIGUOUS without `_bound_ambiguity`. Every other CLICK-phase route to AMBIGUOUS bounds it. G3's inventory refuses unbounded entities, so on level 2 the inventory could never be accepted.

- **Fix:** `_bound_contradicted(...)` is extracted and called in the CLICK phase. It records disposition `CONFIRMATION_CONTRADICTED` and `inertness_claim_permitted: False`, with the standard retry condition.
- **Result:** G3 then reaches its designed path. The controller hands the coverage report to Duck ("G3 has bounded ambiguity: the coverage report is Duck's"), and Duck's report is accepted: levers E0006 and E0007, ambiguous E0004 and E0005.

**D5: axiom A2 sees an inventory no answer can satisfy.**

`legal_move_status` called any demanded answer with a template legal. G3 now exposes `answer_blocked()`: once the roster is complete and nothing is pending, it reports roster entities whose results are unbounded. `legal_move_status` treats a blocked answer as no legal move.

- **Extraction:** `_unbounded_entities()` and `_expected_entities()` are pulled out of `_submit_inventory`, and both callers use them.
- **Effect:** without D4, the existing watchdog would have ended v4 within one Duck turn instead of after 2.7 hours.

**D6: the level-completed wake no longer pre-empts the controller at level entry.**

`wake_reason` woke Duck on every boundary event. When a level change froze the level and restarted the ladder at G0 (R9-R17), level entry is the controller's: G0 and G1 come from metadata.

- **Fix:** `_ladder_restarted(machine, boundary)` suppresses that one wake.
- **Unchanged:** `game_over`, `done`, `run_complete`, and a level change without a restart still wake Duck.

## Tests

**New:** `tests/test_r9_r21_g3_contradicted.py`, 4 tests.
**Fixture:** the v4 run's own record, `tests/fixtures/vc33_kaggle_carry_v4_record.json.gz` (47 transitions). Level 2 is driven as it was live: the controller's own answers, and every recorded action through a freshly issued capability, recorded like live.

| Test | Pins |
|---|---|
| `test_a_contradicted_confirmation_is_recorded_as_a_bounded_ambiguity` | D4: confirmations E0004 and E0005 CONTRADICTED, E0006 and E0007 SUPPORTED; exactly E0004 and E0005 bounded, with no inertness claim and a retry condition |
| `test_the_live_level_two_g3_reaches_an_accepted_coverage_report` | D4: the report is Duck's, legal, and accepted with the expected levers and ambiguities |
| `test_an_inventory_no_answer_can_satisfy_is_not_a_legal_move` | D5: the exact v4 state is illegal |
| `test_a_level_change_that_restarts_the_ladder_does_not_wake_duck` | D6, on the v2 record: no wake at level 2's G0; `game_over` still wakes; a level-1 machine still wakes on `level_completed` |

**Fail-first:**
- **Before any fix:** all 4 failed.
- **Each fix reverted alone,** in separate copies:

| Fix reverted | Tests that fail |
|---|---|
| D4 | 2 |
| D5 | 1 |
| D6 | 1 |

So each fix is independently necessary.

**Suite (cloud, Python 3.12):** 517 passed, 1 skipped, 0 failed. That's 513 at `fbea80c` plus the 4 new tests. ruff is clean.

**Ratchet (non-blank, non-comment lines):**

| File | Before | After | Note |
|---|---|---|---|
| `virelai_gates.py` | 5,412 | 5,411 | Compensated by folding the three existing `_bound_ambiguity` call sites' arguments and one `journal.transition` call; formatting only |
| `controller_executor.py` | 330 | 334 | Far below any tier |

## Files (the patch applies cleanly to `fbea80c`; verified)

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_gates.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/controller_executor.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r21_g3_contradicted.py` (new)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/fixtures/vc33_kaggle_carry_v4_record.json.gz` (new)

## For the Chief Engineer (ruling requested, not blocking)

D4 files stateful levers as **bounded ambiguities**. On vc33's level 2 that is 2 of 4 real levers:
- (16,0): its effect vanished on the repeat press;
- (24,0): its effect moved on the repeat press.

Neither is studied in G4. The ruling requested: should G3 certify a **state-dependent lever** as its own class (responds, but not repeatably), and pass it to G4-A for orbit study? Level 1's win came from studying such a lever. The answer decides how much of vc33 the ladder can model, and it changes what G3 claims.

— Claude, Alpha build seat, 2026-10-03

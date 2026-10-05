# Build slice R9-R23: the mu bucket (D12–D17)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Ruling:** `RULING_MU_BUCKET_v1_2026-10-03.md` (Director-ruled, full version).
**Trigger:** `REVIEW_RING9_CARRY_VC33_V6_KAGGLE_2026-10-03.md`. On level 3, G3 held 7 certified levers and one object it could not attribute (E0028), then waited for evidence no move could bring, and the A2 watchdog ended the run.
**Base:** `8656839` (R9-R22), branch `r9-r20-level-entry`.
**Altitude:** architectural, ruled by the Director. The code changes are code-level against that ruling.

## What was actually on the board (read from the v6 record, first-hand)

- By its click at t107, E0028 occupied **no cell**: levers pressed earlier in the sweep had moved it off.
- The clicked cell belonged to **E0071**, a 92-cell object born mid-sweep. That is why the click's owner could not be resolved.
- Under the ruling, E0028 goes into mu. A later return on a changed board would settle it ABSENT.
- E0071 is a newborn object and in no roster; it is a separate open question, recorded in the ruling.

## What it builds

**D12: a level-tier mu bucket.**
- `mu_bucket.py` adds a `MuBucket` on the gate machine, built fresh each level.
- G3 files every bounded ambiguity into it (`mu_return.after_g3_outcome`). Each entry records the counter-masked board it was tried on, the entity that owned the clicked cell, the evidence and the reason.
- Entries carry no role tag and no inertness claim.

**D13: G3 closes PARTIAL.**
- When at least one lever is certified and only bounded ambiguities remain, the inventory is accepted as `LEVER_INVENTORY` with `closure: PARTIAL`, and the mu objects are listed in `ambiguous_entities`.
- The controller writes that inventory itself, with no Duck turn.
- With no certified lever at all, G3 behaves as before: Duck writes the coverage report.

**D14: return when stuck.**
- `controller_executor.return_to_mu_if_stuck` runs at the top of every controller turn. It acts only when the ladder is stuck: every built gate satisfied (the planned stop), or no legal move.
- `mu_return.return_to_mu` then picks the entries never tried on the current masked board:
  - an object that occupies no cell is settled **ABSENT**;
  - the rest reopen G3. G3's product is invalidated, together with its descendants.
- G3 clicks each object where it is now (`MU_REVISIT`, at a cell the object currently owns). The result then follows G3's ordinary path: witness, repeat press, dossier, inventory.

**D15: late levers.**
- G4.1 and G4-A re-seed incrementally (`mu_return.seeded`). Earlier anatomy answers and orbit runs are kept, and the new lever is queued last.
- Each re-emits its product once complete, after an invalidation.
- G4-B and G4-C are rebuilt fresh, because relations learned without the new lever were learned about a different lever set.

**D16: frozen levels carry their mu bucket.** Each frozen level model records its mu bucket, unresolved entries included.

**D17: inventory wording.** The controller's inventory no longer says remote levers "rewrite their own cells". When mu is non-empty, it names the mu objects.

**Ratchet compensation:** G3's roster accounting moved, unchanged, out of `_submit_inventory` into the new `g3_inventory.py`.

## Tests

**New:** `tests/test_r9_r23_mu_bucket.py`, 6 tests, driven on the v6 run's own record as live. The new fixture is `vc33_kaggle_carry_v6_record.json.gz` (110 transitions).

| Test | Pins |
|---|---|
| `test_g3_closes_partial_and_the_ladder_studies_the_seven_levers` | D13, D17: PARTIAL inventory with 7 levers plus mu E0028, written by the controller; G4-A is legal with the 7 levers queued |
| `test_the_mystery_is_filed_with_its_board_and_is_not_retried_on_the_same_board` | D12, M-4: tried at t107, clicked owner E0071, board recorded; no retry on the same board |
| `test_a_mystery_that_left_the_board_is_settled_absent_not_clicked` | M-4: on a changed board, E0028 is settled ABSENT and G3 stays closed |
| `test_a_mystery_that_responds_on_a_changed_board_joins_the_lever_study` | D14, D15 (stand-in, below): retry, witness, repeat, dossier; a PARTIAL inventory with 8 levers; G4.1's earlier answers kept; G4-A queues the late lever; G4-B fresh |
| `test_the_controller_returns_to_mu_only_when_stuck` | D14: no return while a gate has a move; a return at the planned stop |
| `test_each_level_model_freezes_its_mu_bucket` | D16 |

**The stand-in.** No live run has produced a mystery that later responds. The positive test therefore recasts one clean-null level-3 object (E0014), still on the board, as if its first try had been unresolved on another board. It then answers that object's clicks with a remote change. Everything else is the real level-3 state.

**Fail-first:**
- At `8656839`, all 6 fail: the module does not exist.
- **Each fix reverted alone:**

| Fix reverted | Tests that fail |
|---|---|
| D12 filing | 3 |
| D13 partial close | 4 |
| D14 return | 3 |
| D15 incremental seeding | 1 |
| D16 frozen mu | 1 |
| D17 wording | 1 |

**Suite (cloud, Python 3.12):** 529 passed, 1 skipped, 0 failed (523 plus 6). ruff is clean on every changed file.

**Ratchet (non-blank, non-comment lines):**

| File | Before | After | Note |
|---|---|---|---|
| `virelai_gates.py` | 5,391 | **5,353** | −38 |
| `controller_executor.py` | 342 | 351 | |
| `controller_turn.py` | 176 | 179 | |
| `level_model.py` | 98 | 99 | |
| `life_record.py` | 113 | 115 | |
| `mu_bucket.py` | new | 54 | |
| `mu_return.py` | new | 108 | |
| `g3_inventory.py` | new | 56 | |

## Pre-flight

`tools/check_mu_partial_close_from_record.py` replays a live record to its end, as live, and reports where the ladder rests.

| Source | Level | Rests at | Legal | Inventory | Mu | Exit |
|---|---|---|---|---|---|---|
| **R9-R23** on the v6 record | 3 | G4.2-LEVER-ORBITS | yes | PARTIAL, 7 levers | E0028 OPEN (clicked owner E0071) | 0 |
| **`8656839`** (v6's source) | 3 | G3-LEVERS | **no**: `WAIT_FOR_DISCRIMINATING_EVIDENCE` (the live stall) | n/a | n/a | 1 |

## What the next vc33 run should show

- Levels 1 and 2 as in v6.
- Level 3: G3 as in v6 through t110. Then the controller writes the PARTIAL inventory, with no Duck turn, and G4-A studies the 7 levers.
- If the level is not won when the ladder ends, the controller returns to mu first. E0028 should settle ABSENT, and that is reported.

**Hypotheses, not findings:**
- Level 3 may fall to a lever study, as level 2 did.
- The 200-action budget becomes the likely limit: v6 used 110 actions by t110.

— Claude, Alpha build seat, 2026-10-03

**Patch:** `R9_R23_MU_BUCKET.patch` (applies cleanly to `8656839`; the result is verified byte-for-byte; the binary fixture is included), sha256 `4d566621aca7eba63c551fc979262421e33ef3675e4540c4449da111eb1d4011`.

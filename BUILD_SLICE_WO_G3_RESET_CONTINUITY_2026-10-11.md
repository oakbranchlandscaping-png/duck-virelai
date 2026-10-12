# Build slice: G3 reset continuity. G3's entity ledger sees the board and the life resets the agent observed

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat), signed
**For:** Sol's review. The revision 1 review state is preserved below; revision 2 passed the Mac floor and was accepted for commit.
**Governs:**
- `DIAGNOSTIC_G3_LEDGER_FRAME_SYNC_v1_2026-10-11`, option A, as directed by Sol;
- `NOTE_SHARED_FILE_WO_G3_RESET_CONTINUITY_2026-10-11`, filed before the shared edit, plus amendment 1.

**Base:** `2a79081` (`ring9-unified`, local). The device worktree's G3 and ledger files were verified byte-equal to the cloud tree.

**Held:**
- NAV selection and its handoff;
- the lifecycle transition table (unchanged);
- the replay compatibility guard (unchanged, as committed).

## Revision 2: Sol's rulings on revision 1 (2026-10-11)

**Status:**
- The approach is accepted.
- The revised golden was reviewed and accepted after this revision passed the Mac floor.
- NAV selection and its handoff stay held.

**Sol's rulings and what was done:**

| Ruling | Done | Evidence |
|---|---|---|
| **1 · Goldens:** approved in principle; re-record after the checks pass; carry-v7 byte-identical. The k008 bar-remainder ranking goes in a separate targeting log. | Re-recorded with `tools/record_g3_no_choice_golden.py`. carry-v7's entry is **byte-identical**. k008 and k013 **equal the repaired traces reviewed in revision 1**. Exact diff: `golden_diff.txt` (12 hunks). The ranking concern is logged separately: `TARGETING_LOG_G2_FRONTIER_COUNTER_REMAINDER_v1_2026-10-11`. | test 0 for all three records passes on the new golden |
| **2 · k008 replay:** do not stop at T43. After T43, play the saved actions back as history; assert the T44 plan starts from the true post-reset position; keep no-crash and no-false-lever through T61. | `_drive(path, first_nav, plans_through)`: the plan must equal the live action through T43, and the planner is still asked at every step afterwards. New test: the T44 plan stands at `(12, 16)`, where the ego's own footprint sits on the board rebuilt from the record. That footprint is **not** at `(12, 12)`, the live run's pre-death stand. The T61 boundary assertions (E0001 `ATTEMPTED → NO_RESPONSE_YET → ATTEMPTED → AMBIGUOUS`, the deferred boundary observation, no lever without a witness) are unchanged. k013 keeps step-by-step plan equality. | **Fail-first:** on `2a79081` the T44 test fails, `(12, 12) != (12, 16)`. After the change all 6 of the file's tests pass. |
| **3 · Departed objects:** keep all 432 in the history, but drop untouched departed objects from the actionable agenda; a departed object with a witness or G3 work stays. | `library_agenda._departed_untouched`: ledger ABSENT, lifecycle `UNTOUCHED`, no witness, no lifecycle event. Such objects are skipped and counted in `agenda["departed_untouched"]`. The ledger and lifecycle keep every object. | **Excluded side:** k013 has 480 such objects, all still in the ledger, none asked, and `departed_untouched == 480`. **Kept side:** k013's five departed rows that G3 worked on (`E0015`, `E0018`, `E0020`, `E0021`, `E0023`, all AMBIGUOUS) stay, and a departed row given a witness reads `ANSWERED_LEVER`. k013 at 400 has **77 questions** (125 on `2a79081`, 557 in revision 1). Agenda time is about 0.6 ms per call. |
| **Blocker · a broken seed or reset replay must fail closed in Duck's live library** | `library_census._fail_closed`: a reported break (`counter.seed_limitations`, or G3's new `_board_record_breaks`, each `{stage, transition_id, detail}`) becomes a **typed `RECORD_MISMATCH` gap** naming the stage and transition. Every role and scoped null resting on the stale board moves out of `certified` into a `RECORD_MISMATCH` gap ("Is the … claim grounded?"): G2 and G3 for a seed break, G3 only for a reset-replay break. Those gates read `RECORD_MISMATCH` in the census, accounting lists `BOARD_DISCONTINUITY`, and the gate machine's products are not touched. | **k008, RESET 31's record corrupted:** both breaks are typed at transition 31 (G2 seed, and G3 reset replay from the same row). G2 reads `RECORD_MISMATCH`, G1 stays `CERTIFIED`, only EGO is certified, there are no scoped nulls, `NOT_ACCOUNTED`, and **the digest's first gap kind is `RECORD_MISMATCH` with no COUNTER finding**. **k013, RESET 60 corrupted:** a G3-only break at 60. The nine levers become RECORD_MISMATCH gaps, G2 stays certified. **Sound k013:** no break, and the nine levers stay certified. |
| **Note correction: missing rows** | The revision-1 note's claim was not reliable. A transition id is the game's history length, so a level's executed transitions are contiguous. `level_board` now **rejects a gap in the ids** as a missing row. A trailing omission is still detectable only by H2's record check, and the note says so. | `test_a_gap_in_the_levels_transition_ids_is_a_missing_row_and_is_rejected` |

**Fail-first** (recorded in `failfirst_rev1.txt`):
- On revision 1: 4 of the new tests fail (missing row, G2-seed fail-closed, reset-replay fail-closed, departed exclusion). The 3 guards pass: sound record, departed-with-work kept, F6.
- On `2a79081`: the T44 test fails.

**After the changes:**

| File | Result |
|---|---|
| `test_g3_ledger_frame_sync.py` | 17 passed |
| `test_g3_hybrid_lifecycle_replay.py` | 6 passed |
| Cloud full suite | §R2.3 |

**Ratchet (NCNB lines):**

| Function | Revision 1 | Revision 2 |
|---|---|---|
| `compile_level` | 64 | 61 (the accounting block moved unchanged into `_board_accounting`, 10) |
| `_fail_closed` | — | 31 (new) |
| `_board_record_breaks` | — | 6 (new) |
| `_g3_questions` | 30 | 34 |
| `_departed_untouched` | — | 3 (new) |
| `_observe_seed_stream` | 17 | 20 |
| `_latest_observed_board` | 15 | 16 |
| `level_board._level_rows` | 7 | 13 |

### R2.3 · Cloud full suite

**777 passed, 1 skipped, 0 failed** (Python 3.12, 100 files).

How the count adds up: 777 = 759 (the guard slice's floor) + 17 (`test_g3_ledger_frame_sync`) + 1 (the T44 test).

- Test 0 passes for all three records on the re-recorded golden.
- The census, library view and world-model suites pass unchanged (13, 17, 11 and 13).
- ruff: the changed files are clean. `virelai_gates.py` keeps its 2 pre-existing findings.

**Mac floor:** 777 passed, 1 skipped in 1422.61 s. Focused Mac tests: 106 passed in 450.94 s. Sol reviewed the exact golden diff and accepted k008 and k013; carry-v7 remains byte-identical.

---

## 0 · What changed

| File | Change |
|---|---|
| `inference/framework/level_board.py` (new, pure) | `board_through`: rebuilds a board from the level-entry board plus the level's `transition_index` rows, in transition order, **checking every recorded `before`**. `reset_frames`: each RESET after a given transition, as a verified full before-and-after outcome. `BrokenBoardRecord`: names the transition and cell when a row contradicts the board or a transition is recorded twice. |
| `virelai_gates.py` · `_prepare_counter_from_ego` + new `_latest_observed_board` | G2 starts from **the latest observed board**: all indexed transitions of the level, resets included, plus G1's in-flight outcome. That outcome is the one being recorded when G2 is prepared, before its index row is written. On a broken record the seed falls back to `ego.current_grid()` and records the break; it is never resynchronised. |
| `virelai_gates.py` · `_ensure_entity_ledger` + new `_observe_seed_stream` | The ledger takes G2's outcomes and, **in transition order with them, every reset since G2's seed**, each reconstructed and verified. On a broken record **no reset is threaded** and the break is written into `ledger.limitations`. |
| `tests/test_g3_ledger_frame_sync.py` (new) | 11 tests (§2) |

**Not touched:**
- `entity_observation.py`: `observe` still refuses a mismatched frame, so a mismatch never resynchronises and is never evidence;
- the lifecycle and its table; the controller; `observe_system_reset`; `CounterGateMachine.__init__`.

**Both changes run once per level:** the seed when G2 is prepared, the merge when G3's ledger is first built. **Neither is on the per-action controller path.**

**Ratchet (NCNB lines):**

| Function | Before | After |
|---|---|---|
| `_ensure_entity_ledger` | 27 | 22 |
| `_observe_seed_stream` | — | 17 (new) |
| `_prepare_counter_from_ego` | 15 | 18 |
| `_latest_observed_board` | — | 15 (new) |
| `CounterGateMachine.__init__` | 83 | 83 |
| `virelai_gates.py` file | 7,048 | 7,083 |
| `level_board.py` | — | 77 |

## 1 · Fail-first on `2a79081`

Recorded in `failfirst_2a79081.txt`. **8 failed, 1 passed** (the carry-v7 guard):

| Test | Failure on `2a79081` |
|---|---|
| F1 | G2's seed was the board after 30; row 0 differs from the board after 32 |
| F2 | k008: ledger transitions 33, 34, … all mismatched (28) |
| F3 | k013: 61, 62, … mismatched (312) |
| F4 | k008, E0004 with a synthesized local response: `POINTER_OWNER_UNRESOLVED`, not `PRE_ACTION_POINTER_OWNER` |
| F5 (×2) | `level_board` absent |
| F6 (×2) | `level_board` absent. On the ledger, a corrupted reset row (k013, transition 60) was not reported. |

## 2 · After the repair: 11 of 11

| Test | What it pins |
|---|---|
| **F1** | k008 through 32: `counter.initial_grid` equals the board after 32, rebuilt from the record alone |
| **F2** | k008 to 60: **no ledger transition mismatched** (was 28 of 28) |
| **F3** | k013 to 400: **no mismatch** (was 312 of 343). The resets are 60, 113, 166, 219, 272, 325 and 378, and G2's span 61–377 is in the entity history. |
| **F4 (the evidence result)** | k008 at G3's entry, production agent and recorder: the controller's click on E0004, with a synthesized local response on that object, is **`LOCAL_LEVER_WITNESS`**, basis `PRE_ACTION_POINTER_OWNER`, contact attributed |
| **F5 (record-free, ×2)** | The rebuild rule on a 3×3 board: move, reset, move. The board after each, the reset as a verified full frame, and a ledger that threads the reset observes the next outcome while one that skips it cannot. |
| **F6 (×2)** | A contradicted or duplicated row raises `BrokenBoardRecord` naming the transition. On k013, a corrupted reset row is **reported on the ledger** ("transition 60") and the ledger **stays out of step**: there is no silent resync. |
| **G1** | carry-v7: no reset, no mismatch |
| **No false lever (×2)** | Unmodified records: k008 certifies no lever and k013 exactly the live run's nine pointer witnesses, each with its own witness evidence. Same sets as `2a79081`. |

## 3 · Verification

| Run | Result |
|---|---|
| Cloud, the new file | 11 passed |
| **Cloud, full** (100 files) | **767 passed, 1 skipped, 2 failed, 1 error.** The failures are exactly the three expected divergences in §4: test 0 for k008, test 0 for k013, and the k008 fixture of `test_g3_hybrid_lifecycle_replay` (an error at transition 44). Every other file passes. |
| carry-v7 no-choice golden | **byte-identical** (test 0 for carry-v7 passes) |
| ruff | The new files are clean. `virelai_gates.py` keeps its 2 pre-existing findings. |

**How the count adds up:** 767 = 759 (the guard floor) − 3 diverging tests + 11 new.

The Mac floor is not run: the goldens wait for your ruling.

## 4 · Divergences from the current expectations (not updated, awaiting your ruling)

### 4.1 Summary

| Record | First divergence | Cause | Evidence ids | Products | Lifecycle | Levers |
|---|---|---|---|---|---|---|
| **k008** | Event #31, T33, `G2-COUNTER:PILOT_TO_CONTACT:1`, envelope only | G2's ranked object frontier is now built from the real post-reset board. Row 0 is the counter bar refilled by RESET 31: 62 cells of 14 plus a 2-cell 0 remainder, instead of 64 zeros. The remainder becomes member `M0002` and ranks first, so G2's pilot target is `M0002` (2 cells) instead of `M0003`, and every later member id shifts up by one. | All 60 unchanged | `G2-COUNTER`: id and revision unchanged; payload differs **only** in `ranked_object_frontier` (31 fields). Others unchanged. | +1 row: `E0008 UNTOUCHED`, the extra member's entity | None before, none after |
| **k013** | Event #371, T379, `G3-LEVERS:CLICK:1`, envelope only | Entity versions now count G2's history (`v33` → `v351`): the ledger observed 61–377 instead of refusing them | All 395 unchanged | Unchanged | **+432 rows, `E0076`–`E0507`, all `UNTOUCHED`.** These are the G2-span entities, born and gone across six lives; all are now ABSENT in the ledger. | The same nine |

**Attribution changes on k008** (the attribution field of the event table in §4.2):
- **The five CLICK clicks (T38–42):** `COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED` becomes **`SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER`**. The click is now attributed to its object, and only counter cells changed.
- **The NAV steps with residue:** `UNRESOLVED_ATTRIBUTION` becomes **`AMBIGUOUS_EGO_MASKED`**. The ledger now knows where the ego is, so its own changed cells are typed as ego-confounded. They are not called null.
- **Unchanged:** lifecycle states, and therefore every product.

**The `transition_index` hash:**
- **k008:** changes, because the rows carry those dispositions.
- **k013:** unchanged.
- **Frozen levels:** unchanged on both.

### 4.2 Event by event (golden → repair)

The generated tables follow at the end of this note. Every changed event is listed. The only changed field is `probe_sha`, the hash of the probe envelope: the target's member id and entity version are inside it. Probe ids and evidence ids are unchanged everywhere.

### 4.3 A third expectation: `test_g3_hybrid_lifecycle_replay`, k008 fixture

- **What the test does:** it drives k008's NAV pursuit and asserts, step by step, that the controller's planned action equals the **live** run's.
- **Where it diverges:** at **T44** the live run (and `2a79081`) planned `ACTION2` from stand `(12, 12)`. The repair plans `ACTION3` from stand **`(12, 16)`**.
- **Why:** the old ledger never advanced after the reset, so it kept the ego at its **pre-death** footprint `(12, 12)` for the whole pursuit, from T43 to T45 and onward. With the ledger in step, the ego is at its **post-reset** position `(12, 16)`, and after the recorded T44 move it is at `(16, 16)`.
- **What it means:** the live k008 NAV pursuit was planned from a stale ego position. The record cannot be followed past T44 by a correctly informed planner.
- **The k013 tests in that file all pass.**

## 5 · For your ruling (revision 1; answered by Sol's rulings, see Revision 2 above)

1. **Accept the k008 and k013 differences** in §4.1–§4.2. If you do, I re-record the k008 and k013 no-choice goldens with `tools/record_g3_no_choice_golden.py`, carry-v7 still byte-identical, and then the full Mac floor runs.
2. **The k008 lifecycle-replay expectation** (§4.3): the live record was planned from a stale ego. Options:
   - cut that fixture's live-plan check at T43, before the first plan made from the corrected ego;
   - or re-derive the expected plans on the repaired code.
   I have changed neither.
3. **G2-span entities in G3's lifecycle** (k013: +432 `UNTOUCHED` rows for entities now ABSENT).
   - They are honest history, but the agenda lists each as an open `IS_LEVER` question: k013 at 400 goes from **125 to 557 questions**, and agenda time from about **0.6 ms to 10.5 ms** per call. The card is unchanged (4,021 → 4,023 characters).
   - They are never selectable, and the inventory ignores `UNTOUCHED` rows.
   - Whether the agenda should list ABSENT entities that never reached G3's frontier is a policy question. I have not changed the agenda or the lifecycle.
4. **G2's frontier now ranks the counter bar's 2-cell remainder first on k008** (§4.1). That is G2's own ranking rule applied to the true board, where before it ran on a stale one. Flagged, not changed.

— Claude, Alpha build seat

---

## Appendix: generated event tables (golden → repair)

### k008: every changed event

| # | T | Probe | Changed field | Target (golden → repair) | Attribution (golden → repair) |
|---|---|---|---|---|---|
| 31 | 33 | `G2-COUNTER:PILOT_TO_CONTACT:1` | probe_sha | M0003 vNone → M0002 vNone | same |
| 32 | 34 | `G2-COUNTER:PILOT_TO_CONTACT:2` | probe_sha | M0003 vNone → M0002 vNone | same |
| 34 | 36 | `G2-COUNTER:PILOT_TO_CONTACT:4` | probe_sha | M0003 vNone → M0002 vNone | same |
| 36 | 38 | `G3-LEVERS:CLICK:1` | probe_sha | M0003 v1 → M0004 v6 | COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED → SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER |
| 37 | 39 | `G3-LEVERS:CLICK:2` | probe_sha | M0004 v1 → M0005 v7 | COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED → SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER |
| 38 | 40 | `G3-LEVERS:CLICK:3` | probe_sha | M0006 v1 → M0007 v8 | COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED → SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER |
| 39 | 41 | `G3-LEVERS:CLICK:4` | probe_sha | M0007 v1 → M0008 v9 | COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED → SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER |
| 40 | 42 | `G3-LEVERS:CLICK:5` | probe_sha | M0008 v1 → M0009 v10 | COUNTER_ONLY_RESPONSE / POINTER_OWNER_UNRESOLVED → SCOPED_NULL_RESPONSE / PRE_ACTION_POINTER_OWNER |
| 41 | 43 | `G3-LEVERS:NAV:1:1` | probe_sha | M0003 v1 → M0004 v11 | same |
| 42 | 44 | `G3-LEVERS:NAV:1:2` | probe_sha | M0003 v1 → M0004 v12 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 43 | 45 | `G3-LEVERS:NAV:1:3` | probe_sha | M0003 v1 → M0004 v13 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 44 | 46 | `G3-LEVERS:NAV:1:4` | probe_sha | M0003 v1 → M0004 v14 | same |
| 45 | 47 | `G3-LEVERS:NAV:1:5` | probe_sha | M0003 v1 → M0004 v15 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 46 | 48 | `G3-LEVERS:NAV:1:6` | probe_sha | M0003 v1 → M0004 v16 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 47 | 49 | `G3-LEVERS:NAV:1:7` | probe_sha | M0003 v1 → M0004 v17 | same |
| 48 | 50 | `G3-LEVERS:NAV:1:8` | probe_sha | M0003 v1 → M0004 v18 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 49 | 51 | `G3-LEVERS:NAV:1:9` | probe_sha | M0003 v1 → M0004 v19 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 50 | 52 | `G3-LEVERS:NAV:1:10` | probe_sha | M0003 v1 → M0004 v20 | same |
| 51 | 53 | `G3-LEVERS:NAV:1:11` | probe_sha | M0003 v1 → M0004 v21 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 52 | 54 | `G3-LEVERS:NAV:1:12` | probe_sha | M0003 v1 → M0004 v22 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 53 | 55 | `G3-LEVERS:NAV:1:13` | probe_sha | M0003 v1 → M0004 v23 | same |
| 54 | 56 | `G3-LEVERS:NAV:1:14` | probe_sha | M0003 v1 → M0004 v24 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 55 | 57 | `G3-LEVERS:NAV:1:15` | probe_sha | M0003 v1 → M0004 v25 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 56 | 58 | `G3-LEVERS:NAV:1:16` | probe_sha | M0003 v1 → M0004 v26 | same |
| 57 | 59 | `G3-LEVERS:NAV:1:17` | probe_sha | M0003 v1 → M0004 v27 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 58 | 60 | `G3-LEVERS:NAV:1:18` | probe_sha | M0003 v1 → M0004 v28 | UNRESOLVED_ATTRIBUTION / BODY_CONTACT_UNRESOLVED → AMBIGUOUS_EGO_MASKED / BODY_CONTACT_UNRESOLVED |
| 59 | 61 | `G3-LEVERS:NAV:1:19` | probe_sha | M0003 v1 → M0004 v29 | same |

### k013: every changed event

| # | T | Probe | Changed field | Target (golden → repair) | Attribution (golden → repair) |
|---|---|---|---|---|---|
| 371 | 379 | `G3-LEVERS:CLICK:1` | probe_sha | M0016 v33 → M0016 v351 | same |
| 372 | 380 | `G3-LEVERS:CLICK:2` | probe_sha | M0017 v34 → M0017 v352 | same |
| 373 | 381 | `G3-LEVERS:CLICK:3` | probe_sha | M0018 v35 → M0018 v353 | same |
| 374 | 382 | `G3-LEVERS:CLICK:4` | probe_sha | M0022 v36 → M0022 v354 | same |
| 375 | 383 | `G3-LEVERS:CLICK:5` | probe_sha | M0019 v37 → M0019 v355 | same |
| 376 | 384 | `G3-LEVERS:CLICK:6` | probe_sha | M0021 v38 → M0021 v356 | same |
| 377 | 385 | `G3-LEVERS:CLICK:7` | probe_sha | M0024 v39 → M0024 v357 | same |
| 378 | 386 | `G3-LEVERS:CLICK:8` | probe_sha | M0011 v40 → M0011 v358 | same |
| 379 | 387 | `G3-LEVERS:CLICK:9` | probe_sha | M0013 v41 → M0013 v359 | same |
| 380 | 388 | `G3-LEVERS:CLICK:10` | probe_sha | M0020 v42 → M0020 v360 | same |
| 381 | 389 | `G3-LEVERS:CLICK:11` | probe_sha | M0023 v43 → M0023 v361 | same |
| 382 | 390 | `G3-LEVERS:CLICK:12` | probe_sha | M0025 v44 → M0025 v362 | same |
| 384 | 392 | `G3-LEVERS:CLICK:14` | probe_sha | M0003 v46 → M0003 v364 | same |
| 385 | 393 | `G3-LEVERS:CLICK:15` | probe_sha | M0004 v47 → M0004 v365 | same |
| 387 | 395 | `G3-LEVERS:CLICK:17` | probe_sha | M0014 v49 → M0014 v367 | same |
| 390 | 398 | `G3-LEVERS:CLICK:20` | probe_sha | M0015 v52 → M0015 v370 | same |
| 392 | 400 | `G3-LEVERS:CLICK:22` | probe_sha | M0010 v54 → M0010 v372 | same |
| 393 | 401 | `G3-LEVERS:NAV:1:1` | probe_sha | M0016 v55 → M0016 v373 | same |
| 394 | 402 | `G3-LEVERS:NAV:1:2` | probe_sha | M0016 v56 → M0016 v374 | same |

# Build slice R9-R20: level-entry deadlock (D1–D3)

**Date:** 2026-10-02
**Author:** Claude (Alpha build seat), signed
**Trigger:** `REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md` (committed `e09dfbe`)
**Base:** `fbbc7f4` (R9-R06 to R9-R18). The Director ruled 2026-10-02 to branch from `fbbc7f4`, so `ring9-carry-vc33-v3` differs from v2 only by this slice.
**Label:** R9-R20. The NAV seat already used R9-R19 (`72adbe3`).
**Altitude:** code-level. No architectural ruling is needed. D2 tightens how axiom A2 is checked, not what A2 says. It is listed for the Chief Engineer below.

## What it fixes

**D1: a metadata refresh unsettled a fresh pointer ego.** `EgoGateMachine.update_action_metadata` ran `_settle_coverage()` on any ego in ACTIVE, ANSWER_REQUIRED, REOPENED or UNRESOLVED. A click world's ego has no coverage; its G1 closes on the G0 interface axiom. Settling it turned ANSWER_REQUIRED into UNRESOLVED / `REPRESENTATION_GAP_NO_VISIBLE_EFFECT`.

Level 1 never met this, because its G1 closes before the first action. Level 2's ego is the first one built inside an action's recording, by `_advance_level`. The same action's artifact path then refreshes the metadata. That is what happened live.

- **Fix:** the predicate `_refresh_settles()` (extracted, not interleaved). A refresh settles only a non-pointer ego. A refresh that *adds* actions still reopens a pointer ego, exactly as before.

**D2: axiom A2 missed the state.** `legal_move_status` counted `WAIT_FOR_REPRESENTATION_OR_NEW_ACTION` as a legal declared state even when no probe was offered and no answer was asked. Nothing can change that state without a move. It is exactly the deadlock A2 forbids.

- **Fix:** one table, `NO_MOVE_OPERATIONS`, holds every operation that asks for a move no one can make when no probe is offered. The existing two (`QUERY_NEXT_PROBE`, `QUERY_NEXT_G3_TARGET`) are joined by `WAIT_FOR_REPRESENTATION_OR_NEW_ACTION`.
- **Effect:** the existing watchdog (`_NO_LEGAL_MOVE_LIMIT = 3` consecutive checks) now ends such a run as a recorded controller failure within one Duck turn. Before, v2 idled about 3 hours.

**D3: replay was not the live path.** `record_replay.replay` called `record_outcome` but not the post-action `update_action_metadata` that `agent/gate_artifacts.py` makes after every live action. That is why the R9-R17 and R9-R18 tests passed while the live run deadlocked: the R9-R15 lesson again.

- **Fix:** `record_like_live(machine, probe, outcome, valid_actions)` does both steps, and replay uses it.
- The level-2 loops in `test_r9_r17_level_freeze.py` and `test_r9_r18_carry.py` now record through it too, so level-2 behaviour is proven with the live refresh after every action.

## Tests

**New:** `tests/test_r9_r20_level_entry.py`, 4 tests. **Fixture:** the v2 run's own record, `tests/fixtures/vc33_kaggle_carry_v2_record.json.gz`. It has 26 transitions, equal to the exit run's; only Duck's prose answers differ.

| Test | Pins |
|---|---|
| `test_a_metadata_refresh_leaves_a_fresh_pointer_ego_answerable` | D1 |
| `test_replay_refreshes_the_action_metadata_after_every_action_as_the_live_path_does` | D3 (26 refreshes for 26 actions) |
| `test_the_live_level_two_entry_reaches_g2_under_the_controller` | D1 on the live record: G0 and G1 answered by the controller, then G2's first click |
| `test_waiting_for_an_action_while_admitting_none_is_not_a_legal_move` | D2 on the exact live state |

**Fail-first:**
- **Before any fix:** all 4 failed.
- **Each fix reverted alone,** in separate copies:

| Fix reverted | Tests that fail |
|---|---|
| D1 | 2 (`…pointer_ego_answerable`, `…reaches_g2…`) |
| D2 | 1 (`…not_a_legal_move`) |
| D3 | 1 (`…replay_refreshes…`) |

So each fix is necessary on its own.

**Suite (cloud, Python 3.12):** 513 passed, 1 skipped, 0 failed. That's 509 at `fbbc7f4` plus the 4 new tests. `test_no_legal_move.py` (6) passes unchanged, and so do R9-R15 to R9-R18. ruff is clean.

**Ratchet (non-blank, non-comment lines):**

| File | Before | After |
|---|---|---|
| `virelai_gates.py` | 5,413 | 5,412 |
| `record_replay.py` | 244 | 251 (far below any tier) |
| `tool_agent.py` | — | unchanged |

`legal_move_status` was folded, not grown.

## Files

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_gates.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/record_replay.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r20_level_entry.py` (new)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/fixtures/vc33_kaggle_carry_v2_record.json.gz` (new)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r17_level_freeze.py` (the level-2 loop records like live)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_r9_r18_carry.py` (the same)

## For the Chief Engineer

1. **A2 is now stricter.** Any gate that waits for a new action while offering no probe is a no-legal-move state. The full suite, including every ls20, ft09 and vc33 replay, finds no legitimate state of that shape. If a future gate genuinely waits on something other than a move (a timer or an external event), it must declare its own operation, not reuse this one.
2. **A standing lesson, now three instances.** R9-R15's three replay gaps and this D3 all come from live-path side effects that replay re-implemented instead of calling.
   - `record_like_live` is a first step: one function for the replay's per-action path.
   - The structural fix is for the live path and replay to share one function. The live path would call `record_like_live` too. That touches `agent/gate_artifacts.py` and is left for a ruling, because it changes the live recording path.
3. **Merging with `main`.** Sol's 9 source commits since `fbbc7f4` touch neither `_settle_coverage`, `update_action_metadata`, `legal_move_status` nor `record_replay.py`'s step loop, so cherry-picking this slice onto `main` should apply cleanly. Sol's R9-I03 loop guard is a different mechanism (repeated no-progress tool calls) and does not cover D2.

— Claude, Alpha build seat, 2026-10-02

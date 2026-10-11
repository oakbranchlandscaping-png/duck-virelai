# Build report: WO-G3-DIRECTED, CLICK slice, revision 2, for Sol's re-review

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat, click line), signed
**Reader:** Sol (review), via the Director
**Detail:** `BUILD_SLICE_WO_G3_DIRECTED_CLICK_2026-10-11` (revision 2) and `NOTE_SHARED_FILE_WO_G3_DIRECTED_CLICK_2026-10-11` (amendment 1). This report summarises them and does not replace them.

**Ground, at the time of writing:**
- **`ring9-unified`:** `125d4d0`, the held WO-L2a library view, **committed alone**. It sits on `8e13e35` (docs) and `472aa32` (code). Both new commits are local; nothing is pushed. `main` and `origin` are at `472aa32`.
- **Worktree `duck-virelai-r9r20`:** revision 2 of the CLICK slice, **uncommitted**, all 11 file hashes verified against the delivery.

---

## 1 · Asked of Sol

1. **Accept revision 2 for commit**, or return findings. The Mac floor is in hand (§3), and nothing is committed until you rule.
2. **Confirm the scope of the first NAV item**, the HYBRID CLICK-pass fix. The proposal:
   - In `controller_executor._nav_step`'s G3 branch, accept `RANKED_CLICK_TARGET` and serve the bound click as `_ordinary_step` does.
   - Apply the same bounded handoff.
   - Under D3 ("one per G3 phase per level"), a HYBRID level could then hand Duck **two** choices, one in CLICK and one in NAV. Is that intended, or should HYBRID get one per level?
3. **Retry ids.** An explicit head choice that ends ambiguous retries in place under its SEL id. Coverage already reuses `CLICK:{n}` the same way. Each attempt is its own transition row. Do you want an attempt counter in the SEL id, or is this acceptable?

## 2 · Your four findings and the durable events: what closed

Each finding has a test that **failed against revision 1 and passes now**. All 9 new tests failed against revision 1: its code, the held view files, and `gate_artifacts.py` at `472aa32`.

| # | Your finding | Fix | Evidence |
|---|---|---|---|
| 1 | The digest named the gate in progress, not the selected question | `library_digest(model, budget, *, target=None)`. The goal is `library_agenda.selected_target(machine)` with `question_id`. `tool_agent` passes it. A saved record with no machine is unchanged. | Through `agent._gate_context_update`, `card.question_id == digest.goal.question_id == capability.question_id == agenda.selected`. This holds at carry-v7 3 (no choice), 3 (a choice), 7 (an obligation) and 20 (after the inventory), and at the minimal digest tier (budgets 3,000, 1,200 and 700). |
| 2 | An explicit head choice lost the choice | The head chosen explicitly gets the bound SEL envelope (`target.question_id`, `selected_by`) and records `FINISHED`. The no-choice envelope is unchanged: the golden trace still matches byte for byte. | Before the choice the head's probe is `G3-LEVERS:CLICK:1`; after it, the SEL probe on the same action with a new token. The transition row names the SEL probe. The head's `G3-CLOSED` event cites that row's evidence. Coverage resumes at `CLICK:2`. |
| 3 | G4-C was checked against `SUPPORTED`, which the product never writes | `PRODUCT_STATUS`: COMPLETE → `ANSWERED`; UNRESOLVED → `CLOSED_UNRESOLVED`; a level boundary → `CLOSED_BY_LEVEL_BOUNDARY`. Gate, G4-B and G4-C questions all use it. | Product-backed, on the ft09 levers (`start_g4b`): a supported law gives product `COMPLETE`, and the gate question and every lever's LAW question read `ANSWERED`. `close_unresolved` gives `UNRESOLVED`, read as `CLOSED_UNRESOLVED`. |
| 4 | The timeout fallback had no live-path test | Test only; the code path was already correct. | `_HarnessGameSession.play`, the production `ToolAgent`, the live handoff on (default), an ft09-backed game, 58 actions. See the trace below. |
| — | Selection events lived only in memory | A game-long `machine.g3_selection_events` (GAME tier) is flushed to `{stem}_g3_selection_events.jsonl`: after each recorded outcome, after each `virelai('next_probe', question_id=…)`, and at the end of each controller turn. `COVERAGE_RESUMED` marks a handoff that produced no choice. | Through the real tool bridge, an admitted choice and then a refused one, with no action taken: the file holds `ADMITTED`, then `REFUSED` with its reason. The live test covers a handoff with no choice. |

**The live-path timeout trace (finding 4):**
1. Duck's single G3 turn reaches the model ("G3 choice"). The prompt's card and digest both name the head's question.
2. The model answers without a tool call, so the turn yields `turn_time_budget`.
3. The next turn is the controller's coverage click on that head:
   - envelope executor `CONTROLLER`, purpose `RANKED_CLICK_TARGET`, a non-SEL id;
   - the receipt, the row and the envelope agree on the probe id and evidence.
4. The turn ledger reads `DUCK turn_time_budget`, then `CONTROLLER controller_step`.
5. The log on disk reads `HANDOFF`, then `COVERAGE_RESUMED`.
6. The run is not stopped: `_l2a_end_reason` is empty.

**Your decision on ruling D2, recorded as you gave it, in the build note §0a.** The live one-turn handoff amends ruling D2's "zero model calls through G3" (R9-R08, not your probe-id decision D2). The controller-only mode (`g3_choice_handoff=False`) is kept as a regression guard in the m2 ft09 tests.

## 3 · Verification

| Run | Result |
|---|---|
| Cloud, focused (7 files) | 110 passed |
| **Mac, focused** (same 7 files) | **110 passed** (4:41) |
| Cloud, full (98 files) | 755 passed, 1 skipped |
| **Mac, combined floor** (`125d4d0` + revision 2) | **755 passed, 1 skipped** (20:51); matches the cloud |
| ruff | The changed files are clean. `virelai_gates.py` keeps 2 pre-existing findings. |

How the count adds up: 755 = 707 (the held-view floor, now committed) + 47 directed-G3 tests + 1 m2 handoff test.

**Ratchet:**
- `virelai_gates.py` is +25 NCNB over `472aa32` (+2 in revision 2, the event log in `CyberneticGateMachine.__init__`).
- `run_controller_turn` drops from 45 to 10: a flushing wrapper, with the body unchanged in `_run_controller_turn`.
- Every other touched function grows by at most 4 (`_LeverTarget.__init__`, `gated_memory_query`). New logic sits in extracted helpers.
- The selection logic stays outside the gate class, in `g3_selection.py` (158 lines).

## 4 · Honest ledger

1. **No real model has made a G3 choice yet.**
   - What is proven: the choice path through the tool bridge, the timeout path through the live session, and the no-choice path through the golden trace.
   - What is not: whether a live model uses the handoff well. That is a rehearsal question for after NAV, not a test gap in this slice.
2. **The HYBRID CLICK pass still goes to Duck on every step** (`_nav_step` lacks `RANKED_CLICK_TARGET`). This predates the slice. It is unfixed, and it is ruled as the first NAV repair.
3. **Unflushed events are lost on a hard kill.** Events are written to disk only at the three flush points. A kill between an event and the next flush drops those rows. Per C3, a hard kill is reported by the run manifest or an external audit, not by this file.
4. **The live-path world is a hypothesis.** The test's world is the ft09 continuation fixture, which treats unreached tiles as inert. It proves the session plumbing, not ft09's physics.
5. **An ambiguous off-head choice is released to coverage, not retried.** This is a design choice and is recorded. The lifecycle is not widened.
6. **The NAV selection path is still to build** (`planned_nav_step`, the NAV `finish_target` sites).

## 5 · Next, after your ruling

1. **If you accept revision 2:** the Director commits the CLICK slice with explicit paths. I'll supply the command.
2. **NAV slice (Claude, D1):**
   - the HYBRID CLICK-pass repair first, as scoped in §1.2;
   - then NAV selection under pursuit;
   - `planned_nav_step` toward a selection;
   - the NAV `finish_target` sites;
   - tests 2a–2c on NAV cuts.
3. Then the v3 dossier schema (D4).
4. Pushing `8e13e35` and `125d4d0` (and the CLICK commit) is the Director's call. Nothing is pushed yet.

— Claude, Alpha build seat (click line)

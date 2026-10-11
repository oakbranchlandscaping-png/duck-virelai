# Build slice: WO-G3-DIRECTED NAV, piece 1. The HYBRID CLICK pass belongs to the controller

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat), signed
**For:** Sol's review; the commit is **held**.
**Governs:**
- Sol's ruling on CLICK revision 2: HYBRID may offer at most one choice in CLICK and one in NAV. Repair the CLICK pass first. The NAV handoff waits for NAV selection and pursuit.
- Sol's instruction for this piece.
- `NOTE_SHARED_FILE_WO_G3_DIRECTED_NAV_2026-10-11` (filed before the shared edit; amendment 1 for the ratchet extraction).

**Base:** `db8a657` on `ring9-unified` (local), the fail-first baseline.

## 0 · What changed

| File | Change |
|---|---|
| `inference/framework/controller_executor.py` (shared) | `next_owned_step` passes `g3_choice_handoff` to `_nav_step`. `_nav_step` sends G3's `RANKED_CLICK_TARGET` to the new `_g3_click_step`: first the one bounded CLICK handoff (`_g3_choice_due`), then the capability's single bound click, owned by the controller. Ratchet compensation: the bound-action tail repeated in `_nav_step`'s G1 and G2 branches moved **unchanged** into `_bound_step`. |
| `tests/test_g3_hybrid_click_pass.py` (new) | 3 tests (§2) |

**Not touched:**
- `virelai_gates.py`, `g3_selection.py`, `library_agenda.py`;
- `lever_lifecycle.py` and its transition table;
- `planned_nav_step`, reachability, terrain, every G4 gate;
- the golden fixture.

## 1 · Fail-first on `db8a657`

**The harness:**
- **World:** the k008 development record (HYBRID; ruling 10), replayed through the production gate path to G3's entry at transition 37. G3 is in its CLICK phase with 5 selectable rows.
- **Driver:** the production `ToolAgent.analyze`, controller on, live handoff on (the default).
- **Environment:** returns the record's own change when the record took the same action at that transition, and no change otherwise.
- **Model:** a stub that declines the choice: it answers without a tool call and the turn-time budget runs out.

**On `db8a657` (`controller_executor.py` sha `18fcb2fff58d`), all 3 new tests fail:**

| Turn | Owner and reason | Model calls | Actions |
|---|---|---|---|
| Ownership at entry | `DUCK`: "G3 NAV cannot compute RANKED_CLICK_TARGET" | — | — |
| 1 | `DUCK turn_time_budget` (no handoff; no `HANDOFF` event) | 1 | 0 |
| 2 | `DUCK turn_time_budget` | 1 | 0 |
| 3 | `DUCK turn_time_budget` | 1 | 0 |

Every turn goes back to Duck and nothing executes; the selection log stays empty.

**The failure messages:**
- Test 1: "no CLICK handoff: the step went to Duck as an uncomputable NAV step".
- Tests 2 and 3: `step_executed=False, yielded_control=True` on the turn the controller should own.

## 2 · Passing trace (after the repair)

Ownership at entry: "G3 choice: several rows are eligible …" (the CLICK handoff). Seven turns:

| Turn | Ledger | Transition | Envelope (executor, purpose, probe) | Receipt and transition row (probe, evidence) | Action, and the record's action at that transition |
|---|---|---|---|---|---|
| 1 | `DUCK turn_time_budget` | — | — | — | — (the handoff, declined) |
| 2 | `CONTROLLER controller_step` | T38 | CONTROLLER, `RANKED_CLICK_TARGET`, `G3-LEVERS:CLICK:1` | `G3-LEVERS:CLICK:1`, `E-385f374f3f47fea8` (both) | `ACTION6 (1,36)` = recorded |
| 3 | `CONTROLLER controller_step` | T39 | CONTROLLER, `RANKED_CLICK_TARGET`, `CLICK:2` | `CLICK:2`, `E-d6ff8d33c06a3d51` | `ACTION6 (4,36)` = recorded |
| 4 | `CONTROLLER controller_step` | T40 | CONTROLLER, `RANKED_CLICK_TARGET`, `CLICK:3` | `CLICK:3`, `E-24e85aa93cdb7ca0` | `ACTION6 (52,16)` = recorded |
| 5 | `CONTROLLER controller_step` | T41 | CONTROLLER, `RANKED_CLICK_TARGET`, `CLICK:4` | `CLICK:4`, `E-44e9580fdd6e492a` | `ACTION6 (52,40)` = recorded |
| 6 | `CONTROLLER controller_step` | T42 | CONTROLLER, `RANKED_CLICK_TARGET`, `CLICK:5` | `CLICK:5`, `E-d28e7a808318aab3` | `ACTION6 (60,0)` = recorded |
| 7 | `CONTROLLER controller_step` | T43 | CONTROLLER, `PILOT_TO_LEVER_CONTACT`, `G3-LEVERS:NAV:1:1` | `NAV:1:1`, `E-67be6f28bc69674a` | `ACTION1` = recorded |

**Results:**
- **One model call** in the whole CLICK pass (the declined handoff). Selection log on disk: `HANDOFF`, `COVERAGE_RESUMED`; there is no second CLICK handoff.
- G3 is now in NAV, and `choice_handoff_due` is false there: NAV rows are not selectable, so **the NAV handoff stays off**. NAV's first route step is the controller's, unchanged.
- **Agreement with the live record:** after the declined handoff, the controller's six actions are exactly the live run's transitions 38–43. The coverage probe ids `CLICK:1…5` and `NAV:1:1` are the same sequence as k008's no-choice golden trace. Evidence ids are not compared with the golden trace: this path records through the live recorder, the golden through `record_like_live`.

**The tests:**

| Test | What it pins |
|---|---|
| 1 | Sol's observable. After the declined handoff, exactly one controller action. The envelope, receipt and transition row agree on `G3-LEVERS:CLICK:1`; the receipt and row agree on evidence and on transition 38. Ledger: `DUCK turn_time_budget`, then `CONTROLLER controller_step`. Log: `HANDOFF`, `COVERAGE_RESUMED`. The prompt's card names the head's question. |
| 2 | The CLICK pass offers no second handoff. Six controller actions match the record. Every envelope is CONTROLLER (5 `RANKED_CLICK_TARGET`, then `PILOT_TO_LEVER_CONTACT`). Receipts and rows agree on probe id and evidence for all six. No NAV handoff. |
| 3 | Handoff off (the controller-only regression guard): the first turn is already the controller's `CLICK:1`, with no model call and no selection event. |

## 3 · Verification

| Run | Result |
|---|---|
| Cloud, the new tests | 3 passed (10 s) |
| Cloud, focused NAV, ownership and G3 files (per-file counts from the full run) | `test_g3_hybrid_click_pass` 3, `test_g3_directed_click` 47 (no-choice golden included), `test_memory_m2` 21, `test_g3_hybrid_lifecycle_replay` 5, `test_nav_branch_foundations` 37, `test_ring9_nav_cell_site_targeting` 2, `test_sub2_submission_hardening` 8: **123 passed** |
| **Cloud, full** (Python 3.12, 99 files) | **758 passed, 1 skipped**, 0 failed (= 755 + 3) |
| **Mac, focused** (the same 7 files; hashes `7ec5146d0174`, `e9fb4a590cf5` verified) | **123 passed** (4:17) |
| **Mac, floor** (`db8a657` + this repair; `--ignore=tests/test_physics_grammar_contract.py`) | **758 passed, 1 skipped** (20:59); matches the cloud |
| ruff | `controller_executor.py` and the new test are clean |

**Ratchet, `controller_executor.py` (NCNB lines):**

| Function | Before | After |
|---|---|---|
| `_nav_step` | 111 | **101** |
| `_g3_click_step` | — | 5 (new) |
| `_bound_step` | — | 8 (moved code) |
| `next_owned_step` | 16 | 16 |
| `_ordinary_step` | 24 | 24 |
| File | 522 | 529 |

## 4 · Runtime behaviour that changes

1. **HYBRID worlds: G3's CLICK pass is now the controller's.**
   - Before, every `RANKED_CLICK_TARGET` step went to Duck as uncomputable. In the no-choice replays that is 5 such steps on k008 and 22 on k013: each was a Duck turn spent on a click the gate had already bound.
   - Now, with the live handoff, a HYBRID level spends **one** Duck turn on the CLICK pass (the choice), then the controller clicks. In controller-only mode it spends none.
   - Duck can still choose a row in that one turn (`virelai('next_probe', question_id=…)`). The bound SEL envelope is the CLICK slice's, unchanged.
2. **G1 and G2 NAV ownership is unchanged**: the extracted `_bound_step` is the same code.
3. **Pure CLICK worlds are unchanged** (`_ordinary_step` is not touched; m2 21 of 21).
4. **The NAV handoff stays disabled** until NAV selection and pursuit are built, as Sol ruled.

## 5 · Findings for Sol

1. **A CLICK-phase confirmation in a HYBRID world is still routed as a NAV step.**
   - By reading: `_LeverTarget.next_probe` binds a CLICK-phase confirmation (`CONFIRM_LEVER_WITNESS`, `virelai_gates.py:3437-3448`) to the one witnessed click. But `_nav_step` sends every `CONFIRM_LEVER_WITNESS` to `planned_nav_step`, a route step.
   - **Unverified:** no fixture's HYBRID CLICK pass produced a witness (k008: none in 5 clicks; k013: none in 22). My attempt to synthesize one on k008, by recolouring the clicked tile, did not produce a witness either.
   - Not changed here, being outside this piece. If you want it, it is the same one-branch shape (serve the bound click when the confirmation binds one action), with a fail-first test on a synthesized witness.
2. **The handoff paragraph is not in Duck's prompt here.** In this harness the controller session starts at G3 with no prior actions, so `ControllerSession.hand_to_duck` writes no handoff paragraph. Duck therefore does not see "G3 choice" in the prompt here; the card and digest do name the head's question. In a real run the controller has acted at G0–G2, so the paragraph appears, as the ft09 live-path test of the CLICK slice shows. This is pre-existing and noted only because test 1 asserts the `HANDOFF` event rather than the prompt text.

## 6a · Sol's ruling (2026-10-11, relayed by the Director)

1. **Accepted as a scoped slice.** `RANKED_CLICK_TARGET` now goes through the same bounded action path CLICK worlds use. The tests cover the declined handoff, the six recorded controller actions, matching receipts and controller-only mode. Sol reviewed the code and tests but did not rerun the Mac floor; the Director's run gave 758 passed, 1 skipped.
2. **Commit this repair with its shared-file note and build note.**
3. **Follow-up before broader NAV work:** a fail-first test for a HYBRID CLICK-phase confirmation, then make the controller execute the gate's bound click. NAV selection and its handoff stay off until that path is verified. This is filed separately as `BUILD_SLICE_WO_G3_DIRECTED_NAV_CLICK_CONFIRM_2026-10-11`.

## 6 · Next

1. **Done:** the Director copied the 2 code files (hashes verified). The Mac results are the focused 123 and the floor of 758 passed, 1 skipped, matching the cloud. **The commit is held.**
2. Sol reviews this repair.
3. Then NAV selection, route planning and target completion, as Sol scoped them.

— Claude, Alpha build seat

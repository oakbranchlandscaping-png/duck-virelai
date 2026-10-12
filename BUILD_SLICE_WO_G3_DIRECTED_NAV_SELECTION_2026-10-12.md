# Build slice: WO-G3-DIRECTED, NAV selection and pursuit

**Date:** 2026-10-12
**Author:** Claude (Alpha build seat), signed
**For:** Sol's review. **The commit is held.** No golden has been updated.
**Governs:** `NOTE_SHARED_FILE_WO_G3_DIRECTED_NAV_SELECTION_2026-10-12`, filed before any shared edit.
**Base:** `ceeeabd` (`ring9-unified`, local). Before the edit, the device worktree's shared files were byte-equal to the cloud tree.
**Out of scope** (not touched): SUB-4, G4 dossiers, the PLAY-NORMAL wording and the G2 bar-remainder targeting question.

## 1 · What was built

**G3 owns admission** (`g3_selection.py`).
- `admission_candidates` now marks a NAV row as `selectable` when:
  - **no route pursuit is under way** (`_navigation_steps == 0`), and
  - the row is the head, or its lifecycle state is `UNTOUCHED` or `NO_RESPONSE_YET` and it is not an inherited null.
- These rows are never selectable away from the head: AMBIGUOUS, settled (G3-CLOSED / G4-READY), PRESUMED_UNREACHABLE, terrain-typed or reopened rows.
- While any obligation is pending, `admission_candidates` returns nothing, as before.
- **Refusal reasons are recorded**:
  - "the gate owes its … obligation first";
  - "the NAV pursuit under way owes its body contact first";
  - "this NAV row is not selectable now (settled, ambiguous or an inherited null)";
  - "the question names no row this G3 roster serves now".
- `library_agenda.py` is **unchanged**. It reports the gate's `selectable` rows as `OPEN_ACTIONABLE`, and selects the choice while the choice's row is a candidate. It schedules nothing.

**One bound pursuit.**
- **Admission.** `select` records the entity, its version and the admitting transition. In NAV it also clears the previous route evidence and plan.
- **Probe identity.** `selected_probe` serves `G3-LEVERS:NAV:SEL:{member}:L{level}P{life}:R{revision}:{step}`:
  - The prefix up to `R{revision}` is the admission's identity; every route step of that pursuit shares it.
  - Each step is a separate probe, transition row and evidence id.
- **Envelope.** It is the coverage NAV envelope, moved **unchanged** into `_LeverTarget._nav_probe`. Its target carries `question_id` and `selected_by`.
- **Route planning.** `planned_nav_step` is unchanged. It is handed the bound target on every step and re-reads that entity's current cells from the ledger, which is on the post-reset board.
- **CLICK** keeps its SEL id and envelope byte for byte.

**What ends a pursuit.** Every NAV cursor advance now goes through `g3_selection.finish_target`; with no choice, it does exactly what the advance did before.

| Event | Site |
|---|---|
| Contact witness | `record_outcome` |
| Target changed (bounded ambiguity) | `record_outcome` |
| Scoped null | `record_outcome` |
| Terminal boundary or pilot budget | `record_outcome` |
| Reachability answer | `_submit_reachability` |
| Confirmation | unchanged |
| Dossier | unchanged |

- **A finished choice.** The selection clears (FINISHED). If the row was off the head, it joins `_chosen_members` and the coverage cursor stays where it was.
- **Boundary.** A boundary on the pursuit ends the choice as STALE ("a boundary interrupted the pursuit"); the row stays owed.
- **Staleness.** These end a choice as STALE, and the row returns to coverage:
  - a phase, level, life or roster change;
  - the object changing;
  - the row settling;
  - a reopened reachability row coming due ("a reopened row owes its body contact first").

**Coverage is preserved.**
- `advance_past_chosen_rows` now also runs in NAV, so a finished off-head row is not served again.
- The CLICK→NAV flip clears `_chosen_members`, because a row chosen in CLICK still owes its NAV body contact.
- `record_outcome` clears the route evidence when the *pursuit* changes (`g3_selection.pursuit`: cursor plus admission), not only when the cursor does. With no choice the two are the same.
- The lifecycle table, attribution and the witness and certification path are untouched. A lever still requires the existing attributed activation witness.

**The bounded NAV handoff, wired last** (`controller_executor.py`).
- The G3 pilot tail moves **unchanged** into `_g3_pilot_step`, which adds one guard. For a `PILOT_TO_LEVER_CONTACT` capability it offers the handoff through the existing `_g3_choice_due`. That allows one per phase per level, needs at least 2 selectable rows, and requires that no obligation be pending. Because rows are not selectable mid-pursuit, it can only fire between pursuits.
- A timeout, a refusal or a turn with no choice resumes coverage on the next step. `COVERAGE_RESUMED` is recorded once, with no repair loop and no game stop.
- `g3_choice_handoff=False` (controller-only) offers nothing.
- The handoff text is now one constant, `G3_CHOICE_REASON`, shared by the CLICK and NAV handoffs.

**Events.** ADMITTED, REFUSED, STALE, HANDOFF, FINISHED and COVERAGE_RESUMED go to the existing G3 selection log (`_selection_events` and the game-long `g3_selection_events`, flushed to `{stem}_g3_selection_events.jsonl`). Each carries `phase: "NAV"`.

## 2 · Interpretations for Sol to confirm

1. **Entity-version staleness reads sightings.**
   - `EntityLedger.observe` increments every entity's `version` on every observed transition, STILL entities included. Raw version equality would therefore stale every NAV pursuit after its first step.
   - A NAV choice is stale when the object is not PRESENT, or when any sighting after the admitting transition has a relation other than STILL.
   - The selection still names the entity and the version it had at admission. CLICK keeps version equality, since it is served in the same transition.
2. **Owed body contact keeps its priority, read as follows:**
   - A pursuit already under way cannot be displaced by a choice.
   - Every `NO_RESPONSE_YET` row is still served by coverage. A choice reorders that work, but drops none of it.
   - Every NAV row in both records is `NO_RESPONSE_YET` (BODY_CONTACT_OWED). Treating those rows as unselectable would leave no NAV choice to make.
3. **A boundary's end is STALE**, with its own reason, and not a new event type. The row is not counted as chosen, so coverage still owes it.
4. **The `_chosen_members` clear at the CLICK→NAV flip fixes a latent CLICK-slice defect** that NAV exposed. On `ceeeabd` a row chosen off-head in CLICK silently lost its NAV body contact: it was dropped from the NAV candidates and never served (fail-first below).

## 3 · Fail-first on `ceeeabd`

**Test file.** New, mine: `tests/test_g3_directed_nav.py`, 13 tests. The output is in `failfirst_nav_on_ceeeabd.txt`. On `ceeeabd`, **11 failed and 2 passed**.

**Failure causes:**
- **Seven** raised `G3 choice not admissible: a NAV row is not selectable in this slice`: the off-head choice, the explicit head, the mid-pursuit test, the k013 off-head test, two staleness tests and the live choice.
- **Genuine choice:** `assert [] == ['E0001', …, 'E0006']`; no NAV row was selectable.
- **Mid-pursuit:** the refusal reason did not name the body contact owed.
- **CLICK-chosen row:** E0004 was missing from the NAV candidates (the latent defect in §2.4).
- **Two handoff tests:** the first NAV turn executed a step instead of offering the handoff.

**Passing guards (2):**
- The reachability obligation refuses a choice.
- With the handoff off, the NAV pass is the controller's from its first step.

**The worlds:**
- **k008 at transition 42.** NAV entry on life 2, after RESET 31. The head is E0001. Four rows are genuinely eligible: E0002, E0004, E0005 and E0006, the CLICK pass's own scoped nulls, `NO_RESPONSE_YET`. Their eligibility comes from the gate; nothing bypasses it.
- **k013 at transition 400.** On life 8, the head's first planning call certifies a routing limit.
- **Past the record,** an action the record did not take has no recorded response. `RigidEgoWorld`, which lives only in the test, synthesizes one from the record's own evidence:
  - the ego footprint moves as one block by its G1 bearing onto the integer it leaves behind in the record's moves (12);
  - otherwise nothing changes.
  - The solver never reads it.

## 4 · Required evidence

| Required | Evidence |
|---|---|
| **No-choice replays of k008, k013 and carry-v7 match the committed goldens. Goldens not updated.** | `test_g3_directed_click::test_0_no_choice_replays_keep_every_envelope_evidence_id_and_product`, for all 3 records, passes against the golden (sha `d9e08bd753af`, unchanged). Every probe envelope hash, evidence id, product payload, frozen level, transition index and lifecycle state is identical. |
| **A chosen off-head NAV object drives the controller toward it for more than one step; card, library question, capability, route target, receipt and transition row agree.** | **Machine level (k008):**<br>• **Pursuit:** E0004 is chosen with the ego at (12,16), 37 cells away, and pursued for **10 steps**: 9 APPROACH (ACTION2, down 4 each; the stand moves (12,16)→(48,16), distance 37→1), then a CONTACT_ATTEMPT.<br>• **Probe ids:** `G3-LEVERS:NAV:SEL:M0007:L1P2:R7:1` … `:10`, one admission prefix; each step has its own evidence id.<br>• **Close:** the scoped null closes E0004 on its own evidence (G3-CLOSED), then FINISHED.<br><br>**Production agent (`ToolAgent.analyze`):**<br>• **The choice:** Duck chooses through `virelai('next_probe', question_id=…)` in the NAV handoff.<br>• **The steps:** three controller steps follow.<br>• **Agreement on every step:** the card's `question_id` equals the agenda's selected question, which is `Q:L1:G3-LEVERS:E0004:IS_LEVER`. The envelope, the receipt (`_gate_events.jsonl`) and the transition row carry the same SEL probe id. The envelope and receipt targets name E0004 with that question. The receipt and transition-row evidence ids are equal. |
| **An explicit head choice gets a selected identity; an implicit head step stays on the coverage path.** | Implicit: `G3-LEVERS:NAV:1:1`, with no `question_id`, and no events. Explicit: `G3-LEVERS:NAV:SEL:M0004:L1P2:R…:1`, carrying the question; it is the same route action, the transition row names it, and the event is ADMITTED. |
| **A completed off-head pursuit is not served again.** | **k013 (full coverage):**<br>• E0016 is chosen off the head.<br>• Its pursuit ends in its reachability answer, which reuses the controller's understanding, and is recorded ADMITTED → FINISHED.<br>• Coverage then runs to `NAV_ENUMERATION_COMPLETE`.<br>• E0016 is answered **exactly once**; the head (E0002) is still answered (`PRESUMED_UNREACHABLE`).<br><br>**k008:**<br>• After FINISHED, coverage resumes at the head with `G3-LEVERS:NAV:1:1`.<br>• E0004 is gone from the candidates and from the agenda's eligible list.<br>• Full coverage is not driven on k008, because each row costs a whole route at about 2.5 s a step (`_terrain_context`, existing cost); k013 carries that proof. |
| **Mandatory body-contact and reachability work cannot be skipped.** | **Body contact:** after one head step (`_navigation_steps == 1`), no row is selectable, the agenda's eligible list is empty, and no handoff is due. A choice is REFUSED ("the NAV pursuit under way owes its body contact first"), and the next probe is `NAV:1:2`. During an off-head pursuit the head stays `NO_RESPONSE_YET`, still owed.<br><br>**Reachability (k013):** while the certificate is pending, the obligation is REACHABILITY, the agenda selects the obligation, eligible is `[]`, no handoff is due, and a choice is REFUSED ("the gate owes its reachability obligation first"). |
| **A stale or declined choice returns to coverage.** | **New life:** STALE "a new life began", and the next probe is `NAV:1:…`.<br>**Object changed during approach** (a synthesized recolour of one E0004 cell): STALE "the chosen object changed". E0004 is not marked chosen, so coverage still owes it.<br>**Declined handoff:** HANDOFF → COVERAGE_RESUMED, then `NAV:1:1`. |
| **A timed-out handoff costs at most one Duck turn, and the game continues.** | Duck's turn ends on its turn-time budget. The next four turns are controller steps, with no second NAV handoff and no further model call. |
| **k008 plans from the true post-reset ego position.** | The selected pursuit's first plan stands at **(12, 16)**, the ego's footprint after RESET 31. That is the same stand `test_k008_t44_plan_starts_from_the_egos_true_post_reset_footprint` verifies against the record board. |
| **No false lever on either record.** | **k008** after the selected pursuit: witnessed, discovered and unsupported-G4 sets all empty. **k013** after the selected pursuit and full coverage: witnessed = discovered = the nine live pointer levers, with no unsupported G4-READY. |

**Measured added Duck time:**
- **The NAV handoff** adds **one Duck turn per level**: one model request carrying a card of 9,636 characters (gate card 6,330, prompt body 3,306).
- **In the rehearsal** the stub's turn took 0.002 s.
- **In a live run** it is bounded by the turn-time budget.
- **The selected pursuit itself** adds no Duck time; every route step is the controller's.

**Selection-event examples:** the full rows are in `selection_event_examples.json`.

| Case | Event | Entity | Actor | Reason | Transition | Life |
|---|---|---|---|---|---|---|
| k008 off-head pursuit | ADMITTED | E0004 | DUCK | "away from the coverage head" | 42 | 2 |
| | FINISHED | E0004 | DUCK | "the chosen row's G3 work is done" | 51 | 2 |
| k008 mid-pursuit | REFUSED | — | DUCK | "the NAV pursuit under way owes its body contact first" | 43 | 2 |
| k008 new life | STALE | E0004 | DUCK | "a new life began" | 43 | 3 |
| k013 | REFUSED | — | DUCK | "the gate owes its reachability obligation first" | 402 | — |
| | ADMITTED | E0016 | DUCK | — | 402 | — |
| | FINISHED | E0016 | DUCK | — | 402 | — |
| k008 live, declined | HANDOFF | — | CONTROLLER | "a genuine G3 choice was offered to Duck" | 42 | — |
| | COVERAGE_RESUMED | — | CONTROLLER | "no choice was admitted after the handoff" | 42 | — |

## 5 · Revised test (the shared file)

`tests/test_g3_hybrid_click_pass.py::test_the_click_pass_offers_no_second_handoff_and_follows_the_record_into_nav`
- **Why it changed.** It pinned "no NAV handoff until NAV selection". Sol's directive enables that handoff in this slice.
- **What it asserts now:**
  - the CLICK pass still offers **no second CLICK handoff**;
  - NAV's first turn is the one NAV handoff, declined;
  - then the first route step;
  - the six controller actions are still exactly the live run's transitions 38-43;
  - the log reads `HANDOFF/CLICK`, `COVERAGE_RESUMED/CLICK`, `HANDOFF/NAV`, `COVERAGE_RESUMED/NAV`.
- **One added line** gives the NAV handoff turn a fresh turn budget. The test's model stub spends a turn's budget by zeroing `_yield_seconds`, an agent-wide setting, while a live turn measures its own budget from its start.
- **Unchanged:** the other three tests in that file.

## 6 · Results (cloud)

**Focused run:** 19 files, **210 passed** (`focused_cloud_results.txt`):

| File | Passed |
|---|---|
| `test_g3_directed_nav` | 13 |
| `test_g3_directed_click` | 47 |
| `test_g3_hybrid_click_pass` | 4 |
| `test_g3_hybrid_lifecycle_replay` | 6 |
| `test_g3_ledger_frame_sync` | 17 |
| `test_g3_checkpoint` | 5 |
| `test_g3_scheduler` | 16 |
| `test_g3_run_outcome` | 5 |
| `test_g3_recolor_identity` | 5 |
| `test_library_census` | 13 |
| `test_library_view` | 17 |
| `test_memory_m2` | 21 |
| `test_memory_m3` | 11 |
| `test_memory_m4` | 8 |
| `test_controller_end_to_end` | 2 |
| `test_controller_python_bridge` | 6 |
| `test_virelai_controller` | 6 |
| `test_r9_r21_g3_contradicted` | 2 |
| `test_r9_r24_g4_controller_first` | 6 |

**Full cloud suite** (101 files, `--ignore=tests/test_physics_grammar_contract.py`):
- **790 passed, 1 skipped, 0 failed** (`full_cloud_suite_results.txt`).
- That is the Mac floor at `ceeeabd` (777 passed, 1 skipped) plus the 13 new tests.

**Ratchet (NCNB lines; `ratchet_ncnb.txt`):**

| Function | Before | After | Note |
|---|---|---|---|
| `_LeverTarget.next_probe` | 87 | 73 | the NAV envelope and the reopen jump extracted unchanged |
| `_LeverTarget.record_outcome` | 542 | 538 | |
| `_nav_step` | 103 | 93 | pilot tail extracted unchanged |
| `_g3_click_step` | 5 | 4 | |
| `_ordinary_step` | 24 | 23 | |
| `select` | 24 | 27 | |
| `finish_target` | 9 | 10 | |
| `_nav_probe` | — | 13 | new |
| `_take_reopened_row` | — | 7 | new |
| `_g3_pilot_step` | — | 14 | new |
| `g3_selection` helpers | — | 2-19 | new |

**File totals.** These rise by the extracted methods' signature and return lines:

| File | Before | After |
|---|---|---|
| `virelai_gates.py` | 7087 | 7092 |
| `controller_executor.py` | 531 | 538 |
| `g3_selection.py` (mine) | 158 | 213 |

No function grew past its tier. **I flag the file-level +5 and +7 for Sol's ruling** rather than squeeze them out with unrelated edits.

## 7 · Files (parked in `runs/_cowork_xfer/l2a/navselect/`)

| File | Destination | sha256[:12] |
|---|---|---|
| `g3_selection.py` | `inference/framework/` | `febd46f7c961` |
| `virelai_gates.py` | `inference/framework/` | `42089d7f4831` |
| `controller_executor.py` | `inference/framework/` | `0a2c30ac7208` |
| `test_g3_hybrid_click_pass.py` | `tests/` | `af0330b3fff2` |
| `test_g3_directed_nav.py` (new) | `tests/` | `49df6af68e44` |

- **Unchanged and verified byte-equal to `ceeeabd`:** `library_agenda.py`, `life_record.py`, `memory_queries.py` and `tests/fixtures/g3_no_choice_golden.json` (`d9e08bd753af`).
- **Exact shared-file diff:** `shared_file_diff.patch`.
- **The Director runs the Mac floor and commits after acceptance.**

## Revision 2: Sol's review of revision 1 (2026-10-12)

**Status:**
- **Accepted:** the sightings-based NAV staleness rule, the interpretation that Duck may reorder queued body-contact work, and the small file-size increases.
- **Mac result on revision 1:** the focused run passed 87 tests and the hashes matched.
- **Mac verified:** focused review set, 89 passed in 283.78 s; full floor, 792 passed and 1 skipped in 1535.82 s. Sol accepted revision 2 for commit.

**The defect Sol found.**
- **What happened:** after a selected off-head approach changed the object, G3 logged STALE and returned to the coverage head, but kept the abandoned pursuit's step count and route evidence.
- **The result:** the next probe was `G3-LEVERS:NAV:1:3`, carrying two old evidence references. It should have been `NAV:1:1` with no selected-route evidence.
- **Why:** `selected_probe`'s staleness path cleared the selection only.

**Fail-first on revision 1** (`failfirst_r2_on_rev1.txt`): 2 failed. Both tests execute the first resumed controller action.
- **Object change:** `test_after_the_chosen_object_changes_the_resumed_coverage_step_starts_fresh` makes two selected steps, the second recolouring one cell of E0004, then resumes. Revision 1 gives `'G3-LEVERS:NAV:1:3' == 'G3-LEVERS:NAV:1:1'`: it reproduces Sol's finding exactly.
- **New life:** `test_after_a_new_life_the_resumed_coverage_step_starts_fresh` makes two selected steps, starts a new life, then resumes. Same failure.
- **What both tests then assert**, through the shared helper `_assert_fresh_coverage_step`:
  - the resumed probe is `NAV:1:1`, with no `question_id`;
  - the receipt, the transition row and the probe agree on the probe id;
  - the receipt and the transition row agree on the evidence id;
  - the receipt's target is the head (E0001);
  - the receipt's scheduler route evidence is that one step's evidence alone;
  - none of the abandoned pursuit's evidence remains;
  - the step count is 1;
  - the head is ATTEMPTED on the resumed step's evidence (attribution to the head);
  - exactly one STALE event.
- To expose receipts, the test's `Sim.step` now keeps the event `machine.record_outcome` returns. It is still `record_like_live`: record, then refresh the metadata.

**The fix** (`g3_selection.py` only; the diff is `revision2_delta.patch`).
- `yield_choice(g3, reason)` notes **one** STALE and drops the choice. For a NAV choice it also resets the pursuit state: `_navigation_steps = 0`, the route evidence and the cached plan.
- `selected_probe`'s staleness path now goes through `yield_choice`. The object-change, new-life, phase, level, roster and settled paths therefore share the one reset.
- `interrupt_pursuit` (a boundary inside `record_outcome`) records its own STALE and leaves the route evidence alone. The boundary outcome's receipt keeps its route refs, and `record_outcome` clears them at its end because the pursuit changed (unchanged from revision 1).
- **The reopen path** (`_take_reopened_row`) already cleared the same state before calling `yield_choice`. It is unchanged.

**Unchanged from revision 1:** `virelai_gates.py`, `controller_executor.py` and `test_g3_hybrid_click_pass.py`. The golden is unchanged (`d9e08bd753af`).

**Note.** The shared-file note's reference is corrected from `yield_to_obligation` to `yield_choice`, and amendment 1 records this edit.

**Results (cloud):**

| Run | Result |
|---|---|
| `test_g3_directed_nav` | 15 passed |
| Full suite (101 files, `--ignore=tests/test_physics_grammar_contract.py`) | **792 passed, 1 skipped, 0 failed** (`full_cloud_suite_results_r2.txt`) |

**Mac results:** focused review set, **89 passed**; full floor, **792 passed, 1 skipped, 0 failed**. The full floor took **25:35**, which is now the baseline for the separate test-runtime optimization order.

- The full suite includes `test_g3_directed_click` (47, with the test 0 goldens for all three records), `test_g3_hybrid_click_pass` (4) and `test_g3_hybrid_lifecycle_replay` (6).
- **Ratchet:** `yield_choice` goes from 4 to 10 NCNB lines, `selected_probe` from 19 to 18 and `interrupt_pursuit` from 5 to 6. No shared gate function changed.

**Revision 2 hashes** (sha256[:12]; parked in `runs/_cowork_xfer/l2a/navselect_r2/`):

| File | Revision 2 | Revision 1 |
|---|---|---|
| `g3_selection.py` | `43b8c70fcb51` | `febd46f7c961` |
| `test_g3_directed_nav.py` | `65a0f0a954ec` | `49df6af68e44` |
| `virelai_gates.py` | `42089d7f4831` | unchanged |
| `controller_executor.py` | `0a2c30ac7208` | unchanged |
| `test_g3_hybrid_click_pass.py` | `af0330b3fff2` | unchanged |

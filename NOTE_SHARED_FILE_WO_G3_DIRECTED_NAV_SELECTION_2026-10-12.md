# Shared-file note, 2026-10-12 (WO-G3-DIRECTED, NAV selection and pursuit)

**Filed by:** Claude, Alpha build seat, **before any shared edit** (ruling 9).
**Authority:** Sol's directive, relayed by the Director: "proceed with WO-G3-DIRECTED, NAV selection and pursuit".
**Base:** `ceeeabd` (`ring9-unified`, local; the reset continuity slice is accepted; the Mac floor is 777 passed, 1 skipped).
- Before this note, the device worktree's shared files were verified byte-equal to the cloud tree.
- The 12-character sha prefixes are in §5.

**Integration owner:** Claude owns the integration of every file below for this slice. No other seat edits them until it is returned.

## 1 · The NAV call sites at `ceeeabd`

| File | Site | Today |
|---|---|---|
| `g3_selection.py` | `admission_candidates` (`:44-68`) | NAV rows are listed with an obligation tag, but `selectable` is `phase == "CLICK" and …`, so **no NAV row is ever selectable**. |
| same | `select` (`:83-108`) | Refuses every NAV row: "a NAV row is not selectable in this slice". |
| same | `_stale` (`:111-125`) | Checks the entity by raw `version` equality. A NAV pursuit cannot use this, because `EntityLedger.observe` bumps every entity's version on every observed transition, STILL included. |
| same | `selected_click_probe` (`:128-146`) | CLICK only. |
| same | `advance_past_chosen_rows` (`:149-153`) | Guarded by `phase == "CLICK"`. |
| same | `finish_target` (`:156-165`) | Called only from CLICK sites and from the confirmation and dossier sites. |
| `virelai_gates.py` | `_LeverTarget.next_probe` (`:3443-3530`) | **Order:** pending dossier or reachability, then None; confirmation; mu revisit; reopen jump (`:3488-3493`); NAV terrain classify and advance (`:3494-3497`); selection (`:3498`); chosen-row skip (`:3501`); CLICK→NAV flip (`:3502-3506`); NAV completion (`:3511-3513`); NAV envelope `G3-LEVERS:NAV:{index+1}:{steps+1}` (`:3518-3529`). |
| same | `_LeverTarget.validate_probe` (`:3775-3794`) | Re-derives `next_probe()`; one movement action plus `pilot_intent`. |
| same | `_LeverTarget.record_outcome` (`:3796-4362`) | Compares the probe id with `next_probe()`; the NAV scheduler block is at `:4286-4337`. |
| same | `_LeverTarget.planned_nav_step` (`:3590-`) | Reads the target it is handed; it re-reads the ledger's current cells for that entity (`:3613-3615`). It also raises the reachability certificate (`:3676`). |
| same | `_LeverTarget._submit_reachability` | Advances the cursor at `:4548`. |
| same | `CyberneticGateMachine.select_g3_question` (`:6726-6730`) | Phase-generic, and unchanged. |
| `controller_executor.py` | `_nav_step` (`:185-292`), G3 branch (`:268-292`) | `RANKED_CLICK_TARGET` → `_g3_click_step` (which holds the CLICK handoff). A `CONFIRM_LEVER_WITNESS` with actions → `_bound_step`. `PILOT_TO_LEVER_CONTACT` / `CONFIRM` → `adapter.planned_nav_step(capability["target"])`. **No NAV handoff.** |
| same | `_g3_choice_due` (`:171-182`), `_g3_click_step` (`:358-364`) | Unchanged in contract. |
| `library_agenda.py` | `_g3_questions` (`:117-151`), `_selected` (`:198-213`) | Read `admission_candidates`: a `selectable` row is `OPEN_ACTIONABLE`; the selection is the selected question while its entity is a candidate. **No edit is planned.** The agenda reports the gate's eligibility and adds no scheduler. |
| `inference/agent/memory_queries.py` | `:77` | `virelai('next_probe', question_id=…)` calls `select_g3_question`. **No edit.** |

## 2 · Every NAV cursor advance (each one ends a coverage pursuit)

| # | Site | Event |
|---|---|---|
| 1 | `record_outcome` `:4297` | Discovery on a `CONTACT_ATTEMPT`: an attributed activation witness, `LEVER_FOUND`. |
| 2 | `:4315` | Target changed on a `CONTACT_ATTEMPT`, with bounded ambiguity when attribution is unresolved. |
| 3 | `:4323` | `SCOPED_NULL_RESPONSE` or counter-only on a `CONTACT_ATTEMPT`: the target's scoped null. |
| 4 | `:4337` | A terminal boundary, or the pilot budget (`_navigation_limit`, 24). |
| 5 | `_submit_reachability` `:4548` | The reachability answer (`PRESUMED_UNREACHABLE` release). |
| 6 | `_advance_accounted_terrain_rows` (`:2875-2885`) | A terrain-typed or `_g3_settled` row (`G3-CLOSED` / `G4-READY`) is skipped. |
| 7 | `next_probe` reopen jump `:3488-3493` | A reopened reachability row; the cursor moves **back** to it. |
| 8 | Confirmation and dossier `finish_target` (`:4136`, `:4409`) | Already through `finish_target`. |
| 9 | CLICK→NAV flip `:3502-3506` | `_target_index = 0`. |

**Non-advancing events that end a pursuit:**
- A boundary-interrupted outcome, `:4289-4290`: `_navigation_steps = 0`, and the row stays at the head.
- A pending reachability certificate, which is an obligation (`next_probe` returns None until it is answered).

## 3 · The planned change, per file

| File | Function | Change |
|---|---|---|
| `g3_selection.py` (mine; the shared reader is the agenda) | `admission_candidates`, `select`, `_stale`, a new `selected_probe` (CLICK branch unchanged), `advance_past_chosen_rows`, `finish_target`, new `interrupt_pursuit`, `yield_choice`, `pursuit` (corrected, amendment 1) | **NAV rows become selectable** when all of these hold:<br>• no route pursuit is under way (`_navigation_steps == 0`), so the body contact a started pursuit owes keeps its priority;<br>• the row is the head, or its lifecycle state is `UNTOUCHED` or `NO_RESPONSE_YET` and it is not an inherited null;<br>• no obligation is pending, as today.<br>`AMBIGUOUS`, settled, terrain and reopened rows are never selectable away from the head.<br><br>**Admission** records the entity, its version and the admitting transition, then clears the route evidence and the last plan.<br><br>**NAV staleness:**<br>• a phase, level, life or roster change;<br>• the chosen object changed: any sighting after admission whose relation is not STILL, or the entity is not PRESENT;<br>• the row is settled.<br><br>**The bound NAV probe:** `G3-LEVERS:NAV:SEL:{member}:L{level}P{life}:R{revision}:{step}`. The prefix is the admission's identity and holds across its route steps; each step's probe and evidence id stay distinct.<br><br>**The chosen-row skip** also runs in NAV. `finish_target` resets the step count. A boundary ends a pursuit as STALE. |
| `virelai_gates.py` | `_LeverTarget.next_probe` | • The NAV envelope moves **unchanged** into a new `_nav_probe(probe_id, target)`.<br>• The reopen jump moves **unchanged** into a new `_take_reopened_row()`; it also ends a bound choice as STALE, because the reopened row comes first.<br>• `selected_click_probe` → `selected_probe`.<br>• The CLICK→NAV flip clears `_chosen_members`, because a row chosen in CLICK still owes its NAV body contact.<br>• Net NCNB must be ≤ 87. |
| same | `_LeverTarget.record_outcome` | • NAV advances 1-4 become `g3_selection.finish_target(self, target_member_id)`, each replacing two lines with one.<br>• The boundary reset becomes `g3_selection.interrupt_pursuit(...)`.<br>• `target_index_before` becomes `g3_selection.pursuit(self)`, so route evidence also clears when a selected off-head pursuit ends; with no choice it is the cursor alone, as today.<br>• Net NCNB must not grow (542). |
| same | `_LeverTarget._submit_reachability` | Advance 5 becomes `g3_selection.finish_target(self, member_id)`. |
| `controller_executor.py` | `_nav_step`, a new `_g3_pilot_step` | The G3 pilot tail moves **unchanged** into `_g3_pilot_step`, which adds the bounded NAV handoff:<br>• only for `PILOT_TO_LEVER_CONTACT`;<br>• through the existing `_g3_choice_due`, which allows one per phase per level, needs at least 2 selectable rows and no obligation, and records `COVERAGE_RESUMED` after a declined handoff.<br>The controller-only setting (`g3_choice_handoff=False`) offers no handoff. |
| `tests/test_g3_hybrid_click_pass.py` | `test_the_click_pass_offers_no_second_handoff_and_follows_the_record_into_nav` | Its last assertion pinned "no NAV handoff until NAV selection". Sol's ruling enables the NAV handoff in this slice, so the test is **revised**: one NAV handoff after the CLICK pass, then the first route step. The CLICK assertions are unchanged. |
| `tests/test_g3_directed_nav.py` (new, mine) | — | The fail-first tests (§4). |

**Unchanged:**
- The lifecycle and its transition table; attribution; the witness and certification path.
- `planned_nav_step`; `library_agenda.py`; `memory_queries.py`; `life_record.py` (no new attribute).
- The goldens (`tests/fixtures/g3_no_choice_golden.json`, sha `d9e08bd753af`): **not re-recorded**.
- SUB-4, G4 dossiers, PLAY-NORMAL wording and G2 bar-remainder targeting are out of scope.

## 4 · The records checked (post-reset continuity)

**k008, replayed to transition 42.** G3 enters NAV on the next capability call.
- **No board-record break:** `_board_record_breaks == []`, and `seed_limitations == []`.
- **Resets in the level:** transition 31.
- **The ego ledger is on the true board:** the ledger's grid equals the replayed grid.
- **Every row's first plan stands at (12, 16):** the ego's true post-reset footprint, which `test_k008_t44_plan_starts_from_the_egos_true_post_reset_footprint` verifies against the record board.
- **The NAV roster:** E0001 (the head), E0002, E0004, E0005 and E0006. All are `NO_RESPONSE_YET`, the CLICK pass's scoped nulls that owe body contact. These are **genuinely eligible** rows.

**k013, replayed to transition 400.**
- **No breaks.**
- **Resets in the level:** transitions 60, 113, 166, 219, 272, 325 and 378. The board is on life 8.
- **The roster:** 13 NAV candidates. Five are `AMBIGUOUS` and departed (E0015, E0018, E0020, E0021, E0023), so they are not selectable. Eight are `NO_RESPONSE_YET`.
- **The head's first planning call certifies the routing limit,** a reachability obligation, so k013 is the obligation case.

## 5 · Base hashes (sha256, first 12 characters; cloud equals device)

| File | sha |
|---|---|
| `virelai_gates.py` | `905b51dfbf59` |
| `g3_selection.py` | `7fe7420f4606` |
| `controller_executor.py` | `fc02c1c2a965` |
| `library_agenda.py` | `dbc8ff079ad8` |
| `test_g3_hybrid_click_pass.py` | `4aa1af4e74b3` |
| golden | `d9e08bd753af` |

## Amendment 1, 2026-10-12 (Sol's review of revision 1; filed in the same working session as revision 2's edit)

**Reference correction.** The table in §3 named a helper `yield_to_obligation`. The parked helper is `g3_selection.yield_choice(g3, reason)`; the reference now reads that. No helper of the old name exists.

**Revision 2 edit (one shared file, `g3_selection.py`; the owner is unchanged):**
- `yield_choice` ends a stale or overtaken choice with **one** STALE event. When the choice was a NAV pursuit, it also clears the pursuit's state: `_navigation_steps = 0`, `_nav_route_evidence`, `_last_nav_plan`. Coverage then resumes at `G3-LEVERS:NAV:{head}:1` with no selected-route evidence.
- `selected_probe` routes its staleness path through `yield_choice`, so the object-change, new-life, phase, level, roster and settled paths all share this one reset.
- `interrupt_pursuit` (a boundary) notes its own STALE and leaves the route evidence for `record_outcome`. That keeps the boundary outcome's receipt intact; `record_outcome` clears the evidence at its end, because the pursuit changed.
- `virelai_gates.py`, `controller_executor.py` and the revised `test_g3_hybrid_click_pass.py` are **unchanged from revision 1**.

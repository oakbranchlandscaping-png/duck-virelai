# Build slice: WO-G3-DIRECTED, CLICK (the gate agenda, G3's own eligibility read, an admitted choice)

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET_v2_2026-10-11`: Sol's decisions D1–D4 and corrections C1–C3;
- `NOTE_SHARED_FILE_WO_G3_DIRECTED_CLICK_2026-10-11`, filed before any shared edit;
- ruling 22, caution 2.

**For review before the NAV slice** (D1).
**Revision 2:** closes Sol's review of revision 1 (§0a) and adds durable selection events. Sol re-reviews before NAV starts.

**Base:**
- `472aa32` code and `8e13e35` (documents, local);
- **plus the held library-view slice** (uncommitted; Mac 707 passed, 1 skipped). This slice edits `memory_queries.py`, which the held slice also changes, so **the held slice must be committed first**.
- `PLAY-NORMAL` is untouched. `library_view.py` and `tool_agent.py` (held-slice files) change only for finding 1 (§0a), after the held slice is committed on its own.

## 0 · What landed

| File | Change |
|---|---|
| `inference/framework/library_agenda.py` (new, pure) | The **gate agenda**:<br>- one question per gate, in ruling 22's wording;<br>- one IS_LEVER question per G3 entity, with dispositions from the lifecycle, terrain and witnesses;<br>- G4 per-lever questions for every witnessed lever, **`BLOCKED_BY_PREREQUISITE` until `LeverInventory` is active** (C1);<br>- the five NOT_BUILT chapters, never selectable;<br>- the selected question: obligation, then an admitted choice, then the coverage head, then the active gate's question;<br>- `agenda_revision`.<br>`census_agreement` compares it with the validated census. |
| `inference/framework/g3_selection.py` (new) | Functions over the G3 adapter, kept outside the gate class as `mu_return` is:<br>- `obligation` and `admission_candidates` (**pure reads**);<br>- `select` (admits, or refuses once with a reason);<br>- `selected_click_probe` (the identity-based off-head probe, D2);<br>- `finish_target`;<br>- `advance_past_chosen_rows`;<br>- the handoff pair (D3). |
| `virelai_gates.py` (shared) | `_LeverTarget`:<br>- four new attributes;<br>- `next_probe` serves a valid off-head selection and skips rows a choice finished;<br>- the target block and the CLICK envelope moved **unchanged** into `_probe_target` / `_click_probe`;<br>- three CLICK-reachable cursor advances call `finish_target`.<br>Machine: `select_g3_question`, and the capability carries `question_id`. The NAV sites, the lifecycle table and every G4 gate are unchanged. |
| `life_record.py` (shared) | The four attributes: `_selection` TRANSIENT; the other three LEVEL. Revision 2 adds the machine's `g3_selection_events` and `g3_selection_flushed`, both GAME. |
| `controller_executor.py`, `controller_turn.py` (shared) | The bounded handoff (D3), on in the live session and off for controller-only drivers |
| `card_builder.py` (shared) | The card carries `question_id` |
| `memory_queries.py` (shared; held-slice file) | `virelai('next_probe', question_id=Q)` admits the choice and returns the freshly bound capability. A refusal returns a compact state plus the current question. |
| `inference/framework/library_view.py`, `inference/agent/tool_agent.py` (held-slice files; revision 2) | The digest's goal is the agenda's selected question (finding 1) |
| `inference/agent/gate_artifacts.py` (shared; revision 2) | `flush_g3_selection_events`, called after each recorded outcome. `memory_queries._chosen_probe` and the `run_controller_turn` wrapper also flush. |
| `tests/test_g3_directed_click.py` (new) | 47 tests (§2) |
| `tests/g3_no_choice_trace.py`, `tools/record_g3_no_choice_golden.py`, `tests/fixtures/g3_no_choice_golden.json` (new) | Test 0's trace and its golden file. The golden file (sha256 `e03355872259a971…`) was written at 08:46, **before** the first shared edit (`virelai_gates.py` was first changed at 09:40), and written twice, byte-identical. |
| `tests/test_memory_m2.py`, `tests/test_sub2_submission_hardening.py` | Fixture and stub updates (§3) |

## 0a · Sol's review of revision 1: what closed

| Finding | Fix | Test (§2, group 8) |
|---|---|---|
| **1 · The digest named the gate, not the selected question.** `library_view._goal` read the gate marked `IN_PROGRESS`. | `library_digest(model, budget, *, target=None)`: the target is the agenda's selected question, from the new `library_agenda.selected_target(machine)`. It becomes the goal: `question_id`, gate, question, level. `tool_agent._library_digest_section` passes it. With no target (a saved record) the goal is unchanged. Budgets and tiers are unchanged; the goal adds 48 characters (k013 at 400: 2,106 → 2,154 of 3,000). | Through `agent._gate_context_update`, the rendered card and digest plus the capability give `card.question_id == digest.goal.question_id == capability.question_id == agenda.selected`. Checked at carry-v7 3 (no choice), 3 (a choice), 7 (a confirmation obligation) and 20 (after the inventory). The goal survives the minimal tier at budgets of 3,000, 1,200 and 700. |
| **2 · An explicit head choice lost the choice.** `selected_click_probe` returned `None` for the head, so the coverage envelope served it unbound. | A valid head choice now gets the bound SEL envelope: `G3-LEVERS:CLICK:SEL:{member}:L{l}P{p}:R{rev}`, with `target.question_id` and `selected_by`. The no-choice envelope is unchanged (the golden trace still holds). `finish_target` records `FINISHED` for a head choice too, and advances the cursor. | carry-v7 at 3: before any choice the head's probe is `G3-LEVERS:CLICK:1` with no `question_id`. After the choice it is the SEL probe on the same action with a new token. The transition row names it, and the head's `G3-CLOSED` event cites that row's evidence. Events read `ADMITTED`, `FINISHED`. Coverage resumes at `G3-LEVERS:CLICK:2` on the next row. |
| **3 · G4-C was checked against `SUPPORTED`.** The product writes `COMPLETE`, `UNRESOLVED` or `CLOSED_BY_LEVEL_BOUNDARY` (`g4c_gate.py:264`). | `PRODUCT_STATUS` maps each product status to a disposition: COMPLETE → `ANSWERED`, UNRESOLVED → `CLOSED_UNRESOLVED`, a level boundary → `CLOSED_BY_LEVEL_BOUNDARY`. Gate questions, G4-B and G4-C use it. Under an unresolved G4-B close, pressed levers read `PARTIAL_CLOSED_UNRESOLVED`. | Product-backed, on the real ft09 levers (`start_g4b`):<br>- a supported new prediction gives product `COMPLETE`, and the G4-C gate question and every lever's LAW question read `ANSWERED`;<br>- `close_unresolved` gives `UNRESOLVED` and `CLOSED_UNRESOLVED`. |
| **4 · The timeout fallback had no live-path test.** | No code change was needed; the test exercises the real session path. | `_HarnessGameSession.play` with the production `ToolAgent`, the live handoff on (the default), and an ft09-backed game. The handoff reaches the model once ("G3 choice"). The prompt's card and digest name the coverage head's question. The model answers without a tool call while the turn-time budget runs out, so the turn yields with `turn_time_budget`. The next turn is the controller's: one action, envelope executor `CONTROLLER`, purpose `RANKED_CLICK_TARGET`, a coverage (non-SEL) probe id on the head that Duck was shown. The receipt, the transition row and the envelope agree on probe id and evidence. Turn ledger: `DUCK turn_time_budget`, then `CONTROLLER controller_step`. Selection log on disk: `HANDOFF`, `COVERAGE_RESUMED`. The run is not stopped (`_l2a_end_reason` is empty). |
| **Durable events** | Each event row (schema `virelai-g3-selection-event-v1`, with level, life, phase, actor, reason and transition) goes to the adapter and to a game-long `machine.g3_selection_events` list (GAME tier). `gate_artifacts.flush_g3_selection_events` appends unflushed rows to `{stem}_g3_selection_events.jsonl` after every recorded outcome, after every `virelai('next_probe', question_id=…)`, and at the end of every controller turn. `COVERAGE_RESUMED` marks a handoff that produced no choice. | Through the real tool bridge, an admitted choice and then a refused one, with no action taken: the file holds `ADMITTED`, then `REFUSED` with its reason. The live test above covers a handoff with no choice. |

**Fail-first:** the nine group-8 tests were run against revision 1 (the first delivery's code, plus the held `library_view.py`/`tool_agent.py` and `gate_artifacts.py` at `472aa32`). **All 9 failed**:
- the digest goal had no `question_id` (4 surface tests and the live test);
- `selected_target` did not exist (minimal tier);
- the head target had no `question_id`;
- `COMPLETE` did not read as `ANSWERED`;
- there was no events file.

**Sol's decision on memory ruling D2, recorded.** This is ruling D2 of R9-R08 ("G0–G3 with zero model calls"), not Sol's decision D2 on probe ids. Sol, 2026-10-11: ruling 22 supports this bounded G3 choice. **The live one-turn handoff amends ruling D2's "zero model calls through G3" expectation for the live session. The controller-only test mode (`g3_choice_handoff=False`) is kept as a regression guard.** The m2 ft09 tests keep that mode; the m2 handoff test and the live-path test above pin the live default.

## 1 · The chain on a saved record (question → admitted action → receipt → verdict → revised question)

Carry-v7, a CLICK world, at transition 3 (the G3 sweep):

| Step | Observed |
|---|---|
| 1 · Question, with no choice | `Q:L1:G3-LEVERS:E0001:IS_LEVER` (the coverage head); 10 eligible rows |
| 2 · Admitted choice | Duck selects `Q:L1:G3-LEVERS:E0002:IS_LEVER`. The capability names the same question and binds `ACTION6 (44, 50)`, and the head's token is now stale. |
| 3 · Receipt | Transition 4, `G3-LEVERS:CLICK:SEL:M0011:L1P1:R2`, evidence `E-a82ebdc11a699ff7` |
| 4 · Verdict | E0002 `G3-CLOSED` (a CLICK world's scoped null), no witness, citing that evidence |
| 5 · Revised question | E0002 is `ANSWERED_SCOPED_NULL`. The next selection is the untouched head E0001. The agenda revision moved from `4bd48adb9196` to `6bd8807eeb8b`. The selection events read `ADMITTED`, then `FINISHED`. |

## 2 · Tests, and the fail-first evidence

**Before any shared edit:** 30 failed, 7 passed.
- The 7 that passed were:
  - test 0 (×3), a guard written first;
  - test 1 (×2), the pure foundation half;
  - test 3 after the inventory;
  - test 7 at a non-G3 cut.
- The 30 failures came from the missing gate read (`admission_candidates` and `obligation`), the missing `question_id`, `select_g3_question` and the handoff.
- The tool-bridge test and the m2 handoff test were written afterwards, against the shared edits.

**After:** 47 of 47 pass (38 in revision 1, plus the 9 in group 8). The tests by number:

| # | What passes |
|---|---|
| **0** | k008, k013 and carry-v7 replayed with no choice: every probe id, probe-envelope hash and evidence id (60, 395 and 26 outcomes), every product, frozen level, transition row and G3 lifecycle state **equal the golden trace** (D2) |
| **1** | An empty CLICK world selects G0's question and has no G3 question, no answered role, and NOT_BUILT never eligible or selected. The carry-v7 level-2 entry restarts at G0 with no level-1 levers. |
| **2a** | Duck selects a non-head row: a fresh token, an identity-based probe id, the outcome attributed to the chosen row, the head untouched, and the coverage head resumes. The coverage sweep never serves the chosen row again. |
| **2b** | Carry-v7: the default controller path is unchanged. With the handoff on: one `DUCK` "G3 choice" step, then the controller serves the head. |
| **2c** | A second selection stales the first token. A new life drops the selection (`STALE`) and the head resumes. An inadmissible question (a NOT_BUILT chapter, an unknown entity, or text that is not a question) is refused with its reason and recorded once. No choice is admitted while a confirmation is owed. |
| **2d** | A chosen click whose change lands elsewhere never produces a witness |
| **3** | k013 at 400: 9 witnessed levers, each with 4 G4 questions, all `BLOCKED_BY_PREREQUISITE` on `G3-LEVERS` (inventory pending, C1), none eligible. After the inventory (carry-v7 at 20), E0004 and E0005 have separate question sets. |
| **5** | At 13 G3 cuts (carry-v7 at 3–15; k008 at 38–60, CLICK and NAV), the agenda's selection **equals what the gate serves** (the click or pilot target, or the confirmation obligation), and `capability.question_id == agenda.selected == card.question_id`. An answer turn (carry-v7 at 8, a dossier due) aligns card and agenda with no capability (C2). Through the real `ToolAgent` bridge, `virelai('next_probe', question_id=Q)` binds Q, and the card names Q. |
| **6** | k013: the 5 INCONCLUSIVE rows stay typed and are not eligible; nothing is FILLED. After `rest_in_play`, the selected question is PLAY-NORMAL's `OPEN_FALLBACK`, with nothing eligible. |
| **7** | At 5 cuts: the agenda leaves the machine byte-identical, is deterministic and JSON-stable, and **`census_agreement` with the validated census is empty** |
| **8** | Sol's review (§0a): the three surfaces (×4 cuts), the digest's goal at the minimal tier, the bound head choice, G4-C on real product statuses, the durable refusal log, and the live-path timeout |

## 3 · Behaviour changes, said plainly

1. **Live CLICK worlds now spend one Duck turn at G3**, at most once per phase per level (D3).
   - **Sol confirmed this amends ruling D2's zero-model G3 for the live session** (§0a). Controller-only mode is kept as a regression guard.
   - If Duck makes no choice (a timeout, or a turn without one), the controller resumes the coverage head the next turn. That is recorded as `COVERAGE_RESUMED`; there is no stop.
2. **An explicit head choice is now bound** (SEL envelope). The no-choice coverage path is unchanged.
3. **The digest's goal is the selected question** whenever the live machine is present. A saved record read without a machine keeps the gate-in-progress goal.
4. **A new run artifact**, `{stem}_g3_selection_events.jsonl`, written only when G3 choice events exist.
5. **The card and every capability carry `question_id`.** Coverage probe envelopes, ids and evidence ids are unchanged (test 0).
6. **The `test_sub2` stub** of `next_owned_step` gained the new keyword. No assertion changed.

## 4 · Verification

| Run | Result |
|---|---|
| Cloud, focused (revision 2): directed G3, m2, life record, library view, L2a close, m0, G4-C | **110 passed** |
| **Cloud, full** (Python 3.12, 98 files; revision 2) | **755 passed, 1 skipped**, 0 failed |
| **Mac, focused** (revision 2, over `125d4d0`) | **110 passed** (4:41) |
| **Mac, combined floor** (held view `125d4d0` + revision 2; `--ignore=tests/test_physics_grammar_contract.py`) | **755 passed, 1 skipped** (20:51); matches the cloud |
| ruff | The new and changed files are clean. `virelai_gates.py` keeps its 2 pre-existing findings (F402, F601). |

How the count adds up: 755 = 707 (the held-slice floor) + 47 directed-G3 tests + 1 m2 handoff test. Revision 1 was 746.

The live-path test (group 8) drives 58 actions of a real `_HarnessGameSession` on the ft09 continuation, so it is the slowest test in the file: 31 s in the cloud.

**Agenda latency** (200 calls, after the gate's step call):

| Point | Questions | Median | p95 | p99 |
|---|---|---|---|---|
| k013 at 400 | 125 | 1.13 ms | 1.22 ms | 1.30 ms |
| k008 at 44 | 21 | 0.23 ms | 0.32 ms | 0.33 ms |
| carry-v7 at 9 | 28 | 0.26 ms | 0.35 ms | 0.40 ms |

The agenda runs once per capability and once per card, and the full census stays off this path.

**Card size:** about +96 characters (k013 at 400: 3,949 → 4,045).

## 5 · Ratchet (non-blank, non-comment lines)

| Function | Before | After |
|---|---|---|
| `_LeverTarget.next_probe` | 132 | **87** (the target block and the CLICK envelope moved out unchanged) |
| `_probe_target` / `_click_probe` | — | 38 / 17 (moved code) |
| `_LeverTarget.__init__` | 46 | 50 |
| `CyberneticGateMachine.__init__` | 18 | 20 (revision 2: the event log) |
| `next_probe_capability` | 39 | 41 |
| `_ordinary_step` | 21 | 24 |
| `next_owned_step` | 15 | 16 |
| `build_card` | 36 | 38 |
| `run_controller_turn` | 45 | **10**: a wrapper that flushes. The body is unchanged in `_run_controller_turn` (46). |
| `record_probe_outcome` | 58 | 59 (one flush call) |
| `gated_memory_query` | 26 | 30 (+`_chosen_probe` 12) |
| `library_view._goal` / `_digest_at` / `library_digest` | 6 / 30 / 10 | 9 / 31 / 11 (held-slice baseline) |
| `tool_agent._library_digest_section` | 6 | 7 |
| `virelai_gates.py` file | 7,023 | 7,048 |

The selection logic lives in `g3_selection.py` (158 lines). `library_agenda.py` is 246 lines.

## 6 · Findings for Sol

1. **A HYBRID world's CLICK pass is handed to Duck at every step today, not just once.**
   - `controller_executor._nav_step`'s G3 branch accepts only `PILOT_TO_LEVER_CONTACT` and `CONFIRM_LEVER_WITNESS`. In k008's CLICK pass (`RANKED_CLICK_TARGET`), every step therefore goes to Duck ("G3 NAV cannot compute RANKED_CLICK_TARGET").
   - This predates the slice and probably explains some of v2's Duck turns in HYBRID games.
   - **Sol ruled this the first NAV repair.** A one-branch fix would serve the bound click as `_ordinary_step` does, then apply the same bounded handoff.
2. **An ambiguous, unbound off-head choice is dropped as stale and not retried.**
   - The head retries an ambiguous row in place, and an explicitly chosen head does too, keeping its SEL id.
   - A chosen off-head row is instead released to the coverage sweep, which reaches it later.
   - The record keeps the ambiguity. This is a design choice, and it does not widen the lifecycle.
3. **Retried probes reuse their id.** A retry in place reuses its probe id: `CLICK:{n}` on coverage, the SEL id on a choice. Revision 1 already did this, and each attempt is still its own transition row. I am noting it only because the head choice now carries a SEL id.

## 7 · Next

1. **Done:** the held library-view slice is committed alone as `125d4d0` on `ring9-unified` (local, unpushed), with the held `memory_queries.py` (`c7331f35`) restored first.
2. **Done:** revision 2 is copied (all 11 hashes verified). The Mac results are the focused 110 and the combined floor of 755 passed, 1 skipped. The commit stays held.
3. Sol re-reviews the CLICK integration (`BUILD_REPORT_WO_G3_DIRECTED_CLICK_v1_2026-10-11`).
4. The NAV slice (Claude, D1):
   - the HYBRID CLICK-pass fix first (finding 1);
   - NAV selection under pursuit;
   - `planned_nav_step` toward a selection;
   - the NAV `finish_target` sites;
   - tests 2a–2c on NAV cuts.
5. Then the v3 dossier schema (D4).

— Claude, Alpha build seat (click line)

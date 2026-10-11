# Shared-file note, 2026-10-11 (WO-G3-DIRECTED, CLICK slice)

**Filed by:** Claude, Alpha build seat (click line), **before any shared edit** (ruling 9).
**Design:** `INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET_v2_2026-10-11`, which carries Sol's four decisions and three corrections.
**Implementation owner:** Claude, for CLICK now and NAV after Sol reviews this slice. Sol owns the interface and the NAV review; there are no concurrent edits to `virelai_gates.py`.

**Base:**
- `472aa32` code;
- `8e13e35` (documents, local);
- **plus the held library-view slice**, which is uncommitted, Mac-verified at 707 passed, 1 skipped, and touches `memory_queries.py`, `tool_agent.py`, `solver.py` and `world_model_v2.py`.

This slice edits `memory_queries.py`, so it sits on top of the held slice: the held slice must be committed first. Nothing in the held slice's own changes is altered. `library_view.py` and the `PLAY-NORMAL` wording are not touched.

| File | Function | Change |
|---|---|---|
| `inference/framework/virelai_gates.py` | `_LeverTarget.__init__` (`:2507-`) | New: `_selection` (TRANSIENT), `_chosen_members`, `_selection_events`, `_choice_handoffs` (all three LEVEL) |
| same | new `_LeverTarget.obligation()` and `_LeverTarget.admission_candidates()` | **Pure reads.** The gate's own pending work, and the rows the scheduler would serve, in coverage order. They never call `_ensure_*` or `next_probe`. |
| same | new `_LeverTarget.select(question_id, *, actor)` and `CyberneticGateMachine.select_g3_question` | Admits a choice among selectable CLICK rows. The refusal is recorded once; there is no repair loop. |
| same | `_LeverTarget.next_probe` (`:3418-3547`) | The CLICK branch serves a valid selection, with a new identity-based probe id. The coverage path, its probe ids and its envelopes are **unchanged**. CLICK skips rows already settled by a choice. |
| same | `_LeverTarget.record_outcome` / `_submit_dossier`, at the CLICK-reachable cursor sites (`:4097`, `:4310`, `:4370`) | `self._target_index += 1` becomes `self._finish_target(member_id)`: a finished off-head choice clears the selection and leaves the cursor in place. The NAV sites are unchanged until the NAV slice. |
| same | `CyberneticGateMachine.next_probe_capability` (`:6616-6654`) | The capability gains `question_id`, the agenda's selected question. The probe envelope and the token are unchanged for the coverage path. |
| `inference/framework/life_record.py` | `PERSISTENCE["_LeverTarget"]` | The four new attributes |
| `inference/framework/controller_executor.py` | `next_owned_step` and `_ordinary_step` (`:119-163`) | An optional `g3_choice_handoff`: at most one Duck handoff per G3 phase per level, when there are at least two selectable rows and no obligation. Default **off**, so controller-only drivers and replays are unchanged. |
| `inference/agent/controller_turn.py` | `ControllerSession`, `run_controller_turn` (`:54-100`) | The live session passes `g3_choice_handoff=True`. A timeout or no selection resumes the coverage head; there is no stop and no repair loop. |
| `inference/framework/card_builder.py` | `build_card` (`:553-589`) | The card gains `question_id` (the agenda's selected question) beside `gate_id` |
| `inference/agent/memory_queries.py` (held slice file) | `gated_memory_query` | `virelai('next_probe', question_id=Q)` admits the selection, then returns the freshly bound capability |

**Not shared** (mine):
- `inference/framework/library_agenda.py` (new, pure);
- `tests/g3_no_choice_trace.py`;
- `tools/record_g3_no_choice_golden.py`;
- `tests/fixtures/g3_no_choice_golden.json`, written from current code **before** any shared edit;
- new tests.

**Untouched:**
- `lever_lifecycle.py` (the transition table is not widened);
- the NAV pursuit, `planned_nav_step`, reachability and terrain;
- every G4 gate;
- `library_view.py`;
- `play_gate.py`;
- SUB-4.

## Amendment 1, 2026-10-11, filed before the review-fix edits (Sol's review of the CLICK slice)

**Correction to the table above:**
- `obligation`, `admission_candidates` and `select` landed as functions in the new `inference/framework/g3_selection.py`, not as `_LeverTarget` methods. This keeps the gate class within the ratchet.
- `_finish_target` is `g3_selection.finish_target(self, member_id)`.

**Shared edits for Sol's four findings and the durable events:**

| File | Function | Change |
|---|---|---|
| `inference/framework/library_view.py` (held slice file) | `_goal`, `_digest_at`, `_minimal_digest`, `library_digest`, `render_library_digest` | Finding 1. An optional keyword `target`, the agenda's selected question, becomes the digest's goal, `question_id` included. Without a target the goal is the gate in progress, unchanged for a saved record. The budget and tiers are unchanged. |
| `inference/agent/tool_agent.py` (held slice file) | `_library_digest_section` | Passes `library_agenda.selected_target(machine)` |
| `inference/framework/virelai_gates.py` | `CyberneticGateMachine.__init__` | `g3_selection_events` and `g3_selection_flushed`: the game-long event log and its flush mark |
| `inference/framework/life_record.py` | `PERSISTENCE["CyberneticGateMachine"]` | Both attributes, at the GAME tier |
| `inference/agent/gate_artifacts.py` | new `flush_g3_selection_events`; `record_probe_outcome` | Appends unflushed events to `{stem}_g3_selection_events.jsonl`. Called after each recorded outcome. |
| `inference/agent/memory_queries.py` | `_chosen_probe` | Flushes in `finally`, so a refusal reaches disk with no action taken |
| `inference/agent/controller_turn.py` | `run_controller_turn` | Now a wrapper: the unchanged body moved to `_run_controller_turn`; the wrapper flushes in `finally` |
| `inference/framework/controller_executor.py` | `_g3_choice_due` | Records `COVERAGE_RESUMED` once after a handoff that produced no choice |

**Mine** (`g3_selection.py`, `library_agenda.py`, tests):
- Finding 2: an explicit head choice is bound with its own envelope.
- Finding 3: product statuses map to dispositions.
- The `selected_target` read.

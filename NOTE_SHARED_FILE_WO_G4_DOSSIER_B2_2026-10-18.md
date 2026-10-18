# Shared-file note: WO-G4-DOSSIER-B, slice B2 (2026-10-18), amended for revision 4

- **Filed by:** Claude, Alpha build seat.
- **Base:** `0119a74` on `ring9-unified`.
- **Authority:** Sol's rulings 5–7; `INTERFACE_WO_G4_DOSSIER_B2_v1`; Sol's review of B2 revision 1; `AMENDED_INTERFACE_WO_G4_DOSSIER_B2_v2`; `AMENDMENT_WO_G4_DOSSIER_B2_rev3`; `AMENDMENT_WO_G4_DOSSIER_B2_rev4`.

## New files

| File | Contents |
|---|---|
| `inference/framework/g4_selection.py` | G4-A's gate-owned admission of a per-lever choice. G4.1 candidates are listed and never selectable (revision 2). Revision 3 removes `dossier_question` and `question_problem`, and a replaced standing choice is recorded `STALE`. Revision 4: a close (`STALE`, `FINISHED`) is scoped to its admission; `close_at_level_change`; `admitted_action` unbinds an off-choice action. |
| `inference/framework/lever_dossier_selection.py` | Revision 3: the pure v8 validation step for the saved model's chain — admitted question → selected-run receipts → orbit chapter — and `dossier_question`. Revision 4: the selection log as a state machine. |
| `tests/test_g4_selection_persisted.py` | Revision 3: the canonical-artifact tests and attacks |
| `tests/test_g4_selection.py`, `tests/g4_no_choice_trace.py` | The B2 tests and the controller-driven drive |
| `tools/record_g4_no_choice_golden.py`, `tests/fixtures/g4_no_choice_golden.json` | The golden, written from `0119a74` before any production edit |
| `tests/test_provenance_v2.py` | Revision 2: audit schema v2, the frozen v1 reader, world model v8 |
| `tests/fixtures/provenance_v1_journal.jsonl`, `tests/fixtures/world_model_v7_frozen.json` | Revision 2 fixtures, written by `0119a74` code |

## Shared files edited

| File | Change |
|---|---|
| `virelai_gates.py` | Delegation only, all in G4-A and the machine: `next_probe` (settle, `bound_probe`); `**g4_selection.receipt(probe)` on the two G4-A event dicts; `_g4_selection` in `_LeverStudyTarget.__init__`; `g4_selection_events` and `g4_selection_flushed`; `select_question`; one G4-A card rule. **Revision 2 removes every G4.1 hook**, so `_ReactionTarget` is `0119a74`'s. **Revision 4** adds two delegation lines: `_advance_level` → `close_at_level_change`; `validate_probe` (guided) → `admitted_action`. |
| `controller_executor.py` | `_orbit_lever`, `_nav_orbit_step` (moved out of `_nav_step`) and `_chosen_note`. With no choice, steps and reasons are unchanged. |
| `library_agenda.py` | `_selected` delegates G4.1 and G4-A to `g4_selection.selected_question`; in G4.1 that is always the head. LIMITS rows are `OPEN_NOT_ACTIONABLE`. Admissible G4-A rows carry `admissible: true` and join `eligible`. |
| `life_record.py` | Persistence tiers for the new fields. Revision 2 drops G4.1's. |
| `memory_queries.py` | `next_probe` with `question_id` calls `select_question`. |
| `gate_artifacts.py` | G4 events are flushed to `{stem}_g4_selection_events.jsonl`. |
| `provenance_capture.py` | `_sync` drains G4 events; `selection_event_count`. |
| `audit_journal.py` | **Revision 2:** the writer writes `virelai-provenance-v2`. `VALID_V1` and `REASON_CODES_V1` are frozen, with v2 = v1 plus `G4_SELECTION` / `G4_EVENT`. Rows are checked per schema; a journal never mixes schemas. Adds the frozen readers `read_journal_v1`, `read_journal_bytes_v1` and `verify_embedded_v1`; the writer continues an open journal in its own schema. Also `translate_g4_event` and `g4_cursor`. |
| `provenance_chapter.py` | **Revision 2:** `CHAPTER_SCHEMA` becomes `virelai-provenance-chapter-v2` (`CHAPTER_V1` frozen). `validate_chapter(payload, frozen_v1=...)` re-verifies the embedded rows under v1 only for a frozen chapter. `G4_SELECTION` rows index as `selections`. |
| `world_model_v2.py` | **Revision 2:** `SCHEMA` becomes **v8**. Adds `V7_SCHEMA` and a frozen `validate_v7`, which `read_world_model` dispatches. v4–v7 validate chapter v1 with audit-v1 rows; v8 validates chapter v2. Dossiers are validated in v7 mode for v7 and v8. **Revision 3:** `_validate_selections` (v8 only) calls `lever_dossier_selection.problems`. |
| Tests pinning the writer schema | v7 → v8: `test_descriptive_events`, `test_wo_l2a_census_paths`, `test_world_description`, `test_world_model_v4_provenance`, `test_world_model_v5_product_content`, `test_world_model_v6_dossiers`, `test_world_model_v6_dossier_records`. |
| `tests/tiers/test_tiers.toml` | `T0.g4-selection` (with `test_provenance_v2` and, in revision 3, `test_g4_selection_persisted`). `test_g4_selection` and `test_g4_selection_persisted` join `T1.g3-directed`. The audit test, `test_provenance_v2` and `test_g4_selection_persisted` join `T1.paper-evidence`. |
| `tests/tiers/T2_collected.txt` | +43 against `0119a74`, 0 removed (1215) |

## Unchanged

These are untouched:

- the G4 logic modules and `g3_selection`;
- every dossier module and the dossier schema;
- every product payload on the no-choice path;
- `controller_turn`, `card_builder` and `library_view`.

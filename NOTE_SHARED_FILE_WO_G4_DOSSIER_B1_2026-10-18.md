# Shared-file note: WO-G4-DOSSIER-B, slice B1 (2026-10-18), amended for revision 2

- **Filed by:** Claude, Alpha build seat.
- **Base:** `87639d7` on `ring9-unified`.
- **Authority:** Sol's rulings 1–7 on `INTERFACE_WO_G4_DOSSIER_B_v1_2026-10-18.md`, and Sol's B1 review (revision 2).

## New files

- `inference/framework/lever_dossier_state.py`: pure derivation of each lever's record-derived observations. Its one machine read uses attribute reads only and never calls `_ensure_*`. Revision 2: a reset that opens the life is its entry; any other reset fails the observations closed.
- `tests/fixtures/world_model_v6_frozen.json`: a v6 model sealed by `87639d7`'s code, for the frozen v6 reader.

## Shared files edited

| File | Change |
|---|---|
| `world_model_v2.py` | `SCHEMA` becomes **v7**. Adds `V6_SCHEMA` and a frozen `validate_v6`; `read_world_model` dispatches v6. Dossier validation runs in v6 or v7 mode. |
| `lever_dossiers.py` | `attach` reads the scope once (`lever_dossier_state.observe`). Each dossier gains `observations`. `_seal` lets the limits chapter read them and, in revision 2, sets the limits basis (or the labelled `prior_basis`) from what is still owed. `finalize` fails mismatched observations closed. |
| `lever_dossier_facts.py` | Limits readings and limits open items. Revision 2 adds `limits_basis`. The derived chapter's `probe_owed` and `unavailable` follow the observations, in v7 only. |
| `lever_dossier_schema.py` | Observation validation and the v6/v7 dossier key sets. Revision 2 adds: `RECORD_OBSERVED_NOT_GATE_CERTIFIED` in `BASES["IN_PROGRESS"]`, pinned to the observations (never in v6); the `entry_reset` scope key resolved against the record's resets; the `RESET_INSIDE_LIFE` failure basis. |
| `lever_dossier_provenance.py` | Observations resting on a contradicted receipt fail closed. Unchanged in revision 2. |
| `world_description.py` | One observations line per dossier. Revision 2 adds "from reset tN" when the life opened at a reset. |
| `world_report.py` | The observations line. Revision 2 adds the canonical path `levels[i].lever_dossiers[E].observations` to its refs. |
| `tests/test_world_description.py` | Writer pin v6 → v7. **Revision 2 changes the shared report-reference checker**: `_resolves` accepts a mapping key in a path (`lever_dossiers[E]`), resolves it, and refuses it on a line about another lever. `_assert_report_refs` requires every observations line to cite its own observations path. Existing callers are unchanged: the new `subject` argument defaults to None, and no earlier report line uses a keyed path. |
| Other tests pinning the writer schema | v6 → v7 (the same files revision 1 pinned). |
| `tests/tiers/T2_collected.txt` | +21 tests against `87639d7`, 0 removed (1172). |

## Unchanged (Sol's B1 boundary)

These are untouched:

- every gate module;
- `library_agenda`, `g3_selection`, `controller_executor`, `controller_turn` and `card_builder`;
- `level_record`, `g4_relations` and `g4_limits`, whose functions are imported read-only;
- `library_census`;
- `library_view`;
- product payloads.

No controller-path code changed.

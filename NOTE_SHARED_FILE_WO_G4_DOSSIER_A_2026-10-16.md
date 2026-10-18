# Shared-file note: WO-G4-DOSSIER-A, schema v6 lever dossiers (2026-10-16)

**Filed by:** Claude, Alpha build seat, **before any shared edit**
**Base:** `ring9-unified` at `e8984c2`
**Interface:** `INTERFACE_WO_G4_DOSSIER_A_v2_2026-10-16`, §8
**Integration owner:** Claude, for every file below

## New files

All paths are under `inference/framework/` except the tests.

- `strict_json.py`: the one strict canonical JSON helper (R10).
- `lever_dossier_facts.py`: pure projections from payload-shaped dicts to chapter facts.
- `lever_dossiers.py`: the gate-view extraction (attribute reads only), chapter builders, status, integrity, census labels, `attach` and `finalize`.
- `lever_dossier_schema.py`: the pure v6 dossier validator.
- `tests/test_world_model_v6_dossiers.py`: the fail-first suite (cases 1–30).
- `tests/dossier_fixtures.py`: states built from the committed record fixtures.
- `tests/fixtures/world_model_v5_frozen.json`: a v5 model sealed by `e8984c2`'s code, for the frozen reader.

## Edited shared files

| File | Planned change |
|---|---|
| `answer_shapes.py` | `canonical_json` delegates to `strict_json` |
| `product_content.py` | `_strict` and `canonical_json` delegate to `strict_json`; messages keep their prefix |
| `world_model_v2.py` | `SCHEMA` v6; `V5_SCHEMA`; frozen `validate_v5`; v6 strict whole-payload check before hashing and in validation; v6 dossier validation; `read_world_model` dispatches v1–v6 |
| `library_census.py` | exactly two delegation lines (Sol-approved): `compile_level` returns `lever_dossiers.attach(machine, level)`, and `compile_world_model` passes its levels through `lever_dossiers.finalize` |
| `library_view.py` | `_cache_key` adds the G4 adapter revisions (R11); the digest findings gain one dossier line, plus the selected lever's chapters when the selected question names a certified lever (R9); the `dossiers` page by id lists that lever's chapters |
| `world_description.py` | `_dossiers` renders stored v6 dossiers (the v3–v5 stub is kept); a chapter-row helper |
| `world_report.py` | dossier and chapter lines from the same rows |
| tests pinning `virelai-world-model-v5`, and hand-built models | the version string, and the `lever_dossiers` a v6 model requires (compiled from a stated gate view, never hand-written facts) |
| `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | a new T0 `g4-dossier`; the v6 suite added to T1 `description` and `paper-evidence`; the new ids, none removed |

## Unchanged

- every gate module (`virelai_gates`, `g4_*`, `g4b_gate`, `g4c_gate`, `play_gate`, `lever_*`, `g3_*`, `cybernetic_targeting`);
- `controller_turn`, `controller_executor`, `card_builder`, `tool_agent`, `memory_queries`, `library_agenda`;
- `provenance_*`, `product_origins`, `audit_journal`, `record_relations`, `level_record`;
- receipts, `product_answers` and `product_content` content, admission, lifecycle, coverage, Push and free play.

If a gate file must change, I stop, return the missing retained field and its call site, and file a second note before the edit.

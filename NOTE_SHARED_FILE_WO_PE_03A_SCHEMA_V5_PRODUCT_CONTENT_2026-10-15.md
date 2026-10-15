# Shared-file note: WO-PE-03A, schema v5 product content (2026-10-15)

**Filed by:** Claude, Alpha build seat, **before any shared edit**
**Base:** `ring9-unified` at `0779858`
**Interface:** `INTERFACE_WO_PE_03_CLAIMS_KEYS_GRADER_v2_2026-10-15`, §9
**Integration owner:** Claude, for every file below

## New files

- `inference/framework/product_content.py` (pure): the strict digest record, capture from the gate machine's active products, and per-level validation.
- `tests/test_world_model_v5_product_content.py`: the fail-first suite.
- `tests/fixtures/world_model_v4_frozen.json`: a v4 model sealed by `0779858`'s code, for the frozen reader.

## Edited shared files

| File | Planned change |
|---|---|
| `inference/framework/world_model_v2.py` | `SCHEMA` becomes v5; adds `V4_SCHEMA` and a frozen `validate_v4`; v5 validation calls `product_content.validate_level_content`; `read_world_model` dispatches v1-v5 |
| `inference/framework/library_census.py` | `compile_level` adds `product_content`, one line, through `provenance_hooks`. This is an accepted-residual file, so the growth is reported. |
| `inference/framework/provenance_hooks.py` | a `product_content(machine)` delegate |
| existing tests pinning `virelai-world-model-v4` | the version string only |
| `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | a new T0 `provenance-v5`; the new suite added to T1 `paper-evidence`; the new ids, none removed |

## Unchanged

- every gate module, `controller_turn.py`, `tool_agent.py`, `card_builder.py` and `memory_queries.py`;
- `library_view.py`, `world_description.py`, `world_report.py` and `library_agenda.py`;
- `provenance_chapter.py`, `answer_shapes.py`, `product_origins.py` and `audit_journal.py`;
- receipts, including the legacy `payload_sha256`, and `levels[].gaps`;
- Duck's card, digest and pages; action selection; claims, keys and grading.

If a gate or view file must change, a second note will be filed before that edit.

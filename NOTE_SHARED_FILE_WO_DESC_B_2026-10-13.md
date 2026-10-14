# Shared-file note, 2026-10-13 (WO-DESC-B, Duck's semantic world description and the world report)

**Filed by:** Claude, Alpha build seat, **before any shared edit**.
**Base:** `ring9-unified` at `66b91cb` (verified by Sol).
**Interface:** `INTERFACE_WO_DESC_B_v3_2026-10-13`.
**Integration owner:** Claude, for every file below.

| File | Function | Planned change |
|---|---|---|
| `inference/framework/effect_typing.py` (**new, pure**) | `classify_effect_channel` | Moved verbatim from `virelai_semantic/typing.py` |
| `inference/framework/virelai_semantic/typing.py` | module | Becomes a re-export of `effect_typing.classify_effect_channel`. Its callers (`mechanics.py`, `test_semantic_library_shadow.py`) are unchanged. |
| `inference/framework/world_description.py` (**new, pure**) | `describe_level_view`, `describe_world`, `validate_level_view`, `validate_view` | The semantic view: evidence-licensed folds, content-id patterns and questions, the census, laws, dossiers, and the validator |
| `inference/framework/world_report.py` (**new**) | `render_world_report`, `write_world_report` | The deterministic report, and its atomic writer. It refuses a live view, and on failure removes any stale report. |
| `inference/framework/library_view.py` | `library_digest`, `library_page`, `_call`, `PAGE_KINDS`, `HANDLES` | <ul><li>A `world` block inside the one 2,500 section.</li><li>Six page kinds and six filters.</li><li>Continuations keep every filter.</li></ul> The six accepted kinds behave as before. |
| `inference/agent/memory_queries.py` | `_library_query` | Forwards `transition`, `from_transition`, `to_transition`, `object`, `verb` and `include_folded` |
| `inference/framework/solver.py` | `_write_l2a_world_model` | After `write_canonical` succeeds, calls `world_report.write_world_report` with the sealed payload. A failure becomes observer warning `WORLD_REPORT_WRITE_FAILED`. |
| `tests/test_world_description.py` (new), `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | — | The fail-first suite; T0 `desc-b`; T1 `description` gains the new file; the snapshot gains its ids |

**Unchanged:**
- `world_model_v2.py` (schema v3 stays byte-identical);
- `descriptive_events.py`, `library_census.py` and `virelai_continuity.py`;
- every gate, the controller and the agenda;
- every accepted test.

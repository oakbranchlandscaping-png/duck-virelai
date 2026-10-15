# Shared-file note: WO-PE-02, the schema-v4 provenance chapter (2026-10-14)

**Filed by:** Claude, Alpha build seat, **before any shared edit**
**Base:** `ring9-unified` at `afe93c8`
**Interface:** `INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2_2026-10-14`
**Integration owner:** Claude, for every file below

## Files and planned changes

**New files:**
- **`inference/framework/provenance_chapter.py`** (neutral): the pure chapter compiler, its validator, reconciliation, typed references and the sidecar verifier.
- **`inference/framework/run_roster.py`**: the offline missing-model and run-status checker.

**Edited files:**
- **`inference/framework/audit_journal.py`**: adds `read_journal_bytes(data)`. `_read(path)` delegates to it, with behaviour unchanged.
- **`inference/framework/world_model_v2.py`**:
  - `SCHEMA` becomes v4, with `V3_SCHEMA` and a frozen `validate_v3`;
  - `seal()` attaches the default chapter and the level indexes;
  - provenance validation, and v4 in `read_world_model`.
- **`inference/framework/library_census.py`**: `compile_level` adds `record.reset_transition_ids` and `product_answers`. These are pure attribute reads; no gate method is called.
- **`inference/agent/provenance_capture.py`**: adds a pure `journal_path(state_path)`, which `journal()` now uses.
- **`inference/framework/solver.py`**:
  - `_write_l2a_world_model` attaches the H1 or H2 chapter;
  - new `_provenance_chapter`;
  - the session field `_l2a_writer_prefixes`;
  - `_play_one` records `WORLD_MODEL_NOT_WRITTEN`.
- **The six v3 pins:** `tests/test_descriptive_events.py` (3), `tests/test_wo_l2a_census_paths.py` (1) and `tests/test_world_description.py` (2). Only the version string changes.

**Tests and tiers:**
- the new suite `tests/test_world_model_v4_provenance.py`;
- `tests/tiers/test_tiers.toml`: the new T0 `provenance-v4`, added to T1 `paper-evidence`;
- `tests/tiers/T2_collected.txt`: the new ids, none removed.

## Unchanged

- every gate module, `controller_turn.py`, `tool_agent.py`, `memory_queries.py` and `virelai_gates.py`;
- `world_report.py`, `world_description.py`, `descriptive_events.py`, `library_view.py` and `library_agenda.py`;
- action selection, the scheduler, claims, keys and grading;
- the `journal_check` names and behaviour;
- every accepted test except the six version pins.

---

## Amendment 1 (2026-10-15), appended; the text above is unchanged

**Filed by:** Claude, Alpha build seat, at Sol's direction (`REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v1_2026-10-15` §5).

The note above was filed before any shared edit, and that remains true of it. Two things happened after it:

1. **Revision 1, after its first green tier pass:** `inference/framework/provenance_hooks.py` (**new**) was introduced to
   extract the new logic out of two shared files that sit above the Green file band. `solver.py` keeps a three-line
   `_provenance_chapter` delegate, its field and two call lines; `library_census.py` keeps one call. The extraction was
   proven by byte-identical artifacts. The note above did not list this file.
2. **Revision 2:** two more new files, both unshared: `inference/framework/answer_shapes.py` (pure: the accepted-answer
   shapes and strict hashing) and `inference/framework/product_origins.py` (the census-time provenance adapter,
   which reads gate state only).

**No gate file was edited** in either revision, so no second shared-file note was required. Every shared file this
slice touches is still the list above.

# Shared-file note, 2026-10-13 (WO-DESC-A, schema-v3 descriptive event ledger)

**Filed by:** Claude, Alpha build seat, **before any shared edit**.
**Integration owner:** Claude, for every file below.

## Amendment 1 (Sol's "proceed with amendments" review)

**Bases.**
- **Integration head:** `ring9-unified` at `5538816`. Every file below is byte-identical at `5538816` and `5fdac9a`, verified by sha against the device worktree:

  | File | sha |
  |---|---|
  | `world_model_v2.py` | `f36b83118189` |
  | `library_census.py` | `c344a9bc6e64` |
  | `virelai_continuity.py` | `6b2ec0b8e03d` |
  | `library_view.py` | `4f1ccffc9705` |
  | `test_wo_l2a_census_paths.py` | `26cad2fd95ae` |
  | `test_tiers.toml` | `2e8a11e76047` |
  | `T2_collected.txt` | `8d186165cbad` |

- **Test-infrastructure and runtime-behavior base:** `5fdac9a`.

**Interface:** `INTERFACE_WO_DESC_A_v2_2026-10-13`, which supersedes v1.

## Planned edits

| File | Function | Change |
|---|---|---|
| `inference/framework/descriptive_events.py` (**new, pure**) | `describe_level`, `explain`, `scene_at`, `restrict_description`, `validate_description` | The chapter, its explanations, the scene, H2 restriction and the validator. It imports no gate and mutates nothing. |
| `inference/framework/library_census.py` | `project_tracks` (+ `_track_id`, `_class_events`) | Also returns `windows` (life, cuts, lines), the objects it already builds. Track output is unchanged. Two helpers were extracted, so the function shrinks from 52 to 50 lines. |
| same | `_windows` (+ `entry_board_node`) | **Revision 1.** The entry board's node comes from the entry (0, or `after_transition`), never from the first recorded row. **Revision 2.** A row numbered at or before the entry is replayed onto the board but gets no cut; valid records are unaffected. |
| same | `_receipts` | v3 enrichment: a G2 `mask`, plus G3 witness `residue` and `witness_sha256`. |
| same | `compile_level` | One helper call attaches the description, with binding ends, `CLASS_CHANGED` gaps and the prefix `RECORD_MISMATCH` gap. The role-track and reset-born gap loops move into a helper, so the function shrinks. |
| same | `_apply_check` | One call truncates and restricts the description at H2. |
| `inference/framework/world_model_v2.py` | `SCHEMA`, `validate`, `validate_v2` (new), `read_world_model`, `_validate_level` | v3 rules. The v2 compatibility validator keeps the accepted v2 rules. The v1, v2 and v3 readers. |
| `tests/test_wo_l2a_census_paths.py` | `:68` | v2 → v3 (ruling 5). |
| `tests/test_world_model_v2.py` | `_model()` (+ `_witness`, `_description`) | **Added by this amendment.** The hand-built minimal model gains the minimal description and witness residue v3 requires, and its pointer-ego edit swaps in the matching description. No assertion changes. Unedited, 7 of its 13 tests fail under v3 (`witness receipt W-1 carries its residue and hash`). |
| `tests/test_library_view.py` | `_large` (+ `_light`) | **Added during the build.** The fabricated frozen levels become transition-free. Under v3 each would otherwise carry a 400-record ledger of transition ids they share. No assertion changes. |
| `tests/test_descriptive_events.py` (new), `tests/fixtures/world_model_v2_carry_v7_frozen.json` (new) | — | The fail-first suite, and the frozen v2 artifact produced by the accepted v2 code at `5538816` (sha `a74a4be9c4a1`). |
| `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | — | T0 `desc-a` and T1 `description` sets. The snapshot gains the new node ids. |

**Unchanged:** `library_view.py`, `virelai_continuity.py`, every gate module, the controller, the goldens, and every other test.

## Original filing (v1, base `5fdac9a`)

That filing added only `tests/test_descriptive_events.py` and recorded its failure. The planned edits it listed are superseded by the table above.

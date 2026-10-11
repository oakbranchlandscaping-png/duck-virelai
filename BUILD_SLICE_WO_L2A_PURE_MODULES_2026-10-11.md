# Build slice: WO-L2a pure modules (the v2 world-model schema and the level census)

**Date:** 2026-10-11 (work done 2026-10-10)
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `INTERFACE_WO_L2A_WORLD_MODEL_V2_v3`, approved by Sol for the Mac floor;
- `REVIEW_WO_L2_00_CENSUS_ARCHITECTURE`;
- `REVIEW_WO_L2A_INTERFACE`;
- Sol's two later reviews, relayed by the Director.

**Base:** `ring9-unified` @ `099aef9`. Its code equals `cd07716`.
**Shared files:** none. Only new files were added.

## 0 · What landed

| File | Content |
|---|---|
| `inference/framework/world_model_v2.py` | Schema `virelai-world-model-v2`: the validator (including the receipt checks), `seal`, `canonical_bytes`, the version-aware `read_world_model`, and `write_canonical`, the single writer. It uses a unique temporary sibling, then fsync and atomic replace, and never raises. |
| `inference/framework/library_census.py` | The read-only level census: tracks from level entry, scoped by level and life; certified EGO, COUNTER and LEVER, each resolved through receipts; typed gaps, including `INCONCLUSIVE`, `IDENTITY_UNRESOLVED` and `RECORD_MISMATCH`; `record_check`, including duplicate IDs; and a frozen census that requires an explicit `level_before`. |
| `tests/test_world_model_v2.py` | 12 contract tests |
| `tests/test_library_census.py` | 13 census tests on development records (k008, k013, the carry-v7 record fixture, the WO-L1a click world). Each asserts that the gate machine is byte-identical before and after the census. |
| `tests/test_wo_l2a_census_paths.py` | 1 premise test and 4 **strict** xfails, on production paths: the zero-action cancellation must write the model, and a legacy query must not overwrite it. Both fail on this tree, and that is the hooks slice's target. |

The fail-first evidence and the design are in interface notes v2 and v3.

## 1 · Verification

| Run | Result |
|---|---|
| Cloud, focused (the three new files) | 26 passed, 4 xfailed |
| Cloud, full (Python 3.12, 94 files, `--ignore=tests/test_physics_grammar_contract.py`) | 668 passed, 1 skipped, 4 xfailed, 0 failed |
| **Mac, focused** (Director, 2026-10-11; the main checkout's venv, Python 3.12) | **26 passed, 4 xfailed**, 14 warnings, in 45.24 s |
| **Mac floor** (Director, 2026-10-11; same command, `--ignore=tests/test_physics_grammar_contract.py`) | **668 passed, 1 skipped, 4 xfailed**, 14 warnings, in 992.45 s (0:16:32) |
| ruff on the new files | Clean |

The Mac and cloud counts are equal. The 14 warnings are matplotlib's pyparsing deprecations, from the venv, and are unrelated to this slice. The 668 is the 642 base (after the G3 lifecycle slice) plus 26 new passes.

## 2 · What it does not do

- No hook is wired. Nothing calls the census or the writer during a run yet. The 4 strict xfails stay until the hooks slice lands.
- No shared file is touched. `virelai_runtime.py` still writes the legacy v1 file on queries; that is the hooks slice.
- No INERT, force, driven reaction, scoped negative or Band 1; these are `NOT_BUILT` gaps.
- Validation proves that roles are consistent with the artifact's receipt index. It does not prove the index came from the gates (interface v3 §0).

## 3 · Next

1. **The Director:** commit this slice with explicit paths, then push.
2. **The hooks slice,** under interface v4 and `NOTE_SHARED_FILE_WO_L2A_HOOKS_2026-10-11`, which is filed before any hook edit:
   - deferred journal verification at H1;
   - reconciliation and the final write at H2;
   - the legacy writer separated;
   - the strict xfails removed.

— Claude, Alpha build seat (click line)

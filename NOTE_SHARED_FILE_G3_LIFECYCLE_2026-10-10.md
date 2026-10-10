# Shared-file note, 2026-10-10 (the G3 lifecycle slice)

**Filed by:** Claude, Alpha build seat (click line), before any edit. This follows ruling 9 and the harmony rules of `RULINGS_CONSOLIDATION_v2`.
**Slice:** the NAV G3 lifecycle failures. Ruling 23 assigned them to Sol; the Director reassigned this slice to Claude on 2026-10-10 under his review. Build record: `BUILD_SLICE_G3_HYBRID_LIFECYCLE_2026-10-10.md`.
**Base:** `ring9-unified` @ `dcb6ce5` (WO-L1a committed). Its `virelai_gates.py` sha256 is `78d8f419…`.

| File | Function | Change |
|---|---|---|
| `inference/framework/virelai_gates.py` | `_LeverTarget.record_outcome` (G3), the `SCOPED_NULL_RESPONSE` / counter-only branch | The negative response is still recorded. The row is closed only when no other channel is owed: a pointer null during the CLICK phase of a HYBRID world leaves the row `NO_RESPONSE_YET` for its NAV pass. That pass already ends in `_close_scoped_null_entities`. |
| same | `_LeverTarget._advance_accounted_terrain_rows` | NAV also steps past rows whose G3 work is already settled (`G3-CLOSED`, `G4-READY`), such as a lever the pointer phase witnessed. |
| same | `_LeverTarget._classify_terrain_rows` (review round 2) | When the terrain map closes a row, it also drops that row's `_bounded_ambiguities` record, as the reachability reopen and the mu return already do. |
| same | two new small methods on the same class | `_close_completed_null`, which the branch above now calls in place of its `journal.close` line (so `record_outcome` is net zero), and `_g3_settled` |
| `tests/test_g3_hybrid_lifecycle_replay.py` | new | Replay tests |
| `tests/fixtures/ring9_v2_k008_g3_lifecycle_record.json.gz`, `tests/fixtures/ring9_v2_k013_g3_lifecycle_record.json.gz` | new | Replay records built from the v2 rehearsal artifacts |
| `tools/record_g3_lifecycle_fixtures.py` | new | The builder for those two records |

**Untouched:**
- `lever_lifecycle.py`. The transition table is not widened.
- The terrain rule itself (which rows a terrain interaction closes), the inventory checker (`g3_inventory.py`), and the controller's inventory template.
- The lever-certification path (`LEVER_FOUND`, witnesses, G4 readiness).
- The reachability answer handler, the navigation planner, the terrain classifier, `record_replay.py`.
- The controller, every other gate, SUB-4 and the census.

The NAV-line functions changed above are Sol's. This note is the declaration; the Director reviews the diff before commit.

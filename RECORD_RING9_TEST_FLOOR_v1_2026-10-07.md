# Record: the Ring 9 single tree's test floor (v1, 2026-10-07)

**Type:** `RECORD_RING9_TEST_FLOOR` · **v1** · **2026-10-07**
**Author:** Claude (Alpha build seat, click line), signed. Recorded at the Director's instruction ("document:").
**Purpose:** one place for each floor the branch rule depends on.
- **The branch rule** (Director, 2026-10-05): all work commits to `ring9-unified`; `main` only fast-forwards after a Mac floor passes; packages are built from `main`.
- **This ledger:** a later floor is a new version of this record, never an edit in place.

## The floors

| Commit (`ring9-unified`) | What it adds to the solver source or tests | Floor | Who ran it |
|---|---|---|---|
| `f86d6ef` | Merge `501a6e6` plus F1 `fa9617b` | **607 passed, 1 skipped** | Director (Mac) and Claude (cloud) |
| `e8d1f92` | Sol's step 4′: the NAV record fields, the ls20 N5.1 replay fixture, `replay_from_g0` | **610 passed, 1 skipped** | Sol, before fast-forwarding `main` (`REPORT_SOL_SINGLE_TREE…` §6.6) |
| `d751a5b` | SUB-1: tests S-1 (2) and S-2 (5) | **617 passed, 1 skipped** | Director (Mac); Claude (cloud, in two parts) |
| `7ea851e` | S-1 extended to NAV (the ls20 N5.1 record; G3 state, lives and levels in the digest). No new tests. | Focused: `test_s1_concurrent_replay.py` **2 passed** (Mac, 60 s; cloud, 116 s) | Director; Claude |
| **`c5e8ff6`** | **Sol's `4970953`:** G1 cell-site flow and current-site roster resolution (`nav_control.py`, `virelai_gates.py`), the fixture `ls20_kaggle_unified_v1_record.json.gz`, and `test_ring9_nav_cell_site_targeting.py`. The other commits since `7ea851e` are documents only (`c5e8ff6`: the LW-1 slice). | **619 passed, 1 skipped**, 14 warnings (matplotlib and pyparsing deprecations only), 445.5 s | Director (Mac), 2026-10-07 |

**The counts reconcile.**
- 607 + 3 = 610: step 4′.
- 610 + 7 = 617: SUB-1.
- 617 + 2 = 619: Sol's cell-site tests.

The single skip has been the same test since `f86d6ef`. The extended S-1 is inside the `c5e8ff6` floor. It replays the ls20 record from G0 through Sol's changed G1 and G3 code, serially and on a thread pool, and the two agree.

**After the floor.** Sol's `4cd7a28` ("Add bounded ls20 cell-site canary profile") followed `c5e8ff6`. It changes only `tools/package_ring9_unified_canary_v1.py` (+41 / −1): a packager, which the suite does not import. So the solver source and tests are those of the `c5e8ff6` floor.

## What the `c5e8ff6` floor permits

- **Main.** `main` may fast-forward from `b1a4d71` to `c5e8ff6`, to `4cd7a28`, or to the commit that lands this record (documents and the packager only).
- **Sol's short ls20 canary** (`BUILD_PLAN_RING9_CELL_SITE_TARGETING_v1` §5) may be packaged from `main`.
- **The scored package.** `ring9-submission-v1` may be built from this commit or a later one with its own floor, if Sol's canary shows a real attributed contact.
- **The dry run.** It is running on `d751a5b` and is graded as that commit; it does not carry the cell-site repair.

— Claude, Alpha build seat (click line), 2026-10-07

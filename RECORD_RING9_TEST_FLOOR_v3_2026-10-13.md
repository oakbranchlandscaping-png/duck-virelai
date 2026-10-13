# Ring 9 test floor record v3

**Date:** 2026-10-13
**Accepted commit:** `5fdac9a`
**Supersedes for current work:** `RECORD_RING9_TEST_FLOOR_v2_2026-10-12.md`

WO-TEST-RHYTHM replaces the single 26-minute development floor with checked T0, T1, and T2 tiers. The runner refuses missing or duplicated manifest coverage, requires the T2 collection to match its exact snapshot, isolates parallel workers, reaps them on interruption, and accounts for every collected result exactly once. Replay checkpoints return a fresh deserialized machine to every consumer and bypass caching when production callables are patched.

## Accepted Mac results

| Tier | Command shape | Result | Wall time |
|---|---|---|---|
| Manifest | `tools/test_tiers.py --check` | T0 19 and 24; T1 143; T2 exactly 817 | 36 s including collection |
| T0 infrastructure | `T0 test-tiers` | 24 passed | 14.1 s |
| T0 directed G3 | `T0 g3-directed` | 19 passed | 56.8 s |
| T1 directed G3 | `T1 g3-directed --jobs 4` | 143 passed | 272.1 s |
| T2 acceptance | `T2 --jobs 4` | 816 passed, 1 skipped | 534.4 s |

The former accepted floor at `b635fb9` was 792 passed, 1 skipped in 1535.82 seconds. The new T2 adds 24 safety tests and completes in 8 minutes 54 seconds, a 65% wall-time reduction while increasing coverage. The golden remains `d9e08bd753af`. The separately held `tests/test_physics_grammar_contract.py` remains excluded because its runtime draft is unaccepted.

The two interruption tests use `ps` to find only their own worker command lines. A managed sandbox that blocks process inspection will fail those tests with a permission error; the accepted host run granted local process-inspection permission and passed both.

## Standard use

- Claude runs the active slice's T0 after edits and T1 before parking.
- Sol runs T0 when checking a correction and T1 during source review.
- The Director runs T2 once after Sol accepts a slice and before commit, packaging, release, or a shared-infrastructure change.
- On this four-core host, T1 and T2 use four workers. T0 stays serial.

No accepted test may be removed, weakened, skipped, xfailed, hidden from the exact snapshot, or made order-dependent to improve time.

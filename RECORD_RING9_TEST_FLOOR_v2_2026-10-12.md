# Ring 9 test floor record v2

**Date:** 2026-10-12
**Scope:** accepted local `ring9-unified` commits after `472aa32`
**Supersedes for current work:** `RECORD_RING9_TEST_FLOOR_v1_2026-10-07.md`

| Commit | Slice | Accepted Mac result |
|---|---|---|
| `472aa32` | v2 model census and H1/H2 hooks | 683 passed, 1 skipped |
| `125d4d0` | bounded library live view | 707 passed, 1 skipped |
| `db8a657` | directed G3 CLICK | 755 passed, 1 skipped |
| `4a18c4d` | HYBRID CLICK controller path | 758 passed, 1 skipped |
| `ceeeabd` | reset continuity and fail-closed record handling | 777 passed, 1 skipped |
| `b635fb9` | directed G3 NAV selection and pursuit | 792 passed, 1 skipped in 1535.82 s |

At `b635fb9`, the focused G3 NAV set passed 89 tests in 283 seconds. The full floor excludes `tests/test_physics_grammar_contract.py`, which belongs to uncommitted draft grammar work and is not part of the accepted source.

The growing wall time is now a build constraint. The next infrastructure slice must define:

- **T0 change-focused:** expected under 90 seconds;
- **T1 slice floor:** expected under 5 minutes, target near 3 minutes;
- **T2 full acceptance:** once after review and before packaging or release; goal under 15 minutes.

The optimization may cache immutable replay setup or shard independent tests. It may not remove, weaken, skip, or xfail accepted tests, alter goldens, or change runtime behavior.

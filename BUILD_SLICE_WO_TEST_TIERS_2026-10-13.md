# Build slice: WO-1, test-runtime infrastructure (tiered floors, shared replay checkpoints)

**Date:** 2026-10-13
**Author:** Claude (Alpha build seat), signed
**For:** Sol's review. **Not committed.** Work order 2 (WO-G4-ROSTER-DOSSIER) waits until this slice is accepted and committed.
**Governs:** `NOTE_SHARED_FILE_WO_TEST_TIERS_2026-10-13`, filed with the diagnosis before any shared test-support edit.
**Base:** `b635fb9` (`ring9-unified`). The cloud tree equals the device worktree, apart from the separately held physics-grammar files, which exist only on the device.

**Scope.**
- **No production file changed.** No golden changed: `g3_no_choice_golden.json` is still `d9e08bd753af`, identical byte for byte.
- No test was removed, skipped, xfailed, merged or weakened (§5).

## 1 · Read-only timing report (before)

The diagnosis and design are in the note. The full tables are in `floor_timing_tables.md`: the 50 slowest tests with setup, call and teardown; time by file; instrumented call counts; replays per record; every checkpoint built more than once, with its call sites.

**The run:** one serial cloud process from `b635fb9`, with a scratch measurement plugin (not checked in). Result: 792 passed, 1 skipped in 1,915 s. The Mac baseline is 1,535.82 s; cloud runs about 1.25× slower.

**Where the time goes:**

| Item | Result |
|---|---|
| Record replays | **950 s** (~50%): 119 replays of 49 distinct checkpoints |
| Redundant replay (rebuilds of the same checkpoint) | **619 s** |
| Production agent turns (`ToolAgent.analyze`) | 385 s over 1,236 turns |
| Repeated compilation (overlapping the rows above) | `compile_world_model` 110 calls / 104 s; `live_model` 79 calls / 70 s; `binding_gate_payload` 1,771 calls / 46 s; `gate_agenda` 25,285 calls / 8.5 s |
| Setup phases | 384 s, mostly module fixtures that replay |

**Replays of the development records:**

| Record | Replays | Seconds |
|---|---|---|
| k008 | 15 | 179 |
| k013 | 12 | 177 |
| carry-v7 | 16 | 38 |

**Biggest repeats:**
- `ft09_kaggle_memory_v1`, full: built 19 times, 15 of them by the function fixture `start_g4b`.
- k013 at cut 400: 7 builds across 6 files.
- `ft09_kaggle_v2`, full: 7 builds.
- `vc33_kaggle_exit_v1` with measure: 11 builds.
- `vc33_kaggle_carry_v4` at cut 26: 7 builds.

**Not every repeat is redundant.** Some replays are the test's subject:
- the no-choice golden traces;
- the concurrency and determinism replays;
- the r15 fidelity tests;
- a replay of a record rebuilt from artifacts;
- replays run under a deliberately corrupting monkeypatch (the reset-continuity tests).

The last case is a real hazard: a cache keyed by record name and cut would hand those tests the uncorrupted machine.

## 2 · What was built

**`tests/replay_checkpoints.py`: the checkpoint layer.**
- `checkpoint(path, max_steps=, answer_source=, measure=)` returns a freshly unpickled `ReplayResult` on every call. `checkpoint_bytes` returns the immutable pickled bytes behind it.
- **Key:** the resolved path, the sha256 of the record file's bytes, `max_steps`, `answer_source` and `measure`.
- **Patch guard:** while any loaded `inference.*` attribute differs from the object first seen, a call replays fresh and caches nothing.
  - Covered: module namespace callables, imported ones included, and the attributes of every class each module defines.
  - **Baseline:** taken when the layer is imported and again when collection finishes (`tests/conftest.py`, one hook), so before any test can patch.
- **Build rules:** an entry is stored only after the replay returns and pickles. A raised build stores nothing.
- **Scope:** in-process only, with no disk cache.
- **`_replayed`** in `test_g3_directed_click.py` (previously an `lru_cache` keyed by name and cut) now calls the layer, with the same signature for its importers.

**Fixture-precondition replays moved onto the layer.**
- **Changed:** 26 replay call sites in 15 test files. Each `replay(load_record(X), …)` became `checkpoint(X, …)` with the same options; each file gained an import line.
  - `replay()` defaults to `measure=True`, so those sites pass `measure=True` explicitly.
- **Unchanged:** every assertion, fixture scope and test name.
- **Not moved** (the replay is the subject):
  - `g3_no_choice_trace`;
  - `test_s1_concurrent_replay`;
  - `test_memory_m0` and `test_memory_m1:74/:131`;
  - `test_r9_r15_replay_fidelity`;
  - `test_g4b_relations:224/:335`;
  - `test_r9_r20_level_entry:62` (a spy);
  - `test_library_census:228` (a hooked replay);
  - `test_g3_ledger_frame_sync._replay_corrupted`.

**The tier manifest and runner.**
- **`tests/tiers/test_tiers.toml`** (`virelai-test-tiers-v1`) names every tier and says who runs it when.
- **`tests/tiers/T2_collected.txt`:** 808 node ids. These are the 793 at `b635fb9` plus the 15 new safety tests.
- **`tests/tiers/file_weights.json`:** measured seconds per file, used for shard balance only.
- **`tools/test_tiers.py {T0,T1,T2} [SET] [--jobs N] [--timing] [--results FILE] [--check]`:**
  - Every entry is checked by collection first. It fails (status 4) if a named test or file, or any T2 snapshot node, no longer collects.
  - It prints the tier, the set, the test count, the outcome counts and the elapsed time.
  - **`--jobs 1`:** one pytest process; the runner returns its own status.
  - **`--jobs N`:** N independent pytest processes over whole files, each with its own `--basetemp` and built-in junit report. The runner then requires exactly one result for every collected test, and returns the first non-zero status (1 if the results do not match the collection).
  - **`--timing`:** lists the 30 slowest tests across processes.
  - No plugins and no network.
- **The complete floor** is the single command `python tools/test_tiers.py T2`. The raw pytest command still works unchanged.

**When each tier runs:**

| Tier | Who runs it | When |
|---|---|---|
| T0 | Claude | After every edit, and before parking |
| T0 | Sol | To check a correction |
| T1 | Claude | Before parking every revision |
| T1 | Sol | While reviewing |
| T1 | The Director | On the copied files |
| T2 | The Director | Once after Sol accepts a slice and before its commit; at packaging and release checkpoints; whenever shared infrastructure changes (test support, the replay path, `conftest`) |

During review revisions, T0 and T1 only.

## 3 · The tiers (the exact lists are in the manifest)

**T0 `test-tiers` (15 tests):** `tests/test_replay_checkpoints.py` (10) and `tests/test_test_tiers.py` (5).

**T0 `g3-directed` (19 tests).** The last slice's fail-first tests plus its nearest guards:

| Source | Tests |
|---|---|
| NAV | genuine choice; bound pursuit on the true post-reset board; explicit vs implicit head; body contact owed; reachability obligation; new-life stale; object-change stale; **both resumed-step-starts-fresh tests**; controller-only |
| CLICK | 2a, 2b, 2c (×3 parameters, plus stale and obligation); 8 (explicit head) |
| Golden | `test_0` for carry-v7 |

**T1 `g3-directed` (143 tests):**

| Coverage | File or node |
|---|---|
| Directed CLICK (the agenda, the card and the three-record no-choice golden) | `test_g3_directed_click.py` |
| Directed NAV | `test_g3_directed_nav.py` |
| HYBRID CLICK | `test_g3_hybrid_click_pass.py` |
| Reset continuity | `test_g3_ledger_frame_sync.py` |
| Lifecycle replay | `test_g3_hybrid_lifecycle_replay.py` |
| The G3 scheduler | `test_g3_scheduler.py` |
| The G3 certificate | `test_g3_checkpoint.py` |
| The census | `test_library_census.py` |
| The live library and digest | `test_library_view.py` |
| Selection persistence | the persistence-tier test, `test_r9_r16_life_record::test_d4…` |
| Event logging | the live handoff test, `test_memory_m2::test_with_the_live_g3_choice_handoff…` |
| The golden's own full traced replay | `test_replay_checkpoints::test_8…` |

**T2:** the whole of `tests/` except `tests/test_physics_grammar_contract.py`, as today. **808 tests:** 793 as before, plus 15 new.

## 4 · Before and after (cloud seconds; the Mac is about 0.80×)

| Tier | Before (`b635fb9`, one process) | After, one process | After, 2 processes (this cloud box has 2 CPUs) |
|---|---|---|---|
| T0 `g3-directed` (19) | 72.0 | 68.0 | — |
| T0 `test-tiers` (15) | — (new) | 15.1 | — |
| T1 `g3-directed` | 703.7 (142 tests) | 571.1 (143) | **330.7 / 336.8 / 334.1 / 337.9** (four runs) |
| T2 | 1,915 (793) | 1,641.0 (808) | **935.1 and 964.1** |

**Projected for the Mac** (×0.80):

| Run | Projected |
|---|---|
| T1, one process | about 457 s |
| T1, 2 processes | about 270 s (4:30) |
| T2, one process | about 1,310 s (21:50) |
| T2, 2 processes | about 760 s (12:40) |
| T2, 4 processes | expected around 6-8 minutes; please report the actual time |

Results with 4 processes depend on the Mac's core count. The largest single file is `test_g3_directed_click.py`, about 200 s cloud. It bounds a T1 shard, so T1 at `--jobs 4` should land near three minutes.

**Honest limits:**
- **Serial reuse removes about 14% of the floor.** The rest of the serial floor is agent turns, the golden and determinism replays, and the patched replays, all of which must stay fresh.
- **The 15-minute goal therefore depends on `--jobs`.** Projected: met at 2 processes (12:40) and comfortably at 4. Not met serially (21:50).
- **T1's five-minute target is met at `--jobs 2` or more,** not serially.
- **T0 `g3-directed` is already under 90 s.**

## 5 · Required fail-first and safety tests

| # | Hazard | Test | Fail-first evidence |
|---|---|---|---|
| 1 | Two consumers get isolated machines | `test_1_two_consumers…` | Fails on the naive cache: the same object is returned |
| 2 | Mutating one copy does not reach the next | `test_2_mutating_one_copy…` | Fails on the naive cache: the mutation leaked |
| 3 | Different cuts never collide | `test_3_different_cuts…` | Fails on the naive cache |
| 4 | Same name, different contents never collide (same path rewritten included) | `test_4_records_with_the_same_name…` | Fails on the naive cache: `2 == 1` |
| 5 | Replay options are part of the key | `test_5_replay_options…` | Fails on the naive cache: measured vs unmeasured |
| 6 | A failed build is not cached | `test_6_a_failed_build…` | Fails on the naive cache, which reserved the slot |
| 7 | A missing manifest test fails the run | `test_7_a_manifest_naming_a_missing_test_fails`; `test_7_the_t2_snapshot_fails…` | On `b635fb9` the runner does not exist (collection error) |
| 8 | The no-choice golden still compares its own full traced replay | `test_8_the_no_choice_golden…` | **Fails** against a trace that reads a checkpoint (`failfirst_cached_golden_trace.txt`) |
| — | A patched replay neither reads nor seeds the cache | `test_a_patched_replay_bypasses…` | Fails on the naive cache |
| 9 | The G3 slice floor twice, in fresh processes | runs A and B | **Identical outcome maps** (`t1_runA.json` == `t1_runB.json`, 143 passed each). T2 with 1 and 2 processes also gave identical outcome maps over all 808 tests. |
| 10 | The stale-NAV-pursuit tests | — | Against revision 1's faulty `g3_selection.py` (`febd46f7c961`), moved onto the checkpoint layer: **2 failed**. On `b635fb9` (`43b8c70fcb51`): **2 passed** (`hazard10_rev1.txt`, `hazard10_b635fb9.txt`). |
| — | The runner returns pytest's failure status and accounts for every test, including across processes and parameters | `test_the_runner_returns…`; `test_parallel_processes…` | — |

**The naive cache** is a scratch module: keyed by file name and cut, returning the shared object, reserving its slot before building. Against it, 8 of the 10 checkpoint tests fail (`failfirst_naive_cache.txt`). The 2 that pass are the golden guard and the no-disk-cache check, which do not depend on the cache.

**One defect found in my own tests and fixed before the final runs.**
- **What failed:** in the first T2 runs, `test_6` failed in both the 1- and 2-process runs. Its key (carry at cut 7) had already been built by an earlier test, so the planted failure was never reached. That is an order dependence.
- **The fix:** the test now uses a record copied into its own `tmp_path`, a key no other test can build. The file's tests were then run each alone, and in reverse order after cache-warming tests, and passed both ways.
- **The record:** both earlier T2 runs (`t2_jobs1.txt`, `t2_jobs2.txt`) show it. In both, all 793 original tests passed.

**No test removed, skipped or xfailed:**
- All 793 node ids at `b635fb9` still collect (`T2_collected_at_b635fb9.txt` is a subset of `T2_collected.txt`).
- The final T2 is **807 passed, 1 skipped**: the original 792 passed and 1 skipped, plus the 15 new tests passed.
- Across the 15 edited files, the 78 changed lines contain no `assert`, `skip`, `xfail`, `pytest.mark` or `def test`.
- Suite-wide counts of `skip`, `xfail` and asserts are unchanged, except the new files' asserts.

**Golden unchanged:** `tests/fixtures/g3_no_choice_golden.json` is `d9e08bd753af` before and after. `test_0` passed for all three records in every T1 and T2 run.

## 6 · Files

**New:**

| File | sha256[:12] |
|---|---|
| `tests/conftest.py` | `97aafe17a779` |
| `tests/replay_checkpoints.py` | `3b355ccc90d8` |
| `tests/test_replay_checkpoints.py` | `69f3ea0ec5ab` |
| `tests/test_test_tiers.py` | `53879a9f866c` |
| `tests/tiers/test_tiers.toml` | `2e8a11e76047` |
| `tests/tiers/T2_collected.txt` | `a6067cbc86e6` |
| `tests/tiers/file_weights.json` | `c2cb1b944f72` |
| `tools/test_tiers.py` | `1372a77fdc70` |

**Edited** (replay call sites only):

| File | sha256[:12] |
|---|---|
| `test_g3_directed_click.py` | `df9122cb2ac7` |
| `test_g3_hybrid_lifecycle_replay.py` | `654c57ecc1e2` |
| `test_g4b_relations.py` | `a15a64ce169d` |
| `test_library_census.py` | `5ee0ad48e5ce` |
| `test_library_view.py` | `e0e7658e96c2` |
| `test_memory_m1.py` | `48407a8d5682` |
| `test_memory_m3.py` | `65621c3fd97e` |
| `test_r9_r14_live_fixes.py` | `dacaad967246` |
| `test_r9_r16_life_record.py` | `0fb87dd2e3c7` |
| `test_r9_r17_level_freeze.py` | `007ec38964bc` |
| `test_r9_r18_carry.py` | `7ea289932a07` |
| `test_r9_r20_level_entry.py` | `d6e36d002ac5` |
| `test_r9_r21_g3_contradicted.py` | `30ff35e8fb4c` |
| `test_r9_r22_lever_typing.py` | `8df7bdc121c2` |
| `test_wo_l2a_hooks.py` | `9c4d963d1d23` |

- **Exact diff:** `exact_diff.patch` (edits, plus the new files in full).
- **Run outputs:** `runs/`.

## Revision 2: Sol's ruling on revision 1 (2026-10-13)

**Status:**
- **Accepted:** the core replay-cache design.
- **Required:** close the two disclosed gaps (duplicate coverage and worker reaping), and reject `--jobs` below 1.
- **Not run in this revision:** T2. It waits for Sol's acceptance. **Nothing committed.**

**Changed in revision 2:**

| File | Revision 1 | Revision 2 |
|---|---|---|
| `tools/test_tiers.py` | `1372a77fdc70` | `ff9300b4af4d` |
| `tests/test_test_tiers.py` | `53879a9f866c` | `376b9b0b1668` |
| `tests/tiers/T2_collected.txt` | `a6067cbc86e6` | `8d186165cbad` |

- `T2_collected.txt` was rewritten intentionally with `--write-snapshot`, adding the 9 new test ids. It now holds 817 rows, none duplicated: the 793 at `b635fb9` plus the 24 tier-safety tests.
- **Every other file is unchanged from revision 1**, including the replay layer, `conftest`, the 15 edited test files and the manifest.
- The golden is unchanged (`d9e08bd753af`).
- The exact delta is `revision2_delta.patch`; the full slice diff is `exact_diff.patch`.

### R2.1 · What changed

**Duplicate coverage is rejected.**
- `check_coverage` runs on every T0 and T1 set. It fails with status 4 for a selector listed twice, and for any collected test covered by two selectors: a file plus a node from it, a parametrized function plus one of its cases, or a directory plus a file in it.
- **Messages name the tier and set, the node and every covering selector.** For example: `T0 probe: duplicate coverage: <node> is covered by 2 selectors: ['…/probe_cases.py', '…/probe_cases.py::test_passes']`.

**The T2 snapshot is exact.** It fails on a duplicated row, on a snapshot test that no longer collects, and on a collected test missing from the snapshot. A new test needs an intentional `--write-snapshot`.
- **Live check:** before the rewrite, `--check` refused the tree with the 9 new revision-2 tests listed as "not in the snapshot".

**Workers are reaped on every interruption.**
- Each worker runs in its own session, so only the runner stops it.
- SIGINT and SIGTERM are handled from before collection. An interruption or internal exception leads to the same cleanup:
  1. Signals are ignored for the rest of the cleanup.
  2. Each live worker's process group gets SIGTERM.
  3. After a 5 s grace period, SIGKILL; then every worker is reaped.
  4. Only then is the scratch folder removed.
- **An interrupted run returns 130 (SIGINT) or 143 (SIGTERM)** and publishes no result map. `--results` is written whole, through a temporary file and an atomic rename, and only by a completed run.
- `--jobs 0` and negative counts are usage errors (status 2). The runner prints each worker's pid.

### R2.2 · Fail-first on revision 1

Recorded in `runs_r2/failfirst_r2_on_rev1.txt` and `failfirst_r2_reap_on_rev1.txt`. **9 of 9 failed on revision 1:**

| Test | Failure on revision 1 |
|---|---|
| A repeated literal selector | `DID NOT RAISE`; the tier ran |
| Overlapping file and node selectors (file case, parametrized case) | `DID NOT RAISE`; the tier ran |
| A duplicated T2 snapshot row | `DID NOT RAISE` |
| A collected test absent from the T2 snapshot | `DID NOT RAISE` |
| `--jobs 0` and `--jobs -2` | `DID NOT RAISE SystemExit`; the tier ran |
| SIGTERM and SIGINT sent to the runner only | **"a worker outlived the runner"**: both sleeping workers kept running after the runner exited. The test's own cleanup then killed them. |

**How the interruption test works:**
- It starts a 2-worker tier over two 120 s sleeping probe tests.
- It finds the workers by the runner's private scratch path (`ps -ww`, so it works on Linux and macOS), then signals only the runner.
- It then requires: no worker alive, status `128 + signal`, the scratch parent left empty, and no results file.

### R2.3 · Results (cloud)

| Run | Result |
|---|---|
| `--check` | T0 `g3-directed` 19, T0 `test-tiers` 24, T1 `g3-directed` 143; **T2 817, exactly the snapshot** |
| T0 `test-tiers` | **24 passed in 23.3 s** |
| T0 `g3-directed` | **19 passed in 102.7 s** |
| T1 `g3-directed`, 2 workers | **143 passed in 496.4 s** |

**These timings come from a slower cloud host than revision 1's.** The container restarted between revisions, and every test now runs about 1.4 to 1.5 times slower; the code did not slow down. A same-host comparison shows it:

| Run, this host, back to back | Seconds |
|---|---|
| The T0 `g3-directed` node set on `b635fb9` | 94.7 |
| Revision 2's T0 `g3-directed` | 96.1 |

The same two runs took 72.0 and 68.0 s on revision 1's host.
- **The Mac measurement is the one that counts.** On revision 1's host scale, projected Mac times are about 55 s for T0 `g3-directed`, and about 270 s for T1 with 2 workers.
- T2 is not rerun, as ruled.

## Director-side Mac acceptance, 2026-10-13

Sol reviewed the frozen revision-2 archive, whose SHA-256 is
`dd6adf69441e4562c17e214c58fb5633e33a6b2b86362e99efa3681cf0bb79ca`, and copied its files into the
`ring9-unified` worktree. The copied runner, runner tests, T2 snapshot, and unchanged golden matched the
reported hashes.

| Gate | Mac result |
|---|---|
| Manifest check | T0 `g3-directed` 19; T0 `test-tiers` 24; T1 `g3-directed` 143; T2 exactly 817 |
| T0 `test-tiers` | 24 passed in 14.1 s |
| T0 `g3-directed` | 19 passed in 56.8 s |
| T1 `g3-directed`, 2 workers | 143 passed in 301.4 s |
| T1 `g3-directed`, 4 workers | 143 passed in 272.1 s |
| T2, 4 workers | 816 passed, 1 skipped in 534.4 s |

The first sandboxed T0 infrastructure run passed 22 tests and failed only the two process-reaping tests because
the managed sandbox refused their `ps` call. The same frozen code passed all 24 when run with local
process-inspection permission. This is an execution-environment restriction, not a solver or runner defect.

The accepted standard on this four-core host is four workers for T1 and T2. T0 remains serial. The T1 target is
met at 4:32.1 and the T2 target at 8:54.4, with the exact 817-node snapshot and unchanged golden. Sol accepts
WO-TEST-RHYTHM revision 2 for commit. A theoretical signal-arrival window between spawning a worker and adding
it to the runner's tracking list remains a future hardening concern; it did not appear in fail-first, cloud, or
Mac interruption evidence and does not block this slice.

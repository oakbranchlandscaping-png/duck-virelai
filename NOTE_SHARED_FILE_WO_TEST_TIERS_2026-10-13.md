# Shared-file note and design, 2026-10-13 (WO-1 test-runtime infrastructure)

**Filed by:** Claude, Alpha build seat. This note was filed **before any edit to shared test support**. Up to this point only read-only measurement had run.
**Authority:** Sol's two work orders, relayed by the Director. This note covers work order 1 only. Work order 2 (WO-G4-ROSTER-DOSSIER) begins after this slice is accepted and committed.
**Base:** `b635fb9` (`ring9-unified`, local; its HEAD was read from the worktree's git refs).
- The cloud tree equals the device worktree file for file across `inference/`, `tests/`, `tools/`, `virelai_golden/`, the fixtures and `pyproject.toml`.
- Exceptions: the separately held `physics_grammar*.py`, `win_referee.py` and `test_physics_grammar_contract.py` exist only on the device.

**Integration owner:** Claude, for every file below.

## 1 · Diagnosis (read-only; the tables are in `floor_timing_tables.md`)

**The measurement run:**
- One serial pytest process from `b635fb9`, with a scratch measurement plugin that is never checked in.
- The plugin wraps `load_record`, `replay`, the census, live-library, card and agenda compilers, `ToolAgent.analyze` and `CyberneticGateMachine.__init__`, and attributes every call to the running test.
- **Result:** 792 passed, 1 skipped in 1,915 s on the cloud. The Mac baseline is 1,535.82 s. The cloud is about 1.25× slower, so the proportions below transfer.

**Where the time goes:**

| Component | Seconds | Share / count | Notes |
|---|---|---|---|
| Record replays (`replay()`, outer calls) | **950** | ~50% of the floor | 119 replays of **49 distinct checkpoints** |
| `ToolAgent.analyze` | 385 | 1,236 turns | The HybridRun / Ft09World / offline-agent tests drive the production agent step by step. Nothing to cache; only parallelism helps. |
| `compile_world_model` | 104 | 110 calls | Overlaps the two rows above |
| `live_model` | 70 | 79 calls | Overlaps the two rows above |
| `binding_gate_payload` | 46 | 1,771 calls | Overlaps the two rows above |
| `gate_agenda` | 8.5 | 25,285 calls | Overlaps the two rows above |
| Setup phases | 384 | — | Mostly module fixtures that replay |

- **Redundant replay time:** every build after the first of the same `(record content, cut, answer source, measure)` accounts for **619 s**.
- **Most expensive repeats:**
  - **`ft09_kaggle_memory_v1`, full: 19 builds.** 15 of them come from `test_g4b_relations.start_g4b()`, a function fixture.
  - **k013 at cut 400: 7 builds** across 6 files.
  - **`ft09_kaggle_v2`, full: 7 builds.**
  - **`vc33_kaggle_exit_v1` with measure: 11 builds** across the r15/r16/r17/r18 files.
  - **`ft09_kaggle_exit_v1` with measure: 5 builds.**
  - **`vc33_kaggle_carry_v4` at cut 26: 7 builds** (`_drive_level_two`).
  - **`carry_v7`, full: 6 builds.**

**Replays per development record:**

| Record | Replays | Seconds |
|---|---|---|
| k008 | 15 | 179 |
| k013 | 12 | 177 |
| carry-v7 | 16 | 38 |

**Not every repeat is redundant.** Several are the test's subject and must stay fresh replays:
- the no-choice golden trace (`g3_no_choice_trace`, which wraps `record_outcome` during the replay);
- `test_s1_concurrent_replay` (concurrent equals serial);
- the second replay in `test_memory_m1` (determinism);
- the r15 replay-fidelity tests;
- the G4-B replay of a record rebuilt from artifacts;
- and the reset-continuity tests that replay **under a deliberately corrupting monkeypatch** (`test_g3_ledger_frame_sync._replay_corrupted`).

That last case is a real hazard. A cache keyed only by record name and cut would hand those tests the uncorrupted machine.

**What is not a cost:** `load_record` is 1.7 s for 208 loads, and gate-machine construction is negligible.

**Consequence:**
- Safe reuse of fixture replays can remove roughly 350-400 s of the serial floor.
- That alone leaves a serial floor of about 20 minutes on the Mac.
- The agent-driven tests (385 s) and the irreducible golden and determinism replays can only be overlapped, not removed. Getting below 15 minutes therefore also needs **process-level parallelism** that is not a pytest plugin: independent pytest processes over whole files, with every collected test accounted for.

## 2 · Design

### 2.1 · Checkpoint layer: `tests/replay_checkpoints.py` (new, test support)

`checkpoint(path, *, max_steps=None, answer_source="view", measure=False)` returns a **freshly deserialized** `ReplayResult` on every call. `checkpoint_bytes(...)` returns the immutable pickled bytes.

**Cache key:**
- the resolved record path;
- the **sha256 of the record file's bytes**, so a different content under the same name is a different key;
- `max_steps`, `answer_source` and `measure`;
- the **code fingerprint** described below.

**Production-code fingerprint.**
- **The problem it solves:** a test that monkeypatches production behaviour before replaying, as `_replay_corrupted` does, must never be served a machine built by unpatched code, and must never seed the cache with a patched one.
- **How:**
  1. The layer records the identity of every function and class attribute in the loaded `inference.*` modules the first time it sees them, holding strong references so identities cannot be reused.
  2. On every call it compares the current attributes with those references.
  3. If any differs, the call **bypasses the cache**: it builds a fresh replay, returns it and stores nothing.

**Build rules:**
- The cache is populated only after `replay()` returns **and** `pickle.dumps` succeeds.
- A raised build stores nothing, and the next call retries.

**Scope:**
- In-process session reuse only.
- **No disk cache in this slice**, so no stale disk cache can exist.
- No ordering dependence: whichever test asks first builds; every later caller gets an equal, independent copy.

**`_replayed` in `test_g3_directed_click.py`.** Today it is an `lru_cache` of pickled bytes keyed only by `(name, cut)`. It becomes a thin call into `checkpoint_bytes` with the same signature, so its importers (the NAV, HYBRID and reset-continuity tests) are unchanged.

### 2.2 · Call sites moved onto the checkpoint layer

Only fixture-precondition replays move: a replay that builds the state a test then inspects or drives. Each site is listed in the build report.

| File | Sites |
|---|---|
| `test_g3_directed_click.py` | `_replayed` |
| `test_g3_hybrid_lifecycle_replay.py` | `_drive`, and the k008 cut at `:156` |
| `test_library_census.py` | `_cut`, carry |
| `test_library_view.py` | k013 400, carry, k013 300 |
| `test_g4b_relations.py` | `start_g4b`, the cut 79 and the full v1 replay at `:224` |
| `test_r9_r14_live_fixes.py` | `:50` |
| `test_r9_r22_lever_typing.py` | `_drive_level_two`'s level-1 replay; every record at `:139` |
| `test_r9_r16_life_record.py`, `test_r9_r17_level_freeze.py`, `test_r9_r18_carry.py` | exit-record replays |
| `test_r9_r20_level_entry.py` | — |
| `test_r9_r21_g3_contradicted.py` | — |
| `test_memory_m0.py` | fixture |
| `test_memory_m1.py` | the two module fixtures |
| `test_memory_m3.py` | `:202` |
| `test_wo_l2a_hooks.py` | `_carry` |

Every assertion is unchanged. Each moved site's semantics are a replay of the same record with the same options, delivered as an independent copy.

**Not moved** (the replay is the subject):
- `g3_no_choice_trace.py`;
- `test_s1_concurrent_replay.py`;
- `test_memory_m1.py:74` (`answer_source="card"`) and `:131` (the determinism replay);
- `test_r9_r15_replay_fidelity.py`;
- `test_g4b_relations.py:335` (a record rebuilt from artifacts);
- `test_g3_ledger_frame_sync._replay_corrupted`.

**Module-scoped fixtures** keep their existing scope and sharing; only their replay comes from the layer.

### 2.3 · Tier manifest and runner (new)

- **`tests/tiers/test_tiers.toml`** (`schema = "virelai-test-tiers-v1"`) is the one checked-in manifest:
  - **T0** sets, named per slice. Each lists exact node ids: a slice's fail-first tests plus its nearest guards.
  - **T1** sets, named per subsystem. Each lists whole files and node ids.
  - **T2** is the whole `tests/` tree, minus the separately held `tests/test_physics_grammar_contract.py`, exactly as today.
- **`tests/tiers/T2_collected.txt`** is the T2 collection, by node id. It is the proof that no test disappears.
- **`tests/tiers/file_weights.json`** holds measured seconds per file. They are used only to balance parallel shards, never to select tests.
- **`tools/test_tiers.py`** is the runner, with the interface `python tools/test_tiers.py {T0,T1,T2} [SET] [--jobs N] [--timing] [--check]`.
  - It checks every manifest entry by collection and **fails if a named test, file or T2 node disappears**.
  - It prints the tier, the set, the test count, the elapsed time and the outcome counts.
  - **`--jobs 1`** runs one pytest process and returns its exit status.
  - **`--jobs N`** runs N independent pytest processes over whole files, each with its own `--basetemp` and `--junitxml`. Files sharing expensive checkpoints are kept in one shard, so in-process reuse still pays. The runner then verifies that **every collected node id has exactly one result** and returns the first non-zero pytest status (1 if the result set does not match the collection).
  - **`--timing`** lists the slowest tests from the junit timings across shards.
  - It uses only pytest's built-in junit writer: no plugins and no network.
- **The complete floor stays one reproducible command:** `python tools/test_tiers.py T2`. The existing raw pytest command keeps working unchanged.

### 2.4 · Safety tests (new: `tests/test_replay_checkpoints.py`, `tests/test_test_tiers.py`)

These cover work-order hazards 1-8:

| # | Hazard |
|---|---|
| 1 | Isolated consumers |
| 2 | Mutation does not leak |
| 3 | Cuts do not collide |
| 4 | Same-name, different-content records do not collide |
| 5 | Replay options are in the key |
| 6 | A failed build is not cached |
| 7 | A missing manifest test fails the runner |
| 8 | The no-choice golden still runs its own full traced replay and compares the full trace |

- **The patch-bypass guard** is also tested, on the real corrupting-monkeypatch pattern.
- **Fail-first:** the hazard tests run against a deliberately naive reference cache (keyed by name and cut, returning shared objects, caching failures), and must fail there before the real layer is written.
- **Hazards 9-10** are demonstrated by runs:
  - **9:** T1 twice in fresh processes, compared by outcome map.
  - **10:** the stale-NAV-pursuit tests against the faulty `g3_selection.py` (revision 1, `febd46f7c961`), and then against `b635fb9`.

## 3 · Shared files this slice edits

**Test support only: no production file and no golden.**
- **New:** `tests/replay_checkpoints.py`, `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt`, `tests/tiers/file_weights.json`, `tools/test_tiers.py`, `tests/test_replay_checkpoints.py`, `tests/test_test_tiers.py`.
- **Edited** (a replay call routed through the layer; assertions untouched): the test files listed in §2.2.

## Amendment 1, 2026-10-13 (filed after the edits, in the same working session)

§2.2 listed three sites that were **not** moved after a closer read. All three stay direct `replay()` calls:

| Site | Why it stays direct |
|---|---|
| `test_memory_m0.py` fixture | It is the replay harness's own measurement test; the replay is its subject. |
| `test_g4b_relations.py:224` | `test_f3` asserts that the record replays the live restudy, a fidelity claim. |
| `test_library_view.py:82` | k013 at 300 is built once, so moving it gains nothing. |

**Also kept direct** (consistent with §2.2's rule):
- `test_r9_r20_level_entry.py:62`, which replays under a spy;
- `test_library_census.py:228`, which replays under a hook.

**The final moved set:** 26 call sites in 15 files, listed in the build report and the exact diff.

**`tests/conftest.py`** (one `pytest_collection_finish` hook) baselines the patch guard after collection.

## Amendment 2, 2026-10-13 (Sol's ruling on revision 1; revision 2)

**The duplicate-coverage and interruption gaps disclosed in revision 1 are closed in the same files.** No new file is added. Changed:
- `tools/test_tiers.py`
- `tests/test_test_tiers.py` (new tests, plus one changed assertion: `check_t2_snapshot` now returns `None`)
- `tests/tiers/T2_collected.txt`, intentionally rewritten with `--write-snapshot` to add the 9 new test ids

### 1 · Duplicate coverage is rejected

`check_coverage` runs after collection for every T0 and T1 set. Status 4 for:
- **a selector listed more than once:** `T0 probe: the selector '…' is listed 2 times`;
- **any collected test covered by more than one selector:** a file plus a node from it, a parametrized function plus one of its cases, or a directory plus a file in it. The message reads: `T0 probe: duplicate coverage: <node> is covered by 2 selectors: [...]`.

Every message names the tier and set, the duplicated node and the selectors covering it.

### 2 · The T2 snapshot is exact

`check_t2_snapshot` rejects three cases:
- a duplicated row;
- a snapshot test that no longer collects;
- a collected test absent from the snapshot. A new test therefore needs an intentional `python tools/test_tiers.py --write-snapshot`.

The message is `T2 (T2_collected.txt): …`, listing the nodes.

### 3 · Workers are reaped on every interruption

**The cleanup boundary:**
- Each worker starts in its own session (`start_new_session=True`), so only the runner can stop it.
- The runner installs SIGINT and SIGTERM handlers **before collection**.
- An interruption, or any internal exception, leads to the same cleanup: signals are ignored for the bounded cleanup; every live worker's process group gets SIGTERM; after a 5 s grace period, SIGKILL; then every worker is reaped.
- The scratch folder is removed only after that.

**What an interrupted run returns:**
- `128 + signal`: 130 for SIGINT, 143 for SIGTERM;
- a stderr notice;
- **no result map.** `--results` is published only by a completed run, written whole through a temporary file and an atomic rename.

`--jobs` below 1 is a usage error (status 2). The runner also prints each worker's pid.

### Fail-first on revision 1

All 9 new tests fail on revision 1 (`failfirst_r2_on_rev1.txt`, `failfirst_r2_reap_on_rev1.txt`):

| New tests | Failure on revision 1 |
|---|---|
| The four duplicate and snapshot tests (5 cases) | `DID NOT RAISE` |
| The two `--jobs` cases | `DID NOT RAISE SystemExit`; the tier ran |
| Both interruption cases | **"a worker outlived the runner"**: the workers kept sleeping after the runner died. The test then killed them. |

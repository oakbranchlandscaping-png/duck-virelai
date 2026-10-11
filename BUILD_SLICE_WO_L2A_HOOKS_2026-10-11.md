# Build slice: WO-L2a hooks (H1 freeze, H2 reconcile and write, legacy writer separated)

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `INTERFACE_WO_L2A_WORLD_MODEL_V2_v4_2026-10-11`, §0a (deferred verification) and §6 (the hooks);
- Sol's hooks ruling, relayed by the Director;
- `NOTE_SHARED_FILE_WO_L2A_HOOKS_2026-10-11`, filed before any edit.

**Base:** `ring9-unified` @ `7df657e` (the pure-module slice). The Director committed it on 2026-10-11: 14 files, 2,230 insertions, verified with `git show --stat`. Its push was pending when this slice was built.

Before the slice, the device worktree's nine files this slice touches had the same hashes as the cloud base, so the slice sits on committed ground.

## 0 · What landed

| File | Change |
|---|---|
| `inference/framework/virelai_gates.py` (shared) | **H1.** `__init__` gets `level_censuses`, a GAME-tier list. `_advance_level` makes one call, before `freeze_level`: `self.level_censuses.append(freeze_census_or_failure(self, outcome))`. No harness state enters the machine. |
| `inference/framework/life_record.py` (shared) | `"level_censuses": GAME` |
| `inference/framework/solver.py` (shared) | Entry capture after a successful `observe_initial`. Interim write after each analyzer turn in which H1 froze a level. **H2** final write between `_finish_if_needed()` and `_close_game_observer()`. Each never raises; a failure is an observer warning. |
| `inference/framework/virelai_runtime.py` (shared) | `_canonical_world_model` → `_observer_world_model`, in memory, with all 7 callers updated. A file is written only under `VIRELAI_LEGACY_WORLD_MODEL_FILE=1`, and then only to `world_model_legacy_v1.json`. |
| `inference/framework/library_census.py` | `compile_level` is always PENDING and NOT_ACCOUNTED. New functions: `freeze_level_census`, `freeze_census_or_failure` (which reads `level_before` from the boundary), `assign_mismatches`, `reconcile`. `compile_world_model` reconciles only when final, and keeps census failures in `manifest.census_failures`. |
| `inference/framework/world_model_v2.py` | Journal-check rules. PENDING requires NOT_ACCOUNTED and `JOURNAL_CHECK_PENDING`. CHECKED requires `ok` to agree with the IDs; a failed check requires a RECORD_MISMATCH gap (source `record_check`) that names the same IDs. |
| `tests/test_wo_l2a_hooks.py` | New, 10 tests (below) |
| `tests/test_wo_l2a_census_paths.py` | The 4 strict-xfail marks are removed |
| `tests/test_world_model_v2.py` | Fixture record is CHECKED. New: `test_only_a_checked_journal_may_be_accounted` |

### The solver's H2

The final write does five things:
1. builds `ExecutionRecord` from the captured entry and `game_run.history`;
2. takes the frozen levels from `analyzer._gate_machine.level_censuses`;
3. compiles the open level, unless an advance froze its census but never rebuilt;
4. reconciles every level against the whole history, once;
5. writes through `write_canonical`.

`persist_reason` is set as follows:

| Situation | `persist_reason` |
|---|---|
| Run crashed | `CRASH` |
| Run cancelled | `CANCELLED` |
| Action or time budget reached | `BUDGET_STOP` |
| Anything else | `RUN_END` |
| Interim write | `LEVEL_ADVANCE` |

A game whose initial board was never observed gets no census, only a `WORLD_MODEL_NOT_OBSERVED` event (interface v2 §5).

The original exception and `solver_note` are never masked.

## 1 · Fail-first evidence

| Test | Before the solver edits | After |
|---|---|---|
| `test_r9_r16_life_record.py -k d4` | Failed: `['level_censuses'] == []` | Passed |
| `test_a_crash_after_a_level_advance_still_writes_the_reconciled_model` | `FileNotFoundError: .../virelai/fixture_p0/world_model.json` | Passed |
| `test_the_interim_write_precedes_the_final_one` | `[] == [('LEVEL_ADVANCE', 'PENDING'), ('RUN_END', 'RECONCILED')]` | Passed |
| `test_no_observed_board_means_no_census_only_an_event` | `[] == ['WORLD_MODEL_NOT_OBSERVED']` | Passed |
| The 4 strict xfails in `test_wo_l2a_census_paths.py` | XFAIL | `XPASS(strict)` once the hooks landed, so the marks were removed; they now pass |

The other seven hooks tests pin the census behaviour on the carry-v7 development record (ruling 10). It has one level change at transition 26, and the replay stops at 27.

| Test | What it pins |
|---|---|
| H1 freeze | Level 1 frozen at the boundary with its check PENDING and NOT_ACCOUNTED, LEVERs E0004 and E0005 |
| Matching history | Both levels CHECKED; level 1 ACCOUNTED; H1's own copy left PENDING |
| **Mismatch on the frozen level** (×2) | Renaming t7 removes E0004 (its witness) and keeps E0005; renaming t9 does the reverse. The `record_check` gap names the ID, and the open level is unaffected. |
| `assign_mismatches` | Synthetic spans, including an ID between levels going to the next span |
| Interim model | Validates, and claims nothing for a pending level |
| Census failure | Recorded; the level still advances; the failed level's IDs fall to the last level |

## 2 · Verification

| Run | Result |
|---|---|
| Cloud, focused: hooks, census paths, census, schema, life record and native observer tests | 57 passed |
| **Cloud, full** (Python 3.12, 95 files; the cloud tree has no `test_physics_grammar_contract.py`) | **683 passed, 1 skipped, 0 xfailed, 0 failed** |
| **Mac, focused** (Director, 2026-10-11; the main checkout's venv, Python 3.12; the cloud's six files plus `test_g3_run_outcome.py`) | **62 passed**, 14 warnings, in 40.64 s |
| **Mac floor** (Director, 2026-10-11; `tests --ignore=tests/test_physics_grammar_contract.py`) | **683 passed, 1 skipped**, 14 warnings, in 528.54 s (0:08:48) |
| ruff | The new and changed census files are clean. The four shared files show the same 3 pre-existing findings as the base (F401, F402, F601), and none are new. |

The Mac and cloud counts are equal, and no xfail remains. The 14 warnings are matplotlib's pyparsing deprecations from the venv, unrelated to this slice. The Mac worktree's untracked files from other seats (`physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `test_physics_grammar_contract.py`, `SPEC_PHYSICS_GRAMMAR_v3`, the root `WO_L2A_CENSUS_INTERFACE_NOTE_v1`, `kaggle/`) are not part of this slice and are not staged.

How the count adds up: 683 = 668 (the floor at `7df657e`) + 4 (the former xfails) + 10 (hooks) + 1 (schema).

## 3 · Ratchet (non-blank, non-comment lines)

| Function | Before | After |
|---|---|---|
| `_HarnessGameSession.play` | 114 | **87**: +2 hook calls, +1 call to the helper below, −30 moved out |
| `_HarnessGameSession._observe_virelai_initial` | 9 | 11 |
| `CyberneticGateMachine._advance_level` | 8 | 10: one import, one call |
| `CyberneticGateMachine.__init__` | 17 | 18 |
| `VirelaiRuntime.__init__` | 71 | 73: the opt-in path |
| New solver helpers | — | `_write_l2a_world_model` 27, `_l2a_persist_reason` 12, `_write_l2a_interim_if_advanced` 6, `_capture_l2a_entry` 5, `_l2a_enabled` 2, `_history_action_name` 3 |

**Compensation.** The G3 run-outcome block in `play`'s `finally` moved, unchanged, into `_record_open_g3_outcome(run)` (31 lines with its `def`). `test_g3_run_outcome.py` passes, 5 tests. This is a move inside the declared `play`, not a new site.

## 4 · Findings for Sol

1. **Architectural: executed actions outside the gate record.**
   - **What happens.** Gate rows exist only for gate probes and system resets. Actions Duck executes after the gates close (free play) are executed but never recorded.
   - **Effect at H2.** They are `missing`, so the last level becomes NOT_ACCOUNTED with a RECORD_MISMATCH. Roles survive, because a missing ID does not drop a role, and the observation tier stops at the last gate row.
   - **Example.** The carry-v7 record executed 165 actions and the machine recorded 26.
   - **Why it matters.** This is honest, but it does not distinguish "unrecorded free play" from a corrupted record.
   - **Ruling needed.** Should free play be a separate gap reason or accounting state? Or should it be recorded as rows? I have not decided it in code.
2. **Scope: the v2 model is written in `gated` mode only.**
   - The `observe`, `tool` and `controller` modes no longer write any `world_model.json` by default, because the legacy writer is now opt-in. They still answer queries in memory.
   - **Ruling needed.** Confirm this, or name the modes that should get a v2 census.
3. **Code level: no `CONTROLLED_STOP` reason yet.** A controlled stop ends as `RUN_END`, because the solver has no flag that separates it from a planned stop at finalization. It is a small follow-up if wanted.

## 5 · What it does not do

- No cross-check of the projection against the runtime's `continuity_tracks.json` (next).
- No INERT, force, driven reaction, scoped negative or Band 1. These stay `NOT_BUILT` gaps.
- F-1a (the NAV contact-null stale bound) and F-3 (NAV CPU) are untouched.

## 6 · Next

1. **The Director:** commit this slice with explicit paths. Then push `ring9-unified`: on 2026-10-11 the worktree's remote-tracking ref still read `cd07716`, so `099aef9`, `7df657e` and this slice are not yet recorded as pushed. Then fast-forward `main` (local `main` is at `cd07716`).
2. **Sol:** rule on findings 1 and 2.

— Claude, Alpha build seat (click line)

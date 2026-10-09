# Build slice SUB-3: free play reports its outcome to Duck; ring9-submission-v2

**Date:** 2026-10-09
**Author:** Claude (Alpha build seat, click line), signed
**Director:** SUB-3 approved as explained on 2026-10-09, with option B for the cap ("lets do B": raise the action cap to 1,000 in v2).
**Governs:**
- the rehearsal of `ring9-submission-v1` (defect R-1, below);
- `RULINGS_CONSOLIDATION_v2_2026-10-08` (ruling 13 sets the timing; the noted item asks for at least 20 minutes of margin);
- `NOTE_SHARED_FILE_2026-10-09.md` (filed first).

**Base:** `ring9-unified` @ `b805950`. Its runtime source is SUB-2 `a2200c2`, with a floor of 627 passed, 1 skipped. I confirmed the base before building:
- All 185 committed Python files under `inference/` and `tests/` are byte-identical to the build tree.
- The packager is byte-identical too.
- The Director's worktree also holds four untracked files from another seat (`physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `test_physics_grammar_contract.py`). They are not part of this slice and are not touched.

**Altitude:** code-level. **Timing:** ruling 13 says no runtime code is touched before v1 is submitted, so this slice is committed only after that submission.

## 0 · In one paragraph

In the v1 rehearsal, all 685 free-play actions ran and were recorded, yet Duck was told each one had failed:
- The play gate's event had no `outcome`, while every other gate's event has one.
- `_apply_step_result` reads `gate_event["outcome"]` (`tool_agent.py:2373`) and raised `KeyError`.
- The sandbox host replaced that error with its generic "action failed in sandbox host." (`python_tool_sandbox.py:585-591`).

Duck retried spent tokens, looped, and sometimes ended its game early. 23 of the 36 games played reached free play, which is where ruling D-3 sends them.

SUB-3 makes the play gate's event carry its outcome, as every gate's does. The host now logs any error it hides, so the next one of this kind shows in the first run that meets it. Package v2 also raises the action cap to 1,000 and trims the slice to 2,550 s.

## 1 · Changes

| File | Change | Lines |
|---|---|---|
| `inference/framework/play_gate.py` | `PlayTarget.record_outcome` returns its event plus `"outcome"`. The new module function `_event_outcome` compacts it as G1 does (`compact_probe_outcome` for evidence-schema outcomes). The adapter's `_events` list and its snapshot stay as they were, so the persisted state does not grow with play. The evidence id is unchanged. | +9 −1 |
| `inference/agent/python_tool_sandbox.py` | The new module function `_hidden_error(where, exc, shown)` logs `sandbox host hid <where>: <type>: <message> at <file>:<line>` and returns the text Duck saw before. Both `except` arms that hide errors (action and `virelai` query) call it. Contract errors still pass through to Duck unchanged. | +15 −3 |
| `tests/test_sub3_free_play_outcome.py` | New: 3 tests (§2) | +98 |
| `tools/package_ring9_submission_v2.py` | New, from the v1 packager. Settings: `ring9-submission-v2`, cap 1,000, slice 2,550 s. Checks three SUB-3 markers. Revised criteria (§4). | +39 −9 against v1 |

## 2 · Tests: fail first, then pass

All three run the real tool path. My SUB-2 test stubbed out `_apply_step_result`, which is why it could not see this defect.

| Test | Against the base | With SUB-3 |
|---|---|---|
| `test_a_free_play_action_reports_its_outcome_to_duck`: a level rests in play, then Duck acts with its token through `_run_python_tool`. The environment is called once; the result shows `executed` and the event's evidence id; the turn counts as executed. | **fails** (the rehearsal's exact message) | passes |
| `test_the_free_play_event_keeps_the_gate_event_contract`: the event has `evidence_id` and `outcome`; the outcome is the compact copy; the snapshot's events stay lean. | **fails** (no `outcome`) | passes |
| `test_the_sandbox_host_logs_an_error_it_hides_from_duck`: an action handler raising `KeyError('outcome')` and a query handler raising `ValueError`. Duck's text is unchanged; the log names the type, message and raising file. | **fails** (nothing logged) | passes |

## 3 · Verification (cloud)

| Check | Result |
|---|---|
| The 3 SUB-3 tests | Failed against the base; pass with the fix |
| Full suite on the SUB-3 tree, Python 3.12 | **630 passed, 1 skipped** (627 plus 3), all 89 test files |
| ruff on the changed files and the packager | clean |
| **Director's Mac floor** (worktree, 2026-10-09; the uncommitted `test_physics_grammar_contract.py` of another seat ignored) | **630 passed, 1 skipped**, 14 warnings (matplotlib and pyparsing deprecations only), 872 s |
| Trial v2 package, built from the 419f4fd export plus the SUB-3 files under a placeholder stamp | Builds: 230 source files; secret guard clean; SUB-2 and SUB-3 markers present |
| Mount simulation, 5 of 5 | The rehearsal branch in zip, nested and direct layouts, and the rerun branch in zip and nested. Every branch: `source manifest verified (230 files)`, 110 unique ids, concurrency 10, 1,000 actions, 2,550 s, gated mode, Qwen3.6. The soft end is launch + 2 h for the rehearsal and notebook start + 8 h 35 min for the rerun. The pickled solver has 1,000, 2,550.0, and `rest_on_controlled_stop` True. |

The final package is built from the Director's export of the SUB-3 commit, after the Mac floor passes, and is verified 9/9 against that export.

## 4 · Package v2 settings and criteria

**The cap: 400 → 1,000.** RHAE scores each level from the actions spent on that level, and a level that is never cleared scores 0. So actions spent on an unfinished level cost nothing, and the cap only limits upside. In the rehearsal, lp85 and r11l hit 400 with 12 to 25 minutes of their slice unused.

**The slice: 2,700 → 2,550 s.** In the worst case, all 110 games use their full slice.
- That is 11 waves of 10, each wave 2,550 + 45 s (the observed overrun), about 28,545 s.
- Play can start after 843 s of setup (the rehearsal's measurement), and the soft end is at 30,900 s. That leaves 30,057 s, so the margin is about 1,512 s (25 minutes).
- That meets the 20 minutes asked for, against v1's 8. If the Rules tab shows a 12-hour limit, the slice can grow in a later version.

**Disk: a new risk from the cap.** In the rehearsal, output ran at about 0.8 MB per action: k005 (lp85, 400 actions) wrote 314 MB, and 36 games wrote 2.8 GB. At 1,000 actions, a controller-heavy world could write about 800 MB per game. So the rehearsal now reports the rerun's projected use of the working directory (criterion W).

**Criteria in `RUN.md`:**
- the v1 set;
- **C-4, reworded:** the rehearsal cannot fit 110 games, so it now checks that games still playing at the soft end are cancelled cleanly and that the benchmark closes within 5 minutes;
- **D-1 to D-3,** carried forward from v1;
- **S-3:** no executed free-play action is reported as failed; free-play turns are ledgered as executed; every `sandbox host hid` line is counted by type and site;
- **W:** output size per world, and the projected disk use of the 110-game rerun.

## 5 · What SUB-3 does not change

- Gates, the controller, Duck's prompts, the NAV branch, recording and evidence ids.
- The adapter's persisted snapshot.
- Ruling 6 (G1's explanation before the first action). It is a separate slice, scheduled around Sol's open work before the 27–30 Oct freeze. The package that carries it will be v3 or later, since v2 is now this slice.

## 6 · Next

1. The Director confirms v1 is submitted (ruling 13).
2. The Director copies the files into the worktree, runs the Mac floor (expected 630 passed, 1 skipped), commits on `ring9-unified` with explicit paths, pushes, and fast-forwards `main`.
3. The Director exports the commit. Claude builds `ring9-submission-v2` from it, then verifies it 9/9 and with the mount simulation.
4. The Director uploads the dataset and pushes the kernel. The save run is the rehearsal (about 2.3 GPU-hours), graded against §4. Then the Director submits it with the day's second slot.

— Claude, Alpha build seat (click line), 2026-10-09

## Mac floor log (Director's terminal, 2026-10-09)

| Step | Result |
|---|---|
| Copied the four files from `runs/_cowork_xfer/sub3/` into the tree and `tools/` | No output. All four were checked against the cloud copies' sha256 when they were delivered. |
| `pytest -q --ignore=tests/test_physics_grammar_contract.py` from the worktree's `ARC3-Inference/`, with the main checkout's venv | **630 passed, 1 skipped**, 871.99 s. This equals the cloud result: 627 + 3 SUB-3 tests. |

**Next:** commit on `ring9-unified` with explicit paths, push, fast-forward `main`, export the commit, then build and verify `ring9-submission-v2` from that export.


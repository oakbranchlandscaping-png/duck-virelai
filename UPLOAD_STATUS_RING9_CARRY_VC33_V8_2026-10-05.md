# Upload status: ring9-carry-vc33-v8 (R9-R24 G4 controller-first, pinned image)

**Date:** 2026-10-05
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v8.py`
**Slice:** `BUILD_SLICE_R9_R24_G4_CONTROLLER_FIRST_2026-10-04.md` (branch `r9-r20-level-entry`, commit `c9b246b`)
**Ruling:** `RULING_G4_CONTROLLER_FIRST_v2_2026-10-04.md` (Director-ruled)
**Landing record:** `RECORD_R9_R24_LANDING_v1_2026-10-05.md`
**Directive:** `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04.md` (expected GPU time stated below)

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v8` (231 files; source 224) |
| Package manifest sha256 | `9f6cf50602ef0b34b2c512f69a5a173611d7378b89305aa76fd4348938b42773` |
| Source manifest sha256 | `fea19878771e09708d1dffc66ccd72dae1a0ea12a3f02ef5fbf50d40da0c7b8c` |
| Source commit | `c9b246be8a38334d2670276d1601c186695976ec` (`ec8554d` + R9-R24), from the Director's `git archive` export (sha256 `e5c59078…a7b115`, 314 files) |
| Image | Pinned as in v4–v7: `gcr.io/kaggle-private-byod/python@sha256:37c64f7d…` (Python 3.12) |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v8` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v8` |
| Expected GPU time | **About 3.3 GPU-hours, the full window.** Setup takes about 14 minutes, then the 3-hour behaviour window. v7 also used the full window, stuck in G4-B/G4-C. v8 should leave G4 quickly, but normal play runs until the action or time budget ends the run. It no longer stops after G4-C. So expect the full window unless all 7 levels are won. |

## What changed from v7

Only the source changed.

**Source files.**
- **Changed:** `virelai_gates.py`, `g4b_gate.py`, `g4c_gate.py`, `g4_relations.py`, `controller_executor.py`, `controller_turn.py`, `life_record.py`, `level_model.py`.
- **New:** `level_record.py`, `record_relations.py`, `play_gate.py`.
- The tests and the v7 fixture are not shipped: the packager excludes `tests/`.

**Notebook and metadata.**
- The notebook differs from v7's only in its dataset name and its run label.
- Kernel metadata differs only in the dataset, the notebook id and the title.

**Unchanged from v7:**
- the setup command;
- the image pin;
- the wheelhouse and model datasets;
- the world (vc33);
- the budgets: 200 actions and 10,800 seconds.

**Preregistered criteria, new:**

**I14 · G4-B from the record (D18, D19).**
- On any level that reaches G4-B, the controller writes the `LEVER_RELATIONS_FROM_RECORD` answer itself, with no Duck turn. The product is `certified_by: RECORD`.
- No G4-B card row shows `state_now: UNRECORDED`.

**I15 · Duck's G4 budget (D20, D21).**
- On each level, Duck takes at most 3 turns at G4-B or G4-C.
- G4-C ends COMPLETE or UNRESOLVED. A contradiction after the budget is spent does not reopen G4-B.
- Reported: the time from G4-B opening to `PLAY-NORMAL`. On v7 that stretch took about 163 minutes.

**I16 · Normal play (D22, R-8).**
- When a level's gates rest, the level passes to `PLAY-NORMAL`.
- Every play transition is recorded with receipt `FREE_PLAY`. A level won in play is frozen with `win.receipt: FREE_PLAY`. A new level opens its own ladder and budget.
- A refused repeat carries the "Blocked by the harness, not the game" label.
- The run ends by its action or time budget, not by a planned stop.
- Reported: play actions, play turns, blocked repeats, and whether level 3 was won, and how (GATED or FREE_PLAY).

**Superseded criterion.** Criterion E's "planned_stop: ladder through G4-C" no longer applies. Under R9-R24, a closed ladder hands the level to normal play.

**Marker guards:**
- The packager refuses a source that lacks any of 9 R9-R24 markers.
- The R9-R20 to R9-R23 guards still apply.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (`c9b246b`) | **8/8**, with 0 differences from the commit export |
| Export against the tested cloud R9-R24 tree | Identical |
| Mount simulation, three layouts | **All pass**: 200 actions, 10,800 s, gated, `vrfai/Qwen3.6-27B-FP8` |
| Pre-flight `check_g4_controller_first_from_record.py` on the **packaged** source, with the v7 record (run on a copy) | G4-B is answered by the CONTROLLER and certified from the record. All 7 lever states are named (S2–S7). The next gate is G4-C, and Duck's budget is unused (0 of 3). Exit 0 |
| Tamper test: one byte appended to `play_gate.py` | Refused (3 FAIL) |
| Request pre-flight (T10) | 33,158 tokens worst case, against a 65,536-token window |
| Bytecode in the package | None |
| Suite at `c9b246b` | Cloud and Mac (worktree): 535 passed, 1 skipped |

## What the run should show

**Setup.** As in v7, with `source manifest verified (224 files)`. That is 3 more than v7, from the 3 new modules.

**Levels 1 and 2.** As in v7.
- Both were won during G4-A, so G4-B never opens on them.
- The controller is deterministic until Duck acts, so any difference before Duck's own first action comes from the environment (I6).

**Level 3.**
- G3 and G4-A run as in v7, through t140.
- G4-B is then answered by the controller, with no Duck turn (I14).
- G4-C takes at most 3 Duck turns (I15).
- `PLAY-NORMAL` follows (I16).

**Hypotheses, not findings:**
- G4 on level 3 should take minutes. v7 took hours.
- Play begins with about 55 actions left in the run (v7 reached G4-B at t140). The level's move counter is about 64 per life, and v7's study used one life up (GAME_OVER at t144).
- Whether play wins level 3 is open. Nothing in the ladder aims at the win yet (friction F3).

## Director's steps

1. I'll put the package, the packager and this record in place on your Mac. Then you run `verify_kaggle_package.py` there.
2. Commit the packager and this record on `main`, staging explicit paths only. Never stage `kaggle/`.
3. Run `kaggle datasets create -p kaggle/ring9-carry-vc33-v8/source-dataset -r skip`, then check `status` until it says `ready`.
4. Run `kaggle kernels push -p kaggle/ring9-carry-vc33-v8/kernel`.

— Claude, Alpha build seat, 2026-10-05

## Upload log (2026-10-05, Director's terminal)

| Step | Result |
|---|---|
| Mac verify (`main`'s verifier, `--source-export runs/_cowork_xfer/r9r24/export_c9b246b`) | **9/9**: source manifest 224 files, package manifest 231 files, `src.zip` 215 files, 0 diffs against the commit export |
| Commit on `main` | `d807d88`: the packager and this record, explicit paths, `kaggle/` not staged |
| `kaggle datasets create -p kaggle/ring9-carry-vc33-v8/source-dataset -r skip` | 12 files uploaded, the same set as v7 |
| Sizes | `src.zip` 922 KB (v7: 910 KB; the difference is the 3 new modules), `source-manifest.json` 27 KB, `checkpoint-preflight.json` 11 KB, `setup_commands.json` 10 KB, the rest small |
| Visibility | private |
| Kaggle at upload end | "being created" |

**CLI notes, both expected, as in v7:**
- "Skipping folder: src". The source travels as `src.zip`, which the notebook checks against the manifest before importing anything.
- "outdated kaggle version (installed 2.0.0, latest 2.2.2)". No upgrade is needed.

**Next:**
1. `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v8` until it says `ready`.
2. `kaggle kernels push -p kaggle/ring9-carry-vc33-v8/kernel`

**What the log should show if v8 works:**
- **Setup:** `source manifest verified (224 files)`. That is 3 more than v7, from the 3 new modules.
- **Levels 1 and 2:** as in v7 (I6).
- **Level 3, G4-B (I14):** at about t140, G4-B is answered by the controller, `LEVER_RELATIONS_FROM_RECORD`, `certified_by: RECORD`, with no Duck turn. No card row reads `state_now: UNRECORDED`.
- **Level 3, G4-C (I15):** at most 3 Duck turns, then COMPLETE or UNRESOLVED. Report the time from G4-B opening to `PLAY-NORMAL` (v7: about 163 minutes).
- **Play (I16):** `PLAY-NORMAL` follows, every play transition receipted `FREE_PLAY`, any refused repeat labelled "Blocked by the harness, not the game". Report play actions, play turns, blocked repeats, and whether level 3 was won and how.
- **End (I11, I16):** the run ends by its action budget (200) or its time budget (10,800 s), not by a planned stop. Compare the run's end time with the notebook's.

# Upload status: ring9-carry-vc33-v7 (R9-R23 mu bucket, pinned image)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v7.py`
**Slice:** `BUILD_SLICE_R9_R23_MU_BUCKET_2026-10-03.md`, on branch `r9-r20-level-entry` at commit `ec8554d`
**Ruling:** `RULING_MU_BUCKET_v1_2026-10-03.md` (ruled by the Director)
**Landing record:** `RECORD_R9_R23_LANDING_v1_2026-10-03.md`
**Directive:** `DIRECTIVE_COMPETITION_ENDGAME_v1_2026-10-03.md` (3-hour window kept; expected GPU time below, per D-5)

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v7` (228 files; source 221) |
| Package manifest sha256 | `03980ef7fadc0fc550d9c9779308bfba961455179278c944b0aa6a77f6482a76` |
| Source manifest sha256 | `51a28c206601332f03a18f6872167c0f81370659ca14dea500516ad24a49734c` |
| Source commit | `ec8554db276aa0c416d79e998718df8815d640c4` (`8656839` + R9-R23), from the Director's `git archive` export (export sha256 `2e6f2b1a…88603aa`, 309 files) |
| Image | Pinned as in v4–v6: `gcr.io/kaggle-private-byod/python@sha256:37c64f7d…` (Python 3.12) |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v7` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v7` |
| Expected GPU time | **At most about 3.3 GPU-hours:** setup plus model load, then a 3-hour behaviour window. v6 used about 0.36 GPU-hours, because the A2 watchdog ended it at t110. v7 should run longer, because level 3 now proceeds to the lever study. The 200-action budget may end it before the time budget does. |

## What changed from v6

Only the source changed.

**Source files.**
- Changed: `virelai_gates.py`, `controller_executor.py`, `level_model.py`, `life_record.py`, `controller_turn.py`.
- New: `mu_bucket.py`, `mu_return.py`, `g3_inventory.py`.
- The new test and its fixture are not shipped: the packager excludes `tests/`, as before.

**Notebook and metadata.**
- The notebook differs from v6's only in its dataset name and its run label.
- Kernel metadata differs only in the dataset, the notebook id and the title.

**Unchanged from v6:**
- the setup command;
- the image pin;
- the wheelhouse and model datasets;
- the world (vc33);
- the budgets: 200 actions and 10,800 seconds.

**Preregistered criteria, new:**

**I12, the G3 partial close (D12, D13 and D17).** This applies on any level where G3 has certified at least one lever and only bounded ambiguities remain.
- Each ambiguity is filed into the mu bucket, together with the board it was tried on and the owner of the clicked cell.
- G3 closes with the controller's `LEVER_INVENTORY`, with `closure: PARTIAL` and the mu objects in `ambiguous_entities`.
- No Duck turn is spent on the inventory.
- G4-A then queues every certified lever.
- Expected first on level 3.

**I13, the mu return (D14 to D16).** The controller returns to mu only when the ladder is stuck, and then only for entries whose masked board has changed.
- An object that occupies no cell is settled ABSENT without a click.
- Every retry is a `MU_REVISIT` click on a cell the object owns now.
- A retry that certifies a lever re-emits G3's inventory. G4.1 and G4-A keep their earlier work, and the late lever goes to the back of the queue.
- Reported: every mu entry with its final status, and each frozen level model's mu list.

**Marker guards:**
- The packager refuses a source that lacks any of 11 R9-R23 markers.
- It also refuses a source that still carries the old inventory wording ("rewrite their own cells").
- The R9-R20 to R9-R22 guards still apply.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (`ec8554d`) | **8/8**; the bundled source matches the commit export exactly (0 differences) |
| The same check on the Mac with `main`'s verifier, which carries one extra check (the runtime output cap against the receipt, added in Sol's `a68043e`), using the export extracted to `runs/_cowork_xfer/r9r23/export_ec8554d` | **9/9** (run by Claude on the device; the Director repeats it at step 1) |
| Export against the cloud R9-R23 tree | Identical |
| Mount simulation in three layouts (nested, zip, direct), with both dependency datasets mounted | **All pass**: 200 actions, 10,800 s, gated, `vrfai/Qwen3.6-27B-FP8` |
| Pre-flight `check_mu_partial_close_from_record.py`, on the **packaged** source with the v6 live record (run on a copy, so the package stays free of bytecode) | Rests at level 3, **G4.2-LEVER-ORBITS**, legal (PROBE). Duck's orientation turn is due. G3 closed **PARTIAL** with E0010–E0013 and E0015–E0017; E0028 is OPEN in mu (1 try, clicked owner E0071). Exit 0 |
| Tamper test: one byte appended to `mu_return.py` | Refused (3 FAIL) |
| Request pre-flight (T10) | Worst case 33,158 tokens, against a 65,536-token window |
| Bytecode in the package | None |
| Suite at `ec8554d` | Cloud: 529 passed, 1 skipped. Mac (worktree): 529 passed, 1 skipped |

## What the run should show

**Setup.** As in v6:
- Python 3.12 paths and the 174-wheel install;
- the source manifest verified, now at **221 files** (v6 had 218; the 3 new modules make up the difference).

**Levels 1 and 2.** As in v6.
- Level 1 should be won in 26 actions.
- Level 2 should be won at t69 by the controller's G4-A press of E0007.
- The carry should grade 4/4 on level 2 and 7/8 on level 3.
- The controller is deterministic until Duck acts. Any difference before Duck's own first action is the environment's, not Duck's (I6).

**Level 3.**
- G3 runs as in v6 through t110.
- Then the controller writes the PARTIAL inventory, with no Duck turn: 7 levers, with E0028 in mu.
- Then G4-A starts with Duck's orientation turn and studies the 7 levers.
- The v6 stop at G3 (`WAIT_FOR_DISCRIMINATING_EVIDENCE`, ended by the watchdog) must not recur.

**At the end.**
- If the ladder runs out of moves on level 3 without a win, the controller returns to mu before stopping. E0028 should settle ABSENT, with no click, because it occupies no cell.
- This report must include every mu entry and its final status.

**Hypotheses, not findings:**
- Level 3 may fall to the lever study, as level 2 did.
- The 200-action budget is the likely limit, since only 90 actions remain after t110.
- E0071, the object that appeared during the sweep, is in no roster, and nothing in R9-R23 studies it. That is the open Director question about newborn objects.

## Director's steps

1. I'll put the package, the packager, the export and this record in place on your Mac. Then you run `verify_kaggle_package.py` on the Mac.
2. Commit the packager and this record on `main`, staging explicit paths only. Never stage `kaggle/`.
3. Run `kaggle datasets create -p kaggle/ring9-carry-vc33-v7/source-dataset -r skip`, then check `status` until it says `ready`.
4. Run `kaggle kernels push -p kaggle/ring9-carry-vc33-v7/kernel`.

— Claude, Alpha build seat, 2026-10-03

## Upload log (2026-10-03, Director's terminal)

| Step | Result |
|---|---|
| Mac verify (`main`'s verifier, `--source-export runs/_cowork_xfer/r9r23/export_ec8554d`) | **9/9**: source manifest 221 files, package manifest 228 files, `src.zip` 212 files, output-cap encoding `server_default` on both sides, secret scan clean, 0 diffs against the commit export |
| Commit on `main` | `aaa4a91`: packager and this record, explicit paths, `kaggle/` not staged |
| `kaggle datasets create -p kaggle/ring9-carry-vc33-v7/source-dataset -r skip` | 12 files uploaded, the same set as v6 |
| Sizes | `src.zip` 910 KB (v6: 904 KB; the difference is the 3 new modules), `source-manifest.json` 27 KB, `setup_commands.json` 10 KB, `checkpoint-preflight.json` 10 KB, the rest small |
| Visibility | private |
| Kaggle at upload end | "being created" |

**CLI notes, both expected, as in v6:**
- "Skipping folder: src". The source travels as `src.zip`, which the notebook checks against the manifest before importing anything.
- "outdated kaggle version (installed 2.0.0, latest 2.2.2)". No upgrade is needed.

**Next:**
1. `kaggle datasets status stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v7` until it says `ready`.
2. `kaggle kernels push -p kaggle/ring9-carry-vc33-v7/kernel`

**What the log should show if v7 works:**
- **Setup:** `source manifest verified (221 files)`. That is 3 more than v6, from the 3 new modules.
- **Levels 1 and 2:** as in v6 (I6).
- **Level 3 (I12):**
  - after G3's sweep, the controller writes a PARTIAL inventory, with no Duck turn: 7 levers, and E0028 in mu;
  - then G4-A, with Duck's orientation turn.
- **End (I13):** before any stop on level 3, a mu return. E0028 should settle ABSENT.
- **End time:** the run's end time against the notebook's end time (I11).

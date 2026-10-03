# Upload status: ring9-carry-vc33-v5 (R9-R21 G3 fix, pinned image)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v5.py`
**Slice:** `BUILD_SLICE_R9_R21_G3_CONTRADICTED_2026-10-03.md` (branch `r9-r20-level-entry`, commit `623ad58`)

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v5` (224 files; source 217) |
| Package manifest sha256 | `24603b22eccbcc09dc6ee70e5a94290817770092f699ef8c48724245a1e03ec6` |
| Source manifest sha256 | `1e99054c8a37de52a937d0718f40fa1347447d2fa3c3f64935f77865a52df359` |
| Source commit | `623ad58cf0847fdaf0ab22a444a023bbc4e6b062` (fbbc7f4 + R9-R20 + R9-R21), from the Director's `git archive` export |
| Image | pinned as in v4: `gcr.io/kaggle-private-byod/python@sha256:37c64f7d…` (Python 3.12), `docker_image_pinning_type: original` |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v5` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v5` |

## What changed from v4

Only the source. File by file against v4:
- exactly 2 source files differ, `virelai_gates.py` and `controller_executor.py`;
- the setup command is byte-identical;
- the image pin, datasets, world, budgets and criteria are v4's.

**New preregistered criterion, I9 (G3 on level 2):**
- A confirmation that does not repeat is a bounded ambiguity.
- G3 ends with an accepted inventory or coverage report. The coverage report is Duck's when ambiguity is bounded.
- The ladder moves on to G4.
- Level 2's G0 and G1 are the controller's, with no Duck turn at level entry.
- Any unanswerable answer is ended by the A2 watchdog within one Duck turn.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (623ad58) | **8/8** |
| Mount simulation, three layouts | **All pass** |
| Level-entry pre-flight (`check_level_entry_from_record.py`, v2 record) | G0, then G1, then G2 first click, all by the controller (exit 0) |
| **Level-2 G3 pre-flight** (new `tools/check_level_two_g3_from_record.py`, v4 live record, each package's shipped source) | **v5:** the coverage report is Duck's ("bounded ambiguity"), legal, and accepted (exit 0). **v4, negative control:** the controller's inventory is refused, "unbounded probe results: {'E0004': 'AMBIGUOUS', 'E0005': 'AMBIGUOUS'}", and the state is still called legal (exit 1). That is exactly the live stall |
| Tamper: one byte appended to `controller_executor.py` | Refused (3 FAIL) |
| Suite at `623ad58` | Cloud 517 passed, 1 skipped; Mac (worktree) 517 passed, 1 skipped |

## What the run should show

- **Setup (I5, I8):** as in v4.
- **Level 1 (I6):** v4's first 26 gate events.
- **Level 2 entry:** this time the controller answers G0 (D6), so a small difference from v4 at t27 is expected and correct. After that, G2 and G3's sweep should repeat v4 through t47: the same clicks, and the carry graded 4/4 RECONFIRMED.
- **Past t47 is new:** a Duck turn writes G3's coverage report (levers E0006 and E0007, ambiguous E0004 and E0005), and then G4.1 and G4-A study level 2's two certified levers.

**Likely limits (hypotheses, not findings):**
- The 200-action budget. 47 actions were used through G3 in v4.
- Duck's coverage report could be refused for its prose. The template itself is accepted; Duck is judged on its fields.
- The two stateful levers get no G4 study. That is the Chief Engineer question in the slice doc.

## Director's steps

1. Put the package and tool in place (I'll do it); `verify_kaggle_package.py` on the Mac.
2. Commit on `main`, staging explicit paths.
3. `kaggle datasets create -p kaggle/ring9-carry-vc33-v5/source-dataset -r skip`, then `status` until it says `ready`.
4. `kaggle kernels push -p kaggle/ring9-carry-vc33-v5/kernel`

— Claude, Alpha build seat, 2026-10-03

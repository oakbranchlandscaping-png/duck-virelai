# Record: R9-R23 (the mu bucket) has landed

**Type:** `RECORD_R9_R23_LANDING` · **v1** · **2026-10-03**
**Author:** Claude (Alpha build seat), signed.
**Read with:** `RULING_MU_BUCKET_v1_2026-10-03.md` and `BUILD_SLICE_R9_R23_MU_BUCKET_2026-10-03.md`. Both are committed on the branch, in `ec8554d`.

## 1 · What was committed

| Where | Commit | What |
|---|---|---|
| Branch `r9-r20-level-entry` (worktree `duck-virelai-r9r20`) | **`ec8554d`** (`ec8554db276aa0c416d79e998718df8815d640c4`), on `8656839` | R9-R23: 12 files, +715/−104. 5 files are new: `mu_bucket.py`, `mu_return.py`, `g3_inventory.py`, `tests/test_r9_r23_mu_bucket.py` and the fixture `tests/fixtures/vc33_kaggle_carry_v6_record.json.gz`. The ruling and the build slice are committed in the worktree root. |
| `main` | **`e869ef9`** | `tools/check_mu_partial_close_from_record.py`, the R9-R23 pre-flight (73 lines). |
| `main` | `1e10466` (earlier) | The v6 review, `REVIEW_RING9_CARRY_VC33_V6_KAGGLE_2026-10-03.md`. My handoff notes listed it as uncommitted. That was wrong: it was already committed. |

## 2 · Verification behind the commit

- **Mac pytest in the worktree, run by the Director:** 529 passed, 1 skipped, 14 warnings, in 663 s. This is the same as the cloud run: the 523 tests of R9-R22 plus the 6 new ones.
- **Fail-first** (in the build slice):
  - at `8656839`, all 6 new tests fail;
  - with each fix reverted on its own, 1 to 4 tests fail.
- **Pre-flight on the v6 record:**
  - R9-R23 rests at G4-A on level 3. Its inventory is PARTIAL, with 7 levers, and E0028 is OPEN in mu. It exits 0.
  - `8656839` rests at G3 in the live stall. It exits 1.
- **Export check:**
  - `ec8554d` holds 309 files under the two exported paths: `variants/ring9-cybernetic-gates/ARC3-Inference` and `variants/ring9-cybernetic-gates/tufa-arc-agi-framework`.
  - `8656839` holds 304. The difference is exactly the 5 new files.

## 3 · Finding: the Ring 9 source has forked

This is on the record so that it is not lost. It is not a ruling.

- **The fork point.** The click line and `main` split at `fbbc7f4` (R9-R18).
- **The click line** is on the branch: R9-R20 to R9-R23, 4 commits. Every vc33 carry run since v5 was packaged from this branch.
- **The NAV line** is on `main`, Sol's work. Since `fbbc7f4` it has 10 commits that touch Ring 9 code, from R9-R19 (the NAV lever branch) to `f985410`.
  - `main`'s working tree also holds Sol's uncommitted N1–N4 NAV build: 10 Ring 9 files, about 1,250 lines.
- **Four files are changed on both lines:**
  - `virelai_gates.py`
  - `controller_executor.py`
  - `life_record.py`
  - `controller_turn.py`
- **What this means.** Directive D-2 asks for a scored submission on all 110 games by about 12 October. One submission runs one source tree, and that tree must play both click games and NAV games. So the two lines have to be merged before the first submission. The overlap in those four files grows with every slice either seat adds.
- **The question for the Director.** When the merge happens, and which seat does it, is a plan question. It is not code-level, so this record leaves it to the Director. Until it is decided, I keep building on the branch, and I do not touch `main`'s Ring 9 files.

## 4 · Next

1. **Export.** The Director exports `ec8554d` with `git archive`, using the same two paths as before. The file goes to `runs/_cowork_xfer/r9r23/export_r9r23.tar.gz`.
2. **Package v7.** I package `ring9-carry-vc33-v7` from that export, using the v6 packager.
   - New marker checks for R9-R23.
   - Two new run criteria: a PARTIAL G3 close on level 3, and the mu return reported when the ladder ends.
   - **Planned budget, unchanged from v6:** a 3-hour window; at most about 3.3 GPU-hours (v6 used about 0.36).
3. **Upload and run.** The Director uploads and runs v7, and I review it.
4. **Open items carried forward:**
   - newborn objects such as E0071 (a Director question);
   - the merge in §3;
   - four Kaggle facts still to verify (deadline time, submissions per day, RTX PRO 6000 quota, and whether reruns count).

— Claude, Alpha build seat, 2026-10-03

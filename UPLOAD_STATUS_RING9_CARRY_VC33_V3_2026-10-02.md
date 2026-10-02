# Upload status: ring9-carry-vc33-v3 (R9-R20 level-entry fix)

**Date:** 2026-10-02
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v3.py`
**Slice:** `BUILD_SLICE_R9_R20_LEVEL_ENTRY_2026-10-02.md` (on branch `r9-r20-level-entry`)
**Review that triggered it:** `REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md`

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v3` (224 files; source 217) |
| Package manifest sha256 | `37ca7c9660f541bafc95ff4cb3d567a9a66f260208cb10c1edd7244521fb817c` |
| Source manifest sha256 | `97860934fc281e382b254fba6e89a171c506d32d1433a542ed75ef054a167ea4` |
| Source commit | `fbea80c7fd345fb121bfda2fa2c358361789528b`: `fbbc7f4` plus R9-R20 only. Built from the Director's `git archive` export, verified byte-identical |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v3` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v3` |
| Mounts | the dataset above, `stephenkaskin/virelai-vllm-wheelhouse-v3`, `stephenkaskin/virelai-qwen3-6-27b-fp8` (unchanged from v2) |

## What changed from v2

Only the source. File by file against v2:
- **Source:** exactly 2 files differ, `virelai_gates.py` and `record_replay.py`. That is R9-R20.
- **Setup command:** byte-identical.
- **Notebook:** only the dataset id and the label differ.
- **Everything else:** the remaining differences are identities, the manifests and receipts, and the docs.

The world, budgets, model, dependencies and criteria are v2's. Two additions:
- **I7, preregistered (level entry):** at level 2, G0 and G1 close under the controller with zero model calls, and G2 takes the controller's first level-2 click. If any gate ever waits while admitting no move, the A2 watchdog ends the run within one Duck turn as a controller failure, instead of idling.
- **Updated claim limit:** level 2 has been entered once live (v2, deadlocked before any click). R9-R20 is proven offline on that live record and on a stand-in level 2, never on the real level 2 beyond its spawn board.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (fbea80c) | **8/8** |
| Mount simulation, three layouts | **All pass**: wheelhouse and model resolve to your datasets, manifest (217 files), world, receipt and budgets verified |
| **Level-entry pre-flight** (new `tools/check_level_entry_from_record.py`, run on each package's own shipped source, with the v2 live record) | **v3: G0 answered, then G1 answered, then G2 first click, all by the controller (exit 0).** v2's shipped source, as a negative control: G0 answered, then **G1 handed to Duck, "offers no probe and no answer"**, with `legal: true` (exit 1). That is exactly the live deadlock and the A2 hole |
| Tamper: one byte appended to `record_replay.py` | Refused (source manifest, package manifest and `src.zip` FAIL) |
| Suite at `fbea80c` | Cloud 513 passed, 1 skipped; Mac (clean worktree) 513 passed, 1 skipped |

## What the run should show

**Before level 2:**
- **I5:** setup as in v2.
- **I6:** level 1's gate events repeat the exit run's (and v2's) 26 transitions until Duck's first own action.
- **X-1:** level 1 freezes as in v2.

**The new part, from transition 27:**
- **I7:** the controller answers G0 and G1 and starts G2's search on level 2's board, with no model call.
- **X-2:** each of the 4 carried candidates is graded the first time G3 clicks it after level 2's counter mask exists, as RECONFIRMED or FALSIFIED. Candidates G3 never clicks stay UNCONFIRMED.

**Likely limits (hypotheses, not findings):**
- **The 200-action budget.** Level 1 took 26 actions. On ft09, G2 alone took 57, and G3 sweeps every object.
- **One extra Duck turn at level entry,** the orientation, once G4.1's product exists on level 2.
- **The model is never the cause** of a level-2 stall before G4: G0 to G4.1 are the controller's.

## Director's steps

1. Put the package and tools in place (I'll do this), then run on the Mac: `verify_kaggle_package.py` (7/7 there).
2. Commit on `main`, staging explicit paths: the package, the two tools and this file. The source commit `fbea80c` stays on its branch.
3. `kaggle datasets create -p kaggle/ring9-carry-vc33-v3/source-dataset -r skip`, then `status` until it says `ready`.
4. `kaggle kernels push -p kaggle/ring9-carry-vc33-v3/kernel`

— Claude, Alpha build seat, 2026-10-02

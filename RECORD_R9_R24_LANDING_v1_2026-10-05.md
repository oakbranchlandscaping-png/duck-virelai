# Record: R9-R24 (G4 controller-first) has landed

**Type:** `RECORD_R9_R24_LANDING` · **v1** · **2026-10-05**
**Author:** Claude (Alpha build seat), signed.
**Read with:**
- `RULING_G4_CONTROLLER_FIRST_v2_2026-10-04.md`
- `DIAGNOSTIC_G4B_CONTROLLER_RELATIONS_v2_2026-10-04.md`
- `BUILD_SLICE_R9_R24_G4_CONTROLLER_FIRST_2026-10-04.md` (on the branch)

## 1 · What was committed

| Where | Commit | What |
|---|---|---|
| Branch `r9-r20-level-entry` (worktree `duck-virelai-r9r20`) | **`c9b246b`** (`c9b246be8a38334d2670276d1601c186695976ec`), on `ec8554d` | R9-R24: 20 files, +1,081/−88. **New:** `level_record.py`, `record_relations.py`, `play_gate.py`, `tests/test_r9_r24_g4_controller_first.py`, the fixture `tests/fixtures/vc33_kaggle_carry_v7_record.json.gz`, and the build slice. |
| `main` | **`f79a3b7`** | Ruling v2, diagnostic v2 (which corrects v1's D3), and the pre-flight tool `tools/check_g4_controller_first_from_record.py`. |
| `main` | `6a3183c` (earlier) | Ruling v1, diagnostic v1, and `tools/diagnose_g4b_controller_relations_from_record.py`. |
| Not committed | | The patch, `runs/_cowork_xfer/r9r24/R9_R24_G4_CONTROLLER_FIRST.patch` (sha256 `6e357710…260f`), and the v7 record copy in `runs/_cowork_xfer/r9r24/`. `runs/` is git-ignored. The v7 record is committed as the branch fixture instead. |

**How the code reached the Mac.**
- While the link to the Mac's command line was down, Claude wrote the 20 branch files straight into the worktree over the file link.
- Before writing, Claude checked that every one of the 14 files being modified matched `ec8554d` byte for byte.
- After writing, Claude read all 24 files back (the 20 branch files and the four on `main`). Each one was byte-identical to the version tested in the cloud.

## 2 · Verification behind the commit

- **Mac pytest in the worktree (Director):** 535 passed, 1 skipped, 14 warnings, in 393 s. This is identical to the cloud run: R9-R23's 529 plus the 6 new tests.
- **Fail-first** (in the build slice):
  - At `ec8554d`, all 6 new tests fail at collection.
  - Each fix reverted on its own fails 1 to 4 tests: D18 2, D19 4, D20/D21 3, D22 4, R-8 1, forced rest 1.
- **Pre-flight on the v7 record (G4B_FIRST 141):**
  - **R9-R24:** exits 0. G4-B is certified by the CONTROLLER from the record, all 7 lever states are named, the ladder moves to G4-C, and Duck's budget is still unused.
  - **`ec8554d`:** exits 1. Duck owns G4-B, and every state reads `UNRECORDED`.

## 3 · Finding: the Ring 9 fork has widened

This is on the record because the first scored submission depends on it. It is not a ruling.

**Where the lines stand.** Both still split at `fbbc7f4` (R9-R18).
- **The click line** (this branch) is R9-R20 to R9-R24: 5 commits.
- **The NAV line** on `main` now has 14 commits touching Ring 9 code since `fbbc7f4`. The newest is `aa799b5`, "Make NAV G3 preserve first lever witness". `main` also records a NAV Kaggle checkpoint submission (`c0f31e7`, N5.3).

**Eight files are now changed on both lines**, up from four at R9-R23:

| File | Kind |
|---|---|
| `virelai_gates.py` | code |
| `controller_executor.py` | code |
| `controller_turn.py` | code |
| `life_record.py` | code |
| `g4b_gate.py` | code |
| `g4c_gate.py` | code |
| `test_g4b_relations.py` | test |
| `test_memory_m1.py` | test |

**Why it matters.** Ruling R-3 says the merge comes "soon", and each slice on either line adds to the overlap. A scored submission runs one tree. Until the two lines merge, the click line's improvements can't reach a submission, and nor can the NAV line's.

## 4 · Next

1. **Export.** The Director exports `c9b246b` with `git archive`, using the same two paths as before, to `runs/_cowork_xfer/r9r24/export_r9r24.tar.gz`.
2. **Package `ring9-carry-vc33-v8`** from that export, using the v7 packager. It adds:
   - R9-R24 marker checks;
   - new criteria for G4-B written by the CONTROLLER from the record, Duck's G4-B/G4-C turns kept within 3 per level, UNRESOLVED instead of a reopen loop, and `PLAY-NORMAL` transitions receipted `FREE_PLAY`;
   - the time used at G4 on level 3, reported.
3. **Open items for the Director:**
   - the merge (§3);
   - newborn objects (E0071);
   - friction F3: nothing in the ladder aims at the win;
   - friction F5: the per-game time budget for a submission.

— Claude, Alpha build seat, 2026-10-05

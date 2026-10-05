# Review: the Ring 9 unification (`ring9-unified`, `501a6e6`)

**Type:** `REVIEW_RING9_UNIFICATION` · **v1** · **2026-10-05**
**Author:** Claude (Alpha build seat, click line), signed. A decorrelated review of Sol's merge. This seat did not audit the merge before it was committed.
**Asked:** "unify the build and create a single tree… start with simply a review in full and lets assess and plan" (Director, 2026-10-05).
**Ground:** bundle of all refs taken 11:25 (`main` `130a374`, `r9-r20-level-entry` `c9b246b`, `ring9-unified` `501a6e6`). Every number below was measured here unless marked [READ], meaning read from a document.
**Method:**
- Read-only against the repo.
- Did a mechanical re-merge of the two parents and diffed Sol's merge against it, so every hand-made resolution is visible.
- Compared the test IDs of both parents with the merge.
- Ran the full suite on the merge, and the click pre-flights on the merge and the click parent.
- Drove targeted gate-level probes on the merge and on `main`.
- Wrote one fix with a fail-first test (§4). Nothing has been committed or pushed.

---

## 0 · Verdict

The merge is a real, careful piece of work, and it is the right shape: one tree, with both lines' tests carried, and the click line's record replays unchanged. Sol's reported count reproduces exactly here: **605 passed, 1 skipped**.

**It is not ready to become the floor.** Three things are in the way:

1. **F1: a regression that blocks NAV's G3 inventory.**
   - Neither parent has it; the merge creates it.
   - A NAV target that Duck released as `PRESUMED_UNREACHABLE` now counts as unbounded.
   - So a completed NAV roster has no legal move. A2 rests the level in PLAY-NORMAL, and G4 never opens.
   - Live ls20 runs produce this state routinely: 14 `TARGET_REACHABILITY` answers in the N5.1 artifacts.
   - The fix is one line. With it, the full suite runs **607 passed, 1 skipped** (§4).
2. **F2: a behaviour change on the click line.** The merge gives CLICK G3 the first-witness rule. I agree with the design, but it is untested live:
   - every click record replay in the suite now runs the *old* G3 path in legacy mode;
   - the unified tree's vc33 trajectory diverges from v7's at level 1's first lever;
   - v7's level-1 and level-2 wins are therefore unmeasured under the unified tree.
   It needs your ratification and one live canary.
3. **F3: the NAV evidence the unification doc cites isn't in the repo.**
   - The doc says direct live evidence supports N5.3's first-witness path. Sol's own N5.3 upload record says the run was queued and "no behavioral result is claimed", and no N5.3 output is under `runs/`.
   - No test in the suite replays any NAV run. All 13 record fixtures are vc33 or ft09.
   - NAV's merge validation is synthetic only, which is how F1 got through.

The rest is code-level tidying (§3).

---

## 1 · What the merge is

| | Measured |
|---|---|
| Shape | A true merge commit. Parents `130a374` (`main`, the NAV line) and `c9b246b` (the click line, R9-R24). |
| Divergence since `fbbc7f4` | `main` 95 commits, branch 5 |
| Textual conflicts | **3 files:** `controller_turn.py`, `controller_executor.py`, `virelai_gates.py` (5 hunks). Six more files changed on both sides and auto-merged. |
| Hand-made changes beyond conflict resolution | 13 files, +254/−201, mostly in `virelai_gates.py` (+241 lines changed), `record_replay.py` and seven test files |
| `main` | **Not moved.** Still at `130a374`, still dirty with the four frozen-variant edits. The single tree exists only as branch `ring9-unified`, checked out in the old click worktree (`duck-virelai-r9r20`). |
| `virelai_gates.py` (non-blank, non-comment lines) | `fbbc7f4` 5,413 · `main` 6,965 · branch 5,344 · **merge 6,969** |

### How the resolutions read

**`controller_turn.py`.** Sol kept `main`'s ownership law: a wake reaches Duck only when the next step is Duck's own, and the budget check runs on both paths.
- My `_takes_duck_choice` guard was dropped, correctly, because the ownership rule covers it.
- **One consequence:** the counter, action and time-budget wakes no longer reach Duck when the controller owns the next step. R9-R24's docstring said they did. This is `main`'s ruling (`4e1be00`), not an error, but the click line's behaviour changes with it.

**`controller_executor.py`.**
- NAV's prediction gates now try the record first (`_relations_step`). This is safe, but it degenerates on NAV, as the next point shows.
- R9-R24's press attribution is click-only: a press is a click at the lever's site or on its object, and a NAV body contact matches neither.
- So NAV G4-B always falls to Duck's 3-turn budget. The unification doc defers this, honestly.

**`virelai_gates.py`.**
- Both sides' G3 state is kept.
- The mu revisit is limited to the CLICK phase. A HYBRID world that has switched to NAV never revisits its mu objects (minor, open).
- **G4 intake** accepts both a first-witness discovery and a legacy confirmation, the latter only through `certified()` (R9-R22).
- **The inventory check** went back to `main`'s inline form, which knows `PRESUMED_UNREACHABLE`. The blocking check in front of it is the click line's `_unbounded_entities`, which does not. That mismatch is F1.

**Tests: none were lost.**
- The merge has 606 test IDs; the union of the parents has 611.
- **The 5 IDs missing from the merge:**
  - one is renamed with its body rewritten (the click scheduler test, for first-witness);
  - one is my old ft09 end-to-end name, which I had already renamed;
  - three are tests `main` had deliberately removed in `4e1be00`.
- **One new test:** `test_click_first_positive_witness_certifies_lever_and_advances_roster`.

**Tests whose assertions were loosened:**
- The ft09 end-to-end test used to assert that the offline controller repeats the live run *exactly*. Now only the first 57 actions must match.
- `test_memory_m4` no longer checks the "retaining controller ownership after wake" line.
- Five tests and `card_duck.py` now set `_legacy_confirmation_replay = True` to keep their old traces.

These are honest consequences of F2, but the click line has now lost its "replay equals live" check for G3.

### Checks I ran

| Check | Merge `501a6e6` | Click parent `c9b246b` |
|---|---|---|
| Full suite (cloud, Python 3.12, per file) | **605 passed, 1 skipped** | 535 passed, 1 skipped (earlier, as landed) |
| R9-R24 pre-flight (v7 record, 141) | exit 0 | exit 0. Output **byte-identical** to the merge's |
| R9-R23 mu pre-flight (v6 record) | exit 0 | exit 0. Output **byte-identical** to the merge's |
| ruff, pyflakes errors on the merged files | 3: 2 inherited from `main`, plus 1 new unused import | 0 |

The click pre-flights match because they replay old records in legacy mode. They prove the merge kept the click line's past. They do not test its new G3.

---

## 2 · The findings, ranked

### F1 · A bounded NAV target now blocks G3 (regression; code-level; fix ready)

**What happens.** When Duck answers a reachability certificate, the target is marked `PRESUMED_UNREACHABLE` and recorded in `_bounded_ambiguities` (`virelai_gates.py:4446`). Then:
- `_unbounded_entities()` (`:4473`) treats only `AMBIGUOUS` and `BUDGET_STOPPED` as bounded.
- The inventory check below it (`:4526`) does count `PRESUMED_UNREACHABLE` as ambiguous. That is `main`'s code, and the two now disagree.

**Probe** (a two-target NAV roster: target 1 released as unreachable, target 2 closed null, roster complete):

| | `main` `130a374` | merge `501a6e6` |
|---|---|---|
| `legal_move_status()` | legal: the move is ANSWER, the coverage report is Duck's | **not legal:** "G3's inventory is demanded but these results are unbounded: {'E0001': 'PRESUMED_UNREACHABLE'}" |
| What follows | Duck writes the coverage report, G3 closes | `rest_if_no_legal_move` puts the level into PLAY-NORMAL; G3 never closes and G4 never opens |
| Duck's report, if submitted | accepted (`G3_BOUNDED_COVERAGE_REPORT`) | refused: "G3 coverage cannot be reported with unbounded probe results" |

**Live relevance.** `PRESUMED_UNREACHABLE` appears in the N5.1, N5 and terrain-v2 ls20 artifacts, with 14, 11 and 13 reachability answers. N5.x never completed the roster, so the bug has not fired live yet. It would fire on the first unified ls20 run that does.

**Fix.** One line: add `PRESUMED_UNREACHABLE` to the bounded set. Patch and tests are in §4.

### F2 · CLICK G3 now discovers on the first witness (a behaviour change; ratify, then canary)

The merge extends Sol's N5.3 NAV rule to CLICK. One attributed activation with masked residue is now the durable `LEVER_FOUND`, and the roster advances with no confirmation repeat.

**Reading the design, I agree with it:**
- It is "G3 discovers, G4 types" applied to both channels.
- It saves actions: v7's record holds 13 lever dossiers, so 13 confirmation actions out of 200 would not be spent.
- G4-A repeats every lever anyway.

**But it is unmeasured, and the risk is specific.**
- On a click world, the confirmation press also changed the board. In vc33, levers move regions.
- Without it, every later G3 target is probed on a different board. The sweep's attributions, its mu set and the G4-A order can all differ from v6 and v7.
- Those are the runs that cleared levels 1 and 2. Both wins came from G4-A presses at particular moments [READ, the v6/v7 reviews].
- So the unified tree's vc33 score is not inherited from v7. It is open.

**Whether it needs ratifying.** It changes G3's contract on CLICK, and that contract was set in R9-R22 with the repeat. I'd treat it as an architectural ruling that was made inside a merge. It is sound, but it is yours to ratify. It was not ruled on its own.

**Replay fidelity.**
- Live machines run the new path. Replays of old records switch to legacy mode when the record holds `LEVER_DOSSIER` answers.
- I checked that the live path cannot create a dossier: the only `_pending_confirmation` writer is behind the legacy flag. So a unified live record replays as live.
- But no such record exists yet. Until one does, nothing pins the new click G3 to the frame.

### F3 · The NAV evidence is synthetic only (a gap; process)

**What the doc claims.**
- "Direct live evidence supports N5.3's NAV first-witness path."
- Validation step 5: "NAV N5.1/N5.3 evidence preserves terrain, reachability, and lever discovery behavior."

**What the repo shows.**
- `UPLOAD_STATUS_RING9_G3_NAV_N5_3_LS20_V1` (Sol, `c0f31e7`) says the notebook was queued and "no behavioral result is claimed until the executed artifacts are downloaded and graded."
- There is no N5.3 directory under `runs/`.
- The suite has no NAV record fixture and no NAV replay. The 13 fixtures are vc33 and ft09.
- The NAV tests (`test_nav_branch_foundations.py` and others) are synthetic boards.

**What it means.** The click line has its live records as fixtures, so a merge that broke its past would fail loudly. The NAV line has none, so F1 passed all 605 tests.

**What closes it.** Pull N5.3's output if it has finished. Make an ls20 record from it, or from N5.1, which is on disk. Add a NAV replay test, as was done for vc33.

### F4 · Code-level tidying (Sol's tree, or folded into the fix)

| Item | Where |
|---|---|
| `check_inventory_claims` is imported and unused. `g3_inventory.py` is now dead code. | `virelai_gates.py:78`. The import is removed in my patch; the module is left for Sol to retire |
| `explanation`, `competing` and `falsifier` are computed twice in `_submit_inventory` (dead re-assignment) | `virelai_gates.py:~4570` |
| The R9-R23 ratchet extraction of the inventory check is undone by the re-inline: `virelai_gates.py` is 6,969 lines against `main`'s 6,965 | §1 |
| The mu revisit is CLICK-phase only, so a HYBRID world's mu objects are never revisited after it switches to NAV | `virelai_gates.py:3434` |
| NAV G4-B from the record degenerates to Duck, because press attribution is click-only (documented as deferred) | `level_record._acted_lever` |
| **Worktree hazard.** From a linked session's shell, `git worktree list` shows `duck-virelai-r9r20` as *prunable*, because that path isn't mounted there. A `git worktree prune` run from any session would remove the canonical tree's admin data. Never run prune from a session. | Mac repo |

---

## 3 · What the merge did not touch (the rest of the repo)

These are unchanged since `REVIEW_VIRELAI_FOLDER_v2` (2026-10-04) and re-checked today:

- **No git remote.** The whole record (now three lines and the unification) exists on one disk.
- **Four tracked files in frozen rings are modified and uncommitted:** `ring6/DESIGN.md`, two `ring7` modules, and `kaggle-ring6.3-run1/EVALUATION.md`. That is +398/−183 lines.
- **Untracked items:** about 40 `kaggle/` package directories, `_to_delete/`, `claude/`, and two top-level documents.
- The README still points newcomers at `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`. The documentation index is current (updated today).
- **No submission mode** exists in the source. That is the critical path the folder review named; the merge was its prerequisite.

---

## 4 · The fix for F1 (ready, not committed)

**Patch:** `UNIFIED_FIX_PRESUMED_UNREACHABLE.patch` (sha256 `47b42e6d…6173`), against `501a6e6`. It touches 2 files, +62/−2.
- `virelai_gates.py`: `PRESUMED_UNREACHABLE` joins the bounded set in `_unbounded_entities`, and the dead `check_inventory_claims` import is removed. The ratchet is net zero (6,969 → 6,969).
- New `tests/test_ring9_unified_presumed_unreachable.py`, with 2 tests:
  - a completed roster with one released target has a legal move;
  - the coverage report accepts that target.

**Fail-first:**

| Tree | The 2 new tests |
|---|---|
| merge `501a6e6` | **2 failed:** `legal` is False, then "unbounded probe results" |
| `main` `130a374` | The coverage-report test **passes** (this is `main`'s behaviour, restored). The other errors only because `main` lacks the click line's helper. |
| merge + fix | 2 passed |

**Suite with the fix:** 607 passed, 1 skipped (§6).

---

## 5 · Plan

The principle is the folder review's: one writer per shared file. Sol is the active builder and owns `ring9-unified`. Anything that changes source is Sol's to apply, or the Director's to apply from my patch.

**A · Now, no GPU (today)**

1. **Apply the F1 fix** (Sol, or the Director applies the patch). Run the Mac floor on it: expect 607 passed, 1 skipped.
2. **Rule on F2:** ratify first-witness G3 for CLICK, or keep the confirmation repeat on CLICK only. I recommend ratifying.
3. **Make it literally one line.**
   - Fast-forward `main` to the fixed `ring9-unified`. It is a direct descendant, and the dirty files are untouched by it, so `--ff-only` works.
   - Retire `r9-r20-level-entry`: keep the ref as provenance and stop committing to it.
   - Decide which checkout is the editing tree. Sol's doc names the worktree; one branch matters more than which folder.
4. **Back up off this disk:** a private remote and `git push --all`, plus a dated copy of `runs/`. About ten minutes.
5. **Add NAV record evidence (F3).** Pull N5.3's output if it has finished. Build an ls20 record fixture and a replay test that pins at least G3's first witness and a reachability release. This is Sol's, since it is Sol's world.

**B · First live evidence of the single tree (GPU, small)**

6. **One unified canary per channel, short budgets.**
   - **vc33:** does first-witness CLICK G3 still clear levels 1 and 2? Where does level 3 rest? Count the actions saved.
   - **ls20:** the roster completes with a released target, G3 closes, and G4 opens (F1 live).
   - Each run's record becomes a fixture, which restores "replay equals live" for both channels.
7. **v8, already queued on `c9b246b`:** let it run unless the queue makes it the run to drop.
   - **Its G4 evidence carries over.** R9-R24's code is identical in the unified tree, and the click pre-flight output is byte-identical.
   - **Its G3 evidence doesn't.** v8 runs the confirmation path.
   - If quota allows only one vc33 run this week, the unified vc33 canary is the more informative run.

**C · The critical path, on the single tree**

8. **Submission mode:** a run deadline passed to the ladder, a per-game slice with A2 bound to it, the public roster at a concurrency the model can serve, and a 25-game dry run under the 9-hour guard. This is the folder review's §3.1. Nothing in it is built.
9. Then the ports and pillars (S-, W-, H- series), against one tree.

**Owners:**

| Item | Owner |
|---|---|
| 1, 3, 5 and F4 | Sol (or the Director from the patch) |
| 2 and 7 | Director |
| 4 | Director (ten minutes at the terminal) |
| 6 | the seat that packages it. I can write the unified packager for both worlds from my v8 packager |
| 8 | to be named |

---

## 6 · Verification behind this review

- **Bundle:** 7.8 MB, all refs; cloned clean.
- **Mechanical re-merge:** `git merge-tree --write-tree 130a374 c9b246b` (git 2.43) gives tree `2f18500` with 3 conflicts. All of §1's "hand-made" diffs are relative to it.
- **Test IDs:** collected at each of the three commits (580 / 536 / 606) and diffed.
- **Full suite on the merge:** 82 files, one process per file, 2-way parallel. Result 605 passed, 1 skipped, 0 failed.
- **Suite with the fix:** see the closing line below.
- **Pre-flights:** run under each tree's own `inference` on `PYTHONPATH`, and their outputs diffed.
- **Probes:** `presumed.py` (F1) and `approach.py`, a NAV positive approach frame. The second showed no difference between `main` and the merge, so it is not a finding.
- **Live artifacts:** grepped on the Mac, read-only.

**Suite with the fix applied:** 607 passed, 1 skipped, 0 failed. That is the merge's 605 plus the 2 new tests; every other file's count is identical to the merge's.
- The unused import was removed while that run was in progress.
- After removing it, I re-ran the new tests with `test_g3_scheduler` and `test_r9_r23_mu_bucket`: 24 passed.
- ruff is clean on the new test file.

— Claude, Alpha build seat (click line), 2026-10-05

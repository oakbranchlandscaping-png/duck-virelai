# Record: the Ring 9 single-tree agreement between Sol and Claude

**Type:** `RECORD_RING9_SINGLE_TREE_AGREEMENT` · **v1** · **2026-10-05**
**Author:** Claude (Alpha build seat, click line), signed. It records an exchange carried by the Director.
**Parties:** Sol (Alpha build seat, NAV line) and Claude (Alpha build seat, click line). Each item is marked **AGREED**, **AMENDED** or **DIRECTOR**.
**Read with:**
- `UNIFICATION_RING9_SINGLE_TREE_v1_2026-10-05.md` (Sol, on `ring9-unified`)
- `REVIEW_RING9_UNIFICATION_v1_2026-10-05.md` (Claude)
- Sol's response of 2026-10-05, quoted in part below
**Ground:** `ring9-unified` @ `501a6e6`; parents `main` @ `130a374` and `r9-r20-level-entry` @ `c9b246b`. Nothing in this record is committed source.

---

## 1 · The exchange

| Step | Who | What |
|---|---|---|
| 1 | Sol | Merged the two Ring 9 lines as `501a6e6` on branch `ring9-unified`. Suite 605 passed, 1 skipped. `main` was not moved. |
| 2 | Claude | Reviewed the merge independently. The suite and the click pre-flights reproduce. Six findings, F1–F6, of which F1 is a regression. The fix for F1 is a patch with fail-first tests. |
| 3 | Sol | Accepted F1, F3 and F5; confirmed F4; answered F2 with the Director's ruling; proposed the split of the work. |
| 4 | Claude | This record: the reply to Sol (§2) and the agreed plan (§3–§5). |

## 2 · Findings, as settled

**F1 · A bounded NAV target blocked G3. AGREED.**
- Sol states the meaning: `PRESUMED_UNREACHABLE` counts as bounded *only* together with its evidence entry in `_bounded_ambiguities`. It releases the current roster obligation; it doesn't claim the target is inert.
- `REOPENED` blocks again. The existing membership test in `_unbounded_entities()` (`virelai_gates.py:4479`) already enforces this, and the reopen path removes the entry (pinned by `test_reachability_answer_explains_limit_releases_target_and_stays_bounded`).
- Claude's patch and its 2 tests are accepted as they stand. Patch: `runs/_cowork_xfer/unify/UNIFIED_FIX_PRESUMED_UNREACHABLE.patch`, sha256 `47b42e6d…6173`.
- The fix lands as its own commit. Clean-up goes in separate commits.

**F2a · First-witness discovery on CLICK. DIRECTOR (one line to confirm).**
- **Sol cites the Director:** *"we should mirror the CLICK G3. collide with something. record a change, mark it as a lever, move on to the rest of the list. then return to the initial lever for typing"*. Sol reads it as a gate law for both channels.
- **Claude's reading.**
  - The procedure in the quote has no repeat. So the Director's account of G3 is first-witness, and the unified code matches it.
  - The quote was given to correct NAV, with CLICK as the reference. CLICK as built (R9-R22) *did* repeat: Claude added a prospective confirmation press as the falsifier for "a hidden process changed the object at the same moment as the click."
  - First-witness moves that falsifier into G4-A, which repeats every lever anyway. Claude concedes the design.
  - What is left is not an argument between the two seats. It is one fact for the Director to confirm: that CLICK should lose the repeat too.

**F2b · The new CLICK trajectory must be measured. AGREED.**
- v6 and v7 are evidence for the confirmation implementation only. Legacy replay preserves the past; it says nothing about the new path.
- A short unified vc33 canary is required, and its record becomes a fixture.

**F3 · The unification document overstated NAV evidence. AGREED.**
- Sol will correct the evidence paragraph and the validation ladder.
- The live evidence is N5.1's positive contact at transition 18. N5.3 is validated only synthetically and was never graded live.
- The signature will name "parallel repository-structure, runtime and lineage audits commissioned by Sol." The audit agent `claude_tree_audit` was not this seat.

**F4 · Wake ownership. AGREED.**
- A wake doesn't entitle Duck to a turn. The controller recomputes ownership. Duck's budget is charged only when Duck owns the step.
- The click line has adopted this law.
- R9-R24's build slice is a filed record and stays as filed. This record notes that it is superseded on this point.

**F5 · NAV presses from the record. AMENDED.**
- **Sol's press signature.** A NAV press is all of the following:
  - `pilot_intent == CONTACT_ATTEMPT`;
  - `contact_epoch.target_entity_id` is the lever;
  - the contact evidence equals the transition's `evidence_id`;
  - `procedure_id` is the target-bound procedure;
  - `final_action` equals the transition's action;
  - the attempt is terminal and not interrupted by a boundary.

  `REFUSED` counts as a press. A null result is still a press. `APPROACH` is never a press. A row without this identity falls back to Duck.
- **Sol's seam.** A compact `intervention` field on each transition row: `kind`, `entity_id`, `procedure_id`, `final_action`, `contact_outcome`.
- **Claude's amendments:**
  1. **The ego mask.** `level_record.presses()` computes effects as `masked_changes(before, after, counter law)`. On NAV the ego moves on every press, so every press would read as "changed elsewhere."
     - NAV effects must subtract the ego's footprint as well, the way G3 attribution does.
     - Proposal: the row also carries the attribution's residue, as local and remote cell counts plus the disposition, keyed by `evidence_id`. NAV presses then read G3/G4's own attribution instead of recomputing it from boards.
  2. **The schema.** The new field is GAME tier, like every `transition_index` row. Its tier goes in `life_record.PERSISTENCE`.
     - `record_replay` must accept rows that lack it, since every existing record does. The answer id must stay a function of levers, claims and transitions, so that a replay gives the same answer.
  3. **Order.** Sol's seam comes first. Claude's `presses()` and `record_relations` work follows against Sol's NAV fixture, not against synthetic rows.

**F6 · Clean-up and the HYBRID mu limit. AGREED.**
- After F1, in separate commits:
  - the unused `g3_inventory` import and the dead module;
  - the duplicated assignments in `_submit_inventory` (`virelai_gates.py:4546`, `:4570`);
  - restoring the inventory extraction for the ratchet.
- The HYBRID mu-return limit (`virelai_gates.py:3434`) gets its own test and its own slice.

## 3 · Who builds (as Sol proposed; Claude accepts)

| Work | Owner |
|---|---|
| F1 fix and its tests (Claude's patch), as its own commit | Sol |
| Corrections to the unification document (evidence, ladder, signature) | Sol |
| NAV record fixture and replay test (from N5.1, or N5.3 when pulled) | Sol |
| NAV `intervention` and residue fields in the transition record | Sol |
| NAV-aware `presses()` and record-derived relations | Claude |
| Unified CLICK/NAV packager | Claude |
| CLICK canary: packaging and grading | Claude |
| NAV canary grading | Sol |
| Submission scheduler and slice guard, in new files | Claude |
| Hooks into the gate machine, and ownership review of those hooks | Sol |
| F6 clean-up; HYBRID mu slice | Sol |
| Private remote, off-disk backup, Kaggle actions, Mac pytest | Director |

**The rule for the shared file:** one writer per window. `virelai_gates.py` is Sol's for the windows in §4. Claude's work goes in new files, or in the modules Claude already owns (`level_record.py`, `record_relations.py`, `play_gate.py`, packagers, tools).

## 4 · The sequence

Sol proposed seven steps. Claude agrees to the content and amends the order in two places, for the calendar: the first scored submission is due about 12 October, and Kaggle queue times are long.

| # | Step | Owner | Gate to pass |
|---|---|---|---|
| 1 | F1 commit and the document corrections | Sol | — |
| 2 | Full local floor on the Mac | Director | 607 passed, 1 skipped |
| 3 | Inspect status, then fast-forward `main` to `ring9-unified`. Freeze `r9-r20-level-entry` and stop developing on `ring9-unified` separately. | Director | `--ff-only` succeeds; the four dirty frozen-ring files are untouched |
| 4 | **Package and queue both canaries at once** (vc33 and ls20, short budgets) | Claude packages; Director pushes | Packages verified against the commit export. Tests are green, which is the prerequisite for a live run. |
| 4′ | **While they queue:** the NAV fixture and replay, the NAV `intervention` seam, F6 | Sol | Floor green after each commit |
| 4″ | **While they queue:** submission mode in new files (deadline, per-game slice, A2 bound to the slice, roster runner) | Claude | Offline dry run over recorded worlds; Mac floor |
| 5 | Grade the canaries. Each record becomes a fixture. | Claude grades vc33, Sol grades ls20 | Exit criteria in §5 |
| 6 | Sol's hooks for submission mode, then a 25-game dry run under the 9-hour guard | Sol, then the Director runs it | A completed run with a table of where each game's ladder rested |
| 7 | NAV presses from the record (after the seam and fixture) | Claude | NAV G4-B certified from the record on the ls20 fixture |

**What changed from Sol's order:**
- **The canaries no longer wait for the NAV fixture.** The tests already pass, so a live run is allowed. The fixture comes from a historical run and doesn't affect what the canary measures. Queueing early buys back queue time.
- **Submission mode moves ahead of NAV relation generalization.** Submission mode is on the critical path to about 12 October. NAV G4-B from the record is an improvement, and without it NAV G4-B falls back safely to Duck's 3-turn budget.

## 5 · Canary exit criteria (preregistered)

**vc33 (unified CLICK).** 200 actions; the time budget is proposed below.
- Setup: the source manifest verifies against the unified commit.
- **G3 on every level:**
  - every `LEVER_FOUND` has a single witness;
  - no G3 confirmation probe occurs;
  - the roster advances immediately.
- **Reported against v7:** actions spent in G3 per level, and whether levels 1 and 2 clear, and how (GATED or FREE_PLAY). A clear is not presumed.
- **Level 3:**
  - G4-B certified by the controller from the record;
  - at most 3 Duck turns at G4-B/G4-C;
  - `PLAY-NORMAL` with `FREE_PLAY` receipts;
  - the time from G4-B opening to PLAY-NORMAL reported.
- **Replay:** the run's record, replayed offline without legacy mode, reproduces the live action sequence exactly.

**ls20 (unified NAV).** Budget proposed by Sol.
- The first positive contact emits `LEVER_FOUND` with no confirmation detour.
- Any released target is `PRESUMED_UNREACHABLE` and bounded. If the roster completes, G3 closes with an inventory or a coverage report, and G4 opens. This is F1, live.
- No level rests in PLAY-NORMAL because G3 had no legal move.

**Proposed vc33 budget:** 200 actions and 3,600 s of behaviour time, about 1.3 GPU-hours with setup.
- v7 cleared levels 1 and 2 in about 8.6 minutes of behaviour time.
- Under R9-R24, level 3's G4 should take minutes.
- An hour answers every criterion above without paying for 3 hours of free play.

## 6 · For the Director

1. **F2a:** confirm in one line that CLICK G3 also drops the confirmation repeat (first witness, then the next target). Both seats agree on the design.
2. **v8** (queued on `c9b246b`): if it hasn't started, cancel it and spend that run on the unified vc33 canary.
   - The unified canary answers everything v8 would on G4, because R9-R24's code is identical and the pre-flight output is byte-identical.
   - It also measures first-witness G3, which v8 cannot.
   - If v8 is already running, let it finish.
3. **Backup:** choose a private remote and its credentials, then `git push --all`, and make a dated copy of `runs/`. Do this before step 3.
4. **Approve** the split (§3), the order (§4) and the canary budgets (§5).

— Claude, Alpha build seat (click line), 2026-10-05

---

## Addendum A · Director's rulings, backup, and step 1 (2026-10-05, later the same day)

**Director's rulings**
- **Agreement:** the split (§3), the order (§4) and the canary criteria (§5) are approved as written.
- **F2a:** CLICK G3 drops the confirmation repeat. It records the first witness and moves to the next target, as NAV does.
- **v8:** it was already `RUNNING` on Kaggle when checked, so it continues.
- **`runs/`:** stays local only, by the Director's choice.

**Backup**
- Private remote `origin` = `github.com/oakbranchlandscaping-png/duck-virelai`.
- All three branches were pushed and checked with `git ls-remote`: `main` `130a374`, `r9-r20-level-entry` `c9b246b`, `ring9-unified` `501a6e6`, each identical to the Mac.
- Before the push, Claude scanned every blob in history, plus the contents of the 20 committed `src.zip` files, for credentials. None were found.
- Pushes use HTTP/1.1: `git -c http.version=HTTP/1.1 -c http.postBuffer=157286400 push origin --all`. The default HTTP/2 push stalled.

**Step 1 (Sol), checked by Claude on the Mac repo**

| Commit | Content | Check |
|---|---|---|
| `fa9617b` (parent `501a6e6`) | "Bound released NAV targets in G3 inventory" | Its diff equals Claude's patch line for line (`index` lines excluded) |
| `f86d6ef` (parent `fa9617b`) | Corrections to the unification document: the signature, the evidence paragraph and validation step 5 | Read in full; matches F3 as agreed |

- Sol's focused run: 24 passed. This is the same set Claude ran on the patched tree.
- The branch is two commits ahead of `origin/ring9-unified` and is not yet pushed.

**F5 schema: two refinements from Sol, accepted by Claude**
1. **Residue as cell coordinates.** The NAV residue is stored as cell coordinates (`attributed_residue`: `evidence_id`, `disposition`, `local_cells`, `remote_cells`), not just counts. `record_relations` needs to know which lever regions the residue touches, and counts can't say that. Claude's amendment asked only for counts and was too weak.
2. **Persistence.** `life_record.PERSISTENCE` declares machine attributes, not fields inside a row. A field on a `transition_index` row inherits the row's GAME tier, so record tests pin that instead. Claude's amendment was wrong on this point.

**ls20 canary budget**
- **Sol's proposal:** 120 actions and 1,800 s, with six criteria. A run that hits its budget before the roster completes is diagnostic only.
- **Claude's arithmetic from the N5.1 artifacts:**
  - G0–G2 took 12 actions.
  - G3 used 39 actions and resolved about 6 of 16 eligible targets: about 6.5 actions per target.
  - So completing the roster is projected at about 12 + 16 × 6.5 ≈ 116 actions, before the 2 reopened targets.
  - Time was 691 s of wall clock, 681 s of it in 8 Duck turns: about 85 s per turn.
  - Both 120 actions and 1,800 s are therefore at the edge for the criterion the canary exists to test (F1 at roster closure).
- **Claude's counter-proposal:** 160 actions and 2,700 s. That is about 15 more minutes of GPU time, and makes roster closure likely rather than marginal.
- **Decision:** the Director's.

## Addendum B · Step 2: the Mac test run on the fixed tree (2026-10-05)

- **Tree:** the `duck-virelai-r9r20` worktree on `ring9-unified` @ `f86d6ef` (F1 fix `fa9617b` plus the document corrections).
- **Command (Director):**
  `PYTHONPATH=.:tests:../tufa-arc-agi-framework/src ~/Desktop/virelai-review/duck-virelai/variants/ring9-cybernetic-gates/ARC3-Inference/.venv/bin/python -m pytest -q tests`
  run from the worktree's `ARC3-Inference` folder.
  - The worktree's own `.venv` has no pytest, so this uses the main checkout's environment.
  - `PYTHONPATH` puts the worktree's source first.
- **Result:** **607 passed, 1 skipped, 14 warnings in 367 s.** This is the merge's 605 plus F1's 2 regressions, and it matches the cloud run exactly. The 14 warnings are the usual pyparsing deprecations inside matplotlib.
- **Status:** gate 2 of §4 is met. Next: push `ring9-unified`, check `main`'s status, then fast-forward `main` (step 3).

## Addendum C · Step 3: `main` is the single tree (2026-10-05)

- **Pushed:** `ring9-unified` went `501a6e6..f86d6ef` on `origin`.
- **Checked before the move:** the only tracked files with edits were the four frozen-ring files (`runs/kaggle-ring6.3-run1/EVALUATION.md`, `variants/ring6/DESIGN.md`, and two `variants/ring7` modules). `main` is an ancestor of `ring9-unified`, and none of the four overlaps the files the move changes.
- **Moved (Director):** `git merge --ff-only ring9-unified` took `main` from `130a374` to `f86d6ef`. 48 files changed, +3,047/−342: R9-R20 to R9-R24, the merge, F1, and the document corrections. The four frozen-ring edits are untouched.
- **Branches now:**

| Branch | Commit | Role |
|---|---|---|
| `main` | `f86d6ef` | The single tree. Test floor 607 passed, 1 skipped. |
| `ring9-unified` | `f86d6ef` | Same commit as `main`; checked out in the `duck-virelai-r9r20` worktree |
| `r9-r20-level-entry` | `c9b246b` | Frozen; provenance for v1–v8 |

- **Not yet done:** `main` still has to be pushed to `origin`, and this record and `REVIEW_RING9_UNIFICATION_v1` still have to be committed on `main`.

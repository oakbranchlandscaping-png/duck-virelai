# Directive v3: one north star, one tree, one queue — to 8 November 2026

**Type:** `DIRECTIVE_COMPETITION_ENDGAME` · **v3** · **2026-10-05**
**Status:** **RATIFIED by the Director, 2026-10-08** ("all are ratified"). Supersedes v2.
**Author:** Claude, Apex seat (granted by the Director 2026-10-05), signed.
**Supersedes on ratification:** `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04.md`. v1 and v2 stay in place as history.
**Binds:** every chamber working in or for this repo, whatever its seat. A chamber that has not read this document and the highest-version State of the Build is not working on the project.

---

## 0 · The north star (Director, 2026-10-05)

> **A finished solver with actual results, and a submittable paper.**

Everything below serves that sentence. Anything that does not serve it — however interesting — is deferred by this directive, and the deferral is recorded, not argued.

Operationally the north star is three artifacts, and the project is finished when all three exist:

1. **A scored ARC-AGI-3 Kaggle submission** linked to the paper (hard requirement of the Paper Prize; score need not be competitive).
2. **The glass-box world report**, emitted per game by the solver itself: the world's mechanics and, where observed, its win condition, every line carrying its evidence.
3. **The paper**, by 8 November, playing for Theory, Universality, Novelty and Completeness; Accuracy conceded.

What changed from v2, with the dated reason: the Director made the paper the whole deliverable (2026-10-05) and punted grading until a report exists worth grading. The model-swap window therefore becomes conditional (§4), the world report becomes a chartered slice ahead of all other build work except the merge (§2), and the chambers get named lanes (§3) so that five seats act as one.

---

## 1 · The critical path, in order

Nothing on this list starts until the item above it is committed, except where marked ∥ (parallel).

| # | Step | Exit observable | Lane |
|---|---|---|---|
| 1 | **Promote the merge.** `ring9-unified` exists (Sol; 605 passed, 1 skipped). Before it becomes `main`: fix F1 (one line; 607 passed), the Director ratifies F2 (CLICK G3 first-witness rule) and runs its one live canary, F3 is recorded as a known gap (NAV validated synthetically only). Then `ring9-unified` → `main`; retire the worktree. (`REVIEW_RING9_UNIFICATION_v1_2026-10-05`) | One tree at a named commit in the State of the Build. | Director + click seat + Sol |
| 1b | **Backup.** The remote exists (`origin`, GitHub, 2026-10-05). Remaining: `git push --all` after #1, and a dated snapshot of `runs/` (19 GB, gitignored, one copy) to a second disk. | Snapshot path recorded. | Director |
| 2 ∥ | **R9-R25 — the world report.** `tools/compile_world_report.py` reads `gate_answers`, `level_lessons`, `win_capsules` (and the target-journal snapshot when present) → `world_model.json` (schema `virelai-world-model-v1`) + `world_report.md`. Built and tested offline on the v7 files. Then the runtime writes `TargetJournal.snapshot()` at level end and run end and calls the compiler at run end. Assembly and rendering only; no gate logic changes. | From v7 offline: a `world_model.json` that passes the validator; claim counts by status × executor; a `world_report.md` where every line cites a transition or is marked unadmitted. | Report seat |
| 2 ∥ | **Submission mode.** A run-level deadline passed down to the ladder; a per-game slice with the A2 watchdog bound to it; the full roster at a concurrency the model can serve; the hard 9-hour guard. No gate is weakened; a game the ladder cannot reach is still played within its slice. | A dry run on the 25 public games completes inside the guard, with a per-game table: slice used, gate the ladder rested at, levels, actions, and the world report emitted. | Click seat |
| 2 ∥ | **NAV under the slice.** NAV games must not crash or idle: G3 NAV closes UNRESOLVED cleanly within the slice and hands Duck normal play with the gate products. Terrain depth beyond that is deferred (§4). | The same dry run shows every NAV game ending by planned stop or slice, never by watchdog failure. | NAV seat |
| 3 | **The 25-game dry run** (one notebook, ≤9 GPU-h). This single run is the submission proof *and* the paper's evidence run: it emits 25 world reports, 22 of them on worlds no gate was developed against. | Table above; 25 reports on disk; the run packet filed. | Director runs; click seat reviews |
| 4 | **First scored submission, ~12 October**, on Qwen3.6-27B-FP8. | A leaderboard score, any value. | Director |
| 5 | **Answer keys and grading** (now unpunted, because reports exist). Keys for all 25 public games written and committed *before* reading any report; per-claim correct / wrong / unverifiable, missed, invented; at least one game graded blind by a non-author. | A grading table, by game, by executor. | Director writes keys; a non-author grades |
| 6 ∥ | **Learn-to-win** LW-1 → LW-3 on the vc33 record (replay, no GPU); LW-4 prospective on level 3 as the single prospective case. | Admitted or refused explanation per level, with citations and residue; the two-win ledger; the level-3 verdict. | Click seat |
| 7 | **Freeze 27–30 Oct; final submission.** Second and third submissions between 13 and 26 Oct only as the build improves, never for the score alone. | Final submission recorded with its commit. | Director |
| 8 | **Paper, 31 Oct – 8 Nov**, but the outline and methods begin now (§3, paper lane). | Submitted. | Paper seat + Director |

---

## 2 · R9-R25 is chartered

**Naming note (2026-10-05, evening):** R9-R24 was taken today by G4 controller-first (`c9b246b`, Director-ruled). The world report is therefore **R9-R25**. The same landing record reports the fork at **eight** shared files; critical path #1 is now more urgent, not less.

Ratified by this directive on signature: the world report, R9-R25 (critical path #2) is the next build slice on the click line, scoped exactly as above. Its reasons are on the record in the Apex review of 2026-10-05: the pieces exist (`virelai_world_model.py`, 1,148 lines, schema v1; `gate_answers.jsonl`, 84 rows on v7, carrying `executor` per answer; `level_lessons` and `win_capsules`, 2 each on v7) and are not assembled. The report is written by the controller; Duck never writes it. Three kinds of line: CONTROLLER-certified; DUCK-proposed and admitted; DUCK-proposed and not admitted. Duck's free-text narration is an appendix, labelled, ungraded.

---

## 3 · The lanes — four chambers, one Apex, one Director, acting as one

Roster confirmed by the Director, 2026-10-05: a **paper chamber**, **Claude Alpha builder**, **Sol Alpha builder**, a **learn-to-win chamber**; plus this **Apex** chamber and the **Director**. Each chamber owns one lane. A chamber that finds work outside its lane files it as a friction with its altitude and hands it to the Director; it does not do it.

| Lane | Chamber | Owns (deliverable) | Does not touch |
|---|---|---|---|
| **Director** | Stephen | Merge (#1), remote and `runs/` snapshot (#1b), the GPU queue, every Kaggle action, answer keys (#5), ratification, every transmission between chambers | — |
| **Submission** | Claude Alpha builder | **Submission mode** (critical path #2): run deadline → per-game slice → A2 bound to the slice → full roster at a serviceable concurrency → 9-hour guard; the 3-game local smoke; the review of the 25-game dry run (#3). Also the two runtime write hooks for R9-R25 (`TargetJournal.snapshot()` at level end and run end; the compiler call at run end) — two small commits, wired after the compiler exists. | NAV gate internals; the compiler and renderer; LW rungs; paper text |
| **World report + learn-to-win** | Learn-to-win chamber | **R9-R25 offline:** `tools/compile_world_report.py` and the renderer, built and tested on the v7 files, no runtime changes. Then LW-1 → LW-3 on the vc33 record (replay), LW-4 as the one prospective case. The report format is what LW-2/3 consume, so the same chamber owns both. | The runtime; gate logic; submission mode; the paper text |
| **NAV safe under the slice** | Sol Alpha builder | NAV games end well in the dry run: G3 NAV closes UNRESOLVED cleanly inside a slice and hands Duck normal play with the gate products; no watchdog failures, no idling. The terrain work is deferred past the dry run (§4). | Click gates; the four shared files without a `NOTE_SHARED_FILE` first; the compiler |
| **Paper** | Paper chamber | **Outline filed by 12 Oct.** The derivation section from the ARC-AGI-3 paper (§2.1, §2.3, §3.4, §3.5, §3.6). The gate taxonomy with necessary vs contingent archetypes. The admission rules and the three-line-kind report format. The honest ledger. Evidence tables filled only from filed run packets (#3) and the grading table (#5). Methods and derivation drafted by 26 Oct. | Any claim not traceable to a committed document or filed run; any number not at a commit |
| **Apex / verification** | Claude, this chamber | This directive; the Ring 9 State of the Build at each checkpoint; grading every chamber's return against its exit observable; routing frictions; keeping the lanes straight | Building anything |

**Hand-offs between lanes, in order.** Learn-to-win chamber delivers the compiler (offline, v7-tested) → Claude Alpha wires the two hooks → the dry run emits 25 reports → the paper chamber and the Director receive them → keys are written (Director, before reading any report) → grading → the paper chamber fills its tables. The paper chamber never waits idle: outline, derivation, taxonomy and admission rules need no run.

**The GPU queue is one queue and the Director holds it.** ~30 GPU-h/week, every seat. Order of priority, fixed: the dry run and submissions; then LW-4; then anything else. Every run packet states its expected GPU-hours before upload. No chamber proposes a run without naming what it displaces.

**One tree.** After #1, `main` is the only line. A seat that needs isolation uses a short-lived branch merged within the day, never a second worktree that lives for weeks.

**Shared files.** `virelai_gates.py`, `controller_executor.py`, `life_record.py`, `controller_turn.py` are the fork's scar. A seat that must change one files a one-line note (`NOTE_SHARED_FILE_<date>.md`) naming the function before committing, so the other seat reads it before its next slice.

---

## 4 · Deferred by this directive (recorded, with reasons)

- **The model-swap window (v2 D-3, D-8)** becomes *conditional*: it opens only if the first scored submission is on the board by 12 Oct **and** the 25 reports from #3 are graded. Otherwise it is cut on 13 Oct with a dated note. Reason: the paper concedes Accuracy; the swap buys only Accuracy and costs days and quota the evidence run needs. The engine-versus-gate measurement is a later paper.
- **Pillar 1 ports beyond P1–P3.** Reason: nothing else on the port register serves the four rubric categories in play.
- **NAV terrain depth** beyond clean closure under the slice. Reason: NAV is a different paper; the submission needs NAV games to end well, not to be won.
- **Gate-order ablation.** Reason: already deferred by the Director (2026-09-30); the paper claims decomposition, not order.
- **The four Kaggle facts** stay open items on the Director (deadline time, submissions/day, quota, whether reruns bill). They gate #7's slack, not the critical path.

---

## 5 · How a chamber works under this directive

1. Open with this document, then the highest-version State of the Build, then its lane's documents. Not memory.
2. Produce one of: a committed slice with its filed review, a filed ruling, a recorded kill, or an honest "examined — no change". A session that ends with none of these did not finish.
3. Every filed document is `TYPE_NAME_vN_YYYY-MM-DD`, signed, with a one-line entry at the top of the documentation index.
4. Every claim is tagged committed / believed. A report, a score, a test count: at a commit, or marked unverified.
5. Frictions are routed, not fixed in place: code-level → the work order; architecture → the Apex seat; plan → the Director. The exception channel is open: halts are information.
6. The Director carries everything between chambers. A chamber never assumes another chamber's state; it reads what the Director filed.

---

## 6 · Calendar with teeth

| Dates | Must be true by the end |
|---|---|
| Mon 5 – Tue 6 Oct | Merged; remote pushed; `runs/` snapshot; R9-R24 and submission mode started |
| Wed 7 – Thu 9 Oct | R9-R24 passes on v7 offline; submission mode passes a local 3-game smoke; NAV closes clean |
| Fri 10 – Sat 11 Oct | The 25-game dry run; 25 reports on disk; run packet filed |
| Sun 12 Oct | First scored submission; State of the Build v1 for Ring 9; **paper outline filed** |
| 13 – 19 Oct | Keys committed; grading; LW-1–3; swap window opens or is cut (13 Oct) |
| 20 – 26 Oct | LW-4 canary; second submission if the build improved; **methods and derivation sections drafted** |
| 27 – 30 Oct | Freeze; final submission |
| 31 Oct – 8 Nov | Paper written from filed evidence only; submitted |

A date missed is not a failure; it is information. It is reported in the State of the Build the same day, with what it displaces.

---

— Claude, Apex seat, 2026-10-05. Pending ratification by the Director.

# Rulings: consolidation of the build (v1, 2026-10-08)

**Type:** `RULINGS_CONSOLIDATION` · **v1** · **2026-10-08** · Recorded by Claude, Apex seat, signed. **Director-ratified 2026-10-08** ("all are ratified"). Binds every chamber.

## Ratified today
1. `DIRECTIVE_COMPETITION_ENDGAME_v3` — ratified; supersedes v2.
2. `THESIS_v1_2026-10-05` — ratified. The paper chamber writes from it; the build team builds toward it.
3. `SPEC_PHYSICS_GRAMMAR_v2` and its foundations `FOUNDATIONAL_ARCHETYPES_v2`, `NESTED_TAXONOMY_SPEC_v5` — ratified. **Learn-to-win is the physics grammar's win sentence**: one line, one spec, one build order (LW-0 → LW-A → LW-B1/2/3 → LW-C → LW-D → LW-E → LW-F). LW-0 is a go.
4. `BUILD_PLAN_PAPER_EVIDENCE_v1` — ratified as the plan of record, with its §4b (not inherited) and §4c (preconditions).
5. **Learn-to-win ownership.** The learn-to-win chamber owns the grammar spec and the offline code, LW-0 through LW-D, on the spec's order. Claude Alpha's earlier LW-1 slice is superseded where it overlaps. Claude Alpha owns the runtime side: the report hooks, the goal freeze at level entry (LW-E), submission mode. Nobody writes learn-to-win code outside this split.
6. **G1's explanation is never a precondition for the first action.** No model turn may gate action before evidence exists; Duck's explanation is proposed and admitted afterwards. (Dry run: 8 games ended at zero actions.)
7. **An exhausted gate in a scored run rests in PLAY-NORMAL; it never ends the game.** (Already built in SUB-2: first controlled stop rests, second ends.)
8. **The scored submission gates on two things only:** the rehearsal passes its checks, and the Director confirms the Kaggle facts. Sol's NAV canary is paper evidence, not a submission blocker.
9. **Branch rule, every chamber:** commit to `ring9-unified`; `main` moves only after a Mac floor; packages are built from `main` at a commit, never from a working tree.
10. **Keys before reports.** The Director writes the 25 answer keys from play, reading no run artifact, and commits them before the report compiler runs on any save-run output.

## The two-builder ownership table (Claude Alpha, Sol)

| Area | Owner | The other builder |
|---|---|---|
| Submission mode, packaging, rehearsal grade, `ring9-submission-v*` | Claude Alpha | reads the packet |
| World-report runtime hooks (`TargetJournal.snapshot()` at `level_model.freeze_level`; compiler call at run end) | Claude Alpha | — |
| Goal freeze at level entry (LW-E), on the `carry.py` pattern | Claude Alpha | — |
| CLICK gates G0–G4.x, `level_record.presses()` (click-shaped) | Claude Alpha | files a `NOTE_SHARED_FILE` before touching |
| NAV: G1 bearings, G3 cell-site contact and roster, G3→G4 handoff, NAV-aware `level_record.presses()` | Sol | files a `NOTE_SHARED_FILE` before touching |
| NAV safe under the slice (free play, no idle, no watchdog failure) | Sol | — |
| `virelai_gates.py`, `controller_executor.py`, `controller_turn.py`, `life_record.py`, `record_replay.py`, and any other file both lines changed | **whoever has the open slice**, one at a time | `NOTE_SHARED_FILE_<date>.md` naming the function, filed before the commit; the other builder reads it before their next slice |
| Report compiler, LW-0 → LW-D (offline) | learn-to-win chamber | both builders read its slices; neither edits them |

**Harmony rules.** One tree, one queue, one index. Each builder's day ends with a signed index line naming the commit and what it touched. A builder who needs a shared file the other has open waits or files a friction — never a parallel edit. Runs are proposed with their GPU-hours and what they displace; nothing is queued that will not be graded.

— Claude, Apex seat, 2026-10-08

# Build plan: everything the paper needs, in order, with the code it lands on (v1, 2026-10-07)

**Type:** `BUILD_PLAN_PAPER_EVIDENCE` · **v1** · **2026-10-07** · Author: Claude, Apex seat, signed. Planning document; nothing built here.
**Ground:** `main` = `ring9-unified` at `e9e5112` (docs) / runtime floor `c5e8ff6`: **619 passed, 1 skipped** (`STATE_OF_THE_DUCK_BUILD_v2`). Paths below are under `variants/ring9-cybernetic-gates/ARC3-Inference/`; `I/` = `inference/`. Line numbers read at the `ring9-unified` worktree on 2026-10-07; re-verify at file:line before building (reading discipline §8).
**Governs with:** `THESIS_v1_2026-10-05`, `DIRECTIVE_COMPETITION_ENDGAME_v3` (draft), `SPEC_PHYSICS_GRAMMAR_v2` §7, `LEARN_TO_WIN_ZOOM_v2`, `SWEEP_DETERMINISTIC_OFFLOAD_PRIOR_ART_v1`.
**Corrections to the directive, from the repo:** the merge is promoted (`main` = unified, F1 fixed in `fa9617b`); submission mode exists (SUB-1, `d751a5b`); a 110-clone dry run has completed (`UPLOAD_STATUS_RING9_SUBMISSION_DRYRUN_v1`); the remote exists. Critical path #1 and the first half of #2 are done. This plan starts from there.

**The rule every slice obeys (from the sweep):** a module lands with the function that reads it, in the same slice. No fifth field card.

---

## 0 · What the paper needs, mapped to slices

| Paper claim / section | Evidence artifact | Slices that produce it |
|---|---|---|
| Linked scored submission (hard requirement) | Leaderboard entry from `ring9-submission-v1` | SUB-2 |
| C2 · the world report per game, every line evidenced | `world_model.json` + `world_report.md` per game, 25 public | R9-R25, SUB-3 |
| C2 · grading | Keys + grading table | GRADE-1, GRADE-2 |
| C3 · goal as prediction N → N+1 | Admitted explanations; the two-win ledger; level-3 verdict | LW-0, LW-A, LW-B, LW-C, LW-D, LW-E, LW-F |
| Reproducibility (deterministic inquiry) | Byte-identical reports; identical gate products through G4.1 on two live passes | REPRO-1 |
| Executor breakdown (what the model adds) | Lines by executor; admission rate | R9-R25 (free), GRADE-2 |
| Honest ledger: hidden state, players | Two axiom tests with counts | AX-1, AX-2 (optional) |
| Front-loaded action curve (H0) | actions per level across levels, per game | SUB-2/SUB-3 packet (free) |

---

## 1 · Submission track (owner: Claude Alpha; Director runs Kaggle)

### SUB-2 · First scored submission (~12 Oct)
**State:** SUB-1 built submission mode: 110 unique game ids from the gateway (`I/framework/kaggle.py`, count-and-uniqueness contract, `d751a5b`); concurrency and per-game caps from `I/framework/run.py:429-436` (`max_actions_per_game`, `concurrency`); the soft end in `I/framework/solver.py:409-419` (`soft_deadline_reached`) and the per-game action cap at `solver.py:451-459`; planned stops receipted at `solver.py:173-179`. Dry run settings: 10 concurrent, 600 s / 400 actions per game, 2-h soft end; expected 2.3 GPU-h.
**Build:** (1) grade the dry run against C-1…C-7 (`UPLOAD_STATUS_RING9_SUBMISSION_DRYRUN_v1` §4); (2) the ruling in §5 below on an exhausted G3 (`I/framework/play_gate.py:70,109`, D22; `I/agent/controller_turn.py:104-116`, the no-legal-move rest) — a scored run must never end a game while its slice has time; (3) package `ring9-submission-v1` from `main` with `tools/package_ring9_submission_v1.py`, verify with `tools/verify_kaggle_package.py` (9/9); (4) submit.
**Exit:** a leaderboard score, any value; the run packet with per-game: gate rested at, actions, levels, Duck turns and seconds (criterion R). This packet is also the first all-25 read of Ring 9 and the first `a_n/b_n` table.
**GPU:** ~2.3 h for the save run; the competition rerun per fact #4.

### SUB-3 · Reports from every scored run (after R9-R25)
Add the two hooks (R9-R25 §2) so the public save run emits 25 `world_report.md`. No new logic. The competition rerun's outputs are not returned, so the public run is the evidence run.

---

## 2 · R9-R25 · The world report (owner: learn-to-win chamber builds the compiler; Claude Alpha wires the hooks)

**What exists.**
- Schema and validator: `I/framework/virelai_world_model.py` — `WORLD_MODEL_SCHEMA` `:10`, `Claim` `:31` (status + `EvidenceRef` `:20`), `WorldModel` `:144`, `canonical_bytes` `:179` and `model_sha256` `:262` (byte-identical output), `validate_world_model` `:518`, `empty_world_model` `:594`, `with_level_lessons` `:266`.
- Inputs on disk per run: `gate_answers.jsonl` (`I/agent/gate_artifacts.py:117-123`, `record_gate_answer`; rows carry `gate_id`, `executor`, `semantic_claims`), `gate_events.jsonl` (`:90`), the G3 target ledger (`:18`), `level_lessons.jsonl` and `win_capsules.jsonl` (`I/framework/virelai_runtime.py:~505-523`, paths; capsule written `:678-691`), `world_model.json` path configured `:523` and never produced.
- Certified products in memory only: `TargetJournal` `I/framework/cybernetic_targeting.py:110`, `snapshot()` `:160`, uncalled.
- The grading unit's prior: `virelai_v4/weave/claim_decomposer.py` ("decompose the induced map into human-gradable claims").

**Build, two commits.**
1. `tools/compile_world_report.py` (new; offline). Reads a run's `gate_answers`, `level_lessons`, `win_capsules`, journal snapshot if present → `WorldModel` via `empty_world_model` + claims, validated by `validate_world_model`, written canonical; then `world_report.md`: sections self · time · response · players (declared UNKNOWN) · model · value; one claim per line; three line kinds by `executor` and admission (CONTROLLER-certified / DUCK-admitted / DUCK-refused); evidence ref at line end; Duck's `scientist_note` (`I/agent/scientist_note.py:56`) as a labelled appendix. Test on `runs/kaggle-ring9-carry-vc33-v7/output/` first.
2. Runtime hooks: write `target_journal.snapshot()` beside the gate artifacts at level end (`I/framework/level_model.py:79`, `freeze_level`) and run end; call the compiler at run end from the runtime's artifact close.

**Exit:** on v7 offline, `world_model.json` passes the validator; claim counts by status × executor; a report where every line cites a transition or is marked unadmitted; `model_sha256` identical on two runs of the compiler.
**GPU:** none.

---

## 3 · Learn to win (owner: learn-to-win chamber; the live freeze on Claude Alpha). Order per `SPEC_PHYSICS_GRAMMAR_v2` §7, cheap first.

### LW-0 · Noun continuity (proper nouns)
Inside `CONTRACT_G3_ENTITY_LIFECYCLE_v1`: structural GROW/SHRINK joins; DEFORM abstains. Ledger: `I/framework/entity_observation.py:148` (`EntityLedger`, schema `:506`). **Exit:** v7 level 2's four distinguishing entities (E0002, E0003, E0078, E0079) have continuous worldlines across the level or the break is declared. Owed ruling §5-1.

### LW-A · The record keeps the board at the win
`virelai-recorded-world-v1` (`I/framework/record_replay.py:14`) stores one `changed` list per step (`:258`, `:274`); at a level switch that is the next level's spawn. The board at the win lives only in the capsule (`I/framework/virelai_win_capsule.py:85-90`, layer `len-2`). **Build:** `virelai-recorded-world-v2` with the winning layer on level-ending steps; regenerate fixtures from run artifacts (`tools/record_from_artifacts.py`); replay reads it. **Exit:** replayed record yields the winning board whose SHA matches the capsule's `winning_render`. Touches `record_replay.py` (shared file: `NOTE_SHARED_FILE` first).

### LW-B · Every certified entity in the vocabulary (B1 common nouns, B2 verbs/conditions, B3 prepositions)
- B1: REACTIVE-DRIVEN from G4 effect edges re-keyed from cells onto worldlines (`I/framework/g4_reactions.py`, `record_relations.py` D19). Hypothesis to check first: cell-keyed channels lose a moving driven object (spec §7).
- B2: joint-vector coupling fit; prior `virelai_v4/weave/coupling.py` (480), `I/framework/virelai_semantic/joint_transform.py`.
- B3: a fixed relation set over typed entities — `aligned`, `inside`, `touch`, `overlap`, `same_row/col`, `shape_matches`, `count`, `none_left`, `every_<rel>`. Port JustAdev `arc3/dsl.py:1597-1688` (Apache-2.0, `8b8a728`), transcribed with provenance, keyed on G3-ledger types, never colour. New file `I/framework/win_relations.py`. Inputs: `I/framework/level_record.py:53` (`level_boards`) and the ledger.
**Exit:** on v7 level 2, a separator exists in entity+relation terms, strict and broad (`LEARN_TO_WIN_ZOOM_v1` §2 showed none in lever terms), or the vocabulary gap is declared.

### LW-C · The referee and the win sentence
Replace `tools/compile_post_win_grammars.py:101-111` (`_minimal_separator`, Ring 8 regions, strict only) and its caller `I/framework/virelai_lessons.py:303-343` (`_object_win_explanation`) with a gate-side referee: candidates over LW-B's vocabulary; strict contrast (earlier uses of the winning action) and broad contrast (every earlier state, action-gating guard); simplest separator preferred; **novelty-separated** flag when the winning configuration never occurred before; admission rules per `PILLARS_…` §2 (every clause cites a gate product; true at every win; false across the contrast; a state condition; residue declared). Priors for the elimination shape: `Universal_Solver_v3_5/crucible/hypothesis/omega.py`, `falsification/primitives.py`. **Exit:** planted toy cases pass; v7 level 1 admitted-with-novelty-flag or refused; v7 level 2 admitted in entity terms or refused with reason. Phase sovereignty: computed from the gate machine's record (`level_model.py:8`), capsule as cross-check.

### LW-D · Lift, instantiate, grade (replay-prospective, vc33 L1→L2)
Pattern: `I/framework/carry.py` — statuses `:29`, `declared_at_transition` `:106`, grading `:126`, schema `:135`. New `I/framework/goal_carry.py`: lift colour-free (JustAdev `goal_signature` `dsl.py:1744-1754`), instantiate on N+1 by type (`instantiate_goals` `:1757-1793`, drop already-satisfied), freeze at the entry transition, grade from N+1's record: RECONFIRMED / SPECIALISED (satisfied-without-win with a winning-class action; add a conjunct or a stage ordered by the life record) / KILLED (`goal_progress` `:1914-1953` as the prior). The ledger cumulative across wins. In-house priors: `Universal_Solver_v3_5/memory/win_transfer.py`, `win_library.py`. **Exit:** with the code blind to level 2, a preregistered verdict per level-1 candidate against the recorded level-2 win; the two-win ledger. **GPU:** none.

### LW-E · Live-prospective, vc33 L2→L3
Runtime: freeze the ledger's goal at level-3 entry where `freeze_level` fires and the lever carry freezes (`level_model.py:79`, `carry.py:106`), before any level-3 action. The Director runs the canary (~0.4 GPU-h, as v6). **Exit:** the verdict is recorded before the level-3 win, whichever way it goes.

### LW-F · Reports carry the goal
The world report's "value" section renders the ledger's current sentence with its citations and its residue. One renderer change in R9-R25.

---

## 4 · Evidence instruments (owner: Director + a non-author; tools by Claude Alpha)

### GRADE-1 · Answer keys, committed before any report is read
`keys/<game>.md` for all 25 public games, in the archetype vocabulary: self (action surface, locus, budget), time (what decays), response (what responds, its law), players, win condition per level. Written by the Director from play, not from source. Commit hash is the timestamp. Exit: 25 files, committed before SUB-3's run is downloaded.

### GRADE-2 · The grader
`tools/grade_world_report.py`: per claim, correct / wrong / unverifiable against the key; missed (key facts absent from the report); invented (report claims absent from the key), by executor. Blind human grading on ≥1 game by a non-author recorded beside it. Exit: one table, 25 rows × executor.

### REPRO-1 · Reproducibility, measured
In the SUB-3 packet: `compile_world_report.py` twice per game, diff; one game, two live passes, diff the gate products through G4.1 (criterion I6's premise, `RUN.md`: "the controller is deterministic until Duck acts"). Exit: 25 identical SHAs; one live pair with identical products through G4.1 or the divergence transition named.

### AX-1 · Hidden-state test (transcribe, do not invent)
**Correction (2026-10-08, golden mine):** the detector exists in the golden tree — `golden/push/machine.py`, `Machine.contradictions`: a state machine keyed `masked state + action + clicked worldline`, with an explicit contradiction when the same key yields different outcomes. The latest golden commit records an ls20 level-1 completion at node 351 with zero contradictions (a builder report in git, not a reviewed run record). Ring 9's AX-1 transcribes that logic over `I/framework/masked_world_state.py` (retroactive identity) and emits a `HIDDEN_STATE` claim citing both transitions. The sweep's "no prior in any generation" is withdrawn for this row. Exit: on all 25 dry-run records, a count per game; a report line where it fires.

### AX-2 · Autonomous change (optional; the "players" row)
Residual attribution: change on a transition not ego, not counter, not a certified lever effect, recurring ⇒ `AUTONOMOUS` claim. Prior: `Universal_Solver_v3_5/discovery/census/cohesive_unit_discovery.py`. Only if time allows after LW-D; otherwise the report declares the section unknown, which is on-thesis.

---

## 4b · Not inherited (binding on every port; from the golden mine, 2026-10-08)
- v3.5's fixed win-kind taxonomy (guesses among goal families; the win is observed, then described).
- Confidence thresholds and class-wide passability assumptions from old NAV code.
- Engine-derived goal priors from outside notebooks.
- Any field-card or contract type without its reader landing in the same slice.
- Anchor-only target addresses not rebound to current full cell sites.
- Replay fixtures richer than production records.
- Tests that validate a schema without showing the controller acts on the result.
- Golden's Push / masked-state SEARCH: the strongest internal explorer, and **off the paper-critical path**; it is the `ACT_ON_GOAL` slice after LW-E.

## 4c · Preconditions surfaced by the mine
- SUB-2's submission hardening is **uncommitted** in the unified worktree (reports 627 passed, 1 skipped, not independently rerun). It is committed, with its tests rerun on the Mac, before `ring9-submission-v1` is packaged. A package is built from a commit, never a working tree.
- The golden ls20 level-1 completion becomes citable in the paper as the deterministic floor only once it has a filed run record (packet, log, test count at commit). Until then it is a builder's note.

## 5 · Rulings this plan needs (Director), in unblocking order

1. **Exhausted G3 in a scored run → rest in PLAY-NORMAL, never end the game** (`STATE_OF_THE_DUCK_BUILD_v2` §2-2). Recommended: yes; a slice with time left is never surrendered.
2. **LW-0 go** inside the lifecycle contract; `FOUNDATIONAL_ARCHETYPES_v2` / `NESTED_TAXONOMY_SPEC_v5` ratification status (spec §8).
3. **Q-1…Q-5** of `BUILD_SLICE_LW_1_RELATIONS_REFEREE_LEDGER_v1` §6: the relation set is our own closed enumeration (yes); outcome referee now, transition referee later (yes); read-only check for the winning frame (yes); ownership per §3 above; exposure declaration filed as written.
4. **Keys authored by the Director; blind grader named.**
5. **AX-2** scheduled or left declared-unknown.

---

## 6 · Order and dates (teeth)

| By | Done |
|---|---|
| Thu 9 Oct | Dry run graded; ruling 1; R9-R25 compiler passes on v7 offline; LW-0 started |
| Sat 11 Oct | `ring9-submission-v1` saved and verified 9/9; hooks wired (SUB-3); LW-A done |
| Sun 12 Oct | **Scored submission on the board.** 25 reports from the save run on disk. Keys committed *before* the reports are opened. |
| 13–16 Oct | GRADE-2 table; REPRO-1; LW-B (B1–B3) |
| 17–20 Oct | LW-C; LW-D (replay-prospective verdict, two-win ledger) |
| 21–24 Oct | LW-E canary; LW-F; AX-1; second submission if the build improved |
| 27–30 Oct | Freeze; final submission |

Every slice: fail-first tests on the v7 record; the consumer named; signed; one index line.

— Claude, Apex seat, 2026-10-07

# Build plan: ports and the two pillars, ready to execute (v1, 2026-10-04)

**Author:** Claude (Alpha build seat), signed.
**Status:** **BUILD PAUSED** by the Director (2026-10-04 07:07): *"We must pause actual building so the same files are [not] being edited at the same time, but we can fully detail our plan so when the time comes we are ready to execute."* This document is that plan. Nothing in it has been built.
**Governs:** the execution of `PORT_PLAN_PUBLIC_NOTEBOOKS_v2_2026-10-04`, `PILLARS_PORT_AND_LEARN_TO_WIN_v1_2026-10-04`, and `RULINGS_PORT_AND_PILLARS_v1_2026-10-04` (R-1 to R-8), under `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04`.
**Read at:** `main` `d9d6347`; click branch `r9-r20-level-entry` `ec8554d`; fork point `fbbc7f4`. Ring 9 paths below are relative to `variants/ring9-cybernetic-gates/ARC3-Inference/`.
**Tags:** [OBS] = read at the cited file:line; [HYP] = inference.

---

## 0 · The rule this plan is built around: new files, thin hooks

The two Ring 9 lines are both changing the same files [OBS, `git diff --stat fbbc7f4..main` and `..r9-r20-level-entry`]:

| File | Changed on the click branch | Changed on `main` (NAV) |
|---|---|---|
| `inference/framework/virelai_gates.py` | yes | yes (+1,572) |
| `inference/framework/controller_executor.py` | yes | yes |
| `inference/framework/life_record.py` | yes | yes |
| `inference/agent/controller_turn.py` | yes | yes |
| `inference/agent/tool_agent.py` | — | yes (+438) |
| `inference/framework/solver.py` | — | yes (+40) |
| `inference/agent/gate_artifacts.py`, `prompts.py`, `framework/card_builder.py`, `g4b_gate.py`, `g4c_gate.py`, `lever_lifecycle.py` | — | yes |

The first four are the shared files named in `RECORD_R9_R23_LANDING_v1` §3. The rest are changed on `main` only, so a port that edits them before the merge would create a new conflict.

**So every work order below puts its logic in new modules,** which collide with nothing. **Shared files receive only hook lines:** a few lines each, listed exactly in the hook ledger (§4) and applied to the merged tree, never to either line alone. Most of the work can therefore be written and tested before the merge. Only the hooks wait for it.

**Start condition for hooks:** the merge is done and the merged tree's Mac floor is recorded (`uv run pytest` count at the merged HEAD). Until then, building is paused (Director, 2026-10-04). Whether new-file-only work may proceed during the pause is ruling Q-2 (§8).

---

## 1 · Track S: the 110-game submission spine (before the ~12 October submission)

### S-1 · Proof that games can share one process

- **Why.** Games run as threads in one process. The static audit found no shared mutable state (`DIAG_R5` §3). A runtime test must confirm it.
- **New file:** `tests/test_s1_concurrent_replay.py`.
- **Method.** Replay the live records already in `tests/fixtures/` (`vc33_kaggle_carry_v6_record.json.gz`, `ft09_kaggle_v2_record.json.gz` and others) through `inference/framework/record_replay.py:194 replay()`. Do it once serially, then 8 at a time in a `ThreadPoolExecutor` with the records interleaved. Assert that each record's gate events, products and memory card are **byte-identical** between the serial and concurrent runs.
- **Fail-first.** A deliberately injected module-level cache, present only in the test, must make the test fail. This proves the test can see a leak.
- **Hooks:** none.
- **Exit:** the test passes on the merged tree; Mac floor +1.

### S-2 · The run deadline and per-game time

- **Found while planning [OBS]:** most of this already exists.
  - `solver.py:403 soft_deadline_reached()` reads `solver.soft_time_remaining_seconds()` (the notebook's soft end).
  - `should_stop()` (`:439-456`) stops on the soft deadline, the per-game runtime limit and the action cap.
  - `request_timeout_seconds()` (`:420-437`) shortens model requests to fit the remaining time.
- **What is left:**
  1. **A test** that a session stops before the soft end, and that a model request in flight is cut to the remaining time. It uses a fake clock injected through a new `inference/framework/run_clock.py`, which also holds S-3's shared clock.
  2. **Per-game fairness**, so that one stalled game cannot hold the model while others wait. S-3's admission gate does this, not a per-game time cap.
- **Hooks:** H-1 (`solver.py`, use `run_clock` for `time.monotonic()` in three places).
- **Exit:** the fake-clock test passes.

### S-3 · Priority admission for model calls (PT-2)

- **New file:** `inference/agent/priority_admission.py`, transcribed from Franzen `ARC3-Inference/inference/agent/priority_scheduler.py` (134 lines) and `_PriorityGate` (`tool_agent.py:1976-~2150`) at `tonghuikang/daniel-franzen-arc-agi-3` @ `b2fee61` (Apache-2.0, with a provenance header).
  - **Kept:** the priority formula (immediate gain *A*, continuation tail *B*, stall factor *C*); `TAIL_LOOKUP_REMAINING` (8/7/5/0); the tail fade over the last 20%; release and re-enqueue as one critical section; the prefix-preserving handover.
  - **Not kept:** `TAIL_LOOKUP_80K` and `priority_pace_reference.json`, which were fitted on his model. The pace starts neutral.
- **Slots: 10 to start.** That is the server's own concurrency figure, `DIAG_R5` §1. It is tuned in the canary.
- **Controller turns never take a slot;** only model requests queue.
- **Reads only** public level counts and each game's own progress.
- **New file:** `tests/test_s3_priority_admission.py`, with these cases:
  - a higher-priority game is admitted first;
  - a game in controller-only gates is never blocked;
  - release and re-enqueue are atomic, tested with a barrier;
  - the tail fades over the final 20%;
  - the gate reads no game identity, asserted on the snapshot fields.
- **Hooks:** H-2 (`tool_agent.py`, wrap `post_chat` at about `:1833` in `with admission.slot(session):`).
- **Exit:** tests pass; the canary shows no idle slot while games wait.

### S-4 · Submission mode settings and packaging

- **What changes:**
  - concurrency for game sessions set to cover 110 games (sessions are cheap while controller turns run; the model slots are S-3's 10);
  - per-game time policy left to S-3;
  - `MULTIMODAL_UPSCALE=10` (`inference/framework/kaggle.py:121`; affordable per `DIAG_R5` §2.6);
  - the packager writes the submission receipt fields (model, slots, upscale, per-game GATED/FREE_PLAY).
- **New file:** `tools/package_ring9_submission.py`, adapted from the existing `tools/package_ring9_carry_vc33.py`.
- **Hooks:** none in shared files. This is config plus a packager.
- **Exit:** cloud verify and Mac verify pass; mount simulation 3/3, as the v6 and v7 packages do.

### S-5 · Free play when the ladder rests (R-2: "use what data we have and keep playing")

- **Rule.** When the ladder rests, the session switches to FREE_PLAY for the rest of its time. The ladder rests when A2 declares an end, or when a gate stays unclosable within the bounded wait.
  - Duck's card keeps every certified product: action surface, ego, counter mask, levers and their laws, carry, life record.
  - Duck may batch actions (R-1).
  - The gates keep recording.
- **New file:** `inference/framework/play_mode.py`. It holds the mode decision (a pure function of the gate machine's state) and the receipt line.
- **New file:** `tests/test_s5_play_mode.py`, built on the recorded rests in the fixtures:
  - a record whose ladder rests switches to FREE_PLAY;
  - a record whose ladder is still closing stays GATED;
  - the certified products carry into the free-play card;
  - the receipt says FREE_PLAY with the transition at which it switched.
- **Hooks:** H-3 (`controller_turn.py`, consult `play_mode` before handing the turn to Duck) and H-4 (`gate_artifacts.py`, write the receipt line).
- **Paper rule (R-2):** prereg and paper claims cite gated evidence only. FREE_PLAY transitions are tagged in every record so they can be excluded mechanically.

### S-6 · Perception for Duck (PT-4)

- **New files**, transcribed from Franzen @ `b2fee61` (Apache-2.0):
  - `inference/utils/animation.py` (333 lines): the frames an action played, offered to Duck's sandbox as data;
  - `inference/utils/frame_diff.py` (307 lines): matched objects (moved, rotated, appeared), offered as a tool;
  - the game-over frame image, added to `inference/agent/vision_context.py`.
- **Firewall check:** neither file carries world content; checked on transcription.
- **Evidence.**
  - Scott Le Grand: frames are the only change that moved his hidden score; a text narration of the same frames regressed [REPORT].
  - So frames are given **as data or an image, never narrated by the harness.**
- **Tests:** `tests/test_s6_perception.py` covers frames exposed in the order played, `frame_diff` on toy boards, and the game-over frame attached once.
- **Hooks:**
  - H-5: `python_tool_sandbox.py`, add `animation_frames` and `frame_diff` to the runtime variables. Changed on neither line since the fork [OBS]: low risk.
  - H-6: `vision_context.py`, the game-over image. Also unchanged on both lines.

### S-7 · Waste guards in free play (R-1, R-8: "block and label why it is being blocked")

- **New file:** `inference/agent/waste_guard.py`. It is active only in FREE_PLAY; guided gates are untouched, because R-1 keeps one gate-admitted action at a time there.
- **What it blocks:**
  - **Known no-op:** an action that already changed nothing outside the counter mask from this masked state.
  - **Stale batch:** the remaining actions in a batch after one changed nothing.
  - **Terminal:** any action after a level-complete or game-over result.
- **Masking:** the G2-certified counter mask where it exists, otherwise a 1-cell border.
- **Every block carries a label that names the harness as its source, the reason, and the evidence:**

  > `HARNESS REFUSAL (not the game): ACTION3 from this board changed nothing outside the counter at t41 and t44; it was not sent. Choose a different action or board state.`

- **Tests:** `tests/test_s7_waste_guard.py`:
  - each block type fires;
  - each label names the harness and cites transitions;
  - nothing fires in GATED mode;
  - the counter mask is used when certified.
- **Hooks:** H-7 (`solver.py`, call `waste_guard.check()` in `step_env` (`:790`) before `_execute_action` (`:873`)).
- **Watch item:** whether the label prevents the confusion Scott Le Grand measured is graded at the first canary that triggers a block.

### S-8 · Retained functions (PT-6)

Optional; after S-1 to S-7.
- **New file:** `inference/utils/retained_functions.py` (Franzen, 301 lines).
- **Hook:** H-5's runtime-variable list.
- **Exit:** a test that a function Duck defines is available in the next call, and its board-specific globals are refreshed.

### The bundled canary (the Director runs it)

**Package:** S-1 to S-7 (S-8 optional) on the merged tree. **GPU: about one evidence run** (D-5).

**Preregistered criteria:**

| ID | Criterion |
|---|---|
| C-1 | Runs offline against the competition's bundled environment files (non-rerun mode) for the public games, under a time cap. No crash. |
| C-2 | Every game has a receipt (GATED or FREE_PLAY, with its switch transition). |
| C-3 | No artifact carries another game's ID (cross-game mixing check). |
| C-4 | The run ends before the soft deadline. No request is in flight at the end. |
| C-5 | Admission keeps all model slots busy while games wait. Controller turns are never queued. |
| C-6 | Prompt tokens with 10× images stay under the 65k window: max ≤ 40k (the v6 max was 28.5k). |
| C-7 | vc33 still clears levels 1 and 2 with gate events identical to v6 up to level 2 (regression guard). |

The run cap and the exact command are set in the canary's upload record, before the run.

---

## 2 · Track W: learn to win (pillar 2), offline, no GPU until W-6

| WO | What | New files | Hooks | Tests (fail-first) | Exit |
|---|---|---|---|---|---|
| **W-1** | Relations between certified entities: same type, colour class, alignment (rows/columns), containment, adjacency, overlap, shape match, vanish, count, "every"; ego relations when G1 is embodied. The geometry is transcribed from JustAdev742 `dsl.py:1597-1767` @ `8b8a728` (Apache-2.0), **re-keyed on certified entity types, with no colour constants and no 64-cell constant**. His kind list is not ported (lesson 0016 was derived from game source). The relation set is fixed from our vocabulary before any win record is opened. | `inference/framework/win_relations.py` | none | `tests/test_w1_relations.py` on toy boards | Each relation is correct on toy boards; no constants beyond the grid passed in |
| **W-2** | The referee (R-6). The outcome check is transcribed from Tycho `wmlib_template.py:1071-1375` @ `f68912a` (Apache-2.0): a candidate holds at every win, is false at every non-win state, with typed misfires (missed or false win, missed or false death). The transition check comes from `:434-892`, with **our G2 counter mask as Tycho's UNKNOWN mask** and the anti-vacuity coverage. The per-entity claim check comes from JustAdev742 `dsl.py:245-289, 905-968`. Zero model calls. | `inference/framework/win_referee.py` | none | `tests/test_w2_referee.py`: a planted correct condition is admitted; a planted wrong one is killed with the right misfire type; a candidate abstaining everywhere is refused as vacuous; **the action-gating guard**: a state satisfying the condition without a winning-class action is not counted as a counterexample | All four cases pass |
| **W-3** | **G8-EXPLAIN**, a gate target opened by the observed win. It builds the describe table (W-1 over every recorded state of the level), the strict contrast (earlier uses of the winning action) and the broad contrast (every earlier state, under the guard). It computes survivors (W-2), asks Duck **one bounded question** ("state the win in these terms only; name what they do not explain"), and admits or refuses (W-2). Residue is recorded. | `inference/framework/g8_explain.py` | H-8 (`virelai_gates.py`: register the target behind the level freeze); H-9 (`card_builder.py`: a G8 slot) | `tests/test_w3_g8_explain.py` on a toy two-level world with a known planted win | An admitted explanation cites gate products, carries residue, and is refused when given a planted wrong answer |
| **W-4** | **The win ledger.** Generalise (keep what wins share, after the colour-free lift); specialise (the condition held and a winning-class action was taken, but no win came: open a missing conjunct or an ordered stage, with the order taken from the life record); kill (a win while the condition is false). Every operation cites its transitions. | `inference/framework/win_ledger.py` | none | `tests/test_w4_ledger.py`: generalise, specialise (including an ordered "then") and kill on toy worlds | All three operations, each with citations |
| **W-5** | **G9-B goal carry.** At level entry, the ledger's surviving set is lifted and instantiated on the new board by type identity (the same matching as `carry.py`). Anything already true at entry is dropped. The rest is **frozen before any action** and graded by the level's own record. | extends `inference/framework/carry.py` (unchanged on both lines since the fork [OBS]) | none beyond W-3's | `tests/test_w5_goal_carry.py` | Frozen at entry; graded at the level end |
| **W-6** | **Offline lab on vc33.** The machinery is committed first. Then, on the **v6 record** (`tests/fixtures/vc33_kaggle_carry_v6_record.json.gz`): (a) explain the level-1 win; (b) freeze the goal at level-2 entry and grade it against the **recorded** level-2 win (retrospective); (c) update the ledger with the level-2 win. The verdict forms are preregistered in the test before it is run. | none | none | `tests/test_w6_vc33_lab.py` | A recorded verdict per candidate, plus the two-win ledger |
| **W-7** | **Live level-3 test (LW-4).** The ledger's goal is frozen at level-3 entry and graded live. **The Director runs the canary.** | none | none | canary criteria filed with its upload record | A verdict decided before the level-3 win: reconfirm, specialise or kill |

**Honesty rule carried from the pillars plan.** vc33 is a dev world, and the build seat has read a description of its win kind. W-6 and W-7 show the machinery **works**. Generalisation waits for the held-out worlds under the prereg, and the `su15` exposure is declared (R-4).

---

## 3 · Track A: `ACT_ON_GOAL` (named project, R-7; opens after W-7 passes)

These are outline work orders only. Each gets its own plan when the project opens.

| WO | What | Source |
|---|---|---|
| A-1 | Masked-state machine: (masked state, key) → state; contradictions reported, never averaged; untried keys listed coverage-ordered; `route()` gives the shortest known path. This is also canon's Push and G7. | golden `push/machine.py:57-207`, `push/search.py:40-120` (ours). Ring 9 already has the masked addresses (`masked_world_state.py`). |
| A-2 | Code-fitted rules and a simulator, so a small model never has to write a simulator; Duck names, the referee admits | JustAdev742 `dsl.py:293-891, 1064-1422` (Apache-2.0) |
| A-3 | Planners with a status taxonomy (found / unreachable / over budget), `validate_plan`, and subgoals for ordered goals | Tycho `wmlib_template.py:1376-1773` (Apache-2.0) |
| A-4 | Predict, act, compare: **one predicted frame per committed action**, halting on the first divergence | baseline1 `plan_executor.py:70-111` (MIT), adapted to one action per frame |

---

## 4 · The hook ledger (the only edits to shared files)

| Hook | File | Exact change | WO | Changed on both lines? |
|---|---|---|---|---|
| H-1 | `inference/framework/solver.py` | Use `run_clock.now()` in place of `time.monotonic()` at `:400`, `:408` and in `request_timeout_seconds` | S-2 | `main` only |
| H-2 | `inference/agent/tool_agent.py` | Wrap `post_chat(payload)` (about `:1833`) in `with admission.slot(session):`, including the 429 retry loop | S-3 | `main` only |
| H-3 | `inference/agent/controller_turn.py` | Before handing a turn to Duck: `mode = play_mode.decide(machine)`; in FREE_PLAY, build the free-play card | S-5 | **both** |
| H-4 | `inference/agent/gate_artifacts.py` | Write the play-mode receipt line on each transition | S-5 | `main` only |
| H-5 | `inference/agent/python_tool_sandbox.py` | Add `animation_frames`, `frame_diff` (and later `retained_functions`) to the runtime variables | S-6, S-8 | neither |
| H-6 | `inference/agent/vision_context.py` | Attach the game-over frame image once | S-6 | neither |
| H-7 | `inference/framework/solver.py` | In `step_env` (`:790`), call `waste_guard.check()` before `_execute_action` (`:873`) | S-7 | `main` only |
| H-8 | `inference/framework/virelai_gates.py` | Register G8-EXPLAIN behind the level freeze (`_advance_level` path) | W-3 | **both** |
| H-9 | `inference/framework/card_builder.py` | Add a G8 slot and its budget | W-3 | `main` only |

**Each hook carries the ratchet:** no function grows past its tier, logic lives in the new module, and the hook only calls it. Each hook is announced in the documentation index before it lands (R-3).

---

## 5 · Sequence and calendar

| Window | Work | GPU |
|---|---|---|
| Pause (now until the merge) | Plan only (this document); answer the rulings in §8. If Q-2 is yes: write the new modules and their tests (S-1, S-3, S-6 files, S-7 module, W-1, W-2, W-4), which touch no shared file. | none |
| Merge day | The merge (owner per Q-1); Mac floor recorded at the merged HEAD | none |
| Merge + 1–2 days | Hooks H-1 to H-7; S-4 packager; S-5 | none |
| ~9–10 Oct | **Bundled canary** (§1) | ~1 run |
| ~11–12 Oct | **First scored submission** | submission |
| After the submission | H-8, H-9, W-3, W-5, W-6 (offline lab) | none |
| 13–24 Oct | W-7 level-3 canary; the model swap window (D-3, D-8) in parallel | canaries |
| 25–26 Oct | D-8 decision | — |
| 27–30 Oct | Freeze; final submission | submission |

**Calendar risk [HYP].** If the merge slips past about 7 October, the canary and the first submission compress. The fallback that keeps the 12 October date is to submit with S-1 to S-4 only (spine and settings), with free play and the guards following in the next weekly submission.

---

## 6 · Risks

1. **The merge itself.** `virelai_gates.py` changed on both lines (+1,572 on `main` alone). A bad merge breaks gates on both kinds of world. **Mitigation:** both lines' full test suites must pass on the merged tree, and both lines' live records (the vc33 v6 fixture, the NAV fixtures) must replay to their recorded results before any hook lands.
2. **Free play blurring the claim.** Mitigation: per-transition FREE_PLAY tags, and a mechanical exclusion in the prereg analysis (R-2).
3. **Labelled refusals still confusing the model** (R-8). Mitigation: graded at the first canary that triggers a block. If confusion shows, the fallback is Scott Le Grand's run-and-tag.
4. **Admission starving a game.** Mitigation: the stall factor *C* and the tail fade. C-5 checks it.
5. **Pillar 2 finding no separating condition on vc33.** That is a legitimate result: an empty survivor set reopens the vocabulary question and is reported as such, never patched.

---

## 7 · What is deliberately not in this plan

- The model swap: D-3's window, its own protocol.
- Context drain (PT-3) and stale-image stripping (SL-1). Both were measured unnecessary (`DIAG_R5` §2).
- JustAdev742's goal-kind list, his engine-internal instrumentation, and fitted priority tables.

---

## 8 · Rulings owed (Director)

1. **Q-1. The merge:** who performs it (Sol, Claude, or the two in sequence) and the target date. The calendar in §5 assumes about 6–7 October.
2. **Q-2. During the pause, may new-file-only work proceed?** That is new modules and their tests, touching no shared file and with no hooks. It would let S-1, S-3, S-6, S-7, W-1, W-2 and W-4 be ready the moment the merge lands. Recommended: yes.
3. **Q-3. Fallback for 12 October:** if the merge slips, submit with S-1 to S-4 only (recommended), or hold the date for the full bundle.

— Claude

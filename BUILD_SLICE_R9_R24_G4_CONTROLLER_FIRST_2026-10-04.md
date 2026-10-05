# Build slice R9-R24: G4-B from the record, Duck's per-level budget, normal play after the gates (D18–D22)

**Date:** 2026-10-04
**Author:** Claude (Alpha build seat), signed
**Ruling:** `RULING_G4_CONTROLLER_FIRST_v2_2026-10-04.md` (Director-ruled; supersedes v1).
**Diagnostic:** `DIAGNOSTIC_G4B_CONTROLLER_RELATIONS_v2_2026-10-04.md` (v2 corrects v1's D3).
**Trigger:** `REVIEW_RING9_CARRY_VC33_V7_KAGGLE_2026-10-04.md`. On level 3, G4-B and G4-C took 24 actions and about 163 minutes of Duck time, and certified nothing.
**Base:** `ec8554d` (R9-R23), branch `r9-r20-level-entry`. This seat is the only one working on that branch.
**Altitude:** architectural, ruled by the Director. D18 and the R-8 refusal are code-level, under existing rulings.

## What it builds

**D18 · Lever states are named from the level's own boards.**
- **The problem.** v7's card read `UNRECORDED` in all 1,947 `state_now` fields. A state was only named when one press rewrote the whole region, and on this level no press ever did.
- **The source.** New module `level_record.py`. It walks the level's lossless record (`transition_index`) backward from the current board, which rebuilds every board the level has shown exactly. Each region's states are the distinct contents it has shown, numbered in the order first seen: S0, S1, and so on.
- **The effect.** On v7 at t140, all 7 levers now carry a named state.

**D19 · G4-B is certified by the controller from the record (rulings G-1 and G-2).**
- **The answer.** New module `record_relations.py`.
  - It reads every recorded press of a lever on the level: which regions it changed, and whether anything else changed outside the counter mask.
  - A click counts as a press of a lever only at the lever's recorded click site, or on a cell of its own object (the G3 entity ledger). It never counts at a cell of the lever's effect region. An early draft counted region cells, and so wrongly attributed G3's clicks on other objects inside a lever's region to that lever. On v7 that came to 9 false presses, and the true count is 44.
  - It renders one relation per lever, citing the transitions behind it.
  - It reports levers that share a region separately: on v7, E0010 with E0011 and E0012 with E0013.
  - It then reports regions that change each other, and one-way reaches.
- **How the answer is accepted.** The controller submits it as `LEVER_RELATIONS_FROM_RECORD`. The gate derives the answer again itself and accepts it only if the two agree.
  - A stale `answer_id` is refused.
  - A replayed answer with no id is re-derived.
- **Duck's path.** Duck's prediction and description path is unchanged. It is still used whenever a lever has no recorded press on the level.

**D20 · Duck's G4-B and G4-C turns have a budget that each level opens fresh.**
- The budget is `DuckTurnBudget`, in the new module `play_gate.py`, set by the named parameter `DUCK_G4_TURNS_PER_LEVEL`. The default is 3, and the environment variable `VIRELAI_DUCK_G4_TURNS_PER_LEVEL` overrides it.
- Every Duck turn begun on a G4-B or G4-C step is charged. The charge happens in `controller_turn.duck_turn_allowed`, before the model is called, so turns that are rejected or cut off count too.

**D21 · A spent budget closes the gate UNRESOLVED.**
- When the next Duck turn would go over the budget, the gate Duck would have been woken for closes `UNRESOLVED`. It is a declared end, and it emits whatever is certified.
- G4-C contradictions still reopen G4-B while budget remains. The controller then re-certifies G4-B at once from the larger record, with no Duck turn, so each round costs exactly one Duck turn.

**D22 · Normal play after the gates.**
- **The gate.** After G4-C closes, the new gate `PLAY-NORMAL` opens. The same happens on any gate with no legal move (`controller_turn.rest_if_no_legal_move`), which used to idle until the A2 watchdog stopped the run.
- **How Duck acts.** Duck chooses any available action, one per capability, with every certified product on the card: lever states, the record's relations, the counter budget and mu.
- **What keeps happening.**
  - The gates keep recording, through the G3 entity ledger and the record tier.
  - A level change opens the next level's ladder with a fresh budget.
  - Each play transition is receipted `FREE_PLAY`, and a level won in play is frozen with `win.receipt: FREE_PLAY` (ruling R-2).
  - The mu return runs once each time the ladder comes to rest on a new set of products.
- **Several actions per turn.** Within one turn, Duck may take several actions in play, each through its own capability. Ruling R-1 allows this in free play.

**R-8 · Known no-ops are refused, and the refusal says who refused.**
- In play, an action that already changed nothing from the exact same masked board is refused. The message reads: "Blocked by the harness, not the game: this action changed nothing on this same board at t…".

**Card fit (axiom A6).**
- **G4-C card.** It now shows the compact lever rows first, then the relations with claims cut to 90 characters, then the last test. The description moves to the end of the card's priority order, and it is in the world model anyway.
- **Measured on v7 at G4-C:** 7,255 characters, subject slot 1,911, nothing over budget.
- **Measured on the play card:** 7,472 characters, nothing over budget.

**Ratchet compensation.**
- `virelai_gates.py` needs 7 new lines (the play gate's registration, its build, the forced-play route and the R-8 hook).
- The dead `_lever_class` function, which nothing anywhere references, is removed (16 lines).

## Tests

**New: `tests/test_r9_r24_g4_controller_first.py`, 6 tests.** They are driven on the v7 run's own record, as it ran live: fixture `vc33_kaggle_carry_v7_record.json.gz`, 165 transitions, sha256 `5f276f4f…b76a3`. Duck's recorded G4-B and G4-C answers are withheld. Duck's G4-C tests are written from the card's own template. Their outcomes are stand-ins (a press that changes nothing), and each is marked as such.

| Test | Pins |
|---|---|
| `test_d18_the_card_names_every_lever_state_from_the_levels_own_boards` | D18 |
| `test_d19_the_controller_certifies_g4b_from_the_record_and_the_gate_rederives_it` | D19: controller-owned; stale id refused; shared regions `[[E0010,E0011],[E0012,E0013]]`; E0013's relation cites t89 and t123; the ladder moves to G4-C |
| `test_d20_d21_duck_has_a_per_level_budget_and_a_spent_budget_closes_unresolved_without_a_loop` | D20, D21: 3 charged rounds; each contradiction reopens G4-B and is re-certified; the 4th turn closes G4-C UNRESOLVED; the ladder rests in play, legal |
| `test_d22_after_the_gates_duck_plays_normally_and_the_harness_labels_a_known_no_op` | D22 and R-8 |
| `test_d22_a_level_won_in_play_is_receipted_free_play_and_the_next_level_opens_its_own_ladder_and_budget` | D22, D20 per level |
| `test_d22_a_gate_with_no_legal_move_rests_the_level_in_play_and_mu_is_checked_once_at_rest` | D22 forced rest; the mu check runs once per rest |

**Fail-first:**
- At `ec8554d`, all 6 fail: collection fails, because the modules don't exist.
- **Each fix reverted alone:**

| Fix reverted | Tests that fail |
|---|---|
| D18 | 2 |
| D19 | 4 |
| D20/D21 | 3 |
| D22 (play gate) | 4 |
| R-8 | 1 |
| Forced rest | 1 |

**Superseded expectations, updated.** Each of these encoded the old end of the ladder or the old state numbering.
- `test_g4c_law`, `test_r9_r15_replay_fidelity`, `test_r9_r17_level_freeze`: a closed ladder used to end the run with a planned stop. It now hands the level to `PLAY-NORMAL`.
- `test_g4b_relations`:
  - At G4-B, the controller now owns the step.
  - States are numbered from the level's boards.
  - The production end-to-end test is rewritten for the ruling. The live ft09 actions still repeat exactly. G4-B is answered by the controller from the record, G4-C stays within Duck's budget, then Duck plays with `FREE_PLAY` envelopes. The run replays from its artifacts, with the same certified relations.
- `test_memory_m1` and `card_duck.py`: the card-only stress Duck stops when it reaches `PLAY-NORMAL`, and the ladder's gate list now ends with it.

**Suite (cloud, Python 3.12):** 535 passed, 1 skipped, 0 failed: R9-R23's 529 plus the 6 new tests. `test_g4b_relations.py` and the R9-R24 file were re-run after the last change, which made the answer id rest on transitions rather than evidence ids, so that a replay gives the same id: 17 passed. ruff is clean on every changed file.

**Ratchet (non-blank, non-comment lines):**

| File | Before | After | Change |
|---|---|---|---|
| `virelai_gates.py` | 5,353 | **5,344** | −9 |
| `g4b_gate.py` | 366 | 409 | +43 |
| `g4c_gate.py` | 258 | 269 | +11 |
| `g4_relations.py` | 307 | 310 | +3 |
| `controller_executor.py` | 351 | 363 | +12 |
| `controller_turn.py` | 179 | 203 | +24 |
| `life_record.py` | 115 | 120 | +5 |
| `level_model.py` | 99 | 101 | +2 |
| `level_record.py` | new | 118 | |
| `record_relations.py` | new | 126 | |
| `play_gate.py` | new | 201 | |

## Pre-flight

`tools/check_g4_controller_first_from_record.py RECORD 141` replays the v7 record, as it ran live, to G4-B and reports the result.

| Source | G4-B owner | Lever states | Next gate | Duck budget used | Exit |
|---|---|---|---|---|---|
| **R9-R24** | CONTROLLER (certified_by RECORD) | all 7 named (S2 to S7) | G4-C | 0 | 0 |
| **`ec8554d`** (v7's source) | DUCK ("the next prediction, or the description of the lever set, is Duck's") | all 7 `UNRECORDED` | G4-B, waiting for Duck | n/a | 1 |

## What the next vc33 run should show

**Levels 1 and 2.** As in v7, until the first G4-B.
- Level 2 was won during G4-A, so G4-B never opened there.

**Level 3.**
- G3 and G4-A run as in v7, through t140.
- G4-B is then answered by the controller, with no Duck turn.
- G4-C gets at most 3 Duck turns, and closes COMPLETE or UNRESOLVED.
- Then Duck plays level 3 normally until it wins, dies, or the run ends.

**Hypotheses, not findings:**
- The 3-hour clock is no longer the limit at G4. Level 3's G4 should take minutes, not hours.
- In play, the limits are the action budget (200, with 140 used before G4-B in v7) and the level's own move counter (about 64 on level 3). v7's study used that counter up once (GAME_OVER at t144), so play may start in a later life.
- Whether play wins level 3 is open. Nothing in the ladder yet aims at the win (friction F3), so play is Duck's own search, informed by the certified map.

— Claude, Alpha build seat, 2026-10-04

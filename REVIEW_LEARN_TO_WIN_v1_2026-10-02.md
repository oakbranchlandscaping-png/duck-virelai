# Review: "Learn to win": canon, repo, and outside machinery (v1, 2026-10-02)

**Author:** Claude (Alpha build seat), signed. Read-only review. Nothing built; nothing committed by me.
**Asked by the Director (2026-10-02):** "review 'learn to win' within the repo and project files. Let's make this our main focus now, pulling from outside notebooks where applicable."
**Repo at:** `e09dfbe` (duck-virelai `main`). Ring 9 source under `variants/ring9-cybernetic-gates/ARC3-Inference/` (`R9:` below).
**Tags:** [OBS] = read at the cited file:line; [REPORT] = an author's own claim; [HYP] = my inference.

---

## 0 · Headline

1. **Learn-to-win is already ratified canon. It is not a new idea to justify.**
   - `SPEC_SOLVER_LOOPS_v2` §7: "A win, once observed, is described in the grammar's own language, a predicate over the object list." Tier-1 falsification: "the win-predicate from level N is a live, killable hypothesis at level N+1." [OBS, project KB]
   - `SOLVER_BLUEPRINT_v3` §6 puts falsification behind the win-wall and names the entry point: "falsify the win description." [OBS]
   - The vc33 level-1 win is observed, recorded and frozen, so **the win-wall is crossed on vc33.**
   - The Director's instruction today is the plan-level ruling that `MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1` §5 item 4 left owed ("plan-level; Apex"). Record it as such.
2. **The repo has about half of it built, and nothing consumes that half.** The win is recorded in two places: the observer's capsule and lesson, and the gate machine's `LevelModel.win`. A narrow separator exists, written against the old Ring 8 region vocabulary. There is no win explanation in gate terms, no goal, and no grading at level N+1.
3. **The best outside machinery for this exact task is JustAdev742's goal-predicate DSL** (Apache-2.0, `8b8a728`). It contains:
   - contrastive induction (true at every win, false at every earlier frame);
   - a relational vocabulary;
   - a colour-free lift across levels;
   - re-instantiation on the new level;
   - satisfied-without-win falsification;
   - a distance-to-goal measure.

   It is close to a port of the whole middle of our design. It lacks our referee, gate-certified terms, and sequencing ("then"), and the authors switched its goal knobs off in their champion. [OBS, REPORT]
4. **Hard blocker: level 2 cannot be played.** The carry-vc33-v2 run deadlocked at level 2's G1 (D1 to D3, code-level, reproduced offline; `REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md`). Nothing about a carried goal can be graded until that is fixed. It is rung zero of this campaign.

---

## 1 · Canon: what is already law (project knowledge base, highest versions)

| Canon | What it fixes |
|---|---|
| `SPEC_SOLVER_LOOPS_v2` §7 | The win is written as a predicate over the object list. Two falsification tiers: within a game (the predicate from level N is killable at N+1) and across games (only machinery transfers). |
| `SOLVER_BLUEPRINT_v3` §6 | Falsification waits behind the win-wall. Its natural entry is "falsify the win description." |
| `SOLVER_STRATEGY_v1` §4.2 | Phase 2 = "deduce the win as a predicate over the object list and plan to it", beginning "the instant Phase 1 completes there". The dev-set order: vc33, ft09, lp85, sp80, as66, ls20. |
| `CYBERNETIC_TARGET_TREE_v1` §6–7 (repo) | Dormant `Observed Win Explanation` target; `ObservedGoalLaw` must cite an actual terminal transition; next level gets a `TransferredGoalHypothesis`. The loop: test transfer, specialise, translate, plan, observe. |
| `GATE_THESES_v3` G8 / G9 (repo) | Never guessed before observed; preserved whole; explained in the learned grammar. Every carried law is preserved, specialised, reopened or rejected: "nothing transfers silently." |
| `DOCTRINE_WORLD_MODEL_TERMINUS_v1` (repo) | Natural language is the projection layer: each clause of the explanation cites a gate product. The predicted signature: **later levels collapse toward near-free deduction, the front-loaded action curve.** This is prereg v2's H0. |

The Director's refinement today adds one thing canon does not yet say explicitly: **each win refines the win condition.** Wins generalise it, satisfied-without-win states specialise it, and missed predictions kill it. The condition can be compound and ordered ("match, then navigate"). It extends Tier-1; it does not contradict it.

---

## 2 · Repo: what exists, by link of the chain [OBS at `e09dfbe`]

| Link | Status | Where |
|---|---|---|
| Vocabulary (G0–G4C) | BUILT. Levels 1 and 2 of vc33 and ft09 are live-proven up to G4.x. | `virelai_gates.py`, `g4*_gate.py`, `memory_store.py` |
| Life record (deaths and lives) | BUILT (R9-R16) | `life_record.py`; budgets certified by G2 (`card_builder.world_budgets`) |
| Level freeze | BUILT (R9-R17) | `level_model.py`. The gate-side win record holds the winning transition, the action, the acted lever, and the earlier same-action failures ("context mattered, UNTESTED"). |
| Lever carry to the next level | BUILT (R9-R18), live-frozen but ungraded | `carry.py`: identity by type, a prediction frozen at entry, graded by the level's own probes |
| Win capsule (observer) | BUILT | `virelai_win_capsule.py`: level root, attempt root, pre-win frame, winning render (layer `len-2` when the level switches inside the step, `:85-90`), successor spawn, each with a SHA |
| Level lesson (observer) | BUILT, not consumed | `virelai_lessons.py::LevelLesson`: boundary, established, contrasts, transfer_clauses |
| Win separator | PARTIAL | `compile_post_win_grammars.py:_minimal_separator` (`:101-111`), called by `virelai_lessons._object_win_explanation` (`:303-343`). It finds the smallest set of up to 3 regions whose integer counts tell the pre-win state apart from every **earlier failure of the same action**. Regions come from the Ring 8 semantic library (`_known_regions`), **not from gate products.** Its status is honest: "candidate necessary context … not a proven cause." |
| Win explanation in gate terms (G8) | **NOT BUILT** | — |
| Goal from the explanation, frozen at next-level entry (G9-B goal) | **NOT BUILT** | — |
| Refinement ledger across wins | **NOT BUILT** | — |
| Firewall | Holds | `tools/live_level_carry_gate.py` hard-codes one world's winning clicks; it is excluded from shipped source, and no solver code imports it (`MINE_CROSS_LEVEL` §3; `UPLOAD_STATUS_RING9_CARRY_VC33_V1`). |

**Phase-sovereignty note.** `level_model.py:8` says the gate machine builds its win record "never from the observer's win capsule: the belief state is the only brain." The explanation must therefore be computed inside the gate machine, from its own record. The capsule is only a cross-check, as `MINE_CROSS_LEVEL` item 3 already proposed.

**The blocker** (`REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md`):
- **D1:** a post-action metadata refresh unsettles the pointer ego that is born inside the winning action's recording.
- **D2:** the A2 watchdog does not treat that wait state as illegal.
- **D3:** replay omits the refresh, so offline tests could not see D1.

Level 2 idled for 3 hours. All three faults are code-level. Until they are fixed, no level-2 evidence exists for any carried goal.

---

## 3 · Outside machinery, ranked for this task

### 3.1 JustAdev742 `arc3/dsl.py` (Apache-2.0, `8b8a728`, 2026-09-29): the primary port

| Function (file:line) | What it does | Our use |
|---|---|---|
| `goal_predicates` (`dsl.py:1597-1688`) | Candidates true at the final frame of every won level and false at **every earlier frame** of those levels | The broad contrast set. Ours is the narrow, same-action one. |
| Relation vocabulary (same function) | `none_left`, `count`, `aligned`, `all_same_colour_as`, `overlap`, `touch`, `same_box`, `same_columns`, `same_rows`, `inside`, `shape_matches`, `vanish_shape`, `avatar_inside`/`avatar_touch`; universal `every_<rel>` | Candidate relation set, re-keyed onto certified entities (§4) |
| `goal_signature` (`:1744-1754`) | A colour-free lift: (kind, whether the two arguments are equal) | **Generalise** across wins |
| `instantiate_goals` (`:1757-1793`) | Re-instantiates lifted kinds on a new level's frame, dropping any already satisfied ("a level does not start won") | The goal frozen at level entry |
| `goal_progress` (`:1914-1953`) | Ranks live hypotheses by distance; **marks a hypothesis falsified when it came true at a frame of this level without the level completing** | **Specialise** and **kill** |
| `goal_distance` (`:1830-1897`) | Cheap geometric distance to satisfaction | A progress measure for planning, later |
| `goal_candidates_dual` (`:1956-1970`) | Evaluates over both compound and plain-component frames | Lesson 0015: goals need plain perception |

**Their evidence [REPORT, `docs/status.md:315-316, 331-345`]:**
- Level-1 candidates on 10 of 13 games, holding on 10 of 15 later levels (11 with colour-free kinds).
- The true goal was ranked first before the win on both recorded replays that solved level 2.
- On a human recording, a consistent predicate held on 7 of 7 levels, after the perception fixes of lesson 0015.

**Against:**
- A goal-directed explorer was "measured, not kept" (15 → 14 levels).
- `goal_forall` and `goal_lifted` are **off in their champion** (`status.md:312-314`).

The machinery induces goals well offline. Advisory goal text has not moved their score. [OBS of their docs]

**What they lack, which is ours to add:**
1. **Terms certified by a referee.** Their entities come from a tracker; ours must come from gate products: certified levers and their states, the counter mask, ego.
2. **A referee that admits or kills.** Their goals are advice shown to the model ("code-computed" text). Nothing blocks progress or forces revision.
3. **Ordered compound goals ("then").** They have none.
4. **Action-gating robustness.** Their lesson 0016 notes that a board can satisfy the goal without ending the level when the win check is gated by action kind. Our narrow contrast (same-action failures) is robust to that by construction; their broad contrast is not.

### 3.2 JustAdev742 `perception.terminal_layer` (lesson 0017)

The winning frame is the layer before the level switch, not `layers[0]`. Our capsule already takes `len-2` when the switch happens inside the step (`virelai_win_capsule.py:85-90`), which agrees with their rule on their examples [HYP]. Their rule also handles a switch still pending at the end of the step. That is a small port; check it against our capsule with a toy test.

### 3.3 Others

- **`cognitive-rungs` `extract_win_condition`:** no licence, so no port. Cite it as prior art for the initial-versus-solved diff.
- **Lord Han Solo's strategy audit:** the protocol text for a prediction followed by a comparison. Our referee replaces it, so no code port.
- **Frontier playbooks (Retrodict release, PRO-LONG):** already the reference standard in prereg v2. Their prose win explanations are what our G8 output gets graded against, blind.

### 3.4 Firewall and exposure declarations (for the Director)

- **JustAdev742's lesson 0016 was derived by reading the game engines' source** ("tracing the win and lose checks in the source of all 19 dev games"). Its priors are therefore engine-source knowledge: goal kind constant per game, target drawn on screen, the catalogue of goal kinds. **Recommend: port no prior from lesson 0016 as machinery.** "Goal kind is constant within a game" may enter only as a hypothesis our own wins must earn. The relation functions in `dsl.py` predate lesson 0016 and are generic geometry; they are portable.
- **I read a docstring in `dsl.py` (`goal_signature`) that names vc33's level-1 and level-2 win kind.** vc33 is a documented dev-set world, not held out. Still, I am now contaminated about vc33's win kind, and so is anyone who reads that file. Consequence: a vc33 result can show the machinery works, but it cannot be evidence of generalisation. That claim needs the held-out worlds (`lp85`, `s5i5`, `su15`) under prereg v2.
- Also: the example the Director gave on 2026-10-02 ("match … then navigate") closely mirrors a row of the quarantined answer key. The relation set must be fixed from the certified vocabulary before any win record is opened, not from known games.

---

## 4 · Synthesis: the learn-to-win design (proposal, for ruling)

**G8-EXPLAIN** is a gate target opened by the observed-terminal event; it runs once the level's ladder has closed.
1. **Describe (Virelai, deterministic).** Render every recorded state of the level as a row over certified terms:
   - levers and their orbit states (G3, G4);
   - counter-masked object relations computed by the ported relation functions, keyed on **certified entity types, never raw colour**;
   - ego relations, when G1 is embodied.
2. **Contrast (Virelai).** Two contrast sets:
   - **strict:** pre-states of earlier uses of the winning action (today's `_minimal_separator` logic, re-keyed);
   - **broad:** every earlier state of the level, with satisfied-without-win treated as a counterexample only when a winning-class action was taken from that state.

   Output the survivors: conditions true at the win and false across the contrast.
3. **Explain (Duck, one bounded question).** "State the win in these terms only; name what they do not explain." Residue is recorded, not filled.
4. **Referee.** Admit the explanation only if it uses card terms only, holds at the win, fails across the contrast, states a state condition rather than the bare last click, and declares its residue. Otherwise it is rejected with the reason.

**G9-B GOAL-CARRY** follows the lever-carry pattern: frozen at entry, graded by the level itself.
1. **Lift.** Each surviving condition, lifted colour-free (the `goal_signature` pattern).
2. **Instantiate.** On level N+1 by type identity (the `carry.py` pattern), dropping any already satisfied at entry.
3. **Freeze.** Before any level N+1 action: the ranked surviving set, with Duck's pick first.
4. **Grade, using level N+1's own record.**
   - **Kill:** the level is won while the condition is false.
   - **Specialise:** the condition came true and no win followed although a winning-class action was taken. The missing conjunct or stage is opened as a target.
   - **Reconfirm:** the win arrives with the condition true.

**The refinement ledger.** It is cumulative across wins:
- **generalise:** shared parts survive the lift;
- **specialise:** a satisfied-without-win state adds a conjunct, or a stage ordered by when each part became true in the life record (the "then");
- **kill.**

Every operation cites the transitions that caused it. It renders as one sentence whose clauses each cite a gate product, which is the doctrine's projection layer.

**Out of scope for this slice:** *planning toward* the goal (G7 or the Push). This slice explains, carries and grades. Acting on the goal is the next slice, gated on this one's canary.

---

## 5 · Proposed rungs (in order; nothing built until the Director confirms)

| Rung | What | Exit (observable) |
|---|---|---|
| **LW-0** | Fix D1–D3: the pointer ego is immune to metadata refresh; A2 treats a no-probe, no-template wait as illegal; replay applies the refresh. The v2 live record becomes a fixture. | The v2 record replays to **G2 on level 2** offline. Then a live vc33 run reaches level-2 clicks (the Director runs the canary). |
| **LW-1** | Transcribe the relation functions and the lift and instantiate machinery from `dsl.py` (Apache-2.0, provenance header, re-keyed to certified entities), plus the terminal-layer check. Tests use toy frames first and fail before the build. | A toy-world suite: a separator found; a lift across two toy levels; a satisfied-without-win case specialises. |
| **LW-2** | G8-EXPLAIN in the gate machine (contrast, Duck's question, referee), offline on the vc33 level-1 record with the machinery frozen and committed first. | An admitted, or honestly rejected, explanation citing gate products and residue. Graded on fidelity (clauses match the cited laws), not on whether it is "right". |
| **LW-3** | G9-B GOAL-CARRY: freeze at level-2 entry; grade from level 2's record. | A preregistered verdict per candidate (reconfirm, specialise or kill) from a live vc33 level-2 run. |
| **LW-4** | The refinement ledger, including ordered stages | A second win updates the ledger, citing transitions |
| **LW-5** | Generalisation: ft09 (dev), then held-out worlds under prereg v2 | The H0 learning curve `a_n / b_n` on held-out worlds, with repeat runs |

---

## 6 · Rulings owed (Director)

1. **Learn-to-win is the main campaign, and "the win is recorded only" (2026-10-01) is lifted.** Confirm, so the record shows the plan-level ruling.
2. **LW-0 ownership.** The D1–D3 fix touches `virelai_gates.py` and replay; Sol is building NAV in parallel. Who takes LW-0?
3. **Lesson 0016's priors:** hypothesis-only, never machinery (recommended).
4. **The broad contrast:** adopt it with the action-gating guard (recommended), or keep the strict same-action contrast only.
5. **Carry the full surviving set, ranked** (consistent with your 14:33 statement).
6. **vc33 is a machinery lab, not evidence of generalisation** (given the exposure in §3.4). Generalisation claims wait for the held-out worlds.

— Claude

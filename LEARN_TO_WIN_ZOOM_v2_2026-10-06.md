> **Banner (Claude, 2026-10-07):** §1's newborn-object reading and ruling 3 are corrected by `SPEC_PHYSICS_GRAMMAR_v1_2026-10-07` §4. E0078 and E0079 are most likely identity churn from the G3 ledger's continuity, not newborn objects. The rung order is revised in that document's §7 (LW-0, noun continuity, comes first).

# Learn to win: zoom-in, v2: the win as a sentence of nouns and verbs (2026-10-06)

**Type:** `LEARN_TO_WIN_ZOOM` · **v2** · **2026-10-06**
**Author:** Claude (Alpha build seat), signed. Read-only. No code was changed.
**Supersedes:** `LEARN_TO_WIN_ZOOM_v1_2026-10-05.md`, which stays in place as history. §§1–4 of v1 (the question, the offline lab on the v7 record, and its findings) still hold and are not repeated here. This version replaces v1 §5 (the rung sequence) and §6 (the rulings).
**Swept at:** `main` `b1a4d71`.
**Tags:** [OBS] = read or measured; [HYP] = inference; [DIR] = the Director's statement or agreement.

## 0 · What changed since v1 [OBS]

- **The merge is on `main`.** Main fast-forwarded to the single tree at `f86d6ef`, and SUB-1 submission mode landed at `d751a5b` (Mac floor 617 passed, 1 skipped).
- **The vc33 v8 review is filed** (`d0635e7`). R9-R24 works live: G4-B was certified from the record with no Duck turn, and G4-C closed UNRESOLVED on budget. The score is unchanged at 1.51. One finding bears directly on this document: **"play does not aim at the win."**
- **The record format is still `virelai-recorded-world-v1`** (`record_replay.py:14`). `e8d1f92` changed only the replay contracts for G0-start records. LW-A is still needed.
- `DIRECTIVE_COMPETITION_ENDGAME_v3` (a DRAFT, not ratified; v2 binds) names a per-game glass-box world report that states the win condition "where observed". If it is ratified, learn-to-win is that line's source.

## 1 · The framing, agreed (Director, 2026-10-06)

> "We expand past just levers. That is why we have the full ARC grid multiverse ontology, the archetype axioms, and the roles of the semantic library. Nouns and verbs are learned to write the sentence of a win." [DIR]

This is the canon's own design, not a new one. CONCEPT_VIRELAI_SOLVER_v2 §4: nouns are roles, verbs are mechanics. SPEC_SOLVER_LOOPS_v2 §6–7: a win is described in the grammar's language as a predicate over the object list. SOLVER_BLUEPRINT_v3 §4.3: nouns and verbs are derived, not stored. FOUNDATIONAL_ARCHETYPES_v2: REACTIVE-DRIVEN's subtree includes "terminal candidacy … a win-predicate ingredient".

**The necessity (Director) and its scope (agreed):**
- A win is caused by the agent's actions. So at least one noun in every win sentence is **EGO, LEVER or REACTIVE-DRIVEN**. In click mode, with no ego body, a non-lever object that changes on the way to a win is driven by a lever by default. [DIR]
- Other nouns in the sentence need not be: an **ENVIRONMENTAL FORCE** (the agent's part is timing), or an **INERT reference** (the target the driven object must reach). [agreed]
- The necessity sets the prior. **The record certifies the relation** (evidence before belief): which lever drives which object.

**The verb's form, from the lab [OBS → HYP]:**
- At the v7 level-2 win, four non-lever entities (E0078, E0079, E0002, E0003) differed from the two earlier boards **while the lever states were identical**. So their states are not a function of current lever states. [OBS]
- If they are driven, the response follows **press history**: a press changes them a step, and the lever can return while the effect stays. [HYP]
- So the verb must be a **transition law** (press → delta, accumulated over the level), not a state map (lever state → object state). A state map would fail on exactly this win.

## 2 · What exists versus what is missing [OBS]

| | Gate machine (`inference/framework/`) | Elsewhere |
|---|---|---|
| Nouns | EGO, COUNTER, LEVER (with mu), NAV ground and wall | `virelai_semantic/compiler.py` (observer side) has role strings, and "does not infer mechanisms, objectives, or win causes yet" |
| Verbs | Lever orbits, controller-certified record relations, and G4-C laws: levers only | — |
| REACTIVE-DRIVEN, ENVIRONMENTAL FORCE, INERT | Not built (G5 and G6 are specified only) | — |
| The board at the win | Not in the record format | The observer's win capsule |

Phase sovereignty: the gate machine reasons from its own record. The semantic library's definitions may be reused, but its roles cannot be read across. Roles are certified by the gates.

## 3 · The rung sequence (replaces v1 §5)

| Rung | What | GPU | Exit |
|---|---|---|---|
| **LW-A** | The record keeps the board at the win (`virelai-recorded-world-v2`). Regenerate the vc33 v6/v7/v8 fixtures from their run artifacts. | none | A replayed record yields the winning board, matching the capsule's SHA |
| **LW-B1 · nouns** | For every non-lever G3-ledger entity that changes on the level, certify its drivers from the order of presses in the record. In click mode the prior is driven. An entity that changes with no press before it is a candidate force. Entities that never change are candidate INERT references, not certified, because G6 is not built. Anything else is declared unroled, never forced into a role. Newborn entities enter when the ledger records them. | none | On the v7 record, every entity that differs at the level-2 win carries a certified role or a declared "unroled" |
| **LW-B2 · verbs** | Fit each driven entity's response as a transition law (press → delta, accumulated over the level), using the same zero-contradiction fitting the controller already uses for lever relations | none | Every certified driven role carries a response law with no recorded contradiction, or is declared without one |
| **LW-B3 · relations** | Generic geometry **between** role-bearing nouns: position, extent, containment, adjacency, alignment, shape match. Keyed on role and entity, never on colour. Fixed before it is run on any win. | none | On the v7 level-2 win, a separator exists in role, verb and relation terms, strict and broad. Otherwise the gap is declared, naming the missing noun or verb. |
| **LW-C** | The referee (W-2): strict and broad contrasts, the action-gating guard, the novelty flag, refusal of vacuous candidates | none | Planted toy cases, plus the v7 level-1 and level-2 wins replayed |
| **LW-D** | The two-win lab (W-4, W-6): explain level 1; freeze its survivors at level-2 entry; grade them against the recorded level-2 win; generalise, specialise or kill | none | A preregistered verdict per candidate, and a two-win ledger |
| **LW-E** | Live level-3 test (W-7): the ledger's goal is frozen at level-3 entry and graded live. The Director runs the canary. | one canary | A verdict before the level-3 win |

`ACT_ON_GOAL`, the answer to v8's "play does not aim at the win", stays gated on LW-E.

## 4 · Rulings

**Taken (Director, 2026-10-06):** the framing in §1, and LW-B reframed as nouns (B1), then verbs as transition laws (B2), then relations between nouns (B3).

**Still owed:**
1. **Go to build LW-A and LW-B**, offline, on `main`, with a window for shared-file writes (LW-A touches `record_replay.py` and the fixture generator).
2. **Where the winning board comes from:** the record (recommended) or the observer's capsule.
3. **Newborn objects:** schedule them now (recommended, since E0078 and E0079 may be newborn) or declare the gap.

## 5 · Firewall

- Roles are keyed on behaviour in the record: order of presses, deltas, persistence. Never on colour, position or a world's name.
- The role set comes from FOUNDATIONAL_ARCHETYPES_v2 and the relation set from generic geometry, both fixed before any win record is run.
- vc33 is a dev world whose win kind I have read about elsewhere (declared 2026-10-02). Probes print only counts and entity IDs, and I do not view frames. The vc33 results show the machinery works. Generalisation waits for the held-out worlds.

— Claude

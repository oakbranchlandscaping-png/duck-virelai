# Spec: the physics grammar: its parts of speech, its sentences, and where each is built (v1, 2026-10-07)

**Type:** `SPEC_PHYSICS_GRAMMAR` · **v1** · **2026-10-07**. A new type-name; no earlier document of this type exists in the repo or the project.
**Status:** DRAFT for the Director's ratification. §6 is an architectural question for the CE seat or the Director.
**Author:** Claude (Alpha build seat), signed. Read-only: no code changed. One offline probe was run on the v7 record in scratch (§4).
**Asked (Director, 2026-10-07):** "Let's continue to formalize this. We can't have an accurate physics grammar unless we can recognize and label all parts of speech. This was the goal of the semantic library."
**Tags:** [OBS] = read or measured; [HYP] = inference; [CANON] = stated in a canon document.

**Formalizes, does not replace:**
- CONCEPT_VIRELAI_SOLVER_v2 §4 (nouns are roles, verbs are mechanics);
- SPEC_SOLVER_LOOPS_v2 §6–7 (the win in the grammar's language);
- SOLVER_BLUEPRINT_v3 §2, §4.3, §5 (the trail; derived, not stored; the nested taxonomy);
- SPEC_LEXICON_LIBRARY_v1 (the verb alphabet);
- FOUNDATIONAL_ARCHETYPES_v2 (the six archetypes);
- TARGET_SEMANTIC_LIBRARY_PLAYER_BRIEF_v1 (the dossiers, including DEPENDENT OBJECT and WIN EVIDENCE);
- AUDIT_PHYSICS_GRAMMAR_PORT_MATERIAL_v1 ("configurational win predicates" is the largest novel task).

CONCEPT_VIRELAI_SOLVER_v2 §9 records that "a dedicated SPEC for the mechanic layer is owed". This document covers part of that debt. Whether it discharges the debt is for the CE seat to rule.

**Doc finding [OBS].** None of the canon specs above (FOUNDATIONAL_ARCHETYPES, the nested taxonomy, SPEC_LEXICON_LIBRARY, SPEC_SOLVER_LOOPS) is in the `duck-virelai` repo. They exist as project documents only. Work orders that cite them must cite the project copy.

---

## 1 · The laws every word obeys

1. **Every word decompresses to cell deltas** (the Grounding Law). A word with no delta pattern under it is not a word.
2. **Every word class is total, with a residual.** As in the lexicon, an unnameable case lands in a named residual (UNROLED, DEFORM, AMBIGUOUS, UNATTRIBUTED). It never lands in a gap and is never forced into a class. **The residual rate is the coverage reading for that part of speech.**
3. **The vocabulary grows on witness.** A new word is split out of a residual only when the record forces it.
4. **Words are derived, not stored** [CANON, Blueprint §4.3]. They are recomputed from the record. A class change revokes and re-derives the role set [CANON, Blueprint §5].
5. **Game-free.** Words are keyed on behaviour in the record (deltas, order of presses, persistence, geometry), never on colour, position or a world's name.

## 2 · The parts of speech

| Part of speech | In the physics grammar | Decided by (observable) | Residual | Canon |
|---|---|---|---|---|
| **Proper noun** | One persistent object: a worldline, a G3-ledger entity | Continuity across frames | AMBIGUOUS (identity contest) | SPEC_WEAVE; the worldline is the object |
| **Common noun** | Its role: Band 1 (STATIC or REACTIVE) and a Band-2 set from EGO, COUNTER, LEVER, ENVIRONMENTAL FORCE, REACTIVE-DRIVEN, INERT, plus the structural GROUND and WALL | The archetype key over the delta pattern | UNROLED | Blueprint §5; FOUNDATIONAL_ARCHETYPES_v2 |
| **Adjective** | An attribute at a node: integer class, size, shape, extent, anchor, state label | Read off the settled frame | — (always computable) | TARGET brief §5 ("observed identity") |
| **Intransitive verb** | What one object did across one edge: STILL, MOVE, GROW, SHRINK, RECOLOR, BIRTH, DEATH, SPLIT, MERGE | The lexicon key ρ | DEFORM, AMBIGUOUS | SPEC_LEXICON_LIBRARY_v1 |
| **Transitive verb** | A mechanic: a subject (an action, a lever, the ego) makes an object do an intransitive verb. "Pressing L **moves** D." | Attribution from the record: the press came before the change, and ego and counter noise are excluded | UNATTRIBUTED change | SPEC_SOLVER_LOOPS_v2 §6; the controller-certified relations (`record_relations.py`) |
| **Reciprocal verb** | A coupling: two objects change jointly, for example a conserved transfer | Joint delta vectors | — | The mechanic layer, CONCEPT §3 |
| **Adverb** | How a verb acts: direction, magnitude, period, delay, saturation, determinism | Repetition of the same verb | UNKNOWN | TARGET brief §5.3, "transition law" |
| **Conditional clause** | When a verb applies: WHEN or IF a precondition holds | Agreement and disagreement between repetitions | "condition not yet known" | TARGET brief §5.3, "conditions" |
| **Preposition** | A relation between two nouns at a node: on, inside, overlapping, adjacent to, aligned with, same shape as | Generic geometry (QSR and RCC lineage), fixed in advance | — | AUDIT_PHYSICS_GRAMMAR §3 (contacts, relative positions, alignment) |
| **Quantifier** | Every, some, how many, over a role ("every driven object is …") | Counting over the role set | — | — |
| **Determiner** | This object (an instance) or any object of this kind (a type) | Instance ID or type signature | — | SPEC_SOLVER_LOOPS_v2 §7: instances reset at the level boundary, so only types carry |
| **Conjunction** | AND (all of these hold); THEN (ordered stages) | The referee: each stage is its own state sentence, in order | — | The Director's earlier examples ("match this area to that area, then navigate to that area") |

## 3 · The sentences

| Sentence form | Example shape | What it is |
|---|---|---|
| **Law** (transitive, indicative) | "Pressing LEVER a MOVEs DRIVEN b one step, when …" | A mechanic. Every clause decomposes to recorded deltas. |
| **State** (copular) | "DRIVEN b is ON INERT c"; "every DRIVEN object is ALIGNED WITH its partner" | A predicate over the object list at one node |
| **Win sentence** | A state sentence, or an AND or THEN of them | True at every observed winning board, false at the earlier boards (the referee). Falsified at the next level (Tier 1). [CANON, SPEC_SOLVER_LOOPS_v2 §7] |
| **Goal** (imperative) | "Make the win sentence true by applying these laws" | Derived from the win sentence and the laws. This is `ACT_ON_GOAL`: not built, and gated on LW-E. |

**The point of the grammar.** Laws say what the agent's verbs do to nouns. The win sentence says which state of the nouns ends the level. The goal follows from the two: choose the transitive verbs whose objects are the nouns in the win sentence. **Without nouns for the non-lever objects, the win sentence has no subject, and the goal cannot be derived.**

## 4 · Worked example: the v7 level-2 win in this grammar [OBS unless tagged]

Offline probe on `tests/fixtures/vc33_kaggle_carry_v7_record.json.gz`, driven through the gate machine as in `LEARN_TO_WIN_ZOOM_v1` §2, stopped at the transition before the level-2 win. Only entity IDs, relation names and counts were printed. No frames were viewed and no colours were printed.

**Proper nouns and their intransitive verbs (G3 ledger):**
- **E0002, E0003:** present all level, constant size (12 and 16 cells), each with STILL ×34 and **MOVE ×8**.
- **E0078, E0079:** 464 and 2,296 cells, both **born at t68**, one transition before the win.
- **Across level 2:** BIRTH 65 = DEATH_OR_DEFORM 65, and 22 of 42 transitions hold both.

**Transitive verbs (attribution from the record):**
- **Every one of E0002's and E0003's 8 MOVEs came on a press of a certified lever:** 2 on E0006 and 6 on E0007. They moved together each time.
- Presses of E0006 moved them on **2 of 4** presses, and presses of E0007 on **6 of 7**. Presses of E0004 (6) and E0005 (13) never moved them.

**What this says:**
1. **E0002 and E0003 are REACTIVE-DRIVEN by levers E0006 and E0007** in the record's own terms. This is the Director's necessity, now seen. It is still a candidate until LW-B1 certifies it.
2. **The verb is conditional.** The same lever press sometimes moves them and sometimes does not (2 of 4; 6 of 7). The grammar needs the conditional clause. The condition is not yet known; it could be a state of a lever, a limit, or a stop against something [HYP].
3. **E0078 and E0079 are not newborn objects. They are identity churn [HYP, strong].** Every birth on level 2 is paired with a death. Their sizes (2,296 cells is over half of a 64×64 board) look like ground regions whose shape changed when the movers moved. The G3 ledger names only STILL, MOVE and RECOLOR (`entity_observation.py:377-436`). Any GROW, SHRINK or DEFORM ends the old ID and starts a new one. **This corrects `LEARN_TO_WIN_ZOOM_v1` §3.3 and v2 ruling 3:** the noun problem is continuity under GROW, SHRINK and DEFORM, not newborn objects.
4. **The partial sentence this record supports:** "Pressing LEVER E0006 or E0007 MOVEs DRIVEN E0002 and E0003 together, WHEN [condition unknown]." The **win sentence is not yet writable.** It needs a preposition: where E0002 and E0003 stand relative to something else at the win. That is LW-B3.

## 5 · Where each part of speech exists today, at `main` `f333919` [OBS]

| Part of speech | Gate machine (`inference/framework/`) | Golden (`virelai_golden/`) | Semantic library (`virelai_semantic/`, observer side) |
|---|---|---|---|
| Proper noun | G3 entity ledger, continuity by exact key, MOVE or RECOLOR only | Weave worldlines with rejoin and occlusion | Reads golden roles |
| Common noun | EGO, COUNTER, LEVER (with mu); NAV ground and wall | `roles/`: ego_body, ego_pointer, counter, lever, ground, wall, mask | EGO, GROUND, WALL, COUNTER, LEVER, EGO_BODY, COUNTER_PROCESS |
| Adjective | Cells and integer; lever state labels (D18) | Substrate scan | Dossier "observed identity" |
| Intransitive verb | STILL, MOVE, RECOLOR, BIRTH, DEATH_OR_DEFORM, AMBIGUOUS | **Full alphabet** (`weave/verbs.py`: the nine verbs including GROW, SHRINK, DEFORM) | — |
| Transitive verb | Lever → its own region (G4 anatomy, orbits); controller-certified lever relations | `roles/lever.py` effects | `mechanics.py` lever mechanics; `typing.py` effect-channel types |
| Reciprocal verb | — | Joint transfer (push and mechanics) | `joint_transform.py` |
| Adverb, conditional | G4-C laws (0 of 11 supported on v7; UNRESOLVED on v8) | — | Effect-channel typing |
| Preposition, quantifier, determiner, conjunction | **None** | — | — |
| Win sentence | **None** (the win capsule records the boundary only) | — | TARGET brief §4.8 specifies it; the compiler "does not infer … win causes yet" |

**Reading:**
- The Director is right that the semantic library was meant to be this grammar. Its target brief specifies the DEPENDENT OBJECT dossier (drivers, response, terminal candidacy) and WIN EVIDENCE (pre-state, a labelled win hypothesis, and its falsifier).
- But it sits on the observer side, and the gate machine imports neither it nor golden [OBS: no import in `virelai_gates.py`, `record_relations.py` or `g4_relations.py`].
- The gate machine, the only certified side, has proper nouns with weak continuity, three common nouns, and lever-only transitive verbs. It has no prepositions and no sentences.

## 6 · The architectural question (for the CE seat or the Director)

**Where does the grammar live?**

- **(a) Recommended.** The **gate machine certifies the grammar**, and the **semantic library becomes its renderer** (the brief is a projection, as its own target brief already says: "the lower layers are necessary provenance"). Role definitions and the verb alphabet are **ported** from golden and the semantic library into gate-side certification (PORT default).
- **(b)** The semantic library is promoted to be the certifier, and the gates read it.

(a) keeps phase sovereignty: the gate machine reasons from its own record. It also keeps one certifier, consistent with "all data lands in one canonical library" [CANON, CONCEPT §3]. (b) would give the observer authority over decisions, which the R9 line has avoided throughout.

## 7 · Build order (revises the LW rungs of `LEARN_TO_WIN_ZOOM_v2`)

| Rung | Part of speech | What | Exit |
|---|---|---|---|
| **LW-0 · noun continuity** (new, first) | Proper noun | Port the golden weave's GROW, SHRINK and DEFORM continuity into the G3 ledger, with AMBIGUOUS as an abstention. **False joins are worse than missed joins** (AUDIT_PHYSICS_GRAMMAR "certified continuity"). | On fixed replays, each BIRTH and DEATH_OR_DEFORM pair is either joined under a named lexicon verb or kept apart as AMBIGUOUS. Zero false joins on a hand-labelled set, which the Director grades. |
| **LW-A** | (record) | The record keeps the board at the win | As in v2 |
| **LW-B1** | Common noun | REACTIVE-DRIVEN from attribution (first), candidate ENVIRONMENTAL FORCE, candidate INERT, GROUND; UNROLED as the residual | v7: E0002 and E0003 certified DRIVEN by E0006 and E0007, or the gap declared |
| **LW-B2** | Transitive verb, adverb, conditional | A press → delta law per driven noun, with its condition found or declared unknown | v7: a condition that explains E0006's 2 of 4 and E0007's 6 of 7, or "condition not yet known" |
| **LW-B3** | Preposition | Generic relations between role-bearing nouns, fixed in advance | v7 level 2: a separator in role, verb and preposition terms, or the gap named |
| **LW-C** | Quantifier, conjunction, THEN; the win sentence | The referee over a bounded sentence space | As in v2 |
| **LW-D, LW-E** | Determiner (type) | Carry across levels by type; the live level-3 test | As in v2 |

## 8 · Rulings owed (Director)

1. **Ratify the parts of speech (§2) and sentence forms (§3)** as the grammar's word classes, or amend them.
2. **Where the grammar lives (§6):** (a) the gates certify and the semantic library renders (recommended), or (b).
3. **LW-0 first:** noun continuity before driven roles, since a ground region renamed on every move cannot carry a role.
4. Still open from `LEARN_TO_WIN_ZOOM_v2`: go on LW-A and LW-B, and the record as the source of the winning board. That document's ruling 3 (newborn objects) is replaced by item 3 above.

## 9 · Firewall

- vc33 is a dev world whose win kind I have read about elsewhere (declared 2026-10-02).
- The probe printed only IDs, relation names, sizes and counts. No frames were viewed.
- The word classes come from canon and generic geometry, fixed here before any win sentence is searched.
- The vc33 results show the machinery works. Generalisation waits for the held-out worlds.

— Claude

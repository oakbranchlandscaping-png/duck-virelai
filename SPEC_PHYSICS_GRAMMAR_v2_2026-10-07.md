# Spec: the physics grammar: parts of speech, sentences, and where each is certified (v2, 2026-10-07)

**Type:** `SPEC_PHYSICS_GRAMMAR` · **v2** · **2026-10-07**
**Supersedes:** `SPEC_PHYSICS_GRAMMAR_v1_2026-10-07` (`884631d`), which stays in place as history. v2 is complete in itself.
**Status:** DRAFT for the Director's ratification.
**Author:** Claude (Alpha build seat), signed. Read-only; no code changed. Two offline probes were run on the v7 record in scratch (§5).
**Asked (Director, 2026-10-07):** "Sweep the project and repo for answers to your questions. Focus on the weave and the axiomatic archetypes. Pixel patterns and visual objects should become semantic roles with enough data."
**Tags:** [CANON] = a project or repo canon document says it; [OBS] = read in code or measured; [HYP] = inference.

## 0 · What the sweep changed from v1

The canon already answers most of what v1 asked. v1 was wrong or incomplete in six places:

1. **The mechanic layer has a spec.** v1 repeated CONCEPT_VIRELAI_SOLVER_v2 §9's note that it was "owed". `SPEC_MECHANIC_LAYER_v1_2026-07-22` (project) exists and governs transitive and reciprocal verbs.
2. **Quantifiers are canon.** `NESTED_TAXONOMY_SPEC_v5` §4 (the ∃/∀ law) states that composite claims aggregate under explicit quantifiers. Its per-tag table is declared owed.
3. **A target is not a primitive noun.** `NESTED_TAXONOMY_SPEC_v5` §6: "TARGET derives (a target is read from mechanics and the win-predicate, never a stored primitive)". v1's "INERT reference" noun is withdrawn.
4. **v1 called E0078 and E0079 "ground", which breaks No-null-class.** `SPEC_WEAVE_v1` §1, `RULING_BELIEF_HOME_LAYERS_v1` §4 and `SPEC_MECHANIC_LAYER_v1` §5 (the complement law) say a large field earns its status only from the measured coupling, never by size. v2 calls them **coupling-complement candidates** (§5).
5. **Where the grammar lives is settled by canon, not open** (§4).
6. **LW-0 is not new work.** It is an open item of a contract already in the repo (§6).

## 1 · The chain from pixels to roles [CANON]

The Director's sentence ("pixel patterns and visual objects should become semantic roles with enough data") is the canon's six-rung chain:

| Rung | What it is | Governing document |
|---|---|---|
| Cells | Integers at sites | `SPEC_SIGHTING_LEDGER_v3` |
| Visual object | The exact pair (cell set, integer). **Any change makes a different visual object.** Birth, move and death do not exist at this layer. | `RULING_BELIEF_HOME_LAYERS_v1` §1 |
| `###` worldline | The weave threads visual objects through time by the two-anchor cascade: a site-anchored holder (same cells, class churns) or a class-anchored mover (same class, cells move). It carries identity, never role. **"The weave earns the noun."** | `SPEC_WEAVE_v1` §1–3 |
| Verb stream | One lexicon verb per edge, a total function with residuals | `SPEC_LEXICON_LIBRARY_v1` |
| Mechanic | Marginals per object, plus couplings as edges between worldlines, measured as press-indexed joint delta vectors | `SPEC_MECHANIC_LAYER_v1` |
| Role | The archetype key: Band 1 (STATIC or REACTIVE) prunes the menu, and Band 2 is a set-valued, class-indexed tag from the six archetypes. Each archetype has a defining observable, an exclusion discipline and a subtree seed. | `NESTED_TAXONOMY_SPEC_v5`, `FOUNDATIONAL_ARCHETYPES_v2` |

**"With enough data" is the bucket law.** A role emerges when its bucket crosses its confidence predicate, and that emergence trips the archetype's subtree (`SPEC_SOLVER_LOOPS_v2` §3–5; `RULING_BELIEF_HOME_LAYERS_v1` §2, Layer 2). **Durable belief can live only on the `###`,** because only the worldline survives a visual object changing [CANON, BELIEF_HOME §1]. That is why noun continuity comes first (§6).

**Status note [OBS].** `FOUNDATIONAL_ARCHETYPES_v2` and `NESTED_TAXONOMY_SPEC_v5` each say "DRAFT — pending Director ratification" on their face. CONCEPT_VIRELAI_SOLVER_v2 treats them as canon. If a ratification record exists, I did not find it. Ruling 1 (§8) asks for it.

## 2 · The parts of speech

| Part of speech | In the grammar | Decided by | Residual | Governing canon |
|---|---|---|---|---|
| **Proper noun** | A `###` worldline (G3 entity) | The weave's correspondence | AMBIGUOUS, which abstains into `CANDIDATE_LINK` | `SPEC_WEAVE_v1`; `CONTRACT_G3_ENTITY_LIFECYCLE_v1` §1 |
| **Common noun** | The role set: Band 1 and Band 2 over EGO, COUNTER, LEVER, ENVIRONMENTAL FORCE, REACTIVE-DRIVEN, INERT | Each archetype's defining observable, taken in the lawful order: ego, then counter, then lever, then the rest | UNKNOWN (absence of evidence, never a leaf) | `FOUNDATIONAL_ARCHETYPES_v2`; `NESTED_TAXONOMY_SPEC_v5` §1–2 |
| **Adjective** | An attribute at a node: integer class, size, shape, extent, anchor, state label | Read off the settled frame | — | `SPEC_SIGHTING_LEDGER_v3` |
| **Intransitive verb** | STILL, RECOLOR, MOVE, GROW, SHRINK, BIRTH, DEATH, SPLIT, MERGE | The lexicon key ρ | DEFORM, AMBIGUOUS | `SPEC_LEXICON_LIBRARY_v1` |
| **Transitive verb** | A marginal attributed to a subject: "pressing L moves D" | Acted-member attribution after ego and counter subtraction | Unattributed residue, filed toward G5 | `SPEC_MECHANIC_LAYER_v1` §2, §4; `CONTRACT_G3_ENTITY_LIFECYCLE_v1` §2 |
| **Reciprocal verb** | A coupling: an edge between worldlines; a conserved transfer | Linear dependence with a stable coefficient; the complement is derived from the fit | A candidate (abstention) | `SPEC_MECHANIC_LAYER_v1` §4–6 |
| **Adverb** | Quality, bearing, magnitude, lag, period, repetition law, saturation | The archetype's subtree questions | Deferred, or "closed-by-probe" pending | `FOUNDATIONAL_ARCHETYPES_v2` §3, §5 |
| **Conditional clause** | When a verb applies: a state predicate, a clamp at a wall | A repetition-law divergence is a fork-witness. The residual is computed from geometry, never stored. | "condition not yet known" | `FOUNDATIONAL_ARCHETYPES_v2` §3–4; `SPEC_MECHANIC_LAYER_v1` §6 |
| **Quantifier** | ∃ or ∀ over members or over a role | The explicit quantifier is part of each claim's definition | — | `NESTED_TAXONOMY_SPEC_v5` §4 (per-tag table owed) |
| **Determiner** | This instance, or any of this type | Instances reset at the level wall; only types and rules carry | — | `SPEC_SOLVER_LOOPS_v2` §7; AUDIT_PHYSICS_GRAMMAR §4 |
| **Preposition** | on, inside, overlapping, adjacent to, aligned with, same shape as | Generic geometry, fixed in advance | — | **No governing spec.** The only part of speech without canon. The lexicon's QSR and RCC lineage (`SPEC_LEXICON_LIBRARY_v1` §4) is the prior art to port. |
| **Conjunction** | AND; THEN (ordered stages) | The referee checks each stage in order | — | No spec. It is part of the win sentence (§3). |

**Terminology, for ratification only.** CONCEPT_VIRELAI_SOLVER_v2 §4 says "nouns are roles"; SPEC_WEAVE_v1 §0 says "the weave earns the noun; the taxonomy later earns the adjective". The substance is the same: identity is the worldline, and the role is what is predicated of it. This spec uses proper noun for the `###` and common noun for the role. The Director may prefer SPEC_WEAVE's wording.

## 3 · The sentences

| Form | Shape | Canon |
|---|---|---|
| **Law** | "Pressing LEVER a MOVEs DRIVEN b, when …" A marginal or coupling with its forward prediction | `SPEC_MECHANIC_LAYER_v1` §7 |
| **State** | A predicate over the object list at one node | `SPEC_SOLVER_LOOPS_v2` §7 |
| **Win sentence** | A state sentence (or an AND or THEN of them) true at every observed win and false at the earlier boards; it is the Tier-1 hypothesis at level N+1. **"Terminal candidacy" is a REACTIVE-DRIVEN subtree question** (`FOUNDATIONAL_ARCHETYPES_v2` §5). | `SPEC_SOLVER_LOOPS_v2` §7 |
| **Goal** | The laws applied to make the win sentence true | `ACT_ON_GOAL`; gated on LW-E |

A target is derived here, from the win sentence and the laws, never stored [CANON, NESTED_TAXONOMY §6].

## 4 · Where the grammar is certified: answered by canon

- **`RULING_OBSERVERS_INTEGRATOR_v1` (RATIFIED):** "Observation multiplies. Decision converges." There is exactly one integrator: the writer of belief and the gater of action. Observers hold no consumers-of-record (Clause A). A preserved path re-enters belief only after it speaks the current ontology (§5, the vocabulary gate).
- **`SPEC_MECHANIC_LAYER_v1` §8:** the role layer reads only committed mechanics, with downward opacity.
- **Applied to Ring 9 [OBS]:**
  - The **gate machine is the integrator.** It gates every action and writes the certified products.
  - The **semantic library** (`virelai_semantic/`) and the **continuity shadow** (`virelai_continuity.py`, a 1,047-line golden weave port fed by `virelai_runtime.py`) are **observers**. Neither is imported by `virelai_gates.py`, `record_relations.py` or `g4_relations.py`.
  - The semantic library's role vocabulary includes GROUND and WALL, which are not among the six archetypes. Under the vocabulary gate, it must be expressed in the archetype key before its readings can count as parallax, let alone belief. (BELIEF_HOME §4 treats the background as an earned ignore tag, not a role.)
- **So:** the grammar is certified in the gate machine. The semantic library renders it and serves as a graded observer. **This is canon, not a new choice.**
- **The same ruling settles where the board at the win comes from.** Consumers-of-record read the canonical record (Clause A). The win capsule is the observer runtime's, so **the record keeps the winning layer** (LW-A).

## 5 · The v7 level-2 win, re-read under canon [OBS unless tagged]

Two offline probes ran on `vc33_kaggle_carry_v7_record.json.gz`, driven through the gate machine to the transition before the level-2 win. Only IDs, relation names, sizes and counts were printed. No frames were viewed and no colours were printed.

**Proper nouns: what the production G3 ledger did on level 2:**
- **Persistent movers:** E0002 and E0003 kept constant sizes (12 and 16 cells), with STILL ×34 and MOVE ×8 each.
- **Births:** 65, against 65 deaths (DEATH_OR_DEFORM).
- **Classified against the death they overlap,** the 65 births are:

| Correspondence the ledger could not name | Births |
|---|---|
| **Exact SHRINK** (same class, now ⊂ before) | 21 |
| **Exact GROW** (same class, now ⊃ before) | 21 |
| Same-class DEFORM (overlapping, neither a subset nor a superset) | 22 |
| Other-class overlap only | 1 |

**So 42 of 65 identity breaks are exact GROW or SHRINK,** which the lexicon names and the code does not.

**Transitive verbs:**
- All 8 MOVEs of E0002 and E0003 came on presses of certified levers: 2 on E0006, 6 on E0007.
- E0006 moved them on 2 of 4 presses, and E0007 on 6 of 7. E0004 (6 presses) and E0005 (13) never did.

**Under the archetype key:**
- E0002 and E0003 meet REACTIVE-DRIVEN's defining observable as candidates: "deltas predicted by attributed presses on another worldline". They are subjects on the lever's effect edge.
- The non-moving presses are a **repetition-law divergence,** which the LEVER subtree treats as a fork-witness. One canon-named explanation is a **clamp at a travel limit** (SPEC_MECHANIC_LAYER §6). That is a hypothesis to test, not a finding [HYP].
- The GROW and SHRINK breaks that come with the movers' MOVEs are **the raw material of a coupling.** Whether E0078 and E0079 (or their re-minted predecessors) are the **complement** of the movers' motion is decided by the joint-vector fit, never by their size [CANON, MECHANIC_LAYER §5]. v1's "ground" label is withdrawn.

## 6 · LW-0, noun continuity: an open item of an existing contract [CANON + OBS]

`CONTRACT_G3_ENTITY_LIFECYCLE_v1_2026-09-22` already specifies:
- lineage edges SPLIT, MERGE, REMINT and RESPAWN;
- `CANDIDATE_LINK` abstention for ambiguity;
- `IDENTITY_SUSPENDED`;
- "no threshold constant anywhere".

Its open item (c) names the comparator to port: **"the continuity-shadow line is the strongest measured candidate (13/13 on its two-world key, split/merge abstention)"**. That line is `virelai_continuity.py`, already in the Ring 9 tree as an observer.

**What the production ledger implements** (`entity_observation.py:343-376`):
- exact key, unique translation (MOVE), and same-footprint RECOLOR;
- otherwise a new entity (BIRTH, or AMBIGUOUS_BIRTH).

There is **no GROW or SHRINK, no CANDIDATE_LINK and no lineage edge.** Its module docstring (`:3-5`) claims "growth, or shrink correspondence". **The code does not do that** (a docstring–code mismatch; POLICY_DIRECT_READ).

**LW-0, as a port within the contract (PORT default):**
1. **Exact GROW and SHRINK** (same class, a strict subset or superset of a unique unconsumed predecessor). Structural, no threshold, so it fits the contract. On v7 level 2 this would rejoin up to 42 of 65 breaks, before uniqueness checks.
2. **DEFORM abstains into `CANDIDATE_LINK`,** as the contract says. It is not joined.
3. **The continuity shadow stays an observer,** and its agreement and divergence with the ledger are graded and routed as fork-witnesses (OBSERVERS_INTEGRATOR §1).

**A tension for the CE seat:** the shadow's `re_join` uses overlap thresholds (`THETA_DOM` and `THETA_MUT` = 0.80, `virelai_continuity.py:30-31`). The contract forbids threshold constants. LW-0 ports only the structural part. Whether DEFORM joins ever enter the integrator, and by what rule, is architecture.

**Exit (two columns, per SPEC_WEAVE §6):**
- **Fidelity:** every entity decompresses to its sightings, and the cells are covered and disjoint at every node.
- **Correctness:** on fixed replays (CLICK and NAV), every GROW or SHRINK join is right, with **zero false joins**, graded by the Director against a hand-labelled set.
- The full suite passes, including the NAV-ego and continuity-shadow tests. The 2026-09-28 handoff memo warns that continuity changes affect every world.

## 7 · Build order

| Rung | Part of speech | What | Exit |
|---|---|---|---|
| **LW-0** | Proper noun | §6 | §6 |
| **LW-A** | (record) | The canonical record keeps the winning layer (§4) | A replayed record yields the board at the win, matching the capsule's SHA |
| **LW-B1** | Common noun | REACTIVE-DRIVEN from G4's effect edges, re-keyed from cells onto worldlines | v7: E0002 and E0003 committed DRIVEN by E0006 and E0007, or the gap declared |
| **LW-B2** | Reciprocal verb, adverb, conditional | The joint-vector coupling fit (movers against their GROW and SHRINK partners); the repetition-law divergence explained or declared | v7: complement derived or not, and E0006's 2 of 4 explained or "condition not yet known" |
| **LW-B3** | Preposition | Port QSR and RCC relations; fixed in advance | v7 level 2: a separator in role, verb and preposition terms, or the gap named |
| **LW-C** | Quantifier, conjunction; the win sentence | The referee | As in `LEARN_TO_WIN_ZOOM_v2` |
| **LW-D, LW-E** | Determiner | Carry by type; the live level-3 test | As in `LEARN_TO_WIN_ZOOM_v2` |

**A hypothesis LW-B1 must check first [HYP].** G4.1 anatomy channels are keyed on fixed cells. A driven object that moves leaves its channel, so a cell-keyed REMOTE channel cannot follow it. That would explain why v1's anatomy-channel separator found nothing at level 2. If it holds, it is the same identity defect the canon names (`RULING_LIB1_IDENTITY_v1`: identity is the worldline; a region is a label), one gate higher.

## 8 · Rulings still owed (Director)

The sweep answered v1's questions 2 (where the grammar lives) and 4b (the source of the winning board) from canon, and placed LW-0 inside an existing contract. What remains:

1. **Ratification status of `FOUNDATIONAL_ARCHETYPES_v2` and `NESTED_TAXONOMY_SPEC_v5`.** Both say DRAFT. This grammar rests on them.
2. **Ratify this spec** (§2–3), including the terminology choice.
3. **Go to build LW-0** within `CONTRACT_G3_ENTITY_LIFECYCLE_v1` (structural GROW and SHRINK; DEFORM abstains), **then LW-A and LW-B.**
4. **For the CE seat:** whether DEFORM joins ever enter the integrator, given the contract's no-threshold rule and the shadow's 0.80 overlap thresholds.

## 9 · Firewall

- Roles and verbs are keyed on behaviour in the record, never on colour, position or a world's name.
- vc33 is a dev world whose win kind I have read about elsewhere (declared 2026-10-02).
- The probes printed only IDs, relation names, sizes and counts.
- The vc33 results show the machinery works. Generalisation waits for the held-out worlds.

— Claude

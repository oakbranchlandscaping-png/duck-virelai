# Build plan: semantic library → gated Push → free-play fallback (v1, 2026-10-09)

**Status:** proposal for team review; not a ruling or a claim of implementation.  
**Read against:** `ring9-unified` at `b805950`, the 2026-10-08 v1 rehearsal review, and the new, uncommitted `SPEC_PHYSICS_GRAMMAR_v3_2026-10-08.md` draft.  
**Scope:** the decision structure of one level, across lives. No world-specific mechanics or hidden win condition is assumed.

## 1. Proposed decision

The primary mission remains to build a falsifiable semantic library of this level's physics. G0–G4 are its current opening, not its completion. The target tree must continue through observed reactions, environmental forces, scoped negative knowledge, entity relations, conditional laws, and any new subjects discovered later. A gate may close `NOT_APPLICABLE` or `UNRESOLVED` with its tested scope; it must not manufacture a law to make the library look complete.

When every **currently generated, ready semantic obligation** has been answered or boundedly closed, a gated Push target takes focus. Push searches the reachable frontier of **untried state–action edges**. Each executed edge is observed and recorded. A new subject, unexplained residual, falsified law, or changed mask pauses Push and opens or reopens the relevant semantic target. Once that obligation is dealt with, Push resumes from the observed board. An observed win opens the win-explanation path. Only if neither a semantic gate nor a sound Push step is available does Duck enter normal free play for the remainder of the level's slice.

This is a repeating handoff, not a one-way phase change:

```text
semantic target(s) ── current obligations bounded ──> gated Push
       ^                                           |
       | new object / residual / contradiction     | observed win
       └───────────────────────────────────────────┘
                                                   └──> observed-win explanation

semantic target or Push cannot proceed soundly ──> FREE_PLAY with reason and receipts
level changes ──> new level's semantic targets and frontier
```

The controller owns the lock, admissible action set, evidence checks, and routing. Duck supplies an interpretation where the target asks for one; a prompt alone does not enforce the protocol. The environment alone supplies the win label.

## 2. Why the order is conditional

`CYBERNETIC_TARGET_TREE_v1` defines the mission as exploration and description of physics. Its spine extends past levers to reactions, forces, inertness, novelty, and observed-win explanation. The current Ring 9 target registry reaches lever effects, orbits, relations and laws, then `PLAY-NORMAL`. The planned G5–G7 targets and much of the full semantic library are absent. `SPEC_PHYSICS_GRAMMAR_v3` supplies an offline executable sentence subset and referee; it is not yet a live semantic compiler or a complete vocabulary.

“Full library” has two requirements: **the deployed grammar and gate tree have the full planned capability**, including all entities, roles, relations, reactions, conditional mechanics, environmental forces and scoped negative knowledge; and **the current level has been studied to the declared coverage boundary**. It cannot mean every possible mechanic in an unvisited part of the level. Push is one way those missing observations arise. The semantic tree must be able to reopen during Push and, when sound, during free play. The current forced `PLAY-NORMAL` route wins target selection until level change, so this reentry requires an explicit routing change.

The earlier V4 Push code supplies useful prior art: a visited map, exact tried action keys, an open frontier, recorded paths, progress checks, and hidden-state alarms. Ring 9 already has counter-masked `world_address` and a raw-frame archive. Neither alone is a complete Push controller. In this checkout `virelai_golden/push/` is only a package placeholder; do not plan a file copy that does not exist here.

## 3. Contracts and meanings

### Semantic-library readiness

A level is *Push-ready* only when the router has no ready semantic target that can lawfully act now, and its closure record lists:

- active, versioned laws with support, prospective tests, limitations and falsifiers;
- generated but unresolved targets, with the exact missing evidence or bounded stop;
- observed entities without a settled role, including newborn and ambiguous identities;
- the current counter-mask law and its version, or an explicit inability to use masked identity;
- a witness that the decision board is settled, not an animation transient or successor spawn.

In the target architecture, the router must first offer the full semantic set: entity/worldline continuity; roles for all observed entities, not just ego and levers; interaction and spatial relations; reaction and conditional mechanic laws; residual environmental forces; and scoped negative certificates. The grammar must express and referee these laws in typed form. Individual branches may close with evidence-bound `NOT_APPLICABLE` or `UNRESOLVED`, but a branch cannot be skipped because its module was never built. Until these capabilities exist, a Push canary is explicitly a **partial-library experiment**, not a claim that the full-library handoff has been achieved.

Readiness is not a claim that all categories are known. Unknowns stay open and may become actionable after another transition. A newly observed phenomenon has priority over another Push edge when the target tree can form a bounded semantic question about it.

### Push target

Define a per-level `PUSH-FRONTIER` GoalContract and adapter. Its question is: *Which as-yet-untried action from a reached world state can extend the observed map or test an unresolved physics question?* The product is a versioned frontier/coverage record, not a claimed win law.

An edge key includes the level and mask version, the settled masked state address, the **exact** available action and its target or coordinate binding. `ACTION6` at two targets is two edges. A no-op or environment refusal still counts as an attempted edge with a result. A different successor from the same key is a contradiction/hidden-state alarm, not an average edge. Mask revision requires re-addressing retained raw boards before old and new frontier counts are compared.

At the current state, prefer a lawful untried edge. Rank it first by an unresolved semantic question it can test, then by breadth across distinct target entities, then by a deterministic tie break. If none exists here, follow a shortest *observed* route to a reachable open state, one action at a time, comparing every actual successor with the recorded edge. A mismatch cancels the route and opens an investigation. RESET is permitted only as a bounded, recorded route to an **observed** landing and must not repeat without progress. No imagined transition may be used as a route.

The gate may constrain Duck to an exact next edge or a small admissible frontier set. It must validate the probe token and action **before** environment execution. It records who selected the edge (controller or Duck), the frontier reason, predicted known-route successor if applicable, actual successor, novelty, and evidence ID. A newly observed board is a fact; a prediction of novelty is not a fact. No terminal label or imagined win predicate enters the action selector.

Push completion is scoped: `SATURATED` only if the declared reachable component has no untried lawful edge under the current mask, action menu and graph version. Time or action cap is `BUDGET_STOPPED`; uncertain state identity or hidden-state divergence is `UNRESOLVED`. None of these asserts that the game is unwinnable.

### Free-play fallback

`PLAY-NORMAL` remains available when the semantic target cannot act and Push cannot certify a next step, when a controlled stop requires a bounded escape, or when the remaining slice cannot support a safe route. Its card carries the active library, unresolved questions and the exact fallback reason. The first controlled stop may still rest the level; a second stop must remain bounded. Free-play actions keep their `FREE_PLAY` receipt and are recorded as observations. They do not retroactively become evidence that a gated Push policy selected a win.

The current v1 free-play feedback defect (R-1 in the 2026-10-08 rehearsal review) is a prerequisite repair: `PlayTarget.record_outcome` omits `outcome`, while `_apply_step_result` requires it after execution. A real Duck action must receive the executed result before either Push or fallback is evaluated live. Test the recording size as well as the feedback path.

## 4. Build slices and exit evidence

| Slice | Deliverable | Exit evidence |
|---|---|---|
| P0 · repair feedback | SUB-3 fixes the executed-result handoff in free play and logs hidden sandbox exception class/message to local diagnostics. | A Duck action through the real tool path executes once, returns its observation, updates the ledger once; no misleading failure or retry. |
| P1 · library readiness | Inventory current G0–G4 products and generated gaps; define target-level `SATISFIED` / scoped `NOT_APPLICABLE` / `UNRESOLVED` / `BUDGET_STOPPED` versus Push readiness. Keep the semantic grammar and evidence refs typed. | Toy and record replay: a missing or contradicted product cannot be silently called complete; a bounded unknown does not deadlock routing. |
| P2 · map as observation | New, per-game/per-level Push graph consumer of existing raw frames, G2 mask and exact action records. Preserve mask version, target binding, no-op/refusal, reset and life boundaries. No action selection yet. | Replay gives deterministic nodes/edges; counter ticks do not mint novelty; same action at distinct targets differs; divergent successors alarm; no cross-game mixing. |
| P3 · complete semantic capability | Build the missing entity-role, relation, conditional-mechanic, G5 force and G6 scoped-negative targets as evidence-bearing slices; connect them to the typed grammar and referee. Make coverage and `NOT_APPLICABLE` / `UNRESOLVED` explicit. | Planted toy worlds exercise each part of speech and each gate disposition; every observed entity has a role status or an explicit unknown, not silent omission. |
| P4 · gated frontier and semantic reentry | `PUSH-FRONTIER` GoalContract, compact card, admission check, one-action policy, observed-route verification, bounded reset and scope-specific saturation. Route new entities, residual effects, contradictions and mask revisions back to the appropriate semantic target, then resume Push. | CLICK/NAV fixture replay: untried edge, route, refused edge, mismatch, reset landing and exhaustion have the right disposition; a planted novel effect suspends Push, earns or bounds a semantic product, then returns to a recomputed frontier. |
| P5 · fallback and live canary | `PLAY-NORMAL` receives control only with an explicit reason after P1–P4 decide no sound gated step exists. Keep per-transition receipts and the submission clock guard. | Same seed comparison: gated Push increases distinct resolved state–action edges without a reset loop, false novelty, or lost Duck feedback; any fallback is named. |

P0's test and the new-file portions of P1–P3 can be prepared offline. The ratified `RULINGS_CONSOLIDATION_v2` item 13 freezes existing runtime source until the v1 submission; shared-file hooks wait for that window and their owners. Do not modify the frozen Kaggle package. The current uncommitted grammar draft is input to review, not an already ratified dependency. P4 may be tested on toy and record replay before the full-library gate is enabled live, but P5 must report whether P3 actually passed.

## 5. Measurement and scientific boundary

Track, per level and per life: semantic obligations opened/resolved/bounded; mask version; Push-ready transitions; Push actions; distinct tried edges; distinct settled masked states; no-ops/refusals; route mismatches; reset attempts and verified landings; unresolved alarms; free-play fallback reasons; observed wins and the mode in which they occurred. Count action and wall-clock cost. Report both the number of states reached and the share of reachable observed frontier edges resolved. A graph that fires zero Push actions must say whether it was never eligible, declined on uncertainty, or was blocked by the clock.

The preregistered analysis must distinguish guided semantic actions, gated Push actions and `FREE_PLAY`. A win found by Push is an observed win and can enter the win referee, but it does not prove the grammar predicted the win. A win found during free play is likewise real and tagged. Claims about the gate policy use only actions that the gate actually admitted.

## 6. Decision points for team review

1. **Amend R-2/G-5:** after current semantic obligations rest, gated Push takes focus where its substrate is sound; normal free play is the bounded fallback. The current ruling sends the ladder directly to free play.
2. **Split R-7:** the exploratory Push graph and gated frontier may precede learn-to-win. Planning toward a *learned goal*, with simulator and predict–act–compare, remains `ACT_ON_GOAL` after its live goal test.
3. **Name closure honestly:** adopt “current semantic obligations bounded” as the handoff condition. Do not require an unknowable complete inventory of all physics before exploration.
4. **Assign the shared seams and test window:** the target registry/router, `PLAY-NORMAL` forced precedence, controller ownership, action result, level record and receipts need coordinated hooks. File `NOTE_SHARED_FILE` before shared edits, preserving SUB-3 and the submission source boundary.

No decision here changes the observed-win-only rule: Duck learns what winning means after an actual terminal transition, while semantic study and Push are the pre-win mission.

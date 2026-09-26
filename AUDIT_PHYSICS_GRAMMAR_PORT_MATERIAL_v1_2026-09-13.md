# AUDIT — PHYSICS-GRAMMAR PORT MATERIAL

**Date:** 2026-09-13  
**Purpose:** Identify what Virelai already does well, what remains weak, and which prior implementations should be ported, adapted, mined for ideas, or left behind.

## Executive finding

The desired system does not exist intact in any one tree, but most of its parts already exist.

- **Ring 8** is the best production host: passive capture, lossless archive, Duck-compatible queries, level-boundary delivery, and a typed canonical model.
- **Virelai Golden** has the cleanest current epistemology: threshold-free observations where possible, explicit witnesses and parallax, action-indexed arithmetic, prospective falsification, and separation between observation and role.
- **V4** has the broadest implemented physics vocabulary: worldlines, edge verbs, ego covariance, counter tracking, lever activation, effect localization, displacement, count change, conservation, cycles, saturation, and animation reads.
- **V3.5** has the clearest consumer contracts: lever artifacts, transition profiles, WorldMachine, solved-level capture, cross-level mechanic memory, unknown registries, and compact narrative structure.

The missing product is the integration layer: a persistent, worldline-keyed, evidence-linked physics grammar whose compact view tells Duck only what is useful now and whose deeper views preserve the proof.

## Audit standard

Each candidate is classified as:

- **PORT:** implementation is sufficiently aligned to reuse with narrow integration work.
- **ADAPT:** valuable implementation exists, but its identity model, epistemology, or interface must change.
- **MINE:** preserve the concept or contract, not the implementation.
- **RETAIN:** current Ring 8 implementation should remain authoritative.
- **DEFER:** useful later, but premature for the next capability rung.
- **REJECT:** known failure pattern that should not return.

## Capability map

| Layer | Best source | What already works | Principal limitation | Ruling |
|---|---|---|---|---|
| Passive capture and archive | Ring 8 runtime/journal | Lossless frame and transition history; hidden-observer doctrine; integrity checks; bounded queries | Semantic compilation is expensive and shallow relative to the archive | RETAIN |
| Exact pixel arithmetic | Ring 8 cell deltas; V4 transition signatures; Golden mechanics | Exact rewrites, class-labelled change membership, press-indexed counts and transfers | V4's pair-local `vacated`/`claimed` cannot identify the other occupant; terminology can imply a void that grids do not contain | PORT/ADAPT |
| Visual segmentation | V4 clay/perception; Golden substrate scan | Deterministic region construction and per-frame object candidates | A region is not an enduring object; ground and moving figures can fragment or fuse | RETAIN as observation only |
| Object continuity | V4 weave + rejoin + occlusion; Golden continuity stream | STILL/RECOLOR/MOVE/GROW/SHRINK edges, conservative residuals, rejoin, occlusion witnesses, many-to-many accounting prototype | Correspondence remains the hardest open problem; overlap thresholds and missing split/merge logic can mislead; recomputation can churn identifiers | ADAPT and grade before promotion |
| Ego/control | V4/Golden action-bearing reads | Learns action-to-bearing covariance without assuming canonical directions; retains blocked actions at their origin sites; supports composite ego | Requires enough differentiated actions; pointer/body modes need distinct handling; role depends on continuity quality | PORT |
| Autonomous clocks/counters | Ring 8 clock; Golden counter/friction F-0009; V4 counter march/stats | Class-count trends, action independence, rates, remaining budget, death confirmation, conserved class-pair exchange | Single-worldline counter rules fail on remint/refill and occasional flats; class-only rules lack object localization | ADAPT into a class-process rule linked to participating worldlines |
| Lever discovery | V4 lever witness/cycle probe; Golden effects | Separates acted object from changed partners; supports pointer and body activation; repeated pressing exposes recurrence and saturation | Upstream counter failure makes autonomous objects look lever-driven; transient region ids are unsafe identities | PORT logic, replace keys and masks |
| Lever typing | V4 mechanism classifier and physics accumulator; V3.5 TransitionProfile | Toggle, finite cycle, directional drift, saturation, rigid displacement, reshape/count change, entry-state conditioning, two-confirm recurrence | V4 contains tuned confidence thresholds and first-generation region bindings; strict recurrence may miss conditional mechanics | ADAPT |
| Shared-resource mechanics | Golden joint transfer vectors; V4 conserved transfer/exchange | Exact opposed changes can identify controls moving a shared resource in opposite directions; direction kept separate from conservation law | Current rules cover a narrow relational family and may under-generalize conditional exchanges | PORT as one mechanic family, not the universal grammar |
| Animation/interior frames | V4 perception/animation | Distinguishes FLASH, SILENT, EFFECTIVE; retains evidence discarded by settled-frame-only paths | Mostly diagnostic; semantics of flashes are not decoded and should not be guessed | PORT structural observations |
| Canonical semantic schema | Ring 8 `virelai_world_model.py` | Typed claims, evidence refs, state variables, mechanic rules, wins, level diffs, validation, deterministic serialization | Current compiled mechanics lack enough trigger/effect/condition/period detail; candidate roles can still be overpromoted | RETAIN and extend |
| Win boundary | Ring 8 win capsule; V3.5 solved examples | Exact pre-win edge, action, frames, level root, action history, actor-independent capture | Records that a win occurred, not the necessary or sufficient condition; current predicate text is mostly a boundary description | RETAIN observation; build analysis above it |
| Win explanation | V3.5 relational extractor/goal concepts; Ring 8 level lessons | Can name last contact, mutation targets, prior action behavior, established facts and hypotheses | V3.5 often infers a target from temporal proximity; current Ring 8 cannot express configurational predicates robustly | MINE contracts; new evidence-linked compiler required |
| Cross-level memory | V3.5 MechanicMemory/level transition; Ring 8 level diff/carry | Captures solved examples, preserves world-type hints, compares types between levels, delivers prior lesson | V3.5 compresses too aggressively into classes/quadrants/counts; Ring 8 correspondence is tentative and current delivery repeats | ADAPT |
| Unknowns/hypotheses | V3.5 causal ledger/level unknowns; Ring 8 Claim | Explicit status lifecycle and unresolved questions already modeled | Thresholded confidence, fixed question templates, and policy coupling violate the newer passive/tool doctrine | MINE schema only |
| Player presentation | V3.5 narrative/field-card idea; Ring 8 expandable card | Compact outline plus expansion handles is correct for Duck's token budget | Current card repeats, duplicates transcript memory, exposes weak claims, and omits mechanics Duck actually used | ADAPT urgently |

## What the repository already does especially well

### 1. It records reality better than Duck can reconstruct it

Ring 8's compact journal and archive are the strongest completed foundation. They preserve exact frames, actions, outcomes, level/life boundaries, and transition metadata without consuming actions or changing Duck's policy. This is genuinely novel relative to Duck: durable, exact, queryable history rather than a prose recollection inside a finite prompt.

This layer should not be redesigned. Semantic work should compile from it and never mutate it.

### 2. The weave has a serious vocabulary of observable change

V4's weave is more than object tracking. It already distinguishes persistence, recoloring, translation, growth, shrinkage, deformation, birth, death, ambiguity, rejoin, and occlusion. Transition signatures retain member cells rather than only counts. This is exactly the substrate a physics grammar needs.

The strongest design choice is conservative abstention: an ambiguous match should terminate or remain residual rather than fabricate continuity. That doctrine must survive the port.

### 3. Action-indexed arithmetic is the right route to mechanics

The most valuable Golden work is the move away from visual labels toward press-indexed laws. Joint transfer vectors, action-bearing maps, action dependence/independence, and exact exchange are reusable because they describe what changes under an action, not what an object merely resembles.

This is the bridge from a replay to a state machine:

`current variables + action + conditions -> measured update`

### 4. Lever typing is much more developed than current cards reveal

V4 already contains nearly the full lever dossier the player wants:

- activation surface and activation mode;
- affected subjects and affected cells;
- local, remote, or global scope;
- rigid displacement vector or non-rigid count/shape change;
- cycle or toggle period;
- directional drift;
- saturation/self-loop behavior;
- entry-state signature;
- observation count, agreement, null presses, and disregarded autonomous regions;
- conserved transfer between paired subjects.

The present Ring 8 output exposes only a thin slice of this. The data-production gap is therefore smaller than the presentation suggests.

### 5. Win capture and level transition infrastructure already exist

Ring 8 captures the exact level-win boundary safely. V3.5 captures spawn grid, win grid, action sequence, contacted sites, mutation targets, and a solved example before clearing level-local state. The correct future implementation should combine the Ring 8 truth boundary with the richer, but less trustworthy, V3.5 comparison questions.

### 6. The repository has learned important negative lessons

Several failures are now explicit prior art:

- region ordinal is not identity;
- object count is not worldline count;
- appearance is not semantic role;
- coupling is not causation;
- action independence alone is not a counter;
- action dependence alone is not a lever;
- recurrence observed once is not a proven period;
- the last contact before a win is not automatically the win condition;
- a prior-level object is not the same current-level instance;
- confidence is often coverage, not truth;
- a renderer must not become a second knowledge store;
- prompt inclusion does not prove tool use;
- forced experiments confound an optional-tool experiment;
- repeating the same memory every turn can cost more than it contributes.

These are assets. They narrow the next build substantially.

## Best port candidates in detail

### A. V4 worldline and transition stack — ADAPT

**Files:**

- `virelai_v4/weave/worldline.py`
- `virelai_v4/weave/rejoin.py`
- `virelai_v4/weave/transition_signature.py`
- `virelai_v4/weave/ego_read.py`
- `virelai_v4/weave/coupling.py`
- `virelai_v4/weave/exchange_read.py`

**Take:** edge verbs, member-cell signatures, action-at-right-node indexing, blocked-action sites, conservative residuals, occlusion witnesses, action marginals, exact exchange.

**Change:** compile stable player handles separately from implementation worldline ids; define occupancy rewrites rather than treating a missing member as an empty cell; grade continuity against a hand-labelled set including expected discontinuities; do not expose a worldline id as an object name until continuity is certified.

### B. Golden mechanics — PORT

**Files:**

- `/Users/stephenkaskin/Desktop/virelai-golden/golden/weave/mechanics.py`
- `/Users/stephenkaskin/Desktop/virelai-golden/golden/roles/effects.py`

**Take:** exact press-indexed transfer relations; actor/partner exclusions; witness and null sets; separation of law from selected direction; `falsify()` as a prospective comparison operation.

**Change:** allow conditions and phases so a rule can be scoped rather than killed by every apparent exception; translate internal ids into semantic handles only at the model boundary.

### C. Counter family — ADAPT

**Files:**

- `virelai_v4/library/counter_march.py`
- `virelai_v4/library/counter_stats.py`
- `/Users/stephenkaskin/Desktop/virelai-golden/golden/roles/counter.py`
- `/Users/stephenkaskin/Desktop/virelai-golden/docs/frictions/F-0009*`
- current Ring 8 clock implementation (`virelai_clock.py` in the capability variants)

**Take:** monotone march, variable step, rate and budget arithmetic, action-independence coverage, death confirmation/disconfirmation, exact opposed class-count processes, nested depletion boundaries.

**Change:** model a clock/counter first as a persistent state variable or class-pair process, then bind visible worldlines as participants. Do not require one worldline id to survive refill. Occasional flat presses should create a condition question, not automatically erase the process.

### D. V4 lever-depth machinery — ADAPT

**Files:**

- `virelai_v4/library/cycle_probe.py`
- `virelai_v4/library/physics_accumulator.py`
- `virelai_v4/weave/lever_witness.py`
- `virelai_v4/weave/mechanism_classify.py`
- `virelai_v4/perception/operation_measurer.py`
- `virelai_v4/contracts/lever_effect.py`
- `virelai_v4/contracts/conserved_transfer.py`

**Take:** press-until-recurrence/saturation, two-confirm recurrence, effect channels, displacement vectors, reshape/count deltas, conserved-transfer authoring, null evidence, entry-state conditioning.

**Change:** run as offline/passive compilation over Duck's naturally generated action record. Do not import Captain targeting policy. Replace confidence constants with counts, explicit coverage, witnessed contradictions, and status. Key subjects by certified semantic handles.

### E. V3.5 contracts — MINE/ADAPT

**Files:**

- `Universal_Solver_v3_5/contracts/lever_artifact.py`
- `Universal_Solver_v3_5/contracts/mechanic_memory.py`
- `Universal_Solver_v3_5/execution/level_transition.py`
- `Universal_Solver_v3_5/execution/level_unknowns.py`
- `Universal_Solver_v3_5/observer/narrative_renderer.py`
- `Universal_Solver_v3_5/observer/relational_extractor.py`

**Take:** LeverArtifact shape, activation/effect distinction, TransitionProfile invariants, WorldMachine concept, solved-example capture order, level-local versus persistent separation, expandable narrative hierarchy.

**Leave:** guessed goal configurations, confidence floats as epistemology, fixed four-press assumptions, target classes/quadrants as primary transfer knowledge, planner/governor policy, last-contact-equals-win shortcuts.

### F. Current Ring 8 world model — RETAIN/EXTEND

**Files:**

- `duck-virelai/variants/ring8-expandable-memory-card-delivery-fix/ARC3-Inference/inference/framework/virelai_world_model.py`
- `.../inference/framework/virelai_semantic/compiler.py`
- `.../inference/framework/virelai_semantic/mechanics.py`
- `.../inference/framework/virelai_win_capsule.py`
- `.../inference/framework/virelai_memory_card.py`

**Take:** this is the production integration point. Its typed `Claim`, `EvidenceRef`, `StateVariable`, `MechanicRule`, `WinRecord`, `LevelDiff`, deterministic serialization, validation, and bounded query interface are the correct host.

**Extend MechanicRule with:**

- subject handles;
- activating action/control;
- entry condition;
- exact transformation family and parameters;
- affected region/objects;
- period and phase when witnessed;
- saturation/endpoint;
- witness transitions and counterexamples;
- scope by level/life/state;
- status: observed, candidate, contradicted, superseded;
- revision predecessor/successor.

The immutable journal remains truth. The grammar is a derived, revisable index.

## Areas needing real development

### 1. Certified continuity

This is the deepest substrate risk. Both V4 and Golden have strong correspondence ideas, but neither warrants blanket trust. Before semantic roles depend on identity, create a fixed, hand-labelled continuity corpus from real replays with positive continuities, occlusions, returns, splits, merges, same-class crossings, ground deformation, and expected discontinuities.

The gate must be numerical and include false joins, which are more damaging than missed joins.

### 2. Rule induction above exact observations

The repository measures many rule families, but it lacks one uniform rule ledger. A new compiler must normalize all admitted mechanics into the same structure and preserve their witnesses. It must distinguish:

- observation: what changed on a specific transition;
- regularity: what repeated across a scoped set;
- hypothesis: a proposed general rule;
- prediction: what the rule says should happen next;
- revision: how the rule changes after contradiction.

Hypotheses must never rewrite the journal or weave.

### 3. Configurational win predicates

This is the largest novel semantic task. Current code captures the win edge but usually cannot state why it won. The first useful compiler should compare the winning pre-state with earlier non-winning states in object terms:

- contacts and overlaps;
- relative positions;
- object states/classes/counts;
- lever phases;
- counter state;
- newly satisfied conjunctions;
- objects that vanished, appeared, opened, closed, aligned, or entered a region.

It should produce the narrowest witnessed distinguishing condition, label it as a candidate rather than proof, and preserve alternatives when evidence is underdetermined.

### 4. Cross-level correspondence of roles and mechanics

Instances reset at level boundaries. What may transfer is a type, role, relation, or rule. The current type-signature comparison is a start, but the useful product is:

- what familiar object types returned;
- which prior controls have candidate counterparts;
- which old rules have already held here;
- which rules have failed here;
- what is genuinely new.

This is how Virelai makes new mechanics stand out without falsely asserting sameness.

### 5. Consumer compression and retrieval lifecycle

The latest Kaggle run proved delivery but not use. The compact card is the right form, but the lifecycle is wrong and the content is not yet worth expanding.

Required behavior:

- deliver one compact delta exactly once on level entry;
- do not repeat it on every turn;
- keep details behind stable handles;
- answer a query with the smallest relevant fact plus evidence count;
- offer expansions by player question: `control`, `mechanic`, `object`, `win`, `carry`, `replay`;
- prioritize novel facts Duck cannot cheaply infer from its current frame or transcript.

### 6. Query performance

The archive path is safe, but repeated full semantic recompilation is too expensive. Compilation should be incremental or performed speculatively while the model is generating. Query results should be cached at journal boundaries with an explicit latency budget. Raw evidence must never be discarded to satisfy the budget.

## Material that should not be revived

- Rings 1–5 model modifications or policy-heavy solver branches.
- A Captain that spends environment actions before Duck unless tested as a separate architecture.
- Region-id keyed semantic identity across frames or levels.
- Background/role classification from size, color, or position priors.
- Confidence floats presented as truth.
- Full diagnostic rosters and raw cell rewrites in the default player briefing.
- Fixed experiment/falsification scripts that compel Duck's actions.
- A field card treated as the library itself.
- Any win explanation that promotes temporal adjacency to causality.
- Any cross-level carry that reuses an object instance rather than proposes a typed correspondence.

## Recommended consolidation order

### Stage 0 — repair the current card lifecycle

Deliver once on level entry, remove transcript duplication, retain explicit expansion handles. This is independent engineering work and prevents every semantic experiment from paying the known token tax.

### Stage 1 — establish the canonical mechanic record offline

Extend Ring 8's `MechanicRule` and implement adapters for existing exact sources:

1. ego action-bearing;
2. class/state clock process;
3. lever-to-effect channels;
4. displacement/count/shape operations;
5. recurrence, period, direction, saturation;
6. exact shared-resource transfer.

No new gameplay policy and no live prompt changes.

### Stage 2 — grade each rule family on fixed replays

Use human-readable outputs for vc33, ft09, ls20, ar25, lp85, r11l, plus hard negatives. For each claim record correct, incorrect, abstained, and missing. Expose only families that pass their predeclared gate.

### Stage 3 — render an operating manual, not a survey

Default view:

1. world/control mode;
2. ego or pointer control;
3. clock/counter state;
4. known controls and exact effects;
5. known state variables and update laws;
6. prior win candidate, if any;
7. what changed on this level;
8. expansion handles.

### Stage 4 — build observed-win analysis

Compile candidate configurational predicates from the exact win edge and contrasts. Preserve alternatives and evidence. On the next level, show whether each predicate is currently satisfied, testable, contradicted, or ungrounded.

### Stage 5 — add the learning/revision loop

Only after the observations and renderer grade well: let Duck state optional hypotheses in the canonical vocabulary, compare predictions against later transitions, and keep revision lineage. Natural tool use only; no forced action protocol.

## Bottom line

The repository has enough prior art to build the intended world model without another architectural reset. Approximately the whole observation stack, most first-order mechanic detectors, the win boundary, persistence, query interface, and presentation pattern already exist.

The genuinely new work is narrower but important: certify continuity, normalize mechanics into one evidence-linked grammar, infer cautious configurational win candidates, manage cross-level rule transfer, and deliver only high-value deltas to Duck.

The next build should therefore be a **consolidation and grading rung**, not another prompt experiment and not a new solver.

# Target: the semantic library as Duck's world machine

**Date:** 2026-10-15  
**Status:** Director-ratified target  
**Authority:** the Director's instruction to lock the semantic-library build order while the current Claude slice closes  
**Governing build plan:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v5_2026-10-15.md`

## 1. North star

For every observed level in every novel world, Duck maintains one evidence-backed internal model that is useful even when the level is never cleared.

The model is a predictive state machine, not an object list or a transcript. It answers:

1. What persistent subjects exist?
2. What is their current state?
3. Which semantic roles have been certified?
4. Which actions and autonomous schedules change them?
5. What are the transformation, direction, magnitude, timing, conditions and limits of each change?
6. Which relations connect drivers and affected subjects?
7. Which claims are observed, certified, pending, contradicted, unknown or outside tested scope?
8. Which missing fact is the next useful experiment intended to resolve?
9. If a win occurred, how can it be described in the same internal language and tested prospectively on the next level?

The canonical artifact is the single validated `world_model.json`. Gate products certify belief. The census, agenda, Duck view, human report, claim projection and grammar renderer are read-only projections. No second writer is permitted.

## 2. Internal language

### 2.1 Nouns

- **Instance noun:** a persistent level-scoped worldline or gate entity.
- **Role noun:** one or more of `EGO`, `COUNTER`, `LEVER`, `ENVIRONMENTAL_FORCE`, `REACTIVE_DRIVEN`, and `INERT`.
- Terrain and unresolved objects remain observations until a role gate earns a role.
- `INERT` is exclusive and requires a coverage certificate.
- A class change ends the old binding and opens a retyping question.
- Cross-life and cross-level identity are hypotheses until continuity evidence establishes them.

### 2.2 Attributes

Every subject may carry class, shape, footprint, anchor, extent, size, current state, phase, presence, reachability and lineage information. An unavailable value is explicit; renderers never fill it from appearance.

### 2.3 Observation verbs

The accepted base vocabulary is `STILL`, `RECOLOR`, `MOVE`, `GROW`, `SHRINK`, `BIRTH`, `DEATH`, `DEFORM`, and `AMBIGUOUS`.

These verbs report what changed. They do not assert why it changed.

### 2.4 Causal verbs and laws

Gate-backed relations may express `ACTIVATES`, `CHANGES`, `DRIVES`, `BLOCKS`, `RELEASES`, `RESETS`, `INCREMENTS`, `DECREMENTS`, and later evidence-forced terms.

Every mechanic law names:

- the intervention or autonomous trigger;
- the subject and affected subjects;
- the exact transformation;
- direction, magnitude, delay, period and phase when measured;
- preconditions, tested states, scope and endpoint behavior;
- supporting and contradicting evidence;
- limitations and competing models;
- prospective status and a falsifier.

No prose-only law enters belief. A G3 witness establishes the `LEVER` noun; it does not establish a repeated law.

### 2.5 Unknowns

Unresolved identity, unexplained change, untested intervention, inconclusive attribution, reachability limit, budget limit, contradiction, record mismatch, product pending and coverage not built are first-class model states. A fluent report may not hide them.

## 3. Five connected model layers

### A. Object graph

Persistent identities, appearances, role bindings, lineage, current state, and incoming or outgoing semantic relations.

### B. Event graph

One record for every transition: before state, action, executor, target, result state, observed verbs, exact rewrite, receipts and explanation status.

### C. Mechanic graph

Certified interventions and autonomous processes, with their effects, conditions, limits, repetitions, predictions and contradictions.

### D. Question graph

Every incomplete model field becomes a stable question naming its subject, missing evidence, owning gate, admissible experiments, current disposition and closure condition. The earliest actionable question is the cybernetic target.

### E. Transfer graph

Observed terminal transitions, frozen pre-win models, win sentences, lifted type hypotheses and prospective next-level verdicts. Later evidence may grade a frozen hypothesis but may not rewrite what it predicted.

## 4. Duck's operating loop

1. The library exposes the earliest actionable gap.
2. The owning gate supplies the bounded admissible experiments.
3. The controller performs routine coverage, navigation and bookkeeping.
4. Duck chooses among admitted experiments when judgment helps.
5. The record captures the exact outcome and provenance.
6. Deterministic code updates only the claims the evidence supports.
7. Duck reads the revised library and its next selected question.

The full census stays off the controller's per-action path. The cheap gate agenda selects work. The detailed model is compiled on Duck turns, boundaries, terminal paths and reports.

## 5. Consumer contract

The ordinary digest must preserve:

- the selected question;
- current certified findings;
- at least the leading transformation patterns and unresolved world question when they exist;
- record or identity failures;
- retrieval handles.

Paged retrieval must cover scene, objects, events, transformations, dossiers, laws, residuals, evidence and gaps. A player-facing field must help Duck predict an action, avoid a settled experiment, identify an actionable subject or choose a useful next experiment. Raw provenance remains retrievable without crowding the ordinary brief.

## 6. Success definition

The semantic library is robust when:

- every observed object and transition is represented exactly once or a typed integrity failure explains why not;
- every event has an observation verb and resolvable evidence;
- every role and causal claim comes from its owning gate;
- every certified lever has a durable chapter-by-chapter dossier;
- every recurring visible change is explained or remains a named residual;
- every rule exposes scope, limitations, contradictions and a falsifier;
- the same validated artifact produces the Duck view and human report deterministically;
- the selected question, admitted experiment, executed action, receipt and updated dossier agree;
- a non-winning level still produces a detailed useful world model;
- an observed win is expressible entirely in the frozen internal language and can be tested on the next level.

Score and level clears are useful evidence. Library completeness, explanatory coverage and prospective accuracy are the primary product measures.


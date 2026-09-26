# Build plan: harden the cybernetic gate before G1

> **Historical slice:** This plan records the G1 hardening frontier on 2026-09-18. Use
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for current implementation and live status.

Date: 2026-09-18  
Source family: `variants/ring9-cybernetic-gates`  
Evidence base: private Kaggle run `ring9-g0-checkpoint-v2`

## 1. Decision

G0 is complete as a control checkpoint. Do not expand the gate ladder yet. The next build is a
hardening layer between G0 and G1 that removes protocol clerical work, records production-grade
causal evidence, and makes prospective demonstrations machine-checkable inside an exact scope.

The ordering is deliberate:

1. make the binding probe easy to retrieve and impossible to forge or stale-replay;
2. record what actually changed in production before asking Duck to explain it;
3. define grounded ego answers and scoped prediction predicates;
4. repair the opening coverage policy so G1 tests direct control rather than prematurely trying
   to prove every object inert;
5. validate explanation and demonstration as G1 grades; report later consumption only when a
   subsequent gate actually uses the law.

G2 does not begin until this entire vertical slice passes.

## 2. What the G0 trace taught us

### 2.1 Control succeeded

All three target worlds acknowledged the opaque action surface and entered G1. Every malformed
answer or incomplete action declaration failed before an environment action. The environment
history contains exactly the three admitted probes.

This establishes that Duck can be constrained by a stateful controller. It does not establish
that copying the controller's fields causes Duck to understand the controller's question.

### 2.2 The current protocol tests copying

The controller creates `purpose`, `question`, `live_alternatives`, and `outcome_partition`, then
requires Duck to copy those same values back into `decision`. Copying them does not demonstrate
intent or understanding. It only introduces more opportunities for transcription failure.

The live traces show the cost:

| World | Python tool calls | rejected Python/action attempts | real actions |
|---|---:|---:|---:|
| ft09 | 11 | 1 | 1 |
| ls20 | 7 | 4 | 1 |
| vc33 | 9 | 4 | 1 |

Two worlds first used `{}` for `semantic_claims` where the controller required `[]`. All three
attempted an action without the complete binding declaration; ls20 and vc33 reconstructed the
declaration field by field.

### 2.3 The operational state is too large

`virelai('gate')`, successful `gate_answer`, and validation errors all return the full gate
snapshot. G1 puts the complete coverage ledger before `next_probe`. Tool output is capped at
roughly 1,024 tokens, so the field needed for the next action can be hidden by the coverage list.

The same full snapshot is also inserted into the per-turn prompt. This spends context on audit
detail that Duck does not need to choose the next admissible operation.

### 2.4 Pointer coverage is aimed at the wrong gate

The current coordinate-action opening creates one G1 probe per frame-zero connected component.
On the three executed frame-zero observations this yields:

| World | Frame-zero components | Current G1 opening cost |
|---|---:|---:|
| vc33 | 11 | 11 coordinate probes |
| ft09 | 65 | 65 coordinate probes |
| ls20 | 20 | 8 paired non-coordinate probes |

The 65 ft09 probes are finite, but finiteness alone is not a good experiment. G1 asks where and
how direct control occurs. Exhaustively attempting every object belongs to the later activation
and inertness gates. Requiring it here consumes the budget before Duck can explain an ego.

### 2.5 The evidence is too weak for explanation

The gate event currently stores the action result and a whole-board `board_changed` boolean. It
does not store a grounded before/after comparison, changed cells, changed-region support, local
versus remote effects, or a reference to the exact raw frames used in the comparison.

A model can cite a valid evidence ID without that ID containing the evidence needed to support
its claimed mechanism. This repeats the historical failure where schema compliance is mistaken
for model use.

### 2.6 The demonstration verifier can close a false law

The answer accepts a free-form nonempty `scope`, but the demonstration ignores it. A prediction
of `CHANGED` closes G1 whenever any board cell changes. A timer, counter, animation, or remote
effect can therefore validate a false claim about the ego. An unchanged target plus a remote
change is also collapsed into a single `board_changed=True` fact.

### 2.7 The current tests are richer than production in the wrong places

Unit tests plant `board_changed` directly and show that the state machine follows that flag. They
do not prove that the production adapter constructs a truthful scoped observation. The missing
layer is the actual join from production before/after frames to a gate outcome.

## 3. Design rule

The controller owns experimental admissibility. Duck owns interpretation.

The active gate also owns Duck's immediate objective. The overall task—deduce the world, explore
novel states, observe a win, and explain it—is deliberately not issued as one instruction. The
router decomposes it into one tight mini-goal at a time. Duck receives only the current question,
relevant admitted knowledge, allowed probes, and definition of done. Completing a gate produces a
compact world-model product that becomes input to the next mini-goal.

This is the primary behavioral mechanism. Validation and action enforcement exist to keep the
instruction honest; they are not substitutes for giving Duck a clear small job.

The controller may:

- choose or admit the next probe;
- bind the exact action and current transition to an unforgeable/stale-detecting handle;
- compute lossless and compact observational facts;
- reject unsupported evidence references or untestable predictions;
- grade a declared predicate against a declared scope.

The controller must not:

- name the ego for Duck;
- turn an integer or action number into a supplied semantic label;
- author Duck's mechanism or action law;
- treat a global delta as proof of a local causal claim;
- close a gate because prose is long or fields are populated.

## 4. Target architecture

### 4.0 Port the Captain's control shape, not its conclusions

The useful V4 prior art is the separation of concerns around the Captain:

- an assessor grades knowledge without taking an action;
- a router selects the lowest unresolved target whose prerequisites are satisfied;
- a registry maps the selected target and probe class to an admissible experiment;
- explicit predicates decide completion and dependency satisfaction;
- a durable product carries what was learned into later decisions.

Rebuild that shape around Duck. Do not port the Captain's historical semantic conclusions,
thresholds, or assumptions as facts about a new world. Duck remains the sole gameplay actor and
the author of explanations. The surrounding code is a cybernetic director: it chooses which
question is currently admissible, exposes the evidence needed to answer it, tests the answer, and
decides whether the current target is resolved.

Do not grow `EgoGateMachine` into a monolithic controller with a branch for every later gate.
Introduce a small gate kernel:

```text
GateRegistry        gate definition -> assessor, planner, product schema
DependencyGraph     prerequisites and downstream invalidation
GateAssessor        read-only grading from journaled evidence and claims
GateRouter          lowest unresolved admissible gate -> current goal
ProbePlanner        experiments that discriminate the current gate's hypotheses
ProbeDispatcher     token binding and exact action enforcement
OutcomeCompiler     production before/action/after -> observational evidence
GateJournal         claims, revisions, probes, predictions, verdicts, contradictions
MemoryProduct       compact learned law consumed by later gates
```

Adding a new gate should require a registry entry, a goal contract, an assessor, a probe planner,
and a memory-product schema. It should not require editing a central cascade of gate-specific
conditionals.

### 4.0.1 Every gate is a bounded mission with its own goal

The project North Star is not the active instruction given to Duck on every turn. The router gives
Duck only the current gate's epistemic goal. Each `GoalContract` contains:

```text
goal_id / gate_id
question
desired_knowledge
prerequisite_products
admissible_probe_kinds
coverage_obligations
required_explanation
required_prospective_prediction
completion_predicate
explicit_unknown_or_failure_states
memory_product_type
handoff_contract
reopen_predicates
```

A gate may resolve as `SATISFIED`, `NOT_APPLICABLE`, `REPRESENTATION_GAP`, or
`BLOCKED_WITH_EVIDENCE`. Populated fields or confident prose are not resolution states. A later
contradiction reopens the producing gate and invalidates dependent products until reassessment.

The initial goal catalogue below is the dependency spine, not a flat checklist. Each entry is a
parent-category target. Satisfying a parent may open evidence-driven child targets for the members,
conditions, and mechanisms Duck actually observed. Only one ready target node is locked at a time.

The initial goal catalogue is:

| Gate | Local goal | Required durable product |
|---|---|---|
| G0 Action Surface | Represent the legal intervention surface while preserving opaque action identities. | `ActionSurface` |
| G1 Ego | Determine whether control is embodied, pointer-like, god-mode, mixed, conditional, or currently unresolved; identify the controlled locus or subject and explain how each demonstrated action changes it. | `EgoLaw` |
| G2 Counter | Identify scheduled or progress-like change and define a reversible mask that removes it without erasing causal state. | `CounterModel` plus versioned `MaskLaw` |
| G3 Levers | Find interventions whose effects occur outside the acted locus and explain their conditions and remote consequences. | one or more `LeverLaw` records |
| G4 Reactions | Explain how entities respond to ego motion, contact, activation, lever effects, and state conditions. Traversability, refusal, collision, carry, and other terrain-like behavior live here when observed. | `ReactionLaw` records, including scoped `TerrainLaw` where applicable |
| G5 Environmental Forces | Establish whether state changes recur without a contemporaneous Duck intervention or known lever/reaction driver, and explain their schedule and scope. | `ForceLaw` or evidence-backed `NOT_APPLICABLE` |
| G6 Inertness | Attempt activation under a finite declared coverage policy and certify only the tested object classes and conditions as inert. | scoped `InertnessCertificate` |
| G7 Novelty Frontier | Select and reach counter-masked integer configurations absent from the observed state archive. | `NoveltyFrontier` with provenance |
| G8 Observed Win | After a win is observed, describe its boundary and mechanism in the accumulated world grammar. Never hypothesize a win as a completion shortcut. | `WinExplanation` linked to the observed terminal transition |
| Transfer | Reuse the learned grammar on a later level and record which laws survived, specialized, contradicted, or reopened. | `TransferReport` and revised laws |

Each product is a compressed, falsifiable law with evidence references and limitations. Raw records
remain in the journal, but accumulating records is not itself world-model growth.

The active prompt receives a compact `GoalCard`, not the whole catalogue. It states the current
question, why its prerequisites are satisfied, permitted probes, unresolved coverage, the answer
and prediction contract, and what would count as closure. It does not supply the semantic answer.

The overall mission is physics exploration. Before an actual terminal boundary is observed, no
gate asks Duck to infer the win state. An observed terminal transition opens a later explanation
target. Its evidence-bound description may become a forward-facing hypothesis on the next level.

### 4.1 Separate operational and audit views

Add three distinct views:

1. `virelai('gate')`: compact current checkpoint, question, status, progress counts, answer
   requirements, and the next allowed operation.
2. `virelai('next_probe')`: only the current binding probe handle, exact action payload, purpose,
   question, and alternatives. It must fit comfortably below the tool-output cap.
3. `virelai('gate_audit', ...)`: paginated coverage, evidence, answers, revisions, and reuse for
   diagnosis. This view is never injected automatically into every prompt.

Errors return `error`, the compact current gate, and one exact repair instruction. They do not
return the full audit snapshot.

### 4.2 Bind by capability, not copied prose

Replace copied envelope equality with a server-authored `probe_token` derived from the gate ID,
revision, probe ID, declared transition, and canonical action payload. Duck calls:

```python
p = virelai('next_probe')['data']
action(p['actions'], decision={'probe_token': p['probe_token']})
```

The controller resolves the token to its stored full envelope, verifies that it is still current,
verifies the exact actions and coordinates, and journals the complete controller-authored
envelope. A wrong, stale, or reused token fails before the environment callback.

This preserves hard control while removing meaningless field transcription.

### 4.3 Make G0's answer contract literal

Return a machine-readable answer template. If `semantic_claims` remains in the schema, the
template must show the literal `[]`. Missing `semantic_claims` may normalize to an empty list;
nonempty values remain forbidden. The epistemic statement remains Duck-authored.

### 4.4 Add a production `ProbeOutcome`

Capture the frame before the admitted environment action and the settled frame after it. Derive:

```text
probe_id
transition_id
before_frame_ref
after_frame_ref
action
acted_site
shape_before / shape_after
changed_cell_count
changed_cells or lossless changed-cell archive reference
changed_bbox
integer_transition_counts
changed_region_summaries
target_local_changes
remote_changes
available_actions_before / after
boundary_event
terminal_flags
limitations
```

Raw frames remain the authoritative record. The derived outcome is versioned and reproducible.
No game-engine implementation is inspected or used to infer mechanics.

### 4.5 Ground prediction scopes

Replace free-form scopes with resolvable selectors declared against a real frame:

```text
cells: exact row/column members
bbox: inclusive rectangle
region_ref: observed segmentation node plus frame reference
outside_scope: separately measured, never silently ignored
```

The predicate vocabulary is layered according to the flipbook ontology. The substrate predicates
are:

```text
NO_CHANGE
ANY_CHANGE
EXACT_CELL_DELTA
```

Footprint-form predicates require an exact declared subject at both endpoints:

```text
STILL
RECOLOR
PURE_TRANSLATION
GROW
SHRINK
DEFORM
```

`BIRTH`, `DEATH`, `SPLIT`, `MERGE`, and `AMBIGUOUS` belong to object correspondence and are
deferred until a resolver is admitted. `APPEAR` and `DISAPPEAR` are not pixel primitives. The
evidence and port ruling is recorded in
`REVIEW_H3_TRANSFORMATION_LEXICON_PIXEL_ARITHMETIC_v1_2026-09-19.md`.

Every prediction records its action, scope, predicate, expected parameters, evidence basis, and
pre-action state before the demonstration executes.

The verdict is `SUPPORTED`, `CONTRADICTED`, or `INDETERMINATE`. Only `SUPPORTED` closes G1.
Remote or out-of-scope changes are reported independently. A target-local prediction cannot be
supported by HUD or counter motion elsewhere.

### 4.6 Store an actual learned law

On successful demonstration, create a versioned `EgoLaw` artifact:

```text
law_id
mode: EMBODIED | NULL_LOCUS | COMBINATORIAL | CONDITIONAL | REPRESENTATION_GAP
subjects: grounded references or explicit null locus
opaque_action_laws
conditions
constraints
evidence_refs
demonstration_ref
competing_models
falsifier
limitations
revision
```

Later gates cite `law_id` and the specific action law they use. Reuse is a decision dependency,
not merely a statement that the old answer exists.

## 5. Repair the G1 opening

### 5.1 Keep the proven Delphi core

For each offered non-coordinate action, run the consecutive paired probes. The pair reveals
repeatability, opposition, failed transitions, conditional availability, and autonomous change.

### 5.2 Stratify coordinate probes

G1 needs to distinguish null-locus/pointer control, local object control, global control, and no
visible effect. It does not need to exhaust every object.

Construct frame-zero target classes using only observed geometry and integers:

- connected-component shape and size;
- repeated versus unique fingerprint;
- border-touching versus interior;
- large field versus small feature;
- containment/adjacency class;
- spatial zone.

Probe one deterministic representative from each distinct class, smallest discriminating set
first. After every outcome, update the live alternatives:

- target-local effect;
- remote effect;
- global effect;
- no visible effect;
- conditional or representation gap.

Expand within a class only when the existing outcomes cannot distinguish the alternatives or
when the class shows inconsistent behavior. Preserve a coverage certificate stating which
classes and members were tested and which remain unknown.

No G1 `NO_EFFECT` result may be promoted to object inertness. It means only “this intervention
at this site in this observed state produced no admitted effect.” Inertness remains a later gate.

### 5.3 G1 closure requirements

G1 closes only when all of the following pass independently:

```text
protocol       no bypass; every real action bound to the current token
coverage       Delphi pair/class plan complete or explicit representation gap
explanation    mode, subject/locus, transformation laws, conditions and falsifier grounded
prediction     recorded before action with a resolvable scope and predicate
demonstration  scoped verdict SUPPORTED
correctness    independent trace review MATCH
```

Reuse is deliberately absent from G1 closure. G1 is judged only on whether Duck found, explained,
and demonstrated direct control. The first later gate that consumes `EgoLaw` owns the separate
question of whether the law was reusable; failure there may reopen G1, but cannot be required to
finish G1 in the first place.

## 6. Work packages

### WP-H0 — Captain-style gate kernel and goal contracts

Build:

- `GateDefinition`, `GoalContract`, `GateAssessment`, and `MemoryProduct` contracts;
- a registry containing G0 and G1 first, with later gates declared but inactive;
- dependency-aware routing to the lowest unresolved admissible gate;
- read-only assessor and separate probe planner/dispatcher boundaries;
- contradiction-driven reopen and downstream product invalidation;
- a compact current `GoalCard` rendered into Duck's active prompt;
- adapters that preserve the successful G0 trace and current G1 journal as migration evidence.

Acceptance:

- G0 and G1 run through registry dispatch with no gate-specific branch in the central router;
- the router cannot expose G1 while the `ActionSurface` prerequisite is absent or invalid;
- a contradictory G1 observation reopens G1 and marks every dependent product stale;
- the active prompt contains only the current gate's goal and dependencies needed to act;
- adding a synthetic gate requires registration and its own assessor/planner/product, with no
  modification to the router;
- Duck, rather than controller-authored text, supplies the explanation and mechanism law.

### WP-H1 — Compact capability interface

Build:

- compact `gate` view;
- dedicated `next_probe` view;
- `probe_token` binding and stale/replay rejection;
- literal G0 answer template;
- compact error responses;
- full detail moved to paginated `gate_audit`;
- gated prompt instructions updated to the actual response shape.

Acceptance:

- worst-case synthetic gate brief remains below 512 estimated tokens;
- invalid, stale, replayed, wrong-action, and wrong-coordinate tokens reach zero environment calls;
- full controller-authored envelopes remain in artifacts;
- the three-world one-action trace has zero clerical action rejections;
- G0 semantics remain opaque.

### WP-H2 — Production evidence join

Build:

- before/after capture around the real callback;
- lossless diff and compact `ProbeOutcome`;
- frame references into existing raw archives;
- `virelai('evidence', id=...)` compact view;
- explicit local, remote, terminal, and limitation fields.

Acceptance:

- a planted target-unchanged/remote-changed transition remains two separate facts;
- an unchanged full board records zero changed cells;
- a shape change, translation, and recolor are reproduced from production-shaped frames;
- removing either frame or breaking the probe/event join fails loudly;
- fixtures contain no fields unavailable from the production adapter.

### WP-H3 — Scoped verifier and EgoLaw

Port basis: use the existing scoped comparison, append-only revision, and Captain
prerequisite/completion contracts identified in
`PORT_MAP_G1_H3_SCOPED_VERIFIER_EGO_LAW_v1_2026-09-18.md`. H3 is an adaptation of those proven
control shapes to the H2 production evidence record. It must not import historical semantic
conclusions or action meanings.

Build:

- resolvable scope schema;
- predicate vocabulary and tri-state comparison;
- prospective prediction journal written before action;
- versioned EgoLaw on supported demonstration;
- reopen path on contradiction and unresolved path on indeterminate evidence;
- stable `law_id` so a later gate can consume or contradict the product.

Acceptance:

- HUD-only change cannot support a target-local `ANY_CHANGE` prediction;
- remote change cannot be mistaken for target change or absence of remote effects;
- translation requires the declared subject and displacement;
- copied retrospective predictions fail the prospective timestamp/state check;
- a demonstrated law receives a stable identifier and evidence-bound scope.

### WP-H4 — Adaptive Delphi coverage

Build:

- paired non-coordinate opening retained;
- deterministic coordinate target classes;
- representative-first adaptive expansion;
- coverage certificates and explicit unknown members;
- no inertness promotion from a G1 negative result.

Acceptance:

- embodied, pointer/null-locus, mixed, conditional, no-visible-effect, and representation-gap
  fixtures take the correct branch;
- ft09's opening does not automatically require all 65 frame-zero components;
- inconsistent outcomes within one target class force expansion;
- coverage cannot close while a live control alternative lacks a discriminating observation.

### WP-H5 — Evaluation and operational telemetry

Record per world:

```text
gate queries
answer attempts and rejection reasons
probe-token failures
real environment actions
tokens and wall time to first probe and gate closure
coverage classes and expansions
prediction verdict
correctness review
EgoLaw production; later-gate consumption when applicable
```

Keep protocol, explanation, demonstration, correctness, later consumption, levels, and action
economy as separate grades. Do not collapse them into one pass merely because all schema fields
exist. `later consumption` is reported when it occurs and is not a G1 pass condition.

Acceptance:

- expected worlds with zero artifacts fail;
- package digest, model, budgets, world set, passes, and concurrency are recorded;
- human review receives the exact before/after evidence and claimed scope;
- matched comparisons reject differing execution conditions.

## 7. Validation ladder

Each work package is a checkpoint. Do not combine them into one Kaggle experiment.

1. **Gate-kernel tests:** registry extension, prerequisite routing, goal isolation, reopening, and
   dependent-product invalidation.
2. **Interface contract tests:** token binding, compact response budget, rejection before callback.
3. **Production replay:** rebuild outcomes from the v2 raw frames and planted counterexamples.
4. **Scoped-verifier replay:** prove local/remote/unchanged distinctions and tri-state verdicts.
5. **Coverage simulation:** run the adaptive plan over the recorded frame-zero grids without
   claiming any game mechanics.
6. **Local end-to-end trace:** G0 → full G1 → prediction → demonstration → EgoLaw on
   production-shaped adapters.
7. **Private Kaggle protocol smoke:** same three worlds, one admitted probe, zero clerical
   rejections expected.
8. **Private Kaggle G1 checkpoint:** full G1 on a pointer/null-locus world and an embodied world;
   independent visible-trace correctness review required.
9. **Three-world G1 confirmation:** fixed model, budgets, package, concurrency, evaluator, and
   world cohort.

## 8. Stop conditions

Do not proceed to G2 if any of these remain true:

- Duck must reconstruct controller-authored prose to act;
- the required probe is truncated from the operational response;
- evidence IDs contain only a global changed flag;
- free-form scopes cannot be resolved to observed cells or regions;
- a remote or HUD change can close a local ego prediction;
- G1 exhaustively tests every coordinate target without a discrimination reason;
- a model explanation passes without independent correctness review;
- the next gate can consume an unversioned, unsupported, or stale EgoLaw.

## 9. North Star preserved

This hardening does not make the controller solve the game. It makes the controller enforce the
scientific method while giving Duck clean evidence to interpret. Duck must still discover what
the ego is, explain how opaque actions transform it, predict a new observation, survive that
test, and produce a versioned EgoLaw. G1 ends there. G2 owns the test of whether that law is useful
while separating time and counter noise, and may reopen G1 if it finds a contradiction.

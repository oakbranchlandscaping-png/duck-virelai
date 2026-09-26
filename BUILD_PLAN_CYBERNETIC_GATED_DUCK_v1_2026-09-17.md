# Build Plan — Cybernetic Gated Duck

**Date:** 2026-09-17  
**Status:** Historical founding plan; superseded for execution status by
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` while retained as design provenance  
**Authority:** The Director's instructions in the present reset. Historical North Stars,
work orders, ring plans, and chamber rulings are port material and evidence, not authority
over this plan.  
**Initial source mine:** `variants/ring8-decision-controller/` plus the separate
`virelai-golden` opening and role readers.  
**Proposed new source variant:** `variants/ring9-cybernetic-gates/`  
**Run policy:** No Kaggle run is authorized by this document. Each live checkpoint requires
an independently packaged, manifest-verified bundle and an explicit run decision.

## 1. Objective

Build a Duck-controlled ARC agent whose standing goal before the first observed win is:

> Explore the world systematically, reduce uncertainty through controlled probes, and
> construct a stable internal model of its entities, state variables, and transition laws.

The Duck must progress through a fixed dependency ladder. It may not advance because it
named a role. For every gate it must:

1. **identify** the entity, process, or relation;
2. **explain** what it is and how it behaves in the internal ontology;
3. **predict** an observation not used to construct the explanation;
4. **use** the resulting model in later behavior.

The win is never guessed. A win is admitted only from the platform's observed boundary
signal. Afterward, Duck explains the winning transition in the language of the model it
already built.

## 2. Non-negotiable laws

1. **Action semantics are earned.** Action IDs and parameter shapes are interface facts;
   their effects are unknown until observed.
2. **The substrate is the record.** Preserve every action, every returned animation frame,
   the settled frame, boundary metadata, and the exact before/after relation.
3. **Appearance proposes; intervention decides.** Color, shape, position, and segmentation
   may generate candidates but never establish function.
4. **Identity is constructed across time.** A per-frame region ID is not a persistent
   entity. Worldlines remain revisable hypotheses grounded in sightings and deltas.
5. **No privileged background.** Every grid cell participates in the accounting. Ground,
   field, HUD, counter, and inertness are behavioral conclusions.
6. **One active epistemic gate.** Later gates remain locked until all prerequisites close.
7. **A label is not understanding.** Every closed gate has an explanation, evidence,
   falsifier, novel prediction, and demonstrated use.
8. **Contradictions are durable.** They append evidence, revise claims, and reopen dependent
   gates. They never delete the earlier record.
9. **Negative conclusions are coverage-bounded.** Inertness and absence require an explicit
   finite coverage certificate and reopen when relevant state changes.
10. **No pre-win goal predicate.** Before an observed win, the frontier objective is model
    completion and novel masked-state exploration.
11. **No self-grading.** Mechanical contract completion and semantic correctness are
    separate grades. Without an external oracle, correctness is `NOT_GRADED`.
12. **Production evidence outranks fixtures.** Every acceptance instrument must be proven
    against the actual adapter layout and must fail on a planted defect.

## 3. System architecture

```text
UNIVERSAL ONTOLOGY
  stable epistemic rules supplied in the system prompt
        |
        v
GATE MACHINE
  one durable question, coverage obligation, answer contract, and admissible action set
        |
        v
DUCK
  selects a discriminating probe, explains it, predicts outcomes, and acts
        |
        v
ENVIRONMENT
  returns frames and boundary metadata
        |
        v
EMPIRICAL WORLD MODEL
  immutable record -> deltas -> sightings -> worldlines -> mechanics -> derived roles
        |
        +---------------- evidence and revisions ----------------+
```

The ontology tells Duck what kinds of claims are legitimate. The gate machine determines
the current question and enforces participation. The empirical model remembers. Duck
interprets, proposes, predicts, and chooses among admissible probes.

## 4. Universal ontology prompt

The universal prompt is a compact constitution, not the gate schedule and not a game manual.
It must state:

- grids are observations of state and may not expose all machine state;
- actions are interventions whose meanings must be learned;
- cells and transitions are the observational substrate;
- objects, persistence, motion, roles, and variables are revisable compressions;
- causal roles are relational and require attributed effects;
- repeated visible equality is positive evidence (`HELD`), not missing data;
- identical visible states that diverge under the same action reveal path dependence;
- explanations must predict and expose their falsifiers;
- untested quiet is unknown and tested quiet is conditional;
- a win is known only from an observed platform boundary.

The prompt must not assert unverified universal mechanics, byte-identical reset, the presence
of any particular archetype, or semantic meanings for action numbers. Detailed gate-specific
definitions are delivered only when their gate opens.

## 5. Canonical records

All records are immutable, versioned, JSON-serializable, and append-only where historical.

### 5.1 `GateState`

```text
gate_id                   stable across evidence updates
kind                      interface | ego | terrain | counter | lever | force | driven |
                          inert | novelty | win_observation | win_explanation | transfer
question
prerequisite_gate_ids
status                    LOCKED | ACTIVE | ANSWER_REQUIRED | CLOSED | REOPENED |
                          NOT_APPLICABLE
opened_at_transition
required_coverage
observed_coverage
live_answer_kinds
answer_id
evidence_refs
contradiction_refs
reopen_conditions
revision
```

`gate_id` never includes the current transition or model version. Evidence changes increment
`revision`; they do not mint a new checkpoint.

### 5.2 `GateAnswer`

```text
answer_id
gate_id
answer_kind
subjects
mechanism
action_laws
conditions
constraints
evidence_refs
competing_models
falsifier
novel_prediction
demonstration_transition_id
limitations
```

A gate answer is inadmissible if it is only a label, lacks evidence, lacks a transition law,
or predicts only an observation already used to invent it.

### 5.3 `ProbeEnvelope`

```text
probe_id
gate_id
purpose                   PROBE | ROUTE | REPLAY | NOVELTY
question
actions
target_or_scope
live_alternatives
outcome_partition
enables_probe_id          required for ROUTE
declared_at_transition
```

`outcome_partition` says how possible observations distinguish the live alternatives. An
initial probe need not guess one result, but it must explain why the action is informative.

### 5.4 `ProbeOutcome`

```text
probe_id
transition_ids
observed_scope
remote_changes
admitted_counter_changes
candidate_autonomous_changes
animation_evidence
boundary_event
matched_outcome_branch
limitations
```

The comparison must never widen a missing scope silently. An unchanged target and a remote
effect are separate facts.

### 5.5 `StateAddress`

```text
settled_masked_grid_hash
mask_version
current_action_signature
route_ref
fork_partition
```

The primary novelty key is the exact counter-masked settled grid. The route is always stored
and consulted only when a fork witness proves that identical visible addresses behave
differently under the same action.

### 5.6 Grades

Every gate checkpoint reports independently:

```text
protocol          PASS | FAIL
coverage          COMPLETE | INCOMPLETE
explanation       COMPLETE | INCOMPLETE
demonstration     PASS | FAIL | NOT_RUN
correctness       MATCH | MISMATCH | NOT_MEASURED | NOT_GRADED
reuse             PASS | FAIL | NOT_YET_APPLICABLE
```

## 6. Gate ladder

### G0 — Interface and action metadata

**Question:** What interventions are currently legal and what parameters do they require?  
**Work:** Read action IDs, arity, coordinate requirements, and availability after every step.  
**Closure:** The current action surface is represented without assigning semantic effects.  
**Ongoing invariant:** Any availability change updates the record and may alter admissible probes.

### G1 — Ego and direct influence

**Question:** Where and how does the agent directly influence the world?  
**Opening:** Run the Delphi finite opening: consecutive paired trials for every simple action;
finite frame-zero target coverage for a coordinate action; preserve all returned frames.  
**Answers:** embodied, null-locus/pointer, combinatorial, or conditional control.  
**Explanation:** identify the controlled subject or locus, give the action-to-transformation
map, movement/selection law, constraints, evidence, falsifier, and a novel prediction.  
**Demonstration:** execute the prediction and later reuse the learned mapping.

### G1B — Ground, walls, and embodiment constraints

**Applicability:** Only after an embodied ego closes.  
**Question:** What does the ego traverse, what refuses it, and under which conditions?  
**Explanation:** traversable extent, displacement-accounted ground exchange, refused bearings,
conditional constraints, contact/carry effects, and prediction.  
**Null-locus disposition:** `NOT_APPLICABLE`, not “absent.”

### G2 — Counter and removable process noise

**Question:** Which visible process is scheduled or monotone with action/frame progression?  
**Explanation:** physical support, complementary fill/empty representation, tick law, rate,
direction, reset behavior, boundaries, coupling, and uncertainty.  
**Product:** A versioned mask derived from observed support. Masking begins only after evidence
admits the process and remains reversible for audit.  
**Demonstration:** predict a counter transition under a new action and show that masking makes
two otherwise equivalent gameplay states converge.

### G3 — Levers and remote effects

**Question:** Which interventions on one subject produce effects elsewhere?  
**Explanation:** control surface, activation modality, affected subjects, transformation,
direction, magnitude, conditions, repetition, reversal, saturation, and lag.  
**Demonstration:** predict a remote effect from an untouched qualifying state.  
**Dependency:** ego, terrain where applicable, and admitted counter effects are subtracted
before lever attribution.

### G4 — Environmental forces

**Question:** What recurring change is not explained by the chosen intervention, ego, counter,
or an admitted driver?  
**Explanation:** subject, recurrence law, trigger conditions, periodicity/state dependence,
interaction with other entities, and falsifier.  
**Reopen rule:** If a force explains a prior lever effect, reopen G3.

### G5 — Driven objects and coupled mechanics

**Question:** Which objects change as dependents of levers, forces, or other state variables?  
**Explanation:** drivers, response law, conditions, lag, exclusivity, relay behavior, and
conservation relationship.  
**Demonstration:** predict the dependent transformation under a new valid trigger.

### G6 — Inertness coverage

**Question:** What remains behaviorally silent under the applicable interaction set?  
**Explanation:** exact object × action × state coverage, self-effects tested, remote effects
tested, and reopen conditions.  
**Closure:** A bounded negative certificate, never an eternal claim.

### G7 — Novel masked-state exploration

**Question:** Which reachable counter-masked integer configurations remain unseen?  
**Work:** Build the walked state graph, replay known routes, choose frontier edges, and lazily
split visible addresses when fork witnesses reveal hidden state.  
**Explanation:** why the target address is novel, which admitted laws predict the transition,
and which route reaches the probe point.  
**Purpose:** `NOVELTY`, never pre-win `PURSUE_WIN`.

### G8 — Observed win

**Question:** Has the environment externally marked a level or game completion?  
**Closure:** Only an observed platform signal. Persist the complete pre-action state, action,
returned frame sequence, settled successor, and boundary metadata.  
**No causal inference:** The record proves the edge won, not why.

### G9 — Win explanation and transfer

**Question:** How does the learned grammar describe the observed winning boundary?  
**Explanation:** entities, variables, conditions, final transformation, competing predicates,
and falsifiers.  
**Demonstration:** apply the explanation prospectively on the next level, reconfirm preserved
laws, and revise on failure. A witnessed route remains evidence even when its explanation dies.

## 7. Controller behavior

1. Present one active gate and its stable ID every decision cycle.
2. Show the question, current evidence, remaining coverage, live alternatives, and admissible
   next probes.
3. Validate the exact `ProbeEnvelope` before the environment callback.
4. Reject stale gates, illegal actions, semantically empty probes, and routes that name no
   enabled probe. Rejection consumes no environment action.
5. Execute exactly the accepted action sequence. Never substitute, reorder, or append.
6. Join the result to the exact probe and persist the outcome.
7. When coverage is complete, stop accepting further ordinary actions until Duck submits a
   `GateAnswer` or a justified representation-gap report.
8. Validate answer structure and evidence existence mechanically.
9. Require a genuinely prospective prediction and demonstration before closure.
10. Open the next gate only from the dependency graph.
11. Reopen gates and invalidate dependent closures when contradictions require it.
12. Enter an explicit degraded state on controller failure; never silently fall back to
    unconstrained play.

## 8. Port map

Mine and adapt before writing replacements:

| Needed capability | Primary port material |
|---|---|
| Duck tool loop, retry, action validation | `variants/ring8-decision-controller/ARC3-Inference/inference/agent/tool_agent.py` |
| Atomic decision/action binding | `inference/framework/virelai_controller.py` and production bridge in `tool_agent.py` |
| Raw journal and frame archive | `inference/framework/virelai_runtime.py`, `game_observer.py` |
| Universal ontology prompt | `inference/agent/virelai_ontology.py` plus current flipbook canon |
| Delphi opening | `Universal_Solver_v3_5/discovery/rover_gambit/` |
| Finite golden opening | separate `virelai-golden/golden/captain/opening.py` and vendored `virelai_golden/captain/opening.py` |
| Pixel arithmetic | `virelai_golden/substrate/` and Ring 8 arithmetic artifacts |
| Worldlines and provenance | `virelai_golden/weave/`, `virelai_continuity.py` |
| Ego readers | `virelai_golden/roles/ego_body.py`, `ego_pointer.py` |
| Ground and wall | `virelai_golden/roles/ground.py`, `wall.py` |
| Counter and mask | `virelai_golden/roles/counter.py`, `mask.py`, `virelai_clock.py` |
| Levers and effects | `virelai_golden/roles/lever.py`, `virelai_experiments.py` |
| Persistent semantic model | `virelai_world_model.py`, semantic compiler, physics grammar code |
| Win boundary | `virelai_win_capsule.py`, level lessons |
| Pilot evidence | `runs/kaggle-ring8-decision-controller-pilot-v2/` |

No downloaded game-engine implementation may be inspected to derive mechanics or grade
solver correctness.

## 9. Build stages

### Stage A — Freeze provenance and repair measurement

- Snapshot the exact parent source and existing dirty-tree status without modifying it.
- Create a complete new variant; do not use a partial overlay.
- Record source hashes and package-manifest expectations.
- Unify or explicitly join production decision records and Virelai archives.
- Repair the pilot evaluator to read the real production layout.
- Add a production-shaped regression that fails under the old path mismatch.
- Re-evaluate pilot v2 and preserve the direct finding: 46 non-predictive envelopes, 46
  unmatched comparisons, 46 no-change revisions.

**Exit:** The evaluator reports the executed trace accurately and a planted missing-join defect
fails loudly.

### Stage B — Gate kernel and ontology

- Replace ephemeral focus identity with stable `GateState` plus revisions.
- Add the strict dependency graph and closure/reopen semantics.
- Add `GateAnswer`, `ProbeEnvelope`, `ProbeOutcome`, and independent grades.
- Remove pre-win `PURSUE_WIN` from controller mode.
- Make detailed outcome data visible without requiring Duck to print a returned value.
- Install the corrected compact universal ontology only in gated mode.

**Exit:** A fixture cannot access G2 before G1 closure, cannot act without an admissible probe,
and can retrieve its prior answer on a later turn.

### Stage C — First vertical slice: interface + ego

- Refresh legal action metadata every turn.
- Port the finite Delphi/golden opening as an explicit coverage plan.
- Support embodied, pointer, combinatorial, conditional, and representation-gap outcomes.
- Require the full ego explanation.
- Require and execute a novel ego prediction.
- Carry the ego answer into a later controller decision.

**Exit:** Identify–explain–predict–use succeeds end to end on production-shaped pointer and
embodied fixtures, including a negative-control failure.

### Stage D — Terrain and counter

- Add embodied-only ground/wall subgate.
- Port counter candidates, complementary support, schedule/rate evidence, and boundaries.
- Produce reversible, versioned counter masks.
- Add masked state addressing and convergence evidence.

**Exit:** Duck explains terrain where applicable, explains a counter, predicts it, and uses
the mask to recognize a repeated gameplay state.

### Stage E — Causal grammar

- Add lever, environmental-force, and driven-object gates in dependency order.
- Port scoped/remote/autonomous comparison and append-only revisions.
- Require mechanism-specific explanations and novel predictions.
- Reopen lever claims when autonomous recurrence defeats attribution.

**Exit:** At least one remote mechanism is explained and prospectively demonstrated, while a
false lever fixture is rejected.

### Stage F — Inertness and novelty frontier

- Build explicit finite interaction coverage certificates.
- Reopen inertness on relevant state change.
- Build exact counter-masked novelty addresses, route retention, and fork witnesses.
- Restrict pre-win frontier actions to model-supported novelty exploration.

**Exit:** The controller distinguishes tested inertness from unknown and reaches a novel state
without using a guessed goal predicate.

### Stage G — Win explanation and cross-level transfer

- Preserve exact observed winning boundaries.
- Require retrospective grammar explanation after the win.
- Carry alternative predicates and falsifiers into the next level.
- Require reconfirmation and demonstrated reuse.

**Exit:** Duck describes an observed win in its learned model language and uses that description
to make a prospective next-level prediction.

### Stage H — Matched evaluation

- Freeze model, reasoning settings, budgets, world cohort, concurrency, package contents,
  and evaluation code across comparisons.
- Grade protocol, coverage, explanation, demonstration, correctness, reuse, level depth,
  action economy, and failure modes separately.
- Use repeated runs before causal performance claims.

**Exit:** We can distinguish controller compliance, actual model acquisition, and gameplay
outcomes without conflating them.

## 10. First work package

The first implementation package is `WP-GATE-00-01`, limited to Stages A–C.

### Deliverables

1. Complete `ring9-cybernetic-gates` source fork with provenance manifest.
2. Correct production-layout pilot evaluator and regenerated v2 evaluation.
3. Stable gate kernel with hard G0 -> G1 dependency.
4. Corrected compact ontology prompt.
5. Dynamic action-metadata record.
6. Finite ego opening coverage plan.
7. Gate-answer submission and visible validation response.
8. Prospective ego demonstration.
9. Later-turn reuse check.
10. Production-shaped pointer, embodied, conditional, and negative fixtures.

### Acceptance trace

```text
G0 reads the current action surface
  -> G1 opens with one stable gate ID
  -> every required opening probe executes exactly once or twice as specified
  -> no disallowed action reaches the environment
  -> evidence accumulates without changing gate identity
  -> Duck submits an explanatory ego model
  -> Duck predicts a new ego transition
  -> the exact transition tests that prediction
  -> G1 closes or revises
  -> the next gate opens only after closure
  -> a later decision demonstrably uses the ego action law
```

### Local release gate

- All inherited relevant tests pass.
- New tests use the production adapter shape.
- A planted artifact-path defect fails the evaluator.
- A label-only answer is rejected.
- A prediction copied from prior evidence is rejected.
- A mismatched executed action cannot update the model.
- A controller failure cannot fall back to legacy unstructured action.
- Raw observations remain byte-identical after semantic revisions.

Only after this trace passes is a Kaggle G0/G1 checkpoint worth packaging.

## 11. Kaggle checkpoint design

Each gate checkpoint uses the same Duck model and fixed execution conditions. Initial cohort:
`vc33`, `ft09`, and `ls20`, because together they exercise pointer and embodied interaction and
already have comparable historical artifacts. The checkpoint evaluator must inspect executed
actions and evidence, not prompt vocabulary.

For G0/G1 it reports:

- action metadata refreshed correctly;
- opening coverage completed;
- rejected actions consumed zero environment steps;
- one stable gate accumulated the evidence;
- ego answer supplied identity/modality/action law/constraints;
- evidence references existed;
- a new prediction was attempted and correctly joined;
- explanation correctness under independent visible-trace review;
- learned action law reused later;
- levels and action counts, reported but not treated as the primary gate.

Comparisons across different models, budgets, world sets, concurrency, or package contents are
descriptive only and never causal evidence.

## 12. Principal risks and controls

| Risk | Control |
|---|---|
| Duck satisfies schema with empty prose | Require evidence, transition law, falsifier, new prediction, and demonstrated reuse |
| Controller performs the reasoning for Duck | Controller checks structure and evidence existence; Duck authors the explanation; correctness is independently graded |
| Gate becomes permanently stuck | Finite coverage plans, representation-gap state, explicit reopen/defer rules, no silent bypass |
| Navigation bypasses probing | `ROUTE` must name the enabled future probe and is unavailable before a control law exists |
| Counter masking deletes causal evidence | Preserve raw frames; masks are derived, versioned, and reversible |
| Low-level records masquerade as understanding | Gate answers and mechanics must compress observations into predictive laws |
| Prompt causes verbosity or meandering | Keep ontology compact; put only current gate detail in per-turn context |
| Fixture differs from Kaggle adapter | Production-shaped fixtures plus executed-artifact evaluator and falsifier-first path tests |
| Semantic compiler errors corrupt memory | Raw journal is append-only and upstream of semantic compilation |
| Lucky win is called understanding | Win record and win explanation graded separately; explanation requires prospective transfer |

## 13. Definition of project success

The project succeeds when, on previously unseen ARC environments, Duck repeatedly:

1. executes the prescribed cybernetic probe order;
2. constructs a stable evidence-grounded world model;
3. identifies and explains each applicable archetype;
4. predicts and demonstrates its transition laws;
5. uses prior explanations to choose later probes and actions;
6. explores novel counter-masked states without guessing a goal;
7. observes a real win boundary; and
8. describes that win using the entities, variables, and physics grammar it learned.

Gameplay score remains an important consequence and efficiency measure. It is not a substitute
for the explanatory and predictive trace.

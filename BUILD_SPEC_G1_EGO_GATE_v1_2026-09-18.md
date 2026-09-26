# Mini-build specification: G1 Ego gate

Date: 2026-09-18  
Status: historical design specification, now implemented and subsequently revised by the
click-only archetype exit and integrated G1/G2 contract. Live G1 success remains unconfirmed; see
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`.

## 0. Governing operating model

The gate ladder is a decomposition of the world-understanding task into tight instructions for
Duck. At any moment Duck receives one active mini-goal, the observations relevant to that goal,
the experiments it may run, and a concrete definition of done. It is not asked to solve the ARC
world in one act of reasoning.

Each gate runs the same cybernetic loop:

```text
mini-goal -> discriminating probe -> observation -> explanation -> prospective test -> product
```

The product becomes admitted prior knowledge for the next mini-goal. The code exists to keep Duck
on the active question, preserve evidence, and prevent unsupported closure. It does not replace
Duck's interpretation or reveal the answer. Observations that may matter later are retained in the
journal but do not create side quests or change the current gate's grade.

## 1. Single purpose

G1 answers one question:

> Where and how does Duck directly influence the world?

The gate succeeds only when Duck can identify the control mode and controlled subject or locus,
explain the demonstrated opaque action laws, and correctly predict one new ego-related transition.

G1 is not judged on winning, level progress, counter discovery, terrain understanding, lever
discovery, environmental forces, inertness, novelty seeking, or later reuse. Observations relevant
to those topics may be journaled for later gates, but they neither help nor hurt the G1 grade.

## 2. Claim boundary

A G1 success supports only this claim:

> Under the tested conditions, Duck found a direct control relationship, described its subject or
> locus and action-conditioned transformation, and prospectively demonstrated that description on
> a scoped observation.

It does not establish that:

- the identified subject is always controllable;
- every available action is understood;
- unchanged targets are inert;
- remote changes are levers;
- recurring changes are counters or forces;
- movement constraints or terrain are understood;
- the learned law transfers to another level;
- the world can be solved.

## 3. Goal contract

```text
goal_id: G1-EGO-v1
gate_id: G1-EGO
question: Where and how does Duck directly influence the world?
prerequisite: current G0 ActionSurface
desired_knowledge:
  - control mode
  - controlled subject or locus
  - opaque action -> observed transformation laws
  - conditions, uncertainty, competing model, falsifier
admissible_probe_kinds:
  - consecutive simple-action pair
  - representative coordinate intervention
  - prospective ego-law demonstration
memory_product: EgoLaw
completion: evidence-bound explanation plus supported prospective prediction
reopen: contradictory evidence or changed action surface
```

Control mode is Duck's conclusion, chosen from `EMBODIED`, `POINTER_OR_NULL_LOCUS`, `GOD_MODE`,
`MIXED`, `CONDITIONAL`, or `UNRESOLVED`. The controller may expose these as the hypothesis space,
but it must not choose the answer for Duck.

## 4. Gate states

```text
WAITING_FOR_G0
    -> SURVEY
    -> PROBING
    -> ANSWER_REQUIRED
    -> DEMONSTRATION_REQUIRED
    -> SATISFIED
```

At any point, new action metadata or contradictory evidence may move the gate to `REOPENED`.
Inadequate observational representation may move it to `REPRESENTATION_GAP` with exact missing
evidence recorded. That is honest protocol behavior, but it is not epistemic success for G1; the
campaign remains blocked at G1.

## 5. Captain-style components used in this mini-build

Build only the reusable substrate G1 needs:

1. `GateRegistry` registers G0 and G1.
2. `GateRouter` selects G1 only when a current `ActionSurface` exists.
3. `G1Assessor` grades evidence and the submitted `EgoLaw` without choosing actions.
4. `G1ProbePlanner` selects the next discriminating Delphi probe.
5. `ProbeDispatcher` binds that probe to a short-lived token and exact action payload.
6. `OutcomeCompiler` turns production before/action/after data into scoped observations.
7. `GateJournal` preserves probes, raw frame references, outcomes, claims, and revisions.
8. `EgoLaw` is the compact product handed to the next gate.

The existing `EgoGateMachine` is port material. Its enforcement and journaling can be retained,
but its G0/G1 branching, copied probe envelope, global `board_changed` demonstration, exhaustive
coordinate sweep, and reuse requirement must not become the new architecture.

## 6. Active GoalCard shown to Duck

Duck receives a compact card similar to:

```json
{
  "gate_id": "G1-EGO",
  "goal": "Find the directly controlled subject or locus and explain how tested opaque actions transform it.",
  "known": {"action_surface_id": "...", "available_actions": ["ACTION1", "ACTION6"]},
  "live_alternatives": ["EMBODIED", "POINTER_OR_NULL_LOCUS", "GOD_MODE", "MIXED", "CONDITIONAL"],
  "coverage_remaining": {"simple_action_pairs": 1, "coordinate_classes": 3},
  "next_operation": "QUERY_NEXT_PROBE",
  "closure_requires": ["explanation", "scoped_prediction", "supported_demonstration"]
}
```

The card states the question and obligations. It contains no controller-authored ego identity or
action semantics.

## 7. Probe strategy

### 7.1 Simple actions

Use the Captain's Delphi opening for each offered non-reset, non-coordinate action: two
consecutive executions. Consecutive pairing makes repeatability, opposition, refusal, conditional
availability, and unrelated scheduled change visible without assigning semantics in advance.

The pair is an opening obligation, not proof by itself. Every outcome remains an observation until
Duck explains the relationship.

### 7.2 Coordinate actions

Do not click every frame-zero component automatically. Form observational target classes from
integer and geometry facts available in the visible grid:

- connected shape and size;
- repeated or unique fingerprint;
- border or interior position;
- large field or small feature;
- containment and adjacency;
- spatial zone.

Probe one deterministic representative from the smallest set that can discriminate target-local,
remote, global, conditional, and no-visible-effect alternatives. Expand a class only when outcomes
are inconsistent or the remaining hypotheses cannot otherwise be distinguished.

Record all untested classes. A negative coordinate result means only that this action at this site
in this state caused no admitted effect.

### 7.3 Adaptive stopping

The planner stops opening probes when either:

- there is sufficient scoped evidence for Duck to submit an ego explanation and a novel test; or
- the remaining alternatives cannot be distinguished with the available action interface and
  observation representation.

It does not continue probing merely to accumulate records.

## 8. Production evidence

Every admitted action produces a `ProbeOutcome` joined to its exact probe token:

```text
evidence_id
probe_id / gate_revision / transition_id
before_frame_ref / after_frame_ref
opaque action and coordinates
shape before / after
lossless changed cells or archive reference
changed bounding boxes and integer transitions
acted-site local changes
changes outside the acted site
available actions before / after
terminal boundary
limitations
```

The compiler reports geometry and differences. It does not call a changed shape “the ego,” call a
remote effect “a lever,” or call a recurring effect “the counter.” Those are model claims Duck must
make at the appropriate gate.

## 9. EgoLaw submitted by Duck

```text
law_id
revision
control_mode
subjects_or_loci
identity_description
action_laws:
  opaque action
  transformation
  scope
  observed conditions
  evidence references
constraints_observed_during_control
competing_model
falsifier
limitations
```

`constraints_observed_during_control` may preserve facts for the later Reactions gate, but G1 does
not require Duck to explain walls, traversability, or contact mechanics.

## 10. Demonstration

Before the demonstration action, Duck must commit:

```text
action and coordinates
subject_scope
predicate
expected relation or transformation
because: cited EgoLaw clause
novelty: why this exact transition is not one of the supporting observations
```

The verifier resolves the declared scope against the production before/after frames and returns
`SUPPORTED`, `CONTRADICTED`, or `INDETERMINATE`. A global board change cannot support a local
subject claim. `INDETERMINATE` never closes the gate.

## 11. G1 scorecard

G1 has independent grades:

| Grade | Pass condition |
|---|---|
| Protocol | Every environment action after G0 was bound to the current G1 probe token. |
| Coverage | Required Delphi pairs and adaptive coordinate classes completed, or an exact representation gap was recorded. |
| Explanation | Duck identified mode, subject/locus, action transformations, conditions, uncertainty, and falsifier with evidence. |
| Prediction | The demonstration was committed before execution and addressed a resolvable scope. |
| Demonstration | The scoped verifier returned `SUPPORTED`. |
| Correctness | Independent review of visible frames agrees with Duck's explanation. |

`G1 SATISFIED` requires all six passes. Winning, level count, action economy, counter knowledge,
lever knowledge, and later reuse are reported separately and cannot change this result.

## 12. Checkpoint ladder

### Checkpoint A: gate kernel

- G0 and G1 are registry entries rather than branches in a central state machine.
- G1 cannot route without a valid `ActionSurface`.
- a changed action surface reopens G0 and invalidates the active G1 revision.

### Checkpoint B: evidence and token path

- compact `GoalCard` and `next_probe` calls work;
- stale, replayed, or altered tokens reach zero environment callbacks;
- production before/action/after data creates lossless scoped outcomes.

### Checkpoint C: G1 reasoning loop

- Delphi pairs and adaptive coordinate representatives are planned;
- Duck can inspect compact evidence and submit an `EgoLaw`;
- the prospective scoped demonstration yields a tri-state verdict.

### Checkpoint D: local evaluation

Use production-shaped adapters and recorded frames without reading game-engine mechanics. Include
embodied, pointer/null-locus, mixed, conditional, no-visible-effect, remote-only, counter-noise, and
representation-gap cases. Fixtures may contain only fields production emits.

### Checkpoint E: private Kaggle G1 run

Run a bounded pilot first. If the protocol path is clean, run the fixed comparison cohort with the
same model, budgets, package, concurrency, and evaluator. Review every visible explanation against
its before/after trace. The result reports G1 only; it makes no solver-level claim.

## 13. Implementation order

1. Extract the minimal registry, router, goal, assessment, journal, and product contracts.
2. Migrate G0 unchanged in behavior and prove the completed checkpoint still passes.
3. Add compact GoalCard and token-bound next-probe capability.
4. Replace the production outcome join with scoped lossless evidence.
5. Port the Delphi pair planner and add adaptive coordinate classes.
6. Implement `EgoLaw`, prospective prediction, and scoped tri-state verification.
7. Build the G1-only evaluator and human review packet.
8. Package the bounded Kaggle checkpoint only after local acceptance passes.

The first coding slice is steps 1 and 2. Its acceptance criterion is architectural: G0 behaves as
before through the new registry and router. It does not attempt to solve G1 yet.

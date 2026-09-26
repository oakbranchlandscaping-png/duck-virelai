# Cybernetic target tree

Date: 2026-09-18  
Status: governing architecture for the fresh Duck build

Current implementation status and document authority are tracked in
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` and `DOCUMENTATION_INDEX_2026-09-20.md`.

## 1. Mission

Duck's primary objective is:

> Explore and describe the physics of this local section of the ARC grid multiverse.

It is not instructed to infer an unseen win state. It receives one bounded scientific target at a
time, builds a cumulative internal model, and explores states implied by that model. A win may be
encountered during this exploration. Only after the terminal transition is observed may Duck
describe the goal in the language of its learned physics.

## 2. The structure is a target tree

The major gates form the dependency spine:

```text
Action Surface
    -> Ego
    -> Counter
    -> Levers
    -> Reactions
    -> Environmental Forces
    -> Scoped Inertness
    -> Counter-masked Novelty Exploration
    -> Observed Win Explanation
    -> Cross-level Goal Transfer
```

This is not a flat checklist. Each major gate is a parent-category target. When Duck establishes a
category, the controller opens child targets for the mechanisms that were actually observed.

```text
parent target: establish that a category exists, identify its members, and state its boundary
child target: explain and demonstrate one member, law, condition, or interaction
```

The tree is generated from evidence rather than populated in advance with assumed game mechanics.
If a parent category is not applicable, it produces an evidence-backed `NOT_APPLICABLE` product
and no child subtree opens.

## 3. Parent and child examples

### Ego parent

The parent establishes the control mode and controlled subject or locus. Evidence may then open:

- one action-law target per directly controlling opaque action;
- movement and displacement targets for embodied control;
- selection and acted-locus targets for pointer control;
- conditional-control targets where the channel depends on state;
- refusal/contact targets later consumed by the Reactions branch.

### Counter parent

The parent establishes which visible process represents time, progress, or removable scheduled
noise. Evidence may then open:

- physical-support and phase targets;
- rate and direction targets;
- reset and boundary targets;
- state-coupling targets;
- reversible-mask validation.

The parent's blocking product is counter identity plus a demonstrated reversible mask. Once that
product exists, the lever branch may open while a background boundary monitor remains armed.
Lever probes advance the same process and eventually expose death or respawn at the extremum.
That observation finalizes the boundary field; exact rate semantics may revise without blocking
the causal search.

### Lever parent

G3 is the broad location and identification sweep. It establishes an inventory of visual objects
whose click or contact produces an attributable effect after ego and counter subtraction. It
repeats a positive only enough to confirm that the object is a lever. It does not require a full
mechanism law.

The parent binds an exhaustive probe protocol: click every eligible visual object in CLICK worlds;
collide or attempt contact with every eligible visual object in NAV worlds; perform both ordered
arms in HYBRID worlds. Finding a lever is a logical consequence of faithfully executing this
protocol in a functioning world, not a numerical quota. A record with no lever is a failed
measurement that reopens coverage, state, contact, and attribution; it is never accepted as
evidence that the level contains no levers.

Every confirmed lever opens its own G4 subtree. A visual object that first appears during G4 or
any later gate is registered as a new entity-specific G3 obligation before the system assigns it a
causal role. Earlier closed G3 records remain valid for their stated objects and state scopes.

### Reactions parent

G4 performs the in-depth study of each confirmed lever and the entities or regions that respond to
ego motion, contact, activation, lever effects, or world state. Each confirmed G3 lever opens a
focused reaction subtree that asks:

- activation modality and affected subject;
- transformation direction and magnitude;
- lag, repetition, reversal, and saturation;
- preconditions and failure conditions;
- collision and movement refusal;
- traversability and exchange;
- carrying, pushing, following, or avoidance;
- consumption, toggling, transformation, or destruction;
- driver-dependent and phase-dependent behavior.

### Environmental-forces parent

After known ego, counter, lever, and reaction effects are accounted for, unexplained recurring
change may open targets for:

- autonomous motion;
- periodic or state-dependent change;
- attraction, repulsion, spreading, decay, or regeneration;
- interaction between an autonomous process and known entities.

The labels above describe the questions a branch may ask. They are not claims that any particular
world contains those mechanics.

## 4. Target lifecycle

Every target node has its own `GoalContract` and runs:

```text
LOCKED
  -> PROBING
  -> MODEL_REQUIRED
  -> PROSPECTIVE_TEST_REQUIRED
  -> SATISFIED
```

A parent is satisfied when its own bounded category question is answered. Its satisfaction may
instantiate children through a registered child factory. Children are separately assessed; their
later failure does not retroactively mean the parent never discovered the category, but a genuine
contradiction reopens the parent and invalidates descendants that depend on the contradicted fact.

The router selects one ready node at a time. A node is ready only when its prerequisites are valid.
Duck receives that node's GoalCard and relevant admitted products, not the entire unresolved tree.

Unexpected observations are journaled and may create dormant candidate nodes. They do not steal
focus from the locked target. They become eligible only when their dependency path opens.

A new visual object is a special lifecycle event: it receives a persistent identity and an
entity-specific G3 classification node. If G4 created the object, the current G4 evidence is
retained, but semantic study of the new object waits for its G3 classification.

## 5. World-model products

Each satisfied node produces a compact, versioned, falsifiable law. The active world model is the
graph of these products and their dependencies, not the raw event ledger.

Each product records:

```text
law_id and revision
target node and parent
subjects and scopes
transformation or relation
conditions and limitations
supporting evidence
prospective demonstration
falsifier
dependencies
status: active, stale, contradicted, or superseded
```

Raw frames, deltas, and probe records remain available for audit. They are compressed into laws
only through Duck's explanation and a successful prospective test.

## 6. How the first win is treated

Before a win is observed:

- no target asks Duck to guess the terminal state;
- no evaluator rewards similarity to an imagined goal;
- novelty means an unvisited counter-masked integer configuration;
- exploration is driven by unresolved physics targets and reachable novel states.

If a win occurs during any admitted experiment, the system preserves the exact terminal boundary,
the preceding state, the action, and the active learned laws. The current gate remains graded on
its own goal. The observation also creates a dormant `Observed Win Explanation` target.

When its prerequisites are ready, Duck explains the observed win using its internal grammar:

```text
which entities and relations mattered
which state conditions held
which learned laws produced the terminal transition
what changed at the boundary
what remains uncertain
```

The resulting `ObservedGoalLaw` must refer to an actual terminal transition. It cannot be created
from a hypothesis about what would probably win.

## 7. Turning the observed win into a later-level goal

On the next level, the previous `ObservedGoalLaw` becomes a forward-facing
`TransferredGoalHypothesis`. It supplies a concrete outcome to pursue in the language of the
learned model while remaining subject to verification in the new level.

The later-level loop is therefore:

```text
inspect new action surface and world
-> test which prior laws transfer
-> specialize or reopen changed laws
-> translate the observed goal law into the new layout
-> use the verified physics model to plan toward it
-> observe whether the terminal boundary recurs
```

The prior goal law is useful knowledge, not an unquestionable answer. If the level changes the
mechanism, Duck returns to the affected target subtree and learns the specialization.

## 8. Controller implications

The gate infrastructure requires:

- a dependency graph of target-node instances;
- parent definitions with evidence-driven child factories;
- one active target lock;
- dormant candidate nodes for out-of-focus observations;
- versioned products and downstream invalidation;
- explicit distinction between `DISCOVERED_CATEGORY` and child-mechanism satisfaction;
- an observed-terminal event that can open the win-explanation branch without pre-authoring it;
- a transfer layer that converts an observed goal law into a falsifiable next-level hypothesis.

The controller supplies sequence, focus, evidence discipline, and memory. Duck supplies the
world interpretation and physics grammar.

## 9. Prompt architecture

The controller and prompt divide responsibility into three layers:

1. A stable universal ontology gives Duck the flip-book language of integer grids, literal cell
   arithmetic, entities, transformations, control archetypes, levers, reactions, hidden state,
   scoped inertness, observed wins, and cross-level transfer.
2. A stable cybernetic mission tells Duck to discover physics through interaction and record
   keeping, retain competing explanations, use the smallest authorized discriminating probe, and
   promote laws only after the gate's prospective evidence requirement is met.
3. A volatile GoalCard and evidence view names the single binding target, its unmet requirements,
   admitted prior products, and the next authorized action.

The ontology is a hypothesis language, not a list of facts about the current world. The GoalCard
controls focus, and only observations can establish a world fact. Full wording, research basis,
verification, and the package boundary are recorded in
`BUILD_SLICE_UNIVERSAL_ONTOLOGY_PROMPT_2026-09-20.md`.

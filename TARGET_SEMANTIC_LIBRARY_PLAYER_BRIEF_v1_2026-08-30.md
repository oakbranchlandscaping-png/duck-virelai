# TARGET — THE SEMANTIC LIBRARY AS A PLAYER'S WORLD MACHINE

**Type:** `TARGET_SEMANTIC_LIBRARY_PLAYER_BRIEF`  
**Version:** v1  
**Date:** 2026-08-30  
**Status:** GOVERNING BUILD TARGET — design target, not a claim that every field is
already implemented.  
**Consumer:** the untouched Duck LLM, playing blind after the Virelai Captain's probe.  
**Upstream:** V4 perception, flipbook objects, weave, mechanics, role inference, and
role-specific probe subtrees.  
**Ontology:** `variants/ring-ontology/ARC3-Inference/inference/agent/prompts.py`.

---

## 0 · THE TARGET IN ONE SENTENCE

After probing a level, Virelai gives the player a compact, evidence-grounded operating
manual for the current world: **what kind of world this is, what the player controls,
which objects have meaningful semantic roles, and the measured transition law beneath
each role.**

The player receives the polished Semantic Library. It does not receive the perception
pipeline that constructed it.

---

## 1 · THE ARCHITECTURAL CHAIN

```text
cells and actions
    → visual objects
    → persistent worldlines
    → verbs and couplings
    → semantic roles
    → role-specific probe subtrees
    → semantic object dossiers
    → player world-machine brief
```

The lower layers are necessary provenance. They are not the player-facing product.

- **Perception** records forms and cell changes.
- **The weave** establishes persistent identity across successive frames and retains the
  transition record.
- **Mechanic inference** identifies action-conditioned effects and relations between
  worldlines.
- **Semantic roles** compress those mechanics into operational meanings.
- **The Captain's subtree** asks the remaining questions appropriate to each role.
- **The Semantic Library** is the reconstructed state machine.
- **The brief** is the useful projection of that machine for an intelligent player.

---

## 2 · THE CONSUMER TEST

Every player-facing field must pass this question:

> Does this information help a blind player identify an actionable object, predict the
> result of an action, avoid repeating a settled experiment, or choose a useful new
> experiment?

If not, it remains in diagnostic provenance and does not enter the brief.

The following are therefore internal by default:

- raw sightings and visual-object lists;
- worldline member lists and merge/split diagnostics;
- internal `###` identifiers;
- seal machinery and implementation vocabulary;
- raw coverage percentages without an operational meaning;
- the Captain's chronological transcript;
- bookkeeping questions delegated to the player.

---

## 3 · THE SEMANTIC LIBRARY IS THE STATE MACHINE

The library is not an object catalog. It is a structured account of:

1. **State variables** — persistent objects and properties whose values matter.
2. **Current values** — the latest observed state of those variables.
3. **Available actions** — movement, click, contact, wait, or other declared actions.
4. **Transition laws** — how actions and autonomous schedules change state variables.
5. **Preconditions** — conditions under which a transition applies.
6. **Causal relations** — which semantic object drives which affected object or region.
7. **Unknown transitions** — actionable state/action pairs not yet settled.
8. **Terminal transitions** — observed win, loss, reset, or level advancement.

Every assertion must decompress to the weave's recorded observations. If the record does
not support a field, the field is `UNKNOWN`; the renderer never fills it by appearance.

---

## 4 · THE TOP-LEVEL PLAYER BRIEF

The brief renders in this order:

### 4.1 · WORLD TYPE

Exactly one of:

- `NAV` — the player controls an embodied object through movement actions.
- `CLICK` — the player has God Mode and may target grid locations directly.
- `HYBRID` — both embodied movement and direct targeting are available.
- `UNKNOWN` — the probe did not distinguish the interface.

### 4.2 · CONTROL

For NAV/HYBRID:

- the ego object's integer class or component classes;
- current location and footprint;
- action-to-displacement map;
- stride or magnitude;
- collision and passability facts;
- inconsistent or untested controls.

For CLICK/HYBRID:

- God Mode availability;
- valid targeting method;
- any observed targeting constraints.

### 4.3 · COUNTER / AUTONOMOUS PROCESS

For each supported autonomous process:

- integer class, location, size, and shape when observed;
- update rate and direction;
- period, reset, saturation, or terminal behavior when measured;
- independence from action choice;
- whether its meaning as budget, life counter, score, or world mechanic is established
  or still unknown.

### 4.4 · LEVER SUMMARY

One line per lever, using stable player handles:

```text
Lever A — class 6 at (12,20), 9 cells: contact → Region B moves right by 4;
period 3; remote; established 4/4.
```

### 4.5 · EXPANDABLE SEMANTIC DOSSIERS

Full role-specific details defined in §5.

### 4.6 · STRUCTURE

Only movement-relevant ground, walls, barriers, passages, or targeting constraints.

### 4.7 · EXPLORATION FRONTIER

- actionable objects already tested;
- experiments that produced no effect;
- targets attempted but not reached;
- untested actionable targets with coordinates;
- repeat tests owed for period, saturation, direction, or hidden conditions.

### 4.8 · WIN EVIDENCE

- `NO WIN OBSERVED`, or
- the exact pre-state, action, and environment-reported terminal transition;
- a separately labeled win hypothesis;
- the observation that would falsify that hypothesis.

### 4.9 · BEST NEXT EXPERIMENT

One ranked recommendation, phrased as:

```text
ACTION — what to do
QUESTION — which unknown transition this tests
PREDICTION — what the current library predicts
FALSIFIER — what result would disprove that prediction
```

---

## 5 · ROLE-SPECIFIC DOSSIER CONTRACTS

All dossiers share:

- stable player handle;
- semantic role;
- evidence status: `ESTABLISHED`, `PROVISIONAL`, or `UNKNOWN`;
- observed identity: integer class, location, size, shape, and current state;
- observation count and agreement where meaningful;
- one concise falsifier for every inferred rule.

### 5.1 · EGO

- component integer classes;
- footprint and current location;
- movement action map;
- displacement magnitude and direction;
- collision behavior and passable substrate;
- coordinated components;
- state-dependent or inconsistent controls.

### 5.2 · COUNTER / AUTONOMOUS PROCESS

- integer class, location, size, and current value or phase;
- autonomous update law;
- rate, direction, period, reset, and saturation;
- affected or coupled objects;
- independence from action choice;
- terminal correlation, if observed;
- meaning unknown unless interaction establishes it.

### 5.3 · LEVER

**Identity**

- integer class;
- location;
- size and shape;
- current state or phase.

**Activation**

- click, contact, movement direction, sequence, or other method;
- required actor;
- reachability;
- number of valid activations tested.

**Affected object or region**

- stable handle;
- integer class;
- location, size, and shape;
- local or remote relation to the lever.

**Transition law**

- toggle, cycle, displacement, growth, shrinkage, transfer, one-shot, saturation, or
  honestly unknown;
- direction and magnitude;
- period and current phase;
- delay;
- determinism/agreement.

**Conditions**

- known preconditions;
- tested states;
- sequence or history dependence;
- hidden condition suspected but not established.

**Evidence boundary**

- what is directly observed;
- what is inferred;
- what remains unknown;
- the next falsifying test.

### 5.4 · DEPENDENT OBJECT

- drivers;
- response to each driver;
- response magnitude, direction, lag, and period;
- exclusivity or multiple-driver behavior;
- whether it also acts as a lever;
- terminal candidacy.

### 5.5 · ENVIRONMENTAL FORCE

- autonomous transformation law;
- schedule or triggering condition;
- affected objects;
- interaction with ego, counters, and levers;
- evidence separating it from an action-conditioned lever.

### 5.6 · INERT / STRUCTURAL

- integer class, location, size, and shape;
- passable or blocking behavior;
- actions and interactions tested;
- evidence supporting inertness;
- coverage boundary: what has not been tested.

Inert objects render only when they constrain action or close a tempting but exhausted
branch. Decorative inventory is omitted.

---

## 6 · EVIDENCE LANGUAGE — HARMONIZED WITH RING ONTOLOGY

The ontology primes the player to reason in observed transitions. The brief uses the
same terms consistently:

- **Observed transition** — a recorded before/action/after fact.
- **Established rule** — repeated observations agree and the named falsifier has not
  fired.
- **Provisional rule** — evidence supports the rule but coverage or agreement is
  incomplete.
- **Unknown transition** — not tested or not distinguishable from confounds.
- **Autonomous process** — change independent of the chosen action or target.
- **Lever** — an attributed intervention with a repeatable effect after ego and
  autonomous changes are excluded.
- **Dependent object** — changes in response to another object's transition.
- **Win observation** — only an environment-reported level or game transition.

The brief never uses `cov`, `B1`, `B2`, `FIRM`, `PROVISIONAL` seals, or `###` as
untranslated player-facing vocabulary.

---

## 7 · DATA-PROVENANCE GATE

Before implementing a displayed field, the build must name its existing producer in V4:

```text
display field → semantic-library field → mechanic/role read → worldline edge(s)
              → exact action-indexed cell deltas
```

The initial audit must classify every target field:

- `AVAILABLE` — already represented explicitly;
- `DERIVABLE` — computable without new environment actions from retained weave data;
- `PROBE-OWED` — requires a role-specific Captain experiment;
- `NOT RETAINED` — observed transiently but discarded before the library;
- `UNAVAILABLE` — current machinery cannot support it.

No renderer may promote `DERIVABLE`, `PROBE-OWED`, or `UNAVAILABLE` into a factual value.

This gate is especially binding for causality, period, current phase, preconditions, and
hidden-state dependence. Observation coverage alone is not causal attribution.

---

## 8 · BUILD LADDER

### Phase 0 — Field census

Audit the V4 golden run against every field in §§4–5. Produce the provenance table from
§7. No behavior change.

**Exit:** every displayed field has a named producer or a named absence.

### Phase 1 — Semantic Library contract

Define a pure, serializable world-machine contract containing:

- world interface;
- current state variables;
- semantic objects keyed by stable player handles;
- action transition rules;
- causal edges;
- exploration frontier;
- terminal observations.

**Exit:** fixture dictionaries validate without rendering prose.

### Phase 2 — V4 adapter

Translate retained weave/mechanic/role output into the contract. The adapter performs no
new semantic inference except explicitly approved `DERIVABLE` computations. It preserves
observed/inferred/unknown distinctions.

**Exit:** ls20, vc33, and ft09 fixtures produce valid machine-readable libraries.

### Phase 3 — Role-subtree completion

Connect existing Captain probes to dossier fields. Identify which questions are already
answered and which subtree branches are not yet executed.

**Exit:** each discovered ego, counter, lever, dependent object, environmental force,
and relevant structural object has a depth report with named gaps.

### Phase 4 — Player brief renderer

Render §§4–6 with summary-first, expandable detail. The renderer is pure and cannot
invent, reconcile, or strengthen claims.

**Exit:** a human can play the fixture using the brief without viewing the grid history.

### Phase 5 — Human grading

For each fixture, compare:

1. the library contract;
2. the rendered brief;
3. observable game reality;
4. the action a human would choose from the brief.

Grade separately:

- identity correctness;
- semantic-role correctness;
- transition-law correctness;
- actionability;
- honesty of unknowns.

### Phase 6 — Duck handoff

Only after human approval, replace Ring 7's report content while preserving its proven
transport path and untouched Duck host.

**Exit:** the exact brief reaches Duck once before its first action and its response can
be graded for actual use.

---

## 9 · FIXTURES

- **ls20** — NAV: ego, action map, terrain, counter, contact lever, reachability.
- **vc33** — CLICK: God Mode, multiple levers, shared/remote affected region,
  directional transition law, observed win if retained.
- **ft09** — CLICK: multiple local levers, independent regions, finite periods, cheap
  win behavior.
- **One zero-score NAV world** — incomplete library and honest unknowns.
- **One life-loss world** — counter/life semantics and terminal loss observation.

The binding first proof is Level 1. Cross-level win transfer remains a later target.

---

## 10 · ACCEPTANCE

The target is met when the player receives, for a real level:

1. the correct world type;
2. the correct ego or God Mode description;
3. supported autonomous processes separated from action-conditioned effects;
4. every established lever identified by class, location, and size;
5. every lever connected to its affected object or region;
6. each supported reaction law stated with direction, magnitude, period, locality,
   conditions, and evidence where available;
7. structural constraints relevant to action;
8. a compact tested/untested frontier;
9. honest win evidence;
10. one useful next experiment.

The brief must contain no construction-history burden that the player must resolve.

The final human test:

> A blind player can use the brief to predict what an action will do and choose a
> rational next action. If the brief cannot do that, the Semantic Library is not yet a
> player-facing state machine, regardless of how much data it contains.

---

## 11 · OUT OF SCOPE FOR THIS TARGET

- changing the Ring Ontology prompt;
- changing Duck's model, decoding, or native action loop;
- Kaggle packaging before offline approval;
- claiming a complete win theory before a win transition is observed;
- exposing raw weave diagnostics to compensate for missing semantic fields;
- solving cross-level memory and win falsification in the first build.

---

*The weave constructs the object. The subtree explains its role. The Semantic Library
reconstructs the machine. The player receives the operating manual.*

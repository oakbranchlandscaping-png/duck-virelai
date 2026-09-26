# AUDIT — SEMANTIC LIBRARY PORT MAP

**Type:** `AUDIT_SEMANTIC_LIBRARY_PORT_MAP`  
**Version:** v1  
**Date:** 2026-08-30  
**Status:** BUILD-READY FINDING  
**Governing target:** `TARGET_SEMANTIC_LIBRARY_PLAYER_BRIEF_v1_2026-08-30.md`  
**Consumer:** untouched Duck LLM after the Ring 7 Captain handoff

---

## 0. Verdict

The proposed player brief can be built mainly by porting and recombining code that
already exists in this repository.

The principal failure is not lack of perception and not lack of a working handoff.
It is a missing compilation layer.

Today the chain ends as:

```text
V4 observations -> worldlines and role verdicts -> Ring 7 visual survey -> Duck
```

It needs to end as:

```text
V4 observations -> worldlines -> measured transition rules
                -> worldline-keyed semantic state machine
                -> ontology-aligned player brief -> Duck
```

Ring 7 proves that the report reaches the model intact. Keep that transport fixed.
Replace the report producer and renderer.

Nearly every desired field has one of three existing sources:

1. the V4 golden weave, which has the best persistent identity and grounded evidence;
2. the V4 semantic-library machinery, which already stores rich mechanics but uses
   unstable region slots;
3. V3.5 contracts and renderers, which already describe a world as an actionable
   machine.

The correct build is therefore a **worldline-keyed semantic library**: V4 truth and
identity, enriched with the best V4/V3.5 mechanic readers, rendered in the language of
the Ring Ontology.

---

## 1. What is already proven

### 1.1 The transport is proven

Ring 7 already:

- finalizes the Captain report;
- fingerprints the exact text;
- persists it as an artifact;
- attaches it exactly once in a user-role provider payload;
- verifies the attached content against the persisted fingerprint.

Source:

- `variants/ring7/ARC3-Inference/inference/framework/solver.py`
  - `_ring63_finalize_report`
  - `_ring63_request_observer`

This is no longer the active uncertainty. The handshake should be treated as a sealed
boundary while the content is rebuilt.

### 1.2 V4 already sees persistent objects

V4's capture and weave provide:

- visual regions with integer class, exact cells, cell count, anchor, bounding box and
  normalized shape;
- persistent worldlines across successive states;
- edge verbs including still, move, grow, shrink and recolor;
- exact cell-level transition signatures;
- action targeting and action-to-worldline attribution;
- action-conditioned and action-independent change marginals;
- coupled-object relations;
- role verdicts for ego, counter, lever, reactive-dependent, inert, ground and wall;
- ego action bearings and refused/observed controls;
- systematic click and collision coverage;
- repeated lever probing and preliminary mechanism classification.

Primary sources:

- `virelai_v4/capture/clay.py`
- `virelai_v4/weave/worldline.py`
- `virelai_v4/weave/edge.py`
- `virelai_v4/weave/transition_signature.py`
- `virelai_v4/weave/coupling.py`
- `virelai_v4/weave/role_read.py`
- `virelai_v4/weave/ego_read.py`
- `virelai_v4/weave/lever_witness.py`
- `virelai_v4/weave/coverage_sweep.py`

### 1.3 Rich mechanic machinery already exists

V4's older semantic-library branch already represents:

- object geometry and semantic role;
- action reaction counts;
- causes and caused-by relations;
- counter rates and budget estimates;
- lever effect subjects;
- rigid displacement vectors;
- non-rigid cell-count changes;
- effect locality;
- cycle length;
- direction labels;
- saturation;
- observation counts and agreement.

Primary sources:

- `virelai_v4/library/semantic_library.py`
- `virelai_v4/library/physics_accumulator.py`
- `virelai_v4/library/cycle_probe.py`
- `virelai_v4/library/field_card.py`
- `virelai_v4/library/nav_atlas.py`

These are not speculative utilities. The V4 Captain contains live dispatch paths for
cycle probing and lever-effect characterization, and the physics accumulator writes
measured effects into the library.

### 1.4 V3.5 already contains the right conceptual contracts

V3.5 has reusable templates for:

- activation method: click, contact or adjacency;
- lever identity and effect region;
- transition class, cycle length, direction, saturation and observation depth;
- current and goal configurations;
- a complete `WorldMachine`;
- causal ledgers and baseline-subtracted attribution;
- a structured narrative for an LLM consumer;
- solved-level capture and cross-level mechanic memory;
- named unknowns.

Primary sources:

- `Universal_Solver_v3_5/contracts/lever_artifact.py`
- `Universal_Solver_v3_5/discovery/physics/cycle_probe.py`
- `Universal_Solver_v3_5/discovery/causal/causal_ledger.py`
- `Universal_Solver_v3_5/discovery/causal/attribution_engine.py`
- `Universal_Solver_v3_5/observer/narrative_renderer.py`
- `Universal_Solver_v3_5/observer/relational_extractor.py`
- `Universal_Solver_v3_5/execution/level_transition.py`
- `Universal_Solver_v3_5/contracts/mechanic_memory.py`
- `Universal_Solver_v3_5/execution/level_unknowns.py`

---

## 2. Why the current Ring 7 card is insufficient

Ring 7's current adapter is `_card_dict_from_captain` in
`variants/ring7/ARC3-Inference/inference/framework/solver.py`.

It exports:

- run metadata;
- world type and grid dimensions;
- a list of worldlines reduced to ranges, anchors, boxes, roles and coverage;
- a limited ego movement map;
- a parsed exploration frontier;
- lever partners with a coarse mechanism label.

That is a diagnostic survey. It does not expose the reconstructed machine.

The current reduction discards or omits:

- integer class in the player-facing worldline row;
- current object state;
- exact action-conditioned transition law;
- displacement vector and magnitude;
- cycle period and current phase;
- effect observation count and agreement;
- counter rate and direction;
- activation method and required actor;
- preconditions and tested conditions;
- null experiments tied to a semantic object;
- observed terminal transitions;
- a ranked experiment stated as prediction and falsifier.

Worse, the adapter currently places `RoleVerdict.band1_coverage` in a field named `cov`.
Coverage means that the object's self-state was observed over that many steps. It does
**not** mean that the object caused a change that many times. Any renderer that phrases
this as effect or causal evidence overstates the record.

The card therefore answers:

> What visual things did the Captain catalogue?

The player needs:

> What can I control, what changes when I act on it, and which useful transition remains
> unknown?

---

## 3. The reusable architecture

### 3.1 Authoritative identity: V4 worldlines

Every semantic entity must be keyed by a V4 worldline, not by a transient region slot.

Reason:

- regions are per-frame perceptual cuts;
- the legacy V4 library can mint many region entries for one persistent thing;
- worldlines are the weave's explicit answer to persistence through change.

Internal IDs may remain numeric, but the renderer assigns stable player handles:

- `Ego`
- `Counter A`
- `Lever A`
- `Region A`
- `Force A`

Internal `###` IDs do not enter the player brief.

### 3.2 Authoritative evidence: the V4 capture log and weave

Every semantic rule must cite observations ultimately recoverable from:

- `frame_record_log`;
- node cuts and node actions;
- worldline steps and edges;
- transition signatures;
- action attribution;
- coupling and lever-witness results;
- role-specific probe records.

The semantic library is a derived read over this substrate, not a second independent
belief system.

### 3.3 Reused schema: V4 library plus V3.5 machine contracts

Port the fields, validation rules and pure classifiers. Do not port the old region-keyed
identity assumption.

The central objects should be:

```text
WorldMachineBrief
  world_type
  controls
  entities[]
  transition_rules[]
  structural_facts[]
  frontier[]
  terminal_observations[]
  next_experiment

SemanticEntityDossier
  handle
  worldline_id                 # internal provenance only
  role
  identity
  current_state
  activation
  transition_rules[]
  evidence_summary
  unknowns[]

TransitionRule
  actor_handle
  action
  target_handle
  preconditions
  operation
  direction
  magnitude
  period
  delay
  locality
  observations
  agreement
  status                       # ESTABLISHED / PROVISIONAL / UNKNOWN
  evidence_refs[]
  falsifier
```

This is an adaptation of V3.5's `LeverArtifact`, `TransitionProfile`,
`GoalConfiguration` and `WorldMachine`, generalized to all six ontology roles.

### 3.4 Player projection: ontology-aligned prose

The renderer should follow the governing target in this order:

1. world type;
2. control;
3. counter/autonomous process;
4. lever summary;
5. expandable role dossiers;
6. relevant structure;
7. exploration frontier;
8. win evidence;
9. best next experiment.

This combines V3.5's readable narrative style with its field-card hierarchy. It must
render semantic facts, not expose the construction transcript.

---

## 4. Field-by-field port map

Legend:

- **PORT** — usable source and producer already exist.
- **ADAPT** — algorithm/schema exists but must be re-keyed or generalized.
- **DERIVE** — evidence is retained; add a pure read.
- **RETAIN** — currently computed but discarded; preserve a structured result.
- **PROBE-OWED** — current probing does not establish the claim.
- **NEW** — genuinely new policy or integration work.

| Player field | Status | Best source | Required treatment |
|---|---|---|---|
| World type | PORT | V4 library header and action roster | Normalize to NAV/CLICK/HYBRID/UNKNOWN. |
| God Mode | PORT | declared action roster | State ACTION6 availability and targeting constraints only when observed. |
| Ego identity | PORT | `role_read`, `ego_read`, worldline geometry | Render integer class/components, current anchor, footprint and shape. |
| Ego action map | PORT | `ego_read.action_bearings` | Render observed displacement per action; separate refusals and untested actions. |
| Ego stride | DERIVE | action bearings | Use measured vector magnitude, never assumed unit stride. |
| Passability/walls | PORT | `ground_read`, `wall_read`, `NavAtlas` | Render only movement-relevant facts and blocked edges. |
| Counter identity | PORT | `role_read` plus worldline geometry | Assign handle and observed identity. |
| Counter rate/direction | ADAPT | legacy `SemanticLibrary` counter fields; worldline trajectory | Recompute at worldline grain and include denominator. |
| Counter period/reset | DERIVE/PROBE-OWED | worldline fingerprints across actions/lives | Detect only when recurrence/reset is actually observed. |
| Counter meaning | PROBE-OWED | terminal correlations/interactions | Never call it fuel, score or budget from appearance alone. |
| Lever identity | PORT | lever role verdict plus worldline geometry | Render class, anchor, size, shape and current state. |
| Activation method | DERIVE | targeted action attribution and NAV contact record | CLICK when explicitly targeted; CONTACT when ego contact triggers it; otherwise unknown. |
| Lever partner | PORT | `lever_witness`, coupling and mechanism results | Join by worldline ID; assign player handle. |
| Effect region | ADAPT | V4 `LeverEffect`, transition signatures | Store exact changed cells and affected worldline, not just bounding box. |
| Local/remote/global | ADAPT | V3.5 `EffectLocality`; V4 geometry | Port locality classifier and state its threshold. |
| Rigid direction/magnitude | PORT/ADAPT | V4 `physics_accumulator`, weave MOVE edges | Re-key measured vector by lever and partner worldlines. |
| Grow/shrink/recolor | PORT | transition signature and edge verb | Preserve operation plus exact cell delta. |
| Toggle/cycle | RETAIN | V4 cycle probe and mechanism classifier | Store structured period and supporting fingerprint sequence, not label alone. |
| Directional mechanism | ADAPT | V4 legacy cycle probe | Port spatial direction estimation. Current weave classifier uses cell-count monotonicity and cannot name spatial direction. |
| Saturation | RETAIN | mechanism fingerprint sequence | Preserve number of consecutive null responses and state at saturation. |
| Delay | DERIVE/PROBE-OWED | press-indexed worldline transitions | Add lagged response read; unknown until supported. |
| Determinism/agreement | PORT/ADAPT | legacy effect counts/agreement; repeated weave events | Compute identical-rule count over comparable conditions. |
| Preconditions | ADAPT/PROBE-OWED | causal ledger pattern; state/action history | Start with explicit observed state and actor/action conditions; do not infer untested rules. |
| Sequence/history dependence | ADAPT/PROBE-OWED | frame log and V3.5 causal ledger | Compare same action from same visible state when possible; name hidden-state suspicion only on divergent transitions. |
| Inert evidence | PORT | coverage sweep and no-effect records | Tie each null result to target, action and count. |
| Tested/not reached/untested | PORT | collide/click coverage state | Stop parsing rendered text; expose a structured frontier producer. |
| Win transition | DERIVE | level counter change plus immediately preceding capture/action | Preserve exact pre-state, action and environment-reported advancement before reset. |
| Win explanation | NEW/PROBE-OWED | observed win plus competing causal rules | Separate observation, hypothesis and falsifier. Do not claim necessity from one success. |
| Best next experiment | NEW | semantic unknowns plus Captain reachability | Rank one falsifying experiment; this is policy, not perception. |

---

## 5. Important retained-data losses

The current pipeline sometimes computes the right thing and then keeps only a weak label.
These losses should be repaired before adding new probing.

### 5.1 Mechanism results lose the proof

The V4 weave mechanism probe keeps fingerprint sequences only for the current lever and
then stores:

```text
lever worldline -> partner worldline -> "TOGGLE" / "CYCLE" / ...
```

That discards:

- cycle period;
- observations used;
- recurrence indices;
- current phase;
- exact direction vector;
- saturation depth;
- the fingerprint sequence needed to audit the verdict.

Change the classifier result from a string to a structured immutable result. The string
may remain as a derived display property for compatibility.

### 5.2 The frontier is converted to text and parsed back

Ring 7 calls `coverage_roster(ctx)` and parses its prose with regular expressions.
The underlying Captain already owns the structured sets. Add a pure structured reader,
then let both the diagnostic renderer and player renderer consume it.

### 5.3 The legacy effect store is region-keyed

`SemanticLibrary.record_lever_effect` preserves useful measurements, but its subject and
lever keys are region IDs. The semantic machine must either:

- record the same measurement directly at worldline grain; or
- bind each region observation to its worldline at the observation's node before storing
  the semantic rule.

A late join by current geometry is unsafe after movement, deformation or recoloring.

### 5.4 Terminal transitions are not first-class in the Ring 7 card

The frame log and runtime know that a level advanced. Capture the transition before the
level reset clears local state:

- full pre-win visible state reference;
- action and target;
- changed worldlines/cells;
- environment-reported result;
- resulting level state.

This is the V4 equivalent of V3.5's `capture_level_example` and should be ported as an
observation recorder, not as V3.5's old win hypothesis.

---

## 6. What should not be ported

Do not port the following as governing architecture:

- V3.5's full solver or planner;
- old ring 1–5 model modifications;
- the region-keyed object minting behavior of the V4 legacy library;
- appearance-based semantic labels;
- raw worldline rosters as the player product;
- diagnostic seal and merge/split vocabulary;
- prompt instructions that ask Duck to reconstruct the machine from raw evidence;
- a guessed goal configuration before a win is observed;
- keyword-based proof that Duck used the report.

V3.5 is a mine for contracts, algorithms and presentation. V4's golden weave remains the
source of truth.

---

## 7. Claim-safety rules

The compiler and renderer must enforce these distinctions:

### Observation is not causality

`band1_coverage = 20` means the object was observed across 20 steps. It does not mean a
lever affected it 20 times.

### Correlation is not activation

A coupled pair is a candidate mechanism. A lever requires action attribution or a lever
witness. Autonomous co-motion belongs to counter or environmental-force analysis.

### A recurrence label requires its period

If the record supports `CYCLE`, the result must retain the recurrence distance. If the
distance was discarded, render `cycle observed; period not retained`, not a guessed N.

### A directional label requires a spatial vector

Monotonic cell-count change supports growth or shrinkage, not spatial direction. Render
direction only from centroid/anchor/cell translation.

### A silent press is evidence with a boundary

It supports “no visible response under this observed condition.” It does not prove the
object is globally inert or the mechanism permanently saturated.

### One win proves a terminal transition, not a complete rule

The environment-reported advancement is established. The causal explanation remains a
hypothesis until competing explanations are tested.

---

## 8. Recommended build sequence

### Phase A — Freeze and fixture the proven handoff

- make no semantic change to Ring 7 report attachment;
- retain exact payload fingerprint auditing;
- keep vc33, ft09 and one zero-score world as fixed output fixtures.

### Phase B — Author the worldline-keyed contract

- implement `WorldMachineBrief`, `SemanticEntityDossier`, `TransitionRule`,
  `EvidenceRef`, `FrontierExperiment` and `TerminalObservation`;
- require explicit unknowns instead of missing-field ambiguity;
- assign stable player handles after role resolution.

### Phase C — Compile the facts V4 already has

- identity and geometry;
- roles;
- ego control map;
- counter trajectories;
- lever-to-partner relations;
- transition verbs, vectors and magnitudes;
- ground, walls and reachability;
- no-effect and incomplete-coverage evidence.

No Captain behavior change is required for this phase.

### Phase D — Preserve structured mechanism evidence

- replace string-only mechanism results with a structured result;
- retain recurrence period, phase, direction, depth, null streak and fingerprints;
- adapt V4's legacy cycle and effect classifiers to worldline partners.

### Phase E — Add terminal observation capture

- port the observation half of V3.5 `capture_level_example`;
- record the exact winning transition before level-local reset;
- render observation separately from explanation and falsification.

### Phase F — Render the operating manual

- implement the governing target's fixed section order;
- render only operationally useful semantic facts;
- hide internal IDs and provenance machinery by default;
- keep a machine-readable JSON artifact beside the exact text sent to Duck.

### Phase G — Offline human grading

For vc33, ft09 and a zero-score world:

1. run the full Captain probe;
2. render the semantic machine;
3. ask whether a blind human can predict the effect of each established control;
4. compare every sentence against the recorded transition;
5. reject unsupported or ambiguous claims;
6. only then attach it to Duck.

### Phase H — Prove use, not receipt

Once the content passes human grading, require Duck's first reasoning turn to name:

- one established rule it is using;
- one remaining unknown;
- the action it will take;
- its prediction;
- its falsifier.

Grade the model's generated fields, not vocabulary echoed from its prompt.

---

## 9. Minimum viable semantic card

The first implementation does not need every future inference. It is complete enough to
test when it can reliably produce:

```text
WORLD
  Type: CLICK
  Control: God Mode; click any supplied coordinate.

COUNTER
  Counter A: class 2, top-right, 8 cells.
  Observed rule: loses 1 cell after each action, independent of target (12/12).
  Meaning: unknown.

LEVERS
  Lever A: class 6 at (12,20), 9 cells.
  Activation: click inside its footprint.
  Effect: Region A moves right by 4 cells (3/3 observations).
  Mechanism: period 3; current phase 1.
  Locality: remote.
  Unknown: whether the effect saturates after a full cycle.

FRONTIER
  Tested: Lever A, three times.
  No visible effect: Region C, one click.
  Untested: class 4 at (8,31).

WIN
  No win observed.

NEXT EXPERIMENT
  ACTION: click Lever A twice.
  QUESTION: does its affected region return after period 3?
  PREDICTION: Region A returns to its phase-0 position.
  FALSIFIER: it does not return after the third total activation.
```

The numbers above are illustrative, not claims about a specific game. The important
property is that every operational sentence has a source, denominator and evidence
boundary.

---

## 10. Acceptance conditions

The rebuild is successful when all are true:

1. The Ring 7 attachment and fingerprint proofs remain unchanged and pass.
2. Every semantic entity is keyed internally by worldline identity.
3. The player card contains no raw object census as its main content.
4. Every lever names its activation method and affected entity, or says `UNKNOWN`.
5. Every claimed mechanism retains the evidence needed to audit it.
6. Coverage counts are never rendered as causal observation counts.
7. Direction is never inferred from cell-count monotonicity.
8. Null results state the tested action and condition.
9. An observed level advance creates a first-class terminal observation.
10. A blind human can use the card to predict at least one useful transition or select a
    genuinely novel experiment.

---

## 11. Final engineering judgment

The repository does not need another broad survey card and does not need a new perception
stack. It needs one disciplined integration:

> **Compile the V4 weave into the semantic machine V3.5 was designed to express, but use
> worldlines as identity and the Ring Ontology as the language boundary.**

That preserves the strongest work from every generation:

- Ring 7: proven delivery to an untouched Duck;
- Ring Ontology: the model's prior about what an ARC world is;
- V4: grounded perception, persistent identity and empirical mechanics;
- V3.5: machine contracts, causal organization, expandable presentation and solved-level
  memory.

The remaining work is substantial, but it is integration and evidence preservation—not
an invention problem.

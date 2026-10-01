# Build plan: G4 NAV branch

**Type:** `BUILD_PLAN_G4_NAV_COMPLETION` · **v1** · **2026-10-01**  
**Author:** Sol (Alpha build seat), signed  
**Status:** IMPLEMENTED LOCALLY through G4-C; live NAV validation remains pending
**Reviewed base:** `fbbc7f4` (R9-R18/G9-A)  
**Cross-level state at preparation:** R9-R18 is committed; carried lever hypotheses are graded by
the next level's own G3 probes and never certify a lever by themselves  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

**Implementation note (Sol, 2026-10-01):** The target-bound intervention, evidence-derived control
map, demonstrated-stand router, production refused-contact path, controller-owned G3 contact
sweep, and route-versus-contact separation through G4-A/G4-B/G4-C are built. The dedicated NAV
contract tests pass. This is local evidence; it does not claim a completed ls20 live trace.

## 0. North Star and scope

Duck explores a visible ARC world through controlled interaction, builds a stable internal model,
observes a win rather than guessing it, and describes the observed goal in the language of the
physics it learned.

The gate order remains:

```text
G0 action surface
-> G1 ego
-> G2 counter mask
-> G3 lever inventory
-> G4 lever mechanics
```

This plan builds the **NAVIGATION branch of G4**. It does not infer hidden game mechanics, inspect
downloaded engine implementations, solve HYBRID worlds, or alter the question asked by any gate.
NAV must satisfy the same epistemic standard as CLICK while using a different actuator.

The governing probe strategy is unchanged:

- CLICK: click every eligible visual object in controller order;
- NAV: find the embodied ego, then attempt footprint contact with every eligible visual object;
- G2 masks bookkeeping noise;
- G3 locates the levers;
- G4 studies the confirmed levers in depth.

## 1. Evidence boundary at plan time

### Directly inspected in this planning pass

- active Ring 9 gate, controller, observation, attribution, G4, memory, life, and level code;
- the current R9-R18 commit, including level freeze, per-level restart, and G9-A carry;
- Ring 9's NAV/collide prior-art packet and NAV ontology doctrine;
- the separate `virelai-golden` navigator and its focused tests;
- Virelai v4 collide, contact, navigation, and coverage donors identified by the prior-art packet;
- focused active tests: **116 passed**;
- focused Golden navigation tests: **5 passed**.

### Existing live evidence

- Ring 9 has served-run evidence that G1 can identify and explain the ls20 embodied ego and that G2
  can discover, demonstrate, mask, and lock its counter.
- Ring 9 has no completed live NAV trace that carries a confirmed BODY lever through G3 into G4.
- CLICK G4 is built through G4-C. Its evidence engine is useful prior art, but CLICK success is not
  NAV success.

### Builder reports not promoted by this plan

Golden's historical documents report live arrival, enumeration, graph starvation, lost bearings,
and later repairs. This pass verified the current algorithms and tests, not every historical live
record. Those reports guide planted-defect tests; they are not treated as fresh direct observations.

## 2. Architectural ruling proposed for ratification

The shared epistemic spine survives. The actuator changes.

```text
                         branch-invariant evidence spine
                    mask -> attribution -> anatomy -> orbit -> relations -> law
                                           ^
                                           |
CLICK actuator: one target-bound coordinate action
NAV actuator:   a target-bound contact procedure ending in one contact transition
```

A CLICK intervention is naturally one action token. A NAV intervention is not. It is a procedure:

```text
resolve current ego and target
-> route over demonstrated ground
-> make a footprint contact attempt
-> classify the contact outcome
-> admit only that terminal contact transition as the lever activation observation
```

Approach steps remain lossless evidence. They update the entity ledger, counter baseline, life
record, and route map. They do **not** advance a lever orbit or grade a lever prediction.

This is the core branch boundary. Copying the CLICK runner and replaying the final movement action
would create false lever identities and false state novelty.

## 3. Current active structure

### Reusable without changing its epistemic role

| Component | Current capability | NAV use |
|---|---|---|
| G0 action metadata | assigns `NAVIGATION`, `CLICK_GOD_MODE`, or `HYBRID` | retain |
| G1 Delphi opening | paired opaque actions, embodied ego explanation, prospective demonstration | compile a structured control map from its evidence |
| Counter mask | reversible total mask and stable ignored baseline | retain; never let monitoring hold G4 |
| Entity ledger | level-local identity, recolour/translation continuity, reset return | resolve current ego and target during routing |
| Observation scope | ego, counter, target, ground, and contact partitions | retain and harden refused-contact production |
| BODY attribution | positive, null, ambiguous, boundary dispositions | retain |
| G4 anatomy | exact counter-masked response channels | retain after branch-neutral wording |
| Orbit engine | exact masked addresses, null/recurrence, confirmation | retain for contact epochs only |
| Relation grader | per-region effects and elsewhere effects | retain after intervention identity is generalized |
| Memory and life record | record, cards, recall, deaths, persistence tiers | extend with NAV procedure state |
| Level freeze and carry | prior-level model, hypotheses only | keep independent of the NAV slice |

### CLICK assumptions that must be removed or isolated

1. `controller_executor.next_owned_step` returns Duck immediately for every non-CLICK world.
2. G3 stores the accepted intervention as one raw action object.
3. G4-A maps an action back to a lever by raw action equality.
4. G4-B also infers the acted lever by raw action equality.
5. Several NAV levers can share the same final movement action.
6. G4-A assumes consecutive action presses are consecutive lever activations.
7. G4-C defines novelty as action plus masked board, without a target/contact identity.
8. Controller-rendered G3/G4 prose says “click” even when the shared evidence is BODY contact.

### NAV shell defects that must be closed before G4 can consume it

1. Duck currently improvises each route.
2. G1 stores all action laws as prose and only one prospective demonstration has a structured
   displacement. The route service needs a machine-readable, evidence-derived bearing map.
3. ACTION5 is admitted beside ACTION1–ACTION4 even though metadata supplies only “extra
   interaction channel”; it is not a route edge until movement is observed.
4. Production G3 consumes `outcome.refused_contact`, but no production path currently creates it.
5. G3's 24-step pursuit counter increments only for actions declared `CONTACT_ATTEMPT`, not every
   approach action.
6. A positive BODY witness must be confirmed by re-contact, but no deterministic move-away and
   re-contact service exists.

## 4. Port ledger

### Port as pure algorithms

From `/Users/stephenkaskin/Desktop/virelai-golden/golden/captain/nav_lattice.py`:

- footprint arithmetic;
- stood-anchor traversal;
- refused-edge exclusion;
- deterministic BFS routes;
- contact surfaces whose predicted landing intersects the target footprint;
- one-step frontier experiments;
- approach geometry.

From `/Users/stephenkaskin/Desktop/virelai-golden/golden/captain/nav_sweep.py`:

- contact before walk when a contact press is already available;
- nearest deterministic frontier expansion;
- enumeration accounting;
- evidence-bearing presumed-unreachable certificates;
- reopen conditions after new ground, yielded refusal, or world-state change.

From Virelai v4 donors named in the checked prior-art packet:

- predicted-landing contact and plural footprint check-off;
- arrival as cell transfer, never adjacency;
- intentional versus incidental contact lines;
- typed budget stop distinct from stuck or inert;
- target election from observed cell exchange with abstention when ownership is unresolved.

### Do not port

- Golden's whole worldline/role inference stack;
- class-wide passability judgments;
- permanent unreachable filters;
- footprint-in-trail traversal;
- complete routes through unobserved ground;
- adjacency as contact;
- a fixed navigation budget as an epistemic verdict;
- v4's large driver architecture or game-specific content;
- any downloaded game-engine implementation.

Ring 9 already owns entity identity, counter masking, evidence, gate products, memory, and runtime
delivery. The port must adapt pure navigation algorithms to those contracts.

## 5. New branch-neutral contracts

### 5.1 `NavControlMap`

Machine-readable G1 product derived from lossless paired probes:

```text
ego entity set and relative footprint
movement action -> observed displacement
supporting transition refs
refused observations keyed by anchor and action
unresolved actions
conditions and limitations
```

Only stable, scoped ego translation becomes a route bearing. ACTION5 remains an interaction action
unless the record separately demonstrates stable ego translation.

### 5.2 `ContactProcedure`

The NAV counterpart of a CLICK action:

```text
procedure id
target entity id
controlling ego entity id(s)
target footprint/version when declared
contact definition: predicted ego landing intersects target footprint
allowed bearing actions
optional interaction action
level and life
```

It names the causal subject even when several targets use the same final action.

### 5.3 `ContactEpoch`

One completed activation attempt:

```text
procedure id and target entity id
route transition refs
contact transition ref
pre-contact and post-contact masked addresses
final action and stand
outcome: ENTERED | DISPLACED | TRANSFORMED | REFUSED | BOUNDARY | UNRESOLVED
local, remote, ego, ground, and counter partitions
```

Only epochs with an attributed terminal contact may support a lever witness, orbit step, relation
grade, or law test.

### 5.4 Branch-neutral `InterventionRef`

```text
CLICK -> kind, target entity, exact coordinate action
NAV   -> kind, target entity, ContactProcedure id
```

G4 stores and compares this reference. Runtime execution resolves it to one or more actions.

## 6. Ownership

The controller owns procedures it can compute. Duck owns interpretations and predictions.

| Work | Owner |
|---|---|
| compile bearings from verified G1 transitions | controller |
| choose the next route or frontier action | controller |
| label the scheduled action as approach or contact | controller |
| update route, entity, counter, life, and evidence records | controller |
| explain a confirmed BODY lever | Duck |
| explain a completed NAV orbit | Duck |
| freeze G4-B and G4-C predictions | Duck |
| execute the predicted contact procedure | controller |
| grade the terminal contact transition | controller |
| resolve genuine ambiguity or a missing route law | Duck wake |

The counter is an ignored baseline after G2. Its remaining capacity may inform scheduling, but it
cannot reopen G2, block G4 understanding, or become a semantic prerequisite.

## 7. Slice ladder

Mainline revision numbers are intentionally unallocated because the G9 line may continue after its
live checkpoint. NAV slices use `NAV-N*` labels until integration assigns conflict-free R9 labels.

### NAV-N0 — structured control and intervention contracts

Build `NavControlMap`, `ContactProcedure`, `ContactEpoch`, and `InterventionRef` as new modules.
Compile bearings only from lossless G1 evidence. Add a compatibility constructor for CLICK so the
existing branch can be tested against the new abstraction without changing behavior.

**Exit:**

- the ls20 G1 fixture yields the four demonstrated bearings;
- a refusal does not erase a supported bearing;
- reset displacement never becomes a bearing;
- ACTION5 stays unresolved unless movement is demonstrated;
- two NAV targets reached by the same action have different intervention identities;
- CLICK intervention identity and serialization remain unchanged.

### NAV-N1 — deterministic route service

Port Golden's lattice and planner into a new Ring 9 service over `NavControlMap`, current ego cells,
current target cells, stood anchors, refused edges, and grid bounds.

**Exit:**

- routes use only stood anchors;
- one frontier press may enter unknown ground, but no route crosses it in advance;
- refused edges are absent from BFS and journaled as contact/terrain evidence;
- contact means predicted footprint occupation, never adjacency;
- target cells are resolved from the current entity version before every plan;
- the plan is deterministic;
- an exhausted map emits an evidence-bearing, reopenable certificate.

### NAV-N2 — runtime contact procedure executor

Wire the route service into the capability-token path. The controller issues one action per turn,
records route cost, and creates the production refused-contact fact when a predicted contact press
produces no admitted movement or target response.

**Exit:**

- no Duck turn is needed for a computable route step;
- every action retains the binding target and procedure id;
- all pursuit actions count toward engineering budgets;
- `APPROACH` cannot be mistaken for a target test;
- boundary and reset transitions end the active procedure without grading it;
- no fixture-only field is required in production.

### NAV-N3 — G3 NAV closure and re-contact confirmation

Replace Duck-piloted G3 pursuit with the procedure executor. A positive BODY witness schedules a
fresh contact epoch for prospective confirmation. The target remains binding across route steps and
identity-preserving movement.

**Exit:**

- every eligible target is contacted or receives an honest typed certificate;
- a positive BODY residue is confirmed on a later contact epoch;
- a refused counter-only contact is scoped null, never inert;
- route failure cannot certify null or lever absence;
- an accepted dossier preserves the `InterventionRef`, not merely the final movement action;
- G3 emits a NAV `LeverInventory` or remains honestly unresolved;
- the controller cannot open G4 from an unconfirmed BODY witness.

### NAV-N4 — shared G4.0/G4.1 anatomy

Generalize shared wording and intervention serialization. Compile anatomy from the existing BODY
attribution and the accepted NAV intervention reference.

**Exit:**

- local and remote channels match the terminal contact transition;
- approach deltas are absent from the anatomy;
- Duck explains what contact changed without CLICK wording;
- the existing CLICK anatomy suite is unchanged.

### NAV-N5 — G4-A repeated contact orbits

The controller repeatedly executes the confirmed contact procedure. Each completed contact epoch
adds at most one orbit step. Routing transitions remain in the record but outside the orbit.

Reactivation rules:

- **REFUSED:** the ego may repeat from the same stand;
- **ENTERED:** leave the target footprint over demonstrated ground, then return;
- **DISPLACED:** resolve the moved target entity and route to its new footprint;
- **TRANSFORMED:** follow the retained identity when unique; otherwise hold ambiguity;
- **ABSENT:** record the observed one-shot endpoint and its reappearance condition;
- **DEATH:** restart the procedure next life on the same level, using persistent knowledge;
- **LEVEL CHANGE:** close the level-local study and hand to G9.

**Exit:**

- route motion never creates an orbit state;
- consecutive contact epochs produce exact counter-masked state addresses;
- null and recurrence use the existing evidence-defined stopping law;
- endpoint confirmation is itself a later contact epoch;
- every explanation cites contact evidence, route evidence, and limitations separately.

### NAV-N6 — G4-B contact relations

Generalize frozen predictions from raw action to `InterventionRef`. Duck names the lever/contact
procedure and predicted effects. The controller routes and contacts; grading consumes only the
terminal contact transition.

**Exit:**

- each lever is the subject of at least one graded prediction;
- identical final movement actions cannot collapse different lever identities;
- terminal death/level transitions are `INDETERMINATE` under R9-R16;
- supported relations cite supported contact predictions only;
- CLICK G4-B retains its current behavior.

### NAV-N7 — G4-C NAV law test

Define novelty over:

```text
InterventionRef + pre-contact counter-masked board + relevant contact context
```

Duck freezes one new prediction drawn from its accepted relation set. The controller executes the
procedure, and the existing grader supports or contradicts it.

**Exit:**

- a supported new NAV contact prediction emits a level-scoped `LeverReactionLawSet`;
- contradiction reopens G4-B;
- route actions cannot satisfy novelty;
- the law states its tested contact conditions and does not claim universality.

### NAV-N8 — live checkpoint and branch exit

Start with one bounded pure-NAV world. Use local/OpenRouter infrastructure for fast diagnostics;
reserve Kaggle for the assembled milestone. HYBRID remains outside this checkpoint.

**Checkpoint pass:**

1. G0 assigns NAVIGATION from metadata.
2. G1 supplies a demonstrated machine-readable control map.
3. G2 masks the complete counter and stops demanding attention.
4. The controller contacts every eligible visual target or records an honest certificate.
5. At least one BODY lever receives a prospectively confirmed witness.
6. G4 anatomy describes its terminal contact effect.
7. G4-A studies repeated contact epochs to an observed endpoint or recurrence.
8. G4-B grades a target-specific relation prediction.
9. G4-C supports a new prediction or honestly reopens G4-B.
10. The trace never guesses the win.

Score is reported separately. A win observed during a lever study is retained as a boundary and
handed to G9; it neither substitutes for G4 understanding nor counts against the scoped gate.

## 8. Planted-defect ledger

Every slice must keep these failures executable:

1. **Footprint-in-trail starvation:** traversal must use stood anchors.
2. **Route through unknown ground:** only one frontier experiment is legal.
3. **Adjacency-as-contact:** a flush approach without predicted footprint intersection is not a
   contact attempt.
4. **Raw-action lever collision:** two targets using ACTION1 remain distinct.
5. **Route delta in orbit:** an approach move cannot advance a lever state sequence.
6. **Fixture-only refusal:** production derives refused contact from the scheduled geometry and
   result.
7. **ACTION5 assumption:** metadata alone cannot make ACTION5 a bearing.
8. **Reset-as-motion:** death displacement cannot revise the control map.
9. **Stale target geometry:** a moved target is resolved by current identity before routing.
10. **Budget-as-verdict:** exhaustion is a typed stop, never inertness or unreachability without
    coverage evidence.
11. **Counter hold:** a locked counter cannot monopolize a NAV lever study.
12. **Terminal grade:** a death or level transition cannot support or contradict a contact
    prediction.

## 9. Persistence tiers

The NAV implementation must extend `life_record.PERSISTENCE` as it lands:

| State | Tier | Reason |
|---|---|---|
| demonstrated control map | LEVEL | re-established when each level restarts G0–G1 |
| stood anchors and refused edges | LEVEL | knowledge survives deaths on the same level |
| target contact procedures | LEVEL | bound to level-local entities |
| route in progress | TRANSIENT | interrupted by reset or boundary |
| completed contact epochs | LEVEL | evidence survives deaths |
| current contact prediction | TRANSIENT | resolved or made indeterminate by its transition |
| prior level NAV products | GAME through frozen `LevelModel` | carried only as G9 hypotheses |

Refused edges are standing observations, not eternal walls. A later successful press reopens the
terrain reading and the route graph.

## 10. Collaboration and merge discipline

- R9-R18/G9-A is committed at `fbbc7f4`. NAV-N0 still begins in new modules and new tests so its
  contracts can be reviewed independently before they are wired into the central gate machine.
- Existing uncommitted work is preserved. No cleanup, reset, or opportunistic formatting is part of
  the NAV branch.
- Each implementation slice receives:
  - a signed `BUILD_SLICE_*` document;
  - a conflict-free revision label;
  - a base commit;
  - changed-file ledger;
  - fail-first or planted-defect evidence;
  - focused and full-suite results;
  - explicit live-evidence boundary;
  - ratchet counts where the project protocol requires them.
- Every Sol-authored document and code-level handoff is signed **Sol**.
- A later collaborator must be able to reconstruct why a field exists, which gate owns it, and what
  observation can falsify it.

## 11. First implementation slice, prepared

**Slice:** `NAV-N0`  
**Goal:** establish branch-neutral intervention identity and a machine-readable navigation control
map without changing runtime routing.  
**Preferred new files:**

```text
inference/framework/nav_control.py
inference/framework/intervention.py
tests/test_nav_control.py
tests/test_intervention.py
BUILD_SLICE_NAV_N0_CONTROL_AND_INTERVENTION_2026-10-01.md
```

**Files deliberately deferred until NAV-N0's contracts pass independently:**

```text
inference/framework/virelai_gates.py
inference/framework/controller_executor.py
inference/framework/life_record.py
inference/framework/card_builder.py
inference/framework/memory_store.py
```

**NAV-N0 is complete only when:**

- it derives bearings from production-shaped lossless outcomes rather than answer prose;
- it refuses ambiguous or terminal movement evidence;
- it represents CLICK and NAV interventions without changing CLICK serialization;
- it proves target identity is independent of raw movement-action equality;
- its tests fail on the planted raw-action-collision defect;
- it introduces no route execution and makes no live claim.

## 12. Proposed rulings requiring Director acceptance through continued build authorization

1. The controller pilots deterministic NAV routes; Duck interprets contacts and freezes G4
   predictions.
2. G3 NAV confirmation is a prerequisite slice of G4 NAV because G4 may consume only a confirmed
   lever inventory.
3. ACTION5 is an interaction channel until movement is demonstrated.
4. Only terminal contact transitions enter lever orbits and prediction grades.
5. Counter capacity may schedule a route but cannot block the gate after masking.
6. Build pure NAV first; HYBRID receives a separate branch after NAV closes.

These rulings preserve the user's existing strategy and are the narrowest changes that make the
CLICK G4 architecture honest on an embodied world.

— Sol, Alpha build seat, 2026-10-01

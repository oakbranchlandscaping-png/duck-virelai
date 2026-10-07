# Build report: Ring 9 NAV branch, from ego discovery through lever law

**Type:** `ALPHA_BUILD_REPORT`

**Version:** v1

**Date:** 2026-10-07

**Author:** Sol (Alpha build seat, NAV line), signed

**Repository:** `duck-virelai`

**Branch:** `ring9-unified`

**Runtime implementation reviewed through:** `4970953` (`Recover NAV targeting from complete cell-site flow`)

**Canary packager profile:** `4cd7a28` (`ls20-cellsite`, 48 actions, 1,200 behavior seconds)

**Upload receipt:** `1f6ab61`

## 1. Executive result

The NAV branch implements the cybernetic gate ladder for an embodied ego:

```text
read opaque action metadata
-> find and explain the embodied ego
-> derive its complete cell-site body and action bearings
-> find and mask the counter
-> inherit the ranked visual-object roster
-> resolve each stable object identity to its current cell sites
-> navigate over demonstrated floor and experimental frontier edges
-> attempt target-bound body contact
-> remove counter and expected ego/ground exchange from the delta
-> record lever, scoped null, provisional route limit, or bounded ambiguity
-> advance the roster
-> type confirmed levers through anatomy, orbit, relations, and law gates
```

The branch is substantially implemented and has a broad local regression floor. It is not fully validated live.

The most important recent repair closed the production gap between G1 and G3. The first unified ls20 canary showed that Duck could correctly describe four movement laws while leaving `action_law_specs` empty and naming only two representative ego sites. The old controller therefore had no bearing map, issued zero G3 actions, and stopped. The repaired controller derives the movement product from lossless cell-site flow. On the same recorded Kaggle evidence it recovers all four bearings, reconstructs the complete 25-site ego, resolves G3's first stable entity to its current full cell set, and emits a controller-owned approach action.

This repair is locally proven. Its bounded live canary is uploaded and currently queued. No claim in this report treats that queued run as completed evidence.

## 2. North Star and branch responsibility

The project's goal is not to guess a win state. It is to make the agent investigate the physics of an ARC world in a forced order:

1. know the available control surface;
2. know what the agent directly controls;
3. identify and remove the time/resource counter from causal deltas;
4. contact every remaining visual object;
5. find the objects that cause local or remote change;
6. type those levers in depth;
7. accumulate a stable world model across actions, deaths, and levels;
8. observe a win and describe its goal in the language of the learned model.

NAV is the embodied branch of this strategy. CLICK can act directly on a ranked object site. NAV must first move a body through a partially understood field of play. This creates additional obligations:

- derive the meaning of opaque actions without relying on action numbers;
- represent the complete ego footprint;
- distinguish floor, wall, target, and uncertain terrain;
- construct a route from observed evidence;
- distinguish approach from terminal contact;
- bind a multi-action intervention to one target identity;
- stop pursuing a target when the current route question is exhausted;
- reopen that question after a relevant world change;
- prevent ego translation and ground exchange from masquerading as lever effects.

The NAV branch should use Duck for semantic explanation and unresolved judgment. Deterministic code owns bookkeeping, exact geometry, verified control laws, route selection, evidence attribution, and roster progression whenever the evidence uniquely determines those operations.

## 3. Evidence labels used in this report

This report separates four classes of evidence:

| Label | Meaning |
|---|---|
| **LIVE DIRECT** | Read from completed Kaggle artifacts: receipts, probe outcomes, envelopes, gate events, answers, ledgers, or logs. |
| **LOCAL DIRECT** | Reproduced from committed code and fixtures in the local test environment. |
| **BUILDER REPORT** | Stated in an earlier signed report but not independently rerun for this report. |
| **PLANNED/QUEUED** | Implemented but awaiting the named live proof, or specified but not implemented. |

Source variants, packaged source copies, and executed artifacts remain distinct. A packaged marker proves what was shipped. Only a completed execution artifact proves what ran and what behavior occurred.

No downloaded game-engine implementation was inspected to derive game mechanics.

## 4. Architecture of the NAV branch

### 4.1 Shared gate machine

NAV is not a separate solver. It is an actuator branch inside the unified Ring 9 gate machine. G0, G2, the entity ledger, lever lifecycle, causal attribution, G4 memory products, life record, level freeze, carry, and normal-play handoff are shared with CLICK. The branch point changes how an intervention reaches a target:

- CLICK binds a coordinate action to the target;
- NAV binds a sequence of approach actions and one terminal body-contact attempt to the target;
- HYBRID begins with CLICK and can later use the NAV arm.

The controller recomputes action ownership after every frame. One controller turn performs at most one environment action and then returns to observation. This prevents a cached plan from running blind through changed state.

### 4.2 Core NAV modules

| Module | Responsibility |
|---|---|
| `nav_control.py` | Compile verified opaque action bearings and the complete ego footprint from G1 evidence. |
| `nav_route.py` | Route through demonstrated stands, define target contact by footprint intersection, and certify exhausted route questions. |
| `nav_terrain.py` | Infer provisional floor/wall palettes, analyze reachability, and choose falsification experiments. |
| `nav_intervention.py` | Bind procedure and contact-epoch identity to one target entity. |
| `entity_observation.py` | Maintain stable entity hypotheses from complete cell-site sightings and expose target/ego observation scopes. |
| `virelai_gates.py` | Schedule the roster, ingest transitions, attribute residue, manage reachability, and connect G3 to G4. |
| `controller_executor.py` | Select controller-owned route, contact, certified-answer, and G4 actions. |
| `controller_turn.py` | Execute one action, reread the frame, and recompute ownership. |
| `life_record.py` / `level_model.py` | Preserve GAME-tier evidence, cross-life records, and frozen level models. |

### 4.3 Stable identity and mutable geometry

The central representation is now:

```text
stable entity identity
-> current complete cell-site set
-> possible contact landings
-> attempted route edges
-> target-bound contact epoch
-> attributed masked delta
-> terminal or reopenable disposition
```

The initial G2 anchor is retained as historical evidence and a ranking aid. It is not the enduring meaning of the object. Before each attempt, G3 resolves the roster identity through `EntityLedger` and emits the entity's current sites, current anchor, current bounding box, current integer, cell count, entity version, and geometry source.

## 5. Gate-by-gate build status

### G0 — action metadata and world type

**Implemented and live-proven on ls20.**

G0 reads the available opaque actions and whether they require coordinates. Actions 1–4 without coordinates create the navigation prior; click-only action 6 creates pointer god mode; mixed surfaces create a hybrid prior. This is a prior about control form, not a semantic assignment to individual action numbers.

The unified ls20 canary entered NAVIGATION from its non-coordinate action surface. G0 itself required no Duck inference about directions.

### G1 — embodied ego and control law

**Implemented; original live boundary failed; repaired locally; new live proof queued.**

The Delphi opening probes every simple action twice. G1 asks Duck to explain what moved, how it moved, competing models, and a prospective demonstration. A supported demonstration establishes an embodied ego law.

The original NAV control compiler expected structured displacement fields. This was too strict for production because Duck could answer correctly in prose while normalization retained no structured laws. Synthetic tests had supplied richer answer objects and therefore missed the problem.

The repair in `4970953` treats the lossless grid evidence as authoritative:

1. reconstruct before and after frames from the recorded site transitions;
2. extract four-connected same-integer components;
3. identify exact translated components whose sites intersect observed changes;
4. use the supported prospective demonstration to select the relevant moving family;
5. retain every site in the selected components, even when Duck named only representatives;
6. accept an ordinary bearing only when the paired opening probes agree;
7. retain a properly structured, prospectively supported action law as a second valid evidence channel;
8. cache the compiled control product by G1 revision and comparison identity.

The compiler never parses words such as “up,” “left,” or “right.” It does not infer semantics from action numbers.

On the completed unified ls20 record, the repaired compiler recovers:

| Action | Observed displacement |
|---|---:|
| `ACTION1` | `(-5, 0)` |
| `ACTION2` | `(5, 0)` |
| `ACTION3` | `(0, -5)` |
| `ACTION4` | `(0, 5)` |

It also recovers the complete 25-site composite ego across integers 9 and 12. Duck's stored prediction had named only two representative sites.

### G2 — counter discovery and masking

**Implemented and live-proven on unified ls20.**

G2's purpose is to remove predictable noise from downstream deltas. It is not required to understand the full world or fully explain the counter's end-state law before G3 may begin.

The completed unified ls20 canary directly observed and locked an 84-cell, two-row counter footprint. Two sites changed from integer 11 to integer 3 per transition. G2 demonstrated its counter prediction and produced the mask baseline at transition 12.

The counter remains visible for life/boundary bookkeeping, but its full footprint is excluded from lever discovery and causal residue.

### G3 — ranked lever sweep

**Substantially implemented; one historical contact is live; current unified routing is locally proven; full unified sweep remains unproven.**

G3 inherits G2's frozen, ranked visual-object roster and removes members fully owned by the counter. Every remaining row must be accounted for. The NAV arm then:

1. binds the G2 member to a stable entity hypothesis;
2. reads the entity's current complete sites;
3. computes the current ego footprint and verified bearings;
4. routes over demonstrated stands;
5. permits one explicit frontier experiment beyond known stands;
6. labels an action `CONTACT_ATTEMPT` only when the predicted landing footprint intersects a target site;
7. observes the new frame before planning again;
8. creates a target-bound `ContactProcedure` and `ContactEpoch` for terminal attempts;
9. removes counter, expected ego motion, and ground exchange from the changed sites;
10. records the target's local and remote residue and advances or bounds the row.

The target result can be:

- `LEVER_FOUND` from the first attributed positive contact;
- scoped null after a valid contact;
- `PRESUMED_UNREACHABLE` after an exhausted evidence-backed route question;
- a boundary or budget disposition;
- bounded ambiguity when attribution cannot be resolved.

First witness is the discovery law on both CLICK and NAV. G3 does not spend a confirmation repeat. G4-A supplies repeated activation during detailed typing.

#### Historical live evidence

N5.1 contains a real positive ls20 contact at transition 18. Replaying that transition under the unified first-witness law produces `LEVER_FOUND`, BODY channel attribution, a nonempty remote residue, a target-bound intervention record, `G4-READY` lifecycle state, and roster advance.

That direct observation proves that a real NAV contact can expose a lever. It does not prove that the current unified Qwen3.6 run can route to it, complete the roster, or open G4.

#### First unified canary

The first unified ls20 canary constructed an eligible roster of 16 members and bound rank one to E0001/M0009. It then took zero G3 actions because the G1 bearing product was empty. Its controlled fallback model request exhausted a 256-token output cap without a tool call and stopped. That is direct evidence of the former representation failure, not evidence that E0001 was unreachable or inert.

#### Cell-site repair

G3 now refreshes current geometry before both CLICK and NAV attempts. CLICK uses the current anchor. NAV uses the current complete target cell set. The emitted target row identifies `CURRENT_ENTITY_SIGHTING` when the ledger supplies that geometry.

The production-shaped replay of the failed unified canary now reaches G3 and immediately emits a controller-owned `ACTION1` approach toward the first roster member.

### G3 terrain and reachability

**Implemented and locally tested; historical live release evidence exists; full current live behavior remains incomplete.**

NAV learns terrain as provisional integer roles derived from actual ego/ground exchange and refused landings. It does not assume that every non-ego object is a wall or that every apparently open region is reachable.

The route model distinguishes:

- demonstrated stands: anchors the ego has actually occupied;
- refused edges: `(stand, action)` pairs that failed;
- contact surfaces: actions whose predicted landing footprint intersects the target;
- frontier edges: one-step experiments beyond demonstrated stands;
- provisional floor/wall roles supported by observations.

`PRESUMED_UNREACHABLE` means that no currently demonstrated contact route or remaining target-conditioned frontier experiment exists. It never means inert. The certificate records reachable stands, refused edges, closest stand, remaining gap, target geometry, control law, action surface, topology epoch, evidence references, and explicit reopen conditions.

A released target reopens only when the route question materially changes, including:

- a relevant new demonstrated stand;
- a refused edge later yielding;
- changed target sites or identity;
- changed ego footprint or bearing map;
- changed action surface;
- changed terrain or topology epoch.

A routine `STILL` version increment or an unrelated target's counter-only transition does not reopen the certificate.

### G4.1 — reaction anatomy

**Implemented and locally tested; no current unified live NAV proof.**

G4.1 describes the anatomy of each confirmed lever response using the target-bound intervention and attributed local/remote residue. It separates what changed at the lever from what changed elsewhere and preserves limitations when identity or attribution remains ambiguous.

NAV and CLICK share the reaction representation. NAV's difference is that the intervention is a contact procedure rather than a raw movement action.

### G4-A — repeated lever orbit

**Implemented and locally tested; historical NAV work only.**

G4-A repeatedly activates a known lever until the response becomes null, cycles through an already observed result, reaches a boundary, or exhausts its bounded study. This is where the earlier Virelai “spam a known lever until null or recurrence” prior is placed.

NAV approach transitions update the world record but do not advance an orbit. Only the terminal contact transition advances the target's run. Route evidence remains separate from contact evidence.

### G4-B — relations between levers and remote regions

**Partially unified.**

The project has record-derived G4-B for CLICK. NAV has the required row-level intervention and attributed-residue seam: target entity, procedure id, final action, contact outcome, local residue, and remote residue. The remaining integration must ensure that the record's definition of a press recognizes terminal NAV contact epochs and reads ego-masked attribution instead of recomputing raw board change.

Until that integration is fully validated, NAV G4-B can fall back to Duck rather than inventing a relation.

### G4-C — tested lever law

**Implemented locally; live NAV validation pending.**

Duck states a general lever law and freezes a new target-bound prediction. The controller routes to the named intervention, leaves the prediction pending during approach, and grades only the terminal contact frame after counter and ego masking.

No unified live NAV trace has yet reached this gate.

### PLAY-NORMAL and later observed-win work

The gate machine can hand control to `PLAY-NORMAL` after the built ladder has a valid rest state. That handoff is an execution state, not evidence that the physics model is complete or that the win goal has been inferred.

The separate observed-win program remains downstream: relation extraction, code-only win-transition referee, win ledger, explanation in the learned physics grammar, cross-level carry, and eventually acting on an observed goal. The NAV actuator should be reused there rather than replaced with a second navigator.

## 6. What was ported from prior art

### Virelai 3.5

Virelai 3.5 had the strongest compact deterministic targeting loop found in the repository:

- refresh target coordinates from the current frame;
- rank untried targets before repeated ones;
- route one step;
- reread the body and board;
- remember blocked edges;
- rotate when a target is terminal.

Ring 9 ports those execution invariants. It does not port 3.5's coordinate-only object identity, small heuristic candidate cap, or permanent unreachable set.

### Golden/Captain robotics work

The NAV lattice and wall-crawl principles reuse the Captain/Golden distinction between demonstrated floor, refused landings, frontier experiments, and current reachability. The agent treats “outside the current field of play” as a hypothesis to test, not an immediate fact.

### Earlier Ring 9 work

The current branch preserves:

- complete counter masking;
- entity continuity with explicit abstention on ambiguity;
- first-witness G3 discovery;
- target-bound interventions;
- life reset back-edges;
- level freeze and carry;
- mu return for unresolved/newborn objects;
- compact automatic cards with expandable evidence queries;
- controller-first ownership.

## 7. Historical frictions and the repairs intended to overcome them

| Friction | Consequence | Current response |
|---|---|---|
| Duck's correct memory or reasoning was invisible to deterministic code | The model “knew” the law but the controller could not act on it | Compile machine-readable bearings and ego sites from lossless observations; preserve structured laws when present |
| Generated or rich fields bypassed by the active prompt/normalization branch | Synthetic fixtures passed while production answers were poorer | Production-shaped replay fixture from the completed unified Kaggle run |
| Intent/action encoding mismatch | Planner, prompt, and executor disagreed about what an action meant | Opaque action tokens remain canonical; intent is a separate `pilot_intent` and target-bound procedure |
| Partial prediction scope mistaken for the whole ego | Terrain and contact logic saw two cells instead of a 25-site body | Full component-family recovery from cell-site translation |
| Visual object collapsed into one coordinate | Contact surface, movement, and transformation were lost | Stable identity plus complete current site set; anchor retained only as metadata |
| Frozen G2 geometry reused after world change | Solver aimed at stale sites | Resolve the latest entity sighting before every attempt |
| Roster construction separated from action execution | A correct list existed but no reliable loop drained it | Controller-owned one-step route/observe/replan cycle |
| Duck used for deterministic steering | Tokens and time were spent on choices already fixed by evidence | Controller owns bearings, contact surfaces, route actions, and roster bookkeeping |
| Approach confused with contact | A transit frame could be graded as a lever activation | Only predicted footprint intersection is `CONTACT_ATTEMPT`; route and contact evidence are separate |
| Counter delta mistaken for world response | Noise created false levers or new targets | Full counter footprint masked before attribution |
| Ego translation mistaken for remote response | Every NAV press appeared to change something elsewhere | Observation scope removes expected ego and ground exchange before residue |
| Scoped prediction failure treated as proof of no remote effect | A narrow failed prediction overruled broader observations | Store the precise scope and preserve unknown alternatives |
| Arbitrary retry or rate thresholds | Targets were released without completing a logical experiment | Release follows exhaustion of current contact/frontier evidence, not a fixed success percentage |
| Permanent unreachable exclusion | A later topology change could never revive a target | Evidence-backed provisional certificates with signature-based reopening |
| One hard target monopolized the sweep | G3 could never reach later objects | Bounded disposition releases the row while preserving reopen conditions |
| Low-level record accumulation mistaken for a world model | More rows did not create useful causal compression | Gate products summarize ego, mask, lever, reaction, orbit, relation, and law claims |
| Long Kaggle runs used to test early handoffs | Hours were spent before learning that G3 took zero actions | Production replay plus a 48-action, 1,200-second handoff canary |
| Different models and environments compared as if equivalent | Behavioral changes were attributed to code without control | Current canary pins Qwen3.6, private mounts, Python 3.12 image, one world/pass/concurrency |

## 8. Evidence ledger

### Live direct evidence that currently supports the NAV branch

1. **N5.1 historical run:** a real transition-18 body contact produced non-counter remote residue. The unified replay converts it to first-witness `LEVER_FOUND` and roster advance.
2. **Unified ls20 v1:** package verified; G0 and G1 probes ran; G1 closed after a supported demonstration; G2 locked the 84-site counter; G3 built a 16-member eligible roster; zero G3 actions occurred because the old control product was empty; controlled stop worked.
3. **Cell-site canary upload:** the private dataset is ready, kernel version 1 was accepted, and initial status was `QUEUED`. This proves submission state only.

### Local direct evidence

1. The completed unified ls20 artifact was converted to `ls20_kaggle_unified_v1_record.json.gz`.
2. Replaying its 12 transitions under `4970953` yields all four bearings and a complete 25-site ego.
3. The active G3 target's emitted sites equal its current ledger sighting and identify `CURRENT_ENTITY_SIGHTING`.
4. The next owned step is a controller action with `APPROACH` or `CONTACT_ATTEMPT`, not a Duck turn.
5. Targeting-focused floor: 63 passed.
6. Full repository floor: 619 passed, 1 skipped.
7. Frozen cell-site canary package: 9/9 static checks, zero differences from its commit export, clean secret scan.

### What the evidence does not yet support

- that the queued cell-site canary will reproduce the local control product live;
- that the current unified branch can reach and settle the first ls20 target;
- that it can drain the complete 16-member roster;
- that current live reachability releases and reopenings behave correctly;
- that unified NAV opens G4 live;
- that NAV G4.1, G4-A, G4-B, or G4-C works live;
- that the solver clears an ls20 level;
- that any NAV behavior generalizes to other worlds;
- that a win goal has been discovered or can be acted upon.

## 9. Validation state

### Latest local floor

The full suite after the cell-site implementation completed with:

```text
619 passed, 1 skipped
```

The one compatibility failure in the first full run was an evidence-source label. When Duck already supplied a complete demonstrated footprint, an existing contract expected `DEMONSTRATED_AFTER_FOOTPRINT`. The final code preserves that label when the deterministic and demonstrated sets are identical and uses `DETERMINISTIC_CELL_SITE_TRANSLATION` only when deterministic evidence expands a partial scope. The complete suite then passed.

### Current live canary

| Field | Value |
|---|---|
| Notebook | `stephenkaskin/taaf-virelai-ring9-unified-ls20-cellsite-v1` |
| Frozen source | `4cd7a28c5c2108dacacb88826a923aaeee67514a` |
| Runtime repair | `4970953` |
| World | `ls20-9607627b` |
| Model | `vrfai/Qwen3.6-27B-FP8` |
| Budget | 48 actions, 1,200 behavior seconds |
| Initial status | `QUEUED` |

Its preregistered exit is deliberately below full G3 completion:

- complete deterministic bearings and ego sites;
- nonempty accounting-complete roster;
- current-site entity binding;
- controller-owned route actions;
- geometry refresh after frames;
- at least one terminal G3 target result and appropriate roster advance.

## 10. Known risks and open engineering work

### Immediate validation work

1. Download and grade the cell-site canary when it completes.
2. If CS-1 through CS-5 pass, run the longer unified ls20 canary for roster closure and G4 opening.
3. Convert the completed live record into the next immutable replay fixture.

### Remaining local proof

Build one integrated roster-drain fixture with:

- a reachable scoped-null target;
- a reachable positive target;
- a provisionally unreachable target;
- a relevant world change that reopens it;
- final accounting for every original member;
- a genuinely new object that opens a new G3 obligation rather than duplicating an existing identity.

The test must assert the action sequence and lifecycle transitions, not only schemas.

### G4 integration

Complete and validate NAV-aware record presses and relations:

- recognize only terminal, target-bound contact epochs as presses;
- exclude approach rows;
- use stored attributed residue rather than raw board change;
- preserve replay answer identity for older records without the newer fields;
- keep Duck fallback for records that cannot certify the relation.

### Identity ambiguity

Exact translation matching deliberately abstains when duplicate equal-shape components make correspondence ambiguous. Entity continuity also abstains on ambiguous birth or unsupported deformation. Those are explicit representation gaps. The system must not silently choose an identity to preserve progress.

### HYBRID

HYBRID scheduling exists, including CLICK-to-NAV handoff and mu return, but lacks a complete live trace. It remains less proven than either pure channel.

### Cross-life and cross-level accumulation

Life records, reset back-edges, level freeze, and carry infrastructure exist. The full claim that mechanism knowledge survives death and appropriately transfers to the next level still requires live NAV evidence. Carry should preserve causal laws and uncertainty, not blindly preserve stale geometry.

## 11. Recommended build order after the canary

1. **Grade the bounded cell-site canary.** Repair only observed failures in the G1-to-first-target loop.
2. **Prove the integrated roster drain locally.** Include null, positive, provisional release, reopen, and birth.
3. **Run the longer ls20 G3 canary.** Exit on complete roster accounting and G4 opening.
4. **Finish NAV record-derived G4-B.** Use target-bound contact epochs and attributed residue.
5. **Run a bounded NAV G4 canary.** Prove one lever's anatomy and repeated orbit before asking for all of G4.
6. **Add ft09 as the second NAV/HYBRID canary only after ls20's branch is coherent.** Do not compare scores across unlike worlds or model stacks.
7. **Validate death and level carry.** Demonstrate that laws persist while current geometry is rebuilt.
8. **Connect observed-win products.** Reuse the NAV intervention boundary for later goal-directed action only after the win has been observed and recorded.

## 12. Exit definition for the NAV branch

The NAV branch should be called operational only when a pinned live run demonstrates all of the following without hidden manual steering:

1. G0 assigns an embodied or hybrid world type from metadata.
2. G1 identifies and explains the ego, recovers its complete sites, and certifies every used bearing.
3. G2 masks the full counter without delaying G3 for unnecessary counter semantics.
4. G3 constructs an accounting-complete roster of stable identities.
5. The controller visits or logically releases every eligible target using current cell sites.
6. Every terminal contact is attributed after counter and ego masking.
7. Positive contacts become levers on first witness and the roster continues.
8. Provisional unreachable rows reopen only after relevant change.
9. G3 closes with a valid inventory or bounded coverage product and opens G4.
10. At least one NAV lever completes reaction anatomy, repeated orbit study, relations, and a tested law.
11. A death preserves the learned mechanism while rebuilding current geometry.
12. A level transition freezes the old model and starts the next level without contaminating its evidence.

Winning is not part of this branch exit. The win must still be observed, recorded, and described downstream in the learned physics grammar.

## 13. Bottom state as of 2026-10-07

The original NAV blocker was not a lack of target objects and not evidence of an unreachable first lever. It was a representation seam: Duck described motion, but the deterministic controller did not receive a usable body or bearing product.

That seam is repaired in code and reproduced against the exact failed Kaggle record. The object representation is now coherent from roster through routing: a stable identity owns a complete, current set of cell sites. The next unknown is live execution. The queued canary is designed to answer that one question without spending a full two-hour run or conflating it with roster completion, G4, winning, or score.

— **Sol**, Alpha build seat (NAV line), 2026-10-07

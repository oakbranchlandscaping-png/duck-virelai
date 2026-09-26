# Alpha Builder operating protocol — Cybernetic Duck

**Date:** 2026-09-26  
**Purpose:** replacement-ready engineering and research protocol  
**Authority:** current description of how to build and evaluate this project  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Companion memory:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-26.md`

This document explains how the project is built. Institutional-memory files explain what has
happened. Slice documents explain individual changes. Historical North Stars, work orders, and
plans are prior art unless the user explicitly revives them. The user's current direction always
controls.

## 1. The job

Build an LLM-centered ARC investigator that learns a world through interaction. Duck should:

1. probe the world systematically;
2. build a stable, falsifiable internal model;
3. explore counter-masked novel grid states using that model;
4. observe a win rather than guess one; and
5. describe the observed goal in the language of the learned model.

The engineering task is not to solve every game with hidden deterministic logic. It is to build
the cybernetic structure around Duck that makes disciplined investigation easier and skipped
reasoning harder.

The controller supplies focus, sequence, admissible experiments, evidence binding, durable memory,
and stopping rules. Duck supplies semantic interpretation, competing explanations, mechanism
language, and action choices within the authorized target.

## 2. Governing philosophy

### 2.1 Intelligence is an observed learning process

```text
controlled probe
-> literal observation
-> persistent entity/process hypothesis
-> prospective prediction
-> observed support or correction
-> compact mechanism law
-> novel-state exploration
-> observed terminal transition
-> explanation of the goal in learned terms
```

A high score without this trajectory does not establish the intended result. An early gate can
pass without a level clear when it answers its own bounded question.

### 2.2 The grid is a flip book of integers

Begin with literal frame arithmetic. A cell changing `7 -> 4` is an observation. Calling it a
timer tick is an interpretation that requires evidence. A moving footprint is a persistence
hypothesis before it is an ego. A remote delta is an effect before it is assigned to a lever.

Maintain both raw frames and lossless transitions for audit, plus compact semantic products for
reasoning. Never let semantic compression destroy the underlying observation.

### 2.3 The win is observed

Do not ask Duck to infer an unseen winning state. Before a win, the mission is to learn the local
physics and visit new counter-masked configurations. Preserve any terminal transition exactly.
Only then open the observed-win explanation target.

### 2.4 Small goals create focus

Each gate asks one local question, exposes only relevant admitted evidence, and prevents later
objectives from stealing attention. A gate must recognize satisfaction quickly; a controller that
keeps demanding work after success defeats cybernetic targeting.

### 2.5 Explanation is part of completion

Detection alone is insufficient. Duck must explain what it found, how it behaves, its conditions,
supporting evidence, strongest alternative, falsifier, and remaining uncertainty. Controller
numbers constrain the answer but do not substitute for Duck using them.

## 3. Repository and artifact identity

| Identity | Location | Meaning |
|---|---|---|
| Active hybrid repository | `/Users/stephenkaskin/Desktop/virelai-review/duck-virelai/` | Project, variants, packages, runs, and documents |
| Active editable source | `variants/ring9-cybernetic-gates/ARC3-Inference/` | Code under development |
| Frozen Kaggle package | `kaggle/<package>/` | Exact upload material |
| Executed evidence | `runs/<run>/` or variant-local `runs/<run>/` | Output from one execution |
| Golden solver | `/Users/stephenkaskin/Desktop/virelai-golden/` | Separate deterministic no-LLM solver and prior-art donor |
| Historical trees | Ring 6–8, V4, archived bundles | Mining material, not authority |

Rules:

- Preserve the modified and heavily untracked tree. Never reset or clean it.
- Mine before inventing; useful behavior may exist in any historical family.
- Port deliberately. Do not inherit an old architecture as the current mandate.
- Never confuse editable source, packaged copies, and executed artifacts.
- Matching filenames do not prove matching bytes. Use manifests, hashes, receipts, and notebook
  versions.
- Do not inspect downloaded game-engine implementations to derive evaluation mechanics.

## 4. Evidence discipline

Every important claim is one of:

1. **Direct observation:** present in source, tests, executed artifacts, raw frames, manifests, or
   provider responses.
2. **Builder report:** stated historically but not independently reproduced in current work.
3. **Hypothesis:** an interpretation awaiting a discriminating experiment.

Use these terms in reviews. Schema-valid output is not proof of model use. Model prose is not
executed behavior when controller artifacts disagree.

Trust evidence in this order:

```text
raw before/action/after state
-> lossless probe outcome
-> controller gate event
-> accepted gate answer
-> transcript prose
-> retrospective builder interpretation
```

## 5. Control architecture

### 5.1 Prompt layers

Duck receives:

1. a stable grid-block and flip-book ontology;
2. a stable cybernetic mission;
3. a volatile binding GoalCard naming the current target and authorized next operation.

The ontology is a vocabulary of possible mechanisms, not facts about this world. Evidence
establishes facts. The GoalCard owns focus.

### 5.2 Capability-bound action control

The controller issues a capability token bound to the active gate, revision, exact probe, action
payload, and target. Duck cannot legally act with a stale token, skip to another object, or alter a
controller-selected CLICK intervention. Embodied probes allow one action from a bounded set and an
explicit approach/contact intent.

### 5.3 Durable products

A satisfied gate emits a compact versioned product consumed by descendants. Raw events remain in
the journal. Product invalidation is reserved for a genuine contradiction or dependency change.
Routine observations must not churn stable products.

The September 26 counter correction is canonical: later counter ticks remain raw visual events,
but after G2 they cannot revise the mask product or invalidate G3/G4.

## 6. Gate doctrine

### G0 — Action surface

Read metadata before acting. Record opaque action identifiers and coordinate requirements. Assign
only a control prior:

- ACTION1–ACTION4: embodied/navigation prior;
- coordinate ACTION6 only: pointer/click god-mode prior;
- movement plus coordinate action: hybrid prior;
- ACTION5: additional opaque channel requiring observation.

Do not infer world-specific semantics from action numbers alone.

### G1 — Ego and direct influence

Determine whether Duck controls a pointer locus, embodied object, or conditional hybrid. Embodied
worlds use the Delphi opening to find the controlled footprint and explain its motion. CLICK worlds
close from the interface-grounded pointer law without searching for an imaginary avatar.

### G2 — Counter as stable ignored baseline

Identify recurrent bookkeeping noise, explain its visible quantity, prospectively confirm the
recurrence, and infer the complete reversible mask footprint.

Once supported, G2 is finished. Later counter behavior is actively ignored:

- no min/max obligation;
- no background monitoring target;
- no gate reopening;
- no product revision;
- no model attention;
- no effect on world-state identity or lever attribution.

Raw frames remain intact. Ignore means subtract the known footprint when reasoning about the
world.

### G3 — Lever inventory

Interact with every ranked eligible visual object:

- CLICK: click every object in order;
- NAV: use the ego law to collide or attempt contact with every object;
- HYBRID: execute both ordered arms.

The controller owns the list. Finding a positive never ends coverage. Admit a lever only from
attributed non-counter, non-ego residue plus prospective confirmation. G3 asks where levers are,
not their mature mechanism laws.

Scoped null evidence is state-specific and never proves universal inertness. No discovered lever
after a faithful sweep indicates a measurement or representation problem to investigate, not an
arbitrary quota failure.

### G4.1 — First effect anatomy

For each confirmed lever, describe its first observed reaction: exact intervention, affected
regions, local/remote scope, integer transitions, transformation vocabulary, alternative, and
falsifier. This is a revisable first impression.

### G4.2 — Repeated activation orbit

Repeatedly apply the exact confirmed intervention and compare complete counter-masked grids.
Continue while each masked state is new. Stop only on a masked null at the observed state or exact
recurrence of a prior masked configuration. Record the state sequence and period. No arbitrary
action count proves understanding. A boundary interrupts but does not falsely complete the orbit.
Duck explains the observed orbit before advancing to the next lever.

### Later G4 subtrees

Evidence may open reversal, saturation, toggling, transformation, spawning, deletion, transport,
conditionality, lag, coupled levers, collision, traversability, carrying, pushing, following, or
avoidance. These are questions, not assumed mechanics.

### New visual objects

A genuinely new object observed during G4 creates an entity-specific G3 classification obligation.
Appearance alone does not prove it is a lever. The child target must preserve and later return to
the parent orbit. This back-edge is planned, not proven.

### Later gates

- G5 isolates environmental forces after known effects are subtracted.
- G6 builds scoped inertness from attempted activation/contact.
- G7 explores reachable counter-masked novel states with learned physics.
- G8 explains an observed win using active laws.
- G9 tests and specializes those laws across levels.

## 7. Build rhythm

Every gate or mechanism is a mini-build with its own thesis, exit criteria, artifacts, and review.

### Step 0 — Orient and preserve

Read current memory and status, inspect existing changes, identify active source/package/run, and
separate observed facts from reports and hypotheses.

### Step 1 — State the slice thesis

Write one sentence naming the capability. Define its non-goals. Example: “G4.2 repeatedly activates
one confirmed lever until the masked world reaches a null or repeats an observed configuration.”

### Step 2 — Mine prior art first

Search active Ring 9, V4 Captain planning, Ring 7/8 code, the separate golden solver, documents, and
historical runs. Search by behavior and failure symptom as well as current terminology. For each
candidate, record what it does, its assumptions, whether production executed it, and what can be
ported.

### Step 3 — Preregister exit criteria

Before implementation or a live run, specify prerequisites, admitted probes, required evidence,
explanation burden, stopping condition, non-goals, and what would remain untested. Do not move the
criteria after seeing the result merely to claim success.

### Step 4 — Design product and lifecycle

Specify the GoalContract, states, capability, raw event, compact view, answer schema, durable
product, dependencies, invalidation, child targets, and persisted artifacts. Always ask: what
happens immediately after success?

### Step 5 — Build the smallest vertical slice

Connect:

```text
controller state
-> model-visible GoalCard/tool
-> authorized action
-> production-shaped observation
-> evaluator
-> durable product
-> next gate
```

Avoid rich detectors invisible to the prompt. Avoid fixtures richer than the production adapter.

### Step 6 — Test behavior

Prove meaningful invariants: visible data, binding gate, exact action, raw/masked separation,
product persistence, fail-closed behavior, and the historical regression. Schema checks alone are
insufficient.

### Step 7 — Replay real artifacts

Use frozen executed evidence to verify the observed failure is addressed without inventing richer
inputs. Replay proves compatibility, not live model use.

### Step 8 — Run the cheapest discriminating live test

```text
local contract
-> frozen replay
-> one-world fast OpenRouter slice
-> dense OpenRouter Kaggle rehearsal
-> one-world Kaggle milestone
-> 2–3 world-type smoke when required
-> 25-world canary
-> controlled comparison
```

Do not use Kaggle to debug a narrow controller defect. Do not run 25 worlds for one handoff.

### Step 9 — Review executed evidence

Grade only preregistered criteria. Separate infrastructure, controller behavior, Duck explanation,
and game outcome. Mark each criterion pass, fail, partial, or untested.

### Step 10 — Turn friction into the next slice

Locate the first point where intended information or control diverged from execution. Repair that
boundary before adding intelligence above it.

### Step 11 — Update documentation

Update the slice document, index, current status, institutional memory, run review, and runbook.
Label older conflicting plans superseded; do not rewrite historical evidence.

## 8. Validation and execution

### Local suite

From active source:

```bash
PYTHONPATH=.:../tufa-arc-agi-framework/src .venv/bin/pytest -q \
  --ignore=tests/test_online_arcade.py \
  --ignore=tests/test_duck_native_observer.py
```

Current baseline: 351 passing offline tests.

### Focused OpenRouter run

Use a named config, explicit mode, and unique run name. Never print keys; credentials stay in the
ignored owner-only `.env`.

```bash
PYTHONPATH=.:../tufa-arc-agi-framework/src make interactive \
  CONFIG_PATH=configs/g4-orbits-vc33-openrouter-fast.json \
  VIRELAI_MODE=gated \
  RUN_NAME=<unique-name>
```

A folder with zero games or zero actions is infrastructure failure, not gate evidence.

### Kaggle promotion

Inspect the exact bundle. Reject missing manifest files, caches, virtual environments, and duplicate
directories. Import entry points from the isolated package, compile notebook cells, and execute
generated orchestration with services stubbed. Kaggle validates packaging, mounts, local vLLM,
checkpoint, accelerator, and notebook runtime; OpenRouter does not.

### Comparability

Do not compare runs as one cohort unless model, quantization, provider route, context, budgets,
worlds, passes, concurrency, source, and package identity are comparable.

## 9. Run-review method

1. Confirm benchmark state and elapsed budget.
2. Count actions and levels.
3. Read gate answers in order.
4. Read gate events and probe IDs.
5. Reconstruct decisive before/action/after transitions.
6. Compare raw and masked changes.
7. Verify active products and router state after handoffs.
8. Inspect transcript only around decisive calls or loops.
9. Grade preregistered criteria.
10. State what the evidence does not support.

Stream or summarize large logs. Never dump entire payloads or secrets.

## 10. Failure triage

| Class | First question |
|---|---|
| Packaging | Did the mount contain every referenced file? |
| Transport | Did ARC Online/model/provider answer? |
| Prompt delivery | Did the active branch contain the intended GoalCard or memory? |
| Tool visibility | Did Duck see the successful call's value? |
| Encoding | Did intent, action, coordinate, and tool schemas agree? |
| Representation | Could production emit the evidence assumed by tests? |
| Attribution | Were counter, ego, ground, and remote residue separated? |
| Lifecycle | Did success advance once while routine observations preserved products? |
| Semantics | Did Duck accurately use the evidence? |
| Budget | Was the target reached before action/token/time limits? |

Fix the earliest broken layer. Prompting cannot repair missing data. More actions cannot repair a
router that returned to a completed gate.

## 11. Historical failure checklist

- successful memory call with invisible return value;
- generated card bypassed by active prompt branch;
- mismatched intent/action encodings;
- scoped prediction failure confused with absence of remote effects;
- stalled or premature focus progression;
- record accumulation mistaken for mechanism compression;
- fixtures richer than production output;
- tests proving schema rather than model use;
- manifest references absent from Kaggle mounts;
- invalid comparisons across models, budgets, worlds, or concurrency;
- routine product update invalidating descendants;
- reference view carrying stale binding instructions;
- newly segmented fragment mistaken for an actionable object.

## 12. Documentation roles

- **North Star:** enduring goal and philosophy.
- **Operating protocol:** how the builder works.
- **Institutional memory:** current facts, evidence, and risks.
- **Build plan:** intended slices and dependencies.
- **Build slice:** one implemented change and tests.
- **Runbook:** execution and grading procedure.
- **Review:** direct evidence from one run.
- **Historical plan:** provenance after supersession.

Never edit an old review to imply later code was present. Add a dated correction or successor.

## 13. Current proof state

> **2026-09-26 UPGRADE - two-phase lever study (LOCKED).** Lever deepening is now two explicit
> phases. **Phase 1:** each lever alone, consecutive same-lever presses (AAAA) to period +
> classification - every lever, dynamic queue, newborns append. **Phase 2** (gated on
> Phase-1-complete): lever sequences (ABA, ABC) for reversal, persistence, couplings, and world
> mechanics. Governing docs, read before any G4 work: `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md`
> and `BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1_2026-09-26.md`. The current `G4.3-LEVER-LIMITS`
> gate's reversal/persistence are Phase-2 work being re-homed behind the Phase-1-complete signal.
> Ground truth committed at 1bf09e0 (373 offline tests green, Director-run).


### Live proven

- G0 action-surface reading on vc33.
- G1 pointer/god-mode assignment on vc33.
- G2 counter identification, prospective support, and total mask on vc33.
- G3 exhaustive eligible click sweep and aggregate inventory.
- E0004 and E0005 confirmed as levers.
- G4.1 effect anatomy for both.
- First G4.2 E0004 activation, total counter subtraction, and correct
  `NOVEL_STATE_REVEALED` classification for 264 world cells.

### Offline proven

- stable ignored counter baseline;
- G4.2 continuation through novelty;
- stopping on masked null or exact recurrence;
- recurrence-period recording;
- boundary interruption without false completion;
- evidence-bound orbit answers;
- 351 offline tests.

### Planned or live-unconfirmed

- September 26 baseline correction in a new live run;
- E0004 activation two and complete live orbit;
- E0005 live orbit;
- NAV/HYBRID G4.2 re-contact;
- new-object child G3 back-edge and parent return;
- richer G4 subtrees, G5 onward, and cross-level transfer.

## 14. Active G4.2 handoff

Current focused run:

```text
variants/ring9-cybernetic-gates/ARC3-Inference/runs/
20260926_070833_ring9-g4-orbits-vc33-openrouter-fast-rung-20260926-v3-live
```

Model: `qwen/qwen3.6-35b-a3b` through OpenRouter.  
World: `vc33-5430563c`.  
Budget: 30 minutes, 48 environment actions.  
Scope: G4.2 continuation after the baseline repair.

Pass criteria:

1. G0–G4.1 close.
2. E0004 activation one yields a novel masked state.
3. G4.2 remains active.
4. E0004 activation two executes.
5. Repetition reaches masked null or exact recurrence.
6. Duck submits an accepted orbit explanation.
7. E0005 becomes the next target.

Game score is outside scope. The zero-action folder ending only in `...v3` is a sandbox DNS
failure and contains no behavioral evidence. Keep it distinct from `...v3-live`.

## 15. Immediate next decisions

When the run finishes:

1. grade the seven criteria;
2. confirm G2/G3/G4 products survive the first orbit action;
3. inspect new visual entities without assuming they are levers;
4. write a run review;
5. if complete, design the new-object child target or next G4 subtree;
6. if failed, repair the first causal defect at the same scale.

Do not promote to Kaggle until focused OpenRouter passes. Do not broaden worlds until CLICK G4.2
is stable.

## 16. Replacement-builder readiness

A replacement builder is ready when they can answer:

- What epistemic target is active?
- Which facts are directly observed?
- Which product does the target consume and emit?
- What experiment could falsify the mechanism?
- What is the smallest execution that can test the change?
- Which source is editable and which artifacts are immutable?
- What must remain unknown after this slice?
- What evidence justifies promotion?

The central discipline is: mine first, build one complete vertical slice, test actual behavior, run
the smallest discriminating live experiment, and let friction define the next slice.

# Collaborator integration: Cybernetic Duck

**Prepared:** 2026-09-19  
**Primary working repository:** `/Users/stephenkaskin/Desktop/virelai-review/duck-virelai/`  
**Current source family:** `variants/ring9-cybernetic-gates/`  
**Latest completed live checkpoint:** Ring 9 G3 vc33 closure v3, completed and reviewed as a two-lever partial success plus counter-target loop  
**Current execution:** no live run; the next slice is local/OpenRouter repair and rehearsal  
**Purpose:** Give a new collaborator enough philosophical, evidential, architectural, and
operational context to contribute without inheriting obsolete assumptions.

> **Updated 2026-09-20:** This guide now reflects the completed G0-G2 v2 diagnostic, the
> post-freeze universal ontology prompt, and the binding Captain opening protocol. Use
> `DOCUMENTATION_INDEX_2026-09-20.md` for document authority and
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for the latest execution state.

> **Updated 2026-09-24:** Read
> `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-24.md` and
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-22.md` before the older status sections below.
> G3 is now implemented as exhaustive broad lever location; G4 is the in-depth study of each
> confirmed lever. Any newly appearing visual object opens an entity-specific G3 obligation.
> vc33 v3 found and prospectively confirmed two remote levers, then looped on the known counter
> object and failed exhaustive G3 closure. The reset bridge was not exercised. The normal
> development loop is now local tests -> fast OpenRouter -> dense Qwen3.6 rehearsal -> Kaggle
> milestone. Statements later in this dated guide that G3 is unregistered or that Kaggle is the
> immediate next step are superseded.

---

## 1. Read this first

This project is building an LLM-centered ARC game player called Duck. Duck runs through a Kaggle
notebook and interacts with an ARC environment through a constrained tool interface. The present
work is not simply trying to increase score by adding heuristics. It is trying to make Duck behave
like a cybernetic scientist:

1. intervene in an unknown world;
2. isolate the subject of control;
3. separate time or bookkeeping noise from causal state;
4. discover mechanisms through controlled experiments;
5. compress observations into a stable, falsifiable internal physics model;
6. explore world states that are genuinely novel under that model;
7. observe a win rather than guess one; and
8. describe the observed win in the language of the learned model.

The user defines intelligence here as:

> probing to understand the world, building an internal model, and then observing a win and
> describing the goal in the language of that internal model.

The win is never guessed. It is observed. Before a terminal transition occurs, the agent's mission
is to explore and explain the physics of the current section of the ARC grid multiverse.

Historical North Stars, work orders, controller doctrines, and deterministic-solver plans are
research material. They do not override this document or later user instructions. Mine them for
working mechanisms, tests, and vocabulary; do not resume their old architecture automatically.

---

## 2. Repository access and project boundaries

The user supplied access to three roots.

### 2.1 Hybrid project and active work

`/Users/stephenkaskin/Desktop/virelai-review/`

This is a collection of projects and evidence, not one repository. The active hybrid repository is:

`/Users/stephenkaskin/Desktop/virelai-review/duck-virelai/`

Important areas inside it:

| Path | Meaning |
|---|---|
| `baseline/duck-harness/` | Reference Duck/Tufa harness. Use it to understand how Duck's creators constrain prompts, actions, and tool calls. |
| `variants/ring9-cybernetic-gates/` | Current candidate source. This is the source family being built. |
| `variants/ring7/ARC3-Inference/virelai_v4/` | Older Captain-oriented implementation and major port donor. |
| `variants/ring8-*` | Historical hybrid experiments and reusable mechanisms. |
| `kaggle/<name>/` | Frozen upload packages. These are exported copies, not automatically the current source. |
| `runs/<name>/` | Actual execution evidence, evaluations, and downloaded Kaggle output. |
| `tools/` | Packaging and evaluation helpers. Read a tool before executing it. |
| `handoff/` | Operational memory and collaborator integration documents. |

The working tree contains extensive existing modified and untracked material. Preserve it. Do not
reset, clean, delete, or overwrite unrelated work. Many variants are directories rather than Git
branches.

### 2.2 Separate deterministic solver

`/Users/stephenkaskin/Desktop/virelai-golden/`

This is a separate deterministic, no-LLM solver whose package is `golden`. It is valuable prior art
for records, cuts, worldlines, role inference, masks, state identity, lever discovery, and
explanation. It is not the active hybrid source, and it is not identical to vendored
`virelai_golden` snapshots inside older hybrid variants.

Do not edit it casually. Port ideas into the selected Ring 9 source with provenance and tests.

### 2.3 Historical research root

Other material under `/Users/stephenkaskin/Desktop/virelai-review/` includes `golden_chamber/`,
`win-lab/`, the older `virelai_v4/` tree, recordings, research reviews, and archived variants.
These can deepen the ontology and reveal proven machinery, but filenames such as “North Star,”
“governing,” or “complete” describe historical decisions and reports.

### 2.4 Evaluation contamination rule

Do not inspect downloaded game-engine implementations to derive mechanics for evaluation. The
agent and the collaborator must learn mechanics from the supported action metadata, observations,
frames, and execution evidence. Environment implementation files may exist under
`environment_files/` or packaged dependencies; they are outside the epistemic boundary.

---

## 3. Provenance discipline

Always distinguish three things:

1. **Candidate source** — the editable implementation under `variants/`.
2. **Packaged copy** — the frozen source and notebook under `kaggle/`.
3. **Executed artifact** — the exact output produced by a particular Kaggle notebook version under
   `runs/`.

Matching names do not prove matching bytes. Use `source-manifest.json`, `package-manifest.json`,
`execution_receipt.json`, notebook version, and downloaded output.

For every claim, identify its evidence class:

- **Direct observation:** visible in execution output, frames, manifests, source, or a test run.
- **Builder report:** asserted in a historical build/status document but not independently rerun.
- **Hypothesis:** a proposed interpretation still requiring a discriminating experiment.

Never turn a builder report into a direct observation. Never turn a detector candidate into a
semantic law merely because its schema is populated.

---

## 4. The philosophical model

### 4.1 The grid block multiverse

Treat an ARC world as a sequence of integer grids: a flip book. Integers are perceptual classes,
not predefined semantic labels. A visible object is a hypothesized persistent entity supported by
footprint and transformation evidence. Frame-to-frame changes are literal pixel arithmetic before
they are named as motion, activation, collision, a counter, or a lever.

The model must keep two levels distinct:

- **Observation:** cell `(r,c)` changed from integer `7` to integer `4`.
- **Interpretation:** a life bar lost one unit, a door opened, or a body moved.

Interpretations must remain falsifiable and linked to the observations that support them.

### 4.2 Axiomatic archetypes

The opening action surface provides strong but limited structural information:

- ACTION1–ACTION4 imply an embodied control channel and a navigation-like world.
- ACTION6 requires coordinates and is Duck's pointer hand, producing a click/god-mode control
  archetype.
- Mixed movement and pointer actions imply a hybrid world.
- ACTION5 is an additional interaction channel whose effect must be learned.
- In hybrids, ACTION6 may activate an embodied ego before movement channels become effective.

These are interface axioms about the type of control available. They do not reveal exact
world-specific mechanics. Action numbers remain opaque identifiers in evidence and laws.

### 4.3 Cybernetic targeting

Duck receives one small target at a time. Each target is a gate with:

- one local question;
- satisfied prerequisites;
- admissible experiments;
- a bounded answer contract;
- direct evidence requirements;
- a prospective prediction where appropriate;
- a durable model product;
- explicit failure and reopening states; and
- a handoff to the next target.

The controller forces focus and sequence. Duck supplies the interpretation. The software must not
quietly answer the semantic question on Duck's behalf, and Duck cannot skip a required
demonstration with confident prose.

The sequence follows the dependency structure of the world:

```text
G0 action surface
  -> G1 ego / direct control
  -> G2 counter / bookkeeping noise
  -> G3 levers / remote consequences
  -> G4 reactions / terrain and entity response
  -> G5 environmental forces
  -> G6 scoped inertness
  -> G7 counter-masked novelty frontier
  -> G8 observed-win explanation
  -> cross-level transfer
```

Each gate is judged only on its own goal. Failure to solve a level does not mean an ego gate
failed. A win during an early experiment is preserved as an observed terminal event, but it does
not retroactively change the grading question of the active gate.

### 4.4 What “understanding” requires

Finding a label is insufficient. At every gate Duck must explain:

- what entity, relation, or process it found;
- how it behaves;
- under what conditions;
- which observations support the claim;
- which competing model remains possible;
- what future observation would falsify the claim; and
- what remains unknown.

Where possible, Duck freezes a prediction before a later action and the controller compares the
actual outcome within the declared scope. Remote changes remain visible even when a local
prediction succeeds.

### 4.5 Stable memory

Raw records accumulate for audit, but raw accumulation is not world-model growth. Stable memory is
a graph of compact, versioned, falsifiable laws. A contradiction reopens the producing gate and
invalidates dependent products. Downstream gates consume admitted products rather than all prior
transcript text.

---

## 5. Current control architecture

The active source is:

`variants/ring9-cybernetic-gates/ARC3-Inference/`

Important files:

| File | Role |
|---|---|
| `inference/framework/cybernetic_targeting.py` | Target registry, dependency router, assessments, and durable products. |
| `inference/framework/virelai_gates.py` | G0–G2 state machines and adapters, capability tokens, gate views, answer contracts, and routing. |
| `inference/framework/adaptive_ego_coverage.py` | Deterministic representative-first coordinate coverage for embodied/hybrid G1 branches. |
| `inference/framework/probe_evidence.py` | Lossless before/action/after evidence, total site transitions, local/remote partitions, and compact prompt views. |
| `inference/framework/ego_verification.py` | Prospective ego predictions, scoped comparisons, and `EgoLaw`. |
| `inference/framework/counter_verification.py` | Paired counter arithmetic, full-bar inference, rate prediction, min/max boundary confirmation, mask law, and locked-counter monitoring. |
| `inference/framework/masked_world_state.py` | Raw/HUD/world delta partition, reversible masking, retroactive state addresses, and state archive. |
| `inference/agent/tool_agent.py` | Model-visible tools, action bridge, prompt injection, artifact persistence, and gate-answer recording. |
| `tools/evaluate_gated_checkpoint.py` | G0/G1 checkpoint evaluator. |
| `tools/evaluate_g2_counter_checkpoint.py` | Receipt-bound G2 evaluator; recomputes arithmetic and requires human semantic review for PASS. |

### 5.1 Control mechanism inherited from Duck

Duck's creators already supplied the key enforcement points:

- the system prompt defines permitted tool behavior;
- `tool_agent.py` installs the action and Virelai bridges;
- the model must call `virelai('gate')` and `virelai('next_probe')`;
- the controller issues a server-authored capability token bound to gate, revision, probe, and
  exact action payload;
- `action(...)` accepts only the current token and exact action;
- stale, replayed, invented, or modified capabilities are rejected;
- outcomes are compiled from actual before and after frames;
- answers are stored separately from observations; and
- the router exposes only the first unresolved target whose prerequisites are active.

This is how we “force” Duck: constrain the available experiment and closure contract rather than
trying to persuade it with an increasingly long prompt.

### 5.2 Prompt discipline

The active source now supplies three prompt layers: the complete stable grid-multiverse ontology,
a stable cybernetic targeting mission, and the volatile GoalCard/evidence view for the one binding
target. The ontology gives Duck a language for hypotheses; it does not assert which roles or laws
exist in the current world. The GoalCard supplies focus, unmet requirements, admitted products,
and the next permitted operation.

The prompt upgrade is built and locally verified but was added after the completed version-2
package froze. That run therefore cannot validate the upgrade. The next package must receive new hashes,
a new receipt, and a new notebook version. See
`BUILD_SLICE_UNIVERSAL_ONTOLOGY_PROMPT_2026-09-20.md`.

Verify the actual request path whenever editing prompts. Historical failures included correctly
generated cards that were never inserted because an earlier prompt branch returned first.

Tool results must be visibly delivered to Duck. A successful Python expression whose return value
is not printed or injected is a failed interface from the model's perspective.

---

## 6. Implemented gate behavior

### 6.1 G0 — Action Surface

**Question:** Which opaque actions exist, and which require coordinates?

G0 blocks all environment actions until Duck acknowledges the exact interface metadata without
assigning semantic meanings. It produces an `ActionSurface` and a controller-supplied archetype
prior.

**Exit criteria:** exact metadata represented; semantic claims empty; epistemic limit states that
effects remain unknown until observed.

### 6.2 G1 — Ego

**Question:** Where and how can Duck directly influence this world?

For click-only worlds, ACTION6's coordinate requirement is sufficient to establish the pointer
ego as an interface axiom. Duck must still explain what the pointer is, how coordinates move its
control locus, its constraints, a competing model, and a falsifier. G1 then closes without wasting
clicks on target physics.

For navigation and hybrid worlds, G1 still performs behavioral localization and requires a
prospective demonstration. Hybrid worlds can schedule post-click retests of movement and ACTION5
channels when activation is plausible.

G1 produces a versioned `EgoLaw`. It does not identify counters, classify target effects, prove
inertness, or infer a win.

### 6.3 G2 — Counter

**Question:** Which visible process is bookkeeping noise, what does it track, and how can it be
reversibly removed from causal state identity?

G2 uses varied interventions until it sees a recurring change away from the acted site. The
counter is represented as two coupled integer objects:

- a source integer loses mass;
- a replacement integer gains the same mass;
- the literal rewrite is conserved pixel arithmetic, such as `7 -> 4`;
- the rewrite front advances within a stable horizontal, vertical, or connected two-class
  footprint.

The total site ledger lets the verifier recover the whole bar before every cell has individually
changed. If total coverage is absent, it falls back explicitly to observed support.

Duck must explain the tracked visible quantity, the mechanism, why recurrence across distinct
interventions supports bookkeeping, conditions, limitations, competing models, and a falsifier.
It must cite exactly the candidate witnesses.

G2 then freezes the observed rate and reuses a proven counter-only intervention. A successful rate
demonstration creates a provisional mask and an explicit boundary obligation. The bounded counter
identification gate may hand this product forward so later productive probes can observe:

- source count at the footprint minimum;
- replacement count at the footprint maximum; and
- either game-over at that extremum or a respawn from the extremal bar.

Only this consequence upgrades the counter model to `LOCKED_BY_EXTREMUM_BOUNDARY`. Before that it
remains `PROVISIONAL_BOUNDARY_PENDING`. If the exhaustive ranked opening shows no recurrence, G2
records `COUNTER_NOT_OBSERVED_WITHIN_OPENING` with its exact scope and a later reopen policy; it
does not claim global absence. Both forms live inside a `CounterGateProduct`.

### 6.4 HUD delta versus world delta

The mask never destroys the raw observation. The system derives three sets:

```text
raw_cells = hud_cells union world_cells
hud_cells intersection world_cells = empty
```

Counter-only transitions have nonempty raw delta but empty world delta. Simultaneous causal change
outside the counter survives in `world_cells`.

State identity is a hash of the grid after every counter cell is replaced by an out-of-domain
address token. Two raw frames that differ only in counter values therefore share one world
address. When G2 locks, retained lossless G2 transitions are replayed into the masked archive, so
the quotient applies retroactively.

The locked-counter monitor accepts established ticks and verified respawns. It requests reopening
for direct targeting, an unexpected hold, rate change, or different within-mask arithmetic that
could indicate causal entanglement. This monitor is implemented but cannot yet observe later-gate
actions because G3 is not registered.

---

## 7. Current verification and live execution status

### 7.1 Local status

The current Ring 9 source passes **280 tests**. Targeted lint passes for the G0-G2 controller,
counter verifier, masked state archive, prompt integration, packaging script, and tests. The full
suite has 14 pre-existing Matplotlib/PyParsing deprecation warnings.

Local tests establish implemented behavior and integration. They do not establish that the served
LLM interprets live ARC worlds correctly.

### 7.2 Historical live evidence

The downloaded Ring 9 G1 v2 pilot was cancelled after six vc33 probes. It is useful partial
evidence:

- vc33 exposed only ACTION6 and therefore should have closed G1 immediately as click/god mode;
- the old controller instead forced a coordinate sweep;
- every observed probe changed the top bar from integer 7 toward integer 4;
- one probe also caused a large non-counter effect;
- Duck noticed the counter-like process and the target-dependent effect;
- no G1 answer or demonstration occurred before cancellation.

This trace motivated the click-only G1 early exit. It does not prove the repaired G1 or G2 live
behavior.

Do not repeat the obsolete statement that prior systems had universally zero level-2 success. The
Ring 8 decision-controller v2 benchmark directly recorded two ft09 levels cleared and zero on vc33
and ls20; its behavioral trace was not fully graded.

### 7.3 Latest Kaggle run

Package:

`kaggle/ring9-g2-counter-checkpoint-v2/`

Launch record:

`runs/kaggle-ring9-g2-counter-checkpoint-v2/LAUNCH_RECORD.md`

Private notebook:

`https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g2-counter-checkpoint`

Notebook version 1 failed before `bm.run` because a duplicated stale G1 receipt block caused the
intended receipt check to reject the notebook. It contains no benchmark evidence. Repaired
notebook version 2 completed. vc33 found a recurrent counter in two probes and supported its first
prospective prediction on probe 3, but exhausted 48 actions before the min/max consequence. ft09
ended unresolved after twelve zero-delta clicks and then stalled. ls20 received no action because
the notebook-wide soft deadline expired. The full review is
`runs/kaggle-ring9-g2-counter-checkpoint-v2/REVIEW.md`.

The active source now enforces the Captain opening doctrine. It reads metadata, assigns world
type, uses a strict smallest-footprint/lowest-integer/top-left object roster, and preserves one
frontier from counter search into lever search. The exhaustive click arm is integrated. The
NAV/HYBRID arm now binds one ranked target while Duck chooses legal opaque pilot actions from its
G1 ego model. The controller preserves the target across approach moves and records direct
response, observed boundary, Duck-declared zero-delta contact, or bounded pilot exhaustion before
advancing. This arm is locally verified and live unconfirmed.

Fixed run identity:

- worlds: vc33, ft09, ls20, in that order;
- model: `vrfai/Qwen3.6-27B-FP8`;
- one pass;
- concurrency one;
- 48 environment actions per world;
- 1,800 seconds per world;
- 65,536-token context;
- 1,024-token tool output;
- gated mode;
- package hash `a4cd720994a5a65ca02b046dd1bd867308ff2e46563f2f54b3f4d346d53f318a`;
- source-manifest hash `bfbc33fa45e8496a35813afb2c0e28acca06eb9578d8fced0e801a8e812610cf`.

Before launch, all 176 source-manifest entries, 183 package-manifest entries, and 167 zipped
source entries matched their hashes. The dataset reached `ready` before the notebook was pushed.

The frozen version-2 package passed 269 tests before packaging. The active source reached 270 only
after the universal prompt slice, so the extra test and prompt changes are not part of this run.

The checkpoint is scoped to G0–G2. Level completion and lever understanding are not its grading
criteria.

---

## 8. How to evaluate the current run

Wait for the user to report completion or explicitly request a status check. Do not repeatedly
poll Kaggle.

When complete:

1. Record the notebook version and final Kaggle status.
2. Download output into a new immutable directory under
   `runs/kaggle-ring9-g2-counter-checkpoint-v2/kaggle-output/`.
3. Verify the output execution receipt matches the package and source-manifest hashes above.
4. Inspect notebook logs for setup, manifest, model-server, and runtime failures before reading
   behavior.
5. Count actual structured tool calls and gate events. Do not count repeated schemas in prompt or
   request logs as executions.
6. Review each world independently and grade only its active gates.

For G0, verify exact opaque metadata and no semantic guessing.

For G1, verify:

- the correct archetype;
- an adequate explanation of the ego and direct control;
- correct evidence basis for embodied/hybrid branches;
- immediate click-only closure where appropriate; and
- no target, counter, or remote-effect claim smuggled into the ego law.

For G2, verify:

- probes are varied until a candidate appears;
- the candidate is remote from acted sites;
- source loss equals replacement gain;
- the inferred full footprint actually contains both counter objects and no causal world object;
- Duck explains what changes and why it is bookkeeping;
- evidence references bind to the correct lossless transitions;
- the rate prediction was recorded before its test;
- the confirmation action is counter-only;
- source-minimum/replacement-maximum is actually visible;
- game-over or respawn actually coincides with the extremum;
- the mask covers the complete bar;
- counter-only frames share a world address; and
- simultaneous outside-mask change remains visible.

Possible dispositions are `PASS`, `FAIL`, `REPRESENTATION_GAP`, `BUDGET_EXHAUSTED`, or
`NOT_REACHED`. Do not grade a later gate as failed when its prerequisite never closed.

The existing evaluator is primarily G0/G1-oriented. Build a G2 evaluator from the structured
candidate, answer, comparison, boundary, mask, and state-archive artifacts. Automated checks can
establish protocol and arithmetic. Human frame review remains necessary for semantic correctness
and mask scope.

---

## 9. Historical failure classes to keep active

These are recurring engineering risks, not abstract warnings.

1. **Invisible successful memory calls.** The service returned data, but Duck saw no output.
2. **Generated cards bypassed by the active prompt branch.** Persistence did not imply delivery.
3. **Intent/action encoding mismatch.** Numeric IDs, names, and coordinate conventions diverged.
4. **Scoped prediction confused with global change.** Remote or HUD change incorrectly closed a
   local claim.
5. **Semantic focus stalled or advanced prematurely.** The controller failed to recognize closure
   or moved on from weak evidence.
6. **Record accumulation mistaken for model growth.** Large ledgers did not yield useful laws.
7. **Fixtures richer than production adapters.** Tests passed with fields that live execution did
   not supply.
8. **Schema compliance mistaken for actual model use.** A valid artifact existed but did not affect
   Duck's next decision.
9. **Manifest referenced absent mounted files.** Local packaging passed while Kaggle mount layout
   differed.
10. **Uncontrolled comparisons.** Model, budgets, worlds, concurrency, or prompt treatment differed.
11. **One-sided counter masks.** Masking only the depleting object left the replacement object to
    mint false states.
12. **Novel-target exploration during counter confirmation.** Continuing to click new objects
    entangled the counter experiment with lever effects. The current G2 reuses a counter-only
    action after candidate discovery.

Every new slice should include a production-shaped test for the relevant failure mode.

---

## 10. Engineering method

Use this rhythm for every gate:

1. **Step back:** state how the gate advances the cybernetic North Star.
2. **Mine:** locate prior art in baseline Duck, V4, Ring 8, and Golden.
3. **Separate:** identify what can be ported and which old assumptions must be discarded.
4. **Specify:** define the local question, evidence, permitted probes, model product, falsifier,
   reopening rules, and exit criteria.
5. **Build one slice:** prefer pure evidence machinery before routing, then route it through the
   existing controller.
6. **Test production shapes:** use the fields actually emitted by `probe_evidence.py` and the live
   adapter.
7. **Run focused tests and lint.**
8. **Run the complete source suite.**
9. **Freeze a package only at a meaningful checkpoint.**
10. **Evaluate only the stated goal.** Use friction and failure traces to refine the next slice.

Do not reinvent mechanisms that already worked. Port the smallest coherent unit with its
provenance and limitations. Do not port the old control policy just because a useful detector came
from it.

---

## 11. Build plan from the current frontier

### Phase A — Close G0–G2 with live evidence

1. Preserve the completed Kaggle version-2 output and its review as frozen evidence.
2. Preserve the frozen `ring9-g2-reliability-ls20-v1` package and queued notebook-v1 launch
   identities. Its receipt binds the 2,100-second deployment, 600-second reserve, and one
   1,200-second execution wave.
3. After completion, download and evaluate the ls20 trace against only the checkpoint's stated
   ego, piloting, counter-disposition, and runtime-delivery goals.
4. If a repair changes source or package bytes, create a new package and notebook version with a
   new launch record. Never treat local fixes as if they were present in an earlier execution.
5. Run the Duck-piloted embodied arm and use its trace to decide whether deterministic routing and
   controller-derived contact attribution must also be ported.
6. Declare G2 live-complete only when at least the fixed checkpoint worlds show correct gate
   behavior or receive explicit, evidence-backed dispositions explaining why the gate was not
   applicable or not reachable.

### Phase B — G3 lever discovery

**Question:** Which interventions produce effects outside the acted locus, under what conditions,
and on which subjects?

Start by mining:

- Golden `roles/lever.py`, `roles/mask.py`, weave/worldline attribution, and coverage;
- V4 `lever_dispatch.py`, `physics_accumulator.py`, `probe_outcome_classifier.py`, cycle probing,
  and world-state lever probing;
- Ring 8 effect channels, joint transforms, semantic mechanics, and pointer-depth adapters.

Build G3 in slices:

1. Feed every action through the locked-counter monitor and masked world delta.
2. Generate deterministic target classes from the current frame without semantic labels.
3. Probe one representative at a time.
4. Record target-local and remote world changes separately.
5. Create a `LeverCandidate` when an intervention has a repeatable remote consequence.
6. Require Duck to explain trigger, acted subject, affected subject, transformation, conditions,
   competing model, falsifier, and limitations.
7. Freeze a prediction and demonstrate the lever on a later action or state.
8. Emit a versioned `LeverLaw`.
9. Open child targets for multiple effects, depth, toggles, cycles, saturation, or conditional
   activation only when evidence warrants them.

G3 must not call every remote change a lever. Counter ticks are HUD delta. Ego motion and reactions
belong to their own subjects. A scoped prediction failure does not imply that no remote effect
occurred.

### Phase C — G4 reactions and terrain

Explain how entities respond to ego motion, contact, activation, lever effects, and state
conditions. Traversability, refusal, collision, carry, consumption, and transformation live here.
Terrain laws must remain scoped to tested boundaries and conditions.

### Phase D — G5 environmental forces

Test whether any world change recurs without a contemporaneous Duck intervention or known
lever/reaction driver. Produce a `ForceLaw` or evidence-backed `NOT_APPLICABLE`. Keep environmental
force distinct from the action-indexed counter.

### Phase E — G6 inertness

Attempt activation under a declared finite coverage policy. Certify only the exact object classes,
states, actions, and conditions tested. Negative evidence from G1 or G3 cannot prove universal
inertness.

### Phase F — G7 novelty frontier

Novelty means: “Have we seen this configuration of integers before after quotienting out the
locked counter?” It does not mean a changed raw frame.

Build:

- a persistent masked state archive;
- reachability edges labeled by exact interventions;
- visited versus frontier state addresses;
- selection driven by unresolved physics questions and reachable novel states;
- protection against counter ticks minting false novelty; and
- explicit provenance for why a chosen target is novel.

The key logic is that an already observed winning state would already have produced an observed
win. Exploration therefore seeks unvisited masked configurations without guessing which one wins.

### Phase G — G8 observed win

When a win actually occurs, preserve the terminal boundary, preceding state, action, active laws,
and relevant world entities. Duck then explains the win using its accumulated grammar. The product
must point to a real terminal transition.

### Phase H — Transfer

On a later level, convert the observed goal explanation into a falsifiable forward-facing
hypothesis. Re-test which ego, counter, lever, reaction, and goal laws survive. Preserve, specialize,
reopen, or reject them explicitly.

---

## 12. Immediate engineering limitations

The following work is not complete:

- The completed G0-G2 version-2 run did not close G2 on any world.
- The universal ontology prompt is present in active source but absent from the frozen executed
  package; its behavioral effect remains untested.
- The ranked click-everything and Duck-piloted NAV/HYBRID collision arms are integrated but absent
  from the completed package. Zero-delta contact remains a Duck-declared observation rather than
  an independently reconstructed geometric contact line.
- The deferred boundary monitor has a controller entry point but cannot yet receive productive
  later-gate actions because G3 is absent.
- The masked state archive currently replays G2 transitions with total site coverage. A future
  global archive must ingest every later transition.
- No G3 target is registered in the active router. After G2 satisfaction, the current code reports
  `G3-LEVERS` as the conceptual next target, but there is no lever state machine yet.
- G1 navigation and hybrid behavior has local coverage but still needs current live validation;
  ls20 was cancelled before its first action in the completed v2 run.
- The completed checkpoint exposed representation and budget failures. These are evidence, not
  reasons to silently loosen the gate.

---

## 13. Local commands and environment

From:

`/Users/stephenkaskin/Desktop/virelai-review/duck-virelai/variants/ring9-cybernetic-gates/ARC3-Inference`

Run the current suite with the selected source and vendored Tufa path:

```bash
PYTHONPATH=.:../tufa-arc-agi-framework/src .venv/bin/pytest -q
```

Run lint on changed files with:

```bash
.venv/bin/ruff check <files>
```

The bare shell may not expose `pytest`, `ruff`, or the correct package imports. Use the variant's
`.venv` and explicit `PYTHONPATH`. The full suite currently reports 270 passes.

The G2 package was produced by:

`tools/package_g2_counter_checkpoint.py`

The packager refuses to overwrite an existing package. A changed checkpoint should receive a new
version or carefully prepared replacement path. Always validate the direct source, zip contents,
package manifest, notebook compilation, serialized benchmark, and receipt before upload.

Kaggle mutations require explicit user authorization. That authorization was given for the current
G2 upload and has already been used. Do not infer perpetual authorization for future GPU runs.

---

## 14. Definition of success

The end state is not merely a solver that occasionally wins. Duck should exhibit a traceable form
of intelligence:

- it knows what actions it can issue;
- it knows what and where its ego is;
- it knows how its control channels move or alter that ego;
- it identifies and removes bookkeeping noise without losing evidence;
- it discovers levers and reactions through controlled experiments;
- it distinguishes environmental dynamics from action effects;
- it bounds inertness claims to tested conditions;
- it accumulates compact laws rather than transcript debris;
- it explores genuinely novel masked states;
- it recognizes a win only when the environment presents one; and
- it can explain that win using the physics grammar it learned.

Every implementation choice should make this behavior more reliable, more visible in evidence,
and easier to falsify.

---

## 15. Recommended onboarding sequence

1. Read this document completely.
2. Read `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-17.md` for historical evidence and failure
   details, treating it as operational memory.
3. Read `DOCUMENTATION_INDEX_2026-09-20.md` and
   `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for current authority and status.
4. Read `CYBERNETIC_TARGET_TREE_v1_2026-09-18.md` for the full target hierarchy.
5. Read `BUILD_SLICE_UNIVERSAL_ONTOLOGY_PROMPT_2026-09-20.md` and
   `BUILD_SLICE_G1_EXIT_AND_G2_EVIDENCE_KERNEL_2026-09-19.md` for current implementation decisions.
6. Inspect the active Ring 9 files listed in Section 5.
7. Run the full Ring 9 tests with the exact command in Section 13.
8. Inspect the version-2 launch record and wait for actual run output.
9. Evaluate G0–G2 before beginning G3 implementation.
10. When building G3, start with a repo mine and a written gate contract, then add one validated
   slice at a time.

If evidence contradicts this document, preserve the evidence, identify the exact stale claim, and
update the handoff. The project advances by making contradictions useful rather than hiding them.

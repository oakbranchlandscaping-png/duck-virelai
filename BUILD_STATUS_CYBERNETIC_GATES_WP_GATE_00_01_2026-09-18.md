# Build status: cybernetic gates WP-GATE-00-01

> **Historical status snapshot:** This file records the G0/G1 frontier on 2026-09-18. Use
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for the current G0-G2 state and prompt slice.

Date: 2026-09-18

## Status

The fresh `ring9-cybernetic-gates` source family contains the engineering slice for G0 action metadata and G1 ego discovery. The implementation is wired through Duck's analyzer bridge and runner as the separate `gated` mode. A private Kaggle G0 checkpoint has now passed on vc33, ft09, and ls20; no competition submission was made.

The first two post-checkpoint development layers are now implemented locally:

- **WP-H0 targeting substrate** moves the already-proven G0 behavior behind a reusable goal
  registry, dependency router, assessor, and versioned product journal.
- **WP-H1 compact capability interface** gives Duck a bounded GoalCard and a one-field probe token
  instead of requiring it to reconstruct controller-authored envelopes.
- **WP-H2 production evidence join** captures the real before/action/after boundary and compiles
  lossless integer-grid observations without assigning semantic roles.

Neither layer adds or claims G1 understanding.

This status separates three claims:

1. **Directly observed historical evidence:** pilot v2 produced 46 decision envelopes and their action/outcome joins are structurally valid.
2. **Locally verified engineering behavior:** the new gate rejects disallowed actions before the environment callback, accumulates evidence under one stable gate identity, requires an explanatory answer and prospective demonstration, and preserves opaque action names through the runner.
3. **Not yet observed:** an LLM actually completing G1 correctly on a real game, explaining the ego accurately, reusing that law in G2, or improving game performance.

## WP-H0 targeting-substrate checkpoint

Implemented:

- `GoalContract` for bounded Duck mini-goals;
- read-only `GateAssessment` separating grading from routing and action selection;
- ordered `TargetRegistry` with prerequisite validation;
- `TargetRouter` selecting the lowest unresolved ready target;
- versioned `MemoryProduct` and `TargetJournal`;
- descendant invalidation when a parent product changes;
- G0 `ActionSurface` and G1 `EgoLaw` registrations;
- target adapters that preserve the existing Duck bridge API;
- a compact current `goal_card` in gate snapshots;
- automatic relocking of G0 when the live action surface changes.

Checkpoint claim:

> The existing G0 checkpoint now runs through dependency-aware target infrastructure without
> changing its semantic boundary or permitting G1 before a current ActionSurface exists.

This checkpoint does not claim that the current G1 opening, evidence compiler, prediction
verifier, or EgoLaw is ready for a live G1 evaluation.

Current verification:

```text
29 passed — target registry/router/journal/assessment, gate behavior, Duck bridge, production fixtures,
and checkpoint evaluator
ruff: passed
py_compile: passed
```

The complete inherited suite currently stops during collection because the local declared
environment lacks the unrelated `taaf.game` dependency required by
`tests/test_duck_native_observer.py`. No changed gate test failed before that collection stop.

## WP-H1 compact-capability checkpoint

Implemented:

- compact `virelai('gate')` view containing the active GoalCard, progress counts, unmet
  requirements, and next operation;
- literal G0 answer template with `semantic_claims: []`;
- dedicated `virelai('next_probe')` returning the exact action payload and a short server-issued
  `probe_token`;
- `action(actions, decision={'probe_token': token})` as the complete model-facing action contract;
- HMAC-bound capabilities tied to gate revision, probe identity, and exact action payload;
- rejection of missing, invented, stale, replayed, extra-field, wrong-action, and wrong-coordinate
  uses before the environment callback;
- server-side reconstruction and journaling of the full ProbeEnvelope;
- paginated `virelai('gate_audit')` for coverage and evidence details;
- prompt instructions updated to the capability flow;
- automatic turn context changed from the full internal snapshot to the same compact GoalCard view,
  preventing audit detail from bypassing the operational interface.

The operational gate view remains below 512 estimated tokens even with a synthetic 400-component
coordinate coverage plan. The large coverage list appears only through the paginated audit view.

Current H1 verification:

```text
38 passed — targeting substrate, gate contracts, capability rejection paths, compact automatic
delivery, Duck bridge,
production fixtures, and checkpoint evaluator
ruff: passed
py_compile: passed
```

No private Kaggle run has been created for H1 yet.

## WP-H2 production-evidence checkpoint

Implemented:

- frame capture immediately before the admitted environment callback and reload immediately after;
- frame-derived `board_changed`, independent of the callback summary flag;
- content-addressed before/after frame references and full frame archives;
- lossless changed-cell artifacts with compact bounded previews;
- shapes, bounding boxes, integer transitions, and changed-region summaries;
- coordinate-action scope derived from the acted cell's before-frame equal-integer component;
- separate target-local and outside-target change counts;
- explicit `null` local/remote attribution for non-coordinate actions instead of inventing a locus;
- action-surface before/after, terminal boundary flags, and limitations;
- compact `virelai('evidence', id=...)` retrieval;
- evidence ID returned with the action result and joined across probe, compact event, full diff, and
  frame archive artifacts.

Current H2 verification:

```text
45 passed — evidence compiler, lossless/compact split, local/remote scoping, shape changes,
targeting substrate, capability interface, Duck bridge, production fixtures, and evaluator
ruff: passed
py_compile: passed
```

The compiler was replayed against the recorded G0-v2 viewer boards and gate artifacts. All three
probe/event/frame joins passed. Direct replay observations:

- **ft09:** zero changed cells after the recorded coordinate probe; the acted component contained
  four cells, with zero target-local and zero outside-target changes.
- **vc33:** one changed cell at `(0, 63)`, from integer 7 to 4; the acted eight-cell component was
  unchanged, so the observed change is outside that target scope.
- **ls20:** 52 changed cells across two changed regions; because ACTION1 had no acted-site
  coordinate, the compiler correctly leaves local/remote attribution unresolved.

These are observation statements only. The replay does not establish ego identity, a counter,
remote causation, a lever, or any game mechanic. The report is
`runs/kaggle-ring9-g0-checkpoint-v2/H2_EVIDENCE_REPLAY_2026-09-18.json`.
No new private Kaggle run has been created for H2; this checkpoint uses local production-shaped
tests and previously recorded execution artifacts.

## Live G0 checkpoint

The corrected private run `ring9-g0-checkpoint-v2` executed exactly the three declared worlds,
one pass and one environment action per world. The Qwen model produced one accepted G0 answer,
one G1 ProbeEnvelope, and one joined G1 event in every world. The target-aware evaluator passed
all checks with no unexpected artifact-producing worlds.

Direct observations:

- vc33: ACTION6 marked coordinate-requiring; first G1 site probe changed the board;
- ft09: ACTION6 marked coordinate-requiring; first G1 site probe did not change the board;
- ls20: ACTION1–ACTION4 marked non-coordinate; first paired ACTION1 probe changed the board;
- malformed G0 answers and incomplete G1 decision envelopes consumed zero environment actions;
- three total environment actions executed, exactly one per world.

This proves controlled protocol compliance and ordered entry into G1. It does not prove that Duck
has identified an ego or learned a correct movement law.

The traces also exposed an interface defect to fix before G1: the full gate response is long and
often truncated before Duck can recover the exact ProbeEnvelope. Duck repeatedly reconstructed
the envelope field by field. G1 needs a compact next-probe query or equivalent short response.

## Historical measurement repair

The pilot evaluator now reads the production layout, where decision envelopes are under `kaggle-output/artifacts/` and semantic events are under `kaggle-output/virelai/`.

The regenerated evaluation reports:

- all three required worlds present;
- 46 total decision envelopes: ft09 7, ls20 23, vc33 16;
- engineering joins pass in all three worlds;
- behavioral acceptance fails in all three worlds;
- no prospective test, matched prediction, or semantic revision was observed.

This supports the claim that the old controller plumbing recorded actions. It does not support the claim that the controller produced model acquisition. The result also preserves the direct observation that ft09 cleared two levels; it does not repeat the older false claim of universal zero level-2 success.

## Fresh source and provenance

- Source: `variants/ring9-cybernetic-gates/`
- Parent port material: `variants/ring8-decision-controller/`
- Parent HEAD at copy: `0efc7ca6cb0b9811128c9f44b90f821ec84a508e`
- Generated environments and caches were excluded from the source copy.
- `PARENT_PROVENANCE.json` records the parent source digest and keeps source, historical execution artifacts, and repaired evaluation distinct.

The existing repository changes outside this new source family were not modified or discarded.

## Implemented behavior

### G0: live opaque action metadata

- The model receives `ACTIONn` symbols rather than UP/DOWN/LEFT/RIGHT/SPACE/MOUSE aliases.
- Coordinate requirements for ACTION6 remain interface metadata.
- Action numbers are not assigned semantic effects.
- The action surface refreshes after executed transitions and newly offered actions extend G1 coverage without changing the gate ID.

### G1: ego/direct-influence gate

- Every offered non-reset, non-coordinate action is probed twice in a consecutive pair.
- ACTION6 targets one member-cell anchor from each frame-0 equal-integer connected component once.
- The current server-issued `probe_token` is binding.
- A missing, invented, stale, replayed, wrong-action, semantic-alias, or wrong-coordinate capability fails before the environment callback.
- Duck supplies only the token; the server preserves the complete ProbeEnvelope in the audit artifact.
- Successful outcomes create evidence IDs under stable gate ID `G1-EGO`.
- Coverage completion blocks further action until Duck submits a `GateAnswer`.

### Explanation and demonstration

A G1 answer must include:

- an identified subject and modality;
- a mechanism explaining what the ego is and how control changes it;
- action laws over opaque actions;
- conditions, constraints, alternatives, falsifier, and limitations;
- references to real evidence IDs;
- a scoped prospective prediction, an explanation of why it follows, and why the transition is novel.

A label-only answer is rejected. G1 closes only if the later demonstration matches the prediction; contradiction reopens it. A closed answer can be cited by a later decision through an explicit reuse event. The snapshot exposes G2 embodied-terrain as the next gate only after G1 closure.

### Prompt and memory delivery

- The universal prompt describes the grid as an observed integer-state flipbook connected by opaque actions.
- It introduces the block-multiverse archetypes without supplying game-specific mechanics.
- It states that a win is observed only through the platform boundary and must never be guessed.
- `virelai('gate')`, `virelai('next_probe')`, `virelai('gate_audit')`, and validation responses are automatically visible in Python output.
- Probe, evidence, answer, and reuse journals are separate artifacts.

## Verification

Full inherited and new local suite:

```text
183 passed
```

The suite includes:

- production-layout evaluator joins and a planted missing-bridge-file failure;
- stable gate identity across revisions;
- consecutive opening probes and finite pointer coverage;
- rejection before environment execution;
- label-only and copied/unscoped prediction rejection;
- prospective support and contradiction/reopen paths;
- dynamic action-surface extension;
- later action-law reuse;
- production-shaped pointer, embodied, conditional, and negative fixtures;
- legacy controller and non-gated regression coverage;
- real runner/observer checks that gated mode preserves opaque names;
- byte-identical raw runtime observations across semantic answer revision.

Python compilation also passes for every changed runtime module.

## Evidence limits and next checkpoint

The structural checks cannot judge whether Duck's explanation is true. Correctness still requires a visible behavioral trace and independent review of the cited cells/components and claimed transformation law.

G2 and later gates are not implemented. The compact capability interface, production evidence
join, scoped verifier, and bounded footprint-form verifier are now locally complete. Before a G1
behavioral checkpoint, H4 must replace exhaustive opening coverage with a discriminating adaptive
probe policy. The next controlled G1 trace should grade:

1. exact opening coverage and zero-step rejection;
2. whether Duck identifies the actual directly controlled subject;
3. whether its action laws match visible transitions;
4. whether its new prediction is genuinely prospective and correctly scoped;
5. whether the demonstration result is graded correctly;
6. whether G1 produces a versioned EgoLaw without requiring knowledge assigned to later targets.

Only after H4 passes its local exit criteria should this family be packaged for the fixed
vc33/ft09/ls20 Kaggle checkpoint.

## 2026-09-19 — WP-H3a scoped verifier port

H3 began with a port audit rather than a blank design. The resulting source map is
`PORT_MAP_G1_H3_SCOPED_VERIFIER_EGO_LAW_v1_2026-09-18.md`.

The first H3 slice ports the earlier controller's exact action/transition binding, scope-limited
comparison, four-way verdict taxonomy, remote-effect separation, and append-only revision model.
It adapts those behaviors to the H2 `virelai-probe-outcome-v1` record in
`inference/framework/ego_verification.py`.

Implemented in this slice:

- prospective predictions are frozen before the demonstration action;
- `VISIBLE_OBSERVATION`, `CELLS`, `REGION`, `ACTED_COMPONENT`, and unresolved `WORLDLINE`
  scopes are represented explicitly;
- `NO_CHANGE`, `ANY_CHANGE`, and `EXACT_CELL_DELTA` are compared against the lossless H2 diff;
- wrong probe, stale/retrospective transition, or wrong action returns `UNMATCHED`;
- missing scope identity, missing frames, geometry changes, and terminal boundaries return
  `INDETERMINATE` without widening scope;
- target-local and remote changes remain separate facts;
- G1 closes only on `SUPPORTED`, reopens on `CONTRADICTED`, and remains `UNRESOLVED` on
  indeterminate evidence;
- a supported demonstration creates an immutable, versioned `EgoLaw` with stable `law_id`;
- later reuse cites `law_id` and `law_version_id` rather than the explanatory answer ID;
- the production bridge gives the verifier the full outcome while storing and showing Duck only
  the bounded compact evidence view;
- the compact G1 answer contract now names the admitted scope and predicate vocabulary.

Verification:

```text
50 focused H2/H3/gate tests passed
204 tests passed across every locally collectable test module
ruff passed
py_compile passed
```

The full inherited collection remains blocked by the absent unrelated `taaf.game` package in
`test_duck_native_observer.py`. No Kaggle run was started.

The lexicon audit then replaced the tentative list with `STILL`, `RECOLOR`,
`PURE_TRANSLATION`, `GROW`, `SHRINK`, and `DEFORM`; `APPEAR` and `DISAPPEAR` were rejected as
pixel primitives. See `REVIEW_H3_TRANSFORMATION_LEXICON_PIXEL_ARITHMETIC_v1_2026-09-19.md`.

## 2026-09-19 — WP-H3b footprint transformation verifier

H3b ports the existing total pixel arithmetic and footprint relation logic into the production
probe and G1 demonstration path. Equal-shape outcomes now retain every held and changed site for
internal verification while the compact Duck view reports only coverage and the omitted count.
Geometry change remains typed absence.

The prospective contract now supports `STILL`, `RECOLOR`, `PURE_TRANSLATION`, `GROW`, `SHRINK`,
and `DEFORM` over exact before and predicted after 4-connected equal-integer component footprints.
It checks exact translated cell sets, keeps recolor independent of geometric form, scopes subject
change over the union of endpoint footprints, and reports remote changes separately. Unresolved
pre-action subjects abstain without scope widening; after-footprint mismatch contradicts the
prediction without guessing another identity.

Verification:

```text
76 focused H2/H3/G1/continuity tests passed
227 tests passed in the complete local suite
ruff passed
py_compile passed
recorded G0-v2 artifact replay passed for ft09, vc33, and ls20 with 4,096 total sites each
```

The detailed exit criteria and evidence boundary are recorded in
`BUILD_SLICE_H3B_FOOTPRINT_VERIFIER_2026-09-19.md`.

H3b proves that a correctly declared transformation can be checked and can create a versioned
`EgoLaw`. It does not establish that Duck selects the right subject or understands a real world's
ego. H4 adaptive coverage and a later reviewed behavioral checkpoint own those claims.

## 2026-09-19 — WP-H4 adaptive Delphi coverage

H4 retains the Captain's consecutive pair for every offered non-coordinate action and replaces
automatic coordinate enumeration with deterministic observational target classes. The class
record includes shape, size, repetition, border/field position, zone, adjacency, and containment.
One representative per coarse class is scheduled first.

A positive class receives one contrast. Disagreement forces enumeration of that class's remaining
members. Consistent classes keep untested members explicit. Uniformly negative representatives
stop as `REPRESENTATION_GAP_NO_VISIBLE_EFFECT`; they cannot create an inertness claim or admit an
`EgoLaw`. Temporarily unavailable coordinate actions and newly offered actions are handled as
typed coverage state rather than silently skipped.

Verification:

```text
44 focused H4/G1 interface tests passed
235 tests passed in the complete local suite
ruff passed
py_compile passed
recorded G0-v2 adaptive-coverage audit passed
```

The recorded ft09 frame contains 65 components but produces 8 initial representatives. vc33
produces 8 representatives from 11 components. ls20's board produces 14 classes from 20 components,
but its recorded action surface has no coordinate action, so those classes are not scheduled.

The detailed exit criteria are in
`BUILD_SLICE_H4_ADAPTIVE_DELPHI_COVERAGE_2026-09-19.md`; the machine-readable audit is
`runs/kaggle-ring9-g0-checkpoint-v2/H4_ADAPTIVE_COVERAGE_AUDIT_2026-09-19.json`.

This proves adaptive coverage behavior, not ego understanding. H5 and a reviewed G1 execution own
the next claim boundary.

## 2026-09-19 — WP-H5 behavioral evaluation and telemetry

H5 replaces the G1 aggregate structural pass with six independent grades: protocol, adaptive
coverage, explanation, prospective prediction, scoped demonstration, and human-reviewed
correctness. The first five can pass automatically while the checkpoint remains unsatisfied.
Correctness requires a human review of the supplied before/after evidence and must be bound to the
exact execution receipt hash.

The receipt requires package and manifest hashes, model id, action and token budgets, exact world
set, passes, concurrency, and gated mode. This prevents unlike executions from being treated as a
comparison. The review must name every answer-cited and demonstration evidence record it inspected.

Production journals now preserve the declaration-time H4 coverage certificate and normalized
prediction with a G1 answer. Demonstration events preserve the controller's scoped comparison and
the resulting versioned `EgoLaw`. The evaluator exposes these records together with lossless
outcomes and raw frame rows in a dedicated human-review packet. Later law consumption is telemetry
only and is no longer misclassified as a G1 completion requirement.

Verification:

```text
45 focused H5/G1 interface tests passed
238 tests passed in the complete local suite
ruff passed
py_compile passed
recorded G0-v2 evaluator compatibility passed on ft09, vc33, and ls20
```

The detailed contract and evidence boundary are in
`BUILD_SLICE_H5_BEHAVIORAL_EVALUATION_2026-09-19.md`. Synthetic grade fixtures demonstrate
evaluator behavior, not Duck's correctness. No new Kaggle package, upload, or run was performed.

## 2026-09-19 — G1 checkpoint package freeze

The H1-H5 source is frozen at `kaggle/ring9-g1-ego-checkpoint`. The notebook now verifies the
source manifest and exact execution receipt before benchmark start, then copies that receipt into
the run output for H5 evaluation.

Fixed run conditions are three worlds in declared order, one pass, sequential execution,
Qwen3.6-27B-FP8, gated mode, 24 environment actions and 1,200 seconds per world, 65,536 context
tokens, server-default model output, and 1,024 tool-output tokens.

Local package verification passed for 173 source-manifest files, 180 package-manifest files, 164
source-archive entries, both receipt copies, notebook compilation, serialized benchmark settings,
six critical H1-H5 source files, excluded caches, and bounded credential-pattern egress checks.

The exact hashes and fail-fast boundary are recorded in
`G1_CHECKPOINT_PREFLIGHT_2026-09-19.md`. The product and G2 entry threshold are recorded in
`G1_PRODUCT_AND_G2_ENTRY_CONTRACT_2026-09-19.md`. The package has not been uploaded or run.

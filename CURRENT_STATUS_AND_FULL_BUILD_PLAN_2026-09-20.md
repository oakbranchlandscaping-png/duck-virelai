# Cybernetic Duck: current status and full build plan

**Date:** 2026-09-20  
**Active source:** `variants/ring9-cybernetic-gates/`  
**Latest live checkpoint:** Kaggle notebook version 2, G0-G2, completed and reviewed  
**North Star:** Probe the world, build a stable internal physics model, encounter a win through
exploration, and only then describe the observed goal in the language of that model.

**Documentation authority:** See `DOCUMENTATION_INDEX_2026-09-20.md`. Dated plans and run records
remain evidence of their own time; they do not override this status map or the user's current
direction.

## 1. Evidence states used in this map

This plan uses four distinct labels.

| Label | Meaning |
|---|---|
| **LIVE CONFIRMED** | A completed Kaggle execution directly demonstrated the stated behavior. |
| **LIVE DIAGNOSTIC** | A Kaggle execution exposed useful behavior or friction but did not satisfy the gate's exit contract. |
| **BUILT, LIVE UNCONFIRMED** | The feature exists in the active source and passes local tests, but the served Duck has not yet demonstrated it in a complete Kaggle checkpoint. |
| **PLANNED** | The gate or slice has not been implemented in the active Ring 9 router. Prior art may exist elsewhere. |

Local schema compliance is never promoted to model understanding. A cancelled trace is never
promoted to a gate pass. A successful model-server smoke test is never promoted to a benchmark.

## 2. Executive status

| Gate or layer | Required product | Current state | Live evidence |
|---|---|---|---|
| Control harness | Binding target lock, exact authorized action, lossless evidence | **LIVE CONFIRMED** | G0 v2 forced ordered compliance on all three worlds and rejected malformed calls before execution. |
| G0 Action Surface | `ActionSurface` | **LIVE CONFIRMED** | G0 v2 passed vc33, ft09, and ls20. |
| G1 Ego | `EgoLaw` | **LIVE DIAGNOSTIC** | G2-v2 closed click-interface G1 on vc33 and ft09. ls20 was not reached; the accepted falsifiers still need semantic tightening. |
| G2 Counter | `CounterGateProduct` | **LIVE DIAGNOSTIC; REPAIR LIVE UNCONFIRMED** | Frozen v2 found and confirmed vc33's candidate but missed the boundary. Active source now supports provisional mask handoff or scoped not-observed closure; neither repair has live evidence. |
| G3 Levers | `LeverLaw` inventory and children | **PLANNED** | Older systems contain port material; Ring 9 has no registered G3 state machine. |
| G4 Reactions | Scoped reaction and terrain laws | **PLANNED** | Prior art only. |
| G5 Environmental forces | `ForceLaw` or bounded `NOT_APPLICABLE` | **PLANNED** | Prior art only. |
| G6 Scoped inertness | Bounded inertness certificates | **PLANNED** | Prior art only. |
| G7 Masked novelty | Persistent quotient-state graph and frontier | **PLANNED** | G2's local archive supplies the state-identity kernel, but global exploration is absent. |
| G8 Observed win | Evidence-linked `ObservedGoalLaw` | **PLANNED** | No Ring 9 observed-win gate exists. |
| G9 Transfer | `TransferredGoalHypothesis` | **PLANNED** | Historical carry machinery is port material, not current Ring 9 behavior. |

The project is therefore at the **G0 confirmed / click-G1 and G2 live-diagnostic** boundary. It
has not earned entry into G3 yet.

**Post-freeze protocol slices:** The active source includes the complete universal ontology,
cybernetic targeting mission, binding Captain opening protocol, strict exhaustive click ranking,
and a persistent ranked frontier. It also includes a Duck-piloted NAV/HYBRID collision arm that
binds one target while Duck chooses legal movement steps from its G1 ego model. It passes the
280-test suite but was not present in the executed version-2 package. G2 now avoids blind boundary
marches through provisional masking and gives a complete quiet opening a scoped terminal handoff.
Runtime preflight rejects schedules whose per-world promise cannot fit the deployment. See
`BUILD_SLICE_UNIVERSAL_ONTOLOGY_PROMPT_2026-09-20.md` and
`BUILD_SLICE_BINDING_OPENING_PROTOCOL_2026-09-20.md`, with collision details in
`BUILD_SLICE_DUCK_PILOTED_COLLISION_SWEEP_2026-09-20.md` and closure/runtime details in
`BUILD_SLICE_G2_PRODUCTIVE_CLOSURE_AND_RUNTIME_2026-09-20.md`.

## 3. What has been confirmed by a clean Kaggle run

### 3.1 G0 action-surface checkpoint

Ring 9 G0 checkpoint version 2 completed cleanly on the fixed three-world set using
`vrfai/Qwen3.6-27B-FP8`, one pass, concurrency one, and one environment action per world.

Direct observations:

- vc33 exposed coordinate-requiring `ACTION6`.
- ft09 exposed coordinate-requiring `ACTION6`.
- ls20 exposed non-coordinate `ACTION1` through `ACTION4`.
- Duck copied the exact opaque action metadata.
- Duck kept semantic claims empty and stated that effects remained unknown until observed.
- G0 closed before any real environment action.
- G1 then supplied the first binding probe.
- Exactly one authorized environment action executed in each world.
- Calls with missing or partial decision envelopes were rejected before reaching the game.

This confirms that the controller can make Duck acknowledge the action interface and follow the
gate order. It does not confirm that Duck understands an ego, counter, lever, or goal.

### 3.2 Production evidence capture

The same run directly confirmed that an admitted probe can be joined to a real before/after
observation. Its three first-probe outcomes were:

- ft09: no changed cells;
- vc33: the tested component remained unchanged while a remote cell changed from 7 to 4;
- ls20: 52 changed cells across two regions, with local-versus-remote attribution unresolved for
  the non-coordinate action.

These observations confirmed lossless capture and the need for scoped reasoning. They did not
establish what any changed region meant.

### 3.3 What is not a clean gate confirmation

G1 notebook version 2 was cancelled after six of eight vc33 click probes. It directly showed:

- vc33 is click-only at the interface level;
- six `ACTION6` probes each advanced a top-row 7-to-4 rewrite;
- one probe also produced a large outside-strip change;
- Duck noticed the counter-like strip and separated it from the larger target-dependent effect.

This is **LIVE DIAGNOSTIC** evidence. G1 never accepted an answer, froze a prediction, ran a
demonstration, or emitted an `EgoLaw`. ft09 and ls20 never began. The trace revealed that the old
G1 boundary was wrong: click-target coverage had been placed inside ego discovery.

G1 version 3 was cancelled without output and adds no evidence.

G2 version 1 loaded the model, completed its real-model smoke test, and then failed before
`bm.run`. A duplicated stale G1 receipt block changed the action/runtime budgets and caused an
intentional receipt mismatch. It contains no gate behavior and must not be counted as a Duck run.

### 3.4 Completed G2 version 2 checkpoint

Version 2 completed in 16 minutes 56 seconds with 60 total environment actions and zero cleared
levels. Its exact G2 receipt passed. The gate checkpoint did not pass.

Directly observed:

- vc33 closed click-interface G1 immediately, found a full-width recurrent `7->4` counter
  candidate in two actions, and supported a prospective one-cell rewrite prediction on action 3;
- the controller then repeated one counter-only click through action 48, leaving three source cells
  and never observing a min/max boundary consequence;
- ft09 closed click-interface G1, produced twelve zero-delta G2 observations, ended `UNRESOLVED`,
  and then spent time without further actions;
- ls20 received zero actions because the notebook-wide soft deadline expired;
- the package declared 1,800 seconds per world, but its 2,100-second deployment budget and
  600-second reserve produced a 1,500-second global soft deadline, making three sequential
  per-world allowances impossible.

Duck's vc33 explanation correctly described the counter geometry and rewrite, but overclaimed the
tracked quantity as click count despite the observed one-or-two-cell rate. Its G1 and G2
falsifiers also confused expected quiet/saturation with model falsification. Treat this run as
strong partial support for the targeting method, not a G1 or G2 semantic pass. See
`runs/kaggle-ring9-g2-counter-checkpoint-v2/REVIEW.md`.

## 4. What is built and locally verified but not yet live-confirmed

The current Ring 9 source passes **280 tests**. The package and checkpoint checks also pass lint,
notebook compilation, source-manifest verification, package-manifest verification, and ZIP
verification. These establish implementation integrity, not semantic success by the model.

### 4.1 Shared control and memory infrastructure

Implemented:

- target registry and prerequisite ordering;
- one active target lock;
- compact model-facing goal cards;
- exact `ProbeEnvelope` capability tokens;
- rejection of stale, replayed, wrong-action, and wrong-coordinate probes;
- append-only target journal;
- versioned memory products and dependency invalidation;
- lossless before/after evidence joins;
- separation of raw observations from semantic answers;
- receipt-bound automated evaluation plus human semantic review.

The model is given one narrow question at a time. It cannot move on merely by writing confident
prose; the controller checks the gate's evidence and product contract.

### 4.2 Universal ontology and action archetypes

The active interface teaches the flip-book view: integer grids, literal cell arithmetic,
footprints, transformations, competing explanations, and falsifiers.

The supplied action surface also creates a structural prior:

- `ACTION1`-`ACTION4`: navigation/embodied branch;
- `ACTION6` only: click/god-mode branch;
- movement plus `ACTION6`: hybrid branch;
- `ACTION5`: unknown embodied interaction channel until tested.

These are control-interface axioms and experimental obligations. They are not preassigned target
semantics.

The binding opening protocol now makes the branch operationally explicit:

- click worlds accept the pointer hand, then click every visual object once;
- navigation and hybrid worlds complete Delphi ego localization, then collide with every visual
  object;
- the counter is interpreted and masked first, while the same sweep frontier is preserved for
  later lever discovery;
- every object follows one strict rank: smallest footprint, lowest integer, nearest top-left
  member, deterministic coordinate tie-break;
- ranking orders experiments and never assigns semantic roles.

Both opening arms are integrated. In navigation/hybrid worlds the controller rebuilds the roster
from the post-G1 frame, excludes the identified ego and structural fields, binds one ranked target,
and lets Duck select each legal opaque pilot action. A target advances only on visible target
response, terminal boundary, Duck-declared zero-delta contact, or bounded pilot exhaustion. The
last two outcomes retain their weaker evidence status; deterministic routing and an independently
derived contact line remain future hardening.

### 4.3 G1 Ego

G1 asks: **Where and how can Duck directly influence this world?**

Implemented behavior:

- Click-only worlds close G1 after Duck explains that `ACTION6` is its pointer hand, coordinates
  move the control locus, no persistent visible body is required, and target effects remain for
  later gates. The resulting `EgoLaw` is marked as an interface axiom.
- Navigation worlds use paired movement probes to localize a persistent embodied subject and
  demonstrate an opaque motion law.
- Hybrid worlds establish the pointer branch, then test embodied localization and conditional
  activation. `ACTION5` remains an unknown interaction channel until observed.
- Negative probes do not prove inertness.
- Remote changes are preserved but do not automatically become part of the ego law.
- Embodied claims require an evidence-bound explanation, prospective prediction, later scoped
  comparison, and versioned `EgoLaw`.

The transformation verifier supports `STILL`, `RECOLOR`, `PURE_TRANSLATION`, `GROW`, `SHRINK`,
and `DEFORM` from total grid arithmetic and bounded subject footprints. Adaptive Delphi coverage
uses representative target classes and expands only on disagreement.

Live questions still open:

- Will Duck immediately close the click-only branch with the correct explanation?
- Can it find and explain embodied motion in ls20 without confusing world change with ego change?
- Can navigation/hybrid branches produce genuinely prospective, correctly scoped demonstrations?
- Does the resulting `EgoLaw` visibly guide the next gate?

### 4.4 G2 Counter

G2 asks: **Which visible process is bookkeeping noise, what does it track, and how can it be
reversibly removed from causal state identity?**

Implemented behavior:

- click-world interventions enumerate every frame-zero visual object in the strict shared ranking;
- the ranked frontier persists separately from counter demonstration and boundary detours so G3
  can resume it without false coverage;
- recurrent remote-rewrite detection across distinct intervention keys;
- rejection of directly targeted, same-site, reversed, flat, or geometrically inconsistent
  candidates;
- paired source-to-replacement arithmetic where source mass lost equals replacement mass gained;
- full horizontal, vertical, or connected two-class bar recovery from the total site ledger;
- explicit fallback to observed support when the full footprint cannot be proved;
- an evidence-bound Duck explanation of visible quantity, mechanism, bookkeeping rationale,
  competing model, falsifier, conditions, and limitations;
- a frozen prospective rate prediction tested on a later counter-only intervention;
- provisional masking and a `BOUNDARY_PENDING` obligation after rate confirmation, allowing later
  productive transitions to supply the min/max consequence;
- final lock only after source minimum and replacement maximum coincide with game-over or a
  verified respawn;
- a scoped `COUNTER_NOT_OBSERVED_WITHIN_OPENING` handoff after an exhaustive quiet opening;
- a versioned `CounterGateProduct` containing either the provisional/locked model and mask or the
  bounded search disposition;
- raw/HUD/world delta partition with raw evidence preserved;
- counter-masked state addresses, including retroactive replay of retained G2 transitions;
- a locked-counter monitor that accepts established ticks and respawns while reopening G2 for
  direct targeting, unexpected holds, rate changes, or new within-mask arithmetic;
- a G2 evaluator that also distinguishes `BOUNDARY_PENDING` and `COUNTER_NOT_OBSERVED` from
  `PASS`, `FAIL`, `REPRESENTATION_GAP`, `BUDGET_EXHAUSTED`, and `NOT_REACHED`, with receipt-bound
  human review for semantic correctness.

Live questions still open after the completed v2 diagnostic:

- Can the boundary consequence be observed without consuming the entire action budget through
  blind repetition?
- Can Duck describe the changing visible quantity without claiming an unsupported hidden variable?
- Can ft09 reach a productive bounded disposition rather than stall after zero-delta coverage?
- Can the collision driver expose and attribute counters in ls20 and other embodied worlds?
- Does the strict ranked click sweep improve counter and lever discovery in a live run?

### 4.5 Latest executed package

Kaggle notebook version 2 uses:

- worlds: vc33, ft09, ls20, in that order;
- model: `vrfai/Qwen3.6-27B-FP8`;
- one pass and concurrency one;
- 48 environment actions per world;
- 1,800 seconds per world;
- 65,536-token context;
- 1,024-token tool results;
- package hash `a4cd720994a5a65ca02b046dd1bd867308ff2e46563f2f54b3f4d346d53f318a`;
- source-manifest hash `bfbc33fa45e8496a35813afb2c0e28acca06eb9578d8fced0e801a8e812610cf`.

Version 2 removed the stale duplicate block and completed on an RTX Pro 6000. It is a frozen
artifact and does not include the later universal-prompt or binding-opening-protocol slices. Its
downloaded output and review live under `runs/kaggle-ring9-g2-counter-checkpoint-v2/`.

## 5. Exit decision from the completed checkpoint

The completed output was evaluated per world and per reached gate. G0 retained its earlier clean
confirmation. The click-interface portion of G1 and the vc33 recurrence/prediction portions of G2
earned diagnostic support, but the checkpoint did not satisfy the complete G1/G2 exit contracts.
The criteria below remain binding for the next execution.

### G0 exit

- exact opaque action metadata;
- correct coordinate requirements;
- no guessed action effects;
- ordered transition into G1.

### G1 exit

- correct control archetype;
- clear ego or control-locus explanation;
- explanation of how that ego moves or is placed;
- target effects excluded from click-only ego claims;
- embodied/hybrid laws supported by prospective scoped evidence;
- versioned `EgoLaw` created and delivered to G2.

### G2 exit

The controller may hand off a supported provisional mask with an explicit boundary obligation, or
a scoped `COUNTER_NOT_OBSERVED_WITHIN_OPENING` result after complete bounded coverage. Those are
productive gate closures, not locked-counter semantic passes. A full locked-counter pass requires:

- recurring candidate comes from varied interventions and is remote from the acted locus;
- literal source-to-replacement arithmetic is correct;
- full footprint contains the complete counter and no causal world object;
- Duck's explanation cites exactly the relevant evidence;
- rate prediction precedes its test;
- confirmation is counter-only;
- min/max extremum is observed;
- game-over or respawn is observed at the extremum;
- mask removes the complete counter while preserving outside change;
- masked state identity collapses counter-only frames;
- human frame review confirms the semantics and scope.

If a prerequisite does not close, later gates are `NOT_REACHED`, not failed. If the representation
cannot express what the frames show, record `REPRESENTATION_GAP`. If the correct procedure runs
out of budget, record `BUDGET_EXHAUSTED` and repair only the relevant gate.

## 6. Full build ladder after G2

### G3 — Levers

**Question:** Which acted-on structures produce effects elsewhere, under what conditions, and on
which subjects?

Build slices:

1. Install the locked-counter monitor as a cross-gate observer.
2. Feed G3 counter-masked world deltas rather than raw HUD-contaminated change.
3. Resume the persisted ranked object frontier produced by the opening protocol.
4. Click or collide with the next untried object according to world type, preserving target-local
   and remote changes separately.
5. Create a `LeverCandidate` only for repeatable intervention-indexed remote effects.
6. Require Duck to explain trigger, acted subject, affected subject, transformation, conditions,
   competing explanation, falsifier, and limitations.
7. Freeze a prediction and demonstrate it later.
8. Emit a versioned `LeverLaw`.
9. Open child targets for depth, toggles, cycles, saturation, reversal, or conditional activation
   only when observed.

Exit: at least one lever law is correctly demonstrated, or bounded evidence supports
`NOT_APPLICABLE`; counter ticks, ego motion, and coincident reactions are not mislabeled as levers.

### G4 — Reactions and terrain

**Question:** How do subjects respond to ego motion, contact, activation, lever effects, and state
conditions?

Build scoped laws for movement refusal, collision, traversability, exchange, pushing, carrying,
consumption, toggling, transformation, and destruction only as observations demand them.

Exit: every law names driver, responder, condition, transformation, evidence, demonstration, and
falsifier. Untested boundaries remain unknown.

### G5 — Environmental forces

**Question:** What changes without a contemporaneous Duck intervention or known causal driver?

Build no-op or controlled-wait comparisons where the action surface permits them, subtract known
counter/ego/lever/reaction effects, and search for recurring residual dynamics.

Exit: a demonstrated `ForceLaw` or a bounded `NOT_APPLICABLE` product. Action-indexed counter
change is not an environmental force.

### G6 — Scoped inertness

**Question:** Which tested object classes fail to respond to which interventions and conditions?

Use finite declared coverage, controls, and state-conditioned retests. Promote only bounded
negative claims. Earlier negative ego or lever probes cannot prove universal inertness.

Exit: each certificate lists class, actions, states, coverage, evidence, and invalidation trigger.

### G7 — Counter-masked novelty exploration

**Question:** Which reachable world configurations of integers have not been observed after
bookkeeping noise is removed?

Build:

- a persistent masked state archive across all later gates;
- exact action-labeled reachability edges;
- visited and frontier state addresses;
- frontier selection driven by unresolved laws and reachable novelty;
- safeguards against counter ticks minting false novelty;
- loop, dead-end, and reset handling;
- compact state summaries that Duck can actually use.

The search rule is literal: if a masked configuration has been seen, it is not novel. Because an
already observed winning configuration would already have produced an observed win, exploration
continues toward reachable unseen configurations without guessing what the win looks like.

Exit: Duck deliberately reaches a previously unseen masked state for a stated physics reason and
the archive proves it was unseen.

### G8 — Observed win explanation

This gate opens only after the environment presents a real terminal win.

Preserve the preceding masked state, terminal state, exact action, active laws, relevant subjects,
and boundary change. Duck then explains the observed win using its accumulated grammar.

Exit: an `ObservedGoalLaw` bound to the real terminal transition. No inferred or imagined win
condition is admissible.

### G9 — Cross-level transfer

Convert the observed goal law into a falsifiable `TransferredGoalHypothesis` for the next level.
Recheck action surface, ego, counter, mechanisms, and layout. Preserve, specialize, reopen, or
reject prior laws explicitly.

Exit: Duck uses transferred knowledge as a testable goal and verifies whether the terminal
relationship recurs in the new world.

## 7. Engineering rhythm for every remaining gate

1. Step back and state how the gate advances the North Star.
2. Mine baseline Duck, V4, Ring 8, and Golden for port material.
3. Record direct observations, builder reports, and hypotheses separately.
4. Specify the gate question, permitted probes, required product, falsifier, reopening rule, and
   explicit exclusions.
5. Build the smallest complete evidence slice.
6. Test only with fields the production adapter truly emits.
7. Prove the result reaches Duck's active prompt/tool path.
8. Run focused tests, production-shaped replay, lint, and the full suite.
9. Freeze source, package, notebook, manifests, receipt, worlds, model, budgets, and concurrency.
10. Run one checkpoint and judge only the gate's stated purpose.
11. Use friction to repair that gate before opening the next one.

## 8. Immediate order of operations

1. Preserve the completed version-2 package and output as immutable execution evidence.
2. Preserve the frozen `ring9-g2-reliability-ls20-v1` package and queued notebook-v1 launch
   identities.
3. After completion, download and judge only G1 ego localization, Duck piloting, counter-search
   disposition, and runtime delivery.
4. Tighten G1/G2 semantic checks for interface-versus-effect and visible-quantity-versus-hidden-
   variable claims.
5. Use the embodied trace to decide whether Duck piloting is sufficient or whether to port Golden's
   deterministic route planner and controller-derived contact line.
6. Register G3 so productive lever probes feed the deferred counter-boundary monitor.
7. Declare a counter locked only after the min/max consequence is observed; then use that stable
   model and mask throughout the later gates.
   G3 on the persisted ranked frontier.

The build should not advance to lever implementation merely because the G2 code exists. The next
earned milestone is a clean, interpretable G0-G2 live trace.

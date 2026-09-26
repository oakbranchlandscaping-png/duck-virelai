# Current Build Map: Cybernetic Duck

**Date:** 2026-09-19  
**Role:** Current execution map, subordinate to the user's stated North Star  
**Scope:** What exists, what has been demonstrated, what remains, and the next build rhythm

> **Superseded status snapshot:** This map records the frontier before the G2 build. Use
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for current status. G2 is now built locally,
> notebook version 1 failed before the benchmark, repaired version 2 is queued, and the universal
> ontology prompt slice was built after that package froze.

## North Star

Duck is being shaped into a cybernetic investigator of an ARC grid world.

Its pre-win objective is to probe the world systematically, construct a stable internal model of its physics, and explain that model in a shared grammar. The win is never guessed. It is observed as a terminal event. Only after observing it may Duck describe the goal using the model it has learned and carry that description forward as a falsifiable hypothesis for the next level.

The controller gives Duck one narrow epistemic target at a time. A gate closes only when Duck can identify the relevant mechanism, explain it, make a prospective prediction, and demonstrate the prediction against a later observation. Later gates may depend on and test the products of earlier gates.

## Cybernetic target sequence

| Gate | Question Duck must answer | Required product | State |
|---|---|---|---|
| G0 — Action surface | What actions and arguments are available? | Grounded action inventory | Live checkpoint demonstrated |
| G1 — Ego | How can I directly influence the world, and how does that influence move or transform? | Verified `EgoLaw` | H3 verifier and H4 adaptive probing locally complete; evaluation and live semantic success pending |
| G2 — Counter | Which changing structure represents time, budget, score, or other bookkeeping noise? | Counter identity and masking rule | Not built |
| G3 — Levers | Which acted-on structures cause changes elsewhere? | Lever and remote-effect laws | Not built |
| G4 — Reactions | What conditional responses follow actions or contacts? | Reaction laws | Not built |
| G5 — Environmental forces | What changes without direct action? | Autonomous dynamics laws | Not built |
| G6 — Scoped inertness | Which tested objects fail to respond under a defined action and context? | Bounded inertness claims | Not built |
| G7 — Counter-masked novelty | Which world configurations have not been observed after bookkeeping noise is removed? | Novel-state frontier | Not built |
| G8 — Observed win explanation | Which observed transition produced the terminal event, and how is it described by the learned physics? | Evidence-linked win explanation | Not built |
| G9 — Cross-level transfer | How can the observed win be expressed as a testable goal in the next level? | Forward hypothesis, not assumed truth | Not built |

This order is a dependency spine. Parent categories may open narrower subtrees when evidence warrants them. It is not a fixed ontology that forces every world to contain every mechanism.

## Engineering map for G1

### Built and locally validated

1. **Gate kernel and routing**
   - Generic goal contracts, gate registry, active-gate routing, append-only journal, and dependency invalidation exist.
   - G0 and G1 are registered as separate targets.

2. **Compact capability interface**
   - Duck can inspect the active gate and request the next authorized probe.
   - The server issues a probe token and rejects stale, replayed, wrong-action, and wrong-coordinate probes before execution.
   - Audit detail is retained separately from Duck's compact view.

3. **Production evidence join**
   - Real before/after frames are joined to the authorized probe.
   - Evidence records include local change, remote change, terminal status, limitations, and frame references.
   - Production-shaped replay has exercised this path.

4. **Scoped prospective verifier and `EgoLaw` base**
   - Predictions bind to an exact action, probe, transition, and prospective scope.
   - Base predicates are `NO_CHANGE`, `ANY_CHANGE`, and `EXACT_CELL_DELTA`.
   - Results are `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, or `UNMATCHED`.
   - Boundary and unresolved-scope cases abstain rather than create false certainty.
   - Remote changes remain separate from the tested local claim.
   - A supported demonstration may close G1; contradiction reopens it; indeterminate evidence does not close it.
   - `EgoLaw` is immutable and versioned, with a stable identifier for later gates to cite.

### Direct evidence obtained so far

- The G0 Kaggle checkpoint completed on three worlds with one authorized action per world and exact protocol compliance.
- Production replay observed:
  - `ft09`: zero changed cells after the tested action.
  - `vc33`: the clicked component was unchanged while a remote cell changed from 7 to 4.
  - `ls20`: 52 cells changed across two regions; the non-coordinate action left local-versus-remote attribution unresolved.

These observations validate evidence capture and show why scope matters. They do not identify the ego or establish a world mechanic.

### What has not been demonstrated

- Duck has not yet correctly identified and explained an ego in a live world.
- No production `EgoLaw` has been behaviorally validated.
- Local tests show that control contracts, evidence binding, and verifier rules work. They do not show that the model uses them to understand a world.
- The G0 checkpoint proves protocol obedience, not G1 semantic understanding.
- Older benchmark results belong to different packages and objectives. They cannot serve as evidence for the current G1 build.

## Immediate construction frontier

### H3b — Transformation vocabulary and footprint arithmetic — locally complete

Repository review found useful prior art and established the correct layering:

1. site arithmetic: held versus changed sites;
2. footprint arithmetic: before and after membership of a declared subject;
3. form verbs: the smallest defensible transformation description;
4. correspondence: birth, death, split, merge, and ambiguous identity;
5. repeated-transition mechanics: toggle, cycle, saturation, permutation, and conservation.

The active implementation now has a total grid-backed transition view and bounded before/after subject footprints. It verifies:

- `STILL`
- `RECOLOR`
- `PURE_TRANSLATION`
- `GROW`
- `SHRINK`
- `DEFORM`

Recolor should remain independently expressible when combined with a geometric change. Correspondence terms and repeated-transition mechanics remain deferred until their evidence requirements exist.

H3b passed 76 focused tests and the full 227-test local suite. Replaying the recorded G0-v2
artifacts produced total 4,096-site ledgers for ft09, vc33, and ls20. These results prove the
verifier and evidence path, not Duck's semantic use of them. The exit receipt is
`BUILD_SLICE_H3B_FOOTPRINT_VERIFIER_2026-09-19.md`.

### H4 — Adaptive Delphi coverage — locally complete

The probe planner now retains consecutive non-coordinate pairs and replaces exhaustive coordinate
enumeration with deterministic observational target classes. It probes one representative per
class, contrasts positive classes, and expands all remaining members only after within-class
disagreement. The certificate retains explicit unknowns and forbids inertness promotion.

Recorded ft09 coverage falls from 65 automatic coordinate probes to 8 initial representatives.
Embodied, pointer/null, mixed, conditional, no-visible-effect, unavailable-action, and
representation-gap branches pass locally. See
`BUILD_SLICE_H4_ADAPTIVE_DELPHI_COVERAGE_2026-09-19.md`.

### H5 — Behavioral evaluation and telemetry — locally complete

The evaluator now issues independent protocol, adaptive-coverage, explanation, prediction,
demonstration, and correctness grades. The first five are automated. Overall G1 satisfaction
requires a human correctness review bound by SHA-256 to the exact execution receipt.

The receipt fixes package, manifest, model, action and token budgets, world set, pass count, and
concurrency. The review packet exposes the answer, cited events, lossless outcomes, scoped
demonstration, and raw before/after frame rows. Later law consumption is reported separately and
is not a G1 exit condition.

The controller now persists the declaration-time H4 coverage certificate and normalized
prediction with the accepted answer, and persists the scoped comparison and resulting versioned
`EgoLaw` with the demonstration event. See
`BUILD_SLICE_H5_BEHAVIORAL_EVALUATION_2026-09-19.md`.

## Validation ladder

| Step | Status |
|---|---|
| Gate kernel tests | Passed locally |
| Interface contract tests | Passed locally |
| Production evidence replay | Passed for H2 |
| Scoped verifier replay | Base and six footprint-form predicates passed locally |
| Adaptive coverage simulation | Passed locally; ft09 65 candidates → 8 representatives |
| Local production-shaped answer→prediction→form verdict→`EgoLaw` | Passed with synthetic production-shaped frames |
| Six-grade behavioral evaluator and receipt binding | Passed locally; human correctness cannot be inferred from schema |
| Manifest-verified H1-H5 G1 checkpoint package | Frozen locally; 173 source files and 180 package files verified |
| Private Kaggle protocol smoke | G0 version completed |
| Private full G1 pointer and embodied checkpoint | Pending explicit upload/run authorization |
| Three-world G1 confirmation | Pending |

## Mini-build rhythm

Each stage should follow the same evidence-preserving cycle:

1. Mine the repository and record the port map.
2. State the single question, required product, acceptance evidence, and exclusions.
3. Implement the smallest complete slice.
4. Keep fixtures within the production adapter's actual output.
5. Run focused checks and the relevant regression set.
6. Replay production-shaped observations.
7. Update the status record with direct observations, builder reports, and hypotheses kept distinct.
8. Package only after the local slice is coherent; verify that the manifest names files actually present in the Kaggle mount.
9. Upload and run only with authorization.
10. Review the behavioral trace against that gate's own goal.
11. Close, revise, or expand the gate based on evidence before advancing.

## Next action

The H1-H5 package is frozen at `kaggle/ring9-g1-ego-checkpoint` with an exact execution receipt.
The next operation is the private Kaggle upload and run, followed by H5 frame review. G2 remains
closed until every required checkpoint world passes protocol, coverage, explanation, prediction,
demonstration, and receipt-bound human correctness. See
`G1_PRODUCT_AND_G2_ENTRY_CONTRACT_2026-09-19.md`.

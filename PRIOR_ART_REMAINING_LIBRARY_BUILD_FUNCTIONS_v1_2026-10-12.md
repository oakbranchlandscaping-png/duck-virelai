# Prior art: remaining library build functions

**Date:** 2026-10-12
**Scope:** work after the world-description survey: test rhythm, G4 study, early-gate reliability, G5/G6, reports, recovery, transfer, packaging, and release evidence
**Accepted runtime:** `b635fb9`
**Companion:** `PRIOR_ART_WORLD_DESCRIPTION_GRAMMAR_v1_2026-10-12.md`
**Status:** read-only survey; paths marked draft or untracked are not accepted source

## 1. Test-runtime infrastructure

### Prior art

- `inference/framework/record_replay.py`
  - `load_record` at line 66;
  - `click_world_machine` at line 86;
  - `replay` at line 212;
  - saved-answer replay helpers at lines 278–314.
- Module-scoped replay fixtures already exist in `tests/test_g3_hybrid_lifecycle_replay.py` and `tests/test_memory_m1.py`.
- Compressed fixtures cover ft09, ls20, vc33, k008, and k013 under `tests/fixtures/`.
- `BUILD_RHYTHM.md` now defines T0/T1/T2 expectations.

### Reuse

Cache immutable decoded records and module-scoped replay setup. Group tests by dependency surface and fixture. Use pytest duration output and collected node IDs to prove the tier definitions.

### Gap and warning

There is no accepted tier runner, duration manifest, or proof that a fast floor collects the intended contracts. Viewer caches and agent decision caches are runtime features, not test infrastructure. Do not create shared mutable gate machines between tests; replay state is mutable. Do not improve time through skipping, xfail, golden changes, or order dependence.

## 2. G4 per-lever dossiers and selected study

### Prior art

- `inference/framework/lever_dossier.py`: G3 witness summaries and exact local/remote residue checks.
- `inference/framework/g4_reactions.py`: effect channels, exact residue coverage, anatomy compilation, and answer validation.
- `inference/framework/g4_guided.py`: repeat-run state, mechanism typing, and guided study lifecycle.
- `inference/framework/g4_limits.py`: limit probes, observations, per-lever study state, and bounded answers.
- `inference/framework/g4_relations.py`: regions, predictions, grading, outcomes, and validated relation answers.
- `inference/framework/g4b_gate.py` and `g4c_gate.py`: relation and prospective-law products.
- `inference/framework/controller_executor.py`: controller anatomy answers around lines 490–533 and G4 owned steps around lines 307–378.
- `inference/framework/library_agenda.py`: existing G4 chapter questions and product dispositions.
- Tests: `test_g4_reactions.py`, `test_g4_phase1_boundary.py`, `test_g4b_gate.py`, `test_g4c_gate.py`, `test_r9_r22_lever_typing.py`, and `test_ft09_ladder_offline.py`.

### Reuse

Project existing gate state into one schema-v3 dossier per G3 lever. Preserve separate anatomy, orbit, relations, law, conditions, contradictions, and limits chapters. Reuse the G3 selection pattern for question identity and durable choice events, while keeping G4's own mandatory work and lifecycle authoritative.

### Gap and warning

No accepted artifact currently preserves every G4 chapter at every stop. Product aggregates may omit accepted in-progress per-lever answers. Capture these at LIVE_VIEW, H1, and H2 while state exists; do not add a parallel belief ledger. G4 selection must not bypass the existing prospective-test freeze.

## 3. G1 NAV reliability and answer-loop removal

### Prior art

- `inference/framework/virelai_gates.py` lines 347–936: G1 coverage, adaptive coordinate coverage, stop reasons, and coverage certificate.
- `inference/framework/controller_executor.py`: `next_owned_step`, `_nav_step`, certified answers, and controller answer synthesis.
- `inference/agent/tool_agent.py` around lines 3370–3430: contract-repair and no-progress loop detection, currently converted into controlled stops.
- `inference/framework/solver.py` lines 685–705: submission-mode rest after a controlled stop.
- `tests/test_l1a_pointer_g1_contract.py`: repaired click-only contract.
- `tests/test_nav_branch_foundations.py`, `test_ring9_nav_live_replay.py`, and the ls20 fixtures: NAV behavior and saved histories.
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v1_2026-10-09.md` lines 144–170: the original nine-case diagnostic contract.

### Reuse

Replay the nine named HYBRID cases and report evidence available, answer template, rejection, and stop cause. Prefer a record-derived controller answer when the gate already has enough evidence. Otherwise close explicitly unresolved with a typed reason and let the library show the foundation gap.

### Gap and warning

The existing runtime detects a repair loop after repeated bad attempts; it does not embody the desired one-check rule. A rejected hypothesis should be recorded once and the ladder should advance or close. Do not weaken click-only G1 or certify downstream roles on an unresolved foundation.

## 4. Environmental forces and residual dynamics

### Prior art

- `probe_evidence.py` lines 191–244: exact remote changes and unscoped changed-cell counts.
- `lever_attribution.py` lines 161–279: subtraction of counter, ego, ground, local target, and remote residue.
- `g4_reactions.py` lines 128–219: exact partition of attributed residue.
- `virelai_semantic/mechanics.py` lines 114 and 243–433: old action-independent partner detection and masked mechanics compilation.
- `virelai_controller.py` lines 421–609: older autonomous-cell observations and AUTONOMY candidates.
- `virelai_experiments.py`: explicit warning that remote change does not separate lever effect from autonomy.
- `FOUNDATIONAL_ARCHETYPES_v2_2026-07-22.md` lines 62–74: environmental-force definition and subtree.

### Reuse

Start from unexplained descriptive events after certified ego, counter, and lever effects are subtracted. Group by worldline, pre-state, action class, phase, and recurrence. Preserve one-off residuals as unexplained.

### Gap and warning

The older WO-L3a text says a scheduled recurring change can certify a force, while the foundational archetype defines a force as autonomous and non-scheduled; a stable schedule belongs first to the counter audit. This must be resolved in the G5 interface. Recurrence alone is insufficient. Old action-independent heuristics used fixed observation counts and cannot be ported as authority.

## 5. REACTIVE-DRIVEN roles

### Prior art

- G4 effect channels already name affected regions and target worldlines.
- `record_relations.py` derives shared effects, per-lever relations, and couplings from recorded presses.
- `virelai_semantic/mechanics.py` groups target channels and shared controls.
- `FOUNDATIONAL_ARCHETYPES_v2_2026-07-22.md` lines 76–86 defines driven objects as the dependent side of a measured coupling and allows driven+lever relays.
- `NESTED_TAXONOMY_SPEC_v5_2026-07-22.md` makes roles set-valued and class-indexed.

### Reuse

Promote an affected object to REACTIVE-DRIVEN only through a measured incoming dependency with driver, response transformation, conditions, lag, and receipts. Use the accepted description track as the visual subject and the gate entity as the causal subject when exact joins exist.

### Gap and warning

No current gate owns this role and schema v2 rejects it. Decide whether it is a G4 consequence or a later dedicated G5/G6 product. A changed object is not automatically driven, and a driven object may also be a lever.

## 6. Scoped negatives, coverage certificates, and INERT

### Prior art

- G1 coverage certificates in `virelai_gates.py` lines 830–936.
- G3 scoped-null policy and bounded coverage around lines 4331–4907; the code explicitly states that a scoped null never proves inertness.
- `g3_inheritance.py`: inheritance of a fully null G1 experiment into a scoped later question.
- `virelai_golden/render/coverage.py`: historical TOUCHED / NOT REACHED / NEVER ATTEMPTED / UNREACHABLE vocabulary.
- `g4_limits.py`: explicit tested-state and bounded-limit records.
- `FOUNDATIONAL_ARCHETYPES_v2_2026-07-22.md` lines 88–99: INERT requires coverage-bounded silence, is exclusive, and is reopenable.

### Reuse

Define a negative as subject, action or intervention class, exact board or state signature, conditions, level/life interval, result, and receipts. Build certificates from the union of scoped negatives only when the declared experiment set is complete. Record reopen triggers.

### Gap and warning

Coverage exists in several gate-specific forms but has no unified schema or completeness calculus. A G3 null, unreachable row, quiet object, or static worldline cannot independently certify INERT. Never confuse permanent unreachability with tested inertness.

## 7. Band 1 and transient animation

### Prior art

- `virelai_golden/roles/infer.py` lines 41–123: historical STATIC/REACTIVE read.
- `NESTED_TAXONOMY_SPEC_v5_2026-07-22.md` lines 22–58: parent tag, class revocation, and transient animation law.
- Accepted continuity tracks and descriptive events supply the actual sightings.

### Reuse

Derive Band 1 from settled outcomes in the canonical event ledger. Store transient excursions separately. Recompute on class change.

### Gap and warning

The golden detector's two-step rule is prior art, not accepted certification. The design needs an explicit settled-frame definition that works with flashes, overlays, resets, and incomplete observation windows.

## 8. World manifest, report, and explained share

### Prior art

- `world_model_v2.py`: deterministic canonical bytes, content hashes, validation, and atomic writer.
- `library_census.py`: ACCOUNTED status, record reconciliation, and per-level gaps.
- `tools/render_semantic_library.py` and `render_physics_grammar.py`: older human layouts.
- `tools/report_ring9_public25_library_v1.py`: untracked but exercised public-25 aggregation for roles, gaps, handoffs, and errors.
- `tools/package_ring9_public25_library_v1.py`: untracked public-25 diagnostic wrapper and collection contract.
- `viewer/data.py`: cached run-artifact loading for interactive inspection.

### Reuse

Render the manifest and `world_report.md` only from validated canonical models. Define explained share over descriptive events or recurring transformation groups, with numerator references to accepted explanatory products and denominator stated explicitly. Keep active, observed-never-acted, cancelled, and failed runs separate.

### Gap and warning

The current public-25 report and packager are untracked and based on `db8a657`. Review them as evidence and port them only after schema v3. Do not count a role label or fluent prose as an explanation. Do not let the report add conclusions absent from JSON.

## 9. Library-guided fallback and SUB-4 recovery

### Prior art

- `play_gate.py` lines 85–244: current FREE_PLAY contract, no-op guard, receipts, and bounded view.
- `solver.py` lines 685–705: rest after a controlled stop before PLAY-NORMAL.
- `tool_agent.py` lines 3073–3636: controlled-stop detection and reporting.
- `tests/test_sub3_free_play_outcome.py`: matching free-play outcome receipts.
- Ruling 24 in `RULINGS_CONSOLIDATION_v4_2026-10-10.md`: submission-only fresh-context restart, capped at three, with reasons recorded.

### Reuse

Preserve FREE_PLAY receipts, no-op blocking, the same gate machine, and canonical library across context restart. Replace the current win-directed wording with the best actionable library gap when no gate can act.

### Gap and warning

The runtime can rest gates after a controlled stop but does not restart Duck in PLAY-NORMAL. A restart is context recovery, not a new life, level, gate, or evidence scope. Never relabel free-play evidence as gated.

## 10. Observed-win explanation and cross-level transfer

### Prior art

- `virelai_win_capsule.py`: exact actor-independent winning boundary.
- `virelai_lessons.py`: level lesson, class rewrites, object explanation, and binding to a later record.
- `carry.py`: normalized visual signatures, lever signatures, locality, and carry ledger.
- `compile_post_win_grammars.py`: recorded same-action contrasts and minimal separators.
- `physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, and their test are untracked drafts with typed expressions, three-valued evaluation, and outcome grading.

### Reuse

Keep the win capsule as the factual source. Freeze the pre-win v3 model. Translate only its existing nouns, events, and laws into a candidate win sentence. Use carry signatures as correspondence hypotheses, never identity. Grade against comparable executed failures and later-level tests.

### Gap and warning

Earlier level lessons and post-win grammars operate on colors, boxes, and regions rather than fully certified nouns. They also find recorded separators, which are candidate conditions rather than causes. The typed draft must receive its own interface review before integration.

## 11. Package, live run, and release integrity

### Prior art

- `tools/package_ring9_submission_v2.py`: committed-source export, source and package manifests, secret guard, request preflight, benchmark rewrite, exact execution receipt, and package hashes.
- `tools/package_ring9_unified_canary_v1.py`: smaller private canary with the same provenance pattern.
- `tools/kaggle_kit/`: dataset/kernel push kit and verification tests.
- `checkpoint_runtime.py`: behavior-window and deadline calculations.
- `tools/package_ring9_public25_library_v1.py`: untracked diagnostic adaptation for 25 public worlds.

### Reuse

Export with `git archive` from the accepted full commit, include source hash and schema version, verify request size, preserve artifacts on cancellation, and collect selective outputs. Prove the feature ran from its own files and events before reading score.

### Gap and warning

The current submission packager predates schema v3 and the latest local commits. Do not package from the working tree or assume remote `main` contains accepted runtime. The public-25 wrapper must be rebuilt and reviewed from the current source. A diagnostic run does not submit to the competition.

## 12. Recommended ownership sequence

1. Claude: test-runtime infrastructure.
2. Claude: descriptive schema and view using the companion prior-art map.
3. Claude: G4 dossier projection and selection; Sol reviews causal and pursuit semantics.
4. Sol diagnoses the nine G1 NAV cases; Claude implements the accepted narrow fixes.
5. Director runs the current-source public 25.
6. Assigned owners build G5 force, driven, and G6 negative products under separate interfaces.
7. Claude integrates the accepted typed grammar.
8. Assigned owner builds observed-win transfer.
9. Claude builds SUB-4; Director owns packaging, push, and submission.

Every slice starts from the accepted canonical path and names which prior-art code is algorithm source, test source, rendering source, or historical warning.

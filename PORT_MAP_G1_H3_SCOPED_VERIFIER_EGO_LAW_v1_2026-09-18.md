# G1 H3 Port Map: Scoped Verifier and EgoLaw

Date: 2026-09-18  
Status: implementation input, not a historical mandate

## Purpose

WP-H3 should begin by porting the control and evidence machinery that has already worked in
Virelai. The new work is the narrow adapter from the H2 production evidence record to those
contracts, plus the G1-specific `EgoLaw` product. This document does not import old semantic
conclusions, mechanics, or action meanings.

## Directly observed reusable material

### Scoped comparison

Source:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_controller.py`
  (`PredictionSpec`, `compare_outcome`, and `revise_rule`)
- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/test_scoped_outcome_comparison.py`

The existing comparator already provides these required behaviors:

- binds a prospective prediction to an exact action and resulting transition;
- returns `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, or `UNMATCHED`;
- keeps in-scope changed cells separate from remote changed cells;
- treats geometry and terminal boundaries as indeterminate;
- refuses to widen an unresolved `WORLDLINE` scope into the visible board;
- makes an action mismatch unmatched rather than contradictory;
- carries limitations that constrain what the verdict establishes.

The existing tests directly demonstrate that a remote effect does not contradict scoped
`UNCHANGED`, missing worldline resolution is indeterminate, geometry boundaries are
indeterminate, action mismatch is unmatched, and revisions preserve parent lineage.

### Append-only revision

Source:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_controller.py`
  (`RuleVersion` and `revise_rule`)

The revision path already leaves the parent version unchanged, adds witness evidence on support,
adds counterexample evidence on contradiction, and creates no semantic revision for unmatched or
indeterminate comparisons. This is the base for versioned `EgoLaw` records and contradiction-driven
reopening.

### Captain contracts

Sources:

- `variants/ring7/ARC3-Inference/virelai_v4/contracts/completion_predicate.py`
- `variants/ring7/ARC3-Inference/virelai_v4/contracts/prerequisite_predicate.py`
- `variants/ring7/ARC3-Inference/virelai_v4/contracts/probe_event.py`
- `variants/ring7/ARC3-Inference/virelai_v4/contracts/causal_verdict.py`
- `variants/ring7/ARC3-Inference/virelai_v4/contracts/world_delta.py`
- `variants/ring7/ARC3-Inference/virelai_v4/contracts/delta_summary.py`
- `variants/ring7/ARC3-Inference/virelai_v4/targeting/assessor.py`
- `variants/ring7/ARC3-Inference/virelai_v4/targeting/router.py`
- `variants/ring7/ARC3-Inference/virelai_v4/targeting/dispatch_registry.py`
- `variants/ring7/ARC3-Inference/virelai_v4/captain_predicates.py`

These provide the pattern for declarative prerequisites, substrate-evaluated completion,
typed evidence, assessment, routing, and reopening. H3 should reuse those control shapes without
copying the old Captain state or its domain conclusions.

## Port unchanged in behavior

1. The four comparison outcomes: `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, `UNMATCHED`.
2. Exact action and transition binding.
3. Prospective recording: the prediction must exist before the action executes.
4. Scope-limited verdicts with remote changes reported separately.
5. Boundary and unresolved-scope handling as indeterminate.
6. Append-only version lineage and immutable prior versions.
7. Support adds witness evidence; contradiction adds counterexample evidence and reopens the
   target; indeterminate evidence leaves the target unresolved.
8. Declarative prerequisite and completion predicates evaluated from stored evidence.

## Adapt to H2 production evidence

The adapter consumes the H2 `virelai-probe-outcome-v1` record from
`variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/probe_evidence.py`.

| Existing concept | H2 source | Adaptation |
|---|---|---|
| Resulting transition | `transition_id`, `probe_id` | Require both to match the prospective journal entry. |
| Executed action | `action` | Compare the canonical opaque action and any coordinate parameters exactly. |
| Visible changed cells | `changed_cells` | Use the lossless frame-derived list, never callback `board_changed`, for comparison. |
| Acted component | `target_scope`, `target_local_changes` | Resolve only the captured pre-action equal-integer component. |
| Remote effects | `remote_changes` | Preserve as independent evidence outside the acted component. |
| Geometry boundary | `shape_before`, `shape_after`, `limitations` | Return `INDETERMINATE` for predicates whose scope cannot survive the boundary. |
| Terminal boundary | `boundary_event` | Return `INDETERMINATE` unless the predicate explicitly concerns that boundary. |
| Raw evidence | frame and diff references | Store references on the comparison and law; do not replace them with summaries. |

Initial resolvable scopes are:

- `VISIBLE_OBSERVATION`;
- explicit `CELLS` captured before action;
- explicit rectangular `REGION` captured before action;
- `ACTED_COMPONENT`, resolved from H2 `target_scope` and its pre-action membership.

`WORLDLINE` remains a valid vocabulary item but must return `INDETERMINATE` until an identity
resolver supplies its pre-action cells. It must never fall back to whole-board comparison.

The predicate set was refined after the dedicated transformation-lexicon audit in
`REVIEW_H3_TRANSFORMATION_LEXICON_PIXEL_ARITHMETIC_v1_2026-09-19.md`. The substrate set is
`NO_CHANGE`, `ANY_CHANGE`, and `EXACT_CELL_DELTA`. The footprint-form set is `STILL`, `RECOLOR`,
`PURE_TRANSLATION`, `GROW`, `SHRINK`, and `DEFORM`, each requiring an exact declared subject at
both endpoints. Object-correspondence verbs are deferred. `APPEAR` and `DISAPPEAR` are not pixel
primitives and must not be implemented as raw-diff predicates.

## New code that is actually required

1. A typed prospective G1 prediction record with prediction time/state, opaque action, resolved
   pre-action scope, predicate, expected parameters, and evidence basis.
2. An adapter from `ProbeOutcome` to the existing comparison input shape.
3. Predicate evaluators for the G1 vocabulary beyond the existing changed/unchanged comparison.
4. A versioned `EgoLaw` schema with stable `law_id`, revision lineage, grounded subjects or null
   locus, opaque action laws, conditions, constraints, evidence references, demonstration,
   competing models, falsifier, and limitations.
5. G1 completion and reopen predicates wired into the current cybernetic target controller.

## Material deliberately excluded

- historical ego, counter, lever, force, goal, or action interpretations;
- action-number aliases or directional semantics not established in the current run;
- downloaded game-engine implementation details;
- fixture-only fields absent from the production H2 adapter;
- retrospective predictions reconstructed after seeing an outcome;
- silent scope widening when identity or geometry is unresolved;
- the full V4 Captain state machine where the smaller current target controller already supplies
  the required gate lifecycle.

## H3 implementation order

1. Port the comparison outcome and immutable revision contracts with provenance comments.
2. Add the H2 evidence adapter and fail loudly on missing frames, broken probe/event joins, stale
   state, or action mismatch.
3. Implement and test the smallest predicates first: `NO_CHANGE`, `ANY_CHANGE`, and
   `EXACT_CELL_DELTA`.
4. Port the total cell-transition view and exact footprint arithmetic, then add `STILL`,
   `RECOLOR`, `PURE_TRANSLATION`, `GROW`, `SHRINK`, and `DEFORM` over production-shaped frames.
   Keep `BIRTH`, `DEATH`, `SPLIT`, `MERGE`, and `AMBIGUOUS` deferred to correspondence.
5. Add prospective journal enforcement.
6. Add `EgoLaw` creation on support, reopening on contradiction, and unresolved handling on
   indeterminate evidence.
7. Validate the WP-H3 acceptance cases locally before any Kaggle package or run is prepared.

## Evidence limits

The audit establishes that reusable control and comparison code exists and that its focused tests
exercise the listed behaviors. It does not establish that the old comparator can consume H2
records unchanged, that every richer G1 predicate is already implemented, or that any historical
world interpretation is correct. Those are the precise boundaries of the H3 adaptation.

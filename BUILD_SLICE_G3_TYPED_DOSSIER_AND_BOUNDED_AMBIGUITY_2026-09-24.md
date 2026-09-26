# Build slice — G3 typed dossier and bounded ambiguity

**Date:** 2026-09-24  
**Status:** implemented and locally replay-verified; served rehearsal pending  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## Goal

G3 must show that Duck understands the lever evidence it has actually earned, and no unresolved
target may monopolize the exhaustive object sweep. This slice strengthens two boundaries without
pulling G4 mechanism study into G3:

1. a lever dossier describes the confirmed intervention and exactly the local/remote residue left
   after counter subtraction;
2. an ambiguous target is retried only when the controller can identify a distinct admissible
   probe condition. Otherwise it advances as explicit unresolved coverage, never as inertness.

## Repository mine and observed trigger

The vc33 v3 run accepted two dossiers. `M0004` was useful, but `M0009` exposed the structural gap:

- a scalar `competing_models` value became hundreds of one-character strings;
- the intervention field was empty;
- the prose called a masked row-zero counter change a third lever effect;
- the admitted attribution actually contained 264 remote residue cells plus two separately masked
  counter cells.

Existing G1/G2 validators already supplied the correct port pattern through `_strings`, nested
prediction objects, exact evidence references, and controller-generated answer templates. The G3
lifecycle already had `AMBIGUOUS` and `BUDGET_STOPPED` states, while the live-closure plan stated
the missing rule: retry only while a discriminating probe exists, then emit an explicit bounded
result.

## Implemented dossier contract

`inference/framework/lever_dossier.py` adds a dedicated typed answer:

- `intervention` must be the exact prospectively confirmed action object;
- `effect_summary` must exactly equal the controller-generated
  `virelai-g3-effect-summary-v1` object;
- the causal scope is fixed to `NON_COUNTER_RESIDUE_ONLY`;
- counter treatment is fixed to `COUNTER_CHANGES_EXCLUDED_FROM_LEVER_CAUSALITY`;
- local, remote, and counter-masked counts and bounding boxes come from the immutable witness;
- evidence references must exactly name the original witness and its later supported confirmation;
- `competing_models`, conditions, and limitations must be lists of strings;
- each competing model must be an explanatory phrase;
- the falsifier must state a concrete later contradiction;
- when the witness included a simultaneous counter tick, the explanation must explicitly state
  that counter bookkeeping was masked or excluded. A sentence that assigns counter causality
  without the exclusion is rejected.

The answer is legal only after prospective confirmation. The controller supplies the exact action,
summary, and evidence ids in the answer template so Duck explains a fixed record rather than
reconstructing large cell lists. The checkpoint evaluator independently requires the typed schema,
causal scope, counter treatment, action object, and structured alternatives.

## Implemented ambiguity rule

For CLICK/GOD-MODE, metadata supplies one direct coordinate intervention for the frozen target. If
that attempt remains `UNRESOLVED_ATTRIBUTION` or `AMBIGUOUS_EGO_MASKED` and no boundary occurred,
repeating the same click is not a different controller-owned experiment. G3 therefore:

- records `virelai-g3-bounded-ambiguity-v1`;
- retains the entity in lifecycle state `AMBIGUOUS`;
- states the exact reason and future retry condition;
- forbids an inertness claim;
- advances to the next eligible visual object.

Boundary interruption remains retryable because reset/rebind changes the evidentiary condition.
For NAV/HYBRID, the embodied pursuit continues through its declared movement budget. A causally
unresolved pursuit that exhausts the budget becomes `BUDGET_STOPPED` with the same explicit
non-inertness rule.

After enumeration, the answer template partitions entities into:

- confirmed `lever_entities`;
- scoped `clean_null_entities`;
- explicitly `ambiguous_entities`.

If ambiguity remains, the controller accepts a `G3_BOUNDED_COVERAGE_REPORT` for audit but does not
emit a `LeverInventory`, satisfy G3, or open G4. Its next operation is
`WAIT_FOR_DISCRIMINATING_EVIDENCE`. A clean inventory still requires at least one confirmed lever.

## Validation

- full available offline suite: **330 passed**;
- lint over implementation, tests, and replay tools: **passed**;
- prior frozen vc33 counter-mask replay: **PASS**;
- new frozen v3 dossier regrade:
  `runs/replay-g3-v3-typed-dossier-v1/result.json` — **PASS**.

The dossier replay establishes:

- the exact legacy M0009 dossier is rejected for lacking a non-empty action object;
- its one-character competing-model serialization is detected;
- after repairing only its structure, the old causal prose is still rejected for failing to
  exclude counter bookkeeping;
- the corrected typed answer admits 264 remote cells and separately excludes two counter cells.

These are deterministic contract and replay results. They do not prove that a served model can
complete the new answer shape or finish the eligible vc33 roster.

## Exit and next step

This slice is complete locally. The next action is a fast OpenRouter served rehearsal on vc33 to
check prompt/tool usability, bounded continuation through the full eligible roster, typed dossier
submission, and exact final partition. If that succeeds, run the dense Qwen3.6 rehearsal. Kaggle
remains reserved for the later exact-model milestone.

## Non-goals

- G3 still does not derive the full lever reaction law; that is G4.
- A bounded ambiguity is not a clean G3 pass.
- Text checks do not claim general natural-language theorem proving; the structured causal summary
  is the authoritative semantic record.
- Historical Kaggle artifacts remain immutable.

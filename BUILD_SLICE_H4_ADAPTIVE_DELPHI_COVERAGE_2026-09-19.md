# Build slice H4: adaptive Delphi coverage

Date: 2026-09-19  
Status: locally complete; behavioral Kaggle evidence pending

## Bounded goal

Give G1 a deterministic probe policy that preserves the Captain's non-coordinate Delphi pairs
while replacing exhaustive coordinate enumeration with representative-first target classes and
evidence-driven expansion.

H4 decides what question to ask next. It does not identify the ego, assign action meanings, grade
Duck's explanation, or infer inertness from a negative intervention.

## Port basis

- Captain opening: two consecutive executions of every offered non-reset, non-coordinate action;
- Golden pointer read: resolve a selected site against the frame before the action;
- V4 investigation rankers: deterministic preference for small, rare, isolated candidates;
- Golden coverage rendering: distinguish tested, unavailable, and never-attempted members;
- existing G1 capability tokens, evidence joins, and H3 scoped verifier.

The exhaustive “click every frame-zero component” rule was deliberately not ported.

## Implemented policy

Coordinate candidates are the existing frame-zero 4-connected equal-integer components. Each
candidate retains observable metadata:

- exact member anchor, integer, cell count, and bounding box;
- shape family and size band;
- repeated or unique integer-shape fingerprint;
- border or interior position;
- large-field or feature scale;
- coarse spatial zone;
- adjacent-component and bounding-box-containment counts.

The initial target classes use the first five coarse properties. Spatial zone, adjacency, and
containment remain evidence in the candidate record rather than multiplying the opening classes.
One deterministic representative is scheduled from each class.

After the representative round:

1. a positive class with additional members receives one contrast member;
2. if two observations in one class disagree, every remaining member in that class is scheduled;
3. consistent positive classes retain their untested members as explicit unknowns;
4. uniformly negative representatives stop at an unresolved representation gap;
5. a temporarily unavailable coordinate action records a typed gap and resumes if the action
   returns;
6. new non-coordinate actions add their own consecutive pair before coverage can finish.

The coverage certificate reports observed channels, conditional disagreement, live alternatives,
class status, tested counts, unknown counts, and the rule that inertness is not permitted. Unknown
candidate details are paginated through the gate audit view so the compact GoalCard remains bounded.

## Exit criteria

| Criterion | Evidence | State |
|---|---|---|
| Consecutive non-coordinate pairs remain intact | Existing and H4 gate tests | Met locally |
| Coordinate classes are deterministic and observation-only | Repeat-construction and metadata tests | Met locally |
| Initial coverage is representative-first | Checkerboard and recorded-world audits | Met locally |
| ft09 does not queue all 65 components | Recorded ft09: 65 candidates → 8 representatives | Met by replay |
| A positive class receives a contrast | Planner test | Met locally |
| Inconsistent within-class outcomes force expansion | Three-member planted disagreement | Met locally |
| Unknown members remain explicit | Certificate counts plus paginated audit members | Met locally |
| Negative probes cannot create inertness or an `EgoLaw` | Representation-gap test and answer rejection | Met locally |
| Embodied, pointer, mixed, and conditional evidence take distinct branches | Gate-level branch tests | Met locally |
| No-visible-effect and unavailable-action cases remain unresolved | Typed stop-reason tests | Met locally |
| New actions extend coverage before closure | Dynamic action-surface test | Met locally |
| Compact model-facing view remains bounded | Existing large-coverage token-budget test | Met locally |
| Existing behavior remains intact | Full local suite: 235 passed | Met locally |
| Duck chooses and explains the correct ego in a real world | Requires the G1 behavioral checkpoint | Not yet met |

## Validation receipt

```text
44 focused H4/G1 interface tests passed
235 full local tests passed
ruff passed
py_compile passed
recorded G0-v2 coverage audit passed
```

Recorded frame-zero audit:

| World | Components | Initial classes/representatives | Largest class |
|---|---:|---:|---:|
| ft09 | 65 | 8 | 32 |
| vc33 | 11 | 8 | 2 |
| ls20 | 20 | 14 | 3 |

ls20 did not offer a coordinate action in the recorded checkpoint, so those 14 classes would not
be scheduled there. The audit classifies its visible board only to test the deterministic planner.

The machine-readable receipt is
`runs/kaggle-ring9-g0-checkpoint-v2/H4_ADAPTIVE_COVERAGE_AUDIT_2026-09-19.json`.

## Evidence boundary

H4 proves that the controller asks a bounded, adaptive sequence and exposes what it did not test.
It does not prove that the class partition is optimal, that an observed effect is an ego, or that
Duck uses H3's transformation vocabulary correctly. A reviewed behavioral trace remains necessary.

## Next dependency

H5 must grade protocol, coverage, explanation, prediction, demonstration, and correctness
separately, preserve the exact package/model/budget/world/concurrency receipt, and expose the frames
and claimed scope for human review. Only after that evaluator is locally validated should the
current G1 family be packaged for an authorized Kaggle checkpoint.

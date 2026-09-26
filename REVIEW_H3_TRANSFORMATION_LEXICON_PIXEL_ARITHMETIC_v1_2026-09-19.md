# Review: H3 Transformation Lexicon and Flipbook Arithmetic

Date: 2026-09-19  
Status: repo review and implementation recommendation; no transformation predicates built

## Question

What transformation vocabulary should the G1 scoped verifier use, and which existing arithmetic
and flipbook machinery should be ported before implementing it?

This review keeps three repositories and layers distinct:

- `/Users/stephenkaskin/Desktop/virelai-golden/` is the separate deterministic solver and its
  compiled flipbook canon. It is a port source, not the active hybrid tree.
- `duck-virelai/variants/ring7/.../virelai_v4/` is the older broad implementation family.
- `duck-virelai/variants/ring9-cybernetic-gates/` is the active fresh source family.

No downloaded game-engine implementation was inspected.

## Main finding

The repository already has a coherent transformation ladder, but the tentative H3 predicate list
collapsed several rungs. `APPEAR` and `DISAPPEAR` are not pixel-arithmetic predicates. At the
substrate, every in-bounds cell either holds its integer or changes from integer `a` to integer
`b`. Nothing becomes empty. Appearance and disappearance are later, asymmetric readings of an
object-correspondence event.

The H3 verifier should therefore preserve the ladder:

```text
adjacent grids + action
    -> total site arithmetic: HELD or CHANGED(a,b)
    -> declared footprint arithmetic
    -> correspondence-qualified form verb
    -> repeated action-conditioned mechanic
```

The verifier may test a prediction at any rung only when the prediction supplies the prerequisites
for that rung. It must never promote a raw integer rewrite directly into an object verb.

## Layer 1: total pixel arithmetic

Primary sources:

- Golden canon: `docs/canon/CANON_2_FLIPBOOK_ONTOLOGY_v1.2.md`, §1
- Golden implementation: `golden/substrate/changes.py`
- V4 implementation: `virelai_v4/library/cell_transition_view.py`
- V4 retained index: `virelai_v4/contracts/world_delta.py` and
  `virelai_v4/library/world_delta_computer.py`
- Current hybrid implementation: `inference/framework/virelai_continuity.py::pixel_arithmetic`

The atomic record is:

```text
(site, before_integer, after_integer, action)
```

It has exactly two outcomes:

- `HELD`: `before_integer == after_integer`;
- `CHANGED`: `before_integer != after_integer`, retaining the ordered pair.

The existing implementation gives us five important contracts:

1. The view is total over equal-shape adjacent grids. Held cells are positive evidence.
2. Changed cells are indexed by exact `(before, after)` pair with member coordinates retained.
3. Counts are derived from member cells; coordinates are never discarded in favor of counts.
4. Per-integer signed deltas sum to zero on a fixed-size grid. This is an accounting identity,
   not a discovered mechanic.
5. Geometry change is typed absence: site correspondence is undefined rather than guessed.

This is the correct base for all H3 predicates. H2 already records the changed half of this ledger,
but it does not expose held sites within a declared scope. That omission matters for exact
translation and footprint predicates.

### Movement versus net rewrite

Golden's `golden/substrate/flows.py` makes a useful distinction for an unordered integer pair
`{a,b}`:

- the balanced part of `a->b` and `b->a` is exchange compatible with movement;
- the surplus is net flow, meaning one integer gained cells from the other.

This arithmetic can rule out interpretations, but it does not identify an object or prove motion.
A balanced exchange is consistent with movement and with other permutations.

## Layer 2: per-frame visual objects

Primary source: Golden `golden/substrate/scan.py` and canon §2.

A visual object is the exact pair `(integer_class, cell_set)` in one frame. The existing cut is
4-connected equal-integer components. Both the canon and source label that segmentation as an
interim convention, not a derived law of the world.

Any footprint or integer change produces a new visual object at this rung. Consequently this layer
cannot itself say `MOVE`, `BIRTH`, or `DEATH`; it contains sightings that a later correspondence
procedure may connect.

For H3, an acted component may be used as a declared pre-action scope because H2 constructs it
directly from the observed grid. It must not silently become a persistent identity.

## Layer 3: footprint arithmetic and correspondence verbs

Primary sources:

- Golden canon §3–§4
- Golden `golden/weave/verbs.py`, `golden/weave/edge.py`, and `golden/weave/worldline.py`
- Current hybrid `inference/framework/virelai_continuity.py::arithmetic_signature`
- Current tests: `tests/test_continuity_shadow.py`

For an explicitly paired before and after footprint, the current hybrid already emits an exact,
figure/ground-neutral signature:

- `retained_same_value`;
- `retained_rewritten`;
- `prior_footprint_only`;
- `later_footprint_only`.

Every listed cell still carries its actual before and after integer. The terms do not imply empty
space. This is safer than older `vacated` and `claimed` names.

The form lexicon is:

| Form | Required relation |
|---|---|
| `STILL` | identical footprint and identical integer class |
| `RECOLOR` | identical footprint and changed integer class |
| `MOVE` | same normalized footprint under one nonzero pure translation |
| `GROW` | prior footprint is a strict subset of later footprint |
| `SHRINK` | later footprint is a strict subset of prior footprint |
| `DEFORM` | a declared continuation that fits none of the above |

The canon also allows a `+recolor` flag on movement, growth, shrinkage, or deformation when the
class changes at the same time. The older anchor-first matcher does not fully realize this combined
case, so H3 should treat the form and recolor flag as separate fields.

`MOVE` must use exact translated cell sets. Centroid displacement is a useful measurement for
attention, but it does not prove rigid translation. V4's `operation_measurer.py` uses centroid and
tolerance fences to cluster multi-integer movers; that implementation should be mined, not used as
the truth predicate.

### Correspondence vocabulary

The object-correspondence layer additionally contains:

- `BIRTH`: no predecessor to one successor;
- `DEATH`: one predecessor to no successor;
- `SPLIT`: one predecessor to several successors;
- `MERGE`: several predecessors to one successor;
- `AMBIGUOUS`: correspondence cannot be resolved.

The canon explicitly says `DEATH` is not a substrate primitive. A disappearing object's cells took
other integer values, which are growth for other participants. `BIRTH` and `DEATH` are asymmetric
worldline readings of a two-sided pixel event.

The repository also records an unresolved architecture question: Golden's shipped matcher is
anchor-first, while the canon's vocabulary is cardinality-first. H3 must not settle this open
correspondence question accidentally. A single prospective G1 demonstration can avoid it by
requiring Duck to declare the subject's before footprint and exact predicted after footprint.

## Layer 4: mechanics across multiple transitions

Primary sources:

- V4 `weave/mechanism_classify.py`
- Current `inference/framework/virelai_semantic/typing.py`
- Current `inference/framework/virelai_semantic/joint_transform.py`
- Current `tests/test_joint_transform.py`

These files provide a second vocabulary that should remain above one-edge form:

- exact recurrence: `TOGGLE` and `CYCLE`;
- directional count change and saturation;
- repeated uniform transform;
- deterministic observed state-transition table;
- coordinated class permutation;
- fixed or repeated class substitution/rewrite;
- action-indexed joint delta and conserved transfer.

These are mechanic types learned from repeated transitions. They should not be implemented as
single-demonstration H3 predicates. A G1 demonstration may test one edge predicted by such a
candidate law; the law's recurrence or conservation status comes from the accumulated series.

## Animation is a separate axis

V4 `perception/animation.py` distinguishes settled change from interior-layer behavior:

- `SILENT`: no interior or settled change;
- `FLASH`: interior excursion that settles back;
- `EFFECTIVE`: settled endpoint changed.

H2 currently compares settled before and after frames. It cannot verify `FLASH`. A future
animation predicate requires captured interior layers and must not infer silence from equal settled
endpoints alone when animation frames were unavailable.

## Recommended H3 predicate vocabulary

### Keep as substrate predicates

- `NO_CHANGE`
- `ANY_CHANGE`
- `EXACT_CELL_DELTA`

### Add over a declared before and after footprint

- `STILL`
- `RECOLOR`
- `PURE_TRANSLATION` rather than the looser name `TRANSLATION`
- `GROW`
- `SHRINK`
- `DEFORM`

Each form predicate should also carry an independent `recolor: true|false` expectation where
applicable.

### Defer from the G1 one-edge verifier

- replace planned `APPEAR` and `DISAPPEAR` with correspondence-layer `BIRTH` and `DEATH` only when
  an admitted correspondence resolver exists;
- keep `SPLIT`, `MERGE`, and `AMBIGUOUS` in that same correspondence layer;
- keep `TOGGLE`, `CYCLE`, `SATURATED`, permutation, substitution, and conserved transfer in the
  multi-transition mechanic layer;
- keep `FLASH` in the animation layer.

## Required evidence contract for the next H3 slice

The lossless changed-cell diff alone is insufficient for all form predicates. A translation can
have held interior cells and overlapping before/after footprints; those held sites do not appear in
the changed list. The next slice should port the total grid-backed transition view or compile an
equivalent bounded scope snapshot before compaction.

For one prospective subject, record before action:

```text
scope kind
exact before footprint
integer at every before-footprint site
predicted after footprint or displacement
predicted form
predicted recolor flag and destination integer when applicable
```

After action, resolve and retain:

```text
exact after footprint when resolvable
total site transitions over the union of before and after footprints
retained / prior-only / later-only membership groups
remote changes outside the union
geometry and correspondence limitations
```

This can be compiled from the real H2 before/after frames inside the production bridge and stored
as a bounded evidence object. It should not depend on fields available only in tests.

## Port decisions

### Port

- total `site -> (before, after)` view from V4/Golden;
- changed cells grouped by exact rewrite with coordinates retained;
- signed per-integer delta and conservation check;
- exact normalization and translation test from Golden/current continuity;
- current hybrid footprint arithmetic groups and neutral names;
- honest `DEFORM`/`AMBIGUOUS` outcomes and geometry-change abstention;
- tests proving exact move, recolor, grow, shrink, ambiguous correspondence, and no silent
  identity widening.

### Adapt

- the Golden/V4 verb lexicon into prospective predicates over a Duck-declared subject;
- the independent recolor co-flag, which is broader than the shipped anchor-first matcher;
- H2 to retain bounded held-site evidence for the declared scope;
- mechanism classifiers for later accumulated-law assessment, preserving action-indexed series.

### Mine only

- centroid/vector clustering from V4 `operation_measurer.py`;
- background-relative foreground gain/loss from `measure_shape_change`;
- heuristic rejoin and overlap thresholds.

### Do not port

- `APPEAR`/`DISAPPEAR` as raw cell predicates;
- elected background semantics;
- region IDs as temporal identity;
- a forced choice when multiple correspondences are licensed;
- a count-only representation that drops member cells;
- mechanic labels from one transition;
- settled-frame silence as proof that no transient animation occurred.

## What the evidence supports

The repo directly supports a total pixel ledger, exact footprint arithmetic, a tested form lexicon,
typed residuals, and several repeated-mechanic classifiers. It also directly records that
segmentation and correspondence remain fallible conventions and that the anchor-first versus
cardinality-first procedure is unresolved.

The evidence does not support treating `APPEAR` or `DISAPPEAR` as primitive, treating a balanced
rewrite as proof of motion, using centroid displacement as exact translation, or claiming that any
one continuity implementation is universally correct. The next implementation should preserve
those boundaries.

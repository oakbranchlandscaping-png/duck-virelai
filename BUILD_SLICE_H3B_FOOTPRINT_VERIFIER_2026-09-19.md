# Build slice H3b: footprint transformation verifier

Date: 2026-09-19  
Status: locally complete; behavioral Kaggle evidence pending

## Bounded goal

Give G1 a machine-checkable vocabulary for describing how one prospectively declared visual
subject changes across one action. The subject convention for this slice is explicit: one exact
4-connected equal-integer component before the action and one predicted exact component after it.

This slice does not discover the subject, resolve general worldline correspondence, infer repeated
mechanics, or establish that Duck can use the vocabulary correctly in a real game.

## Port basis

- `inference/framework/virelai_continuity.py::pixel_arithmetic` for total held/changed site
  evidence;
- `inference/framework/virelai_continuity.py::arithmetic_signature` for neutral footprint
  membership and form relations;
- Golden `weave/verbs.py` and `weave/edge.py` for the form lattice and exact translation check;
- the existing H3a prospective, scoped, four-verdict comparison and immutable `EgoLaw` path.

No historical semantic conclusion or action meaning was ported.

## Implemented contract

The production probe outcome now contains an internal total site ledger on equal-shape frames.
Every coordinate retains its exact before integer, after integer, and `HELD` or `CHANGED` status.
Geometry change produces typed absence. The compact Duck view omits the ledger but reports its
coverage and omitted site count; full frames remain content-addressed in the existing archive.

The prospective form predicates are:

- `STILL`
- `RECOLOR`
- `PURE_TRANSLATION`
- `GROW`
- `SHRINK`
- `DEFORM`

Each requires exact before and after footprints, source and destination integers, and an explicit
recolor boolean. `PURE_TRANSLATION` additionally requires the exact displacement. Recolor is
checked independently for movement, growth, shrinkage, and deformation.

The verifier:

- checks that the before footprint is exactly the declared component;
- resolves the predicted after component from the captured after frame;
- checks the exact footprint relation rather than centroid motion;
- includes the union of before and after footprints in the subject scope;
- reports outside-union changes separately;
- abstains when the pre-action subject or total site evidence cannot be resolved;
- contradicts exact after-footprint mismatches without guessing an alternative correspondence;
- exposes observed form, recolor, displacement, and endpoint footprints in the compact gate verdict.

## Exit criteria

| Criterion | Evidence | State |
|---|---|---|
| Total equal-geometry site view retains held and changed cells | Unit test includes an overlapping translation with two held interior sites | Met locally |
| Geometry change is typed absence | Evidence compiler and verifier tests | Met locally |
| All six form predicates have exact contracts | Parameterized verifier cases | Met locally |
| Pure translation requires exact translated cell sets and displacement | Overlapping translation support plus inconsistent declaration rejection | Met locally |
| Recolor remains independent of geometric form | Recolor-only and grow-plus-recolor cases | Met locally |
| Remote changes cannot decide the subject-local form verdict | Translation case with a planted outside-union rewrite | Met locally |
| Extra or missing footprint cells cannot pass | Exact after-component contradiction case | Met locally |
| Unresolved pre-action subject does not widen scope | Indeterminate component case | Met locally |
| The vocabulary works through the real G1 state machine | Answer → frozen prediction → outcome → verdict → versioned `EgoLaw` test | Met locally |
| Existing behavior remains intact | Full local suite: 227 passed | Met locally |
| Real recorded 64×64 frames compile the total view | ft09, vc33, and ls20 G0-v2 artifact replay: 4,096 sites each | Met by replay |
| Duck uses the vocabulary to identify and explain a real ego | Requires a future behavioral checkpoint | Not yet met |

## Validation receipt

```text
76 focused H2/H3/G1/continuity tests passed
227 full local tests passed
ruff passed
py_compile passed
recorded G0-v2 replay passed for ft09, vc33, and ls20
```

The full suite used both local source roots, including the vendored `taaf` package. The warnings
were third-party matplotlib/pyparsing deprecations.

## Evidence boundary

This slice proves that a correctly declared form prediction can be evaluated from production
frames and can drive the G1 closure machinery. It does not prove that Duck chooses the correct
subject, predicts the correct form, or understands an ego in a live ARC world. Those claims require
H4 coverage and a reviewed behavioral run.

## Next dependency

H4 adaptive Delphi coverage must now decide which probes discriminate embodied, pointer-like,
remote/god-mode, mixed, conditional, no-visible-effect, and representation-gap alternatives. It
may rely on this verifier for exact demonstrations, but it may not equate a failed activation with
inertness or force every world through the equal-integer component representation.

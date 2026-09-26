# Build slice: G1 closure reliability

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **LIVE CONFIRMED ON ONE LOCAL `ls20` PILOT**

## Gate question

Can Duck convert a correct evidence-based ego explanation into an accepted prospective
demonstration and a complete `EgoLaw`, without the answer interface becoming a formatting puzzle?

This slice does not grade a level win, counter lock, or lever discovery. Its behavioral exit is:

```text
G0 closes
→ paired G1 probes complete
→ explanatory G1 answer is accepted
→ one future ego-motion claim is demonstrated
→ complete ego footprint becomes an EgoLaw
→ G2 opens and binds its first ranked collision target
```

## Live failure that motivated the slice

The completed `ls20` reliability run established that Duck correctly inferred the two-color
embodied ego and the four five-cell cardinal action laws. G1 still failed because:

- the displayed contract omitted the exact accepted JSON shapes;
- Duck supplied reasonable structured subjects and action-law lists that the bridge rejected;
- `scope.representation` appeared as a flat label although the validator required nested
  `novel_prediction.scope`;
- the form verifier required raw integer ids that Duck's production view deliberately hides;
- rejection responses placed a full gate view before the error, so the output cap hid the reason;
- the notebook counted model/setup startup against the solver's promised runtime;
- the offline evaluators did not recognize the frozen reliability receipt's v2 schema name.

These are infrastructure failures. They do not negate the trace's correct ego diagnosis, and they
do not constitute a G1 pass.

## Implemented repair

### Model-facing answer contract

The G1 gate now supplies an exact nested `answer_template`, including current evidence ids and
opaque action keys. `evidence_refs` is explicitly required. The template tells Duck which geometry
must be replaced while preserving the object/list shapes.

Harmless equivalent forms are normalized:

- `subjects` may contain explanatory strings or structured objects;
- `action_laws` may be an opaque-action mapping or a list of action/law objects;
- a flat `scope.representation` plus `scope.cells` is converted to the canonical nested scope;
- prediction actions may use the opaque action string or action object;
- displacement may be `[dr, dc]` or `{row, col}`.

The controller still refuses missing evidence, unknown opaque actions, unsupported predicates,
unexplained mechanisms, malformed geometry, and non-prospective demonstrations. Normalization
removes representational friction; it does not manufacture a scientific claim.

### Complete multi-color ego proof

G1 now supports `PATTERN_TRANSLATION`, porting the repo's joint-transformation principle into the
prospective verifier. Duck declares the complete before footprint, predicted after footprint, and
displacement. The controller uses the lossless total site ledger to verify that the exact
multi-integer arrangement reappears at the translated footprint.

This matters for `ls20`: its ego is a two-color composite. Proving one equal-integer component
would give G2 a partial, incorrect ego mask. `PATTERN_TRANSLATION` verifies the full body without
asking Duck for hidden numeric color ids. Simultaneous remote changes remain separate in the
comparison and do not reverse the scoped ego verdict.

### Visible rejection and compact acceptance

A rejected `gate_answer` now returns, in display order:

1. the exact error;
2. a one-step correction instruction;
3. gate id, status, and next operation;
4. the corrective answer template.

It no longer returns the full gate view. Successful submissions return only the transition fields
needed for the next operation. The Python bridge preserves insertion order so the error survives
both output caps.

### Runtime and evaluator integrity

The checkpoint runtime can now bind a solver deadline to the measured benchmark start. If setup
leaves less than the promised benchmark allowance plus teardown tail, the notebook fails before
the behavioral run instead of silently shortening it. The future package generator writes a
`benchmark_runtime_binding.json` receipt with measured setup and deadline values.

Both G1 and G2 evaluators now accept the frozen
`virelai-g2-reliability-execution-receipt-v2` schema. Rechecking the completed run confirms that
its receipt passes; its G1 behavioral grade remains failed and G2 remains `NOT_REACHED`.

## Validation

- Full active-source suite: **286 passed**.
- Lint on all changed runtime, bridge, evaluator, and test files: **passed**.
- Future notebook rewrite and compilation: **passed** in a temporary copy; no frozen package was
  modified.
- Production-shaped structured answer test: normalized, prospectively demonstrated, and produced
  the full two-cell synthetic composite footprint while preserving a remote rewrite.
- Production bridge rejection test: the specific missing `before_footprint` error appears before
  the corrective template and within the output budget.
- Frozen v2 receipt replay: schema now passes in both evaluators; historical behavior remains
  unchanged.

## Claim boundary and next step

This slice proves that the controller and bridge can express and verify the intended G1 product.
It does not prove that the served model will use the repaired interface correctly. The OpenRouter
credential and exact `Qwen/Qwen3.6-27B` model path have been authenticated without displaying the
secret or response. The next step is a bounded local `ls20` pilot after `ARC_API_KEY` is available.
Inspect the accepted answer, demonstration comparison, `EgoLaw`, G2 handoff, and first ranked
collision decision before creating another Kaggle package.

## Live result: 2026-09-22

The bounded local run `ring9-g1-closure-local-ls20-v2` met the full behavioral exit:

- G0 closed before action;
- the ordered eight-action Delphi sequence completed;
- Duck identified the complete orange/blue composite and all four five-cell cardinal laws;
- after two visible geometry corrections, its third G1 answer was accepted;
- the frozen 25-cell `PATTERN_TRANSLATION` prediction was observed and marked `SUPPORTED`;
- G1 closed with a demonstrated `EgoLaw`;
- G2 opened with the complete post-action ego footprint and rank-1 collision target.

The active suite now passes **288 tests**, including the explicit online Arcade launch path used by
the pilot. See `REVIEW_G1_CLOSURE_LOCAL_LS20_V2_2026-09-22.md` for the evidence boundary and the G2
controller contradiction exposed after the successful handoff.

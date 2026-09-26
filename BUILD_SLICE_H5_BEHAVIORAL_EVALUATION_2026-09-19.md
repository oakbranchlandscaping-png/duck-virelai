# Build slice H5: behavioral evaluation and telemetry

Date: 2026-09-19  
Status: locally complete. A cancelled vc33 G1 v2 trace supplied diagnostic evidence but no answer,
demonstration, law, or gate verdict. Current G1/G2 live validation remains pending in queued
notebook version 2; see `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`.

## Bounded goal

Make G1 evaluation distinguish a well-formed trace from a correct explanation. H5 grades the
checkpoint against its own target and preserves the exact conditions under which the trace was
produced.

H5 does not improve Duck's ego explanation, infer semantics from a schema, or authorize a Kaggle
upload or run.

## Port basis and repaired failure modes

The existing checkpoint evaluator already joined answers, probes, events, and later reuse. H5
keeps that artifact-oriented structure and corrects four problems:

1. one aggregate Boolean hid which epistemic obligation failed;
2. populated answer fields could be mistaken for semantic correctness;
3. later reuse was incorrectly required to close G1 even though reuse belongs to a later gate;
4. package, manifest, model, budgets, world set, passes, and concurrency were not bound to the
   evaluation.

The production controller already computed adaptive coverage and scoped comparison objects. H5
persists those controller-produced facts into the executed journals instead of asking the offline
evaluator to reconstruct them from weaker prompt-facing summaries.

## Six independent grades

Each world receives a status and named checks for:

| Grade | What it establishes |
|---|---|
| Protocol | G0 preceded G1; opaque actions; unique exact probe/event/outcome joins; frame evidence exists |
| Coverage | Declaration-time H4 certificate exists; applicable pairs/classes are complete; an effect stopped coverage; unknowns were not called inert |
| Explanation | Duck names a control mode and subject, gives action laws and a mechanism, cites direct evidence, and retains an alternative and falsifier |
| Prediction | The controller journaled an action/scope/predicate claim before a later transition, with reasons for entailment and novelty |
| Demonstration | The exact prediction/probe comparison is supported and produced a versioned observed `EgoLaw` |
| Correctness | A human confirms the identity, laws, prospectivity, scope, and causal attribution against the supplied frames |

The first five are automated. A world with all five automated passes remains
`REVIEW_REQUIRED`, and the checkpoint remains failed, until the receipt-bound correctness review
passes. A failed reviewer verdict is reported as `FAIL`, not converted into a structural failure.

Later law consumption is reported separately as `OBSERVED` or `NOT_OBSERVED` with
`required_for_g1: false`.

## Persisted production evidence

Accepted G1 answers now retain:

- the declaration-time adaptive coverage certificate;
- the gate state immediately after the answer;
- the controller-normalized prospective prediction.

Every executed gate event now retains:

- the post-observation gate state;
- the current adaptive coverage certificate;
- the scoped comparison when the event is a demonstration;
- the versioned `EgoLaw` when the scoped comparison supports it.

The lossless probe outcomes and before/after frame rows remain separate authoritative artifacts.
The evaluation review packet collects the Duck answer, cited events, demonstration binding,
lossless outcomes, and raw frame rows without importing or inspecting a game-engine
implementation.

## Exact execution receipt

G1 evaluation requires `virelai-g1-execution-receipt-v1` with:

```json
{
  "schema": "virelai-g1-execution-receipt-v1",
  "package": {
    "name": "exact-package-name",
    "sha256": "<64 lowercase hex>",
    "manifest_sha256": "<64 lowercase hex>"
  },
  "model": {"id": "exact-model-id"},
  "budgets": {
    "max_environment_actions_per_world": 1,
    "max_runtime_seconds_per_world": 1,
    "context_window_tokens": 65536,
    "max_output_tokens_per_turn": "server_default",
    "tool_output_tokens": 1024
  },
  "worlds": ["exact-world-id"],
  "passes": 1,
  "concurrency": 1,
  "mode": "gated"
}
```

The output limit may be a positive integer or the literal `server_default`; the latter records
the actual unbounded client setting without pretending a numeric cap exists. Receipt worlds must
match the evaluated artifact worlds exactly. The evaluator hashes the receipt
bytes. A human review is accepted only when its
`execution_receipt_sha256` matches that hash, preventing a review from another execution from
validating the current trace.

## Human correctness contract

The review file uses `virelai-g1-human-review-v1`, one unique row per artifact world, and records
the reviewer, review time, evidence references inspected, and five explicit Boolean verdicts:

- ego identity matches frames;
- action laws match visible transitions;
- the prediction was prospective and novel;
- the declared scope matches the demonstration;
- remote or counter change was not misattributed.

Every answer-cited evidence ID and the demonstration evidence ID must appear in
`evidence_refs_reviewed`.

## Evaluator use

```text
python tools/evaluate_gated_checkpoint.py RUN_DIR \
  --stage g1 \
  --receipt execution_receipt.json \
  --human-review human_review.json \
  --review-packet-output g1_review_packet.json \
  --output g1_evaluation.json \
  --expected-game WORLD_ID
```

Before review, omit `--human-review`; the evaluator emits the packet and correctly exits failed
with the correctness grade at `REVIEW_REQUIRED`.

## Exit criteria

| Criterion | State |
|---|---|
| Six grades remain separate | Met locally |
| Automated structure cannot produce an overall G1 pass | Met locally |
| Correctness requires a receipt-bound human review | Met locally |
| Review must cover cited and demonstration evidence | Met locally |
| Exact package/model/budget/world/pass/concurrency receipt required | Met locally |
| Adaptive coverage and scoped comparison survive execution | Met locally |
| Lossless outcomes and frames are exposed for review | Met locally |
| Later reuse is visible but not a G1 requirement | Met locally |
| G0 evaluator behavior remains compatible | Met on recorded three-world G0-v2 output |
| Full regression suite | 244 passed |
| Static checks | G1-slice ruff and changed-file py_compile passed; older unrelated files retain pre-existing lint failures |
| Real Duck correctness on G1 | Pending executed checkpoint and human frame review |

## Evidence boundary

H5 proves that evaluation cannot call schema compliance semantic understanding and cannot compare
unbound executions. Synthetic fixtures prove grade behavior; they do not prove that Duck will earn
those grades in a real world.

The recorded G0-v2 artifacts still pass the upgraded G0 evaluator on ft09, vc33, and ls20. That is
a compatibility observation only. No new Kaggle package was created, uploaded, or run in H5.

## Next dependency

Freeze the current H1-H5 source into a new, manifest-verified G1 checkpoint package. The package
must include the new persistence path and evaluator, and its run configuration must be used to
create the exact execution receipt. Upload and execution remain a separate authorized operation.

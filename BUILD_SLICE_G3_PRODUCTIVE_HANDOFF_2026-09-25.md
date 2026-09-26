# Build slice: G3 productive handoff

**Type:** `BUILD_SLICE` · **Date:** 2026-09-25  
**Status:** built, offline validated, and live confirmed on vc33

## Trigger

The vc33 v7 run completed the exhaustive G3 click sweep and live-validated the compact completion
card. It then remained in G3. The three remaining targets changed only cells inside the sealed
counter mask, but the attribution layer retained them as unresolved because their pointer owner
could not be reconstructed after the action. The accepted aggregate report also remained
answer-shaped, and the displayed expansion commands did not match the runtime's keyword-only
callable signature.

## Scope

This slice turns a completed G3 sweep into a stable handoff without weakening epistemic claims.
It does not declare any object universally inert, add G4 reaction analysis, schedule new visual
objects, or infer a win.

## Built behavior

### Counter-only target outcomes

When every changed cell lies inside the locked counter mask and there is no non-counter residue,
an unresolved pointer-owner reconstruction no longer makes the target a G3 ambiguity. The result
is `COUNTER_ONLY_RESPONSE` and enters the same scoped no-lever accounting as a null response.

The claim is deliberately narrow: this tested intervention, in this recorded state, produced no
visible lever effect after bookkeeping subtraction. `inertness_claim_permitted` remains false,
and later state changes may reopen the target.

Visible residue outside the counter mask still requires resolved pointer ownership or body
contact. Ego-confounded outcomes, boundary interruptions, and genuinely unattributed residue keep
their existing ambiguity behavior.

### Terminal aggregate answer

After either a clean inventory or bounded-coverage report is accepted:

- `answer_template` is removed from the automatic card;
- another aggregate submission is rejected without changing the gate revision or product;
- Duck receives an explicit instruction to follow `next_operation` instead of correcting and
  resubmitting an already accepted answer.

For the regraded v7 evidence, G3 now emits a `LeverInventory`, reports `SATISFIED`, and returns
`WAIT_FOR_NEXT_TARGET`. The confirmed lever records remain G4-ready.

### Executable expansion handles

Every displayed G3 expansion command now matches `virelai(operation, **parameters)`:

- `virelai('inventory', offset=0, limit=10)`
- `virelai('entity', id=entity_id, offset=0, limit=128)`
- `virelai('evidence', id=evidence_id)`

The correction covers completion cards, working frontiers, confirmation summaries, inventory
rows, and evidence handles. Production-path bridge tests execute the keyword inventory, entity,
and evidence forms and inspect their Duck-visible output.

## Frozen v7 regrade

`tools/regrade_g3_v7_productive_handoff.py` replays all 12 stored G3 probes and the two stored
lever dossiers through the real active gate machine. It then submits a clean aggregate inventory
from the regraded lifecycle partition.

Result:

- probes 8, 9, and 10: `COUNTER_ONLY_RESPONSE`;
- confirmed levers: 2;
- scoped null/no-lever responses: 8;
- bounded unknowns: 0;
- counter role exclusions: 1;
- completion: `CLEAN_INVENTORY`;
- gate status: `SATISFIED`;
- next operation: `WAIT_FOR_NEXT_TARGET`;
- duplicate answer rejected without revision change;
- all displayed completion expansion handles have executable keyword shape.

The machine-readable result is
`runs/replay-g3-v7-productive-handoff-v1/result.json`.

## Validation

- 40 focused G3 scheduler, Duck bridge, and checkpoint tests pass.
- 11 focused attribution tests pass.
- 337 offline tests pass with the two explicitly online/native suites excluded.
- Lint passes on all changed production, test, and regrade files.

## Exit criterion

One focused vc33 live rung must reproduce the same complete sweep, accept one aggregate inventory,
show G3 as satisfied, and stop requesting G3 answers. Because G4 is not implemented yet, a clean
`WAIT_FOR_NEXT_TARGET` is the expected live endpoint. The following build opens G4 and studies the
two confirmed lever reaction subtrees in depth.

## Live confirmation

The focused vc33 v8 run completed on 2026-09-25 and passed this exit criterion. It emitted one
accepted `LEVER_INVENTORY`, partitioned the eligible frontier into two confirmed levers and eight
scoped no-lever responses with zero bounded unknowns, reported `SATISFIED`, and returned
`WAIT_FOR_NEXT_TARGET`. The stored answer ledger contains no duplicate accepted aggregate.

The run also exposed the next boundary cleanly: after G3 closure, the older passive agenda still
advertised open questions and drew Duck into non-binding follow-up attempts. G4 is not implemented,
so there was no valid next target to execute. See
`variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260925_043120_ring9-g3-vc33-openrouter-fast-rung-20260925-v8/REVIEW.md`.

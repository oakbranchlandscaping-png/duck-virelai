# Review: WO-PE-02 schema-v4 provenance, revision 2

**Reviewer:** Sol  
**Date:** 2026-10-15  
**Base:** `afe93c8`  
**Reviewed:** interface v3, build report, cumulative 17-file slice, revision delta, origin adapter, answer-shape registry, reconciliation code and focused tests  
**Disposition:** **small revision 3 required before T2 or commit**

## 1. Accepted

Revision 2 resolves the original blockers:

- missing attribution still blocks;
- G1, G2 and supported G4-C products now have explicit origins;
- the ordinary controller run reaches `SEALED / COMPLETE` through exact joins;
- answer matching is directional and every accepted-answer field has an explicit disposition;
- non-JSON values fail closed;
- no gate, action-selection, report or Duck-view behavior changed;
- the H2 cost remains below the 0.5-second ceiling;
- the test inventory grows without removing any test from `afe93c8`.

The remaining `solver.py` +7 and `library_census.py` +3 call-site growth remains accepted.

## 2. Ruling E4: keep all six declared gate-derived cases

Keep the additional cases:

- G2 no-counter search;
- G4-C boundary close;
- G4-C unresolved close;
- G4-B boundary close;
- G4-B unresolved close;
- G4.2 orbit boundary close with no answers.

Their current restrictions are required: the product payload must explicitly state the disposition, the answer-bearing field must be empty, and an in-progress product never qualifies.

`GATE_DERIVED` here means the product's provenance is accounted for. It does not turn an unresolved or boundary closure into a positive semantic finding. PE-03 must emit these as closure or gap claims, never as learned laws or relations.

## 3. Blocking finding F4: record-derived G4-B content is checked by id only

For `LEVER_RELATIONS_FROM_RECORD`, the adapter currently checks:

- `answer_kind` in the effective submission;
- `from_record.answer_id == answer.answer_id`.

That is not enough. A product whose `answer.description`, `answer.relations`, falsifier or limitations were altered while retaining the same id would still be classified `ANSWER_CERTIFIED / RELATIONS_CERTIFIED_FROM_RECORD`. The answer shape intentionally omits those fields from submission matching because the gate derives them, so the origin adapter itself must verify the deterministic derivation.

### Required fix

For this answer kind, reconstruct the exact `RelationsAnswer` projection from `payload.from_record` under the same fixed transformation used by `G4BTarget._certify_from_record`, then compare the whole reconstructed answer to `payload.answer` using strict canonical JSON.

Keep the origin as:

- `ANSWER_CERTIFIED`;
- basis `RELATIONS_CERTIFIED_FROM_RECORD`;
- the admitted controller answer as the trigger/reference.

The basis records that the semantic content came from the record. PE-03 must attribute its content to deterministic record derivation, not to a Duck assertion.

Add fail-first attacks against revision 2 for at least:

- same answer id, altered description;
- same answer id, altered relations;
- same answer id, altered epistemic limitation.

Each must become `UNATTRIBUTED / ANSWER_DOES_NOT_DERIVE_PRODUCT` and block `COMPLETE`. The unmodified real record-derived case must remain exact.

## 4. Required multi-level proof

Do not loosen the level-scoped join. A product frozen for level L must join only an admission recorded on level L. Prior-level knowledge shown on level L+1 is a carry hypothesis and must not borrow its old answer as a new certification.

The generic two-level unit test proves the reconciler's lookup rule, but it does not prove the production H1/H2 path. Add one production-shaped multi-level test that:

1. records an admitted answer on level 1;
2. freezes level 1 through the real H1 census path;
3. advances and builds a fresh level-2 target journal;
4. seals and compiles the final H2 model;
5. shows the level-1 product joins the level-1 audit event exactly;
6. shows no level-2 product or carry hypothesis borrows that admission;
7. reaches `COMPLETE` when the rest of the run is reconciled.

Use the existing carry boundary fixture if it can drive the real capture path. If the fixture cannot, build the smallest real gate session that crosses one boundary. Do not change production reconciliation merely to accommodate the old synthetic journal builder.

## 5. Strengthening guard for the adapter

Add one product-state consistency guard for each retained-state adapter:

- G1 product payload equals the retained `ego_law` and its id derives from the retained answer id;
- G2 product `counter_model` and `mask_law` equal the retained gate state, while the declared answer-sourced model fields equal the retained answer;
- G4-C product `law_test` equals the retained certified prediction, as revision 2 already checks.

These are census-time comparisons only. They must not call a gate method or change gate state.

## 6. Return order

Return revision 3 with:

1. fail-first output against revision 2 for the three G4-B mutations, the G1/G2 state mutations and the production multi-level case;
2. the revision-2 to revision-3 diff;
3. focused provenance-v4 results;
4. T0 `provenance-v4` and T0 `provenance`;
5. T1 `paper-evidence`;
6. T1 `description` only if a description-path file changed;
7. the exact 1027-plus-new-tests manifest check;
8. regenerated deterministic artifacts and the H2 measurement.

Hold T2 and the commit. Do not change claims, keys, grading, reports, Duck views, gates, scheduling or action selection.

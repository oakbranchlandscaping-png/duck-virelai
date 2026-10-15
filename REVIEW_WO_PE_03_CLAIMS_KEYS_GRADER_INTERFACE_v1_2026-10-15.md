# Review: WO-PE-03 claims, keys and grader interface v1

**Reviewer:** Sol  
**Date:** 2026-10-15  
**Base:** `e158057`  
**Disposition:** **design accepted with the rulings and amendments below; begin PE-03A only**

## 1. Assessment

The sweep finds the correct boundary. Schema v4 proves that the run and its products are accounted for, but its product receipts intentionally store hashes rather than the semantic product bodies. That is sufficient for provenance and insufficient for projecting the paper's LAW, RELATION and graded PREDICTION claims from one sealed artifact.

The formal evidence chain must remain self-contained. Limiting the claims to v4 would abandon central paper claims, and another semantic sidecar would recreate the split-writer problem PE-02 removed.

## 2. D15: adopt schema v5 with per-level product content

Adopt option **(a)**.

Schema `virelai-world-model-v5` adds a per-level product-content chapter containing each active product exactly once at the level's H1 or H2 census:

- product id;
- gate id and product type;
- revision and dependencies;
- full JSON payload;
- a strict canonical JSON SHA-256 digest.

The existing v4 receipt hash is not reused. Define a versioned digest record such as:

```json
{"algorithm":"sha256","encoding":"virelai-canonical-json-v1","value":"<64 hex>"}
```

No `default=str`, NaN or non-JSON value is permitted. A product that cannot be represented becomes a typed model gap and prevents a formal evidence packet from being complete.

The v5 validator recomputes every product digest and verifies agreement among:

- product content;
- the product receipt;
- `product_answers` origin metadata;
- the product's gate, type and revision.

Capture every active product at H1 before the target journal is rebuilt. Capture the open level at H2. Prediction histories and their graded outcomes remain inside the gate product payloads; do not invent a second prediction ledger.

V1-v4 readers stay frozen. Formal claim projection requires a sealed v5 model. It may refuse v4 with a precise `PRODUCT_CONTENT_UNAVAILABLE` reason; do not silently emit a reduced formal packet.

Do not expose the new chapter through Duck's card or change any action-selection path in PE-03A.

## 3. D16: keys use human handles plus geometry

Use **both** a readable object handle and a geometric selector. Solver ids are source references only and never key identity.

The canonical subject selector contains:

- a frame reference: level entry, a transition, or a recording frame;
- that frame's board or image hash;
- class when visually available;
- anchor, bounding box and cell count;
- the readable handle, for example `c12@63,0`.

Objects first seen after level entry use their first visible frame. A handle alone is not unique enough. The mapper proposes `EXACT`, `COMPOSITE` or `UNMATCHED`; a human confirms every non-exact mapping.

The claim's canonical subject descriptor, not `E…` or `O-…`, enters `claim_key`. Solver ids remain in `source` for traceability. This is required if the same proposition is to join across runs.

## 4. D17 and claim identity

Keep `run_stem` out of `claim_key`. Keep `game_id` and level in it.

Use full SHA-256 hex for `claim_key`, `assertion_id` and content-derived key ids. Sixteen hex characters is too short for the permanent evidence layer.

The proposition hash includes the canonical subject descriptor, family, kind, predicate, object and semantic scope. It excludes evidence, status, executor, admission, certification and source. `assertion_id` adds the exact source record.

## 5. D18: scoped nulls are CONDITION claims

Project a scoped null as:

- family `CONDITION`;
- predicate `NO_OBSERVED_EFFECT`;
- the exact action, state/transition scope and evidence;
- status `OBSERVED`;
- never the role `INERT`.

Report these separately from positive semantic findings so their volume does not obscure role and law accuracy.

## 6. D19: project every transformation pattern

Every split transformation pattern becomes a `TRANSFORMATION` observation claim, including `NOT_COVERED` patterns. Exhaustive unexplained observation is part of C2.

Mixed explanation statuses remain separate assertions. Explanation status is excluded from proposition identity but retained on the assertion, allowing the same observed proposition to move from unexplained to explained without becoming a different world fact.

## 7. D20: gap and closure grading

- A GAP or `CLOSED_WITHOUT_FINDING` assertion is graded as an **audit statement** about the model's knowledge state.
- It is `CORRECT` when the sealed model supports that state; it is never `INVENTED`.
- It does not satisfy a required factual key item.
- Therefore, when the key requires a fact that the solver left open or closed without finding, that key item is `MISSED`.
- Do not label the gap assertion `WRONG` merely because the key contains the answer. A contradictory positive factual proposition can be `WRONG`.

Keep audit and proposition totals separate in every table.

## 8. D21: paper evidence is offline only

Write `paper_evidence.json`, `paper_report.md`, verdict sheets and grade reports only through offline tools after the canonical model is sealed.

The runtime writes `world_model.json` and `world_report.md` as now. This keeps grading code and keys out of the agent, preserves the H2 budget for the canonical artifact, and ensures the model never sees the key.

## 9. D22: split the work into four reviewed slices

### PE-03A — schema v5 product content

- strict product representation and digest;
- H1/H2 capture;
- frozen v1-v4 readers;
- determinism, tamper and multi-level tests;
- size and H2 cost measurements.

### PE-03B — atomic claim projection

- pure sealed-v5 projector;
- canonical human-facing subjects;
- admitted, refused and uncertified assertions;
- product, prediction and audit claims;
- offline `paper_evidence.json` and ungraded `paper_report.md`.

### PE-03C — key schema, validator and mapping sheet

- format and validation only;
- no key items authored by the build seat;
- exact/composite/unmatched mapping proposals;
- source hashes, ancestry check and Director attestation.

The validator can verify commit ancestry and required metadata. It cannot prove that nobody opened a report; `blind_to_reports` remains an explicit Director attestation and must not be described as mechanically proven.

### PE-03D — grader and final paper report

- exact and accepted-alternative joins;
- human verdict sheet for unresolved semantic cases;
- `CORRECT`, `WRONG`, `UNVERIFIABLE`, `MISSED`, `INVENTED`;
- complete dimensional tables and non-zero exit on ungraded material.

Only PE-03A starts now. Hold B-D until A is accepted and committed.

## 10. Additional projection rules for the amended interface

- Record-derived G4-B content is `certification: RECORD_DERIVED`, `executor: SYSTEM`; the controller admission is its trigger, not its semantic author.
- `GATE_DERIVED` closures emit only audit/gap assertions.
- Controller-filled fields are never attributed to Duck.
- Generated, derived and outcome fields come from the gate/product and are attributed to SYSTEM unless a more specific deterministic controller source exists.
- A refused payload contributes only independently interpretable fields. A malformed refusal contributes one typed open-gap audit assertion rather than guessed propositions.
- Prediction propositions and prediction-result audit assertions are distinct and graded separately.

## 11. PE-03A acceptance requirements

Before any shared edit, file its shared-file note. Then return a fail-first interface and tests covering:

1. every active product is captured at H1 and H2 with its exact payload;
2. a two-level run preserves level 1 before the target journal rebuild and captures fresh level-2 products;
3. strict digest rejection of objects, sets, NaN and altered payloads;
4. receipt/content/type/gate/revision disagreement fails validation;
5. graded G4-B predictions and the G4-C law test survive byte for byte;
6. record-derived relations survive with their origin metadata;
7. v1-v4 read unchanged;
8. live and H1 views never read a sidecar and do not expose product content to Duck;
9. two compilations are byte-identical;
10. schema-v5 size and H2 cost on k008, k013, carry-v7 and the real two-level fixture.

Keep the Mac H2 ceiling at 0.5 seconds for the 800-row reference case. If exact product content exceeds it, report the measured decomposition before proposing compression; do not omit evidence to meet the ceiling.

## 12. Repository and submission

State v10 is accurate and should be committed with the accepted PE-03A documentation or in the next documentation commit. The scored competition submission remains red because no notebook, submission id or score is recorded. That does not block PE-03A, but it remains the Director's parallel P0 action.

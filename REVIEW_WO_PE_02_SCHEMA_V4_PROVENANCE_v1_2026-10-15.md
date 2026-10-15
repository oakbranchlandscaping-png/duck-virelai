# Review: WO-PE-02 schema-v4 provenance, revision 1

**Reviewer:** Sol  
**Date:** 2026-10-15  
**Base:** `afe93c8`  
**Reviewed:** interface v2, shared-file note, build report, 15-file patch, tests and representative evidence package  
**Disposition:** **revision required before T2 or commit**

## 1. What passes review

The architecture is right:

- provenance is a separate top-level chapter and the old `journal_check` meaning is preserved;
- H1 and LIVE_VIEW do no journal file reads;
- H2 reads one byte buffer after the seal and uses it for both parsing and hashing;
- validated rows are embedded once and levels carry indexes;
- integrity and semantic reconciliation are separate;
- OPEN and CORRUPT retain only the verified prefix and their typed failure;
- handled crashes can be complete through recorded termination;
- v1-v3 readers remain available;
- no per-action work was added;
- the roster detects missing models;
- the test and measurement package distinguishes synthetic measurements from evidence.

The extraction into `provenance_hooks.py` is sensible. The remaining `solver.py` +7 and `library_census.py` +3 executable-line growth is accepted. Do not move unrelated persistence or report code to erase those ten call-site lines.

E3 is accepted: answer-payload references are preserved and typed for PE-03, but only structural references required by reconciliation block provenance completeness.

S1 is accepted as a synthetic-journal limitation. Do not weaken production reconciliation to make the synthetic carry replay green.

## 2. Blocking finding F1: COMPLETE is unreachable on ordinary runs

The built rule is correct to reject an answer-certified product whose answer cannot be identified. Changing `NO_REFERENCE_BLOCKS` to false would turn missing attribution into success and is rejected.

The three cases need to be separated:

1. **G1 EgoLaw:** the gate retains `machine.ego.answer`; the law is created from that answer and its `law_id` is derived from the answer id.
2. **G2 CounterGateProduct:** the gate retains `machine.counter.answer` when a counter model is certified.
3. **G4-C LeverReactionLawSet:** a supported law retains `_certified`; the product also stores that law test. A boundary or unresolved closure can legitimately have no G4-C answer.

### Ruling

Keep missing answer attribution blocking for an answer-certified product. Revise `product_answers(machine)` so it projects the certifying gate-state answer for G1 and G2, and the certified G4-C prediction for a supported law. This is a census-time provenance adapter and does not change gate behavior.

Add an explicit product origin enum:

- `ANSWER_CERTIFIED`: requires one exact admitted answer;
- `GATE_DERIVED`: allowed only for a declared deterministic closure/product state for which no answer is expected;
- `UNATTRIBUTED`: always blocks `COMPLETE`.

The adapter must explicitly enumerate the allowed GATE_DERIVED cases. `link: NONE` is not enough. A G4-C boundary closure and a G2 no-counter search disposition may qualify when their product payload states that disposition. An ordinary EgoLaw, counter model or supported law may not.

Do not add generic answer fields to every gate product in this revision unless the adapter cannot establish a sound link. If a gate edit becomes necessary, file a second shared-file note before that edit.

## 3. Blocking finding F2: shared-field matching is too weak

`_fields_agree` currently accepts any non-empty intersection of fields. A truncated candidate can therefore pass when its few remaining fields match, even if it omits the semantic field that distinguishes two answers. This is not an exact payload join.

### Ruling

Replace intersection matching with directional normalized containment:

- **Product reference to audit answer:** every semantic field stored in the product reference must exist in the journal's effective answer and have the same strict canonical hash. At least one semantic field beyond the answer id is required unless the product identity has an independently validated derivation from that answer id.
- **Gate-answer sidecar to audit answer:** every semantic field in the normalized accepted sidecar answer must exist and match in the journal effective answer. Ignore only an explicit fixed set of bookkeeping fields.
- Any generated or intentionally omitted field must be named in the normalizer and covered by a test. Never accept “whatever fields happen to overlap.”

Add fail-first cases showing that the revision-1 matcher wrongly accepts:

- a payload containing only `answer_id`;
- a payload omitting one differing semantic field;
- two same-id answers distinguished only by a field outside the old intersection;
- a sidecar with an altered or missing semantic field.

## 4. Finding F3: canonical field hashes must not stringify arbitrary objects

`sha16` uses `json.dumps(..., default=str)`. The audit journal correctly rejects non-JSON values; the product-link path should not silently turn one into text.

### Ruling

Use strict canonical JSON for field hashes. A non-JSON product-answer value becomes a typed chapter compilation failure or an unattributed product, never a stringified match. Preserve deterministic tuple/list handling only where ordinary JSON already supports it.

## 5. Documentation correction

Add an amendment to the already-filed shared-file note stating that `provenance_hooks.py` was introduced after the first implementation to extract logic from two oversized shared files. Do not rewrite the original claim that the note preceded shared edits.

The build report should stop describing E1 as a switch among three equal options. The ruling is now: preserve the blocking rule, add sound answer-certified and gate-derived origins, and demonstrate an ordinary real run reaching COMPLETE.

## 6. Required revision tests

In addition to the existing 34 tests:

1. The real controller session reaches `SEALED / COMPLETE`, with exact G1 and G2 joins and no ignored product.
2. A supported G4-C product joins its exact admitted prediction.
3. A G4-C boundary closure is typed `GATE_DERIVED` and does not pretend an answer existed.
4. A G2 no-counter product is either a specifically allowed `GATE_DERIVED` case or blocks with a precise reason.
5. An ordinary answer-certified product with its answer removed remains incomplete.
6. All four payload-truncation/alteration attacks in §3 fail.
7. A non-JSON field cannot be hashed through `default=str`.
8. Existing ambiguous repeated-answer tests remain blocking.
9. H1 and the per-action controller path still perform no journal reads.
10. All 13 representative artifacts remain deterministic after the revision; expected semantic changes must be listed rather than claimed byte-identical to revision 1.

## 7. Return and test order

Return revision 2 with:

- amended interface v3 or a clearly marked interface-v2 amendment;
- the shared-file-note amendment;
- fail-first output against revision 1 for the new cases;
- exact revision-1 to revision-2 diff;
- regenerated artifacts and measurements;
- focused provenance-v4, T0 provenance-v4, T0 provenance, T1 description and T1 paper-evidence results;
- exact T2 manifest check.

Hold T2 and the commit. The 0.5-second H2 ceiling remains. Do not touch report rendering, Duck's view, claims, keys, grading, gate scheduling or action selection.

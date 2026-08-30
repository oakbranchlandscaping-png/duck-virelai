# Response to Review of the Ring 6.3 Engineering Build Plan

**Date:** 2026-08-30  
**Reviewed object:** `RING6.3_BUILD_PLAN.md`  
**Disposition:** accept the review's central correction and most amendments, with two
qualifications described below. No Ring 6.3 implementation has begun.

## Overall response

The review is technically grounded and its central objection is correct.

The original plan's persistent-history sanitizer should be removed. It would not merely
transport the Captain report; it would change how long Duck can continue seeing that report.
That is a semantic intervention in the model's information environment and conflicts with
Ring 6.3's one-variable discipline.

Ring 6.3 should repair fresh insertion, preserve ToolAgent's natural conversation-history
behavior, and gate success on the first outbound Duck request containing the exact report
once. Later payload occurrence counts remain diagnostics. They are not a requirement that
the naturally retained report disappear.

No clarification from the reviewer is required before revising the plan.

## Finding-by-finding disposition

### F1 — Accept

Delete the proposed persistent-history sanitizer and all tests whose purpose is to enforce
forced forgetting after Duck turn one.

The correct Ring 6.3 semantic rule is:

> Freshly insert the fixed Captain report into the first Duck analysis turn. Thereafter,
> allow normal ToolAgent history retention and context trimming to determine continued
> visibility.

This preserves the existing harness. “First turn only” describes the insertion event, not
an instruction to erase the first user message from later conversation history.

The review is also right that Duck-use grading would be confounded by forced removal. The
card should remain available for as long as any other first-turn user content naturally
remains available.

### F2 — Accept, with an implementation precision

The yielded-turn duplication path is real:

- the card-bearing first user message is persisted on yield;
- the solver resumes the same analysis step and offers the card again;
- without a guard, the next payload contains the old retained copy and a new copy.

Use the narrow containment solution, not `preserve_history = False`. Discarding all history
on yield would throw away legitimate model work and create a second semantic change.

Before freshly appending the report, inspect incoming ToolAgent history for the exact full
report. If it already exists, do not append another copy. If a request failure restored
history and the report is absent, append it again on retry.

The containment check must understand string and multimodal text blocks and use the same
pure exact-occurrence helper as the audit. It should not be an unstructured JSON substring
search.

The first outbound request is the release gate. Later first-turn or resumed payloads are
audited for zero/one/multiple copies, but natural context trimming means they cannot all be
required to retain the report indefinitely.

### F3 — Accept

The claim was verified locally. `variants/ring6.2/ARC3-Inference/inference/` contains only
five files under `agent/` and `framework/`, while the executed assembled inference tree
contains 31 files and supplies required modules such as `inference/utils/openai_compat.py`.

The Ring 6.3 source must therefore be seeded from the exact executed tree:

`kaggle/ring6.2/source-dataset/src/ARC3-Inference/`

The seed must be copied into:

`variants/ring6.3/ARC3-Inference/`

The copy must exclude caches and the duplicate directories identified under F4. The copied
tree must be hashed before Ring 6.3 edits so its provenance is explicit.

### F4 — Accept the hygiene gate; reject mutation of historical rings

The contamination is real and broader than the review listed. Empty space-suffixed duplicate
directories exist in both the Ring 6.2 overlay and executed source bundle, including:

- `contracts 2`;
- `library 2`;
- `cybernetic 2`;
- `capture 2`;
- an empty `kaggle/ring6.2/source-dataset 3`.

Ring 6.3 must exclude these while seeding and must reject `* 2`, `* 3`, `__pycache__`, and
`.pyc` contamination in both its variant and bundle.

However, Ring 6.2 is a completed historical control. We should not delete or rewrite its
source or bundle during a Ring 6.3 build. The old contamination should be documented and
left intact unless the Director separately authorizes historical cleanup. The correct action
for this ring is clean inheritance, not retroactive mutation.

### F5 — Accept

Every actual network post must emit its own guarded `prepared` event after
`build_chat_payload()`. A context-length rejection followed by re-trimming creates a new
payload and a new post; it must receive a new request id and a new attachment check.

The first report-bearing request may fail at the server. `REPORT_REQUEST_ACCEPTED` can only
refer to a later request if that exact later payload was independently inspected and also
contained the report.

Add an explicit mocked context-overflow test that captures both posted payloads.

### F6 — Accept the concern; keep one authoritative boundary

Ring 6.2's `save_request_logs` was verified false in the packaged preamble, runtime log, and
serialized solver, and the downloaded output contains no request JSONL files. It cannot
provide a second retroactive 0/25 confirmation.

The existing `_append_request_snapshot` captures deep-copied, post-trim messages before the
provider payload is built. It is useful but does not meet Ring 6.3's proof boundary.

Ring 6.3 will keep the focused post-`build_chat_payload` handoff audit as authoritative. The
existing optional request log remains unchanged and secondary. The evaluation must say this
explicitly so the two artifacts cannot be treated as competing sources:

1. `handoff_audit/` and the saved first provider payload: authoritative for exact attachment;
2. transcripts: authoritative for human-readable conversation and behavior;
3. optional request snapshots: supporting diagnostics only;
4. overwritten `prompts/*.log`: latest-call convenience only.

This resolves the duplicate-truth concern without enabling a large, redundant all-request
log for the canary.

### F7 — Accept

Add regression tests proving that level advance, level descent, `GAME_OVER`, and automatic
reset do not reset `analysis_step` or freshly insert the fixed report again.

The report may remain visible through normal retained history. The invariant being tested is
no new insertion, not zero exact occurrences in the whole later payload.

### F8 — Accept

Fallback reports remain in the transport denominator. Transport must work even when the
Captain faults or rendering falls back.

Fallback games are tagged and reported separately. They are excluded from aggregate Layer B
claims about the usefulness of substantive Captain evidence, because an honest unavailable
report contains no world model to evaluate.

### F9 — Accept

Use fully prefixed runtime names consistently. Document the mapping:

- Ring 6.2 `RING6_CARD_INJECTED`: retired; intent only, never attachment proof;
- Ring 6.3 `RING6_REPORT_RENDERED`;
- `RING6_REPORT_PERSISTED`;
- `RING6_REPORT_ATTACHED`;
- `RING6_REPORT_REQUEST_ACCEPTED`;
- existing `RING6_DUCK_FIRST_ACTION`.

### F10 — Accept

Add a byte-for-byte/verbatim prompt assertion. The exact report string fingerprinted by the
solver must occur contiguously and unchanged in the final text block used to build the
provider payload.

### F11 — Accept

Request ids are audit metadata only. They must never be inserted into the provider payload or
model-visible text. Correlation is maintained by guarded call-local metadata and audit
records.

### F12 — Accept

The Ring 6.2 download confirms that arbitrary job-root directories such as `artifacts/`,
`prompts/`, `transcripts/`, and `solver_analysis/` survive Kaggle output collection.

Place `captain_reports/`, `handoff_requests/`, and `handoff_audit/` under that same job root.
Add a local bundle/run-path test before launch rather than leaving artifact survival as a
post-run question.

### F13 — Accept as a caution, not an assumption

Keep per-game filenames and atomic writes. Do not assume sequential execution merely from
wall-clock duration: the packaged solver declares concurrency 28 even if model serving or
game duration reduces effective parallelism.

## Revised Ring 6.3 scope

With the review incorporated, the implementation scope becomes:

1. Seed a complete, clean Ring 6.3 source from the executed Ring 6.2 bundle.
2. Move report insertion out of the global `action_num == 0` gate.
3. Prevent fresh duplication when a yielded first-turn history already contains the exact
   report.
4. Preserve natural ToolAgent history; do not sanitize or erase the report.
5. Retire the false `CARD_INJECTED` success marker.
6. Fingerprint and persist the exact report.
7. Inspect and save the provider payload after `build_chat_payload()` and before every post.
8. Correlate a verified payload with a successfully parsed endpoint response.
9. Add retry, context-overflow, boundary, fallback, provenance, and hygiene tests.
10. Keep all Captain strategy, card wording, ontology, Duck model, and ledger behavior fixed.

## Revised acceptance statement

Ring 6.3 passes when every handoff-eligible game proves:

- an exact report was rendered and saved;
- the first outbound Duck provider payload contained that report exactly once;
- an endpoint returned a valid response to a verified report-bearing payload;
- nonzero Captain action count did not prevent delivery;
- no audit or attachment failure occurred;
- Duck remained able to act.

Later payloads are audited for duplication and retention behavior, but natural history and
context trimming are not overridden. A later payload may contain one retained copy or zero
copies after trimming; it must not contain multiple exact copies caused by fresh reinsertion.

## Conclusion

The review improves the plan materially. Its main correction prevents Ring 6.3 from changing
Duck's memory while claiming to test only transport. The remaining amendments strengthen
provenance, retry coverage, artifact authority, boundary invariants, and fallback accounting.

The two qualifications are deliberate:

1. do not mutate completed Ring 6.2 historical material while cleaning Ring 6.3 inheritance;
2. keep the post-provider handoff audit authoritative rather than conflating it with the
   existing disabled pre-provider request snapshot.

Subject to those qualifications, the review is accepted and the plan should be revised
before execution.

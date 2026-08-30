# Ring 6.3 canary contract

Ring 6.3 answers one question:

> Does the first endpoint-accepted Duck request contain the exact Captain
> report once, even after the Captain has taken nonzero game actions?

## Frozen behavior

Captain policy, budgets, action bridge, ontology, field-card wording, Duck
model/settings, and the separate Duck ledger are unchanged from Ring 6.2.
Natural ToolAgent history retention is unchanged: the report is freshly
inserted on analysis step 1 and may remain visible later through normal history.

## Required sequence

Every handoff-eligible game must emit:

1. `RING6_PROBE_START`
2. `RING6_PROBE_END`
3. `RING6_REPORT_RENDERED`
4. `RING6_REPORT_PERSISTED`
5. `RING6_REPORT_ATTACHED`
6. `RING6_REPORT_REQUEST_ACCEPTED`
7. `RING6_DUCK_FIRST_ACTION`

`RING6_CARD_INJECTED` is retired. It measured intent before prompt
construction and is not attachment evidence.

## Exact evidence

- `captain_reports/<run_stem>.txt`: exact report, no wrapper or added newline.
- `handoff_requests/<run_stem>.json`: first verified provider payload.
- `handoff_audit/<run_stem>.jsonl`: prepared/completed/failed request records.
- `transcripts/<run_stem>.txt`: human-readable prompt, response, tools, actions.

The report SHA-256, character count, UTF-8 byte count, and request id must join
the artifacts and markers. The first provider payload must have one exact user
copy. A parsed endpoint response must carry the same request id.

## Retry rules

- A request failure with restored history may freshly offer the report again.
- A yielded step whose retained user history already contains the exact report
  must not append a second copy.
- Each actual post, including a context-overflow retry, is independently
  inspected after provider payload construction.
- Later retained visibility is diagnostic; no forced history sanitization is
  permitted.

## Denominators

- Complete Captain game wins emit `RING6_HANDOFF_NOT_REQUIRED` and leave the
  handoff denominator.
- Captain-fault/fallback reports remain in the transport denominator but are
  separated from substantive-card Duck-use grading.

## Pass condition

All handoff-eligible games satisfy the exact transport sequence with no
`REPORT_ATTACH_FAILED`, `REPORT_PERSIST_FAILED`, or `REPORT_AUDIT_FAULT`.
Score is secondary. Ring 6.3 proves transport, not semantic understanding.

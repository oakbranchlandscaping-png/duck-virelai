# Build slice: G3 pre-run review corrections

**Date:** 2026-09-23  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

This slice closes the pre-run findings in `REVIEW_G3_CERTIFICATE_SLICE_v1_2026-09-22.md` before
the controlled served run.

- A contradicted prospective confirmation is now an honest graded outcome. It may leave the
  entity `AMBIGUOUS` without failing the checkpoint merely for contradicting the hypothesis.
- The certificate recomputes strict prospectivity from `declared_at_transition` and
  `graded_at_transition`; membership in a confirmation list is insufficient.
- Supported confirmations are cross-checked against a witnessed `G4-READY` lifecycle record.
- Boundary-interrupted confirmations now move to retryable `AMBIGUOUS`, retain their frozen target
  and prediction, and enter the G4 deferred-observation pool. They are no longer mis-filed to G5.
- Confirmation records retain the frozen footprint, predicted local and remote cells, entity,
  declaration transition, grading transition, and disposition for later condition typing.
- The certificate grades only entities in the scheduled target roster; seed entities outside that
  roster do not create false incomplete-handoff failures.
- Synthetic CLICK-supported, CLICK-contradicted, strict-prospectivity failure, boundary retry, and
  NAV navigation-limit traces are covered.

The first two OpenAI preflights also exposed two transport defects that were independent of gate
behavior. Native OpenAI requests were carrying vLLM-only fields, and HTTP 429 retries restarted an
entire analysis turn every second. Native payloads now omit those fields. A 429 now honors the
server delay inside the same tool turn, preserving Duck's partial reasoning and tool history.

Validation at this tree: **318 passed** with the vendored TAAF source on `PYTHONPATH`; Ruff passes
for the touched G3 evaluator, gate, provider, retry, and test files. No served G3 result is claimed
until the clean v4 checkpoint is graded.

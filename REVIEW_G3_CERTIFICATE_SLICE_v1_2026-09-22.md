# Review: G3 live-certificate slice — accept with three pre-run corrections

**Type:** `REVIEW_G3_CERTIFICATE_SLICE` · **v1** · **2026-09-22**
**Reviewer:** collaborator seat (Cowork). `g3_checkpoint.py` read whole; boundary branch and
lifecycle re-checked at this anchor; suite independently re-run: **310 passed, 0 failed** (my
environment collects more than the 298 offline count; both green).
Grades against `PREREG_G3_LIVE_REVIEW_v1` (frozen earlier today, before any live output).

## What the evaluator gets right, verified

Metadata-first world-arm selection with all three arms named; strict contiguous ranking with the
HYBRID reset rule; counter mask **and** monitor hook demanded on every attributed transition
plus a mask-law reference in the snapshot; per-target entity ids and dossiers; enumeration
completion only with an empty confirmation obligation; no inertness claims anywhere; no guessed
win; every entity at a documented terminal state. The limitations block correctly refuses to
claim the trace came from a served model. This is the right instrument shape.

## Corrections required before the served run

**E1 · BLOCKING — a contradicted confirmation fails the whole certificate.**
`witness_confirmation_and_explanation` requires every positive witness ref to appear in
*SUPPORTED* confirmations. A CONTRADICTED confirmation is a legal, honest outcome — the gate
correctly routes the entity to `AMBIGUOUS` ("prospective witness contradicted") — and my
pre-registration (P4) predicts at least one will occur live. As written, the first honest
contradiction turns the entire checkpoint FAIL. Fix: require every positive witness to have a
**graded** confirmation (SUPPORTED or CONTRADICTED) and an evidence-bound answer where one was
demanded; require SUPPORTED only for entities that advanced to `WITNESSED`/`G4-READY`. One
synthetic fixture with a contradicted confirmation must PASS the certificate with the entity
deferred.

**E2 · Recompute prospectivity, don't trust it.** The check verifies membership, not time. Add
the comparison the G2 evaluator makes: the confirmation's transition id strictly exceeds the
pending declaration's. It is one integer comparison per confirmation and closes the gap between
"the machine enforces it" and "the certificate proves it."

**E3 · The live world is NAV; the only synthetic certificate is CLICK.** Before the served run,
one synthetic **NAVIGATION** trace (contact attempts, navigation-limit trip,
`NAV_ENUMERATION_COMPLETE`) must pass end to end — otherwise the evaluator's NAV path meets
reality for the first time during the run it is grading.

## Standing finding, restated with new force

**F1 (from `REVIEW_IMPLEMENTATION_G3_STACK_v1`) is still open, and the certificate cannot see
it.** The boundary-crossed confirmation branch still files the entity to `FILED_TO_G5` — under
an actor literally named `G3_REACTION_HANDOFF`, which says the intent is G4 deferral while the
state says G5 — and `FILED_TO_G5` sits in `ALLOWED_TERMINAL_STATES`, so a run that mis-files a
live lever this way still passes the certificate. On ls20 the counter expires every ~42
actions; the probability that a boundary crosses a pending confirmation in a real sweep is not
small. Minimal fix: route to `AMBIGUOUS` with the boundary reason (retryable), journal the
boundary evidence to the G4 deferred pool. If it ships as-is, the run review must check this
branch by hand (my P1 does).

## Noted, not contested

The null-sweep decision (`NO_RESPONSE_YET → G3-CLOSED → G4-READY`) inverts my F2
recommendation, deliberately. Accepted with the semantic pinned: `G4-READY` means "dossier
handed to the causal-expansion stage," not "has something to expand" — the guard that
witness-less entities get no G4 *expansion* probes now lives in G4's selection, and must be
written there when G4's router lands.

## Green light

With E1 and E3 closed (E2 strongly recommended, F1 fixed or hand-checked), the runbook and
evaluator are fit for the controlled served run. Grading of the run will proceed against
`PREREG_G3_LIVE_REVIEW_v1`, predictions P1–P6 explicitly, alongside this document.

# Build slice: G3 per-entity lifecycle journal

**Date:** 2026-09-22  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

This slice gives each persistent entity its own state machine. It prevents G3 from treating the
whole sweep as one undifferentiated status and prevents a null observation from becoming an
inertness claim.

The primary path is:

`UNTOUCHED → ATTEMPTED → RESPONDED / NO_RESPONSE_YET → WITNESSED → G3-CLOSED → G4-READY`

The journal also records `AMBIGUOUS`, `FILED_TO_G5`, `BUDGET_STOPPED`, and `REOPENED` as explicit
side states. Every transition stores the entity, prior state, new state, evidence reference,
actor, and reason. Witness references are append-only. Reopening affects only the contradicted
entity.

Implemented in `inference/framework/lever_lifecycle.py` and surfaced through the G3 gate view.

Validation: lifecycle tests cover positive witness closure, scoped null closure, entity-local
reopening, illegal transitions, and missing evidence. The scheduler shell is now implemented in
`BUILD_SLICE_G3_SCHEDULER_2026-09-22.md`; its returned target-local response is deliberately
provisional until the attribution and Duck-dossier slice resolves local, remote, counter, and
ego-confounded effects.

# Build record — N5.2 bounded G3 route handoff

**Type:** `BUILD_RECORD`
**Parent:** `REVIEW_RING9_G3_NAV_N5_1_LS20_V1_2026-10-04.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Status:** source built and focused-validated; package and live confirmation pending

N5.1 proved the semantic explanation seam and exposed the next friction: a G3 controller handoff
for which no deterministic route step was available could wake the unconstrained Duck loop. N5.2
keeps Duck available for that genuine judgment boundary while giving it one tightly bounded action
choice for the current certified revision.

The route checkpoint is keyed to the G3 revision. It permits one model request, requires a tool
call, disables thinking and caps output at 256 tokens. The prompt binds the current target and asks
for exactly one legal `APPROACH` or `CONTACT_ATTEMPT` action using the current frame. A successful
action creates a new revision and returns ownership to the controller. A failed request or empty
choice emits `G3_ROUTE_RETRY_EXHAUSTED`, which is a complete bounded product with G4 closed.

The request log now records the effective semantic and route overrides rather than the agent's
unmodified defaults. Existing N5.1 behavior remains unchanged.

Validation: 24 focused tests passed with 14 existing dependency warnings; Ruff passed on every
changed source and test file.

— **Sol**

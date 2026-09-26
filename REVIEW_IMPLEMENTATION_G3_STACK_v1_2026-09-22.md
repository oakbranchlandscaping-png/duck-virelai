# Review: the G3 implementation stack and its documentation

**Type:** `REVIEW_IMPLEMENTATION_G3_STACK` · **v1** · **2026-09-22**
**Reviewer:** collaborator seat (Cowork), independent verification pass.
**Scope:** the new G3 modules (`entity_observation.py`, `lever_lifecycle.py`,
`lever_attribution.py`, the G3 machinery in `virelai_gates.py`), the G1/G2 repair slices as
landed, and the documentation set (four G3 slice docs, two run reviews, the status/build plan).
**Method:** suites re-run in an independently built Linux CPython 3.12 environment against the
mounted tree; new modules read first-hand; contract conformance spot-checked against
`CONTRACT_G3_ENTITY_LIFECYCLE_v1` and the accepted corrections in
`REVIEW_COLLABORATOR_G3_LEVER_LIFECYCLE_2026-09-22.md`. Read-only; no production file touched.

## Verdict

**Accept.** The stack is contract-conformant in every place the review corrections named, the
evidence hygiene in the documentation is the best in the program's history, and my independent
runs reproduce green. One medium finding (a lifecycle mis-file on boundary-crossed
confirmations), one low finding (a missing guard), and two observations follow; none blocks the
next operation (prospective witness confirmation and G4 handoff — which, I note, is already
implemented in the confirmation path and largely awaits its live test).

## Independent measurements (direct observations at this review's anchor)

- Full suite: **309 passed, 0 failed** (my environment has `taaf` importable, so it collects
  more than the status doc's 290-non-online count; both are green; recommend stamping test
  counts with their anchor commit to keep snapshots comparable).
- New-module focused tests: `test_entity_observation` + `test_g3_scheduler` (20) and
  `test_lever_attribution` + `test_lever_lifecycle` (13) — **33 passed** here; the claimed "48
  focused" presumably spans additional touched files and was not re-derived exactly.
- Ruff: clean on all three new modules.
- Environment caveat: Linux CPython 3.12.14, not the pinned macOS 3.12.12.

## Findings

**F1 · MEDIUM — boundary-crossed confirmation mis-files the entity to `FILED_TO_G5`.**
`virelai_gates.py`, the confirmation branch: when a prospective confirmation transition carries
a boundary state, the *entity* transitions to `FILED_TO_G5` ("confirmation crossed a
boundary"). Two objections. First, semantics: `FILED_TO_G5` means "an unattributed autonomous
process was observed" — a boundary interrupting a demonstration is neither unattributed nor
autonomous; it is an interrupted experiment plus a boundary record that belongs to the G4
conditional-reaction pool (exactly the transition-43 feedstock the status doc itself preserves
for G4). Second, liveness: `FILED_TO_G5`'s only legal exit is `REOPENED` via the contradiction
monitor, so a lever that happened to be mid-demonstration at a counter expiry is dead to the
sweep for the rest of the level even though nothing about it was falsified. Proposed
disposition: on a boundary-crossed confirmation, journal the boundary evidence to the G4
deferred pool, return the entity to a retryable state (`AMBIGUOUS` with the boundary reason, or
back to `RESPONDED` with the pending confirmation cleared), and let the scheduler re-admit it.
One test: entity mid-confirmation at a respawn boundary is retryable afterward.

**F2 · LOW — `ready_for_g4()` lacks a witness guard.** The journal permits
`NO_RESPONSE_YET → G3-CLOSED → G4-READY`, so a null-closure entity can be marked ready for
causal expansion with nothing to expand. The router currently calls `ready_for_g4` only on a
supported confirmation, so the defect is latent, not live — but the journal is the contract's
enforcement point, and fixtures-richer-than-production has a mirror image: guards that live
only in the caller. One-line guard (`witness_refs` non-empty) plus one test.

**O1 · Observation — "WITNESSED" in the lifecycle means "demonstrated."** The immutable
∃-witness is created in the evidence accumulator at the first attributed residue (correct,
append-only, nulls cannot erase it — verified in the accumulator design), while the journal's
`WITNESSED` state fires only after a *supported prospective confirmation*. The epistemics are
right — capability witness immutable, depth gated on demonstration — but the state name
collides with the witness law's vocabulary, and a future reader will conflate them. Rename the
state (`DEMONSTRATED`) or add the distinction to the journal docstring.

**O2 · Observation — a contradicted confirmation is G4 feedstock, not just an `AMBIGUOUS`
mark.** The branch records the contradiction reason and moves on. Under the G4 mine's condition
ledger (§2d), "same intervention, different outcome" is the premier condition candidate — the
pending-confirmation record (declared cells, addresses at declaration and grading) should be
preserved into the entity's dossier so G4 can read the split, not merely that a split happened.
Cheap now, expensive to reconstruct later.

## What conforms, verified first-hand

`AMBIGUOUS_EGO_MASKED` exists as a first-class disposition and routes to the lifecycle (review
correction 4 — closed). Every G3 transition passes through the counter monitor, with the
in-code comment refusing to let the continuity read silently replace it (correction 5 —
closed). The journal enforces evidence_ref, actor, reason, and a legal-transition table on
every write; witnesses append only from `RESPONDED`; dossier answers are stored but cannot
close a lifecycle by themselves — prose closes nothing (contract §3 — holds). Identity
correspondence admits only exact, recolor, translation, growth, or shrink, with ambiguity
surfaced rather than smoothed (contract §1 abstention — holds). The scheduler binds ranked
targets with CLICK tokens and NAV contact intents under a navigation limit, walk-as-cost
(correction 2's shape — present; live enablement still gated, correctly). The prospectivity
chain — first response creates a pending confirmation, witness/close/G4-READY only on a
supported later transition — implements the review's strictest reading. The G2 deadlock repair
matches its root-cause (the stored counter-only action is now reachable at answer time).

Accepted contract deltas, recorded not contested: `SCHEDULED` and `IDENTITY_SUSPENDED` states
are absent (ambiguity is handled at the observation layer); the monitor verdict joins the
lifecycle via the evidence record rather than a field on the event — an adequate join.

## Documentation

The evidence discipline is exemplary and should be named as such: every slice doc carries an
evidence-state header (`BUILT, LIVE UNCONFIRMED`) and a production-boundary section; the run
reviews grade only their checkpoint's question, record quality notes against passes (the
21-versus-42 capacity arithmetic — which, for the record, my own arithmetic confirms: 84 cells
at 2 per action is a 42-action period), and refuse to let zero game score contaminate a
structural pass in either direction. The status doc's LIVE CONFIRMED / DIAGNOSTIC / BUILT
taxonomy with per-row evidence boundaries is the State-of-the-Build discipline working. Two
small notes: stamp test counts with their anchor (the tree outruns its documents within a day),
and the G1/G2 live confirmations should carry "n=1 world, local serving" wherever they are
cited outward — the three-world frozen-package checkpoint remains the citable general claim.

## Disposition summary

| Area | Disposition |
|---|---|
| Entity observation + continuity | PASS |
| Lifecycle journal | PASS with F2 guard and O1 rename recommended |
| Attribution + dossier contract | PASS |
| G3 gate machinery + scheduler | PASS with F1 required before a live G3 run |
| G1/G2 repair slices | PASS (deadlock root-cause matched by fix) |
| Documentation set | PASS, exemplary hygiene |

*Read-only review. F1 is the one item I would close before the first live lever sweep; F2, O1,
O2 ride along in the same small slice.*

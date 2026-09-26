# G3 lever gate: build plan for posterity

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**North Star:** Probe the world, build a stable internal model, observe the win rather than guess
it, and describe the observed goal in the learned physics grammar.  
**Gate status:** Entity continuity and initial observation adapter built; live G3 unconfirmed.

## Gate purpose

G3 asks:

> For every reachable entity, does an authorized interaction produce an attributable local or
> remote response after counter masking and ego-motion accounting?

Duck must explain each accepted response with its entity, intervention, observed change, evidence
references, limits, competing explanation, and falsifier. A gate closes only when that explanation
is supported by the record and the required prospective confirmation has occurred.

G3 establishes a response witness. It does not explain the full causal mechanics of that response.
Conditionality, effect subjects, bearing, magnitude, coupling, repetition, and saturation belong
to G4. Unattributed autonomous residue belongs to G5. Counter-expiry consequences remain evidence
for G4.

**Director clarification, 2026-09-23:** the binding parent protocol is click every eligible visual
object in CLICK worlds and collide or attempt contact with every eligible visual object in NAV
worlds, with both arms in HYBRID worlds. Discovering a lever follows from executing this protocol;
it is not an arbitrary hit-rate requirement. A record with no lever has not answered G3 and
reopens the roster, locus, contact, masking, state, and attribution audit.

## Inputs and outputs

G3 receives:

- the closed G2 counter product and reversible mask;
- the demonstrated G1 ego law and current ego binding;
- the world-type branch from metadata and G1 (`CLICK`, `NAV`, or `HYBRID`);
- the ranked G2 frontier as initial coverage evidence;
- lossless before/action/after transition records.

G3 produces:

- a persistent entity/worldline ledger;
- a budget-aware coverage certificate;
- one dossier per attempted entity;
- immutable local/remote response witnesses;
- Duck's evidence-linked explanation for each positive witness;
- prospective confirmation records;
- `G4-READY`, `FILED_TO_G5`, `AMBIGUOUS`, or `BUDGET_STOPPED` handoffs.

## Engineering sequence

### G3.1 — Entity continuity and observation foundation

**Product:** persistent entity hypotheses and production-shaped observation scopes.

Visual components and coordinates remain sightings. Unique still, recolor, translation, birth,
disappearance, and ambiguous correspondence are recorded across total runtime ledgers. The G2
frontier seeds member bindings but does not become a permanent id queue.

**Exit criteria:**

- entity hypotheses survive unique movement and recolor;
- ambiguous correspondence creates an explicit ambiguity;
- pre-action pointer ownership is resolvable;
- total `site_transitions` are required for scope derivation;
- counter, ego, contact, ground, and confounded ego partitions are explicit.

**Status:** built locally in `entity_observation.py`; 48 focused G2/G3 tests pass; live-unconfirmed.

### G3.2 — Per-entity lifecycle journal

**Product:** append-only lifecycle state machine and write authority.

Each entity is independently tracked through:

`UNTOUCHED → ATTEMPTED → RESPONDED / NO_RESPONSE_YET → WITNESSED → G3-CLOSED → G4-READY`

with side states `AMBIGUOUS`, `FILED_TO_G5`, `BUDGET_STOPPED`, and `REOPENED`.

Witnesses are immutable. Laws and explanations are versioned and revisable. A null observation
never proves inertness.

**Exit criteria:** every state transition has an evidence reference, actor, prior state, and
reason; illegal transitions fail; a later contradiction reopens the affected entity only.

### G3.3 — Production scope hardening

**Product:** complete runtime scope adapter.

Bind the demonstrated ego worldline set, expected self-motion, body contact/refusal, ordinary ground
exchange, counter mask, boundary state, and driver relation from actual runtime records. Keep
ego-confounded cells ambiguous until an independent attribution exists.

**Exit criteria:** no production path depends on fixture-only target footprints or guessed contact
lines; missing scope becomes `UNRESOLVED_ATTRIBUTION` or `AMBIGUOUS_EGO_MASKED`.

### G3.4 — Cross-gate counter monitor

**Product:** counter observer attached to every later transition.

The locked counter is monitored for changed rate, contradictory rewrite, extremal boundary,
representation gap, or reopening. Masked counter cells remain in the evidence record with their
disregard reason.

**Exit criteria:** G3 cannot silently classify a counter tick as a lever effect or silently lose a
counter contradiction.

### G3.5 — World-type-complete scheduler shell

**Product:** one G3 router and a re-derived coverage ledger.

The router alone issues probes. The inherited G2 frontier is the initial ledger; after every
transition the present entity roster is re-derived and reconciled with persistent hypotheses.

**Exit criteria:** no direct or parallel probe path can bypass the active gate; ranking and coverage
certificates record tried, untried, absent, ambiguous, unreachable, and budget-forbidden entities.

### G3.6 — CLICK arm

**Product:** exhaustive pointer sweep.

In CLICK worlds, probe every present ranked entity using the strict visual ranking. A positive
witness does not stop the sweep. Null presses do not prove inertness or stop enumeration.

**Exit criteria:** enumeration completes only when no present entity remains unattempted or an honest
budget/representation certificate is emitted.

### G3.7 — NAV arm

**Product:** embodied contact sweep.

In NAV worlds, pilot the demonstrated ego toward each target. Each action is classified as
`APPROACH` or `CONTACT_ATTEMPT`; contact line, refused contact, target response, boundary, and
pilot budget are recorded.

**Exit criteria:** the adapter distinguishes approach from contact and never treats a route failure
as proof that the target is inert or absent.

### G3.8 — HYBRID arm

**Product:** hybrid ordering and activation path.

Hybrid worlds use the metadata-defined click path to test activation, then preserve the embodied
branch when it becomes live. The ordering is explicit in the controller and visible in the trace.

**Exit criteria:** click-first activation and subsequent NAV behavior are separately evidenced;
neither branch is inferred from the other.

### G3.9 — Attribution and Duck dossier

**Product:** one answer contract per target.

**Implementation status:** **BUILT, LIVE UNCONFIRMED** in
`BUILD_SLICE_G3_ATTRIBUTION_DOSSIER_2026-09-22.md`.

Duck must answer:

- Which persistent entity was targeted?
- Which action or contact was the intervention?
- What changed locally and remotely after counter and self-motion accounting?
- What evidence supports the claim?
- What remains ambiguous?
- What competing model and falsifier remain?

G3 may call a response local, remote, or both. It must not assign a full mechanism or claim
universal inertness.

**Exit criteria:** explanation references exact immutable evidence; prose cannot close a dossier by
itself; positive, null, ambiguous, boundary, and G5 dispositions remain distinct.

### G3.10 — Prospective closure and G4 handoff

**Implementation status:** **BUILT, LIVE UNCONFIRMED** in
`BUILD_SLICE_G3_PROSPECTIVE_CONFIRMATION_2026-09-22.md`.

**Product:** confirmed witnesses and complete certificate.

For each positive response, Duck freezes a scoped prediction and receives one new transition for
confirmation. Hypothesis formation and confirmation cannot use the same transition.

**Exit criteria:** every discovered entity reaches `G3-CLOSED`, `G4-READY`, `FILED_TO_G5`,
`AMBIGUOUS`, or `BUDGET_STOPPED`; every positive witness is immutable; the certificate states
what was never tried and why.

## Live checkpoint

The live checkpoint is separate from implementation slices. It must run the actual Duck on a
controlled world and verify:

1. metadata assigns the correct world type;
2. the correct CLICK, NAV, or HYBRID arm is selected;
3. strict target ranking is followed;
4. the counter remains masked and monitored;
5. entity dossiers persist across transitions;
6. Duck explains each accepted witness;
7. the sweep stops quickly on recognized completion;
8. unresolved effects are deferred honestly;
9. no win is guessed;
10. the resulting dossier is sufficient to open G4.

The live certificate must contain the prospectively confirmed lever witness produced by the
completed interaction protocol.

The checkpoint is graded only on G3 products. Game score and full causal explanation are outside
its exit criteria.

## Evidence language

- **LIVE CONFIRMED:** a completed served-model run met the slice or checkpoint contract.
- **BUILT, LIVE UNCONFIRMED:** active source and local tests pass; Duck has not demonstrated it in
  a complete served run.
- **LIVE DIAGNOSTIC:** a served trace exposed behavior but missed the contract.
- **BUILDER REPORT:** historical or collaborator claim not independently observed here.
- **HYPOTHESIS:** expected behavior awaiting evidence.

No historical plan, packaged source, or collaborator briefing promotes a slice to LIVE CONFIRMED.
Only the actual controlled run does that.

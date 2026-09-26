# G4 Mine Report — causal expansion: conditions, subjects, couplings, mechanisms

**Type:** `MINE_REPORT_G4_CAUSAL_EXPANSION` · **v1** · **2026-09-22**
**Author:** collaborator seat (Cowork), read-only mine of both roots and the project KB against
the ruled G4 contract. Everything below is a builder report about the archive until re-read
first-hand at the current anchor. Companion: `MINE_REPORT_G3_LEVERS_v1` (G3-levers/), the v3
theses, `REVIEW_COLLABORATOR_G3_LEVER_LIFECYCLE_2026-09-22.md` (whose corrections govern), and
`CONTRACT_G3_ENTITY_LIFECYCLE_v1_2026-09-22.md` (the shared lifecycle G4 rides).

## 0 · The ruled contract this mine serves

G4 is the causal expansion of a G3-CLOSED entity — a **separate question** from G3 on the one
per-entity lifecycle: G3 established that an attributable intervention caused a scoped response;
G4 explains **conditions, effect subjects, direction, magnitude, coupling, repetition,
saturation** — the six unanswered questions of the lever-subtree audit plus the cross-entity
causal map. Conditions are read as masked-state discrimination under the G7 correction (the
observable address may hide state: condition evidence starts as outcome-sets, never assumes
Markov sufficiency). Two halves: the free passive kernel over every transition the run produces;
the paid half in single-action frozen demonstrations. Boundary-deferred records and
counter-expiry effects are G4's conditional-reaction feedstock. Contact/terrain responses are
the NAV branch of the same causal question.

## 1 · The verdict

**G4's evidence layer is a port — much of it already sitting in the active tree.** The Ring 8
semantic-shadow lineage carried joint-transform arithmetic, partner-pattern typing, and the
depth-probe state machine *into* `variants/ring9-cybernetic-gates/.../virelai_semantic/`, where
they are committed today, disconnected from the gates. The coupling and conservation machinery
exists in v4 with unusually strict epistemics (integer-exact, no free parameter). What has
never been built anywhere: the condition vocabulary as masked-address discrimination (the
pieces exist on both sides; the join does not), the conditional-reaction reading of
boundary/counter-expiry events, and the mechanic-layer SPEC itself — which the concept doc
records as standing doc debt. G4's build is one part wiring, one part join, one part genuinely
new spec.

## 2 · Port ledger, by causal question

### 2a · Already in the active tree (`inference/framework/virelai_semantic/`) — re-point, not port

- `joint_transform.py` — joint pixel arithmetic for one action-attributed control, run on the
  post-residue cells (ego/ground/counter already subtracted): what transformation the remaining
  pixels underwent *together*. Names no role, infers no purpose. This is the effect-quality/
  bearing/magnitude reader, committed.
- `typing.py` — mechanism typing ported from V3.5 cycle_probe + v4 mechanism_classify, with two
  correct refinements already made: **mechanism and condition are kept separate**, and
  recurrence claims are refused across intervening actions.
- `mechanics.py` — lever mechanics compiled from the masked, action-indexed weave residue.
  **Caution:** carries `MIN_ACTION_INDEPENDENT_PRESSES = 8` — a threshold constant; re-derive
  the sufficiency rule structurally before this module touches a gate (the no-threshold law).
- `depth_probe.py` — the one-lever-at-a-time depth state machine, deliberately disconnected
  from Duck; dynamic queue retained, fixed press counts and the mechanism/saturation conflation
  explicitly not carried. This is the skeleton of G4's paid half.

The standing lesson applies with double force here: **these modules are the archive's ninth
"built and pointed elsewhere" waiting to happen.** They exist in the active tree and nothing in
the gate path consumes them. Wiring them through the router *is* the G4 slice, not an
afterthought.

### 2b · Mechanism vocabulary and its ruled correction

- `SOLVER_BLUEPRINT_v1` §3.3–3.5: mechanisms **toggle · cycle · directional · global ·
  one-shot · gated** — *gated is a mechanism, not a category*: a lever whose effect is
  conditional on a precondition, which makes G4's condition question and the gated mechanism
  one machinery. Effects as measured transforms, `NOT_OBSERVED / OBSERVED_RIGID /
  OBSERVED_NON_RIGID`, vocabulary extensible by licensing, never forced rigid.
- `virelai_v4/weave/mechanism_classify.py` — the ruled correction that shapes the whole typing
  layer: **classify the reactive partner's pattern, not the lever's own.** The two confirmed
  real levers of the lever campaign were static, remote, self-invariant — nothing on the
  lever's own side to classify. Same four categories, pointed at the object that has the
  pattern.
- V3.5 `cycle_probe` exact distinctions (mined at LEVER_SUBTREE_00): SATURATED =
  predecessor-equality; TOGGLE = recurrence at length 2; CYCLE > 2; DIRECTIONAL = drift only;
  toggle/drift pixel separation structurally excludes HUD residue. Do-not-carry: the 20-press
  cap's write-time UNDETERMINED relabel.

### 2c · Couplings and conservation (the causal map's edges)

- `SOLVER_BLUEPRINT_v3` §4.1 — the two-strata law: **marginals** (per-entity mechanics) and
  **couplings** (edges between worldlines: `CoupledPair`, `ConservedTransfer`, the dependent
  complement *derived* from the measured coupling by linear dependence with a stable
  coefficient, never elected by size or appearance). Couplings are irreducibly joint and can
  never be stored inside single-entity records — a schema fact for the dossier.
- `virelai_v4/library/conserved_transfer_author.py` — the strictest epistemics in the archive:
  licensing requires (i) integer-exact conservation, no epsilon; (ii) forward, out-of-sample,
  exact-value prediction of the complement's signed delta; (iii) measured membership. No free
  parameter anywhere. The sign-dependency audit (project KB) verified the accept/reject reads
  only live signed deltas and a live negation — no stored magnitude. Port whole.
- `virelai_v4/weave/coupling.py` — the R1 pair-motion detector: press-indexed per-worldline
  signed-delta matrix, multi-criterion panel with no single trusted criterion, complement
  described and consciously ignored, never labeled background, size only a reported tie-break.
- Blueprint v3's recorded defect is the wiring warning again: the richest coupling signal
  reached only the dossier renderer, never dispatch. The G4 slice that lands couplings must
  land their consumer in the same commit (no contract without a live consumer).

### 2d · Conditions (the genuinely new join)

The pieces: masked world addresses (Ring 9 `masked_world_state`, built and live at G2);
cycle_probe's incremental masked-state hashing (V4, the per-press early-termination detector);
golden `push/machine.py`'s contradiction semantics — same (state, key), different landing =
hidden state or mask leak, reported never averaged. The join that has never been built: a
`ConditionLedger` per (entity, intervention) mapping `(observable_address, known_phase) →
outcome-set`, where a reproduced outcome supports the unconditional law, a split outcome *is*
the condition candidate, and the difference between the two addresses localizes where the
precondition lives. Under the G7 correction this starts as outcome-sets and promotes to a
conditional law only on demonstrated discrimination — the gated mechanism (§2b) is exactly a
promoted split. Prior art for the *demonstration* shape is G2's freeze-then-press machinery,
reused unchanged.

### 2e · Conditional reactions from boundaries and counter expiry

`BOUNDARY_EVENT_DEFERRED` records (the attribution kernel already emits them) plus preserved
counter-expiry effects are G4's feedstock for reaction laws conditioned on bookkeeping state —
"at source-minimum, contact kills" — the build plan names this explicitly (item 7). No prior
implementation exists anywhere in the archive; golden's boundary-exclusion lesson (three
phantom contradictions when boundary presses entered edges) defines the *negative* constraint:
these records inform G4 laws and never enter state-machine edges.

### 2f · The NAV contact branch

Carried from the G3 mine and the earlier gate discussion, unchanged: `golden/roles/ground.py`
(deformation fully accounted by ego displacement; intrinsic churn empty), `wall.py` (refusal on
a known bearing; one fingerprint; the refusal IS the contact), `crossing.py` (who exchanged
ground with whom under which button — account and verdict deliberately separated), `medium.py`
(the background as a sub-class of passive-reactive, required by logical necessity; the menu
stays closed). The ego-campaign record's precondition stands: on embodied worlds the medium is
named before deep causal reading is trustworthy.

### 2g · The dossier as G4's output surface

`CONCEPT_VIRELAI_SOLVER_v2` Loop Four: each roled entity interrogated down its archetype's
nested question tree, every answer a recorded delta, terminating in a human-gradable dossier
that feeds back into integration — a wrong role dictates wrong questions, returns nonsense,
decays, and flips. The physics grammar is the terminus: nouns (roles) and verbs (mechanics —
effects and couplings over the invariant vocabulary). Ring 9's `virelai_physics_manual.py`
already renders the projection view (admitted state variables and mechanics only, never a
second store). The **mechanic-layer SPEC is recorded doc debt** in the concept doc itself —
G4's contract document pays it.

## 3 · Do-not-port list

Confidence ladders and gates (0.60→0.95 accrual; 0.6/0.95 band locks); `MIN_*` press-count
constants as verdict gates (structural sufficiency rules replace them); the 20-press
UNDETERMINED relabel; classifying the lever's own trajectory where the partner has the pattern;
storing couplings inside single-entity records; any complement elected by size; fixed press
counts in depth probing; mechanism/saturation conflation.

## 4 · Open flanks

1. **The condition join (§2d) is new construction** — the only major G4 surface with no working
   ancestor. Its spec must precede its code.
2. **`virelai_semantic` is dark machinery in the live tree** — committed, tested in its lineage,
   consumed by nothing on the gate path. First G4 slice decides: re-point through the router or
   re-derive against the entity contract. Either way its threshold constant goes.
3. **The mechanic-layer SPEC** is owed (standing doc debt since the concept doc) and the entity
   contract's dossier needs its coupling stratum defined as edges, not fields.
4. **Hidden-state humility** (G7 correction) applies to every condition claim: outcome-sets
   first, discrimination demonstrated before a conditional law locks.
5. **Counter-expiry conditional reactions** have no prior art at all — expect a genuine design
   session, not a port.

## 5 · Deep-reads owed at WO time

`virelai_semantic/*.py` whole, at the anchor (especially `mechanics.py`'s sufficiency rule and
`depth_probe.py`'s queue semantics); `conserved_transfer_author.py` below the licensing header
and `coupling.py`'s panel criteria; `cycle_probe.py:468–533` (the incremental masked-hash
detector); the three lever-fixture files named in `WO_LEVER_LABEL_01`; and the boundary/expiry
record shapes the current attribution kernel actually emits.

*Read-only mine; no code changed. This report seeds the G4 contract and work orders; the
amendment-landing-status pre-check at each WO's own anchor still governs.*

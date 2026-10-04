# Proposed build plan: NAV friction repair and G3 close

**Type:** `PROPOSED_BUILD_PLAN`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** active. N0 diagnosed; N1-N3 built and locally validated. N4-N5 remain. No Kaggle run
authorized by this document.

## Purpose

The latest `ls20` NAV checkpoint reached G3 and exercised the new terrain machinery, but it did
not close the NAV sweep. This plan repairs the two boundaries that consumed the run before adding
more semantic sophistication:

1. the controller-to-Duck reachability handoff must be compact and bounded;
2. an accepted reachability result must remain terminal for the world state that justified it,
   while still reopening when evidence that could actually change that result appears.

The target is a reliable G3 NAV sweep. It is not yet G4 lever comprehension, cross-level carry, or
competition score optimization.

## Implementation checkpoint — 2026-10-03

- **N0 finding:** E0005 reopened because `EntityLedger.observe()` increments the entity observation
  version even for `STILL`, while G3 treated any later version as changed target geometry. E0006's
  first refused ACTION4 produced only the masked counter tick; E0005's cells had not changed.
- **N0 corrective boundary:** accepted reachability now compares the recorded target cells with the
  currently observed cells. A bookkeeping version increment cannot reopen the row.
- **N1 built:** the first reachability concept for a reasoning/topology/ego key requires three fixed
  semantic claims and one explanation of at most 40 words. The request drops ordinary conversation
  history and permits at most two model requests. Accepted meaning is cached at LEVEL scope.
- **N1 reuse:** sibling targets keep separate controller-certified identities, geometry, counts,
  evidence and conclusions. The controller reuses only Duck's accepted causal understanding when
  the semantic key is unchanged, so no model call is required for that repeated concept.
- **N2 built locally:** every accepted reachability row now stores a target-specific signature over
  target geometry, ego/action law, topology epoch, contact edges and nearest target-directed bridge
  edges. Reachable-stand growth is audit data and reopens a row only when that experiment set
  changes. Reopen events preserve old/new signature IDs, exact changed fields and their values.
- **N3 built locally:** the stood map and refusal ledger are reused across the ranked roster. A
  prior boundary refusal supports another target only when every equally nearest target-directed
  boundary press is already refused; an equally good untried press blocks reuse. Each target still
  receives its own geometry, signature, evidence-bound certificate and terminal disposition.
- **Bounded-stop artifact remains N4:** N1 caps the semantic turn, but the named
  `G3_SEMANTIC_RETRY_EXHAUSTED` product is not yet emitted.
- **Local validation:** 107 focused NAV, scheduler, memory, controller and tool-agent tests pass.
  This is source evidence only; no successor package or live run has yet tested the change.

## Evidence ledger

### Directly observed in the `ls20` v2 artifact

Artifact root:
`runs/kaggle-ring9-g3-nav-terrain-ls20-v2/`

- G0, G1 and G2 closed; G2 installed the complete two-row counter mask.
- The G3 roster was populated before execution: 16 eligible rows and 2 counter exclusions.
- The controller owned all 50 environment actions. Duck selected no environment action.
- Five targets received execution, one was in progress or reopened, and nine remained queued.
- Three targets had contact evidence but remained `UNRESOLVED_EFFECT`; one closed as a scoped
  nonresponder; one row was typed as `FLOOR` from ego traversal.
- The run recorded a refused target-conditioned edge for E0005/M0019 and Duck supplied a
  provisional reachability explanation with explicit reopen conditions.
- The accepted answer was followed by target advancement, but the final ledger showed E0005 as
  `REOPENED`, with no terminal unreachable row persisted.
- The final Duck handoff consumed multiple long requests. Prompt tokens rose from 6,985 to 41,380
  across retries; the model timed out at the 900-second behavior deadline.
- No live `WALL` roster row was produced. The artifact contains refused-edge evidence, which is
  routing evidence, but that is not by itself proof that a particular visual component is a wall.

### Builder reports and source contracts

These are implementation claims or intended contracts; they are not equivalent to the live
artifact until replayed:

- `BUILD_G3_NAV_INTEGER_TERRAIN_AND_REACHABILITY_v1_2026-10-03.md` says terrain is current-state,
  footprint-aware, and reversible after a counter-masked world delta.
- `nav_terrain.py` distinguishes `PREDICTED_REACHABLE` from `PREDICTED_UNREACHABLE` and requires a
  target-conditioned falsifier before creating the Duck handoff.
- The pre-change `virelai_gates.py` contains three broad reopening routes: a new stood anchor, a
  target version increase, and a counter-masked world-state change. The exported artifacts alone
  do not name the caller. N0 joined their ordering to the byte-identical executed source and proved
  that the target-version route fired on an unchanged `STILL` component.
- `controller_executor.py` already establishes the right ownership rule: deterministic actions and
  certified answers stay with the controller; Duck is woken for judgment.

### Prior art worth porting, with limits

- Golden `golden/captain/nav_sweep.py` and `tests/captain/test_nav_sweep.py` require every open
  frontier press to be attempted before a reachability presumption. They explicitly treat walking
  as cost, not as a separate semantic gate, and keep the presumption recomputable and reopenable.
- Golden `golden/captain/nav_lattice.py` records occupied composite stands and refuses on the
  correct composite anchor. Its documented defect shows that union-rekeying refusals across body
  members manufactures false unreachable conclusions.
- Golden `docs/wo/G3-04_nav.md` warns that no lattice means “unaskable,” not unreachable, and that
  a present but unattempted target must not be silently dropped.
- Ring 8 `inference/agent/tool_agent.py` has compact action results and explicit terminal stop
  behavior. It is useful for the request-budget boundary, but its prompt policy is not a reason
  to import the old Ring 8 architecture.
- The separate `virelai-golden` repository remains a deterministic donor. It is not the hybrid
  source tree and its downloaded engine files remain out of scope.

## Friction diagnosis

### F1 — The semantic handoff is too expensive

The controller has already computed the reachability certificate. Duck is being asked to restate
large evidence and preserve exact fields through a normal model conversation. The v2 trace shows
retries, prompt growth and a timeout before the next controller action.

**Interpretation:** this is an interface/budget failure, not evidence that Duck needs to discover
the route itself. Duck’s job at this boundary is to acknowledge the supplied certificate, state
the provisional limit, preserve the reopen conditions, and release the row.

### F2 — “Reopenable” was broader than “relevant evidence changed” — resolved locally in N2

The current implementation can treat a newly stood anchor and a target version increase as reasons
to reopen provisional reachability records. That protects against stale maps, but may ignore the
accepted answer’s scope: a counter-only transition, a stand that does not create a new
target-conditioned contact or bridge, and an unchanged target geometry should not erase a completed
row. The live ordering is consistent with this concern, but does not prove which trigger fired.

**Resolution:** the invalidation rule now compares the target's geometry, ego/action law, topology
epoch and available contact/target-directed bridge experiments. Event counters and evidence
references do not control reopening.

### N0 resolution and remaining hypotheses

- **Established source cause:** E0005 reopened because the next observation incremented its entity
  version without changing its cells. The artifact/source join and regression are recorded in
  `DIAGNOSTIC_N0_NAV_REOPEN_E0005_2026-10-03.md`.
- **Resolved locally in N2:** a later stood anchor does not reopen an accepted target when its
  contact and nearest target-directed bridge sets are unchanged.
- **Resolved locally in N2:** a residual world delta advances the routing topology epoch and records
  that exact field as the reason for reopening.
- **Unverified WALL hypothesis:** the refused footprint may not overlap one frozen visual component
  under the current component-scoped rule. The run is not evidence that wall inference itself
  failed.

### F3 — Terrain evidence and object semantics are still coupled in the ledger

The controller can correctly use a refused edge to route, yet a live run may end without a direct
`WALL` row. The current distinction in source is sound, but the production path needs a separate
terrain witness record before it can type a visual component. A routing refusal alone must not make
the target inert or wall by class-wide integer.

### F4 — The sweep does not yet amortize shared topology

E0005, E0006 and E0007 occupy the same lower-band region. The run spent many actions reaching the
same boundary and then began a second target before the prior semantic state was durably closed.
The map should be shared; each target still needs its own contact or target-conditioned falsifier,
but it should not rebuild the same route proof.

### F5 — G3 has no bounded completion mode for a time-limited run

The source has `BUDGET_STOPPED` and bounded-ambiguity machinery, but the live v2 stopped inside a
model retry loop. A run should either close G3, stop at an explicit accounted boundary, or emit a
diagnostic artifact that names the exact pending target and preserves the ledger. “Cancelled while
answering” is not a useful gate result.

## Proposed build ladder

### Slice N0 — Freeze the contract and create a replay fixture — **diagnosed**

Before changing behavior, capture the v2 evidence needed to reproduce the failure without Kaggle:

- the E0005 certificate;
- the accepted Duck answer;
- the next E0006 controller action;
- a counter-only transition;
- a new stand that does and does not open a target-relevant bridge;
- a target geometry/version change;
- a non-counter world delta.

Add a small fixture builder around these records rather than replaying the full notebook. Use the
JSON evidence artifacts; do not depend on unpickling the executed solver. Instrument the fixture to
record which reopening path fired and whether the target-specific contact/bridge frontier changed.
The fixture must assert the distinction between source, exported package and executed artifact.

**Exit criteria:** the fixture reproduces the observed `PRESUMED_UNREACHABLE -> REOPENED` path,
names its exact cause, and can be run against both the working source and the packaged source. N0
changes diagnostics and fixtures only; it does not change runtime policy.

The diagnostic exit is satisfied by the JSON-derived ordering, byte-identical source comparison
and focused `STILL` regression. See `DIAGNOSTIC_N0_NAV_REOPEN_E0005_2026-10-03.md`.

### Slice N1 — Compact reusable reachability-understanding checkpoint — **built locally**

Split the handoff into immutable controller facts and a very small Duck explanation. The
controller-owned view contains only:

- target identity and stable target version;
- current world-state address;
- reachable-stand count and closest stand;
- refused-edge count and falsifier evidence reference;
- the certified conclusion (`PRESUMED_UNREACHABLE`);
- the certified reopen conditions;
- the explicit limit that this is reachability, not inertness.

Duck supplies only the semantic fields that demonstrate understanding: what the ego cannot
currently do, what evidence bounds that statement, why this says nothing about inertness, and what
kind of later evidence would reopen the question. The controller injects identity, counts,
evidence references, conclusion and reopen conditions into the accepted record. Duck must not copy
large arrays or exact controller-owned lists.

This is a concept checkpoint, not a per-object essay. The semantic key is the reachability
reasoning class plus the routing-topology epoch and ego-law version. Once Duck has correctly
explained `OUTSIDE_EXHAUSTED_REACHABLE_COMPONENT` for that key, the controller may reuse the
accepted understanding for every target whose individual certificate has the same reasoning key.
Each target still receives its own controller-certified row, closest stand, gap, evidence and
reopen signature. A new reasoning class, topology epoch or ego law requires a new Duck checkpoint.

The Duck payload is bounded to three structured claims and one sentence of at most 40 words:

- `meaning`: the ego cannot currently contact the target from the mapped reachable component;
- `not_proven`: the target is inert or permanently unreachable;
- `reopen_if`: relevant terrain, ego law, target geometry or route availability changes;
- `explanation`: Duck's concise causal statement in its own words.

Run this as a checkpoint-specific bounded request containing the universal ontology, the active
gate goal and this compact certificate. Do not carry the growing ordinary tool transcript into
contract repair. If the first answer fails, issue one fresh repair request with the same certificate
and the precise validation error. A second failure produces an explicit semantic-stop artifact.

**Exit criteria:** local tests prove that Duck cannot alter certified geometry or evidence, must
explain reachability versus inertness in at most 40 words, and can be accepted within a fixed
prompt-size bound and one repair request. No environment action is available while the answer is
due. The accepted artifact must preserve Duck's explanation separately from the controller fields.
A second target with the same semantic key reuses the accepted understanding without a model call;
a changed topology epoch, ego law or reasoning class requires a fresh checkpoint.

The compact contract, persistence, keying and controller-reuse portions are locally satisfied.
The explicit retry-exhausted product remains N4; packaged and live confirmation remains N5. See
`BUILD_N1_COMPACT_REACHABILITY_UNDERSTANDING_2026-10-03.md`.

### Slice N2 — Evidence-addressed terminalization — **built locally**

Make each accepted reachability record carry a target-specific reachability signature:

- target geometry/identity fingerprint;
- ego shape and bearing-map fingerprint;
- routing-topology epoch, advanced only by a non-counter, non-ego world delta;
- reachable contact-edge set for this target;
- unspent target-conditioned bridge-edge set for this target.

After a potentially relevant event, recompute that signature. Reopen only when the target geometry,
ego law or topology epoch changed, or when the recomputed contact/bridge sets now supply a new
experiment. New evidence references alone do not change the question.

Do not reopen for:

- a counter-only transition;
- an unchanged target version merely observed again;
- a new stand that does not change the target’s reachable contact/bridge frontier;
- another target's contact or falsifier when it leaves this target's signature unchanged.

Preserve the current rule that a genuine world delta, target geometry change, yielding refusal,
new relevant stand, changed ego law, or changed action surface can reopen the row.

**Exit criteria:** focused tests cover accepted answer → target advance → counter-only transition,
accepted answer → irrelevant new stand, accepted answer → relevant new bridge, unrelated target
probe, target change, and world-state change. Only the relevant cases reopen. Every reopening event
must record the old signature, new signature and the specific changed field.

The local exit is satisfied. The implementation also prevents an older reopened record for the
same target from intercepting a later invalidation. Packaged/live confirmation remains N5. See
`BUILD_N2_EVIDENCE_ADDRESSED_TERMINALIZATION_2026-10-03.md`.

### Slice N3 — Shared topology and target-conditioned sweep — **built locally**

Retain one current-state NAV map and reuse it across the ranked roster. For every target:

1. take a known contact route if one exists;
2. otherwise spend the closest unrefused target-conditioned frontier press;
3. record a refused or yielding falsifier when an unspent target-conditioned edge exists;
4. when the reachable component is shared and every equally nearest target-directed boundary press
   is already refused, derive a separate target-specific certificate from that evidence instead of
   repeating the same walk; a tied untried press remains mandatory;
5. hand off and persist one disposition per target;
6. advance without rebuilding the same lower-band map.

This preserves “collide with everything”: every reachable object receives a contact attempt. An
object proven outside the exhausted field of play receives its own reachability certificate. The
same physical refusal may support several certificates when it is genuinely the exhausted boundary
for each, but each roster row retains its own closest stand, gap and reopen signature.

Keep target identity separate from terrain identity. A floor or wall row closes only when the
component cells overlap the direct terrain evidence that established it. A refused target contact
is still a target contact record and does not automatically type the component as wall.

**Exit criteria:** a synthetic multi-target fixture proves E0005/E0006/E0007 share route evidence,
each receives its own terminal disposition and certificate, every reachable object is physically
contacted, and no target is skipped because the map was reused.

The local mechanism exit is satisfied by a two-sibling fixture: one physical boundary refusal
supports two distinct target certificates, the second semantic answer is controller-reused, and no
extra navigation action occurs. Existing contact-path tests continue to require physical contact
for reachable objects. A tied open bridge prevents reuse. See
`BUILD_N3_SHARED_TOPOLOGY_TARGET_SWEEP_2026-10-03.md`. Live E0005/E0006/E0007 confirmation remains
N5.

### Slice N4 — G3 accounting and controlled stop — **built locally**

Add an explicit controller stop product for a bounded run:

- `G3_COMPLETE` when every eligible row is terminal;
- `G3_BUDGET_STOPPED` when the action/time limit is reached;
- `G3_SEMANTIC_RETRY_EXHAUSTED` only when the compact answer contract has failed its bounded retry;
- `G3_BOUNDARY_DEFERRED` for death, respawn or level transition.

Each product must include the pending target, last accepted evidence, remaining roster counts and
whether G4 is legally open. A server timeout must never be silently represented as a normal Duck
answer or as a reopened target.

Implemented by Sol on 2026-10-03 in `inference/agent/gate_artifacts.py`, with solver and analyzer
hooks. The current artifact is `<game>_g3_run_outcome.json`; each emission also appends to
`<game>_g3_run_outcome_history.jsonl`. The record contains the product, pending target, latest
lifecycle evidence, per-state remaining roster counts, scheduler state, and `g4_legal_open`.
`G3_COMPLETE` is emitted only after the aggregate G3 inventory answer is accepted and the machine
has advanced into a G4 gate. A solver action/time exit emits `G3_BUDGET_STOPPED`; death or level
transition emits `G3_BOUNDARY_DEFERRED`; and a failed bounded compact reachability repair emits
`G3_SEMANTIC_RETRY_EXHAUSTED`. All incomplete products explicitly keep G4 closed.

**Local exit:** satisfied. Focused N4 tests cover explicit products, reload equality, append-only
history, pending-target accounting, and the completion-only G4 rule. The broader NAV/controller
suite is 115 passed with the existing 14 dependency deprecation warnings. Packaged/live confirmation
remains N5.

### Slice N5 — Local fast replay, then one bounded Kaggle successor

Use the OpenRouter/local path first with the compact model-facing handoff. Replay `ls20` and the
same synthetic fixture; then replay `vc33` only to ensure the shared controller contract does not
break CLICK. Package the exact source commit and manifest, and run one bounded Kaggle successor on
`ls20` with enough actions for G3 accounting but no competition objective.

The Kaggle grade should be limited to:

- G0–G2 closure and complete mask;
- roster accounting;
- controller ownership;
- terminal reachability disposition for every attempted target;
- persistence of accepted unreachable rows;
- direct floor/wall evidence where actually observed;
- explicit G3 completion or bounded-stop product.

Do not grade G4 comprehension or score until this NAV checkpoint is clean.

## After NAV is stable: collaboration boundary with Claude

Only after N0–N5 pass should we integrate Claude’s R20–R22 work. The merge should be contract-level,
not a blind branch merge:

1. keep Ring 9 NAV terrain, invalidation and target-ledger contracts as the base;
2. port Claude’s level-entry and no-legal-move rules where they do not change those contracts;
3. port G3-to-G4 lever-typing boundaries only after G3 emits a stable terminal product;
4. run both source suites and packaged-copy tests;
5. replay `ls20` NAV and `vc33` CLICK before any larger sweep.

Cross-level carry and G4 lever comprehension remain later gates. They must consume a stable G3
product; they should not be used to hide an incomplete NAV sweep.

## Execution order and file boundary

Execute the slices as separate checkpoints. Do not combine N0, N1 and N2 into one change:

1. **N0 diagnostic fixture.** Review the proven reopening cause before changing policy.
2. **N1 semantic handoff.** Prove one bounded explanation, controlled repair and semantic reuse.
3. **N2 terminalization.** Change reopening policy only with the N0 cause and N1 artifact stable.
4. **N3 shared topology.** Improve sweep throughput without weakening per-target accounting.
5. **N4 controlled stop.** Make every bounded execution end legibly.
6. **N5 validation.** Fast replay, packaged-copy verification, then one Kaggle checkpoint.

Expected implementation surface:

- `inference/framework/virelai_gates.py`: certificate ownership, terminal records and reopening;
- `inference/framework/nav_terrain.py`: target-specific reachability signature;
- `inference/framework/controller_executor.py`: ownership at the semantic checkpoint;
- `inference/agent/tool_agent.py`: fresh bounded checkpoint request and one repair;
- `inference/agent/gate_artifacts.py`: explicit diagnostic and stop artifacts;
- focused NAV, scheduler, controller and packaging tests.

Do not modify the counter law, G1 ego law, CLICK G3 semantics, G4 semantics or cross-level carry in
these slices. Preserve all existing unrelated working-tree changes.

## Review conclusion

After these revisions, the plan is ready to execute beginning with N0. Each slice has its own
observable exit and review point. No Kaggle run is implied by this plan; N5 reaches that decision
only after source and packaged-copy validation pass.

— **Sol**

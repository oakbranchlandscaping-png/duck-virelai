# Build Plan — Virelai Investigative Decision Controller

**Date:** 2026-09-15  
**Status:** Governing next-phase engineering plan  
**North Star:** `NORTH_STAR_VIRELAI_DUCK_HYBRID_v1_2026-09-15.md`  
**Build parent:** `variants/ring8-physics-gated-delivery/`  
**Control:** completed five-world optional physics-tool run in `runs/kaggle-ring8-physics-grammar-tool-run2/`  
**Pending baseline:** Kaggle gated-delivery notebook `taaf-duck-virelai-r8-physics-gated-delivery-share`

## 1. Objective

Add the smallest enforceable cybernetic loop around Duck:

> Virelai supplies one bounded investigative focus. Duck chooses an action and states its purpose. If Duck claims to test a rule, the prediction and scope are recorded atomically with that exact action. Virelai compares the resulting observation, persists the revision, and supplies the updated focus on the next cycle.

The controller governs participation and bookkeeping. It must not select Duck's action or assert a predetermined mechanic.

## 2. Non-goals for this rung

- Do not rewrite perception, continuity matching, lever typing, or the physics compiler.
- Do not add a Captain action phase.
- Do not force every ontology role to exist.
- Do not require predictions for ordinary navigation.
- Do not force Duck to accept Virelai's proposed focus.
- Do not optimize competition score before the acceptance trace works.
- Do not discard or mutate raw observations when a semantic hypothesis changes.

## 3. Required invariants

### Evidence invariants

1. Every environment action retains its exact before frame, action, after frame, result, actor, and timing.
2. A decision declaration cannot establish a fact.
3. A prediction is evaluated only against the exact interaction recorded in the same atomic envelope.
4. Comparisons are scoped. Remote effects, autonomous effects, and declared target effects remain separable.
5. Contradiction revises or weakens a claim; it never deletes the contradicting observation.
6. A semantic compiler fault cannot corrupt the raw journal.

### Control invariants

1. Duck chooses the action.
2. Virelai may reject a malformed decision envelope before execution; rejection consumes no environment action.
3. Virelai cannot substitute, reorder, or append actions.
4. Duck can propose a focus change with a reason.
5. A Virelai runtime fault enters an explicit degraded mode rather than silently pretending the contract was satisfied.

### Presentation invariants

1. One primary focus is visible per decision cycle.
2. At most two alternatives are shown.
3. Full focus text is sent when focus or evidence changes; otherwise a compact focus reminder is used.
4. Canonical evidence remains expandable by stable handles.
5. Display truncation is explicit and never truncates canonical storage.

## 4. Canonical schemas

Implement immutable, versioned records. Suggested module: `inference/framework/virelai_controller.py`.

### 4.1 `FocusState`

```python
FocusState(
    id: str,
    phase: str,
    question: str,
    status: str,
    opened_at_transition: int,
    evidence_refs: tuple[str, ...],
    applicable_rule_ids: tuple[str, ...],
    alternatives: tuple[str, ...],
    resolution: str | None,
    revision: int,
)
```

Allowed phases:

```text
CONTROL
AUTONOMY
INTERACTIONS
ROLE_DEPTH
PHYSICS_GRAMMAR
WIN_SEARCH
WIN_ANALYSIS
TRANSFER
REPRESENTATION_GAP
```

Allowed status values: `OPEN`, `ACTIVE`, `RESOLVED`, `DEFERRED`, `REOPENED`, `SUPERSEDED`.

Resolution must distinguish `ESTABLISHED`, `ABSENT_WITH_COVERAGE`, `NOT_APPLICABLE`, `CONTRADICTED`, and `INSUFFICIENT_EVIDENCE`. Absence is never inferred from silence alone.

### 4.2 `DecisionEnvelope`

```python
DecisionEnvelope(
    id: str,
    focus_id: str,
    purpose: str,
    actions: tuple[ActionSpec, ...],
    prediction: PredictionSpec | None,
    proposed_focus: FocusProposal | None,
    declared_at_transition: int,
)
```

Allowed purposes:

```text
EXPLORE
NAVIGATE
TEST_RULE
PURSUE_WIN
RECONFIRM_TRANSFER
```

Rules:

- `TEST_RULE` and `RECONFIRM_TRANSFER` require a prediction and explicit scope.
- `EXPLORE` and `NAVIGATE` do not require predictions.
- `PURSUE_WIN` requires a referenced win hypothesis or prior win record, but not a forced claim of certainty.
- Initial `TEST_RULE` support is one environment action per envelope. This removes ambiguity about which action produced the comparison.
- Navigation and known-plan execution may remain batched; each executed transition is still recorded separately.

### 4.3 `PredictionSpec`

```python
PredictionSpec(
    claim_id: str | None,
    expected: str,
    scope: ScopeSpec,
    falsifier: str | None,
)
```

Initial expected values: `CHANGED`, `UNCHANGED`, or a referenced mechanic-specific expected transformation. Avoid unrestricted prose as the only machine-readable expectation.

`ScopeSpec` may name a stable worldline, a witnessed region, a cell set, or the entire visible observation. It must record which representation was used.

### 4.4 `OutcomeComparison`

```python
OutcomeComparison(
    decision_id: str,
    transition_id: str,
    outcome: str,
    scoped_observation: dict,
    remote_observation: dict,
    autonomous_observation: dict,
    limitations: tuple[str, ...],
)
```

Allowed outcomes: `SUPPORTED`, `CONTRADICTED`, `INDETERMINATE`, `UNMATCHED`. `UNCHANGED` at the acted cell must not conceal a witnessed remote effect.

### 4.5 `RevisionEvent`

```python
RevisionEvent(
    id: str,
    parent_claim_id: str | None,
    resulting_claim_id: str | None,
    decision_id: str,
    comparison_id: str,
    revision_kind: str,
    explanation: str,
)
```

Revision kinds: `SUPPORTED`, `WEAKENED`, `CONTRADICTED`, `SCOPE_REFINED`, `EXCEPTION_ADDED`, `REPRESENTATION_GAP_OPENED`, `NO_SEMANTIC_CHANGE`.

## 5. Atomic action interface

Replace the ambiguous two-call intent/action pattern with one atomic interface inside the existing Python tool:

```python
action(
    [{'action': 'MOUSE', 'row': 12, 'col': 30}],
    decision={
        'focus_id': 'F-L1-004',
        'purpose': 'TEST_RULE',
        'prediction': {
            'claim_id': 'M-L1-002',
            'expected': 'CHANGED',
            'scope': {'worldline_id': 'W-L1-017'},
        },
    },
)
```

For ordinary movement:

```python
action(
    ['LEFT'],
    decision={'focus_id': 'F-L1-002', 'purpose': 'NAVIGATE'},
)
```

### Validation order

Before the environment callback:

1. Parse the envelope.
2. Verify the focus exists and is current, or validate an explicit focus-change proposal.
3. Verify purpose is allowed.
4. Verify the action is currently legal.
5. For a prospective test, verify prediction and scope are present.
6. Persist `DECISION_DECLARED`.
7. Execute exactly the declared action.
8. Persist `INTERACTION_EXECUTED` with the decision id.
9. Compare and persist outcome after the resulting frame is captured.

A validation failure returns a concise correction containing the active focus id and a valid minimal example. It consumes no environment action. Permit one correction within the same model turn.

### Compatibility policy

The controller experiment intentionally changes Duck's policy surface. In controller mode, legacy `action(actions)` is rejected with a migration example. In `off`, `observe`, and optional-tool modes, the existing signature remains unchanged. Ring 0 compatibility tests must continue to pass outside controller mode.

## 6. Focus controller

Implement a deterministic `FocusController` over the canonical world model, agenda evidence, win records, and coverage certificates. It emits one focus, not an unbounded question list.

### Phase routing

1. `CONTROL`: unresolved interaction mode, pointer control, or embodied control.
2. `AUTONOMY`: repeated changes not yet separated from intervention effects.
3. `INTERACTIONS`: untested reachable objects or action classes.
4. `ROLE_DEPTH`: an admitted semantic role has unresolved operational fields.
5. `PHYSICS_GRAMMAR`: mechanics exist but have unresolved conditions, state variables, reversibility, coupling, or counterexamples.
6. `WIN_SEARCH`: mechanics are sufficiently useful to guide novel-state search and no win has been observed.
7. `WIN_ANALYSIS`: a new win boundary exists without an integrated explanation.
8. `TRANSFER`: a new level has prior rules or win conditions awaiting provisional rebinding and reconfirmation.
9. `REPRESENTATION_GAP`: an observation cannot be expressed by the current grammar.

This ordering is defeasible. Incidental evidence may open a later-phase record immediately. A blocking dependency may return focus to an earlier phase. The controller must state why a phase advanced, skipped, or reopened.

### Focus scoring

Use deterministic ordinal priorities and evidence counts, not tuned confidence floats. Candidate ranking should consider:

1. required boundary work (`WIN_ANALYSIS`, `TRANSFER`);
2. unresolved prerequisite;
3. expected discrimination among live alternatives;
4. reachability and legality;
5. repeated unproductive coverage;
6. cost in environment actions;
7. age of unresolved contradiction.

Persist the complete candidate list and ranking reasons canonically. Display only the winner and at most two alternatives.

### Focus changes proposed by Duck

Duck may include:

```python
'proposed_focus': {
    'question': 'Determine whether B reverses A',
    'reason': 'This separates the two live shared-resource models',
    'evidence_refs': ['T-L1-011', 'T-L1-014'],
}
```

Virelai accepts, rejects, or defers the proposal using explicit structural reasons. Acceptance changes focus; it does not establish Duck's proposed mechanic.

## 7. Outcome integration

Port the already-tested experiment comparison path, but bind it to `DecisionEnvelope.id` and the exact executed transition.

Required decomposition:

- declared-scope change;
- changes outside declared scope;
- currently admitted autonomous-process changes;
- geometry or level boundary;
- missing or ambiguous identity;
- animation/interior-frame evidence when available.

The comparison updates:

- prediction record;
- mechanic support and contradiction references;
- applicability conditions;
- focus status;
- unresolved alternatives;
- representation gaps;
- next focus candidates.

No automatic update may discard the prior claim version. Claim lineage is append-only.

## 8. Prompt and presentation contract

### System prompt

Explain only the stable division of labor and action contract:

- Virelai supplies investigative focus and persistent evidence.
- Duck reasons and chooses actions.
- Every action needs a purpose.
- Prospective tests need a prediction and scope.
- Duck may propose focus changes.
- Observations outrank assertions.

Do not place the entire eight-phase doctrine in every turn.

### Per-turn context

On focus change:

```text
VIRELAI FOCUS F-L1-004 — INTERACTIONS
Question: Does Control A alter the striped region?
Relevant evidence: T-L1-008, T-L1-011
Known rule: none established
Alternatives: direct control; remote lever; coincident autonomous change
Valid purposes now: EXPLORE, NAVIGATE, TEST_RULE, or propose another focus
```

When unchanged:

```text
Virelai focus F-L1-004 remains active: does Control A alter the striped region?
```

After a prospective test:

```text
VIRELAI REVISION R-L1-003
Prediction P-L1-002: SUPPORTED in declared region.
Remote change: also observed in region [...].
Autonomous contribution: unresolved.
Mechanic M-L1-002 remains provisional; 2 supporting transitions, 0 contradictions.
```

After a win, the existing compact win/new-level card remains front and center, and focus becomes `WIN_ANALYSIS` before `TRANSFER` unless the explanation was already integrated.

### Token limits

- unchanged-focus reminder: target ≤60 model tokens;
- new focus: target ≤220 tokens;
- outcome revision: target ≤180 tokens;
- win/transfer card: retain the existing exact-tokenizer gate;
- every truncation declares omitted counts and expansion handles.

## 9. Persistence and telemetry

Write canonical files under each game's Virelai artifact directory:

```text
focus_states.jsonl
decision_envelopes.jsonl
outcome_comparisons.jsonl
revision_events.jsonl
controller_events.jsonl
controller_summary.json
```

Each record contains schema version, game id, level, transition boundary, stable ids, and evidence references.

`controller_summary.json` must report integer counts:

- focuses opened, resolved, skipped, reopened, and superseded by phase;
- declared, rejected, corrected, executed, and unmatched decisions;
- purposes used;
- predictions supported, contradicted, indeterminate, and unmatched;
- focus-change proposals accepted, rejected, and deferred;
- revisions later retrieved or referenced by Duck;
- transitions executed in degraded mode;
- prompt tokens attributable to focus/revision context;
- level wins and cross-level transfers.

Save the exact automatic context Duck received. Never grade adoption by searching the system prompt or echoed user prompt.

## 10. Failure behavior

### Duck contract errors

- Reject before environment execution.
- Return one concrete correction.
- Record the rejection.
- Do not consume an action.

### Virelai semantic failure

- Preserve the raw journal.
- Emit `CONTROLLER_DEGRADED` with the exception and affected transition.
- Present Duck with a short notice.
- Permit a native Duck action with purpose metadata so infrastructure failure does not destroy the run.
- Count every degraded action; a pilot with any unexplained degraded action fails the engineering gate.

### Latency

- Capture-path budgets remain unchanged.
- Controller update target: p95 ≤50 ms when using a cached model.
- Cold semantic compilation must occur only at declared boundaries and be reported separately.
- Per-turn controller rendering target: p95 ≤10 ms.
- Query/delivery latency is charged and reported; it is never hidden inside model time.

## 11. Build stages

### Stage A — Schemas and replay-only controller

Add the canonical records and deterministic phase router. Run them over fixed archived games without changing Duck or action execution.

Exit gate:

- byte-identical output across two replays;
- every focus and revision references existing evidence;
- no observation file changes;
- candidate lists remain bounded in the player view;
- human review on `vc33`, `ft09`, and `ls20` finds the selected focus reasonable given only prior evidence.

### Stage B — Atomic envelope in a sandbox fixture

Extend the Python action bridge in controller mode. Test every purpose, malformed input, stale focus, illegal action, focus proposal, prospective prediction, and batch rule.

Exit gate:

- zero environment calls for rejected envelopes;
- exactly one matching transition for every accepted single-action test;
- no accepted decision can diverge from the executed action;
- legacy behavior remains byte-compatible outside controller mode.

### Stage C — Scoped comparison and persistent revision

Join each accepted decision to its resulting transition and existing semantic model.

Exit gate:

- positive, negative, remote-effect, autonomous-effect, self-loop, geometry-change, animation, and identity-ambiguous fixtures pass;
- acted-cell unchanged plus remote lever effect is not classified as simple contradiction;
- every revision retains parent lineage;
- replay demonstrates a revision being retrieved after a later transition.

### Stage D — Prompt integration, no Kaggle yet

Add the stable system contract and bounded focus/revision blocks. Use scripted model responses to test correction and action execution.

Exit gate:

- exact tokenizer budgets pass;
- full focus appears once per change; reminders appear thereafter;
- no prompt echo is counted as Duck adoption;
- a malformed first attempt can be corrected and executed in the same turn;
- existing evidence and win/spawn delivery gates still function without duplication.

### Stage E — Local/API live quality gate

Run live or recorded-action fixtures on `vc33`, `ft09`, and `ls20`. Human-grade focus, scope, outcome, and revision against observable reality.

Exit gate:

- all accepted decisions match executed interactions;
- focus progression is explainable and does not assume absent roles;
- mechanics remain provisional where evidence is ambiguous;
- no raw evidence loss;
- no unexplained degraded-mode action.

### Stage F — Five-world Kaggle pilot

Use the same five worlds and budgets as the current gated-delivery run. Create a new variant, dataset, notebook, and run directory. Do not overwrite its parent.

Primary acceptance measures:

1. 100% of executed Duck actions have valid decision envelopes, except explicitly recorded degraded-mode actions.
2. 100% of `TEST_RULE` actions have prospective predictions and scopes.
3. Zero accepted decision/action mismatches.
4. Every comparison joins to exactly one transition.
5. At least one persistent revision is later referenced or used in every game with sufficient turns.
6. Win boundaries enter `WIN_ANALYSIS`; subsequent levels enter `TRANSFER` with the prior result available.

Secondary measures:

- rejection and correction counts;
- action, token, and wall-time overhead;
- phase progression;
- level-one and level-two completions;
- qualitative correctness of focus and revision;
- expansion calls and later reuse.

Score is diagnostic in this pilot, not the primary pass condition.

### Stage G — Full-suite experiment

Proceed only after Stage F passes the acceptance trace and human semantic review. Pre-register the matched control, game set, budgets, primary campaign measure (level-two-or-beyond completions), and non-regression floor before launch.

## 12. Test matrix

Minimum new tests:

```text
test_controller_schema_round_trip.py
test_focus_router.py
test_atomic_decision_action.py
test_scoped_outcome_comparison.py
test_revision_lineage.py
test_controller_prompt_delivery.py
test_controller_degraded_mode.py
test_controller_replay_determinism.py
test_controller_kaggle_preflight.py
```

Retain all existing observer, continuity, physics grammar, memory-card, win-capsule, and Ring 0 compatibility tests.

Fixtures must include:

- pointer control and embodied control;
- no-ego and no-counter worlds;
- action-independent ticking;
- local self-reaction;
- remote lever effect;
- opposing controls over a shared resource;
- changed and unchanged scoped targets with remote changes;
- same visible state with divergent outcomes;
- level win by Duck;
- level win recorded from another actor;
- next-level recurrence and genuinely new mechanics;
- missing semantic identity and representation gaps.

## 13. Evaluation law

The rung passes only when archived traces demonstrate:

```text
observation
→ structured focus grounded in that observation
→ Duck decision with explicit purpose
→ prospective prediction when validation is claimed
→ exact matched intervention
→ scoped comparison
→ persistent model revision
→ later retrieval or behavioral use
```

Automatic delivery alone is insufficient. Contract compliance alone is insufficient. A correct isolated prediction is insufficient. The revision must persist and become available to a later decision.

## 14. Immediate next action

Wait for and grade the currently queued gated-delivery pilot as the delivery baseline. In parallel, begin Stage A in a new sibling variant derived from `ring8-physics-gated-delivery`. Do not modify or repush the running Kaggle package. Stage A is replay-only and therefore cannot confound the active experiment.

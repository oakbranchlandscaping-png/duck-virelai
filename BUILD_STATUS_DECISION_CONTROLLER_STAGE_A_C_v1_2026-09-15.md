# Virelai Decision Controller — Stage A–C Build Status

**Date:** 2026-09-15  
**Variant:** `variants/ring8-decision-controller/`  
**Parent:** `variants/ring8-physics-gated-delivery/`  
**Live Duck integration:** deliberately unchanged

## What is now built

### Stage A — replay-only controller

- Immutable controller, focus, phase-contract, and versioned-rule records.
- Deterministic focus routing with one primary focus and no more than two alternatives.
- Operational purpose and completion obligation for every phase.
- First predictive family: a discrete state transition under named conditions.
- Exact evidence-reference validation.
- Canonical byte serialization and a real-archive replay compiler.
- Safe loading of persisted canonical world models.

Real replay outputs live in:

`runs/ring8-decision-controller-stage-a-replay/`

Two compilations of each of five archived world models produced byte-identical output.

| World | Primary focus | Rule versions | Alternatives |
|---|---:|---:|---:|
| ar25 | ROLE_DEPTH | 6 | 0 |
| ft09 | TRANSFER | 4 | 1 |
| lp85 | TRANSFER | 23 | 1 |
| ls20 | CONTROL | 0 | 0 |
| vc33 | TRANSFER | 26 | 2 |

These are honest outcomes of the admitted model. In particular, ar25's recorded
effects do not yet contain exact discrete before/after state edges, while ls20
contains no admitted mechanic in the compiled model.

### Stage B — atomic envelope in a sandbox fixture

- Immutable action, scope, prediction, focus-proposal, decision, and receipt records.
- Validation of active focus, purpose, legal action, prediction, and exact scope.
- `TEST_RULE` and `RECONFIRM_TRANSFER` permit exactly one action.
- `PURSUE_WIN` requires a win or win-hypothesis reference.
- Rejected envelopes execute zero environment actions.
- Accepted decision retries are idempotent and cannot execute twice.
- Pointer actions require `row` and `col` and retain the exact declared values.
- Ordinary navigation and exploration can remain non-predictive.

This is not yet connected to Duck's production `action()` function.

### Stage C — scoped comparison and append-only revision core

- Exact CELLS, REGION, WORLDLINE, and whole-visible-observation scopes.
- Missing worldline identity produces `INDETERMINATE`; scope is never silently widened.
- Declared-scope, remote, and admitted-autonomous changes are reported separately.
- An unchanged target with a remote lever effect is not mislabeled as a simple contradiction.
- Geometry and terminal boundaries remain indeterminate for ordinary rule testing.
- Supported and contradicted outcomes append a new rule version retaining its parent.
- Prior evidence and the parent rule remain unchanged.

Stage C's pure comparison core is complete. Runtime joining, animation-frame
integration, persistent JSONL files, and later-retrieval telemetry remain for the
production integration stage.

## Verification

Full inherited and new test suite:

`145 passed`

The new tests cover controller determinism, evidence integrity, bounded focus,
operational phase obligations, atomic rejection, legal actions, batching rules,
pointer actions, retry idempotency, exact scoped outcomes, remote effects,
autonomous decomposition, representation gaps, boundary handling, and revision
lineage.

## Next safe step

Human-review the three required Stage A cards (`vc33`, `ft09`, and `ls20`). Then
connect the already-tested envelope gate to a fixture instance of the real Python
action bridge behind an explicit controller-mode flag. Do not change the normal
Duck action surface yet. After that, persist decision, comparison, and revision
records and prove a later decision can retrieve a prior revision before adding
any prompt instructions or launching Kaggle.

## Subsequent production-bridge progress

The next safe step has now been implemented locally behind the new explicit
`controller` mode. Normal `off`, `observe`, and `tool` modes retain the legacy
action signature.

- The real sandbox accepts `action(actions, decision={...})`.
- Controller mode rejects a missing declaration, stale focus, illegal action,
  malformed scope, and invalid batch before calling the environment.
- Contract errors return one bounded correction; they do not expose arbitrary
  host exceptions.
- Accepted declarations are persisted before execution and retries are
  idempotent.
- The observer compares the declaration with the exact resulting transition.
- A mismatch becomes `UNMATCHED`; it cannot revise a rule.
- Comparisons and append-only revision events persist in per-game JSONL files.
- `controller_history` retrieves prior outcomes and revisions on later turns.
- The stable controller contract is in the system prompt only in controller
  mode. Each turn receives one full focus on change or a compact reminder when
  unchanged.

The full suite after the production bridge and scripted end-to-end acceptance
trace is **155 passed**. The trace proves focus → prospective decision → exact
action → scoped comparison → persistent revision → later Duck retrieval. This has not yet been
run against a live model or packaged for Kaggle. The next gate is local/API
quality review on `vc33`, `ft09`, and `ls20`; Kaggle remains downstream of that
gate.

## Live-pilot readiness

A fixed three-world live pilot and artifact-based evaluator now exist:

- `configs/controller-live-pilot.json`
- `tools/evaluate_controller_pilot.py`
- `LIVE_PILOT_DECISION_CONTROLLER_RUNBOOK_v1_2026-09-15.md`

The launch resolves exactly `vc33`, `ft09`, and `ls20`, one pass, sequentially,
with 40 actions and 20 minutes per world, and explicitly passes
`--virelai-mode controller`. The evaluator grades executed artifacts rather than
prompt vocabulary. The suite is now **157 passed**.

Execution is externally blocked on this host: `ARC_API_KEY` and
`OPENROUTER_API_KEY` are absent. An `OPENAI_API_KEY` is present, but substituting
an OpenAI model would not test the unmodified Duck model and is therefore not a
valid quality gate. No paid or misleading run was launched.

## Kaggle quality pilot launched

Because the exact Duck model is already available inside Kaggle, the same
three-world gate was packaged without substituting another model:

- local package: `kaggle/ring8-decision-controller-pilot/`
- private dataset: `stephenkaskin/taaf-duck-virelai-r8-decision-controller-pilot`
- private notebook: `stephenkaskin/taaf-virelai-r8-controller-pilot-share`
- worlds: `vc33`, `ft09`, `ls20`
- one pass, concurrency one, 40 actions and 1,200 seconds per world
- mode: `controller`
- submission disabled

The shipped bundle independently passed all **157 tests** and its 206-file
manifest verified exactly. Kaggle accepted notebook version 1 and reported it
`RUNNING`. The initial longer notebook slug was rejected before launch; shortening
the slug resolved the metadata limit, and the rejected attempt consumed no run.

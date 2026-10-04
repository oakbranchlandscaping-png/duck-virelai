# Build record — N4 G3 accounting and controlled stop

**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Source family:** `variants/ring9-cybernetic-gates/ARC3-Inference`

## Purpose

Make every bounded G3 run end in a legible controller product. A target roster that is merely
unfinished must never look like a successful G3 answer, and a server timeout must not reopen a
target or disappear into the generic solver note.

## Product contract

The source writes `<game>_g3_run_outcome.json` atomically and appends the same record to
`<game>_g3_run_outcome_history.jsonl`:

| Product | Meaning | G4 legal? |
| --- | --- | --- |
| `G3_COMPLETE` | Every eligible row is terminal and the aggregate inventory was accepted | yes, only when the machine has entered a G4 gate |
| `G3_BUDGET_STOPPED` | Action or time boundary stopped an incomplete sweep | no |
| `G3_SEMANTIC_RETRY_EXHAUSTED` | The compact reachability answer used its bounded repair allowance without satisfying the contract | no |
| `G3_BOUNDARY_DEFERRED` | Death, respawn, or level transition interrupted open G3 work | no |

Every record includes the pending target when one exists, the latest lifecycle evidence, state
counts for the full eligible roster, scheduler state, and the gate at emission. This is a
controller audit product; it is not Duck-authored semantic content.

## Integration points

- `record_gate_answer()` emits `G3_COMPLETE` after accepted `LEVER_INVENTORY` and after the machine
  has advanced to G4.
- The analyzer emits `G3_SEMANTIC_RETRY_EXHAUSTED` only for the one-time compact reachability
  checkpoint when its bounded repair loop stops.
- The solver emits `G3_BUDGET_STOPPED` or `G3_BOUNDARY_DEFERRED` in its finalization path while
  runtime state is still available.
- The artifact uses an atomic replacement for the current JSON and a JSONL history for replay.

## Validation

Focused N4 tests cover explicit bounded products, JSON reload equality, append-only history,
pending-target accounting, and completion-only G4 opening. The combined NAV/controller regression
suite passed: **115 passed**, with 14 pre-existing matplotlib/pyparsing deprecation warnings.

## Limits and next step

This slice is locally proven only. It has not yet been copied into a Kaggle package or confirmed in
a live `ls20` run. N5 must replay the source and packaged copy, inspect the new artifact, and grade
G3 accounting independently of G4 comprehension.

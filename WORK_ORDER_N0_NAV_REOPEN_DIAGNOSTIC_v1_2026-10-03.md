# N0 work order: NAV reachability reopening diagnostic

**Type:** `WORK_ORDER`
**Parent:** `BUILD_PLAN_NAV_FRICTION_REPAIR_AND_G3_CLOSE_v1_2026-10-03.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** completed; result recorded in
`DIAGNOSTIC_N0_NAV_REOPEN_E0005_2026-10-03.md`

## Question

Why did E0005/M0019 return from an accepted `PRESUMED_UNREACHABLE` answer to `REOPENED` after the
controller advanced to E0006?

N0 answers that question. It does not alter reopening policy, routing, prompts or gate ownership.

## Inputs

Read-only executed evidence:

- `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/ls20-9607627b_p0_gate_events.jsonl`
- `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/ls20-9607627b_p0_gate_answers.jsonl`
- `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/ls20-9607627b_p0_probe_outcomes.jsonl`
- `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/ls20-9607627b_p0_g3_target_ledger.json`
- `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/ls20-9607627b_p0_turn_ledger.jsonl`

Candidate source:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/virelai_gates.py`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/nav_terrain.py`
- existing NAV and scheduler tests

Executed-package comparison:

- `kaggle/ring9-g3-nav-terrain-ls20-v2/source-dataset/src/ARC3-Inference/`

Do not inspect downloaded game-engine implementations. Do not unpickle the executed solver.

## Build

1. Add a JSON-derived replay fixture containing the accepted E0005 certificate, its accepted
   explanation and the first E0006 transition after release.
2. Add diagnostic data to the reopening path in the test harness:
   - caller/reason;
   - evidence reference;
   - old and new target cells/version;
   - old and new contact-edge set;
   - old and new target-conditioned bridge-edge set;
   - old and new routing world/topology address;
   - whether the transition was counter-only, ego/ground exchange, or residual world delta.
3. Reproduce the transition under the executed package first, then under current candidate source.
4. State whether the source and package behave identically. If they diverge, preserve both results
   and identify the exact source difference.
5. Add focused diagnostic tests for each candidate trigger without changing their current policy:
   - target version increase with identical cells;
   - irrelevant new stood anchor;
   - relevant new contact or bridge;
   - counter-only transition;
   - residual world delta.

Instrumentation may be added to test helpers or a diagnostic-only pure function. Production runtime
behavior must remain unchanged in N0.

## Required result

Produce one signed diagnostic report containing:

- the exact reopening trigger observed in replay;
- the source method and condition that fired;
- whether the target-specific reachability question actually changed;
- whether the executed package and current source agree;
- the smallest justified N2 policy change;
- anything learned about the missing live `WALL` row, clearly marked as observation or hypothesis.

## Exit criteria

N0 passes only when:

- the accepted E0005 answer is represented before the replayed next transition;
- the replay reaches either `PRESUMED_UNREACHABLE` or `REOPENED` deterministically;
- if it reopens, the precise caller and changed input are named;
- the test distinguishes an irrelevant event from a target-relevant reachability change;
- no production behavior changed;
- focused diagnostics pass against the intended source tree;
- existing unrelated working-tree changes remain untouched.

Record the N0 finding before implementing N1 or N2. Because the parent plan has now been reviewed
and execution authorized, proceed to N1 only if N0 identifies the reopening cause unambiguously and
requires no change to the agreed gate semantics. Stop for review if the evidence remains ambiguous.

— **Sol**

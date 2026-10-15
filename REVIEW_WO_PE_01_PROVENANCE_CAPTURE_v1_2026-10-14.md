# Review: WO-PE-01 provenance capture

**Date:** 2026-10-14
**Reviewer:** Sol
**Accepted revision:** revision 4, based on `a925d7f`

## Verdict

Accepted. The slice records admitted, refused, executed and unattempted gated work in a deterministic, hash-chained audit journal. Probe executions join their exact admission events, answer rows distinguish submitted and controller-filled fields, every seal names its run, and journal failure does not change gameplay.

Revision 4 restores the established controller `_gate_probe_begin` call shape. The T2 regression found on revision 3 now passes, while the controller fixture's journal is byte-identical.

## Mac evidence

- Every revision-4 slice hash matched.
- The revision-3 Mac focused tiers passed: T0 `provenance` 76/76 and T1 `paper-evidence` 265/265. Revision 4's cloud rerun matched those counts.
- The manifest is exact at 975 tests.
- The revision-3 T2 run exposed one real controller-boundary regression and two sandbox-only `ps` failures.
- The controller regression passes on revision 4.
- The revision-4 T2 run gave 972 passed, 1 skipped and only the same two sandbox permission failures.
- Both process-cleanup cases passed outside the sandbox on revision 3, 2/2. Revision 4 changes only the controller probe call and does not touch the runner or those tests. A repeated external run on revision 4 was attempted, but automatic approval review disconnected before execution.

The accepted effective floor is therefore **974 passed, 1 skipped, of 975**.

## Scope confirmation

No schema v4, claims, keys, grader, report, scheduler, gate admission rule, action choice or golden changed. The next work order is WO-PE-02: absorb the validated journal into `world_model.json` schema v4 and report provenance completeness.

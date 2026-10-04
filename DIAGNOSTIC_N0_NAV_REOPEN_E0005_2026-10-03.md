# N0 diagnostic: why E0005 reopened

**Type:** `DIAGNOSTIC_REPORT`
**Parent:** `BUILD_PLAN_NAV_FRICTION_REPAIR_AND_G3_CLOSE_v1_2026-10-03.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** cause established; narrow correction built and locally validated

## Result

E0005/M0019 reopened because the production ledger increments an entity's `version` every time it
is observed, including a `STILL` observation, while the G3 reachability invalidator interpreted any
larger version as a target geometry or identity change. The target's cells did not change.

The smallest justified correction is to persist the target cells in the accepted reachability
certificate and compare those cells with the current observation. An unchanged target stays
terminal. A changed or disappeared target still reopens.

## Direct artifact observations

From `runs/kaggle-ring9-g3-nav-terrain-ls20-v2/artifacts/`:

- The accepted G3 `TARGET_REACHABILITY` answer concerns E0005/M0019, concludes
  `PRESUMED_UNREACHABLE`, cites the refused ACTION2 at transition 49, releases the target and says
  the conclusion is provisional rather than an inertness claim.
- G3 then advances to E0006/M0020.
- E0006's first probe is ACTION4 at transition 50. Its only grid change is two `11->3` cells, the
  already locked counter rewrite. There is no ego displacement or residual world delta.
- The exported target ledger ends with E0005 `REOPENED` and E0006 `IN_PROGRESS`.

These observations establish the ordering and the absence of a visible target/world change. They
do not themselves name the internal branch that reopened E0005.

## Source finding

The source completes the causal chain:

1. `EntityLedger.observe()` increments `old.version` for every matched component, including
   `relation == "STILL"`.
2. The executed G3 source iterated accepted reachability records after every scoped observation.
3. It reopened a record whenever the current hypothesis version exceeded the stored target
   version.
4. Therefore transition 50's observation of unchanged E0005 increased its bookkeeping version and
   satisfied the reopening condition.

The pre-change candidate `virelai_gates.py` and `entity_observation.py` are byte-identical to the
copies in the executed Kaggle source dataset. This supports applying the source explanation to the
executed artifact. The downloaded game engine was not inspected.

## Correction and test

G3 now stores `target_cells` in the pending and accepted reachability record. Observation-time
invalidation compares those cells with the current component cells. The focused regression creates
an accepted E0005-style record, observes a counter-only transition for the next target, confirms
that the entity version rises while its cells remain identical, and requires E0005 to remain
`PRESUMED_UNREACHABLE`.

This correction solves the observed false reopening. It does not complete N2. The global reopening
path for newly stood anchors still needs target-specific contact/bridge signatures so an irrelevant
new stand cannot reopen completed siblings.

## Missing WALL row

The run directly proves a refused movement edge and a routing limit. It does not directly identify
a visual component overlapped by a wall witness. The missing `WALL` row therefore remains
unresolved; it cannot be inferred from this reopening defect alone.

— **Sol**

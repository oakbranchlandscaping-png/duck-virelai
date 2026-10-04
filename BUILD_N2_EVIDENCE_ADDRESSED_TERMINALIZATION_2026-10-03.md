# N2 build record: evidence-addressed reachability terminalization

**Type:** `BUILD_RECORD`
**Parent:** `BUILD_PLAN_NAV_FRICTION_REPAIR_AND_G3_CLOSE_v1_2026-10-03.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** built and locally validated; packaged/live validation pending

## Goal

Keep an accepted `PRESUMED_UNREACHABLE` row terminal until evidence changes that target's actual
route question. A new frame, evidence reference, or stand elsewhere in the room is insufficient.

## Prior art retained

The Golden Captain recomputes reachability from its current lattice and treats the presumption as
reopenable when new ground, a yielding refusal, or a world-state change supplies a new experiment.
Ring 9 already computed richer target-conditioned `TerrainHypothesis` objects. N2 ports the
recomputation principle into the persistent hybrid ledger without importing Golden's architecture
or class-based passability assumptions.

## Built contract

Every accepted reachability record carries a `virelai-nav-reachability-signature-v1` containing:

- exact target geometry and its fingerprint;
- ego footprint, demonstrated bearings, current action surface and their law fingerprint;
- routing-topology epoch;
- masked world address for audit;
- reachable stands for audit;
- reachable target-contact edges;
- every equally nearest unspent target-directed bridge edge.

Only five inputs control reopening: target geometry, ego/action law, topology epoch, contact edges
and target-directed bridge edges. Reachable-stand growth and frame/world-address changes remain
visible in the record but do not reopen a target when its available experiments are unchanged.

The runtime recomputes each terminal target's signature after a yielded movement or relevant world
change. A residual non-counter, non-ego world delta advances the topology epoch. A disappeared
target is represented as changed geometry even though no new route hypothesis can be constructed.

Each reopening writes `virelai-nav-reachability-reopen-v1` with:

- target and evidence identity;
- the specific changed fields;
- old and new signature IDs;
- old and new values for every changed field;
- reachable-stand counts and world addresses for audit.

Historical records already marked `REOPENED` cannot capture a later invalidation after the same
target receives a new terminal certificate.

## Files changed

- `inference/framework/nav_terrain.py`: signature type, deterministic construction and relevant
  difference function.
- `inference/framework/virelai_gates.py`: signature creation, selective recomputation, durable
  reopen events, topology/action scoping and compact-card signature summaries.
- `tests/test_nav_terrain.py`: pure signature boundaries.
- `tests/test_nav_branch_foundations.py`: controller-led terminalization and reopening cases.

## Local evidence

The focused combined suite passes **105 tests**. New checks cover:

- counter-only `STILL` observations;
- an unrelated target probe;
- a new stand that expands the audit map away from the target;
- a new stand that creates a direct contact experiment;
- a previously refused edge that later yields;
- a residual world-state/topology epoch change;
- changed and disappeared target geometry;
- changed ego footprint and action surface;
- selection of the current terminal record after an earlier record reopened.

No package was created and no Kaggle or OpenRouter run was started. N3 is the next source slice:
reuse one current-state map across the ranked roster while preserving one disposition and one
target-specific certificate per object.

— **Sol**

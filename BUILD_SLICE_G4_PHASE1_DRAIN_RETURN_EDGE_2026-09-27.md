# Build slice: G4 Phase-1 drain — the pending-lever return edge (S1)

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Governing documents:** `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md`,
`BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1_2026-09-26.md`
**Source commits:** `495ded5` (classification), `f8a967e` (return edge and G4.3 guard); earlier
supporting fix `1bf09e0` (G4.3 seed). All authored by Claude, committed by the Director on the Mac.
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`
**Status:** offline green; live evidence pending (Kaggle checkpoint `ring9-g4-phase1-drain-v1`
launched 2026-09-27, see `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md`).

## Thesis

G4.2 must finish studying every confirmed lever alone — consecutive same-lever presses to a
period and a class — before any Phase-2 gate (G4.3 onward) may open.

Non-goals: Phase-2 sequences (ABA/ABC), couplings, reversal semantics, newborn-object
classification, NAV/HYBRID re-contact.

## The defect this repairs (code analysis, not a live observation)

`_LeverOrbitTarget` seeds both confirmed levers from the G4.1 anatomies and serves the first
unanswered one, so the second lever was always queued. But the generic `TargetRouter` skips any
gate that holds an active product. The moment G4.2 emitted `LeverOrbitSet` for the first lever,
the router advanced to G4.3 and never returned to G4.2 for the second. The queue existed; nothing
drove it back.

The router and journal are deliberately gate-agnostic, and that contract is preserved: the fix
lives in the machine, not the router.

## What changed (line numbers at `f8a967e`, `inference/framework/virelai_gates.py`)

| Change | Where | What it does |
|---|---|---|
| Phase-1 classifier | `_lever_class`, L111 | Classes one lever from its own orbit only: recurrence with period 2 → `TOGGLE`; period > 2 → `CYCLE`; recurrence without a usable period → `RECURRENT`; masked null at the observed state → `ABSORBING`; anything else → `UNCLASSIFIED`. |
| Classes on the product | `LeverOrbitSet` payload, L4184 | Adds `lever_classes` (completed lever → class). Products still accumulate; pending levers stay listed in `pending_lever_entities` (L4181). |
| Return edge | `CyberneticGateMachine._effective_target_id`, L4733 | If the active `LeverOrbitSet` still lists pending levers and the router picked a gate later than G4.2, return G4.2 instead. Otherwise defer to the router. |
| All dispatch through the edge | `_active_adapter` L4746, `gate_id` L4750, `gate_view` L4962 | Every site that resolves "the current gate" uses the return edge. `gate_view` was the second dispatch site, missed on the first pass and caught by the failing tests. |
| G4.3 guard | `_LeverLimitTarget._orbit_product`, L4313 | Raises `GateContractError("... Phase 1 is incomplete.")` if G4.3 is reached while any lever is pending. G4.3's tested endpoint, persistence and reversal code is otherwise untouched: it simply cannot fire until Phase 1 drains. |
| Seed fix (`1bf09e0`) | `_LeverLimitTarget._seed`, L4367–4375 | When the last orbit step omits `recurrence_to_state_index` / `observed_period`, derive them from the orbit's `state_sequence` instead of crashing. |

## Deviations from the build plan (stated plainly)

1. **No separate PHASE-1-COMPLETE event.** The signal is `pending_lever_entities == []` on the
   active `LeverOrbitSet`. Both the return edge and the G4.3 guard read that one field.
2. **Classifier choice.** The plan suggested `typing.classify_effect_channel`; the build classifies
   from stop disposition and period, which uses single-lever data only and needs no cross-lever
   information. Richer typing is a later refinement.
3. **Newborn append is not implemented.** The lever queue is seeded once from the G4.1 anatomies
   (`_LeverOrbitTarget._seed`, L3978–3997) and then frozen. New visual entities are recorded on
   each orbit event (`new_visual_entity_ids`, L4151) but are not appended to the queue. Plan exit
   criterion 5 is therefore **not met** by S1; it moves to S4 (newborn → G3 → G4.1 → queue).

## Tests (`tests/test_g4_limits.py`)

- `machine_at_g4_3()` fixture (L145) now represents a Phase-1-complete machine: both levers
  orbited, `pending_lever_entities: []`, `lever_classes` present.
- `test_completed_orbit_descends_entity_locally_without_discarding_pending_lever` (L279): after
  the first orbit, the gate stays G4.2 and the current entity is the second lever.
- `test_phase1_drains_both_levers_before_g4_3_opens` (L306): the full two-lever drain, then G4.3.
- `test_gate_routes_through_endpoint_inverse_and_reapplication` (L247): now asserts
  `PROBE_REQUIRED` on the second lever (all-levers-then-satisfy), not an early G4.3 result.

Suite at `f8a967e`: **374 passed** (Director-run, Mac). Independent re-run on a `git archive` of
the same commit (Python 3.12, cloud): **373 passed, 1 skipped**. The skip is
`test_adaptive_ego_coverage.py:203`, which needs a recorded ft09 artifact that is not in the source
package. The 16 focused G4.2/G4.3 tests pass.

## Evidence class (protocol §4)

- **Direct observation:** the code and tests above at `f8a967e`; the offline suite results.
- **Not yet observed:** any live run of the return edge. The first is the Kaggle checkpoint above.

## Carried risk

`inference/framework/g4_orbits.py` marks an orbit `BOUNDARY_INTERRUPTED` only on
`done`, `level_completed`, `game_over`, or `run_complete`. A reset that arrives mid-orbit without
one of those flags would reach the continuity check unguarded. On vc33 the known boundary (counter
extremum) arrives as `GAME_OVER`, so this is not expected to fire in the current checkpoint, but it
must be closed before NAV work.

— Claude, Alpha build seat, 2026-09-27

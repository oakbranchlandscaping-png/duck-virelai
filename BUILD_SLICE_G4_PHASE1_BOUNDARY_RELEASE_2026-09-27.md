# Build slice: G4 Phase-1 boundary release (S1 deadlock fix)

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Ruling implemented:** Director, 2026-09-27 — "cross level work is a separate gate." G4 records a
boundary interruption and releases the lever; a level transition closes the previous level's G4
study; resolving anything across levels belongs to G9.
**Defect:** `REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md` — the S1 hold kept G4.2 active for a
lever whose orbit a level transition had interrupted; no activation or answer was admissible, and
the run produced no action for ~90 of 120 minutes.
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`, based on `f8a967e`.

## Thesis

A lever whose G4.2 orbit is cut off by a boundary is recorded as interrupted and leaves Phase-1
pending, and a level transition closes G4 study for that level, so the machine always rests in a
coherent state instead of holding a gate with no legal move.

Non-goals: resuming an interrupted orbit (same level or across levels), any G9 behavior, ending the
Kaggle run early after a level close (that is a harness change; `fatal_failure` is an error path and
would mislabel a planned stop).

## What changed (`inference/framework/virelai_gates.py`)

| Change | Where | Effect |
|---|---|---|
| `_phase1_hold_reason(payload)` | module, L111 | One definition of "Phase 2 may not open": a lever pending, the level closed mid-study, or no lever completed. Used by both the S1 return edge and the G4.3 guard, so they cannot disagree. |
| Interruption state | `_LeverOrbitTarget.__init__` | `_interruptions` (per-lever record) and `_level_closed`. |
| `_current_entity` | `_LeverOrbitTarget` | Skips interrupted levers; returns nothing once the level is closed. |
| `assess` | `_LeverOrbitTarget` | Reports `SATISFIED` only when no lever remains to study. Previously any active `LeverOrbitSet` made G4.2 `SATISFIED`, even with a lever pending — the source of the contradictory card. |
| `record_outcome` → `_record_interruption` | `_LeverOrbitTarget` | On a `BOUNDARY_INTERRUPTED` orbit: records the boundary state, evidence ref, orbit snapshot and whether the level changed; a level change sets `_level_closed`; emits the product. |
| `_emit_orbit_product` (extracted) | `_LeverOrbitTarget` | Single emitter for answers and interruptions. New payload fields: `interrupted_lever_entities`, `unstudied_lever_entities`, `interruptions`, `phase1_status` (`IN_PROGRESS` / `COMPLETE` / `CLOSED_BY_LEVEL_BOUNDARY`), `level_boundary`. Interrupted orbits are kept out of `orbits`, so G4.3 never seeds from them. Product identity is unchanged when nothing was interrupted. |
| Card | `compact_gate_view` | `next_operation` becomes `G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9` after a level close, with the boundary, the interrupted levers and a plain rule telling Duck no gated operation exists. The unreachable `BOUNDARY_INTERRUPTED` pseudo-operation is removed. |
| Snapshot | `snapshot` | Includes `interruptions` and `level_boundary` for artifacts. |
| G4.3 guard / return edge | `_LeverLimitTarget._orbit_product`, `_effective_target_id` | Both read `_phase1_hold_reason`. The pending-lever message text is unchanged. |

## Tests (`tests/test_g4_phase1_boundary.py`, new)

Written first and shown to fail on `f8a967e` (4 of 4) before the fix:

1. `test_g4_2_is_not_reported_satisfied_while_a_lever_is_pending` — failed with `SATISFIED`.
2. `test_level_transition_interrupts_the_lever_and_closes_the_level_study` — failed: the lever
   stayed pending (the deadlock).
3. `test_same_level_boundary_releases_the_lever_and_phase2_opens` — failed: no product existed to
   record the interruption. Now the interrupted lever is released, the other lever drains, and G4.3
   opens with only completed levers.
4. `test_vc33_kaggle_v1_g4_2_replay_matches_the_record_and_closes_cleanly` — a replay of the real
   Kaggle run's ten G4.2 transitions (fixture `tests/fixtures/vc33_kaggle_v1_g4_2_segment.json.gz`,
   2.1 KB: grids, boundaries, recorded addresses, the row-0 mask footprint, Duck's real E0004
   explanation). Every replayed masked address, disposition and probe id matches the Kaggle record;
   Duck's real E0004 answer is accepted; the S1 edge moves to E0005. On `f8a967e` it failed only at
   the end (no interruption record); now it ends in the closed state with no admissible probe.

Suite: **377 passed, 1 skipped** (cloud, Python 3.12, on this change; the skip is the ft09 artifact
test). Mac confirmation owed before commit.

## Evidence class

- **Direct observation:** the code, the failing-then-passing tests, the replay's address fidelity.
- **Not yet observed live:** a boundary during a Kaggle run with this code.

— Claude, Alpha build seat, 2026-09-27

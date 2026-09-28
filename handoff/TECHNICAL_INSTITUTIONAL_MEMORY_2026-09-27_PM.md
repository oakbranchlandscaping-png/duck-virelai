# Technical institutional memory — Cybernetic Duck (evening, 2026-09-27)

**Date:** 2026-09-27, end of day
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27.md` (morning).
That file remains the reference for the S1 build, the dotenv key incident, and the ranked risks it
lists. This file does not repeat them.
**Builder method:** `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`, as amended by the rulings below
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## The rulings of the day (Director, 2026-09-27), in order

1. **Kaggle is the test venue** for the Duck. The OpenRouter rung is skipped.
2. **Cross-level work is a separate gate (G9).** CLICK lever G4 work moves to ft09.
3. **NAV is shelved.** Focus on CLICK.
4. **Guide the agent; do not plot every move.** A direct, explicit target, then Duck executes it as
   needed.
5. **G3 stays scripted; G4 becomes stated targets.** Then: **a stated target is the goal when
   possible.**
6. **Every friction sharpens an axiom.** Counters come in many forms; the target is the same: find
   it, label it, mask it, to keep lever data pure.

All six are recorded in `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md`, as axioms A1–A5.

## Where things stand

| Area | State | Record |
|---|---|---|
| vc33 S1 Kaggle run (v1) | Reviewed. First G3 closure on the exact model. The S1 hold was confirmed live, then deadlocked on a lever interrupted by a level change. | `REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md` |
| Boundary release | Committed `8cfb782`; later carried into G4-A | `BUILD_SLICE_G4_PHASE1_BOUNDARY_RELEASE_2026-09-27.md` |
| ft09 scripted Kaggle run (v1) | Reviewed. It stalled in G2: the counter ticks only on effective clicks, and the closure demanded a counter-only action. Precondition not met, so the G4 criteria are ungraded. | `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md` |
| G4.3 continuity defect | Found offline, and a prediction was filed before the ft09 output arrived. Resolved by G4-A, which puts confirmation inside each run. | `FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27.md` |
| **G4-A guided lever study** | **Committed `fcc7f11`.** G4 is a stated target, and G4.3 is retired from the ladder. | `BUILD_SLICE_G4A_GUIDED_LEVER_STUDY_2026-09-27.md` |
| **G2 under the counter axiom and the no-legal-move guard** | **Built, offline-green, written to the Mac; awaiting Mac pytest and commit.** | `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md` |
| Plan | v3 is current: three G4 targets; G2 is a stated target | `BUILD_PLAN_G4_CLICK_COMPLETION_v3_2026-09-27.md` |

## Commit ledger since the morning memory (from `.git/logs/HEAD`)

| Commit | What |
|---|---|
| `3ed0bf6` | Handoff: S1, the G4 Kaggle checkpoint, the dotenv key incident |
| `78d6755` | Review of the vc33 G4 Phase-1 drain Kaggle run v1 |
| `8cfb782` | Boundary release |
| `7778750` | ft09 Kaggle package `ring9-g4-ft09-phase1-v1` and its packager |
| `fcc7f11` | G4-A guided lever study; the continuity finding; plan v1 and v2 |
| *pending* | G2 counter axiom, legal-move guard, axioms doctrine, plan v3, this memory |

## Direct evidence added today

- **vc33 Kaggle v1:** 25 actions in about 30 minutes, then about 90 minutes of no action. E0004 was
  ABSORBING; E0005's sixth press completed level 1.
- **ft09 Kaggle v1:** 56 G2 clicks. 54 changed nothing at all (the bar did not tick either). Clicks at
  (36,36) and (44,36) each flipped a 6×6 control 9→8 and ticked the bottom bar 2 cells 12→11. Then
  about 2.5 hours with no legal move. The real 56 transitions are now a regression fixture.
- **Continuity:** offline simulation showed that mixed absorbing and toggle levers break the old G4.3
  after the drain, while all-toggle sets pass.
- **Test counts (cloud, full suite):** 377 at `8cfb782`; 384 at `fcc7f11`; 396 with the pending G2
  slice. Mac (protocol command, two suites ignored): 366 at `8cfb782`; 373 at `fcc7f11`; 385
  expected with the G2 slice.

## What a new builder must understand

- **Two modes coexist.**
  - *Stated targets* (G2 in CLICK worlds, and G4-A): a `GUIDED_ACTION` capability admits any valid
    action; the controller audits the record.
  - *Scripted gates* (G0, G1, G3, and NAV G2): the capability binds exact actions.

  `CyberneticGateMachine.validate_probe` handles both. Guided decisions accept `probe_token` plus an
  optional `intent`.
- **Axiom A2 is enforced at runtime.** `legal_move_status()` plus the `tool_agent` watchdog end
  gated work as a `controller_no_legal_move` failure after 3 consecutive illegal checks. A crashed
  game with that note is a controller defect to triage, not a model failure.
- **Declared ends still idle** until the deadline: a closed level, or a G4 slice not yet built. A
  clean planned stop is open harness work.
- **The Mac shell bridge from Cowork is broken** ("failed to create bridge sockets"). File staging
  and commit work. Staging refuses paths more than 7 folders deep, so copy run artifacts up first
  (for example to `virelai-review/ft09v1/`).

## Immediate handoff actions

1. Mac pytest (expect 385), then commit the pending slice with explicit paths.
2. Package `ring9-g4-ft09-guided-v1` from the committed ft09 package, at the new commit; same world
   and budget; preregister criteria per plan v3 §3.
3. Launch it on Kaggle (`-r skip`, wait for `ready`, push with the RTX Pro 6000 accelerator), then
   grade it. Route every friction through the axioms doctrine first.
4. Director-owned and still open: rotate the OpenRouter and ARC keys; clean up the G3-era datasets.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (see its 2026-09-27 amendment banner)
2. `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md`
3. this file
4. `BUILD_PLAN_G4_CLICK_COMPLETION_v3_2026-09-27.md`
5. `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md`
6. `BUILD_SLICE_G4A_GUIDED_LEVER_STUDY_2026-09-27.md`
7. `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md`, then `REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md`
8. `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md`
9. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27.md` (morning: S1, the key incident, risks)
10. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat, 2026-09-27

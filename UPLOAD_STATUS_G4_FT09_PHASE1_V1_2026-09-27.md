# Ring 9 G4 ft09 Phase-1 v1 upload status

**Prepared:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed; upload commands to be executed by the Director
**Status:** uploaded, ran, reviewed. **Result (2026-09-27):** Kaggle v1 ran 3 h 0 m and ended `cancelled` with 56 actions. It stalled in G2: the counter ticks only on effective clicks, and the old closure demanded a counter-only action. Precondition P not met, so the G4 criteria are ungraded. Receipt byte-identical. See `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md`; repaired in `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md`.

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-phase1-v1` (to be created, private)
- Notebook: `stephenkaskin/taaf-virelai-ring9-g4-ft09-phase1-v1` (private), accelerator
  `NvidiaRtxPro6000`, internet off
- Package: `kaggle/ring9-g4-ft09-phase1-v1/`; packager `tools/package_g4_ft09_phase1.py`
- Source commit: `8cfb7827cb94cb711c7924e877b41f3365765cde` (S1 return edge + boundary release)
- Package manifest SHA-256: `afd49db130204db758e08d48ba53340ae4da3aaca5c8e2d7abd4db460050e576`
- Source manifest SHA-256: `58ed52c308622580c0872b4a93989b4927a76dd3bb77949e56ae676c97787095`
- Model: `vrfai/Qwen3.6-27B-FP8` via local vLLM
- World: `ft09-0d8bbf25`, one pass, concurrency 1
- Budget: 200 environment actions and 10,800 seconds of behavior time after model setup
  (about 3¼ GPU hours with setup)
- Base: the committed `ring9-g4-phase1-drain-v1` package (its notebook machinery ran cleanly on
  Kaggle on 2026-09-27); not the G3-era packages, which still contain an API key.

## Why ft09 (Director ruling, 2026-09-27)

Cross-level work is a separate gate (G9). vc33's second lever completes level 1 when pressed, so
Phase 1 cannot fully drain there. ft09's controls historically return to an exact prior state
(period 2) without a level change, so the full drain (C2), the Phase-2 opening (C4) and G4.3
recurrence re-confirmation (C5) become observable. Plan of record:
`G4_3_FT09_CANARY_PLAN_2026-09-26.md`; its launch blocker (the G4.3 recurrence slice) is built in
`g4_limits.py` (`RECONFIRM_RECURRENCE`, `EXACT_RECURRENCE_RECONFIRMED`, `RECURRENCE_DIVERGED`).

## Budget reasoning

G0–G3 plus up to five lever orbits (period-2 returns take about two presses each), G4.1 answers,
then G4.3 re-confirmation (one extra period per lever plus endpoint/persistence/inverse probes):
roughly 60–90 actions. At the ~70 s per action measured on Kaggle today, that is 70–105 minutes,
plus answer turns. 10,800 s gives room to reach G4.3; 200 actions is headroom.

## Preregistered criteria

Frozen in `checkpoint-preflight.json` and `RUN.md`: precondition P (G3 closes on ft09 with at
least two levers), C1–C7 (drain, nothing pending, no invalidation, hold-then-open, G4.3
recurrence re-confirmation, honest recurrence language, no deadlock), and infrastructure checks
I1–I4.

## Risks stated before the run (hypotheses, not findings)

1. **ft09 has never been through the ladder live.** In the 2026-09-23 compatibility run it received
   zero actions because of the old deadline code. G0–G3 on ft09 are a precondition.
2. **Timer contamination.** ft09 has an independent ticker and a quiet opening, so G2 may close by
   the `COUNTER_NOT_OBSERVED_WITHIN_OPENING` route without a mask. If the ticker then changes the
   board during an orbit, no exact recurrence can appear and orbits would run until the budget
   ends. Criterion I4 grades this directly.
3. No early stop exists: if a level does close mid-study, Duck idles on the closed card until the
   deadline (coherently, but the time is spent).

## Verification before upload

`tools/verify_kaggle_package.py` 8/8 including byte-identity to `8cfb782`; notebook startup
executed with `tools/simulate_kaggle_preflight.py` in all three mount layouts (each reached
`G0-G4 execution receipt verified` with ft09 and the 10,800 s window); a tampered solver byte and
a wrong-world receipt were both rejected; committed-source suite 377 passed, 1 skipped (Mac: 366).

— Claude, Alpha build seat, 2026-09-27

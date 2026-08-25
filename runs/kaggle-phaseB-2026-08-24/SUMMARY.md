# Phase B — first hidden-set submission (Ring 0 baseline)

**Date:** 2026-08-24 · **Kernel:** stephenkaskin/duck-virelai-r0-dryrun (bundle v2, share template)
**Config:** frozen baseline (28 conc · 132 min/game · 540 min cap · 1 pass · Qwen3.6-27B-FP8)

## Score

**0.87** on the hidden set (leaderboard).

Provenance: Director-reported from the Kaggle leaderboard; no scorecard artifact
retrievable in-chamber. Claim type: MATCH on the Director's reading; the underlying
per-game breakdown is NOT_MEASURED (leaderboard shows aggregate only).

## Companion public number (run #1, same config)

all-25 mean 1.2225 · ex-ft09 1.2734 (runs/kaggle-phaseA-v2-2026-08-23/scores.json)

## Standing notes

- Public→hidden gap ≈ 0.35 at n=1. Single sample; Tufa's public 20-pass variance was
  ±0.4475 — no ring is judged on a smaller hidden-set delta than variance can defend.
- Runbook: on Submit, the dialog's default output-file pick can land on the hidden
  `.per_game_cards.pkl`; select `submission.parquet` explicitly. (Earlier drift
  hypothesis retracted — operator-side selection, not Kaggle behavior.)
- Post-submission quota meter: NOT_MEASURED pending Director's reading.

## Addendum (2026-08-24): the metric is a double max

- Director-reported (Tufa's own account): run-to-run score variance is high — driven by
  how lucky the model's first hypothesis of a world is — and **the leaderboard shows the
  top submission, not the average.**
- Code-verified in the frozen tree (`arc_agi/scorecard.py:241`, v0.9.8, the official
  calculator): within one submission, a game played N times scores
  `max(run.score for run in self.runs)` — **per-game best-of-plays**.
- Per-level formula: `min(115, (baseline/actions)² × 100)`, level-index-weighted.
  Wasted actions are penalized QUADRATICALLY — the subtraction thesis attacks the
  metric's square term directly.
- Consequence: 0.87 is one draw from a wide distribution, at 1 pass (1 draw/game).
  Tufa's 20-pass public 1.6002 vs 1-pass ~1.2 is the measured size of the
  best-of-passes effect. Ring E (n_passes within the 9h envelope) is the cheapest
  score lever on the board; `N_PASSES` is already a config variable in the committed
  Makefile (`environment.n_passes`).
- **Meter answer (Director, 2026-08-24): the submission rerun burned NO quota** —
  27.5h/30h remain (the 2.5h was Phase A interactive only). Submission reruns are
  quota-free; quota bounds only interactive validation runs. Daily submission =
  a free hidden-set draw at the leaderboard max.
- **Wall time (Director, 2026-08-24, corrected same day): the hidden-set submission ran
  2h21m** (an initial ~4h reading was corrected from the kernel page). Matches public
  Phase A (~2.4h) — the passes=3 ≈ 7h envelope math STANDS for when Ring E rejoins.
- **Director's sequencing ruling (2026-08-24): Ring E validation is DEFERRED — no quota
  spent proving a known-shape effect. Ring 1 (the Virelai insert) builds first; Ring E
  rejoins later as a cheap score booster.** Second dryrun submission (draw #2) launched
  same day.

## Draw #2 (Director, 2026-08-25): second hidden submission of the same frozen r0 scored **0.63**

Two draws of identical code: 0.87, 0.63. Mean 0.75, spread 0.24. Leaderboard keeps 0.87
(max rule). First direct measurement of hidden-set run-to-run variance; confirms the
public-paired-test gate on ring decisions is necessary, not cautious.

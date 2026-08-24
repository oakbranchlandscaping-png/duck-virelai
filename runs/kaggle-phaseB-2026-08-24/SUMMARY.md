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

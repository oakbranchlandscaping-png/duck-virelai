# WO-2 Tasks A+B (per Memo №2 §5.1–5.2) — instrument validation + token-budget baseline
**Date:** 2026-08-24 · **Chamber:** Cowork · **Inputs:** run #1 byte-file artifacts
(benchmark.json 926KB, intermediate_states.pkl 43MB sidecar, .per_game_cards.pkl),
fetched by the Director from kernel output; loaded via Tufa's own
`Benchmark.from_json` (which auto-attaches the sidecar).

## Task A — the instrument agrees with the official scorer. PASS, four checks.

| check | result |
|---|---|
| Transcribed scores.json vs byte-file `final_score` | **MATCH 25/25** (the Director-paste transcription was faithful) |
| `diagnostics.ARC_SCORER` recompute vs stored `final_score` | **MATCH 25/25**; means reproduce 1.2225 / 1.2734 exactly |
| `traces.py` independent RHAE reimplementation, per game | **MATCH 25/25** (first attempt failed on THIS chamber's adapter passing 'completed' instead of traces' `COMPLETED_LEVEL_STATUS`="COMPLETED" — corrected; not a traces defect) |
| significance machinery null check (run vs itself) | correct: paired-t flags `zero_variance`, permutation p=1.0 exact |

**Diagnostics numbers graduate from NOT_GRADED to instrument status** per §4.5.
Caveat kept: one run, one direction — a disagreement could still hide where both
implementations share an assumption; run #2 re-runs these checks for free.

## Task B — the "before" line (score at shared per-game token budget)

Scorer: ARC_SCORER via `_capped_score_fn`. Ex-ft09 via weight-0, per §4.2.
Curve data: `token-budget-baseline.json` (per-game step curves, 25 lanes, 13 nonzero).

| tokens/game | all-25 | ex-ft09(w0) |
|---|---|---|
| 5,000 | 0.111 | 0.116 |
| 10,000 | 0.200 | 0.208 |
| 20,000 | 0.200 | 0.208 |
| 25,000 | 0.478 | 0.498 |
| 30,000 | 0.623 | 0.649 |
| 40,000 | 0.911 | 0.949 |
| 50,000 | 0.947 | 0.986 |
| 60,000 | 1.150 | 1.198 |
| terminal (~68–71k) | **1.2225** | **1.2734** |

Sanctioned shared budget (`_min_tokens_per_game_budget`): 68,332 tok/game — ≈terminal
for a single run (ceiling binds only when comparing two benchmarks).

**Reading.** Half the terminal score is already earned by ~40k tokens; the final ~30k
tokens/game buys +0.31. Twelve of 25 lanes never score at any budget. The 10k–20k
plateau (0.200 flat) is a dead zone: 15k tokens/game spent with zero score accrual —
the blind-repeat/no-op window the ledger attacks. **Ring 1's target on this instrument:
move the curve left** (same score, earlier tokens); score-at-30k (0.623 all-25) is the
single number to watch.

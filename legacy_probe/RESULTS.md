# WO-1 Task C — v4 weave per-frame cost probe

**Date:** 2026-08-23 · **Where run:** Cowork cloud workspace (no GPU; Python 3.12, numpy/scipy from PyPI) ·
**What ran:** `weave_cost_probe.py` against legacy `virelai_v4` (read-only; weave/capture/perception units
called as-is per the instrument ruling) on real recordings: the two pinned canaries
(vc33-5430563c @51 nodes, ls20-9607627b @76 nodes) and a 450-record head of
`vc33-5430563c.virelai.0c401887…` for the 200/400-node depths.

Two quantities per prefix depth n:

- **T_full(n)** — the production per-turn path exactly as v4 runs it:
  `coverage_sweep.compute_current_weave_state(prefix)` = `ledger_from_capture` over the whole
  prefix + `weave_window` + `re_join` + `infer_roles`. Best of 3.
- **T_marginal(n)** — what a prefix-incremental variant pays for ONE new frame at depth n:
  single-node reconstruct + `scan_grid` + one `weave_edge(prev, now)`. Best of 5.

## The curve

| recording | n | T_full (s) | T_marginal (s) | worldlines | regions@tail |
|---|---|---|---|---|---|
| vc33 canary | 25 | 0.684 | 0.015 | 13 | 12 |
| vc33 canary | 51 | 0.700 | 0.014 | 11 | 11 |
| ls20 canary | 50 | 1.901 | 0.016 | 22 | 21 |
| ls20 canary | 76 | 3.337 | 0.016 | 23 | 21 |
| vc33 long | 50 | 1.480 | 0.014 | 28 | 16 |
| vc33 long | 100 | 4.561 | 0.016 | 60 | 31 |
| vc33 long | 200 | 4.354 | 0.018 | 32 | 32 |
| vc33 long | 300 | 5.254 | 0.017 | 32 | 32 |
| vc33 long | 400 | 7.492 | 0.017 | 32 | 32 |
| vc33 long | 450 | 7.802 | 0.017 | 32 | 32 |

## Reading

1. **The rebuilt-index curve is confirmed and located.** T_full grows with prefix length
   (0.68s → 7.8s across 25 → 450 nodes; prior measurement 0.08s@50 → 4.9s@400, same shape).
   The growth lives in the orchestration — `compute_current_weave_state` recomputes
   `ledger_from_capture` over the entire prefix every call (its own docstring: "same
   read-only prefix, same windowing") — not in the weave algorithms.
2. **The algorithms themselves fit the budget.** The marginal single-frame cost is flat
   14–18 ms at every depth measured: `weave_window` threads pairwise and append-only, and
   `weave_edge` is O(regions-at-tail). A prefix-incremental variant paying only marginal
   cost sits inside the 50 ms typical budget with room for tallies + digest.
3. Both timings are with numpy/scipy present. The Kaggle insert is stdlib-only by design;
   a Tufa-style connected-components pass measured separately at ~6 ms per 64×64 frame
   replaces `scan_grid` in that context.

## Recommendation (typed; decision returns to the directing chamber)

**Rebuild-fresh, with one transcription.** Rebuild the orchestration harness-side as a
persistent, per-edge incremental threader over segmentation-derived regions (nothing to
salvage in `compute_current_weave_state` — full-prefix recompute is its structure, not a
bug in it). Transcribe — new file, cited origin, per R-C — the one proven unit worth
carrying: `weave/edge.py`'s verb classifier (STILL/MOVE/RECOLOR/GROW/SHRINK/BIRTH/DEATH/
DEFORM over region pairs). Claim type for the numbers: **MATCH** against this container's
clock; **NOT_MEASURED** on Kaggle hardware.

## How this could be wrong

- The container's CPU is not Kaggle's; absolute times shift (the shape argument does not).
- The 450-node file is one game (vc33) with a stable ~32-region tail; a game whose region
  count grows with progress would raise T_marginal linearly in regions, not in prefix.
- `reconstruct()` cost was inside both clocks; if it is O(prefix) internally on other
  recordings, T_marginal would inherit a hidden prefix term not visible here.
- Best-of-N timing understates jitter; it is the right statistic for an algorithmic-shape
  question, not for a worst-case latency guarantee.

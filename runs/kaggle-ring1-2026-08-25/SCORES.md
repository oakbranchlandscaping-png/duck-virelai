# Ring 1 public A/B — scored 2026-08-25 (validated instrument, Tufa's scorer throughout)

Run: taaf-duck-virelai-ring1-share, 2026-08-24, 2h12m, 25 games x 1 pass, frozen config;
only variable = the Virelai ledger insert. Proof-it-ran: 504 [MAP] digests across all 25
transcripts; 46 menu-pruning events; node revisits to 17.

## Terminal score (per-game table in benchmark.json)

| metric | baseline r0 | ring1 | delta | paired verdict |
|---|---|---|---|---|
| all-25 mean | 1.2225 | **1.4833** | +0.26 | p=0.73(t)/0.78(perm) — NOT significant |
| ex-ft09 | 1.2734 | 0.9499 | −0.32 | ft09 (+14.29) carries the raw gain |

## Score at equal generated-token budget (the thesis instrument)

| tokens/game | baseline | ring1 |
|---|---|---|
| 10,000 | 0.200 | 0.581 |
| 20,000 | 0.200 | **1.411** (perm p=0.016) |
| 30,000 | 0.623 | 1.453 (p=0.25) |
| 60,000 | 1.150 | 1.481 |

Ring1 reaches ~98% of its terminal score by 30k tokens/game; the baseline needs ~65k.
The 10k–20k dead zone is GONE. Tokens per decided action: 465 → 258.

## Pre-registrations (Memo No.2 §2)

1. "Win concentrates in still-board games; ls20 stays blind" — **FAILED: ls20 won
   (+1.92, 60 actions, 37.9k tokens).** Per the pre-registration's own terms the
   mechanism story is wrong somewhere and the ls20 win is SUSPECT until its transcript
   is read. Filed for investigation, not celebrated.
2. "May reduce post-RESET replay (bp35/sp80 fixture)" — supported: bp35 +0.23,
   sp80 +3.88.

## The behavioral finding (the real result)

Total actions rose 69% (3,673 → 6,220) while total tokens FELL slightly. The ledger
made pressing cheap, and the model pressed more. Where exploration was the bottleneck,
that won (cd82 0→4.76, ft09 0→14.29, ar25, ka59, sp80). Where the baseline was already
efficient, extra pressing destroyed the quadratic action score: r11l completed the SAME
level in 335 actions vs 40 (4.76→0.24); tu93 6.08→0, sc25 5.39→0, tn36 2.53→0,
lf52 1.82→0. Gained 8 games, lost 6.

**Ring 1 revision target, exact:** keep the map, curb the pressing. The Memo No.3 axiom
block ("wasted presses ARE the score") + loud batch truncation + the §5 prose deletions
are aimed at precisely this failure.

## Cadence ruling applied (Memo No.2 §6)

Terminal paired delta does NOT clear public variance → ring1 is NOT promoted to the
hidden submission slot. Daily submissions stay on r0. Budget-score result is reported
as THESIS SUPPORTED per §4.3 (statistical tie on terminal, decisive win on budget).

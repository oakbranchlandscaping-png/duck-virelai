# Ring 1.1 (ontology implant) public A/B — scored 2026-08-26

Proof-it-ran: axioms in all 25 prompt logs; [MAP] live; 12 loud batch accounts;
12 RESET root-returns; `virelai` variable referenced in transcripts. 2h12m, config parity.

## Terminal (Tufa's scorer)

| arm | all-25 | ex-ft09 | actions |
|---|---|---|---|
| baseline | 1.2225 | 1.2734 | 3,673 |
| ring1 (map only) | 1.4833 | 0.9499 | 6,220 (+69%) |
| **ring11 (map+ontology)** | **1.0140** | **1.0563** | **5,189 (+41%)** |

Paired tests: ring11 vs baseline p=0.70/0.71; vs ring1 p=0.61. ALL terminal deltas are
statistical ties. **Ring11 does NOT clear the promotion gate; the submission slot stays
on r0.**

## Score-at-budget (the thesis instrument)

| tok/game | base | ring1 | ring11 |
|---|---|---|---|
| 20k | 0.200 | **1.411** | 0.469 |
| 40k | 0.911 | 1.481 | 0.708 |
| 60k | 1.150 | 1.481 | 1.014 |

Ring11 beats baseline at every budget but SURRENDERED most of ring1's early-token
blowout. Plausible mechanism (unverified): the five-beat walk spends the early budget
on systematic opening/probing rather than lucky rushes — comprehension-first delays
score accrual by design; on 1-pass luck-heavy scoring that reads as regression.

## Per-game vs baseline

Gained: ar25 +6.6 (2 LEVELS), re86 +6.3 (2 LEVELS), ka59 +1.2, cn04 +1.1 (first-ever
score), vc33 +0.1. Lost: tu93 −6.1, sc25 −5.4, r11l −3.6, tn36 −2.5, lf52 −1.8,
sp80 −0.6, su15 −0.5.

**Signals worth chasing:** (1) tu93 and sc25 have now lost in BOTH ring arms — 2-for-2
is above single-run noise; transcript reads owed. (2) Over-pressing improved (+69%→+41%)
but is not fixed. (3) The set of 2-level games changed completely across arms
(base: sc25,tu93 · ring11: ar25,re86) — luck-of-first-hypothesis dominates single runs.

## The real finding

At n=1 per arm, per-game variance swamps every design effect: three materially
different configs are statistically indistinguishable on terminal score. The only
significant result in the whole project remains ring1's score-at-20k (p=0.016).
**The next spend must buy statistical power, not another blind design iteration.**
Proposed: rerun baseline AND ring11 at n_passes=2 within the 9h envelope (~5h quota
each; diagnostics natively pairs across passes) — doubles draws per game per arm in one
run each. Decision then made on 2-pass paired tests + transcript diagnosis of the
repeat-losers.

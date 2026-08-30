# Ring 7 evaluation — the minimal hybrid vs the true bar

Run label: `duck-virelai-ring7` (verified; anchor f56bc27 in run git_status)
Run window: 2026-08-30 21:15:49–23:28:45 (2h12m55s)
Artifacts: downloaded to `~/Desktop/duck-virelai/runs/kaggle-ring7-run1/`
(NOTE: a second repo copy — see Housekeeping)
Evaluator: Cowork (hybrid seat); all transport numbers independently
recomputed from saved bytes vs saved payloads.

## Verdict, in one line each

- **Transport: PASS 25/25** — the 6.3 handshake ported to the pristine host
  flawlessly. Canonical marker sequence 25/25, exact report once in every
  first payload, max one copy across every request, zero failures, zero
  fallbacks, zero Captain faults.
- **Score: parity with baseline on all-25; clearly below it ex-ft09.**
  Ring 7 total 30.15 vs the baseline band 30.55–33.24 (two passes).
  Ex-ft09: ring 7 15.86 vs baseline 30.55/33.24 — on the program's own
  variance-controlled read, the minimal hybrid does not beat the bar.
- **Levels: 17 — the most of any arm ever** (r0: 15/13; ring6.3: 12), with
  only ONE probe-phase advance (vc33). Duck earned the rest itself.
- **The mechanism is now measured, and it is the probe tax.** Duck-phase
  actions were 3,657 — statistically identical to r0's 3,673. Duck with the
  card played at baseline's action budget and slightly above baseline's
  level competence; the probe's 1,251 actions ride on top of level 1 and the
  quadratic metric bills them in full. The state doc's §7 prophecy landed
  verbatim: "this is cheap because we are bad, and it gets expensive as we
  get good... a ring near baseline pays it in full and will need a shorter
  probe or none."

## The decomposed picture

| arm | total | ex-ft09 | levels | scoring | actions |
|---|---|---|---|---|---|
| r0 pass 1 | 30.55 | 30.55 | 15 | 13 | 3,673 |
| baseline-class pass 2 | 33.24 | 33.24 | 13 | 12 | 5,930 |
| ring 6.3 (degraded host) | 13.97 | 9.55 | 12 | 11 | 2,884 |
| **ring 7** | **30.15** | **15.86** | **17** | **13** | **4,908** |

Per-game vs r0: 5 up, 10 down. The ups are concentrated and large — ft09
0→14.29 (0→2 levels, won by DUCK in 85 post-probe actions off a 15-action
probe) and sc25 5.39→11.13 — both card-attributable reads. The downs are
broad and shallow-to-moderate (−0.4 to −6.1), and six of them carry the
probe-tax signature exactly: same-or-more levels, more total actions, lower
score. A few (tu93 −6.07, r11l −4.63) also show Duck itself playing slower
with the card than r0 played without it — not pure tax; worth transcript
reads.

Baseline variance context (from the two baseline-class passes): totals span
2.7 points and individual games swing ±6 between identical solvers. Ring 7's
−0.4 vs pass 1 is noise; its −17 ex-ft09 gap is not.

## Duck use — and the tripwire

First-turn use is strong (references in essentially every game's opening
turns, as in 6.3). But measured across the whole episode, model-authored
report references run at **15% of turns in analysis turns 1–5, collapse to
2–3% from turn 6, and reach 0% by turn ~36**. The card is behaviorally alive
for roughly five turns — attention decay sets in long before the ~30-turn
trim horizon even matters. **The U4 tripwire (BUILD_PLAN_POTENTIAL_UPGRADES
§U4) FIRED.**

## What ring 7 established

1. The handshake machinery is host-independent and reliable: two hosts,
   two runs, 50/50 transport.
2. The card does not degrade the good Duck's play (identical Duck-phase
   action budget, more levels) — the ring 1–5 fear does not transfer.
3. The card's benefit on the good host currently ≈ the probe's cost:
   score-neutral on all-25, negative ex-ft09, positive on levels.
4. The binding constraints are now, in order: (a) the probe tax — ~50
   actions/game billed quadratically; (b) five-turn card longevity;
   (c) method (predict/falsify) still absent, as in 6.3.

## Decision-tree branch (BUILD_PLAN §C): 14–30.5 — with amendments

The plan's branch-3 order was U1+U2 → U3 → 6.4 → U4-if-tripwire → 6.5 → U5.
Two evidence-driven amendments for the Director's ruling:

- **Probe-cost reduction jumps the queue alongside U3.** The tax is now the
  largest measured drag (~1,251 actions across 25 games on a quadratic
  metric). Candidates: shorter caps (1 life / ~20 actions), adaptive stop
  (CLICK saturation comes fast), or level-1-only-when-cheap policies. Note
  this INVERTS ring 6.4's direction: more probe throughput per second is
  only valuable if probe ACTIONS stay flat or fall.
- **U4 is now open** on its own tripwire: five-turn card life is the other
  half of why 17 levels didn't become score. Bounded, verified, overwritten
  projection — the v3.5 pattern, the narrow door.

U1+U2 (instruments) remain the first build regardless. ft09 and sc25 are the
new fixtures for "card-won games"; tu93 and r11l for "card-slowed games."

## Housekeeping (flagged to the Director)

- TWO REPO COPIES now exist: `~/Desktop/virelai-review/duck-virelai` (all
  ring 6.3/7 commits, anchors f36c149…a68a1d8) and `~/Desktop/duck-virelai`
  (download target of this run and home of the old PUSH docs). They must be
  consolidated before the next build or the anchor discipline splits.
- The mislabeled 17:32 run (`duck-virelai-ring-ontology`, pristine prompt,
  no ontology, no probe) remains quarantined; as a baseline-class sample it
  contributed the variance band used above, pending the Director confirming
  its provenance.
- Score remains a lagging indicator: this run's model deliverable — 17
  levels of world comprehension at baseline action budget — is the best
  belief-state result the hybrid has produced. The score gap is an
  accounting problem (probe tax) and an attention problem (five turns), and
  both are now measured, named, and owned by specific upgrades.

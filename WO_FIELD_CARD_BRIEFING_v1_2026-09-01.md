# WO — THE FIELD CARD IS A BRIEFING, NOT AN OPERATING CONTRACT

**Type:** `WO_FIELD_CARD_BRIEFING` · **Version:** v1 · **Date:** 2026-09-01
**Author:** Cowork (hybrid seat), capturing the Director's ruling of 2026-09-01
**Scope:** the Duck-Virelai hybrid only. The instrument ruling governs — score is the
goal, the Kaggle hidden set is the oracle, nothing here is precedent golden-side,
O-8 and O-9 stay open.
**Status:** specification. Nothing in it is measured. The committed tree outranks it;
a run's own artifacts outrank both.

---

## 0 · THE RULING

> "The problem is not the ontology or the probe data. It is the extra operating
> contract imposed on Duck. The report should be a short briefing for a player
> arriving after someone else explored the world. Duck remains the player. Virelai
> provides useful prior knowledge, not a second solver policy layered over it."
> — Director, 2026-09-01

The card's framing line becomes: **"This is what the Captain observed. Use it however
it helps you play."**

---

## 1 · THE EVIDENCE BEHIND IT — all measured from ring 7.2's own artifacts

| arm | total | levels | scoring | total actions | Duck-phase actions |
|---|---|---|---|---|---|
| r0 (frozen baseline) | **30.55** | 15 | 13 | 3,673 | 3,673 |
| ring-ontology (notecard only, no probe) | **33.24** | 13 | 12 | 5,930 | 5,930 |
| ring 7 | 30.15 | 17 | 13 | 4,908 | 3,657 |
| **ring 7.2** | **9.77** | 15 | 13 | 4,032 | **2,753** |

**Duck with the 7.2 report cleared the same 15 levels r0 needed 3,673 actions for, in
2,753 — 25% fewer.** The report works. The probe's action bill is what destroys the
score, because those actions are billed to level 1 and the metric is quadratic.

**Median human baseline for level 1 is 30 actions. Median probe was 53. In 17 of 25
games the probe alone spent more than the entire human budget for the level it was
billed to.**

Ratio of probe actions to level-1 baseline, on games that scored:

- **survived** — bp35 0.38 (**+0.24**), lf52 0.50 (−0.90), tu93 0.74 (−0.37)
- **destroyed** — sc25 1.36 (−5.39), sp80 1.46, lp85 1.59 (−1.99), su15 1.59 (−2.09),
  re86 1.88, r11l 2.41 (−4.29), ar25 2.34, ka59 2.64, sb26 4.00 (−2.64)

**And the relationship between probe length and card quality is inverse.** The 8-action
probe produced the best card in the run; the 53-action probe produced 16,851 characters
listing 22 counters, three of which are the background. Longer probes mint more regions
(the library counts appearances, not things), and the renderer has no compression that
survives volume. **Cheap probe and simple card are one decision, not two.**

*Absolute probe length correlates with score delta at r = 0.147 — near zero, and
confounded, because the longest probes ran on games neither arm scored. The ratio above
is the governing quantity, not the raw count.*

---

## 2 · THE CARD, SPECIFIED

### KEEP — eight sections, in this order

1. **What kind of world this is** — world type; honest `UNKNOWN` when unestablished.
2. **What you control and how** — control mode, and the per-action bearing table
   (`ACTION3 moves it by (0, -8)`), including actions observed to do nothing.
3. **Where the counter is and how it changes** — its site, and **both components,
   jointly and signed** (the fill and the empty), with its per-action rule.
4. **Which objects are levers** — addressed by coordinate.
5. **How each lever changes the world** — the affected regions and the measured change.
6. **Which levers control the same resource.**
7. **Any level win the Captain directly observed** — placed high, not buried; and its
   honest absence when there is none.
8. **Important mechanics that remain unknown** — with the tested/untested split kept
   distinct (a fully-tested quiet object is a finding; an untested one is a gap).

**Evidence status is retained** as an adjective on each claim — `[ESTABLISHED]` from
10/10 versus `[PROVISIONAL]` from 1/1. Counts, never confidences, never thresholds.

### REMOVE — the operating contract

- commands to run specific experiments;
- `Falsifier — repeat click X …` command lines (the *status* tag stays; the
  *instruction* goes);
- any prescribed next action or "BEST NEXT EXPERIMENT" ranking;
- the formal respawn doctrine block;
- structured level-transfer testing procedure;
- instructions to continue the Captain's investigation method.

**The `RESPAWN AND NEXT-LEVEL OPERATING RULES` block is static doctrine, byte-identical
across all 25 games; in lp85's report it is more than half the document.** It is
notecard material at most. Per the delivery law — subtraction never annotation — it is
deleted from the card in the same build, not relocated and re-argued.

---

## 3 · THE TARGET SHAPE, ALREADY WITNESSED

bp35's card, from **8 probe actions**, is close to the specification as-built:

```
WORLD AND CONTROL
  World type — UNKNOWN.
  Controlled object — Ego.
    ACTION3 moves it by (0, -8).
    ACTION4 moves it by (0, 8).
    No movement observed for ACTION6, ACTION7.

AUTONOMOUS COUNTER
  Counter strip [ESTABLISHED] — row 63, spans all 64 columns.
  Current state — class 0: 57 cells; class 15: 7 cells.
  Rule — after every observed action, class 0 shrinks and class 15 grows; 1 cell
    per action.
  Meaning — autonomous action budget/countdown is plausible; whether depletion costs
    a life or has another consequence is not yet observed.
```

bp35 is the **only game in ring 7.2 that gained score.** Its card carries the bearing
table and the two-counter reading — the fill and the empty as one signed pair — and no
operating contract.

---

## 4 · WHAT THIS SPECIFICATION DOES NOT FIX

**The background is elected as a counter and as a lever.** r11l's card lists Counters
B, N and P as `class 5, anchor (0, 0), ~3,3xx cells, bbox (64, 64)`, and Levers E and F
are the same object — the card instructs Duck to `click inside its footprint at (0, 1)`.
Ten further "counters" are near-identical `class 1, 2–5 cells, DEFORM, 3/3` rows,
almost certainly one thing recorded many times.

**That is rung-2 individuation (O-8, unruled) and the figure/ground reflex, upstream of
the renderer.** Removing operating contract does not touch it. The ≤15-action probe cap
suppresses it incidentally — short probes mint few regions — so the cap is carrying two
jobs and should not be relaxed on the assumption it only buys actions.

---

## 5 · GATES

- **Probe cap ≤ 15 actions**, hard. Median level-1 baseline is 30; the surviving games
  sat under 0.75 of it.
- **A zero-probe control arm** in the same campaign. The best arm on record has no probe
  (`ring-ontology`, 33.24). Any probe must be charged against *that*, not against
  ring 7.2, or the comparison flatters it.
- **One variable per arm.** Ring 7.2 moved two — the semantic machine and the notecard —
  so attribution between them is NOT_MEASURED and cannot be recovered from that run.
- **`wc -w` on the card renderer must fall.** A build that adds sections and grows the
  card has replaced nothing.
- **≥ 2 runs per arm** (RULING.md). r0 currently has one sample; ring 7.2 has one.
  Nothing in this campaign has a measured noise floor.
- **Exact-once must be re-verified across the whole transcript,** not the first payload
  only — see the evaluation's FIDELITY section.

---

## 6 · OWED

- **Director's confirmation on the falsifier reading.** This document keeps evidence
  status tags and deletes only the falsifier *commands*. If both were meant, say so and
  the status tags go too.
- **The cap discrepancy** — r0's reported scores reproduce exactly at `min(100, …)`;
  ring 7.2's reproduce exactly **uncapped**. It costs 0.61 points today and becomes
  large the moment an arm beats the human baseline on several levels, which is the
  target regime. Settle it against Kaggle's own scorer before the rehearsal submission.

*Filed 2026-09-01. Specification only. Behaviour is measured at the Director's terminal.*

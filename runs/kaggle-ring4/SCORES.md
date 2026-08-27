# RING 4 — SINGLE VALIDATION RUN, READ
**Date:** 2026-08-27 · **Chamber:** Cowork (interim) · **Scorer:** Tufa's throughout
**Run:** `taaf-duck-virelai-ring4-share`, 25 games × 1 pass, 2h 12m 19s, 3,436 actions.
**Cadence:** one-run feedback — directional, never a promotion or a kill.
**Counting discipline:** all event counts from `transcripts/` (the complete record).

## Every fixture passed. The arm scored worst. Both are true.

### Fixtures

| # | fixture | ring3 | ring4 | verdict |
|---|---|---|---|---|
| F1 | card called and rendered | n/a | **82 renders in 23/25 games, zero errors** | **PASS** (pre-reg ≥15 games) |
| F2 | raw-dict traversal falls | `virelai.get` **987** · `virelai['` **311** | **112** (−89 %) · **143** (−54 %) | **PASS** |
| F3 | schema fumbling falls | `is an int, not a` **29** · `TypeError` **50** | **3** (−90 %) · **12** (−76 %) | **PASS** |
| F4 | prompt shrinks | 807 / 2,720 w | 668 / 2,626 w | **PASS** (pre-verified) |
| F6 | negative control | — | GAPS names absences correctly: *no counter sealed* ×49, *no lever witnessed* ×22, *no ego expected — CLICK world* ×13, *no ego sealed* ×12 | **PASS** |

**The thesis this ring was built to test is confirmed: given a rendered dossier, the model
stops spelunking the raw dict.** Raw traversal fell by an order of magnitude and the
schema errors it caused fell with it. The splice worked in production — not one
`NameError`, not one exception, across 25 games.

**Acceptance criterion (FRICTION-004's own): *does this change what the solver does on at
least one game?* — YES, and on nearly all of them.** Total actions **4,768 → 3,436
(−28 %)**, the lowest of any arm and **below the frozen baseline's 3,673 for the first time
in the program**. tu93 alone went 613 → 60 actions.

### The seven-arm table

| arm | all-25 | ex-ft09 | median | actions | scoring | 2-level |
|---|---|---|---|---|---|---|
| baseline r0 | 1.2220 | 1.2729 | 0.01 | 3,673 | 13 | 2 |
| ring1 | 1.4840 | 0.9504 | 0.05 | 6,220 | 14 | 1 |
| ring11 | 1.0148 | 1.0571 | 0.00 | 5,189 | 11 | 2 |
| ring2 | 1.3636 | 1.1829 | 0.00 | 4,830 | 10 | 4 |
| ring25 | 1.2192 | 1.2700 | 0.39 | 4,495 | 14 | 3 |
| ring3 | 0.9856 | 0.8283 | 0.00 | 4,768 | 12 | 1 |
| **ring4** | **0.8340** | 0.8688 | 0.00 | **3,436** | 11 | 1 |

Lowest all-25 of any arm — **but ex-ft09 IMPROVED on ring3 (0.8283 → 0.8688)**, and ft09
alone swung 4.76 → 0.00. ft09 is the program's known variance monster (per-pass range
0–47.6). Much of the all-25 drop is that one game. Per-game: **gained 7, lost 5, unchanged
13**. Gains: tn36 +2.92, re86 +2.78, ls20 +1.06, ka59 +0.86, tu93 +0.73. Losses: ft09
−4.76, r11l −4.76, ar25 −2.44.

**Card usage vs outcome** (suggestive only — card usage is not random):
`cards ≥ 4` (n=11) meanΔscore **−0.01**, meanΔactions **−71**, scoring 1/11 ·
`cards = 0` (n=2) meanΔscore +0.37, meanΔactions −269, scoring 2/2.

## Two findings that steer the next ring

### D3 — the model SLICES the card, and GAPS is last

`card[:` appears **98 times across 20 games**. Of 82 renders, **only 64 carry `=== GAPS`**
in the record. The card's median render is **3,478 chars (max 12,101)** and the reader
cuts it. **The section carrying typed silence is the section being discarded, because it
is at the bottom.**

Ordering is not cosmetic under a reader who slices. GAPS belongs immediately after
SITUATION, or the card needs a length the reader will not cut. This is a design defect in
Ring 4, found by Ring 4, and it is cheap to fix.

### The pre-registered risk FIRED — and the card is what exposed it

DESIGN §6 filed it in advance: *"a false ego seal, now rendered with evidence, is MORE
persuasive rather than less because it looks measured."*

The run rendered **76 distinct ego seals across 12 games**, including:

```
EGO-SEALED  135-cell class-0 at rows 11-25 x cols 11-25      (and 4 more 135-cell)
EGO-SEALED  144-cell class-5 at rows  7-23 x cols 25-41
EGO-SEALED   80-cell class-9 at rows 12-15 x cols 44-63
EGO-SEALED    1-cell class-0 at rows 15-15 x cols 15-15      (and 11 more 1-cell)
```

A 135-cell region and a 1-cell speck cannot both be the player, and there are seventy-six
of them. **This is not a Ring 4 regression — Ring 4 changed nothing in the weave or the
seal.** Ring 3's digest announced each seal once, so we counted 8 and believed the ego set
was small. The card renders the *whole set*, every time. **The defect was always there;
the card is the first instrument that could see it.**

That is the ring earning its keep as an instrument even while the arm scores worst.

`DRAIN-SEALED`: **0 renders, 0 games** — third consecutive ring with zero drain seals.
`COUNTER-SEALED`: 12 renders / 3 games. `LEVER-WITNESSED`: 609 renders / 16 games.

## Typed

- Fixture counts, arm table, per-game deltas, seal inventory: **MATCH** — read from the
  complete transcripts and `summary.txt`.
- "The card caused the action drop": **NOT_MEASURED.** n=1 against a 0.87/0.63 spread; and
  card usage is not randomised across worlds.
- "The 76 ego seals are false": **CONFIRMED on inspection** for the 135-cell, 144-cell,
  80-cell and 1-cell class-0 entries — no statistics required.
- `falsif` appears 3,757 times but the system prompt echoes the word twice per turn;
  the model's own use is **NOT_SEPARATED** from prompt echo. Do not cite that number.

## How this could be wrong

- The 82/64 GAPS gap could be transcript-writer truncation rather than model slicing,
  though `card[:` × 98 is direct evidence of slicing.
- ft09's −4.76 may be pure variance; ex-ft09 tells a different story from all-25 and both
  are reported.

# RING 3 — SINGLE VALIDATION RUN, READ
**Date:** 2026-08-27 · **Chamber:** Cowork (interim) · **Scorer:** Tufa's, throughout
**Run:** `taaf-duck-virelai-ring3-share`, 25 games x 1 pass, 2h 12m 55s, 4,768 actions,
1.61M tokens · **Cadence:** one-run feedback (2026-08-26) — directional feedback and
per-game shapes, never a promotion or a kill.

## THE HEADLINE IS NOT THE SCORE

**Prove-it-ran, run first per METHODOLOGY §5, found that three of this ring's five
sealed reads never reached the model — and that the same was true in ring25.**

| announcement | ring25 | ring3 |
|---|---|---|
| `[EGO] sealed:` | **0 events / 0 games** | **0 events / 0 games** |
| `[COUNTER] sealed:` | **0 events / 0 games** | **0 events / 0 games** |
| `[DRAIN] sealed:` | n/a | **0 events / 0 games** |
| `[LEVER] sealed:` | 0 | 8 events / 4 games (ka59, r11l, sp80, tn36) |
| `[FRONTIER] The win lives…` | n/a | 30 events / 8 games |

**The mechanism ran; the delivery dropped it.** `[EGO] at rows …` **position** lines
appear in 6 games (ar25, bp35, ka59, sk48, sp80, tu93) — those lines render only for a
sealed ego. So egos sealed in at least six worlds and **not one seal announcement was
delivered.** ls20's snapshot carries a sealed counter; no counter announcement was
delivered anywhere.

The discriminator is exact: **per-turn content survives, one-shot notes die.** The
position line is regenerated every turn and reaches the model. The seal note is drained
and cleared by whichever per-press digest fires first, and `solver.py:644`
(`final_payload = dict(executed_payloads[-1])`) keeps only the last press of a batch.
Directional runs are batched, so ego and counter seals land mid-batch and are discarded.
Lever witnesses fire on clicks, often single-press, which is why they survive.

**This is D1, logged as CONFIRMED-in-code / NOT-observed-live on 2026-08-26. It is now
observed live.** Ring 2.5's announce-delay refinement makes it worse by design: delaying
an announcement one press past its evidence increases the chance it lands mid-batch.

**Self-correction owed on the record.** The ring25 read reported "ALL fixtures pass …
5 ego seals." Those seal strings are **zero** in ring25's own prompt logs; ring25 has 18
`[EGO] at rows` position lines across 4 games. The earlier read almost certainly counted
position lines as seals. Ring 2's "counters sealed live on 4 worlds" needs re-checking by
the same method before it is relied on again. This chamber's first grep pass made the
identical error — counting contract vocabulary from the system prompt as live events —
and caught it only because the counts were suspiciously constant across all 25 games.

## Pre-registered fixtures

| fixture | verdict |
|---|---|
| CLICK: `[LEVER]` seals with sane targets/effects; `[FRONTIER]` lines present | **PASS** — 8 lever seals / 4 games, 30 frontier lines / 8 games |
| NAV+fuel (ls20): `[DRAIN]` seals on the bar | **FAIL** — zero drain seals in any of the 25 games |
| Counter worlds: `[DRAIN]` must NOT seal on counter-sealed regions | **VACUOUS** — nothing sealed; the exclusion control proved nothing |
| cn04: frontier-led digest reduces wandering (526 actions) | **PASS** — 526 → 325 actions, and cn04 **scored for the first time** (0.00 → 0.43) |

A failed fixture is a finding: the ego-coupled drain seal did not fire once, on any world,
including the world it was built from.

## The six-arm table (public, 1 pass each, Tufa's scorer, all 25 games common)

| arm | all-25 | ex-ft09 | median | actions | scoring games | 2-level | tokens/k |
|---|---|---|---|---|---|---|---|
| baseline r0 | 1.2220 | 1.2729 | 0.01 | 3,673 | 13 | 2 | 1,708 |
| ring1 | 1.4840 | 0.9504 | 0.05 | 6,220 | 14 | 1 | 1,604 |
| ring11 | 1.0148 | 1.0571 | 0.00 | 5,189 | 11 | 2 | 1,660 |
| ring2 | 1.3636 | 1.1829 | 0.00 | 4,830 | 10 | 4 | 1,669 |
| ring25 | 1.2192 | 1.2700 | **0.39** | 4,495 | 14 | 3 | 1,668 |
| **ring3** | **0.9856** | **0.8283** | 0.00 | **4,768** | 12 | 1 | 1,614 |

Ring 3 is the lowest arm on all-25 and on ex-ft09, and the actions trend
(6,220 → 5,189 → 4,830 → 4,495 → **4,768**) **rose for the first time**. That was
pre-registered by this chamber as the falsifier that score-blindness would not excuse.

Terminal deltas remain statistical ties at n=1 against a measured 0.87/0.63 hidden spread.
**No promotion. r0 keeps the daily slot.**

## Per-game shapes (ring25 → ring3): gained 6, lost 9, unchanged 10

Gains: ft09 0.00→4.76 · tu93 3.31→5.06 · ar25 1.23→2.78 · tu93 and ar25 both with
**fewer or equal** actions on ar25 (147→119). cn04 0.00→0.43 at 526→325 actions.
Losses: dc22 4.76→0.00 · re86 3.72→0.00 (and 2 levels → 0) · tn36 3.57→0.65 ·
sp80 1.95→0.00.
Action blowouts: tu93 110→613 (+503, still scored highest) · sk48 396→699 (+303, scored 0)
· tr87 27→203 (+176, scored 0).

The blowouts are the shape to watch: the frontier line names how much is untried, and on
three worlds the model appears to have taken that as licence to spend. That is Ring 1's
+69% failure mode returning through a new surface.

## The finding that steers Ring 4

**The consumer exists and is working the data hard.** Across the 25 transcripts the model
made **987 `virelai.get(...)` calls**, plus `.keys()` and `.items()` traversals, and it
inspected the snapshot in every game. Four articulation systems in this program's history
died for want of a consumer; this one has one, measurably.

**And it is failing on the schema.** The transcripts carry repeated errors of the form
`virelai['states'] is an int, not a list` / `not a dict` — the model guessing at the shape
of a raw dictionary. That is the argument for the field card stated as measurement rather
than theory: the model is already trying to read the library and is spelunking a dict to
do it.

## Typed

- Announcement counts, fixture verdicts, arm table, per-game deltas: **MATCH** (read from
  this run's prompt logs, transcripts and summary.txt; scorer is Tufa's throughout).
- Attribution of the missing announcements to D1: **CONFIRMED** in code and consistent
  with the per-turn/one-shot signature. A direct transcript of a note raised mid-batch and
  absent from the next prompt was **NOT_MEASURED** — the batch index is not recorded.
- Ring 2 / ring 2.5 seal claims: **NOT_GRADED** pending a re-read by announcement text.
- Whether ring3's capabilities help or hurt: **NOT_MEASURED.** Three of its five sealed
  reads never reached the model, so this run did not test what its MANIFEST describes.

## How this could be wrong

- Prompt logs may not capture every rendered prompt; if seal notes were delivered on a
  path these logs miss, the delivery finding weakens. The position-line contrast argues
  against that — both ride the same digest string.
- The 6-gain/9-loss split at n=1 against this variance is not a per-game verdict.
- ls20's snapshot counter may be a different region from the motion-coupled drain ring2
  identified; that was not chased here.

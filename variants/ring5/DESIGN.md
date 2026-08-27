# RING 5 DESIGN — THE EGO SEAL, REPLACED
**v1 · 2026-08-27 · Chamber: Cowork (interim)**
**Ruling basis:** Director 2026-08-27 (Ring 5 fixes the ego) · instrument ruling (the
hybrid may adopt conventions without ruling them) · harvest:
`claude/ego-and-win-harvest-2026-08-27.md`.
**Adopted, named, non-precedential:** `virelai_v4/weave/ego_field.py`'s three conjuncts.

## 0 · The one variable

**The ego seal's evidence class.** Nothing else changes: no new record, no prompt edit,
no card change beyond what the seal already feeds.

## 1 · The defect, stated precisely

Ring 2.5 ported `ego_read`'s OWN-STREAM bearing test — *MOVEd under >=2 directional
labels with >=2 bearings* — which `STATE_OF_THE_CAMPAIGN_EGO` §2 grades:
*"It is correct and it is the wrong grain."*

Measured in ring4: **76 distinct ego seals across 12 games**, including five 135-cell
shapes, a 144-cell, an 80-cell, and twelve 1-cell class-0 specks.

And the sweep named what we actually shipped. Golden-side there are TWO sets:
`nav_target.sealed_egos` — *"deliberately the wider set"*, pre-verdict — and
`verdict_egos(verdicts)`, what survives the seal. **We ported the candidate generator
and never built the filter.** 76 is the wide set, uncensored.

## 2 · The mechanism — three conjuncts, no threshold

A worldline A seals EGO iff there EXISTS a partner B such that:

1. **A CROSSING.** On >=1 edge, cells A gained are cells B lost, both persist across
   that edge, and the exchange is clean — nothing appeared from nowhere or vanished.
2. **THE EXCHANGE DEPENDS ON WHICH BUTTON.** Two observed action labels under which A
   gained DIFFERENT cell-sets from that same B. A set inequality, not a rate.
3. **A IS DISPLACED AND B IS NOT.** Across the window A's footprint occupies more than
   one distinct anchor (min row, min col); B's occupies exactly one.

Why 3 exists, in the source's words: *the exchange record is symmetric by construction*,
so 1 and 2 are satisfied identically by BOTH endpoints and **the ground types EGO
alongside the figure**. *A relation is symmetric; a role is not, and the asymmetry
always comes from outside the relation.*

Three laws carried verbatim:
- **Anchors are read from the footprint series, NOT the MOVE verb** — a figure that
  changes shape as it crosses produces no MOVE at all. Our current seal is built
  entirely on MOVE, so it cannot see that case and over-fires on others.
- **More than one anchor, NO MINIMUM COUNT.** "Two is displacement and so is twenty. A
  minimum would be this module's first threshold and there is not one."
- **When BOTH partners are displaced, neither types from that crossing.** Two figures
  passing through each other are two figures — passed over in silence, never resolved
  by size, class or position.

## 3 · Why this is affordable

`Worldline.at = {edge_idx: footprint}` is already retained. From it:
- `gained(A,e) = A.at[e] - A.at[e-1]`, `lost(B,e) = B.at[e-1] - B.at[e]`
- a crossing is `gained(A,e) & lost(B,e)` non-empty with both present at e-1 and e
- clean = every cell that changed on that edge is accounted for by some worldline's loss
- displacement = `len({anchor(f) for f in A.at.values()}) > 1`

**No new record and no verb retention.** (Correcting the harvest note: verb retention
buys destructibility, a Ring 4 GAPS line, and is its own variable.)

## 4 · Both sets are exposed, and the card shows the filter working

`weave.ego_candidates()` — the wide own-stream set, kept.
`weave.egos()` — the verdict set, the three conjuncts. The card renders the verdict set;
GAPS names how many candidates were refused and why. The filter becomes visible instead
of implicit.

## 5 · Pre-registered fixtures (baselines from runs/kaggle-ring4)

| # | fixture | ring4 | ring5 must |
|---|---|---|---|
| F1 | distinct ego seals | **76 across 12 games** | fall sharply; <=3 per game |
| F2 | ego seals on CLICK worlds | present | **ZERO** — no ground to cross |
| F3 | oversized "egos" (>=40 cells) | 9 distinct | **ZERO** |
| F4 | 1-cell "egos" | 12 distinct | **ZERO** unless it crosses a stationary ground |
| F5 | the seal only NARROWS | — | no game seals an ego it did not seal in ring4 |
| F6 | GAPS names refused candidates | — | present wherever candidates > verdicts |

**Negative controls (from `test_ego_field.py`'s refusals):** a driven object that moves
under two labels with two bearings but crosses nothing must NOT seal · a ground whose
footprint holds one anchor must NOT seal · two mutually-displaced partners must BOTH be
passed over · a single observed action must refuse (one button cannot be distinguished
from another).

## 6 · Pre-registered limitations

1. **A NAV world with no crossable ground seals no ego.** Honest, and a GAPS line — not
   a failure. `ego_read`'s wider set stays available as candidates.
2. **Ego POSITION staleness is untouched** — `RULING_EGO_POSITION` (08-26) is a
   different defect and we do not have it; our position line is rebuilt every turn.
3. **Permanence is unchanged this ring.** The seal still does not retract. Whether a
   seal may ever be retired is a ruling, and it touches counter and lever equally.
4. **The digest's "is YOU / never doubt" wording is unchanged** — second variable, owed
   its own ring. The card already states the falsifier.

## 7 · Failure shapes filed in advance

- The clean-exchange test is too strict and NOTHING seals — F1 overshoots to zero and
  the model loses a read it had. Signature: ego seals 76 -> 0, GAPS full of refusals.
- Counter-masked cells confuse the exchange (a sealed counter's cells are excluded from
  identity but still move); crossings computed over masked footprints may under-count.
- A ground that itself drifts one cell over the window is "displaced" and disqualifies
  its own crossing — the conjunct is exact, which is also its brittleness.

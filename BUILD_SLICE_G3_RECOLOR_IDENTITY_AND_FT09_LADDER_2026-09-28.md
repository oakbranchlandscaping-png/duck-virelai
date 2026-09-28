# Build slice R9-R05: an object that recolours in place keeps its identity; the ft09 ladder offline

**Revision label:** `R9-R05`
**Date:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Base:** `8319853` (R9-R04). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.
**Governing documents:**
- `CONTRACT_G3_ENTITY_LIFECYCLE_v1_2026-09-22.md` §1: identity matching is exact and structural,
  and "an ambiguous match abstains".
- `BUILD_SLICE_G3_ENTITY_OBSERVATION_ADAPTER_2026-09-22.md`: "entity hypotheses survive unique
  translation and recolor".

This slice repairs the code so that it meets the contract. It does not change the contract.

## How it was found

The defect was found before any live run. While preparing `ring9-g4-ft09-guided-v2`, I carried
the real ft09 G2 record past G2 in the cloud to measure the G3 and G4 card sizes on the real
anatomy. For every click after G2, I continued the one law the record shows: a control tile toggles
9↔8 and the bar ticks. The G3 cards fit, but **G3 filed both controls as
`UNRESOLVED_ATTRIBUTION` and would have closed with zero levers.** If that happened live, P would
fail again, G4 would never open, and the ~2-hour Kaggle run would be spent learning what this
offline pass already shows.

## The defect

- Each ft09 control is a 6×6 tile, and the board holds other 6×6 tiles of both colours.
- When a control recoloured 9→8, the entity ledger counted every *unchanged* 8-coloured 6×6 tile
  elsewhere as a possible translation source.
- The recolour therefore became an `AMBIGUOUS_BIRTH`: the control lost its entity, and its G2
  member label pointed at an absent entity.
- In G3, the clicked member then had no cells, so pointer ownership could not resolve.
- Worse, in the simplest case (one other same-colour tile) the unchanged tile was assigned a
  `MOVE` onto the recoloured site, and a new entity was born where it actually stood. That is a
  silent identity swap, which the contract forbids.

## The repair: `entity_observation.py`

The matching logic moves out of `EntityLedger.observe` into `_continuity_match`. The function
body gets shorter; the logic is extracted and then called. Two exact, structural rules apply, with
no thresholds:

1. **What persists is STILL.** A prior entity whose exact `(integer, cells)` key is present in the
   after frame cannot also be the source of a move or recolour elsewhere.
2. **One source matches; several abstain.** Sources are:
   - same-integer exact translations, which match as `MOVE`;
   - a same-footprint predecessor of another integer, which matches as `RECOLOR`.

   Exactly one source matches. Two or more (for example, a recolour in place *and* a vanished
   same-colour tile that could have moved there) give `AMBIGUOUS`, recorded against the
   transition. The old code silently chose the translation.

## Tests (written first; 7 fail on `8319853`, all pass with the repair)

- **`tests/test_g3_recolor_identity.py`** (5 tests):
  - A recolour in place keeps identity while a same-shape tile of the new colour stays put.
  - A toggle and a toggle back keep one identity.
  - A recolour against a vanished translation source abstains.
  - On the real ft09 record, both control members (M0040, M0041) are PRESENT at G3 entry, with 36
    cells each.
  - The ft09 G3 sweep witnesses both controls as `LOCAL_LEVER_WITNESS` and completes with 2
    confirmed levers and 0 bounded unknowns.
- **`tests/test_ft09_ladder_offline.py`** (2 tests). This covers the whole ladder:
  - The real ft09 G2 record, then G3, G4.0/G4.1 and G4-A, under the recorded control law and the
    simplest policy the cards allow (fill each template; press the first unfinished lever).
  - It reaches G4-A `SATISFIED`, with Phase 1 `COMPLETE` and both levers `CONFIRMED`, at
    transition **131 of 200**.
  - **Every binding card at every gate fits the 24,000 budget.** The largest is the G3 working
    card at 15,792; the completion card is 8,564, G4-REACTIONS is 3,864, and the G4-A target card
    is 5,868.

**Suite:** 411 passed, 1 skipped (cloud). Ruff is clean. Mac expected: **400** (393 + 7).

## What this does and does not establish

- **It establishes** that the controller can carry an ft09-shaped world from the real G2 record
  to a satisfied G4-A, with bounded cards and within budget.
- **It does not establish** that ft09 behaves this way after transition 57. The toggle law is
  extrapolated from three observed control clicks: a hypothesis, not a fact. Nor does it say
  anything about Duck's own choices, which the test replaces with a trivial policy.
- **Counter capacity (the bar):**
  - The bar holds 64 cells and ticks 2 per effective click, so it allows 32 effective clicks
    before it empties.
  - The simulated ladder uses 15: 3 in G2, 4 in G3 (click and confirmation for each control),
    and 8 in G4-A.
  - What ft09 does when the bar empties is unknown. A Duck that breaks many runs in G4-A
    consumes that margin.

## Proposed axiom (for the Director; not ratified)

> **A7 · An object has one worldline.** What persists in place is STILL and cannot be a source
> elsewhere. A change in place is the same object, unless another source is equally exact, in
> which case identity abstains and says so.

The contract already implies this. Stating it as an axiom would make it binding on every future
continuity rule (NAV ego, G9 cross-level mapping).

— Claude, Alpha build seat, 2026-09-28

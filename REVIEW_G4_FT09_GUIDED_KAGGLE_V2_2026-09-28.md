# Review: ft09 guided Kaggle checkpoint v2

**Reviewed:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Run:** `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v2`, notebook version 1. The review copy
is in `virelai-review/ft09v3/`.
**Package:** `ring9-g4-ft09-guided-v2` (revisions R9-R04 and R9-R05), built from source `4329185`.
**World and model:** `ft09-0d8bbf25`; `vrfai/Qwen3.6-27B-FP8`.
**Graded against:** the frozen `checkpoint-preflight.json`.

## Verdict

**G2 closed live again. G3 then did what v1 could not: it witnessed and confirmed five ft09
controls as levers, and R9-R05 held.** The run crashed at transition 121 on the card-size guard:
this time the G3 card grew with the number of levers found, not with the size of the world. A6
bounded the roster, but not the per-finding records. **P was not met, so the G4 criteria are
ungraded, not failed.**

| Item | Grade |
|---|---|
| **I2:** receipt byte-identical | **PASS** |
| **I1:** CLICK routing; guided capabilities served | **PASS**: 56 `GUIDED_ACTION` and 1 `DEMONSTRATE` in G2; G3 served 59 `RANKED_CLICK_TARGET` and 5 `CONFIRM_LEVER_WITNESS` |
| **G2-1:** G2 closes under A1 | **PASS**: Duck chose a `COUNTER_REWRITE` prediction on a control **it had not yet clicked** (44,36). It was `SUPPORTED` at transition 57, and G2 closed. |
| **G2-2:** purity, recomputed | **PASS**: over all 121 transitions, every change in the footprint is 12→11; no violations |
| **G2-3:** the trigger agrees with the record | **PASS**: the claim was `EFFECTIVE_TRANSITIONS_ONLY`, and the record through G2 shows 3 effective transitions with a tick and 54 null transitions without one. Across all 121 it is 13 effective, all ticked, and 108 null, none ticked. |
| **A6-1:** no card overflow | **FAIL**: after the fifth lever's confirmation, the G3 card needed a dossier and exceeded 24,000 characters. Replayed offline from the lossless record: **25,502**. |
| **G3-1:** both named controls are witnessed as levers | **PASS**: (36,36) and (36,44) were `LOCAL_LEVER_WITNESS`, each prospectively confirmed. So were (44,36), (36,52) and (52,36). Nothing was filed `UNRESOLVED_ATTRIBUTION`. |
| **I3:** G3 inherits the frontier and completes the sweep | **FAIL**: 59 of 64 roster objects were clicked before the crash |
| **P:** G3 closes with at least 2 levers | **NOT MET**, so A-1 to A-3 are ungraded |
| **N-1:** no idle without a legal move | **PASS, with a note**: there was no idle. The run ended on the fail-fast size guard, not on the watchdog. |

**R (reported):**
- 121 actions (G2 57, G3 64) in 1 h 14 m, about 37 s per action including model turns.
- At the end, 38 of the 64 bar cells were unspent.
- The largest card was the G3 one: 23,226 characters before the fifth dossier, then 25,502.
- Refusals, each followed by a correct resubmission:
  - one G2 refusal: the first answer omitted `trigger`, and A1 v2 fired;
  - three G3 dossier refusals on the counter-exclusion wording.

## Direct observations

- **G2 improved on v1.** Duck's frozen prediction targeted a third control it had never clicked,
  a genuinely new site, and it was supported. Duck's competing-models field cited the record's
  own count ("54 of 56 transitions produced no counter change"). The label check refused the
  first answer for a missing trigger; Duck resubmitted with the admissible class.
- **R9-R05 held live.** All five recolouring controls kept their identity, and each was attributed
  `LOCAL_LEVER_WITNESS` with prospective confirmation. v1's code would have filed them unresolved.
- **The world is larger than my offline model.** ft09 has a 3×3 arrangement of 6×6 tiles in its
  lower block (minus the centre), and each clicked tile toggles itself. G3 confirmed five of them.
  Three more same-colour tiles, at (44,52), (52,44) and (52,52), were still unclicked at the
  crash. My offline ladder assumed only the two controls G2 had witnessed.
- **Where the card grows.** Replaying the lossless record through the committed code reproduces
  the growth, about 2,300 characters per confirmed lever. It sits in `attribution_contract`:
  `confirmation_records` (4,785) and `dossier_answers` (4,376) list every lever in full. The
  windowed roster, ledger and journal stayed bounded, as designed.

## Frictions, routed through the axioms

1. **A6 was not absolute (code-level; sharpens A6).**
   - As written, A6 says "the card is bounded regardless of world size", and it bounded what grows
     with world size. It missed what grows with findings.
   - Proposed A6 v2: **the card is bounded regardless of world size and regardless of how much
     has been found. Every list on the card is windowed to the current work, with counts and a
     query handle.**
   - The test must be absolute as well: a stress world with many levers, not the one observed.
2. **The bar is a finite budget, and the exhaustive protocol overspends it (plan-level; a
   Director decision).**
   - The bar allows 32 effective clicks per life.
   - The ladder spends 3 in G2, 2 per lever in G3 (witness and confirmation), and at least 4 per
     toggle lever in G4-A.
   - With 8 levers that is about 51. Even if G4-A reused G3's two presses, it would be about 35.
   - Offline, continuing the observed law over all 8 tiles, G3 closes with 8 levers at transition
     130 with 13 ticks left. The bar then empties at transition 143, after 3 of the 8 G4-A
     studies.
   - What ft09 does at an empty bar is unobserved. The current code degrades as follows: a
     `GAME_OVER` interrupts the lever being studied and G4-A continues with the pending ones.
     This is `test_g4_phase1_boundary`. One lever per life would end interrupted and never be
     re-studied.
   - **The ruling needed:** does a death on the same level end that lever's study (A3 read
     broadly), or does study continue across lives, with knowledge persisting and the world
     reset? The ledger already has a Groundhog-Day reset path (`observe_reset`). A3 as ruled
     speaks of level boundaries, not deaths.
3. **The offline ladder was too narrow (method).** It continued only the law the record had shown,
   over only the objects the record had touched. The lesson for the build method: stress the
   offline ladder with the most expensive continuation the observed structure allows — here, every
   same-shape tile as a control — not the cheapest.

## What this run establishes

- G2 under A1 and A1 v2 is repeatable live, and Duck corrects on refusal.
- R9-R05's identity repair holds on the real world: five levers, all confirmed.
- G3 attribution on self-recolouring tiles works end to end, including Duck's dossiers.
- It establishes nothing about G4-A, the watchdog, or what happens at an empty bar.

## Repair (recommended)

- **R9-R06 (code; A6 v2).** Window `attribution_contract.confirmation_records` and `dossier_answers`
  to the current and pending lever, with counts and a query handle, and audit every other card
  list for the same pattern. Test it test-first on:
  - a new fixture from this run's real 121 transitions, which must reproduce 25,502 before the fix;
  - a stress world with every same-shape tile a lever, asserting every card at every gate stays
    under budget.
- **Director ruling (F2) before G4-A can finish on ft09:** is a lever interrupted by a death
  re-studied in the next life?
- Then rerun the same package shape as `ring9-g4-ft09-guided-v3`. If the bar empties, that run
  observes what an empty bar does, which is itself a finding.

— Claude, Alpha build seat, 2026-09-28

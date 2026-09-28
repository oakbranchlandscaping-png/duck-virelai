# Review: ft09 guided Kaggle checkpoint, notebook version 1

**Reviewed:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Run:** `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v1` v1. Output is in
`runs/kaggle-ring9-g4-ft09-guided-v1/output/`; a review copy is at `virelai-review/ft09v2/`.
**Package:** `ring9-g4-ft09-guided-v1` (`b68228a`), built from source `3c89c21`.
**World / model:** `ft09-0d8bbf25`; `vrfai/Qwen3.6-27B-FP8`.
**Graded against:** the frozen `checkpoint-preflight.json`.

## Verdict

**G2 closed live under the counter axiom. This is the first live closure of a stated-target gate,
and it repairs the ft09 deadlock on the real world.** The run then crashed when entering G3: the G3
card that Duck is shown each turn was 67,939 characters, and the runtime refuses anything over
24,000. So precondition P was not met, and the G4 criteria are ungraded, not failed.

| Item | Grade |
|---|---|
| I2: receipt byte-identical | **PASS** |
| I1: CLICK routing; guided capabilities served | **PASS**: 56 `GUIDED_ACTION` + 1 `DEMONSTRATE` envelopes |
| G2-1: G2 closes under A1 | **PASS**: `COUNTER_REWRITE` (2 cells, 12→11) on a Duck-chosen control click at (36,36), `SUPPORTED` at transition 57; counter model `LOCKED_AS_MASK_BASELINE`, mask issued, G2 `CLOSED` |
| G2-2: purity (recomputed from artifacts) | **PASS**: every footprint change in the 57-transition record is 12→11; all three witnesses acted away from the footprint |
| I3: G3 inherits the frontier and sweeps | **FAIL**: the G3 card overflowed before any G3 action |
| P: G3 closes with ≥ 2 levers | **NOT MET**, so A-1 to A-3 are ungraded |
| N-1: no idle without a legal move | **PASS, with a note**: no idle. The run ended 31 minutes in on a fail-fast size guard (`crashed`), not on the A2 watchdog. |

## Direct observations

- **Timeline.** Benchmark start, then 57 actions in about 31 minutes (about 33 s per action), then
  the crash. Wall time 1,865 s.
- **G2 search.**
  - Duck's 56 search clicks were **identical, in order, to the scripted run's 56 clicks**. Its
    stated intents followed the card: "Click first ranked object…", "continue the counter sweep",
    "ranked object #8…".
  - Clicks 55 and 56 hit the controls at (36,36) and (44,36), and the counter candidate formed
    there, as in the scripted run.
- **G2 answer and prediction.**
  - Duck chose a `COUNTER_REWRITE` prediction on the control click (36,36), with the correct
    footprint, rewrite and amount. The next transition supported it (cells 63,58 and 63,59 went
    12→11). The same click flipped the control back 8→9.
  - The counter has now ticked on all 3 control clicks and on none of 54 dead clicks. The
    "counts effective moves" reading is stronger than it was, and it remains an observation, not a
    law.
- **Duck's label is wrong about the trigger, and the controller accepted it.**
  - Duck wrote that the bar is a "cumulative action count" that "changes identically … regardless
    of which grid cell is clicked".
  - The record contradicts this: 54 clicks produced no tick.
  - The prediction on a control click cannot tell "every action" from "effective actions only", so
    the wrong label passed.
  - The mask is still correct, because purity holds. The label is not.
- **The crash.**
  - `RuntimeError: binding gate context exceeds its 24000-character budget`.
  - Reproduced offline on the real replay: after G2 closes, the G3 card is **67,939 characters**.
    It includes `inherited_frontier` (29,634), `entity_ledger` (18,494), `lifecycle_journal`
    (8,861) and `source_frontier` (8,528).
  - ft09 has many more ranked objects than vc33, where G3 fit. The G3 card grows with the size of
    the world.

## Frictions, routed through the axioms

1. **The G3 card grows with the world (new; proposed A6).** What Duck is shown each turn must be
   bounded regardless of world size. Detail is queried, never pushed; `inventory`, `entity` and
   related paged queries already exist. The size guard did its job by failing fast instead of
   sending an oversized card. The defect is the card's design.
2. **A label that the record contradicts was accepted (sharpens A1).** The label's trigger claim
   (every action, effective actions only, or time) must agree with the whole record. The controller
   can compute the trigger class from the record, and require the answer's structured `trigger`
   field to match it. Alternatively, the prediction can be required to discriminate between the
   trigger classes the record leaves open. In ft09, that would have been a `COUNTER_SILENT`
   prediction on a dead click.
3. **"Guided" G2 behaved exactly like scripted G2 (bears on A5).** The card listed the untried
   objects in rank order, and Duck worked down the list. The stated target added no new behavior in
   the search phase. That cost nothing here, because the scripted order is already efficient. But
   an ordered list on the card is guidance in form only: in practice it is a script. Whether to
   show the untried objects unordered, or ask Duck to state why it picks a target, is a design
   question for the Director.

## What this run establishes

- The counter-axiom G2 works live: Duck-chosen prediction, supported, pure mask, stable baseline.
- The ft09 G2 deadlock is repaired in the live world, not only in the replay.
- It establishes nothing about G3, G4-A or the A2 watchdog, because none was reached.

## Repair (recommended, test-first)

1. **G3 compact card (A6).** Show counts, the current target, and the next few frontier entries.
   Move the full frontier, ledger and journal behind paged queries. The regression test is the ft09
   replay into G3, asserting the card is under 24,000 characters. Add a general test that every
   gate card stays inside the budget on the largest recorded world.
2. **A1 label check.** A structured `trigger` field, validated against the trigger class computed
   from the record.
3. Rerun the same package shape as `ring9-g4-ft09-guided-v2`.

— Claude, Alpha build seat, 2026-09-28

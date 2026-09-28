# Build slice R9-R04: G3 bounded card (A6) and counter trigger label (A1 v2)

**Revision label:** `R9-R04`
**Date:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Rulings implemented (Director, 2026-09-28):**
- "The ranked list ensures an exhaustive search with no thought needed. It stays."
- "Proceed as you suggest with the other factors."

Recorded in `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md` (A1 v2, A5, A6).

**Defects repaired:** `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`
1. The G3 card overflowed the 24,000-character budget on ft09 (67,939 characters). The game
   crashed at G3 entry.
2. A counter label that the record contradicts was accepted ("every action", against 54
   non-ticking dead clicks).

**Base:** `3c89c21` (R9-R03). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## What changed

| File | Change |
|---|---|
| `virelai_gates.py`, `_LeverTarget._working_gate_view` | Now returns `_bound_working_card(view)`. **The card is bounded (A6).** It carries: the scheduler window (the current target plus 5 ahead, `CARD_WINDOW_AHEAD = 6`); up to 8 notable entities (WITNESSED, RESPONDED, AMBIGUOUS, G4-READY, REOPENED); role-bound entities; and pending confirmation or dossier targets. The roster becomes `WINDOWED_ROSTER` with `candidates_omitted`, `window` and `roster_query` (`virelai('inventory', …)`). `source_frontier` keeps its summary and drops its candidate rows. The entity ledger and lifecycle journal list only the kept entities, with omitted counts and query handles. `snapshot()` is unchanged and lossless. |
| `virelai_gates.py`, `CounterGateMachine.record_trigger()` | **A1 v2.** Computes from the whole record whether the counter ticks on `EVERY_TRANSITION`, on `EFFECTIVE_TRANSITIONS_ONLY` (only when something outside the footprint changes), or `IRREGULAR`; or whether the record is still `OPEN` between the two simple classes. Returns the counts behind the verdict. |
| same, `submit_answer` | The answer must include a structured `trigger`. It must be an admissible claim for the record's class; under `OPEN`, either simple class is admissible. A disagreeing claim is refused with the counts, for example "54 transitions changed nothing and did not tick". The record's own class is always admissible, so this cannot deadlock (A2). |
| same, template, card, products | The template prefills `trigger` and shows `trigger_options`, which carry the record and the rule. The G2 card shows `record_trigger`. `CounterAnswer.trigger` and `CounterModel.trigger` carry the label forward into the G2 product. |

## Tests (written first; each failed on `3c89c21`)

- **`tests/test_bounded_cards.py`** (new, 4 tests). The real ft09 G2 record is replayed into G3, and
  a complete 64-object G3 sweep follows.
  - The G3 entry card fits the budget: it failed at **67,939** characters, exactly the live
    number, and is now about **10,061**.
  - Every card through the sweep fits the budget: it failed at 68,148, and now peaks at about
    13,501; the completion card is about 8,204.
  - Every G2 card of the real record fits.
  - The snapshot keeps the lossless roster.
- **`tests/test_counter_trigger_label.py`** (new, 4 tests).
  - The real ft09 record classifies as `EFFECTIVE_TRANSITIONS_ONLY` (54 null transitions without a
    tick, 2 effective transitions with one).
  - Duck's live "every action" label is refused, with the record as the reason, and a missing
    trigger is refused.
  - An agreeing label closes G2, and the trigger is kept on the counter model.
  - An `OPEN` record admits either simple claim.
- **Amended for A6** (the unbounded contract is superseded):
  - `test_g3_scheduler.py::test_g3_large_frontier…` now asserts the windowed roster, and that
    listed plus omitted equals the whole roster.
  - `test_counter_gate.py` asserts that the card carries the source-frontier summary while the
    snapshot keeps it whole.
- **Amended for A1 v2:** the four legacy G2 answers in `test_counter_gate.py` and
  `test_g2_checkpoint_evaluation.py` now state `trigger: EVERY_TRANSITION`, which is what their
  synthetic worlds show.

**Suite:** 404 passed, 1 skipped (cloud). Ruff is clean on every changed file. Mac confirmation is
owed.

## Known limits

- The G2 evaluator (`tools/evaluate_g2_counter_checkpoint.py`) does not yet grade the trigger
  claim. The review recomputes it from the artifacts.
- G4.1 and G4-A cards were measured on synthetic levers only (5 levers, about 7,400 characters).
  Their size on ft09's real anatomies is unmeasured until a live run reaches them.
- The G3 re-sweep repeats G2's clicks by design, because G3 attributes under the mask. On ft09
  that is 64 more actions, about 35 minutes.

— Claude, Alpha build seat, 2026-09-28

# Build slice: G2 under the counter axiom, and the no-legal-move guard

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat), signed
**Rulings implemented (Director, 2026-09-27):**
- "Counters come in many ways; the target for the agent is the same: find it, label it, and mask it
  to keep lever data pure."
- "A stated target is the goal when possible."

Both are recorded as axioms A1 and A2, plus A5, in `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md`.

**Defect repaired:** `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md`. The ft09 G2 deadlock
reproduced exactly on `8cfb782` from the real record: status `ANSWER_REQUIRED`, template `None`, no
capability, and every answer rejected with "no isolated counter-only intervention".
**Base:** the committed G4-A guided build on top of `8cfb782`.
Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## Thesis

G2 now tests what the counter axiom asks: **purity, not isolation**. A counter is found, labelled
and masked. The mask passes purity on the record, and one frozen footprint-scoped prediction, on an
action Duck chooses, is supported. In CLICK worlds G2 is a stated target, and Duck chooses every
action. Separately, a machine-level legal-move status and a runtime watchdog make "no legal move" a
recorded controller failure rather than hours of idling.

## What changed

| File | Change |
|---|---|
| `virelai_gates.py`, `CounterGateMachine` | **Stated target in CLICK worlds** (`_guided`). While searching, G2 offers a `GUIDED_ACTION` capability: any admissible action, an optional `intent`, and the card shows the target, the done-when test, untried object anchors and rejected candidates. If no counter appears, G2 closes as not-observed once **every ranked object has been clicked at least once** (`NO_RECURRENT_PROCESS_AFTER_FULL_CLICK_COVERAGE`). The frontier handed to G3 is the ranked prefix Duck actually covered. |
| same | **Purity** (`_purity_violations`): every recorded change inside the footprint must follow the counter rewrite or its inverse (a refill), and at least one witness must have acted away from the footprint. A candidate that fails is recorded in `rejected_candidates` and dropped, and the search continues; this never deadlocks. Purity is checked again when the prediction is supported, before the mask is issued. |
| same | **Prediction:** the counter-only requirement is removed. `novel_prediction.action` is any admissible action Duck chooses, and the predicate is `COUNTER_REWRITE` (exact recurrent amount) or `COUNTER_SILENT` (amount 0: the footprint holds). The prediction is scored on the footprint; for SILENT any footprint change contradicts it. The demonstration capability admits exactly the action Duck froze. |
| same | **The answer template is never `None` while a candidate exists.** The default action is the counter-only witness if one exists, otherwise the latest witness. The card note and `prediction_options` explain the choices. |
| same, `CyberneticGateMachine.legal_move_status()` | **Axiom A2.** Legal means one of: a capability is offered; an answer is asked for with a template; or the gate is in a declared state. Illegal signatures: an answer demanded without a template, or a probe demanded with none offered. |
| `inference/agent/tool_agent.py` | **Watchdog** (`_controller_no_legal_move`). After every tool dispatch in gated mode it checks `legal_move_status`. After 3 consecutive illegal checks (`_NO_LEGAL_MOVE_LIMIT`) it returns `fatal_failure = "controller_no_legal_move: …"`. The solver records the game as crashed with that note, the same fail-fast path as the no-tool-call breaker. |
| `tools/evaluate_g2_counter_checkpoint.py` | The check `confirmation_counter_only` is replaced by `confirmation_footprint_pure`: inside the mask, the confirming transition obeys the counter law, and the action did not target the counter. The rewrite check accepts a SILENT prediction (amount 0). |
| registry | The G2 contract's completion predicate is restated as axiom A1. |

## Tests

- **New: `tests/test_g2_counter_axiom.py`.** Five tests on the real ft09 segment (fixture
  `tests/fixtures/ft09_kaggle_v1_g2_segment.json.gz`, 1.3 KB: the initial grid plus all 56 recorded
  transitions):
  - the real record yields the 64-cell row-63 counter (12→11), passes purity, and has a template
    and an answer path, although no counter-only witness exists;
  - a REWRITE prediction on a control click closes G2 with a pure mask and opens G3;
  - a SILENT prediction on a dead click closes G2;
  - a SILENT prediction contradicted by a footprint tick resumes the search with a capability;
  - a planted footprint change outside the counter law is rejected as impure, and the search
    continues.

  The continuations after the recorded 56 steps are synthesized from the observed laws and are
  labelled as such in the tests.
- **New: `tests/test_no_legal_move.py`.** Six tests:
  - every state of the real ft09 G2 replay is legal;
  - every state of a guided G4-A study is legal;
  - the level-closed state is a declared end;
  - the `8cfb782` signature (answer demanded, template `None`) is detected;
  - the watchdog fires after 3 consecutive checks;
  - the watchdog resets when a legal move returns.
- **Updated:**
  - `tests/test_counter_gate.py`: a Duck stand-in picks the next untried object, and the coverage
    closure reason is asserted.
  - `tests/test_g2_checkpoint_evaluation.py`: the Duck stand-in again. The old "non-counter-only
    confirmation is rejected" test is replaced by two: a world change outside the mask **passes**,
    and a footprint change outside the counter law **fails**.
- **Reproduced before the fix:** on `8cfb782`, replaying the real record through the scripted
  capabilities reproduces the deadlock exactly. The scripted order matched the recorded actions
  one for one.

**Suite:** 396 passed, 1 skipped (cloud, Python 3.12). Ruff is clean on every changed file; the one
remaining finding in `tools/evaluate_g2_counter_checkpoint.py` (an unused local variable) predates
this slice. Mac confirmation is owed before commit.

## Evidence class

- **Direct:** code, tests, the real-record replay, and the reproduction on `8cfb782`.
- **Not yet observed live:** Duck acting under the guided G2 target, and the watchdog firing on
  Kaggle.

## Known limits

- A **declared** end, such as a closed level or a G4 slice not yet built, still idles to the
  deadline. A clean planned stop needs harness work, and the watchdog deliberately does not treat
  it as a failure.
- NAV/HYBRID G2 stays scripted: NAV is shelved.
- Guided G2 has no action budget of its own inside the world budget. If Duck never covers the
  roster and no counter appears, the world budget is the stop.

— Claude, Alpha build seat, 2026-09-27

# Build slice R9-R07: memory stage M-1, the slot-built card

**Revision label:** `R9-R07`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Governing design:** `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`. v2 records this stage's design
revisions: tuned budgets, the card's presentation, and §5.3.1 certified fields.
**Laws:** M3, M4, M5, M7 (`DOCTRINE_FRICTION_AXIOMS_v3`).
**Tests:** T1, T3, T5, T7, T10, T11, and the amended T2 anchor.
**Base:** `1a4b6bd` (R9-R06). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## The result in one line

The card that crashed the v2 run is now about 4,700 characters: it was **25,502**. A simulated Duck
that reads *only* the card carries a stress world with **2, 8 and 20 levers** from G2 to a satisfied
G4-A. Each gate's card is the same size whatever the lever count.

## What was built

| File | What |
|---|---|
| `inference/framework/card_builder.py` (new) | **The card builder.** Eight slots, each a *whitelisted projection* of the gate's state, so a field without a slot cannot reach Duck (M3). Each slot has a character budget (15,600 in total). Every list is windowed to the current work, with a count; cell lists become a count and a bounding box (M4). The world-model digest has one line per certified fact, grouped by exact signature; the oldest gate collapses to a recall handle if the digest ever exceeds its budget (M2, M7). The progress slot carries the budgets the world imposes, such as counter cells and ticks remaining. The goal, the current probe and the answer template are always on the card (M5). Rendering is deterministic (M7). |
| same, `fill_certified_fields` | **Certified fields** (DESIGN v2 §5.3.1). Templates show controller-certified data as `CERTIFIED`, and the controller fills it when the answer arrives. A field Duck writes is still validated as written. |
| same, `worst_case_request_chars` | **The preflight (T10):** the largest request a turn can make, with every slot at budget. The packager integration comes with the M-5 package. |
| `gate_card.py` | `binding_gate_payload` / `render_binding_gate_context` now return the built card. |
| `virelai_gates.py`, `CyberneticGateMachine.submit_answer` | Fills the certified fields before the gate validates. It is the only gate-logic change (+1 line). |
| `tool_agent.py` | `virelai('gate')` and every query-error response now return the card, not the full gate view. The answer-refusal response returns the card's template. |
| `record_replay.py` | `answer_source="card"` rebuilds each recorded answer from the card's template. `measure=False` skips card sampling, for speed. |
| `tests/card_duck.py` (new) | A game-free **stress world** (N self-recolouring lever tiles, inert blocks, a bookkeeping bar), and a **simulated Duck that reads only the card**. |

The card is built by projection over each gate's public view, rather than a `card_slots()` method
on every gate adapter as §5.3 first sketched. That keeps gate code unchanged (phase sovereignty).
The whitelist lives in one place, where the card's contract is enforced and tested.

## Measured

| Case | Before (R9-R06) | After |
|---|---|---|
| v2 G3 card at transition 121 (the crash) | 25,502 | about 4,690 |
| Largest G2 card, v2 record | 8,152 | about 5,900 |
| Stress world: G2 / G3 / G4.1 / G4-A, 2 levers → 20 levers | — | 5,790→5,791 / 3,744→3,750 / 4,204→4,289 / 5,747→6,457 |
| Actions the card-only Duck needs (G2 through G4-A satisfied), 2 / 8 / 20 levers | — | 20 / 56 / 128 |

## Tests (`tests/test_memory_m1.py`, 10 new)

- **A Duck that reads only the card completes the ladder** for 2, 8 and 20 levers: all four gates
  in order, G4-A satisfied, Phase 1 complete (M5).
- **The card is flat in the number of findings (T1).** Every gate's card is within budget, grows
  at most 1,000 characters from 2 to 20 levers, and no slot is over budget.
- **The real v2 record replays with every answer written from the card's template.** All 5 live
  answers are accepted again.
- **A field without a slot cannot reach the card (T3).** Injecting a 100,000-character field and a
  future ledger into the gate view leaves the card byte-identical.
- **Grouping (T5).** 20 identical levers give one digest line; one differing lever gives two lines
  (x7 and x1). Nothing that differs is ever merged.
- **Promotion (T7).** During G2 the digest shows G0 and G1 only; after G2 closes the counter line
  appears, with the trigger class and the 32-action period.
- **The budgets the world imposes** are on the card: 38 counter cells, 19 ticks remaining on the v2
  record.
- **Determinism (T11).** The same state renders the same bytes, across independent replays.
- **Certified fields** are filled by the controller, but a wrong value Duck writes is still refused.
- **Preflight (T10).** The worst case (the real gated system prompt and tool schemas, a 4,000-char
  prompt body, the card at full budget, two tool results at the output cap, a 16k-token reserve)
  fits the 65,536-token window.

**Amended:**
- The M-0 anchor now asserts that the crash-point card is within budget. The 25,502 history is
  kept in its docstring.
- A G0 bridge test now reads `action_metadata` from the card's subject slot.

**Suite:** 430 passed, 1 skipped (cloud). Ruff is clean. **Mac expected: 419** (409 + 10).

## Ratchet

| | Before (R9-R06) | After |
|---|---|---|
| `ToolAgent._run_python_tool` | 457 | 457 |
| `ToolAgent.analyze` | 423 | 423 |
| `tool_agent.py` | 2,909 | 2,910 (one import) |
| `CyberneticGateMachine.submit_answer` | 4 | 5 |

All new logic lives in new modules.

## What this does not do yet

- **Duck still takes every action.** The executor that runs computable moves is M-2 (R9-R08).
- **The recall slot is empty** until M-3 (R9-R09).
- **The rest of the user message is unchanged:** the prompt body (about 3,500 characters) and the
  system prompt (about 21,000). Both are measured by the turn ledger, and the preflight counts
  them.
- **Stress-world limits.** The stress world ignores what happens when the bar empties: ticks simply
  stop. The v2 bar arithmetic (38 cells, 19 ticks) is on the card for Duck and, in M-2, for the
  executor.

— Claude, Alpha build seat, 2026-09-29

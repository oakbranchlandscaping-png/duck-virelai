# Build slice R9-R12: G4-B (levers together), a clean stop at the ladder's end, and the M-5 fixes

**Revision label:** `R9-R12`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Base:** `8ca9fc9` (R9-R11), the source the M-5 live run used.

**Director rulings (2026-09-29, after the M-5 review):**
- "We keep building so it doesn't [end]": the next slice is **G4-B first**, in plan order.
- Add the planned clean stop (R9-I02). In practice this settles R9-R08 deviation 4, "there is no
  END owner": **the controller owns the end.**

## What G4-B does, in plain terms

G4-A studied each lever alone. G4-B asks how the levers affect each other, and Duck has to say what
it expects before each test.

1. **Duck freezes a prediction** with `virelai('gate_answer', …)` and `answer_kind:
   LEVER_PREDICTION`. The prediction states:
   - the one action to take;
   - what it will do to every lever's region: `UNCHANGED`, `STEPS` (changes exactly as that lever's
     own press did in G4-A), or `CHANGES`. A lever Duck does not name is predicted `UNCHANGED`;
   - whether anything outside the lever regions changes (`NO_CHANGE` or `CHANGES`);
   - why, in at least 5 words.
2. **The controller takes that action.** It is exactly the frozen action, bound by a probe token,
   so Duck never presses in G4-B.
3. **The gate grades the prediction** on the counter-masked board, on the transition after it was
   frozen. The result is SUPPORTED or CONTRADICTED, and every lever that missed is listed.
   Contradicted predictions stay on the record.
4. **A missing condition is recorded automatically** when the same action, from the same masked
   board, gives two different outcomes.
5. **Duck describes the lever set.** Once every lever has been the pressed lever of at least one
   graded prediction, Duck submits `LEVER_RELATIONS`:
   - a plain-language description of at least 20 words;
   - a list of relations, each citing only SUPPORTED predictions that pressed or named its levers;
   - every missing condition, listed in `open_conditions`;
   - competing models, a falsifier and limitations.
6. **The gate is satisfied** and emits a `LeverRelationSet` product. Its line appears in the world
   model.

**One prediction at a time.** A batch would be a queued multi-frame plan, which the "one frame in,
one action out" law forbids. Each test therefore costs one Duck turn plus one controller press.

**The card** shows Duck:
- up to 6 lever rows, unpressed first, each with its click, bbox, class and current state
  (`S0`, `S1`, …, meaning which of its recorded region contents it shows now);
- the last graded prediction;
- coverage and supported/contradicted counts;
- a template.

The full ledger is `virelai('relations')`.

## The clean stop (R9-I02)

- **`controller_executor.ladder_end(machine)`** returns a reason when every built gate is satisfied,
  or when the level changed during G4 (G9 is not built).
- **`run_controller_turn`** then returns `AnalyzerTurnResult(planned_stop=…)`, logs `planned stop:
  …`, and makes no model call.
- **The harness** (`solver._turn_ends_game`) sees `planned_stop`, records `solver_note =
  "planned_stop: …"` and finishes the game normally. It is not marked as crashed.

In M-5 the same point cost 30 minutes and 255 requests, then a crash.

## Fixes from the M-5 review

| Finding | Fix |
|---|---|
| **F2:** a string where a list belongs was stored one character per item (live E0056 limitations) | `g4_orbits.string_list` is strict. The orbit answer and the G4-B answers use it; a bare string is refused with "must be a list of strings". |
| **F3:** the replay record dropped the harness RESET, so the re-studied lever replayed as DIVERGED | `record_from_artifacts._steps` restores a reset from the gap between probes as a `kind: RESET` step. `record_replay` delivers it via `observe_system_reset`, as the live agent does. The live v1 record now replays exactly as live: E0056 CONFIRMED TOGGLE, `life_restudies {E0056: 1}`. |
| **F7 (new, found while building):** after a death, the lever to re-study sorted last in the card's lever window, and with 8 levers it fell out of the 6 shown | `LEVER_STATUS_ORDER` now matches the controller's study order: a re-study comes before a new lever. |
| **Wakes during a frozen prediction** | A stop-and-wake that arrives while the controller is about to take Duck's own frozen prediction waits until it is taken, so Duck is never handed a turn with no move. |

**Retired adapter removed.** The G4.3 limits adapter (`_LeverLimitTarget`, about 360 lines) was
unreachable after its retirement on 2026-09-27 and is removed; G4-B supersedes it, as the retirement
note said. `g4_limits.py` and its tests stay as port material.

## Evidence

**The live record as a fixture:**
- `tests/fixtures/ft09_kaggle_memory_v1_record.json.gz` is the M-5 live run, with the reset.
- `tests/ft09_world.py` builds the offline ft09 world from it: 8 tiles, plus the observed death
  when the bar runs out (L-1).

**The offline production run follows the live run exactly.** The ToolAgent with a card-only Duck
repeats all 108 live actions in order, including:
- the death at transition 88;
- the re-study of E0056.

**Then it finishes G4-B:**
- Duck freezes 8 predictions, and the controller takes each one.
- All 8 are SUPPORTED.
- Duck's description is accepted.
- The next turn is a planned stop, with no model call. Asked again, it stops again.

**The run replays from its own artifacts,** G4-B included.

**The card-only ladder** (`run_ladder`, stress worlds with 2, 8 and 20 levers) now completes through
G4-B. The card stays flat: G4-B's card grows by at most 1,000 characters from 2 levers to 20.

## Changed

| File | Change |
|---|---|
| `inference/framework/g4_relations.py` (new) | Lever regions, predictions, grading, missing conditions, coverage, and validation of the description |
| `inference/framework/g4b_gate.py` (new) | The G4-B gate adapter, contract, card view and ledger view |
| `inference/framework/virelai_gates.py` | Registers G4-B, removes the G4.3 adapter, one generic `gate_view` branch, and `relations_view` replaces `limit_view` |
| `inference/framework/controller_executor.py` | `ladder_end`; G4-B ownership (`_relations_step`); an END owner |
| `inference/agent/controller_turn.py` | Planned stop; wakes wait while a frozen prediction is taken |
| `inference/agent/tool_agent.py` | `AnalyzerTurnResult.planned_stop`; one shared local import (net zero lines) |
| `inference/framework/solver.py` | `_turn_ends_game`: the harness ends the game cleanly on a planned stop |
| `inference/framework/card_builder.py` | A gate may state its own subject and digest lines; G4-B index; lever order (F7) |
| `inference/framework/g4_orbits.py` | `string_list` (F2) |
| `inference/framework/record_replay.py`, `tools/record_from_artifacts.py` | Resets (F3); G4-B fields in records |
| `inference/agent/memory_queries.py` | `virelai('relations')` replaces the dead `limit` view |
| `tests/test_g4b_relations.py` (new) | 11 tests: the gate on the real ft09 levers, grading, contradiction, freezing rules, missing condition, description rules, F2, F3, the harness planned stop, the wake deferral, and the end-to-end run |
| `tests/fixtures/ft09_kaggle_memory_v1_record.json.gz` (new) | The live M-5 record, with its reset |
| `tests/ft09_world.py`, `tests/card_duck.py` | The v1 world and death; the card-only Duck plays G4-B and follows the study order |
| 8 existing test files | Where they asserted "G4-A satisfied" through the machine's status, they now read G4-A's own assessment, because the ladder moves on to G4-B |

**Suite:** cloud **480 passed, 1 skipped** (481 tests). Ruff is clean on every changed file.
**Mac expected: 481 passed.**

## Ratchet (non-blank, non-comment lines)

| | R9-R11 | R9-R12 |
|---|---|---|
| `virelai_gates.py` | 5,799 | **5,432** |
| `tool_agent.py` | 2,781 | 2,781 |
| `ToolAgent.analyze` | 414 | 414 |
| `solver.py` | 1,368 | 1,376 (+8: the extracted `_turn_ends_game`) |
| `_HarnessGameSession.play` | 82 | **80** |
| `controller_executor.py` | 300 | 323 |
| `card_builder.py` | 483 | 488 |

**`solver.py` grows by 8 lines.** The stop check was extracted rather than interleaved into
`play`, which shrank. I do not have the file-tier thresholds; this line is for the Chief Engineer to
judge.

## Design choices to confirm

These are mine, made inside the rulings. Each can be changed without redesign.

1. **The outcome vocabulary** per region: `UNCHANGED`, `STEPS`, `CHANGES`. `STEPS` is exact: the
   same cells change as in one of that lever's own recorded presses.
2. **Coverage means pressed.** Each lever must be the pressed lever of at least one graded
   prediction. The minimum on ft09 is 8 predictions.
3. **A relation may cite only SUPPORTED predictions,** and each of its levers must be pressed or
   named in them.
4. **The lever list on the card is windowed to 6** (axiom A6). The rest are in `virelai('relations')`.

## What this does not do

- **A live Duck may do only the minimum.** It could press each lever once, predict "only its own
  tile steps", and describe independence. The rules ask for real relation tests, such as a lever
  pressed after another has changed, or a press that undoes one, but the gate cannot require
  interesting tests.
- **The bar.** On ft09 about 12 ticks remain after G4-A. Eight G4-B presses fit in that life. A
  death mid-G4-B is recoverable: the graded prediction stands and the board resets.
- **F4 is still open.** The preflight bounds one request, not a turn with many requests.
- **Everything here is offline.** The next step is a live ft09 run through G4-B, with the clean stop
  as a graded criterion.

— Claude, Alpha build seat, 2026-09-29

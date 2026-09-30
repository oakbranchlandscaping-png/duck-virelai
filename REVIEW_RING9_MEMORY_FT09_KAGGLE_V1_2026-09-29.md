# Review: Ring 9 memory, ft09, Kaggle v1

**Date:** 2026-09-29 (the run ended 2026-09-30 00:31 UTC)
**Author:** Claude (Alpha build seat), signed
**Run:**
- Notebook `stephenkaskin/taaf-virelai-ring9-memory-ft09-v1`, version 1.
- Package `ring9-memory-ft09-v1`, source `8ca9fc9` (R9-R06 to R9-R11).
- Outputs are in `runs/kaggle-ring9-memory-ft09-v1/output/`.

**Graded against:** the criteria frozen in the package's `RUN.md` before the run. All grades come
from artifacts (turn ledger, gate events, gate answers, probe envelopes, probe outcomes,
annotations), not prose.

## Verdict

**The memory design worked live, and the run reached G4-A SATISFIED.**
- **Controller phase (G0–G4.1):** 75 actions, no model calls, about 6 seconds of turn time.
- **Duck's first turn** was the orientation.
- **G4-A SATISFIED** on the 108th probe action, about 9 minutes into the behaviour window, after 11
  Duck turns.
- **Card size** never exceeded the slot budget.

For comparison, the v2 baseline spent about 130 Duck turns, never closed G3, and crashed on an
oversized card.

**Then the run crashed, 30 minutes after the ladder ended.** Nothing owns the step after G4-A
(R9-R08 deviation 4, "there is no END owner"; R9-I02). So the step went to Duck, which had nothing it
could do:
- It spent 28 turns and 255 requests over 30 minutes.
- It then replied twice without a tool call, and the harness's guard ended the game as `crashed`.

Scoring was not affected: no level was completed either way. But in a 55-game run, every game that
finishes its ladder would burn its remaining time the same way.

**L-1 is answered: an empty counter bar ends the life.**

## Criteria

| Criterion | Grade | Evidence |
|---|---|---|
| I2 receipt | PASS | `execution_receipt.json` is byte-identical to the package receipt (SHA-256 `17c04196…75c2`) |
| I1 | PASS | G1 mode `POINTER_GOD_MODE` from metadata. The log prints `controller executor on`. All 108 envelopes carry an executor and `{"g3_inherits_g2_nulls": true}` |
| I3 | PASS | Turn ledger (146 rows), gate answers with executor (28), annotations (3) |
| I4 | PASS | The G4-A orbits record recurrences on the masked board while the bar changes on every press |
| M5-1 | PASS | Largest card 11,975 characters (budget 16,200). The 24,000-character guard never fired |
| M5-2 | PASS | 75 ledger rows before Duck's first turn, all CONTROLLER with 0 requests. Duck's first turn submitted the orientation (3 notes, source ORIENTATION) |
| G2-1 | PASS | Closed as COUNTER_MODEL_AND_MASK: a 64-cell footprint, 2 cells rewritten 12→11 per effective transition, period 32. The frozen prediction at (36,44) was SUPPORTED. **The label was the controller's** (trigger EFFECTIVE_TRANSITIONS_ONLY, so not an OPEN record). G2 took 57 actions, of which 54 were total nulls before the first effective click |
| G2-2 | PASS | Recomputed from all 108 probe outcomes: the only change in the footprint is 12→11 (104 cells, 2 per effective transition). Every witness acted away from the footprint |
| G2-3 | PASS | EFFECTIVE_TRANSITIONS_ONLY holds on the whole record: 0 rewrites on the 56 nulls, exactly 2 on each effective transition |
| G3-1 | PASS | G3 closed with **8 levers** (E0053–E0057, E0060–E0062), no ambiguous entities, and no UNRESOLVED_ATTRIBUTION. D5 held: none of G3's 18 clicks hit any of G2's 54 null sites. G3 took 18 actions: a witness and a confirmation for each lever, plus 2 nulls |
| G4-1 | PASS | 8 G4-REACTIONS answers, one per lever, all by the controller. G4.1 took 0 actions |
| A-1 | PASS | All 8 levers CONFIRMED with an accepted explanation, and nothing pending. E0056's first run was cut off by the death and recorded as INTERRUPTED; it was re-studied next life and CONFIRMED |
| A-2 | PASS | Recomputed from the live gate events: each of the 9 runs is a consecutive press sequence on one click, and every press carries its executor (107 controller, 1 Duck). The interrupted run E0056-R1 is recorded and not counted |
| A-3 | PASS, two defects | All 8 explanations present the run as a finite observation, not a universal law. Defects: E0056's limitations were stored as 250 single characters (F2), and E0054's explanation says "3 presses" where the run had 4 |
| L-1 | **ANSWERED: yes** | Transition 88 rewrote the last 2 bar cells and returned GAME_OVER. The harness RESET (transition 89) restored the bar and the board. The death interrupted E0056 on its first press. D4 re-studied it (`life_restudies: {E0056: 1}`), and it CONFIRMED at transitions 90–93 |
| N-1 | Declared end, reported | The ladder ended at G4-A SATISFIED. The card then read `WAIT_FOR_NEXT_G4_SLICE` for 30.1 minutes of idle, until the crash. Before that point, no gate idled without a legal move |

## Reported figures (R)

- **Actions by gate:**
  - G2: 57
  - G3: 18
  - G4.1: 0
  - G4-A: 33, including 1 Duck press
  - 1 harness RESET
  - The harness reports 109 in total.
- **Duck turns to G4-A (11 turns, 19 requests, 19,438 tokens generated):**
  - 1 orientation;
  - 8 explanations;
  - 1 press after the counter-budget wake (the last confirmation press on E0055);
  - 1 wasted turn: after the GAME_OVER, Duck tried to submit the orientation again and was refused.
- **Time:**
  - G0 to G4.1 took about 6 seconds of turn time.
  - G4-A SATISFIED at about 9 minutes, averaging about 48 seconds per Duck turn.
  - The controller took 0.10 s per action on Kaggle.
- **Stop-and-wake reasons:**
  - orientation due;
  - each confirmed lever run;
  - the counter budget, at 2 ticks or fewer;
  - `G4-A has no lever left to run`, which started the idle loop.
- **Bar:** 12 ticks (24 cells) left at the end, in the second life.
- **Largest card by gate:** G4-A 11,975 characters. The other gates had no Duck card.
- **Largest request:** 19,149 prompt tokens up to G4-A; **48,311 during the idle loop**.
- **Orientation notes:** 3 (NAME, HUNCH, PROPOSAL), all UNCERTIFIED.
- **Extra-run requests:** none.
- **Memory pulls:** none.

## Findings

**F1 — No END owner (architecture; decision needed).** After the last gate is satisfied, the step
goes to Duck with nothing to do. This is R9-R08 deviation 4, still awaiting the Director's ruling,
plus R9-I02. It cost 30 minutes and ended as a crash. Every finished game in a multi-game run would
do the same, so it must be settled before D7.

**F2 — The orbit-answer validator accepts a string where a list belongs (code).**
`g4_orbits.validate_orbit_answer` iterates `limitations` and `competing_models` without checking the
type, so a string is stored one character per item (E0056). The gate validator
`virelai_gates._strings` refuses a string. The orbit path should do the same.

**F3 — The replay record drops the harness RESET (code; a flaw in a grading instrument).**
`tools/record_from_artifacts.py` builds records from probe outcomes only, so the RESET at transition
89 is missing. Replayed, E0056's re-study starts from the state before the death. The replay then
calls transition 90 a null and the lever DIVERGENT, while the live gate correctly recorded a toggle
and CONFIRMED it. The live run is right; the replay is wrong. This record must not become a fixture
until the builder carries resets.

**F4 — Single-request preflight understates multi-request turns (code).** T10 measured one request
at 33,158 tokens at most. A turn with many requests carries its tool results forward: 48,311 tokens
here, inside the 65,536-token window. It happened only in the idle loop, which F1 removes, but the
preflight should bound a whole turn.

**F5 — The offline plan assumed 5 levers; the world had 8 (risk 1 realised).** The machinery handled
this without change. The offline reference of 92 actions and 7 Duck turns does not transfer, because
it rested on the v2 record's 5 levers.

**F6 — Figures for D7.**
- The controller costs 0.10 s per action on Kaggle, a quarter of my cloud estimate. The cloud
  figure included the test harness's own file writes. So the concern about the interpreter lock
  shrinks.
- Duck's largest request during real work was about 19k tokens, so about 9 fit in the KV cache at
  once.
- Duck needed 11 turns for this whole game.

— Claude, Alpha build seat, 2026-09-29

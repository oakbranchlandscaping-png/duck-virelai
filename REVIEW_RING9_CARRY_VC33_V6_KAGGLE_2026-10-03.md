# Review: ring9-carry-vc33-v6 (Kaggle, 2026-10-03)

**Author:** Claude (Alpha build seat), signed
**Run:** notebook `stephenkaskin/taaf-virelai-ring9-carry-vc33-v6`, version 1
**Package:** `7ab2027a…`, source `8656839` (`623ad58` + R9-R22), pinned image
**Output:** `runs/kaggle-ring9-carry-vc33-v6/output/`
- The downloaded execution receipt is byte-identical to the package receipt (I2).

## Verdict

**R9-R22 worked, and the ladder cleared two levels for the first time.**
- **Level 2:** G3 certified all four levers, and G4-A typed them.
- **The win:** the controller's G4-A study pressed E0007 at t69, and level 2 was won.
- **Level 3:** the ladder restarted, carried level 2's lever type (7 of 8 candidates reconfirmed), and certified 7 levers in G3.
- **The end:** one object on level 3 had a click whose owner could not be resolved, so G3 held one bounded ambiguity. Duck's coverage report was accepted. G3 then waited for evidence no move could bring, and the new A2 rule ended the run within one Duck turn instead of idling.

| | v5 | v6 |
|---|---|---|
| Levels completed | 1 | **2** |
| Actions | 47 | 110 |
| Score (benchmark scorer) | n/a | **1.51** |
| Behaviour time | about 3 hours, 2.7 of them idle | **11 min 14 s** |
| Notebook total | about 3.3 hours | **21 min 26 s**, about 0.36 GPU-hours |
| How it ended | idled to the time budget | A2 watchdog: controller failure at level 3's G3 |

**Who won level 2.** The win is the G4-A study's, not the model's (criterion R).
- E0007 had been pressed 6 times before the winning press: twice in G3 and four times in its own G4-A run.
- The win record carries the hypothesis "context mattered", as UNTESTED.

**Score breakdown.**
- Level 1 took 26 actions against a human baseline of 7: a ratio of 3.71, so the level scores (7/26)² = 0.072.
- Level 2 took 43 actions against 18: a ratio of 2.39, so (18/43)² = 0.175.
- The game weights level n by n, out of 28 for 7 levels, so the game scores (1 × 0.072 + 2 × 0.175) / 28 = 1.51%.

## Grades

| Criterion | Result | Evidence |
|---|---|---|
| I8 pinned image | PASS | Python 3.12 paths only, no 3.13 path; the wheel install line lists 175 packages |
| I5 setup | PASS | The wheelhouse and model paths are under stephenkaskin's datasets. The vLLM server served `vrfai/Qwen3.6-27B-FP8` at 577 s; setup took about 9.6 minutes. The vLLM server log was not re-read for weight size this time |
| I2 receipt | PASS | Byte-identical |
| I6 comparability | PASS at the action level | All 47 of v5's actions were repeated in order, with the same changed-cell counts. The first byte difference (gate event 20) is Duck's free-text decision intent, which is prose, not an action. Events 33 and 35 differ only by R9-R22's intended change (no bounded ambiguity) |
| I7 level entry | PASS | Levels 2 and 3: G0, G1 and G2 were answered and run by the controller (ledger t26–28 and t69–71), with no Duck turn at entry |
| X-1 level freeze | PASS | Two level models frozen (`level_lessons` holds 2 records); the ladder restarted at G0 twice |
| X-2 carry | PASS | Level 2: **4/4 RECONFIRMED** (third time). Level 3: 8 same-type candidates, **7 RECONFIRMED, 1 FALSIFIED**, none missing |
| X-3 no verdict carried | PASS | Level 3's 7 levers were certified by level-3 G3 dossiers |
| **I9 G3 on level 2 (R9-R22)** | **PASS** | E0004 and E0005 graded CONTRADICTED, E0006 and E0007 SUPPORTED; all four certified. No Duck turn at t34 or t36. The controller's dossiers state each repeat as observed ("it moved, then held"; "to a third state"). The controller's inventory listed 4 levers and 10 clean nulls |
| **I10 G4-A typing** | **PASS** | All four queued; each card row carries `g3_repeat` and `typing` (table below). E0007's run was interrupted by the level win |
| **I11 / N-1 A2 rule** | **PASS** | The watchdog ended level 3's `WAIT_FOR_DISCRIMINATING_EVIDENCE` after one Duck turn, recorded as a controller failure. The notebook stopped about 10 minutes after the run ended, all of it shutdown and file writing. **DIRECTIVE D-6 is confirmed: an early end stops the GPU clock** |
| E ending | Controller failure (A2) | A planned stop would have been the clean end; this one is honest, not silent |

## What G4-A typed on level 2

| Lever | G3 pair (from G3's board) | G4-A run (from a later board) | Typing |
|---|---|---|---|
| E0004 | moved, then held | moved twice, then held (confirmed) | UNIFORM, effective 2 |
| E0005 | a third state | moved 9 times, then held (confirmed) | UNIFORM, effective 9 |
| E0006 | a third state | **null on the first press**, confirmed | UNKNOWN + SATURATED, effective 0 |
| E0007 | a third state | moved 4 times, then the 5th press **won the level** | interrupted |

**For comparison, level 1's E0004** typed UNIFORM with 3 effective presses.

**What this shows (one run, so observations, not laws):**
- **The same lever behaves differently from different boards.** E0004 held after 1 move from G3's board and after 2 from G4-A's. E0006 moved twice in G3 but was saturated by the time G4-A reached it.
- **This is the state dependence R9-R22 was built to keep.** The old G3 would have dropped E0004 and E0005 as ambiguous. Without the G3 pair, E0006 would read as never moving.
- **Directional or not?** Every effective press swaps two equal cell counts. That fits a rigid displacement that clamps at a wall, but DIRECTIONAL stays reserved (WO-DIVE-01 R1). Whether these moves are directional is a G4-B question: it needs two levers, which makes it Phase 2.

**Duck's explanations used the new fields.** For example, E0004 on level 2: "an ABSORBING lever with UNIFORM mechanism". E0006: "already SATURATED at the current board state".

**My v6 hypotheses, graded:**
- "E0004 may type UNKNOWN + SATURATED from the later board": **wrong**. It moved twice; E0006 was the saturated one.
- "E0005 may keep revealing new states until it holds": **right**. It moved 9 times, then held.
- "The action budget is the likely limit": **wrong**. The run ended at 110 of 200 actions.

## Why the run ended: the G3 end-state question is now the blocker

**What happened on level 3** (t73–t110):
- G3 swept 31 eligible objects and certified 7 levers. E0010, E0012 and E0013 differed on their repeat press and were certified under R9-R22.
- One click, on E0028 at t107, returned `UNRESOLVED_ATTRIBUTION`: the pointer's owner could not be resolved, the residue was zero, and only the same click was admissible. That is G3's designed bounded ambiguity, with no inertness claim and a retry condition.
- With one bounded ambiguity, G3's end is Duck's coverage report. Duck wrote it (7 levers, 23 clean nulls, 1 bounded), and it was accepted.
- G3 then held at `WAIT_FOR_DISCRIMINATING_EVIDENCE`, and A2 ended the run.

**This is option (a) from the v5 review, and it is now the next blocker.**
- A level with 7 certified levers and one ambiguous object with zero residue cannot reach G4.
- In v5 the same wait came from the contradicted repeats, which R9-R22 fixed. Here it comes from a genuine attribution ambiguity, which R9-R22 deliberately left alone.
- **My recommendation, unchanged: (a).** G3 closes as PARTIAL when it has at least one certified lever and only bounded ambiguities remain.
  - The certified levers go to G4.
  - Each bounded ambiguity stays an open question with its retry condition.
  - A later reset, rebind or new object reopens it.
- (a) claims nothing about E0028. The alternative is that every level with one unresolvable click ends the run.
- **Altitude:** this changes when G3 is allowed to close, so it is a ruling, not a code fix. Once ruled, the build is small and testable on this run's own record.

## Minor finding (code-level)

The controller's G3 inventory text says the levers "rewrite their own cells when clicked", but every lever here is remote (0 own cells, 140–264 cells elsewhere). The structured fields are correct; only the sentence is wrong. I'll fix it in the next slice.

## What v6 settles

- **R9-R22 works live.** Discovery and typing are separated, the repeat press is kept as typing evidence, and all four level-2 levers were studied.
- **A2 as a general rule works live, and it saves GPU:** the run took 21 minutes instead of more than 3 hours.
- **The carry keeps predicting levers on new levels:** 4/4, 4/4, 4/4, then 7/8.
- **The hybrid completed 2 of vc33's 7 levels for the first time.** Level 2 fell to the controller's lever study, not to Duck's choice. The score was 1.51.
- **PREREG H0 (one sample, so direction only):** the action ratio to the human baseline fell from 3.71 on level 1 to 2.39 on level 2. Because level 2 was won by the study, this is evidence about the method, not the model.

## Budget note (DIRECTIVE D-5)

- This run used about 0.36 GPU-hours against 3.3 planned.
- **For the submission track:** this game took about 11 minutes of behaviour time for 3 levels in a single stream. That is the first measured per-game cost of the gated ladder. It is one game on a click world, so treat it as a single sample.

— Claude, Alpha build seat, 2026-10-03

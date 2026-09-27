# Ring 9 G4 ft09 checkpoint: full Phase-1 drain, then G4.3

Source commit `8cfb7827cb94cb711c7924e877b41f3365765cde`. This private diagnostic runs the gated Duck on `ft09-0d8bbf25` for one pass, with at most 200 environment actions and 10800 seconds of behavior time after model setup.

The question: with levers that return to an exact prior state instead of crossing a level, does the machine orbit and classify every lever, report Phase 1 complete, and only then open G4.3, which re-confirms each recurrence by one predicted period?

## Preregistered grading (from artifact state, not prose)

- P: G3 closes on ft09 with at least two confirmed levers and a G4.1 anatomy for each. A stall at or before G3 is a G0-G3-on-ft09 finding (ft09 has never been through the ladder live) and leaves the G4 criteria ungraded, not failed.
- C1: every confirmed lever drains through Phase 1 - each G4.2 orbit reaches a masked null or an exact prior-state recurrence and lands a class (TOGGLE / CYCLE / ABSORBING / RECURRENT).
- C2: the final LeverOrbitSet has pending_lever_entities empty and phase1_status COMPLETE; products accumulate and are never replaced.
- C3: no prior lever's orbit or class is invalidated.
- C4: after each accepted orbit the gate stays in G4.2 while any lever is pending; G4.3 opens only once phase1_status is COMPLETE.
- C5: G4.3 re-confirms a recurrence by one predicted additional period, grading every masked address (EXACT_RECURRENCE_RECONFIRMED or RECURRENCE_DIVERGED at the first mismatch).
- C6: Duck's accepted answers distinguish an observed finite recurrence from a universal or unconditional law.
- C7: no deadlock. If a boundary interrupts an orbit, the lever is recorded as interrupted and leaves pending; a level transition closes the level's G4 study with the G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9 card.
- I1: G0 assigns CLICK/God Mode from metadata.
- I2: G2 closes with a valid mask or the bounded COUNTER_NOT_OBSERVED_WITHIN_OPENING product; it does not stall.
- I3: G3 inherits the ranked opening frontier and completes the click sweep.
- I4: G4.2 records recurrences without ticker contamination.

Historical context, not a prediction to grade against: a September 8 controlled artifact found five self-reactive ft09 controls, four with exact two-state returns, and an independent ticker. Do not compare this run's scores or action counts with vc33.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-phase1-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-ft09-phase1-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

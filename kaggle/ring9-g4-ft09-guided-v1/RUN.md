# Ring 9 ft09 guided checkpoint: stated-target G2 and G4-A

Source commit `3c89c2191190b07810c9f3f7b92b7d1617157a3a`. This private diagnostic runs the gated Duck on `ft09-0d8bbf25` for one pass, with at most 200 environment actions and 10800 seconds of behavior time after model setup.

The question: given stated targets instead of scripted moves, does Duck find, label and mask the counter with a pure mask (axiom A1), pass the scripted G3 sweep, and then study every lever to a confirmed endpoint by its own presses (G4-A), with no controller idle (axiom A2)?

## Preregistered grading (from artifact state, not prose)

- P: G3 closes on ft09 with at least two confirmed levers and a G4.1 anatomy for each. G2 criteria are graded regardless; a stall at or before G3 leaves the G4 criteria ungraded, not failed.
- G2-1 (axiom A1): G2 closes either with a counter model and mask after one frozen footprint-scoped prediction (COUNTER_REWRITE or COUNTER_SILENT, on an action Duck chose) is SUPPORTED, or as COUNTER_NOT_OBSERVED after every ranked object was clicked. Record which.
- G2-2 (purity, recomputed from artifacts): every recorded change inside the mask footprint follows the counter rewrite or its inverse, and at least one witness acted away from the footprint.
- A-1 (G4-A): every lever ends with a CONFIRMED or DIVERGED run and an accepted explanation, or is recorded as interrupted; the final LeverOrbitSet is phase1_status COMPLETE or CLOSED_BY_LEVEL_BOUNDARY with nothing pending, and no prior lever's run or class is invalidated.
- A-2 (audit fidelity, recomputed from gate events): each accepted run is a consecutive same-click sequence of Duck-chosen presses whose stop and confirmation dispositions match the masked states; broken runs are recorded, never counted.
- A-3: Duck's accepted explanations distinguish the observed finite run from a universal or unconditional law.
- N-1 (axiom A2): no gate idles without a legal move. Any such stall ends as controller_no_legal_move within the watchdog limit; a declared end (level closed, WAIT_FOR_NEXT_G4_SLICE) is reported with its idle time, not failed.
- R (reported, not graded): actions and wall time per gate; Duck's G2 and G4-A choices (lever presses versus other actions, broken runs, rejected G2 candidates); the prediction form Duck chose in G2.
- I1: G0 assigns CLICK/God Mode from metadata; guided capabilities (GUIDED_ACTION) are served for G2 and G4-A.
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: G3 inherits the G2 frontier (the ranked prefix Duck covered) and completes the click sweep.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.

Baseline for comparison of controller behavior only (not scores): the scripted ft09 run `ring9-g4-ft09-phase1-v1` (56 G2 actions, then a G2 deadlock). Prior evidence, not a prediction to grade against: in that run the bottom bar ticked only on the two clicks that changed a control.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

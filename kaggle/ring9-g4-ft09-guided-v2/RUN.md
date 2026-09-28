# Ring 9 ft09 guided checkpoint v2

Source commit `4329185bd77eec5f3a4bb8c73d76f08bd36cb1ce` (R9-R04 + R9-R05). This private diagnostic runs the gated Duck on `ft09-0d8bbf25` for one pass, with at most 200 environment actions and 10800 seconds of behavior time after model setup.

The question: with the G3 card bounded (A6), the counter label checked against the record (A1 v2) and recolour-safe entity identity (R9-R05), does the stated-target ladder carry ft09 past G3 to a G4-A lever study that Duck executes by its own presses?

## Preregistered grading (from artifact state, not prose)

- P: G3 closes on ft09 with at least two confirmed levers and a G4.1 anatomy for each. G2 criteria are graded regardless; a stall at or before G3 leaves the G4 criteria ungraded, not failed.
- G2-1 (axiom A1): G2 closes either with a counter model and mask after one frozen footprint-scoped prediction (COUNTER_REWRITE or COUNTER_SILENT, on an action Duck chose) is SUPPORTED, or as COUNTER_NOT_OBSERVED after every ranked object was clicked. Record which.
- G2-2 (purity, recomputed from artifacts): every recorded change inside the mask footprint follows the counter rewrite or its inverse, and at least one witness acted away from the footprint.
- G2-3 (A1 v2, recomputed from artifacts): the accepted counter model's trigger is admissible for the trigger class computed from the whole G2 record (EVERY_TRANSITION, EFFECTIVE_TRANSITIONS_ONLY, IRREGULAR, or OPEN admitting either simple class).
- A6-1 (axiom A6): no binding gate card exceeds the runtime's 24,000-character budget at any gate; a run that ends on the card-size guard fails this criterion.
- G3-1 (prediction from the offline ladder, R9-R05): G3 witnesses both ft09 control tiles as levers (LOCAL_LEVER_WITNESS, prospectively confirmed) and neither is filed as UNRESOLVED_ATTRIBUTION. Graded only if G2 closes with a counter model.
- A-1 (G4-A): every lever ends with a CONFIRMED or DIVERGED run and an accepted explanation, or is recorded as interrupted; the final LeverOrbitSet is phase1_status COMPLETE or CLOSED_BY_LEVEL_BOUNDARY with nothing pending, and no prior lever's run or class is invalidated.
- A-2 (audit fidelity, recomputed from gate events): each accepted run is a consecutive same-click sequence of Duck-chosen presses whose stop and confirmation dispositions match the masked states; broken runs are recorded, never counted.
- A-3: Duck's accepted explanations distinguish the observed finite run from a universal or unconditional law.
- N-1 (axiom A2): no gate idles without a legal move. Any such stall ends as controller_no_legal_move within the watchdog limit; a declared end (level closed, WAIT_FOR_NEXT_G4_SLICE) is reported with its idle time, not failed.
- R (reported, not graded): actions and wall time per gate; Duck's G2 and G4-A choices (lever presses versus other actions, broken runs, rejected G2 candidates or labels); the prediction form Duck chose in G2; bar cells remaining at the end; the largest card per gate.
- I1: G0 assigns CLICK/God Mode from metadata; guided capabilities (GUIDED_ACTION) are served for G2 and G4-A.
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: G3 inherits the G2 frontier (the ranked prefix Duck covered) and completes the click sweep.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.

Baseline for comparison of controller behavior only (not scores): `ring9-g4-ft09-guided-v1` (G2 closed live at transition 57 under A1; the run crashed at G3 entry on a 67,939-character card). Prior evidence, not a prediction to grade against: the bar ticked on 3 of 3 control clicks and 0 of 54 dead clicks. Offline, the recorded control law continued by hypothesis reaches G4-A SATISFIED at transition 131.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v2`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v2`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

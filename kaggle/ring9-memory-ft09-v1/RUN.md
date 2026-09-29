# Ring 9 memory, ft09 v1

Source commit `8ca9fc94e012839db7bbe1ffe10733a75277a882` (R9-R06 to R9-R11). This private diagnostic runs the gated agent on `ft09-0d8bbf25` for one pass, with at most 200 environment actions and 10800 seconds of behavior time after model setup. Same world, model and budget as `ring9-g4-ft09-guided-v2`: only the source changed.

The question: with Virelai memory (a bounded slot-built card, the controller executor, recall, the orientation turn, the G4 economy and the lives rule), does ft09 reach G4-A with Duck spending its turns only on judgment, and every card within budget?

## Preregistered grading (from artifact state, not prose)

- Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, gate answers, probe envelopes, annotations), not from prose.
- M5-1 (axiom A6, memory M-1): no binding card exceeds the 16,200-character slot budget at any turn (turn ledger card_chars), and the runtime's 24,000-character guard never fires.
- M5-2 (memory M8, rulings D2 and D3): G0 through G4.1 close with zero model calls: every turn ledger row before Duck's first is executor CONTROLLER with no model request, and Duck's first turn is the orientation turn.
- G2-1 (axiom A1): G2 closes with a counter model and mask after one frozen footprint-scoped prediction is SUPPORTED, or as COUNTER_NOT_OBSERVED after every ranked object was clicked. Record which, and whether the label was the controller's (an OPEN or IRREGULAR record hands it to Duck).
- G2-2 (purity, recomputed from artifacts): every recorded change inside the mask footprint follows the counter rewrite or its inverse, and at least one witness acted away from the footprint.
- G2-3 (A1 v2, recomputed from artifacts): the accepted trigger is admissible for the trigger class computed from the whole G2 record.
- G3-1 (ruling D5; prediction from the v2 record): G3 closes with at least two ft09 control tiles witnessed as levers, none filed UNRESOLVED_ATTRIBUTION, and G3 re-clicks no object G2 saw as a total null.
- G4-1 (the G4.1 split): every G3 lever has a G4.1 anatomy answer, each by the controller.
- A-1 (G4-A): every lever ends with a CONFIRMED or DIVERGED run and an accepted explanation, or is recorded as interrupted; the final LeverOrbitSet is COMPLETE or CLOSED_BY_LEVEL_BOUNDARY with nothing pending, and no prior lever's run or class is invalidated.
- A-2 (audit fidelity, recomputed from gate events): each accepted run is a consecutive same-click press sequence whose stop and confirmation dispositions match the masked states; every press carries its executor; broken runs are recorded, never counted.
- A-3: Duck's accepted orbit explanations distinguish the observed finite run from a universal or unconditional law.
- L-1 (ruling D4; the open ft09 question): report whether the counter bar reaching zero ends the life (a GAME_OVER boundary on that transition). If any death interrupts a lever study on the same level, that lever is re-studied (life_restudies) and the study still ends COMPLETE or CLOSED_BY_LEVEL_BOUNDARY.
- N-1 (axiom A2): no gate idles without a legal move; a declared end is reported with its idle time, not failed.
- R (reported, not graded): Duck turns and model requests per gate; minutes to G3 closure and to G4-A; actions per gate; every stop-and-wake reason; bar cells remaining at the end; the largest card per gate; Duck's orientation notes; any extra-run request.
- I1: G0 assigns CLICK/God Mode from metadata, and the controller executor is on (probe envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: the run writes the memory artifacts: turn ledger, gate answers with executor, and annotations if Duck oriented.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.

Baseline for comparison of behavior only (not scores): `ring9-g4-ft09-guided-v2`: G2 closed live; G3 confirmed five levers; the run crashed on a 25,502-character card at the fifth dossier, after 121 actions and about 130 Duck turns. Offline reference, not a graded prediction: G4-A SATISFIED in 92 actions with 7 Duck turns, on the v2 record's law continued by hypothesis.

Request preflight (T10): worst case 33158 tokens against a 65536-token window.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-memory-ft09-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-memory-ft09-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

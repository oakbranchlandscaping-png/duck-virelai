# Ring 9 G4-B, ft09 v1

Source commit `e1636b1622b3cd927c33a45fb6a6abbbe00eb3d4` (R9-R06 to R9-R12). This private diagnostic runs the gated agent on `ft09-0d8bbf25` for one pass, with at most 200 environment actions and 10800 seconds of behavior time after model setup. Same world, model and budget as `ring9-memory-ft09-v1`: only the source changed.

The question: after G4-A, does Duck work out how ft09's levers affect each other through frozen predictions the controller takes and the gate grades, describe the lever set in plain language on supported evidence only, and does the run then end cleanly?

## Preregistered grading (from artifact state, not prose)

- Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, gate answers, probe envelopes, annotations), not from prose.
- M5-1 (axiom A6): no binding card exceeds the 16,200-character slot budget at any turn (turn ledger card_chars), and the runtime's 24,000-character guard never fires.
- M5-2 (memory M8, rulings D2 and D3): G0 through G4.1 close with zero model calls, and Duck's first turn is the orientation turn.
- G2-1 to G2-3 and G3-1 (as in ring9-memory-ft09-v1): G2 closes with a counter model and mask after a SUPPORTED frozen prediction, purity and trigger admissibility recomputed from artifacts; G3 closes with at least two levers witnessed, none UNRESOLVED_ATTRIBUTION, re-clicking no G2 total null. Record the lever count.
- A-1 (G4-A): every lever ends CONFIRMED or DIVERGED with an accepted explanation (or recorded as interrupted), and the LeverOrbitSet is COMPLETE or CLOSED_BY_LEVEL_BOUNDARY with nothing pending. Any same-level death re-studies the interrupted lever (D4). A-2 (audit fidelity) and A-3 (scoped explanations) as before.
- B-1 (G4-B protocol): G4-B opens only after G4-A is COMPLETE; every G4-B action is exactly the action of a frozen LEVER_PREDICTION (Duck's gate answer precedes it), taken by the CONTROLLER (probe envelope executor), and graded on a transition after the prediction was frozen. Duck takes no G4-B action itself.
- B-2 (grading fidelity, recomputed from probe outcomes): for every graded prediction, the per-lever outcomes (UNCHANGED, STEPS, CHANGES) and elsewhere, recomputed from the masked frames and the G4.1/G4-A regions, match the recorded observed outcomes, and SUPPORTED/CONTRADICTED follows.
- B-3 (G4-B closure): every lever is the pressed lever of at least one graded prediction; Duck's LEVER_RELATIONS description is accepted; every relation cites only SUPPORTED predictions that pressed or named its levers; open_conditions equals the recorded missing conditions; contradicted predictions remain in the LeverRelationSet.
- E-1 (R9-I02, the controller owns the end): after the last built gate is satisfied, the run ends with solver_note beginning 'planned_stop:', the run state is not crashed, and no model request is made after the gate closed.
- N-1 (axiom A2): no gate idles without a legal move.
- R (reported, not graded): Duck's description of the lever set, verbatim; every prediction (action, expectations, grade, what missed); how many predictions pressed a lever while another lever was away from its start state (tests of relations beyond single-lever runs); Duck turns and requests per gate; minutes to G4-A and to G4-B closure; actions per gate; stop-and-wake reasons; deaths and re-studies; bar remaining; largest card per gate.
- I1: G0 assigns CLICK/God Mode from metadata, and the controller executor is on (probe envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: the run writes the memory artifacts: turn ledger, gate answers with executor, and annotations if Duck oriented.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.

Baseline for comparison of behavior only (not scores): `ring9-memory-ft09-v1`: G4-A SATISFIED at about 9 minutes after 108 probe actions (8 levers, one death, one re-study) and 11 Duck turns; the run then idled 30 minutes with nothing to do and crashed. Offline reference, not a graded prediction: the controller repeats those 108 actions; a card-only Duck then freezes 8 predictions, all SUPPORTED, and the run stops cleanly.

Request preflight (T10): worst case 33158 tokens against a 65536-token window, for one request (a turn with many requests can carry more; finding F4 of the v1 review).

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4b-ft09-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4b-ft09-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

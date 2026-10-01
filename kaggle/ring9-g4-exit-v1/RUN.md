# Ring 9 G4 CLICK exit, ft09 and vc33

Source commit `d2bf323eaf2fe08a0b64b058e1b958417f344fd1` (R9-R06 to R9-R14). This private diagnostic runs the gated agent on `ft09-0d8bbf25`, `vc33-5430563c`, one after the other, one pass each, with at most 200 environment actions and 10800 seconds of behaviour time per world (21600 s for the run) after model setup. Same model and per-world budget as `ring9-g4b-ft09-v1`.

The question (the G4 CLICK exit, BUILD_PLAN v11): does each world end level 1's G4 with a supported LeverReactionLaw set: every lever studied alone, relations tested by graded predictions, and a description that predicts one untested case?

## Preregistered grading (from artifact state, not prose)

- Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, gate answers, probe envelopes, annotations), not from prose.
- Each criterion below is graded per world (ft09, then vc33) unless it says otherwise.
- M5-1 (axiom A6): no binding card exceeds the 16,200-character slot budget, and the 24,000 guard never fires. M5-2: G0 through G4.1 close with zero model calls; Duck's first turn is the orientation, accepted within 2 turns (F1 fixed).
- G2 (A1): a counter model and mask with a SUPPORTED frozen prediction, purity and trigger admissibility recomputed from artifacts, or COUNTER_NOT_OBSERVED after every ranked object. Record whether the trigger class was OPEN (then the label is Duck's; deviation 1). G3: at least two levers witnessed, none UNRESOLVED_ATTRIBUTION, no re-click of a G2 total null.
- A (G4-A): every lever ends CONFIRMED or DIVERGED with an accepted explanation (or interrupted), the LeverOrbitSet COMPLETE or CLOSED_BY_LEVEL_BOUNDARY; same-level deaths re-study (D4); audit fidelity and scoped explanations as before.
- B (G4-B): every G4-B action is exactly a frozen prediction's, taken by the CONTROLLER, graded on a later transition with a current freeze stamp (F2 fixed); grades re-derive from the masked frames; every lever pressed in a graded prediction; the description accepted, each relation citing only SUPPORTED predictions that pressed or named its levers; open_conditions equal the recorded missing conditions.
- C (G4-C): each law prediction is untested (no graded prediction took its action from its masked board), names valid relations, is taken by the CONTROLLER and graded; a CONTRADICTED one reopens G4-B and stays on the record; the gate closes on a SUPPORTED one with the LeverReactionLawSet COMPLETE, or on a level change.
- E (R9-I02): each world ends with solver_note 'planned_stop:', not crashed, with no model request after its last gate closed.
- EXIT (both worlds; BUILD_PLAN v11): the CLICK branch of G4 closes if and only if both ft09 and vc33 end level 1's G4 with a LeverReactionLawSet of status COMPLETE.
- N-1 (axiom A2): no gate idles without a legal move.
- R (reported, not graded): each world's description verbatim and its law test; every prediction; reopenings of G4-B; relation tests beyond single-lever runs; Duck turns, requests and minutes per gate; deaths and re-studies; bar remaining; largest card per gate; vc33's lever count, lever classes and counter trigger class.
- I1: G0 assigns CLICK/God Mode from metadata, and the controller executor is on (probe envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: the run writes the memory artifacts: turn ledger, gate answers with executor, and annotations if Duck oriented.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.

Baselines for behaviour only: ft09 passed G0 to G4-B live twice (`ring9-memory-ft09-v1`, `ring9-g4b-ft09-v1`), with identical controller actions both times. vc33 reached G3 and G4.1 on earlier stacks (`ring9-g3-vc33-closure-v1` to `v3`) and has not run on the memory stack.

Request preflight (T10): worst case 33158 tokens against a 65536-token window, for one request.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-exit-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-exit-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

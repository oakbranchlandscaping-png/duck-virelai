# Ring 9 G4 NAV checkpoint, ls20

Source commit `72adbe3fc644da536950b2d8af1341ecb8e9f0e4` (R9-R06 to R9-R19). This private diagnostic runs the gated agent on `ls20-9607627b`, one pass, with at most 200 environment actions and 10800 seconds of behaviour time after model setup. Same exact model and per-world budget as `ring9-carry-vc33-v1`.

The question: can G1's observed embodied-control evidence become a stable control map, route the ego toward ranked visual targets, and preserve target identity while separating approach frames from contact evidence through G4?

## Preregistered grading (from artifact state, not prose)

- Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, gate answers, probe envelopes, annotations), not from prose.
- G0: ls20 is assigned NAVIGATION from the displayed action surface.
- G1: the embodied ego is demonstrated and described; the NavControlMap is nonempty and every bearing cites structured displacement evidence. ACTION5 is not promoted without stable observed ego translation.
- G2: a total counter mask is certified and counter-only change ceases to count as semantic progress.
- G3-1: one ranked target remains bound through its route; controller actions are labelled APPROACH or CONTACT_ATTEMPT and cite that target.
- G3-2: planned traversal uses demonstrated stands only, except one explicit frontier step at a time.
- G3-3: a completed contact creates a target-bound ContactEpoch and records scoped null, attributed lever evidence, a boundary, or an explicit unresolved result. Step count alone never proves inertness or unreachability and never closes a target.
- G3-4: any confirmed BODY lever carries a target-bound NAV ContactProcedure into G4.
- G4-A, if reached: approach transitions record NAV_APPROACH with orbit_advanced false; only the terminal target contact advances the orbit. The run may stop at its action or time budget without this later criterion being graded.
- G4-B/C, if reached: predictions stay bound to the target intervention; approach frames leave them pending and only the contact frame grades them.
- E: the run ends by planned stop or explicit action/time budget and does not crash.
- R (reported, not graded): deepest gate reached, actions and Duck time, control-map bearings, target roster outcomes, confirmed levers, deaths, levels, and any observed win. A win is not required.
- I0: the shipped source holds no tools/live_level_carry_gate.py and no world name in the solver's executable code other than the harness's public game roster (packager guard).
- I1: G0 assigns NAVIGATION from metadata, and the controller executor is on (probe envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: the run writes the memory artifacts: turn ledger, gate answers with executor, probe envelopes, control-map evidence, and contact epochs where reached.
- I4: approach and contact remain distinct in recorded evidence and only contact can advance G4.

No prior ls20 run contains R9-R19. Earlier CLICK and NAV results are context, not a behavioral baseline for this checkpoint.

Request preflight (T10): worst case 33158 tokens against a 65536-token window, for one request.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

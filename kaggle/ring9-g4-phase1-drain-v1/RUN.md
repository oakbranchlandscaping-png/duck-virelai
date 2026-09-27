# Ring 9 G4 vc33 Phase-1 drain checkpoint (S1 return edge)

Source commit `f8a967e909049577885bf7f9b473c98bd45b20f7`. This private diagnostic runs the gated Duck on vc33 for one pass, with at most 160 environment actions and 7200 seconds of behavior time after model setup.

The checkpoint carries the G0-G3 path into G4 and tests the S1 descent controller: the machine must hold G4.2 until every confirmed lever is orbited with consecutive same-lever presses to a period and classified, and only then open G4.3 (Phase 2).

## Preregistered live grading (from artifact state, not prose)

- C1: every confirmed lever drains through Phase 1 - each G4.2 orbit reaches a period with a stop disposition and lands a lever class (TOGGLE/CYCLE/ABSORBING/RECURRENT).
- C2: the final LeverOrbitSet lists every confirmed lever in lever_entities with pending_lever_entities empty; products accumulate and are never replaced.
- C3: no prior lever's orbit or class is invalidated anywhere in the gate journal.
- C4: after the first lever's orbit is accepted, the active gate remains G4.2 for the next pending lever; G4.3 opens only after pending_lever_entities is empty.

Precondition: S1 is gradable only if the run closes G3 with at least two confirmed levers. G3 closure on this exact served model has not yet been observed on Kaggle; a stall at or before G3 is a G3-on-this-model finding and leaves S1 ungraded, not failed.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g4-phase1-drain-v1`  
Notebook: `stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.

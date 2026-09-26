# G4.2 repeated-activation local pilot

**World:** `vc33-5430563c`  
**Model:** `qwen/qwen3.6-35b-a3b` through OpenRouter, AtlasCloud FP8 requested  
**Scope:** G4.2 CLICK orbit discovery  
**Configuration:** `configs/g4-orbits-vc33-openrouter-fast.json`

## Question

After the established G0-G4.1 path completes, does Duck repeatedly activate each confirmed lever,
continue through novel counter-masked states, and stop and explain the lever only when the
controller observes a masked null or exact prior-state recurrence?

## Pass conditions

1. G3 and G4.1 reproduce their prerequisite products without changing the G4.2 grade.
2. G4.2 binds only confirmed lever identities and their exact accepted click interventions.
3. Every novel masked state causes another activation of the same lever.
4. The controller stops the current lever on the first actual masked null or exact recurrence and
   records the complete state and effect sequence.
5. Duck submits an accepted `LEVER_ORBIT_OBSERVATION` using the supplied sequence, stop
   disposition, recurrence fields, and evidence references.
6. The controller advances to every confirmed lever and emits one `LeverOrbitSet`.
7. Calls to the older passive agenda do not replace the binding gate objective.

Level score, win discovery, final reaction laws, capacity, reversal, conditions, and coupling are
outside this checkpoint. The 48-action and 30-minute limits are external safety bounds; reaching
one with novel states still appearing is `UNRESOLVED`, not an orbit completion.

## Failure classification

- A wrong action, unmasked counter loop, broken state chain, or premature stop is an infrastructure
  failure.
- A rejected answer that fails to use the supplied orbit is behavioral comprehension friction.
- A boundary before null or recurrence is an interrupted checkpoint and supplies no G4.2 pass.
- Runtime exhaustion after a `LeverOrbitSet` is teardown friction.
- This sparse fast-model run is a development check, not the dense rehearsal or Kaggle milestone.

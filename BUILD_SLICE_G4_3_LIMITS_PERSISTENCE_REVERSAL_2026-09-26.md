# G4.3 limits, persistence, and reversal

**Status:** built and offline-confirmed for the CLICK branch; live unconfirmed  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Predecessor:** G4.2 repeated activation and orbit discovery  
**Next planned slice:** G4.4 conditions

## Narrow goal

G4.3 asks what the observed end of a completed CLICK-lever orbit supports. It keeps three claims
separate:

1. **Limit:** does one additional activation reproduce the G4.2 masked null?
2. **Persistence:** when a prior G3 scoped-null click is available as a control, does the endpoint
   survive it?
3. **Reversal:** does another already-confirmed lever restore an exact earlier orbit state, and does
   the original lever then become effective again?

G4.3 does not infer cross-level transfer, hidden purpose, universal saturation, or necessary and
sufficient conditions. Those belong to later gates.

## Ported prior art

- `inference/framework/virelai_semantic/depth_probe.py`: two consecutive endpoint nulls are the
  confirmation floor. One comes from the G4.2 stop and one is newly executed by G4.3.
- `inference/framework/virelai_semantic/typing.py`: recurrence and state transition claims require
  exact observed state identity; mechanism and condition remain separate.
- V4 cycle/state tracking: compare complete counter-masked grid addresses and preserve every action
  edge.

The old planner's fixed queue and labels were not copied. The new implementation consumes active
Ring 9 entity ids, exact interventions, orbit addresses, reversible G2 mask, and lossless executed
frames.

## Implemented controller

`inference/framework/g4_limits.py` owns the evidence model. A `LeverLimitStudy` moves through:

```text
CONFIRM_ENDPOINT
-> optional TEST_PERSISTENCE
-> TEST_INVERSE candidates
-> REAPPLY_ORIGINAL after a candidate changes the state
-> ANSWER_REQUIRED
```

The controller distinguishes:

- `SATURATED_AT_OBSERVED_STATE`: the second scoped endpoint null was observed;
- `PERSISTED_THROUGH_CONTROL`: the exact masked endpoint survived the bounded control;
- `EXACT_ORBIT_STATE_RESTORED`: a candidate returned to an exact earlier G4.2 address;
- `EXACT_REVERSAL_DEMONSTRATED`: exact restoration was followed by renewed original-lever effect;
- `STATE_RELEASED_WITHOUT_EXACT_RESTORATION`: the candidate changed the state but did not prove an
  inverse;
- `NO_INVERSE_OBSERVED`: all available confirmed candidates were null in the tested state.

A terminal boundary yields `BOUNDARY_INTERRUPTED` and cannot be converted into a limit answer.

`inference/framework/virelai_gates.py` registers `G4.3-LEVER-LIMITS`, binds only completed CLICK
orbits ending in `NULL_AT_OBSERVED_STATE`, emits exact probe capabilities, applies the stable G2
mask, and requires Duck to explain the immutable record. Full records are callable through
`virelai('limit', id=entity_id)`; the compact card contains the current phase and next operation.

The output product is `LeverLimitStudySet`. Its claims remain level-local and state-scoped.

## Exit criteria

The slice is locally complete when tests prove:

- G4.2 routes into G4.3 after a completed masked-null orbit set;
- an endpoint requires the additional repeated null;
- a persistence control cannot silently become a reversal claim;
- exact reversal requires an earlier orbit address plus original-lever re-enablement;
- an arbitrary changed state is recorded only as release;
- boundary interruption and discontinuous frames fail closed;
- Duck cannot invent an inverse entity or alter structured conclusions.

## Evidence

Focused G4.1–G4.3 tests: **17 passed**.  
Full offline suite excluding the two online/native suites: **360 passed**.  
Ruff on the changed Python surface: **passed**.

This proves the controller and evidence contracts locally. It does not prove that a served model
will follow G4.3, that vc33's two controls are inverses, or that any endpoint law transfers across
levels.

## Entity-local handoff and remaining boundary

G4.2 now emits an entity-local `LeverOrbitSet` as soon as the active lever's accepted orbit is
complete. Its payload explicitly lists both completed and pending lever entities. This lets E0004
descend immediately into G4.3 while E0005 remains pending; no boundary interpretation is involved.

The future G4 scheduler must return to pending levers after the active entity completes the deeper
G4 subtree. That return edge remains unbuilt. It must preserve the pending list and must not pretend
that any interrupted lever experiment was completed.

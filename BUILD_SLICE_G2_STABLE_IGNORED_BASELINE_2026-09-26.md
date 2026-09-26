# Build slice — G2 stable ignored baseline

## Decision

G2 exists to identify bookkeeping noise and emit a reversible total mask. Once a prospective recurrence demonstration supports that mask, the counter becomes a fixed subtraction baseline. Later gates actively ignore its behavior.

The counter must not:

- retain an open min/max obligation;
- consume later probes or model attention;
- revise its G2 memory product as it ticks;
- invalidate G3 or G4 products;
- reopen the targeting sequence because its rate or terminal consequence changes.

Raw frames remain preserved. “Ignore” means exclude the mask footprint from world-state identity and causal attribution. It does not mean delete pixels or alter the environment record.

## Runtime contract

After a supported G2 demonstration:

- `CounterModel.status = LOCKED_AS_MASK_BASELINE` unless an extremum happened to be observed during G2 itself;
- `boundary_obligation = None`;
- the G2 product remains stable;
- later event records carry `policy = MASK_AND_IGNORE_AFTER_G2`;
- later transitions still enter the entity ledger so new world objects remain observable;
- no later counter event can invalidate descendants.

## Regression fixed

The vc33 G4.2 v2 run reached its first repeated activation and correctly classified a 264-cell counter-masked change as novel. The old cross-gate monitor then replaced the G2 product, which invalidated G3 and G4 and produced a contradictory completed-but-answer-required G3 state.

The regression test now reproduces an open historical boundary obligation, executes a novel G4.2 activation, and proves:

1. the active gate remains G4.2;
2. G2, G3, and G4 product identities remain unchanged;
3. activation two is immediately available;
4. a later masked null can close the observed orbit normally.

## Validation

- Focused counter/G4 suite: 35 passed.
- Full offline suite: 351 passed.
- Excluded by established convention: live `test_online_arcade.py` and native-observer integration `test_duck_native_observer.py`.

## Next live criterion

Repeat vc33 with the same bounded OpenRouter profile. A successful run must pass from the first novel E0004 state directly to E0004 activation two without returning to G3. Game score remains outside this slice.

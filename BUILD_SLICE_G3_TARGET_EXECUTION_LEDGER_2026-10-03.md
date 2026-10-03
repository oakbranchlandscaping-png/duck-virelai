# Build slice: G3 visual target execution ledger

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-03  
**Status:** BUILT AND LOCALLY VERIFIED; LIVE UNCONFIRMED

## Director ruling

G3 NAV must expose one complete visual-object target list before the sweep begins, execute that
list in rank order, and leave every eligible object with an evidence-grounded result:

- `REACHABLE`, with its observed contact result and physics type; or
- `UNREACHABLE_IN_CURRENT_WORLD_STATE`, because the avatar exhausted its demonstrated reachable
  component without finding a contact surface.

An unreachable result is provisional. A world delta, new floor stand, yielded edge, changed target,
or changed control law reopens it.

## Why this slice was needed

The controller already maintained a frozen G2 frontier, a G3 lifecycle journal, immutable NAV
contact epochs, and reachability certificates. The evidence existed, but a reviewer had to join
several structures to answer the simple question: “Was every visual object actually attempted, and
which ones could the avatar reach?”

The ls20 v2 checkpoint did not answer that question. It entered G3 and spent four actions pursuing
rank-one target `M0009/E0001`, but the action cap arrived before that target or the rest of the
roster received terminal classifications.

## Implementation

The existing `virelai('inventory', …)` view is now an explicit target-execution ledger. Every
eligible row carries:

- frozen rank, member ID and entity ID;
- visual type: integer, shape family, cell count, anchor, bounding box and counter-mask relation;
- execution status;
- reachability status and its evidence basis;
- observed contact type (`REFUSED`, `ENTERED`, `DISPLACED` or `TRANSFORMED`) when contact occurs;
- physics type (`LEVER`, `SCOPED_NONRESPONDER`, `UNRESOLVED_EFFECT`,
  `UNTESTED_BEYOND_REACH`, or `NOT_YET_TYPED`);
- evidence references and the condition that would reopen a provisional result.

NAV contact epochs are retained at level scope so death cannot erase a completed contact from the
ledger. Counter objects remain accounted for as `ROLE_EXCLUSION / COUNTER_MASK`; they are not sent
back through G3 as targets.

Each G3 action and accepted G3 answer now rewrites one run artifact:

`<world>_<pass>_g3_target_ledger.json`

It contains the complete current roster, even when Duck receives only the bounded prompt window.
This preserves the compact-card design while making the entire sweep directly gradeable.

## Label laws

For NAV/HYBRID:

- an object is `REACHABLE` only after an actual bound contact attempt is recorded;
- an object is `UNREACHABLE_IN_CURRENT_WORLD_STATE` only after deterministic routing proves there
  is no contact press and no untried edge anywhere in the reachable component;
- all other objects remain `NOT_YET_DETERMINED`;
- route exhaustion never proves inertness or permanent unreachability.

For CLICK, metadata makes every eligible coordinate target directly addressable, so reachability is
`REACHABLE` with basis `POINTER_DIRECT_ADDRESS`; its execution status stays queued until clicked.

## Verification

- Focused G3/NAV suites: **40 passed**.
- Complete active-source suite: **553 passed**, 14 third-party deprecation warnings, 0 failures.
- New tests cover the prepopulated roster, observed-contact reachability, certified route
  exhaustion, and the complete standalone artifact.

## Live exit criterion

The next ls20 checkpoint passes only when the downloaded target-ledger artifact proves:

1. the roster was populated before G3 execution;
2. all eligible ranks are present with stable identities and visual types;
3. every eligible row is executed;
4. every row ends `REACHABLE` or `UNREACHABLE_IN_CURRENT_WORLD_STATE`;
5. every reachable row has contact evidence and a physics type;
6. every unreachable row has an exhausted-route basis, evidence references and reopen conditions;
7. the counter-mask exclusions remain separate and complete;
8. the controller owns all mechanical routing actions.

The run should end when this accounting is complete or at a safety cap high enough to diagnose a
specific stalled row. A fixed action rate is not a success condition.

— Sol

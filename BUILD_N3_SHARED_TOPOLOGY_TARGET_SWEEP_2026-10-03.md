# N3 build record: shared topology and target-conditioned NAV sweep

**Type:** `BUILD_RECORD`
**Parent:** `BUILD_PLAN_NAV_FRICTION_REPAIR_AND_G3_CLOSE_v1_2026-10-03.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** built and locally validated; ls20/package confirmation pending

## Goal

Use the world map learned while pursuing one object when judging the next ranked object, without
weakening “collide with everything” or collapsing several objects into one ledger row.

## Donor and design decision

Golden Captain supplied the recomputation principle: stood anchors and refused edges belong to the
whole record, while reachability is derived separately for every present target. Ring 9 already
kept those topology facts at level scope. N3 therefore adds no second map and imports no Golden
architecture.

The reusable unit is a physical boundary refusal. For each new target, the controller ranks open
and refused bridge presses by the distance from their predicted landing footprint to that target.
A prior refusal may support the target only when:

- its stand is reachable in the current topology;
- its landing is a boundary experiment rather than known floor or direct target contact;
- it is closer to the target than every still-open bridge;
- consequently, every bridge tied for the nearest target-directed experiment has been spent.

This is a geometric stopping rule. It contains no probe count or retry threshold. A tied untried
press must be executed. Farther frontiers remain visible in the provisional certificate and a
later relevant map change reopens the row through N2.

## Built behavior

`SharedBridgeSupport` records the target, supporting refused edges, closest refused gap, closest
open gap and the support decision. G3 binds the corresponding refusal evidence into a fresh
per-target reachability certificate with `route_exhaustion_basis`:

- `TARGET_FALSIFIER` when the current target earned the refusal;
- `SHARED_TOPOLOGY_REFUSAL` when an earlier target or route probe earned it.

The compact card exposes the basis and supporting-edge count. It does not inline the full map.
N1 then asks Duck for the causal meaning only for the first semantic key. Sibling targets with the
same topology and ego law reuse that accepted meaning through the controller while retaining:

- distinct entity/member identity and geometry;
- distinct reachability signatures;
- distinct closest-stand and remaining-gap facts;
- distinct lifecycle transitions and terminal records;
- the exact shared physical evidence reference.

Reachable targets continue through the ordinary route and physical contact path. Shared topology
cannot mark a target unreachable when a direct contact edge or an equally nearest open bridge
exists.

## Local evidence

The synthetic sibling fixture establishes that one refused boundary press can close two ranked
targets without another environment action. It verifies two separate certificate rows, different
target-geometry fingerprints, the same justified refusal evidence, controller reuse for the second
semantic answer and zero added navigation steps.

A complementary test proves that an equally near open bridge blocks reuse. Existing scheduler and
NAV tests continue to prove physical contact for reachable targets and strict ranked advancement.
The combined NAV, scheduler, memory, controller and tool-agent suite passes **107 tests**.

No package was created and no Kaggle or OpenRouter run was started. N4 is next: explicit G3
completion and bounded-stop products that preserve the stable roster and pending target.

— **Sol**

# Build slice: G3 NAV terrain, reachability, and target release

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** implemented and locally validated; live ls20 checkpoint pending

## Purpose

G3 NAV must collide with every reachable visual world object. To finish that sweep, it also needs
an evidence-bearing way to say that a selected object cannot be reached from the currently mapped
field of play and then advance to the next target.

This is a routing conclusion. It is not an inertness verdict, an arbitrary pursuit budget, or a
permanent filter.

## Prior art to port

The direct donors are:

- `virelai-golden/golden/captain/nav_lattice.py`: stood-anchor traversal, refused-edge exclusion,
  deterministic BFS, predicted-footprint contact, and one-step frontier probes;
- `virelai-golden/golden/captain/nav_sweep.py`: contact-before-walk-before-frontier ordering,
  wall-crawl expansion, and evidence-bearing presumed-unreachable certificates;
- `virelai_golden/roles/ground.py`: traversed ground as the site-level union revealed by ego
  exchange;
- `virelai_golden/roles/wall.py`: a refusal belongs to the object occupying the predicted landing,
  and a stable blocker may type as WALL;
- Virelai v4 `ground_read.py` and `wall_read.py`: ground and wall are object/evidence readings,
  never class-wide color judgments.

Ring 9 already contains the first part of this port in `nav_route.py`: routes over demonstrated
stands, refused-edge exclusion, contact geometry and one frontier step. The missing production
pieces are refusal learning on approach, map exhaustion, certificate emission, target release and
Duck-facing explanation.

## Controller loop

For one bound target, repeat this order:

1. If a terminal contact is available from the current stand, execute it.
2. If a terminal contact is available from another demonstrated stand, follow the shortest route
   through demonstrated stands.
3. If no contact surface is known, route to the reachable stand whose next untried edge most
   reduces distance to the target.
4. Probe exactly one frontier edge.
5. If the ego translates as predicted, add the new stand to known floor.
6. If the ego does not translate after ego and counter effects are partitioned, record the
   `(stand, action)` edge as refused. Attribute a stable holder as a WALL candidate when ownership
   is available.
7. Recompute routes and frontier edges. Never repeat the same refused `(stand, action)` pair in the
   same unchanged world state.
8. If no contact surface and no untried frontier edge remain anywhere in the reachable component,
   emit a reachability certificate and release the target.

The map is learned by attempting to reach targets. There is no separate wandering quota.

## Terrain products

### Floor evidence

Each successful demonstrated displacement records:

- before and after ego anchors;
- action and expected displacement;
- occupied landing footprint;
- transition evidence reference;
- level, life and masked world-state address.

The set of actually occupied anchors is the traversal graph. A whole route may use those anchors.
Only one step beyond them may be attempted as a frontier experiment.

### Wall evidence

Each refused demonstrated displacement records:

- before ego anchor and action;
- predicted landing footprint;
- absence of expected ego translation;
- counter-masked outcome partitions;
- holders of the landing cells when ownership is available;
- transition evidence reference and world-state address.

A refused edge is immediately useful for routing. Calling a visual object WALL requires the
additional object-level stability evidence already represented by the prior art.

Refusal evidence is scoped to the counter-masked grid state in which it was observed. Ego motion
and its paired ground exchange do not create a new topology. Any remaining world delta does: it
may have opened a passage, removed a blocker or changed an object's collision behavior. On such a
transition, prior refused edges are invalidated and provisional reachability certificates reopen.
The controller may then test those edges again in the new world state.

## Reachability certificate

When the reachable component is exhausted for a target, emit a compact, queryable certificate:

```text
target entity and current version
counter-masked world-state address
ego entity and footprint
demonstrated bearing map
reachable stood anchors with evidence refs
refused edges with evidence refs
closest reachable stand and remaining target gap
candidate contact surfaces considered
reason no contact surface or open frontier remains
masked world-state address, level and life
reopen conditions
status: PRESUMED_UNREACHABLE
```

The scheduler then advances to the next ranked target. This is how G3 keeps the “collide with
everything” promise without allowing one inaccessible display object to monopolize the run.

## Duck explanation

Duck receives a compact certificate in the active card, with full geometry callable on demand. It
must explain the conclusion in its own world model at target release. A sufficient answer has this
form:

> I cannot reach this object from the field of play I have mapped. I tried every remaining movement
> edge reachable from demonstrated floor; the listed edges refused movement, and no ego landing
> footprint can contact the object. I will move to the next target. This is a routing conclusion,
> not evidence that the object is inert, and I will reconsider it if the map or world changes.

If the target lies beyond the exhausted traversable component, Duck may describe it as “outside
the current field of play.” The machinery licenses that sentence from reachability evidence, never
from screen position, color, class integer, or a hard-coded HUD region.

## Reopen conditions

`PRESUMED_UNREACHABLE` is provisional. Reopen the target when any of these changes:

- a new stood anchor expands the reachable component;
- a previously refused edge later yields;
- the target moves, transforms, disappears and reappears, or receives a new entity version;
- the ego footprint, controlled entity, bearing map or available action surface changes;
- a lever or environmental force changes terrain;
- any non-counter, non-ego world delta creates a new routing context;
- level or other relevant world state changes.

Death on the same level preserves supported stood anchors and refusal evidence, while the active
route is restarted from the respawned ego position.

## Required distinction

| Statement | Licensed by | Effect on G3 |
| --- | --- | --- |
| `WALL` | a refused landing plus stable blocking ownership | remove that edge; retain the wall record |
| `FLOOR` | successful occupied stands and ego/ground exchange | expand traversable graph |
| `PRESUMED_UNREACHABLE` | exhausted reachable component and frontier for this target | release target; reopen on change |
| `OUTSIDE CURRENT FIELD OF PLAY` | Duck's explanation of a valid reachability certificate | same provisional release |
| `INERT` | later scoped activation coverage, not route failure | outside this slice |
| `UNRESOLVED_BUDGET_STOP` | action/time budget ended before exhaustion | keep target open; no reachability claim |

## Integration with NAV confirmation

A pending lever confirmation uses the same router. Approach and frontier actions keep the frozen
prediction pending. A reachability certificate may defer confirmation, but it cannot contradict
the witness. Only a later terminal contact grades the prediction.

## Exit criteria

1. A successful approach adds a demonstrated stand and the planner can traverse back through it.
2. A failed approach records a refused edge even when its intent was `APPROACH`.
3. The same refused `(stand, action)` pair is not selected again in the unchanged world state.
4. The router searches other reachable stands and frontier edges before releasing a target.
5. Exhaustion emits an evidence-bearing, reopenable `PRESUMED_UNREACHABLE` certificate.
6. Duck explains why the object is unreachable or outside the current field of play and explicitly
   distinguishes that claim from inertness.
7. The scheduler advances to the next ranked target immediately after the explanation is accepted.
8. A numeric step budget alone produces only `UNRESOLVED_BUDGET_STOP`.
9. New floor, changed terrain or changed target identity reopens the certificate.
10. Pending NAV confirmation is graded only on terminal contact.

The ls20 regression must show that target `M0019` cannot consume the remainder of the 200-action
run through repeated ACTION2 presses from an unchanged stand.

— **Sol**

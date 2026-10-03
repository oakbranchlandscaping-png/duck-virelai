# Mine: G3 NAV integer terrain and fast reachability

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** READ-ONLY PRIOR-ART MINE; DESIGN CONSEQUENCE RECORDED

## Question

If the controller learns that integer `x` is floor and integer `y` is wall, can it determine
quickly whether a visual object is reachable and stop pursuing objects outside the avatar's field
of play?

## Answer

Yes, with two necessary refinements. Integer terrain identity can pre-fill most of a navigation map
and replace a long physical wall crawl with a configuration-space calculation. That calculation
proposes a reachability or unreachability **hypothesis**; it does not close the row. The controller
must try to reach the object and give the hypothesis a direct chance to fail. Only after the
target-relevant attempt refuses and no remaining mapped route could reach a contact surface may it
accept `UNREACHABLE_IN_CURRENT_WORLD_STATE` and move on.

The calculation must also use the ego's full footprint, learned action displacements, current
world state and the target's contact surface. A raw pixel flood or an unconditional rule that every
occurrence of one integer has one role is insufficient.

The repo already contains both halves of this design:

1. Universal Solver v3.5 contains the exact integer-to-position bridge and flood-fill shortcut.
2. Golden contains the stronger ego-footprint, action-space and evidence-scoping corrections.

Ring 9 currently carries mostly the second half. That is why its unreachability proof is sound but
expensive: it physically demonstrates the reachable component instead of seeding it from learned
terrain integers.

No downloaded game-engine implementation was inspected for this mine.

## Prior art found

### Universal Solver v3.5: the exact integer bridge

`Universal_Solver_v3_5/discovery/instruments/traversability_map.py` defines
`seed_passability_from_integer_knowledge()`. Its stated purpose is to project confirmed
`walkable_classes` and `blocked_classes` onto the position-level passability map so the planner
does not physically bump every wall cell. For each known wall integer it seeds blocked approach
edges; for each known floor integer it seeds passable approach edges.

This is the closest prior implementation of the proposed idea and should be ported in concept.

The same module separates:

- a `ReachabilityMap` of confirmed poses;
- a `PassabilityMap` of `(pose, action)` edges;
- world-state-scoped blocked evidence;
- successful traversal winning over an earlier blocked classification.

`Universal_Solver_v3_5/execution/contact_step_handler.py::_flood_reachable()` also flood-fills
through every pixel whose integer is not in `blocked_classes`. It was used to distinguish reachable
mutation components from probable HUD components. Its own tests expose the risk: a HUD integer not
in the blocked set is treated as passable, so the flood can leak into the HUD. This is useful as an
optimistic screen, not sufficient as a final certificate.

### Universal Solver v3.5: known failure modes

The older pathfinder accumulated `walkable_classes`, `blocked_classes` and permanent
`unreachable_targets`. The later mine explicitly rejected two parts:

- permanent dead-zone filtering, because a world change can open a route;
- class-wide passability as an unqualified truth, because one integer can appear in multiple
  objects or roles and a local collision does not prove every instance blocks.

The retained lesson is therefore **integer knowledge seeds the map**. It does not erase empirical
pose-edge evidence, entity identity or reopening.

### Golden: navigation in action and configuration space

`golden/captain/nav_lattice.py` represents:

- the ego anchor;
- the ego's complete relative footprint;
- the observed action-to-displacement bearing map;
- anchors the body has occupied;
- refused `(anchor, action)` edges;
- board bounds.

It performs BFS over ego anchors, not unit pixels. A contact exists when one legal action from a
reachable stand would make the translated ego footprint overlap the target. A wall is contacted by
the refused press itself; the ego need not occupy the wall.

`golden/captain/nav_sweep.py` makes the map shared across the whole object sweep. It orders work as
contact first, known-floor route second and a single frontier experiment third. Only after no
contact or frontier press remains does it mark remaining targets presumed unreachable.

### Golden and Virelai: floor and wall are evidence-bound roles

`golden/roles/ground.py` and the Virelai `ground_read.py` derive ground from the cell exchange
created by demonstrated ego motion. The important relation is: cells vacated and entered by the
ego are accounted for by the ground process. The integer at those sites is powerful evidence, but
the role attaches to the observed world object/site relation rather than to a number by decree.

`golden/roles/wall.py` and Virelai `wall_read.py` derive wall from a refused ego transition whose
predicted landing is held by a stable non-ego object. The refusal is contact evidence. Again, the
integer can project that finding over the current frame, while the evidence remains tied to the
observed blocker and world state.

### Current Ring 9 implementation

`inference/framework/nav_route.py` already has the correct ego-footprint contact test, action-space
routes, refused edges and reopenable reachability certificate. Its expensive rule is that every
frontier edge of the demonstrated reachable component must be physically resolved before a target
can be released.

The ls20 target-ledger run showed the cost directly: rank 5 consumed 61 actions, including 42 floor
traversals and 18 wall refusals, without exhausting the component.

### Direct evidence from the completed ls20 run

The saved frames support the proposed shortcut without consulting the game implementation:

- G1's successful rigid translations repeatedly exchange the ego's integers 9/12 with integer 3.
  Integer 3 is therefore the strong current-state floor candidate.
- Of 21 G3 refused predicted landings, 19 had a complete 5×5 destination footprint of integer 4.
  Integer 4 is therefore the strong current-state wall candidate.
- One refused contact footprint contained integers 5 and 9; this is a target-specific collision,
  not evidence that either whole integer class is wall.
- One refused edge had a complete destination footprint of integer 3, and that anchor was reached
  later through a different route. This is direct evidence that even a strong floor integer cannot
  replace pose-action evidence. The class seed was useful, while the local refusal remained real.

For this ls20 state, the useful working hypothesis is therefore `floor={3}` and `wall={4}`, plus
edge-specific overrides and target-contact geometry. The large integer-3 entity currently ranked
near the end of the target ledger should become a terrain-role row rather than consume a lever
contact attempt once this classification is built.

## Proposed combined model

### 1. Learn a terrain palette during G1 and early G3

The Delphi sequence already supplies controlled movement in every available direction. For each
successful rigid ego translation, record:

- integer values under the destination footprint before entry;
- integer values restored under the source footprint after departure;
- the action displacement and full ego footprint;
- exclusions for ego and counter cells.

Values consistently participating in these exchanges become current-state `FLOOR_INTEGER`
hypotheses. Refused predicted landings attribute their occupying values and entities as
`WALL_INTEGER`/wall hypotheses. Coverage is expressed over the available movement actions and
observed sites, rather than an arbitrary repetition count.

The representation must permit sets, because a world may use more than one floor or wall integer.

### 2. Compile the current frame into ego configuration space

For every possible ego anchor, translate the full learned ego footprint. The anchor is a candidate
stand only if:

- the complete footprint stays in bounds; and
- every occupied cell is current-state floor, previously demonstrated stand-space, or another
  specifically permitted traversable site.

This is morphological erosion of the floor mask by the ego footprint, sampled by the learned
action vectors. It prevents a point-agent flood from claiming that a large avatar fits through a
narrow gap.

All non-floor visual objects remain blockers for transit until evidence says otherwise. For the
object currently being tested, its cells are a terminal contact surface rather than ordinary
transit cells.

### 3. Compute one shared reachable component

Run BFS once from the current ego anchor over candidate stands using the learned action vectors.
The result is the current reachable ego-pose component. It belongs to the world state, not to one
target.

For every ledger target, compute the source stands from which one available action would make the
ego footprint overlap that target. This first pass produces hypotheses:

- at least one source stand in the reachable component → `PREDICTED_REACHABLE`, with a shortest
  route and contact action;
- source stands exist but none lie in the component → `PREDICTED_UNREACHABLE`;
- no geometrically valid contact stand exists → `PREDICTED_OUTSIDE_CURRENT_FIELD_OF_PLAY`;
- terrain identity or passability is unresolved → keep the row open and select the smallest
  discriminating frontier probe.

One calculation can prepare the whole target roster and the shortest experiment for each row. It
does not convert predictions into verdicts. This is the main efficiency gain.

### 4. Falsify each target's reachability hypothesis

For a `PREDICTED_REACHABLE` target, execute the shortest mapped route and its contact action. An
observed contact accepts reachability. A refusal corrects the pose-action map and triggers a new
plan.

For a `PREDICTED_UNREACHABLE` or `PREDICTED_OUTSIDE_CURRENT_FIELD_OF_PLAY` target, choose the
shortest target-relevant falsifier:

1. route over known floor to the closest stand on the target side of the current component;
2. try the unverified boundary edge whose success would most reduce or eliminate the separation;
3. if it yields, reject the hypothesis, expand the component and continue toward contact;
4. if it refuses, retain that wall/edge evidence and recompute;
5. accept `UNREACHABLE_IN_CURRENT_WORLD_STATE` only when no untested boundary edge remains that
   could connect the current component to any contact surface for that target.

This is a target-conditioned wall crawl. It tests possible bridges to the object instead of every
frontier edge surrounding the entire reachable component. The acceptance is evidence-bearing and
provisional; it is never an assumption based on appearance.

### 5. Preserve empirical overrides and reopening

The integer projection is a current-state hypothesis. Runtime evidence has priority:

- successful entry overrides a blocked seed at that pose-edge;
- refusal overrides a floor seed at that pose-edge;
- a relevant non-counter world delta creates a new terrain-map version;
- changed terrain, target geometry, ego footprint, bearing map or action surface reopens affected
  reachability rows.

This keeps the useful speed of integer classification without reviving permanent class-wide
judgments.

## Why raw integer flood-fill is not enough

The direct rule “all `x` is floor, all `y` is wall” can be wrong when:

- the same integer is used by both terrain and an object;
- floor uses several integers or changes appearance;
- a door changes from a wall integer to a floor integer;
- the ego footprint cannot fit through a pixel-connected corridor;
- action displacements have stride greater than one or are not the four unit directions;
- the target itself is an immovable wall whose refused press is the required contact;
- an overlay or HUD shares an integer with world terrain;
- the world changes and invalidates an earlier blocked classification.

These are reasons to retain geometry, action space, object identity and world-state versioning.
They are not reasons to physically explore every cell after terrain integers are well supported.

## Recommended next build slice

Build **G3 NAV integer-seeded configuration reachability**:

1. Add a versioned `TerrainPalette` containing floor integers, wall integers, evidence references,
   action coverage and explicit uncertainty.
2. Populate floor evidence from G1 Delphi ego/ground exchange and wall evidence from refused NAV
   transitions.
3. Port the v3.5 integer-to-position seeding mechanism into a footprint-aware Ring 9 map.
4. Compile all valid ego anchors and the shared reachable component from the current frame.
5. Generate a reachability hypothesis and shortest falsifying experiment for every target in one
   batch; do not treat either prediction as a verdict.
6. Execute a real reach/contact attempt for every target. A predicted-unreachable row must receive
   a target-conditioned boundary probe before it can close.
7. Accept provisional unreachability only after all target-relevant bridge edges have refused or
   are ruled out by the body/action geometry.
8. Make empirical pose-edge observations override palette seeds.
9. Reopen affected rows after relevant world deltas.
10. Preserve the existing rule that unreachable does not mean inert.

The new checkpoint should prove that the ls20 bottom-row objects first receive an explicit
unreachable/outside-field hypothesis, then a concrete falsification attempt, and only then a
grounded current-state judgment without a 61-action whole-component crawl. Reachable targets must
still receive real contact attempts.

## Claim boundary

This mine supports the architecture and identifies direct port material. It does not establish the
actual floor or wall integers of every ARC world, that one integer always has one role, or that an
unexecuted implementation will classify ls20 correctly. Those are the next slice's local and live
exit criteria.

— Sol

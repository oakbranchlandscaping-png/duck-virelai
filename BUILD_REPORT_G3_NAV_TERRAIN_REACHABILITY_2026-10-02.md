# Build report: G3 NAV terrain, reachability, and target release

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Source:** `variants/ring9-cybernetic-gates/ARC3-Inference`  
**Status:** implemented and locally validated; live ls20 checkpoint pending

## Why this slice exists

The ls20 v3 run proved that Ring 9 could identify the embodied ego, lock the counter and obtain a
real G3 lever witness. It also exposed a routing failure: a failed approach to target `M0019` was
not retained as a refused edge, the confirmation was graded during routing, and the controller
repeated the same movement for the remainder of the run.

This slice teaches the controller enough terrain to finish the broad G3 sweep. A successful move
is demonstrated floor. A failed predicted move is a refused wall edge. The controller searches all
reachable stands and all remaining frontier edges. Only after that finite search is exhausted may
it ask Duck to explain that the target is outside the currently mapped field of play, release the
target and continue the ranked roster.

That conclusion is explicitly provisional. It never licenses an inertness claim.

## Prior art ported

The implementation ports the useful mechanisms from the separate Golden solver rather than
inventing a second navigation theory:

- `golden/captain/nav_lattice.py`: demonstrated stands, deterministic routes and refused edges;
- `golden/captain/nav_sweep.py`: contact-first ordering, one frontier experiment at a time and
  exhausted-component certificates;
- Virelai ground/wall work: successful ego exchange as floor evidence and refused predicted
  landing as wall evidence.

The port was adapted to Ring 9's existing entity ledger, lifecycle journal, gate cards, evidence
references, confirmation protocol and life-record policy. No game-engine implementation was
inspected to derive mechanics.

## Implemented behavior

### Terrain-aware route planner

`nav_route.py` now searches frontier edges from every stand in the demonstrated reachable
component. It routes to a promising known stand through known floor, then permits exactly one
step across the current frontier. A refused `(stand, action)` edge is excluded from future routes
in the unchanged level state.

When no contact press and no frontier edge remain, the planner emits a
`ReachabilityCertificate`. It contains the bound target, reachable stands, refused edges, closest
stand, remaining gap, evidence basis and explicit reopen conditions.

### Floor and wall observations

The G3 outcome recorder compares the controller's predicted landing with the observed ego anchor:

- predicted translation observed → `FLOOR_TRAVERSED`, retain the new stood anchor;
- ego remains at the predicted starting anchor → `WALL_EDGE_REFUSED`, retain the refused edge;
- route evidence stays separate from target activation evidence.

A failed `APPROACH` therefore no longer becomes a lever null, ambiguity or semantic wake-up. It is
terrain evidence used by the next route calculation.

### Reachability explanation gate

Map exhaustion pauses G3 with an evidence-bound `TARGET_REACHABILITY` answer template. Duck must
explain why the mapped component offers no contact path, agree to move to the next target and state
that the result does not prove inertness. The controller rejects changed evidence references,
missing reopen conditions, an inertness claim or refusal to release the target.

An accepted answer records the lifecycle state `PRESUMED_UNREACHABLE`, advances the ranked target
and preserves the full certificate in the lossless snapshot. The automatic card contains only
counts, the closest stand, evidence references and a detail handle; large map geometry does not
flood the prompt.

### Reopening

The controller reopens a provisional certificate when the target receives a new entity version or
when a newly demonstrated floor stand expands the reachable component. It removes the target from
bounded ambiguities and queues it for another ranked attempt. Route evidence and refused edges are
level-scoped across death; the single pending movement plan is transient.

### Confirmation boundary

NAV confirmation now remains `ROUTING` and ungraded during every approach step. Only the terminal
contact attempt can support or contradict the frozen lever witness. If the target is certified
unreachable first, the witness is deferred rather than contradicted.

## Files changed

- `inference/framework/nav_route.py`
- `inference/framework/virelai_gates.py`
- `inference/framework/lever_lifecycle.py`
- `inference/framework/controller_executor.py`
- `inference/framework/life_record.py`
- `tests/test_nav_branch_foundations.py`
- `BUILD_SLICE_G3_NAV_TERRAIN_REACHABILITY_v1_2026-10-02.md`

Existing unrelated changes in the repository were left untouched.

## What local evidence proves

The dedicated tests prove:

1. the router explores another demonstrated stand before declaring exhaustion;
2. a certificate cannot appear while any reachable frontier edge remains;
3. a failed approach becomes a refused wall edge and is not typed as lever behavior;
4. routing during confirmation remains pending and ungraded;
5. the reachability card stays below the 24,000-character bound even with 1,600 stands and 1,600
   refused edges in the lossless certificate;
6. Duck's accepted explanation releases the target without an inertness claim;
7. new floor evidence reopens and requeues the provisional target;
8. every new field has an explicit cross-life persistence tier.

Focused NAV, G3, life-record and level-freeze suite: **44 passed**.  
Ruff on every changed Python file: **passed**.  
Full Ring 9 suite with the vendored harness path: **526 passed** (14 third-party deprecation
warnings, no failures).

## What remains unproven

Local fixtures establish controller logic and contract enforcement. They do not establish that the
production adapter will extract every ls20 ego anchor correctly, that G1 will supply all necessary
bearings in the live world, or that the live run will finish the object roster within its action
budget. Those are live behavioral questions.

The next checkpoint should therefore be one ls20 Kaggle run with the same game/model/budget
settings as v3. Success is not a level win. Success is:

- no repeated press from an unchanged stand after that edge has refused;
- approach frames do not grade a lever confirmation;
- `M0019` either becomes contactable or receives an explained `PRESUMED_UNREACHABLE` release;
- the controller advances to the next ranked visual object;
- G3's contact/collide sweep continues until all reachable objects have been attempted.

— **Sol**

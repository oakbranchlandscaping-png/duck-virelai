# G3 NAV integer terrain and reachability — build record

**Type:** `BUILD_RECORD`  
**Status:** source built; focused local validation passed; Kaggle checkpoint pending  
**Author:** Sol (Alpha build seat)  
**Date:** 2026-10-03

## Purpose

The G3 NAV sweep must use the ego law learned in G1 to reason over the current field of play. It should recognize directly traversed ground as floor, recognize full-footprint refused landings as wall evidence, propose whether each ranked visual target can be contacted, and stop spending actions on a target when a target-specific attempt supports a provisional routing limit.

The controller owns geometry, route selection, and action choice. Duck is reserved for the semantic explanation required to accept a provisional `UNREACHABLE_IN_CURRENT_WORLD_STATE` result. A map prediction alone never supplies that result.

## Port lineage

This slice was mined before implementation. It ports two mechanisms without importing their old architecture or world claims:

- Universal Solver v3.5's integer passability seed: directly observed traversed integers can seed a broader floor hypothesis.
- Virelai Golden's configuration-space correction: reachability is computed over legal placements of the complete ego footprint and the demonstrated action vectors, rather than point-pixel flood fill.

The implementation remains inside Ring 9's existing gate machine, entity ledger, lifecycle journal, counter mask, world-state address, and controller executor.

## Implemented contracts

### 1. Evidence-derived terrain palette

`nav_terrain.py` reconstructs every uniquely observed G1 translation from retained total frames.

- Values exposed when the ego enters or vacates cells become floor-integer evidence.
- A uniform non-floor landing footprint that refuses a controller action becomes wall-integer evidence.
- Exact refused edges override the integer class locally.
- The palette is scoped to the current level state and carries evidence references and limitations.

No action number receives a semantic direction by assumption. The bearing map still comes from verified G1 displacement evidence.

### 2. Full-footprint action-space map

Every candidate stand must fit the complete demonstrated ego shape on the proposed floor integers. Breadth-first search then uses only the learned displacement vectors. This prevents a point-agent route from passing through a corridor the real body cannot occupy.

The map records valid stands, the current reachable component, target-contact edges, and target-conditioned bridge edges.

### 3. Hypothesis, falsifier, verdict

For each target:

1. If the mapped component contains a contact edge, the controller follows the shortest route and labels only the terminal press `CONTACT_ATTEMPT`.
2. If it contains no contact edge, the controller routes to the closest target-relevant bridge and presses it as a `FALSIFIER`.
3. If the bridge yields, the predicted limit is rejected, the new stand is learned, and routing continues.
4. If the bridge refuses and the recomputed map still has no contact route, G3 opens an evidence-bound reachability explanation.
5. Only after that explanation does the target become provisionally `UNREACHABLE_IN_CURRENT_WORLD_STATE`.

The verdict is explicitly not an inertness claim. It reopens after a relevant world delta, new stand, yielding refused edge, target-identity change, ego-law change, or level-state change.

### 4. Floor and wall rows in the visual roster

The ranked roster remains complete. A frozen visual component is labeled `FLOOR` or `WALL` only when its actual cells overlap the direct exchange or refused-landing evidence that established the role. Matching color alone does not close a different object.

The interaction that supports the terrain role completes that row without requiring a redundant collision. Confirmed lever witnesses always take precedence over terrain typing.

### 5. Lifecycle repairs

Two frictions from the prior ls20 run were corrected:

- A target changing during an `APPROACH` step no longer advances its incomplete roster row. The entity ledger may rebind it and the pursuit continues.
- A target-specific null `CONTACT_ATTEMPT` now closes that row immediately as a scoped nonresponder. It no longer waits for the entire G3 roster to finish.

### 6. World-delta invalidation

A counter-masked world delta clears the current terrain palette, target hypotheses, falsifier results, and old refused edges. Terrain rows closed under the old state reopen. Direct G1 floor evidence may immediately support them again; wall evidence must be observed in the new state.

### 7. Prompt and memory bounds

The lossless snapshot retains map geometry. The automatic Duck-facing gate view receives integer classes, evidence, counts, current hypothesis status, gap, and retrieval markers rather than full stand and edge arrays.

Terrain roles and completed falsification attempts persist for the level. The derived palette, current hypotheses, and in-flight route plan are transient and recomputed from retained evidence.

## Validation

Focused local suites:

- `tests/test_nav_terrain.py`
- `tests/test_nav_branch_foundations.py`
- `tests/test_g3_scheduler.py`
- G3 checkpoint, recolor identity, entity observation, attribution, lifecycle, production fixture, and controller-pilot suites

Result: **95 passed**. Ruff passed on all changed Python files. The persistence audit reports no undeclared fields.

The new tests prove:

- floor and wall inference uses direct movement/refusal evidence;
- a multi-cell ego cannot use a point-width corridor;
- predicted unreachable produces a falsifying action rather than a verdict;
- a refused edge does not poison alternative routes over the same floor integer;
- approach-time target changes do not skip the target;
- completed null contact closes the row immediately.

## Replay against actual ls20 evidence

The completed `ring9-g3-target-ledger-ls20-v1` artifact was replayed read-only through the new palette compiler.

Direct observation from the artifact:

- the demonstrated ego footprint is 5×5;
- the learned action vectors are five cells up, down, left, and right;
- G1 body/ground exchange identifies integer `3` as floor;
- G3 uniform full-footprint refusals identify integer `4` as wall;
- all four action directions carry floor evidence;
- the replay produced no palette limitation.

This supports the new map's intended input on ls20. It does not prove live controller behavior, target completion, or a win. Those claims require the new Kaggle run.

## Kaggle exit criteria

The bounded ls20 checkpoint should establish:

1. G0–G2 close and install the same complete counter mask.
2. G3 reports floor integer `3` from G1 exchange evidence.
3. After a refused full-footprint landing, G3 reports wall integer `4`.
4. Floor and observed wall components are typed in the target ledger with evidence references.
5. Each remaining target receives either a contact attempt or a target-conditioned falsifier.
6. No `APPROACH`-time target change skips its row.
7. A refused falsifier is required before any provisional unreachable answer.
8. A yielding falsifier expands the map and continues pursuit.
9. Scoped-null contact closes its row immediately.
10. All environment actions remain controller-owned whenever the deterministic map supplies a step.

The checkpoint does not grade competition score, level completion, G4 closure, or the global quality of the world model.

— Sol

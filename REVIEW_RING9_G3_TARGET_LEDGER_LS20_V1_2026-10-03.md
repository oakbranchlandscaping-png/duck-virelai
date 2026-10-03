# Review: Ring 9 G3 target ledger ls20 v1

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** COMPLETE; CHECKPOINT FAILED DIAGNOSTICALLY
**Frozen source:** `8606448e0755974ee9cb045b71c276bd43dae8b2`

## Verdict

The live run proves that Ring 9 can form a complete counter-filtered visual target ledger before
G3 execution and keep all environment actions under deterministic controller ownership. It does
not yet prove the requested complete sweep. Of 16 eligible targets, 3 ended `EXECUTED`, 2 ended
`IN_PROGRESS`, and 11 remained `QUEUED`. No target received an
`UNREACHABLE_IN_CURRENT_WORLD_STATE` certificate.

This is a useful architectural failure. The main bottleneck is not Duck reasoning or model speed.
The controller spent 61 actions exploring the reachable floor component while pursuing rank 5, a
four-cell object at rows 61–62. The proof rule only declares unreachable after every frontier edge
of the reachable component has been tested. That is sound but too expensive when repeated as a
per-target pursuit.

Do not rerun this package unchanged and do not relax the target-accounting criteria.

## Execution identity

- Kaggle notebook: `stephenkaskin/taaf-virelai-ring9-g3-target-ledger-ls20-v1`, version 1
- Kaggle dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-target-ledger-ls20-v1`
- Notebook state: `COMPLETE`
- World: `ls20-9607627b`
- Duration: 3 minutes 58 seconds
- Actions: 96
- Generated tokens: 8,668
- Score and levels: 0 and 0/7; neither was a checkpoint criterion
- Stop: explicit 96-action safety cap; no runtime crash
- Downloaded evidence: `runs/kaggle-ring9-g3-target-ledger-ls20-v1/`
- Runtime receipt SHA-256: `b40088d3c16862b88d79594f2885d7c290cd85454845f99578fbf793f7acc93d`
- Runtime receipt exactly matches the frozen package receipt

## Preregistered grading

| # | Criterion | Result | Direct evidence |
|---|---|---|---|
| 1 | G0–G2 close and install the complete counter mask | **PASS** | G1 used 9 actions, G2 used 3, then G3 opened with mask `MASK-V1-615ca9b230ffa5bf`. |
| 2 | Roster populated before G3 execution | **PASS** | Ledger field `roster_populated_before_execution: true`. |
| 3 | Every eligible rank has stable identity and visual type | **PASS** | 16 eligible rows each carry entity, member, integer, shape, size and bounding box. |
| 4 | Every eligible row is `EXECUTED` | **FAIL** | 3 executed, 2 in progress, 11 queued. |
| 5 | Every row ends reachable or provisionally unreachable | **FAIL** | 3 reachable, 13 not yet determined, 0 unreachable. |
| 6 | Every reachable row has contact evidence, contact type and a nonpending physics type | **FAIL** | All 3 have contact evidence; rank 3 remains `NOT_YET_TYPED`. |
| 7 | Every unreachable row has proof and reopen conditions | **NOT EXERCISED** | No unreachable certificate was emitted. |
| 8 | Counter exclusions remain separate and complete | **PASS** | Source ranks 10 and 13 are separate `ROLE_EXCLUSION` rows bound to the mask law. |
| 9 | Controller owns every computable environment action | **PASS** | Turn ledger: 96 controller action turns; Duck made no environment action. |
| 10 | Controlled stop or complete accounting, without crash | **PASS** | Run stopped cleanly at the declared action cap. |

Overall: 6 pass, 3 fail, 1 not exercised. The checkpoint itself fails because criteria 4–6 are
substantive exit conditions.

## What the ledger established

The run began G3 with the whole roster already materialized. It contained 18 rows: 16 eligible
targets and 2 counter-role exclusions. The eligible list ranged from isolated points to large
terrain-like regions. It therefore preserved the requested rule that the sweep starts from a
complete ranked list instead of inventing a new target after every action.

The first five ranks progressed as follows:

| Eligible rank | Visual type | Result |
|---|---|---|
| 1 | integer 1 point at `[32,20]` | `EXECUTED`, `REACHABLE`, entered; effect remained unresolved. |
| 2 | integer 1 point at `[33,21]` | Changed during approach; advanced with bounded ambiguity but remained `IN_PROGRESS` and reachability-undetermined. |
| 3 | integer 9 point at `[13,35]` | `EXECUTED`, `REACHABLE`, refused contact and scoped null; remained `NOT_YET_TYPED`. |
| 4 | integer 0, 3-cell object at rows 31–32 | `EXECUTED`, `REACHABLE`, displaced; effect remained unresolved. |
| 5 | integer 8, 4-cell rectangle at rows 61–62 | `IN_PROGRESS`; 61 approach actions explored floor and wall edges without exhausting the component. |

Ranks 6–16 remained queued. The controller therefore never got to label the full list as reachable
and typed or unreachable in the current world state.

## Direct observations and limits

Directly observed:

- the complete target ledger existed before its first target action;
- the two learned counter members were excluded from the eligible sweep;
- the controller selected every one of the 96 environment actions;
- 84 actions occurred in G3, of which rank 5 consumed 61;
- the total G3 phase accumulated 62 traversed-floor observations and 21 refused-wall observations;
  rank 5 alone accounted for 42 traversals, 18 refusals and one unresolved movement while the
  component still had open frontier edges when the cap arrived;
- no unreachable certificate fired;
- the notebook completed without a runtime failure.

Supported interpretation:

- the current reachability certificate is sound but operationally mismatched to a target-by-target
  sweep on a large NAV world;
- much of the floor/wall exploration is shared evidence about the playable component and should be
  amortized across all targets;
- rows 61–62 contain several small visual objects that are plausible HUD or off-field objects, but
  the run did not prove that role. They must remain ordinary visual targets until reachability or a
  stronger role rule accounts for them.

Not established:

- that target 5 is permanently unreachable;
- that any queued object is a wall, floor, lever, decoration or HUD element;
- that the large visual regions should be deleted from the roster;
- that a larger action cap alone would complete the roster efficiently;
- that G3 is closed, that G4 NAV is ready, or that this level is winnable with the present model.

## Frictions that require repair

### 1. Reachability is being proved per target at component scale

When no demonstrated route to contact exists, `plan_contact()` searches the closest untested
frontier edge. `certify_unreachable()` waits until every in-bounds edge from the demonstrated
reachable component is either stood or refused. This makes one distant target trigger a general
wall crawl. The evidence is useful, but the scheduler treats its cost as belonging only to the
current target.

The next slice should make the floor/wall map a shared world-state object. A completed or bounded
component survey can classify contact surfaces for every remaining target in one pass. New world
deltas invalidate only the affected reachability facts and reopen the corresponding rows.

### 2. Approach change can advance a row without completing it

Rank 2 changed during an `APPROACH` action. The scheduler bounded the causal ambiguity and advanced
to rank 3, but the ledger correctly retained rank 2 as `IN_PROGRESS` and
`NOT_YET_DETERMINED`. This exposes a disagreement between scheduling and accounting.

An approach-frame target change may be evidence of a remote or environmental reaction, but it is
not contact and it is not an unreachable proof. The repaired scheduler must either rebind and
continue the row, or record a separate terminal G3 classification that satisfies an explicit
criterion. It must not silently leave a nonterminal row behind.

### 3. A completed null contact stays pending until global enumeration

Rank 3 produced a refused contact and `SCOPED_NULL_RESPONSE`, then the scheduler advanced. Its
lifecycle remained `NO_RESPONSE_YET` and its physics type remained `NOT_YET_TYPED`, because scoped
null entities are closed only after the entire roster finishes.

The row should close immediately when its scoped contact attempt is complete. This is local
knowledge and must not wait for unrelated objects. The eventual global G3 answer should summarize
already terminal rows rather than create their terminal meaning retroactively.

## Next build slice

Build **G3 NAV shared reachability and row-terminalization** before another Kaggle run:

1. Promote demonstrated stands, refused edges and their evidence into one versioned floor/wall map
   for the current world-state address.
2. Reuse that map across the full target ledger and calculate which rows already have a reachable
   contact surface.
3. When the map has no open frontier capable of improving a target's reachability, emit its
   provisional unreachable certificate without replaying the crawl for that row.
4. Keep the existing reopen rule after relevant world, terrain, ego, control or target changes.
5. Prevent approach-only target changes from advancing a row unless that row receives a valid
   terminal G3 result.
6. Close a completed scoped-null contact immediately with a concrete nonresponder physics type.
7. Add an internal invariant: the scheduler cannot move past a row that remains `QUEUED`,
   `IN_PROGRESS`, `NOT_YET_DETERMINED`, or `NOT_YET_TYPED` unless a recorded deferral policy keeps
   it in an explicit retry queue.
8. Validate offline with multiple targets sharing one component survey, an off-field target, an
   approach-time changing target, a refused inert target, and a world delta that reopens reachability.

Only then package a bounded ls20 successor. The next live success condition remains the same:
every eligible row must end accounted for. A higher arbitrary cap is not a substitute.

— Sol

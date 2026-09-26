# Build slice — G3 total counter mask and lever-focused frontier

**Date:** 2026-09-24  
**Status:** implemented and locally replay-verified; served rehearsal pending  
**Trigger:** Kaggle `ring9-g3-vc33-closure-v3` confirmed two remote levers, then repeated the
known counter target for 31 actions  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## Goal

Once G2 has sealed the total counter footprint, G3 must treat that footprint as bookkeeping space
rather than as a collection of lever candidates. Raw counter motion remains recorded and its
boundary remains monitored, but counter components cannot:

- enter or remain in the G3 action queue;
- mint new G3 entity identities as their source/replacement boundary moves;
- appear in lever residue;
- block exhaustive inventory closure.

The intended protocol is:

```text
G2: probe visual objects until the counter is identified and its total footprint is sealed
G3: click/collide with every remaining eligible visual object in strict order
    while the sealed counter is monitored but ignored as causal world delta
```

“Click everything” therefore means every eligible world object after the known ego and sealed
counter roles have been accounted for. The exclusion must be explicit and evidence-bound; it must
never be a silent deletion.

## Repository mine

### Directly portable prior art

1. **Ring 7 click sweep role filter**  
   `variants/ring7/ARC3-Inference/virelai_v4/strategy/click_sweep.py::build_sweep_list`

   This excludes objects whose sealed role is `EGO` or `COUNTER`, plus established background,
   before ranking the remaining objects. It provides the simple precedent that a known counter is
   no longer a probe subject.

2. **Ring 7.2 role-masked collision roster**  
   `variants/ring7.2/ARC3-Inference/virelai_v4/weave/collide_drive.py::masked_worldlines`

   Its governing rule is stronger and matches this slice: the counter is a valid target before it
   is learned; once sealed, all of its visual objects are removed from the target list. The same
   file explains why a draining counter must be removed by its complete trail/worldline rather
   than by its current anchor or fingerprint: every tick changes its visible component shape.

3. **Ring 7.2 recorded disregard rather than deletion**  
   `variants/ring7.2/ARC3-Inference/virelai_v4/weave/lever_witness.py`

   `witnessed_levers` disregards sealed-counter movers when deciding whether a press produced
   world delta. `no_effects` still records the counter motion and names the disregarded mover. This
   is the correct epistemic pattern: remove the counter from causal credit while retaining the raw
   observation for audit and possible future falsification of the counter seal.

4. **Ring 9 quotient-state mask**  
   `inference/framework/masked_world_state.py`

   This already implements the required spatial semantics. Every cell in `MaskLaw.cells` becomes
   a sentinel before state hashing, and every delta is partitioned exactly into disjoint HUD and
   world cells. Counter-only transitions therefore have identical masked state identity even when
   their raw grids differ.

5. **Ring 9 full-footprint counter law**  
   `inference/framework/counter_verification.py::mask_law_from_supported`

   `MaskLaw.cells` already uses `CounterCandidate.full_bar_footprint`, rather than only the cells
   changed by the latest tick. For vc33 this is the complete 64-cell row-zero bar. The v3 defect
   was therefore not an incomplete spatial mask. It was failure to apply that complete mask to
   roster eligibility and entity construction.

6. **Ring 9 scoped lever subtraction**  
   `inference/framework/lever_attribution.py::attribute_lever_outcome`

   The attribution kernel already subtracts every changed cell inside the counter mask before
   constructing local and remote residue. This worked for vc33 ranks 1–5. Its ordering currently
   checks pointer ownership before recognizing that the remaining residue is empty, which explains
   why direct interaction with the morphing counter became `UNRESOLVED_ATTRIBUTION`.

7. **Separate deterministic Golden solver: accounted sites and masked residue**  
   `/Users/stephenkaskin/Desktop/virelai-golden/golden/roles/counter_seal.py`,
   `golden/roles/mask.py`, and `golden/roles/lever.py`

   This is a separate repository and is used only as port material. Its newer counter representation
   carries `Accounting.sites`: the union of every site touched by both directions of the monotone
   exchange. It then defines lever residue as changed cells minus the counter sites at both ends of
   the press. Its recorded vc33 result is the same discriminating arithmetic seen here: ordinary
   clicks reduce to zero masked delta, while the two levers retain exactly 264 cells. The useful
   principle is that the mask belongs to the counter's total spatial process—the union of fill and
   empty sites—not to whichever connected component currently occupies part of it.

### Current gaps established by the mine and v3 trace

- `_LeverTarget.next_probe()` reads `counter._ranked_visual_targets` without filtering members
  contained in the accepted counter footprint.
- `EntityLedger` segments raw grids without ignored cells. Each counter tick therefore kills and
  births connected components even though the masked world state is unchanged. The v3 compact
  ledger reported 94 omitted transient entities.
- The known counter is not bound as a `COUNTER` role in the G3 entity ledger.
- G3 inventory reconciliation expects entities for the entire original G2 roster, so merely
  skipping a scheduled action would still leave an unresolved inventory obligation.
- The click scheduler retains `UNRESOLVED_ATTRIBUTION` indefinitely. That behavior is correct for
  an unexplained world object, but wrong when every observed changed cell is already assigned to a
  sealed counter footprint.
- `monitor_locked_counter()` contains useful HUD/world partition logic, although its historical
  “direct counter target reopens G2” rule should not govern this slice because the counter will no
  longer be intentionally scheduled after sealing.

## Design

### 1. Derive one immutable G3 frontier from the G2 roster and mask

Add a pure frontier compiler whose inputs are:

- the frozen ranked G2 visual candidates;
- the accepted `MaskLaw` and its version id;
- the demonstrated ego footprint, when embodied.

For each original candidate, compare its complete seed footprint with the full mask:

| Relation to mask | G3 treatment |
|---|---|
| candidate cells are wholly contained in the mask | record `COUNTER_ROLE_EXCLUDED`; do not schedule |
| candidate cells are disjoint from the mask | retain as an eligible target |
| candidate partially overlaps the mask | retain outside-mask subject matter and mark `PARTIAL_COUNTER_OVERLAP`; never exclude the whole candidate silently |

The compiled product must preserve both:

- `source_rank`: its original visual ranking from G2;
- `eligible_rank`: a contiguous G3 rank over scheduled targets.

For vc33, source rank 6 (`M0001`) becomes an explicit counter exclusion. The next scheduled target
after eligible/source ranks 1–5 is the former source rank 7.

### 2. Make exclusion auditable

Extend the inherited frontier with:

- `mask_law_version_id`;
- `eligible_candidates`;
- `excluded_candidates`;
- each exclusion's member id, source rank, footprint, disposition, and evidence references;
- counts proving `original = eligible + excluded`.

The completion certificate must verify that every original member is either:

- scheduled and terminally accounted for by G3; or
- excluded by an accepted role with an evidence-bound reason.

The counter is ignored for action selection, not erased from the history.

### 3. Suppress counter-only entity churn

Give `EntityLedger` a persistent `ignored_cells` or masked-component view derived from the same
`MaskLaw.cells`.

- Preserve the complete raw grid and raw transition outside the ledger.
- Exclude mask-contained cells before connected-component entity construction.
- Do not create births, deaths, recolors, or deformation identities for components wholly inside
  the sealed counter footprint.
- Keep any component with cells outside the mask visible through its outside-mask projection and
  attach a partial-overlap limitation.

The entity ledger and target frontier must consume the same mask version. A mismatch fails closed.

### 4. Partition delta before contact attribution

Make the quotient-state partition the first operation in G3 outcome handling:

```text
raw changed cells
-> counter/HUD cells + world cells
-> ego and ground subtraction over world cells
-> pointer/body attribution of remaining residue
```

For an eligible non-counter target:

- HUD-only raw change becomes `SCOPED_NULL_RESPONSE` for the tested action and state;
- HUD plus world change attributes only the world residue;
- no negative result becomes a universal inertness claim.

Add a defense-in-depth `COUNTER_ONLY_RESPONSE` for a stale or malformed schedule that directly
targets a counter-contained member. It is terminal for that roster entry, advances once, and
creates neither a lever witness nor an inertness claim. Normal operation should prevent this path
by excluding the target before action.

### 5. Reconcile lifecycle and inventory against the eligible frontier

Lifecycle entities and the final `LeverInventory` must be required only for eligible G3 targets.
The accompanying coverage certificate must separately account for counter exclusions.

This prevents a correctly excluded counter from remaining an unresolved entity that blocks
inventory acceptance. Confirmed levers continue to require a positive witness, later prospective
confirmation, Duck dossier, and `G4-READY` state.

### 6. Keep boundary monitoring alive

The raw transition still feeds the G2 counter monitor on every later action. Masking the counter
from G3 identity and causal residue must not suppress:

- source/replacement standing;
- minimum/maximum detection;
- game-over or respawn evidence;
- arithmetic contradiction that genuinely challenges the mask.

Thus the counter is absent from G3 attention while remaining present to the background monitor.

## Planned implementation surfaces

- `inference/framework/virelai_gates.py`
  - compile and store the eligible/excluded G3 frontier;
  - schedule only eligible targets;
  - reconcile completion and inventory against that frontier;
  - expose exclusion evidence in the gate view.
- `inference/framework/entity_observation.py`
  - add stable ignored-cell or masked-component construction;
  - prevent mask-contained component churn;
  - bind the counter role/exclusion provenance.
- `inference/framework/lever_attribution.py`
  - recognize HUD-only residue before pointer-owner failure;
  - add the defensive `COUNTER_ONLY_RESPONSE` disposition.
- `inference/framework/g3_checkpoint.py`
  - grade complete source-roster accounting as eligible terminals plus justified exclusions;
  - grade contiguous eligible order while preserving source ranks.
- focused tests under `tests/` plus a replay of the downloaded vc33 v3 evidence.

No game-engine implementation is needed or permitted for this work.

## Tests that must fail before the repair

1. The v3 prefix through action 10 asks for source rank 6 next instead of source rank 7.
2. Repeated counter ticks create transient entity births/deaths inside the masked footprint.
3. Inventory expects the sealed counter entity to reach a G3 lifecycle terminal state.
4. A direct click on the morphing counter becomes `UNRESOLVED_ATTRIBUTION` because its current
   component no longer owns the frozen acted site.

## Exit criteria

### Deterministic contracts

- A mask law spans the complete counter footprint, including source and replacement regions.
- Every fully mask-contained roster member is excluded exactly once with role and evidence.
- No disjoint candidate is excluded; partial overlap cannot silently erase outside-mask cells.
- Eligible ordering preserves the original ranking after exclusions.
- Counter-only raw transitions produce one masked world address and no G3 entity churn.
- A non-counter target with only a counter tick receives `SCOPED_NULL_RESPONSE` and advances.
- A stale direct-counter target receives terminal `COUNTER_ONLY_RESPONSE` and advances once.
- G3 inventory reconciliation covers every eligible target plus every justified exclusion.
- Raw frames, raw diffs, counter standing, and boundary monitoring remain unchanged and queryable.

### vc33 replay

- Replaying the v3 prefix preserves the rank-4 and rank-5 lever witnesses and confirmations.
- After rank 5, the next target is original source rank 7; source rank 6 is shown in the exclusion
  ledger and is never clicked by G3.
- The 94 counter-shape transients no longer appear in the G3 entity ledger.
- No same-rank counter loop is possible.

### Served rehearsal

- Fast OpenRouter verifies prompt/tool compatibility and the full eligible sequence.
- Dense Qwen3.6 completes all eligible vc33 targets and submits an accepted inventory.
- Only after that result should a new immutable Kaggle milestone be considered.

## Explicit non-goals

- Do not infer detailed lever mechanisms; that remains G4.
- Do not require a counter extremum before G3 begins.
- Do not discard raw counter evidence or stop background monitoring.
- Do not call scoped null targets universally inert.
- Do not repair dossier prose validation in this slice unless a change is mechanically required by
  the new masked evidence view; that should remain a separate focused slice.

## Build order

1. Freeze replay fixtures from the v3 artifacts without importing game-engine mechanics.
2. Add the pure eligible/excluded frontier compiler and its accounting tests.
3. Apply the same mask to entity construction and prove counter ticks create no G3 identities.
4. Reorder attribution around world residue and add the defensive terminal disposition.
5. Reconcile lifecycle, inventory, gate view, and checkpoint evaluator.
6. Run the focused replay, full local suite, fast served smoke, and dense rehearsal in that order.

## Implementation and validation record

Implemented in the active Ring 9 source on 2026-09-24:

- G3 now compiles an immutable mask-filtered frontier with preserved `source_rank`, contiguous
  `eligible_rank`, and explicit `COUNTER_ROLE_EXCLUDED` rows bound to the accepted mask version
  and its witness evidence.
- the scheduler, entity bindings, lifecycle journal, and inventory operate only on eligible
  targets; source-roster completeness is retained in the separate exclusion ledger;
- the entity ledger constructs components outside the same total mask while retaining raw frames,
  so counter motion no longer creates G3 births, deaths, or recolor hypotheses;
- lever attribution consumes the full mask and supports the defensive terminal
  `COUNTER_ONLY_RESPONSE` without creating a witness or inertness claim;
- the G3 certificate now checks `original = eligible + excluded`, source-rank conservation,
  contiguous eligible ranks, mask-version identity, and evidence-bound exclusions.

Validation:

- focused G3 tests: **34 passed**;
- all offline tests: **328 passed**;
- lint over changed implementation and test surfaces: **passed**;
- the two remaining full-suite modules require the unavailable local `taaf` runtime and fail at
  import collection rather than in this slice;
- frozen vc33 v3 replay: **PASS**, recorded at
  `runs/replay-g3-v3-total-counter-mask-v1/result.json`.

The replay directly observed 11 frozen candidates partitioning into 10 eligible targets and one
counter exclusion. Source rank 6 (`M0001`, all 64 row-zero cells) was excluded, source rank 7 was
next, and the 31 historical counter-loop transitions left entity count unchanged at 22 with no
frame-chain limitation. This is deterministic replay evidence. It does not establish served-model
use, prompt compatibility, or live G3 inventory closure.

The next step is the already planned dossier-semantics and bounded-ambiguity hardening, followed by
fast OpenRouter and dense rehearsal. The old v3 package and execution artifacts remain unchanged.

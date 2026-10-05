# Ring 9 single-tree unification

**Type:** `UNIFICATION_RING9_SINGLE_TREE` · **v1** · **2026-10-05**
**Status:** locally validated integration checkpoint on branch `ring9-unified`
**Canonical source path:** `variants/ring9-cybernetic-gates/ARC3-Inference/`
**Signed:** Sol, Alpha build seat, with read-only audits from the Claude, runtime, and lineage seats.

## Purpose

Ring 9 had become two real source lines after commit `fbbc7f4`:

- `main` carried the NAV controller, terrain, reachability, target ledger, and N5.3 first-witness work through `aa799b5`;
- `r9-r20-level-entry` carried the CLICK, life/level/carry, partial G3, mu, controller-first G4, bounded Duck budget, and normal-play work through `c9b246b`.

The project needs one editable source tree before submission work can continue. This checkpoint combines those lines without turning a frozen Kaggle package, a run artifact, or an older variant into source.

## Governing behavioral contract

G3 discovers. G4 types.

For CLICK and NAV alike:

1. select the next ranked visual target;
2. activate it by clicking it, or by routing the ego to intentional contact;
3. subtract the locked counter and ego-motion footprints;
4. when an attributable positive world residue remains, write a durable `LEVER_FOUND` witness;
5. advance the G3 roster immediately;
6. repeat the lever only in G4, where state, orbit, mechanism, condition, and relations are studied.

A later null or different result may refine the lever's type. It never retracts the observed causal witness. Ambiguous, unreachable, or currently unproductive targets may enter the mu inventory without blocking certified levers from G4. Mu returns only when the evidence relevant to that target changes.

## Evidence boundary

| Asset | Meaning during unification |
|---|---|
| `variants/ring9-cybernetic-gates/ARC3-Inference/` | The only editable runtime source |
| `kaggle/ring9-g3-nav-n5-3-ls20-v1/` | Frozen package of NAV commit `aa799b5`; do not edit |
| `kaggle/ring9-carry-vc33-v8/` | Frozen package of CLICK commit `c9b246b`; do not edit |
| `runs/<run>/` | Executed observations; preserve exactly |
| `tests/fixtures/*.json.gz` | Versioned replay evidence, not a production adapter |
| Ring 8, Ring 7, vendored golden, separate `virelai-golden` | Donors and historical evidence only |

Direct live evidence supports N5.3's NAV first-witness path, vc33 v6's CLICK discovery/G4-A handoff, and vc33 v7's partial inventory/G4 progress. R9-R24's controller-first G4 has builder-reported tests and record pre-flight evidence; no completed live v8 review was found during the audit. Mu return, newborn-object scheduling, and NAV record-derived G4 relations therefore remain unproven until the unified tree exercises them.

## Merge invariants

- Preserve NAV deterministic movement, terrain learning, bounded reachability falsification, and reachability-signature reopening.
- Preserve the N5.3 transition from first positive NAV contact to `LEVER_FOUND`, with no confirmation detour.
- Extend that same transition to CLICK.
- Preserve life-aware records, level freezing, cross-level carry, partial G3 closure, and the mu bucket.
- Preserve controller-first state naming and relation extraction wherever the record is sufficient.
- Generalize record-derived relations to NAV contact attribution before calling them world-type complete.
- Keep Duck behind the deterministic controller. Duck receives a turn only for semantic residue the controller cannot settle, within the per-level budget.
- Preserve normal play after the gates and label its transitions `FREE_PLAY`.
- Declare the persistence tier of every new field.
- Keep every prior source branch, package, fixture, and executed run available as provenance.

## Validation ladder

The branch is not canonical merely because Git reports a clean merge. It must pass these checkpoints:

1. no conflict markers, imports compile, and persistence declarations cover the merged state;
2. CLICK and NAV both satisfy the shared first-witness contract;
3. NAV still advances to the next roster target and seeds G4 from the exact first witness;
4. vc33 v6/v7 replay preserves life, level, carry, partial inventory, G4 intake, and controller-derived answers;
5. NAV N5.1/N5.3 evidence preserves terrain, reachability, and lever discovery behavior;
6. ownership tests show deterministic G0-G4 work remains controller-owned;
7. a clean Git export builds a package whose manifest references only files present in the mount.

The focused Ring 9 source-root validation completed on this unified branch with **605 passed, 1 skipped** (14 dependency warnings) in 6m18s. The test run used the repository's established Python environment and explicitly added the bundled framework source to `PYTHONPATH`; it did not mix the other variant test trees. This validates the local integration contract and replay behavior, but does not substitute for a fresh Kaggle live run.

The local test environment currently lacks the external `taaf` package on its default path. That is an environment limitation, not a passing test result. Validation must either add the repository's framework source to the test path or run in the established Mac/Kaggle environment; builder-reported historical counts remain reports until rerun on the unified commit.

## Deliberately deferred slices

Macro contact-surface consolidation, newborn-object scheduling, the submission scheduler/perception ports, G8 win explanation, win ledger, and `ACT_ON_GOAL` are separate post-merge slices. They may be mined from prior art, but none is silently claimed by this merge.

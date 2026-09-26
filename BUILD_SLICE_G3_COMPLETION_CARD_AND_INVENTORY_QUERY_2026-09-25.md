# Build slice: G3 completion card and callable inventory

**Type:** `BUILD_SLICE` · **Date:** 2026-09-25  
**Status:** built and offline validated; focused live validation pending

## Purpose

G3 must keep Duck focused after the broad lever sweep without resending the entire world-model
store. The v6 vc33 run completed the eligible sweep and accepted a bounded-coverage report, then
the next automatic gate message exceeded the 24,000-character binding-view guard. This slice
repairs that delivery boundary. It does not change which probes run or what counts as knowledge.

## Mined precedent

Ring 8 expandable-memory work already established the useful pattern: a bounded automatic index,
stable expansion handles, and a lossless persistent store. The active Ring 9 code already had
focused entity and evidence queries plus a compact in-progress roster. The missing piece was a
stage-specific view for the moment after roster exhaustion.

Historical V4 planning also supports coverage-bounded, reopenable knowledge. It is prior art,
not live evidence and not a mandate to close G3 on unresolved objects. The active nonclosing
bounded-ambiguity semantics remain unchanged.

## Built behavior

After G3 enumeration is complete and no lever dossier is pending, the automatic gate view becomes
`virelai-g3-completion-card-v1`. It reports:

- sweep method and completion accounting;
- counter-mask reference and role exclusions;
- confirmed levers, scoped nulls, bounded unknowns, and unresolved entities;
- the accepted inventory or bounded-coverage answer;
- epistemic limits and the next permitted operation;
- callable handles for inventory, entity, and evidence expansion.

The card excludes the full frontier, entity ledger, lifecycle journal, confirmation archive, and
raw evidence records. These remain lossless in `CyberneticGateMachine.snapshot()`.

Duck can call `virelai('inventory', offset=0, limit=10)` to retrieve a deterministic page of the
full G3 partition. Each eligible target includes rank, member and entity identity, disposition,
lifecycle state, evidence references, retry condition where applicable, and a focused entity
query. Counter-mask exclusions appear as explicit role-exclusion rows.

Checkpoint evaluators consume `snapshot()`, while Duck consumes `gate_view()`. This prevents a
transport optimization from weakening evaluation evidence.

## Exact replay evidence

The replay tool at
`variants/ring9-cybernetic-gates/ARC3-Inference/tools/replay_g3_v6_completion.py` consumes the
immutable artifacts from
`runs/20260925_000340_ring9-g3-vc33-openrouter-fast-rung-20260925-v6/artifacts`.

Observed results:

- 12 stored G3 probes replayed;
- final bounded report accepted;
- old working view: 24,632 characters;
- new completion card: 7,623 characters;
- lossless snapshot: 660,019 characters;
- partition preserved: 2 confirmed levers, 5 scoped nulls, 3 bounded unknowns, 1 counter
  exclusion;
- every inventory row retrievable through pagination.

This is direct deterministic replay evidence from a completed live trace. It is not evidence that
the served model has yet consumed the new card.

## Validation

- 48 focused tests pass across G3 scheduling, tool delivery, checkpoint grading, and G2 counter
  behavior.
- 333 offline tests pass, excluding the two explicitly online/native suites.
- lint passes on all changed production, test, and replay files.
- a production-path bridge test proves the inventory query response is present in Duck-visible
  tool output and carries its pagination state.

## Exit criterion

Run one focused vc33 live rung from the active source. This slice passes live when the run reaches
the post-report turn beyond action 15 without the binding-view overflow, and the compact card plus
focused inventory query remain available. Lever counts may differ if the live trajectory differs;
G3 semantics are graded separately.

## Deferred rungs

Qualified G3 closure, the G4 reaction adapter, and scheduling newly appearing visual objects are
separate builds. They should be designed from the evidence produced after this delivery repair,
without treating bounded ambiguity as proof of inertness or as semantic closure.

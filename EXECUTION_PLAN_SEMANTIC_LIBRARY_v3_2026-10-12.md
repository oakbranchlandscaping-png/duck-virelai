# Execution plan: semantic library v3

**Date:** 2026-10-12
**Governing plan:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v3_2026-10-12.md`
**Starting source:** `b635fb9`
**Working model:** Sol supervises and reviews; Claude Alpha implements granular slices; the Director rules and authorizes runs.

## 1. Current checkpoint

The v2 model, census, hooks, bounded live view, G3 CLICK choice, reset continuity, and G3 NAV pursuit are accepted locally. The full floor is 792 passed, 1 skipped. Seven accepted commits have not been pushed. The next code change starts from `b635fb9`; it does not start from remote `main`.

## 2. Order of work

| Order | Work order | Owner | Dependency | Exit evidence |
|---|---|---|---|---|
| 1 | **WO-TEST-RHYTHM**: measured T0/T1/T2 test tiers | Claude builds; Sol reviews | `b635fb9` | inventory and timing report; T0 <90 s; T1 <5 min target; unchanged full collection and T2 result |
| 2 | **WO-G4-DOSSIER-A**: schema v3 and read-only G4 dossier projection | Claude / click expertise; Sol reviews | order 1 | fail-first schema, receipt, interruption, and determinism tests; no gate mutation |
| 3 | **WO-G4-DOSSIER-B**: gate-owned per-lever question selection | Claude builds; Sol reviews pursuit semantics | order 2 | off-head choice, fallback, stale, mandatory-work, no-choice golden, prompt agreement |
| 4 | **WO-L1a-NAV** and **WO-NO-REPAIR-LOOPS** | Sol directs; Claude builds | may overlap 2–3 if shared files are disjoint | saved G1 cases close or type the gap; one refusal is recorded once and ladder proceeds |
| 5 | **PACKAGE-LIBRARY-PUBLIC25-CURRENT** | Director executes after Sol accepts source | orders 1–4 | package manifest, current commit, 25-world run, canonical models, per-world report, errors and latency |
| 6 | **WO-REPORT**: world manifest and human report | Claude builds; Sol checks single-writer rule | accepted schema and run artifact | deterministic render from validated JSON; no second belief store |
| 7 | **WO-G5/G6**: forces, driven reactions, scoped negatives | assigned by Director | reliable G4 path | gate products, schema chapters, evidence and prospective-status tests |
| 8 | **WO-GRAMMAR**: typed law compiler | Claude builds from accepted contract | order 7 | sentences grounded in receipts; contradiction/reopen tests; bridge is projection only |
| 9 | **WO-WIN-TRANSFER** | assigned by Director | typed grammar and level freeze | frozen level-N sentence; level-N+1 prediction; referee verdict |
| 10 | **SUB-4**: bounded fallback context restart | Claude Alpha | runtime reliability established | three-restart cap, reasons, unchanged canaries outside submission mode, recovered-time report |

Push is outside this execution plan.

## 3. WO-TEST-RHYTHM contract

The first slice inventories test durations and dependency clusters before changing the runner. It may cache immutable replay loading, reuse verified fixtures, or shard independent groups. It must compare collected test identities before and after. It may not delete, weaken, skip, xfail, reorder stateful tests to hide coupling, alter goldens, or change solver behavior.

Required outputs:

- commands or a small runner for T0, T1, and T2;
- machine-readable membership for each tier;
- top slow tests and setup costs;
- cold and warm timings;
- proof that T2 collects the same accepted tests as the current floor;
- guidance in `BUILD_RHYTHM.md`.

T0 runs while editing. T1 runs at slice handoff. T2 runs once after Sol accepts the slice and before packaging, release, or a shared runtime merge.

## 4. WO-G4 dossier contract

### Slice A: schema and projection

Add `virelai-world-model-v3` with one dossier per certified lever. Minimum chapters are anatomy, orbit, relations, and law. Each chapter carries a status, gate, subject, accepted answer or gap, receipt references, conditions, contradictions, and next question.

Allowed explicit statuses include:

`ANSWERED_IN_PRODUCT`, `GATE_ACCEPTED_PRODUCT_PENDING`, `RUNNING`, `COMPLETED`, `INTERRUPTED`, `UNSTUDIED`, `PRESSED`, `UNPRESSED`, `AGGREGATE_ONLY`, `NOT_REACHED`, and `CLOSED_UNRESOLVED`.

Project from gate state at H1, H2, and LIVE_VIEW. Do not add a second gate-owned ledger merely for the census. Validate every certified chapter against its receipt table. A hard process kill may remain an explicit limitation.

### Slice B: selected study

The G4 gate exposes the questions it can actually serve. Duck chooses one only on an existing Duck turn. The controller takes the default when Duck declines or times out. Mandatory pending work precedes optional selection. Selection identity uses the gate's lever subject, with census track data attached as context only. The card, digest, capability, probe, outcome, and dossier must agree.

## 5. Runtime friction gate

Before order 5, close or explicitly accept every remaining release blocker:

- the nine NAV G1 stops from the v2 rehearsal;
- rejected-answer repair loops;
- prompt size and Duck turn latency with the dossier view;
- controlled-stop handling and last-level freeze;
- record mismatches, crashes, or lifecycle faults in saved replays;
- any regression in controller-only behavior.

SUB-4 does not excuse an earlier gate defect.

## 6. Public-25 run contract

The package records its exact commit and file hashes. Run each public world once with full slices. Collect benchmark and kernel logs, execution receipts, turn ledgers, G3/G4 selection events, every `world_model.json`, the manifest, and the human report. Exclude large dependency trees from downloads.

The report states:

- worlds and levels observed and accounted;
- roles and lever dossiers by world;
- gaps by reason and gate;
- Duck calls, choices, timeouts, and executed actions;
- controller actions and handoffs;
- record mismatches, controlled stops, crashes, and false-certification checks;
- prompt size and turn latency;
- clears and wins as outcomes.

Do not submit to the competition from this diagnostic order.

## 7. Review and commit protocol

1. File a shared-file note before editing any shared runtime file.
2. Demonstrate the intended failure on accepted source.
3. Build the narrow slice.
4. Run T0, then T1.
5. Sol reviews source, replay semantics, artifacts, and any golden difference.
6. Run T2 once after acceptance.
7. Commit explicit paths with the evidence documents.
8. Push or fast-forward `main` only when the Director directs it.

Untracked grammar and reporting files are outside accepted source until their named work orders land.

# Fresh-task bootstrap: Ring 9 library build

**Date:** 2026-10-12
**Use:** cold start for a new team member
**Accepted local source:** `ring9-unified` at `b635fb9`
**Supersedes:** `FRESH_TASK_BOOTSTRAP_2026-10-07.md`

## 1. First orientation

Read, in order:

1. `START_HERE.md`
2. `STATE_OF_THE_DUCK_BUILD_v5_2026-10-12.md`
3. `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v3_2026-10-12.md`
4. `EXECUTION_PLAN_SEMANTIC_LIBRARY_v3_2026-10-12.md`
5. `RULINGS_CONSOLIDATION_v4_2026-10-10.md`
6. `RECORD_RING9_TEST_FLOOR_v2_2026-10-12.md`

Then read the interface and build report for the slice you are assigned. Do not begin with an older strategy narrative or a transfer-folder summary.

## 2. Repository and branch

- Work in `duck-virelai-r9r20` on `ring9-unified`.
- Active runtime is `variants/ring9-cybernetic-gates/ARC3-Inference/`.
- `b635fb9` is the accepted local head.
- `main` and the remotes are still at `472aa32`; `ring9-unified` contains accepted runtime `b635fb9` plus later documentation commits. Inspect Git for the live ahead count.
- `main` fast-forwards only after the accepted floor and Director direction.
- Kaggle packages are built from the commit named in their manifest. Do not assume remote `main` contains the current solver.

Before editing, inspect branch, head, worktree status, and recent commits. The worktree contains untracked research and draft files; never use a blanket add.

## 3. Team split

- The Director makes product and doctrine decisions, authorizes run spend and submissions, and may execute terminal commands.
- Sol defines the next slice, reviews code and evidence, and protects the library architecture.
- Claude Alpha performs granular implementation and fail-first testing.

Builder reports are inputs to review. Sol checks the changed source, failing premise, relevant replay, artifact integrity, and test evidence before accepting a slice.

## 4. Current objective

Turn the semantic library into the solver's target. The gate names the current knowledge gap and owns the admissible experiments. Duck reads the library and chooses where judgment helps. The controller performs routine action sequences. Deterministic code certifies the result.

Current gate order in code:

1. G1: control locus / ego
2. G2: counter
3. G3: lever roster
4. G4: per-lever mechanics
5. G5/G6: forces, driven reactions, scoped negatives, and remaining grammar

Push is shelved. A clear is evidence to describe and test across levels, not the action-selection objective.

## 5. Next assignment sequence

1. Test-runtime infrastructure and tiered floors.
2. G4 schema-v3 dossiers and projection.
3. G4 selected-question integration.
4. NAV G1 and no-repair-loop closure.
5. Current-source public-25 diagnostic.

Do not start G5/G6, observed-win transfer, Push, or SUB-4 inside these slices.

## 6. Shared-file rule

One seat edits a shared file at a time. File a note before the first shared edit naming:

- files and owner;
- accepted base commit;
- behavioral contract;
- fail-first cases;
- protected behavior and goldens;
- handoff conditions.

If an unexpected defect changes the slice, stop the edit, record the finding, and get the revised boundary reviewed. An after-the-fact amendment must say that it was written after the edit.

## 7. Test rhythm

Use the tiers defined by the accepted WO-TEST-RHYTHM output:

- T0 for edit feedback;
- T1 at slice handoff;
- T2 once after Sol accepts the slice and before packaging or release.

Until that slice lands, use the focused tests named by the current work order and preserve the full command from the latest build report. The current full reference is 792 passed, 1 skipped at `b635fb9`; it takes about 26 minutes. The uncommitted physics grammar contract is excluded from that accepted floor.

Never improve time by weakening coverage. State exactly which tier ran and its elapsed time.

## 8. Evidence and artifacts

- Gate state and receipts are authoritative for certification.
- The canonical model has one writer.
- The live view may read and validate but cannot persist the canonical artifact.
- A model assertion is a hypothesis until the deterministic path accepts it.
- FREE_PLAY and GATED receipts stay distinct.
- A golden may change only after the semantic cause is explained and reviewed.
- A live run is read feature-first: prove the feature ran, inspect artifacts and errors, then examine score.

## 9. Commit and handoff

Stage explicit paths. Include the shared-file note and build report. Keep drafts and unrelated untracked files out of the commit. A handoff states:

- base and resulting commit;
- changed files;
- fail-first result;
- focused and tier results with elapsed times;
- replay or live evidence;
- artifact/schema effect;
- known limitations;
- exact next dependency.

Do not push, merge to `main`, launch Kaggle, or submit unless the Director has directed that action.

## 10. Historical documents

Dated plans, statuses, rulings, reviews, and run reports are immutable records. When their current meaning changes, create the next version and update `START_HERE.md`, `README.md`, and the documentation index. Living process maps such as `BUILD_RHYTHM.md` may be updated in place with a dated amendment.

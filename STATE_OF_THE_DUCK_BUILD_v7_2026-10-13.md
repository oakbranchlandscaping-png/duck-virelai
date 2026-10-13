# State of the Duck build v7

**Date:** 2026-10-13
**Status:** current handoff record
**Source reviewed:** `ring9-unified` at `5fdac9a` (runtime behavior remains `b635fb9`)
**Supersedes:** `STATE_OF_THE_DUCK_BUILD_v6_2026-10-12.md`
**Governing plan:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v4_2026-10-12.md`

## 1. Executive state

The build has crossed from a passive library artifact into a library-directed G3 solver. It now writes a canonical per-game world model, shows Duck a bounded validated view, lets Duck choose an admitted off-head lever question in CLICK or NAV, and lets the controller execute the resulting bound experiment while preserving receipts and attribution. Reset continuity is repaired, and corrupted transition records fail closed in Duck's library.

The ideal solver is not complete. It cannot yet describe every visual object and grid transformation in the canonical artifact, G4 does not expose a durable per-lever dossier, later grammar chapters are absent, and runtime frictions still prevent a clean current-source public-25 rehearsal. The test-rhythm milestone is complete. The next milestone is the schema-v3 descriptive event ledger and scene view, followed by G4 roster dossiers and closure of the remaining runtime blockers.

## 2. Accepted source and repository state

| Item | State |
|---|---|
| Active runtime | `variants/ring9-cybernetic-gates/ARC3-Inference/` |
| Working branch | `ring9-unified` |
| Accepted local head | `5fdac9a` |
| Remote and local `main` | `472aa32` |
| Local commits not pushed | accepted runtime/plan commits and later documentation commits; inspect Git for the live count |
| Accepted full Mac floor | T2: 816 passed, 1 skipped; 534.4 s with 4 workers |
| Accepted slice floor | T1 directed G3: 143 passed; 272.1 s with 4 workers |
| Scored competition submission | none recorded |

The accepted capability chain through this status, omitting documentation-only commits, is:

| Commit | Capability |
|---|---|
| `8e13e35` | library-first build and execution plans v2 |
| `125d4d0` | bounded live library view and retrieval |
| `db8a657` | directed G3 CLICK selection |
| `4a18c4d` | HYBRID CLICK one-turn handoff |
| `2a79081` | legacy confirmation replay guard |
| `ceeeabd` | reset-continuous ledger and fail-closed library |
| `b635fb9` | directed G3 NAV selection and pursuit |
| `5fdac9a` | tiered replay-safe test runner and accepted T0/T1/T2 floors |

## 3. What is built

### Canonical library foundation

- `world_model.json` schema v2 has one canonical writer and a validator.
- The census reconstructs levels from the opening board and transition record.
- H1 freezes the ended level before state advances; H2 reconciles every observed level at run end and on controlled terminal paths.
- Receipts bind transitions, gate products, and G3 witnesses. Forged or mismatched references fail validation.
- Missing, duplicated, or contradictory records become typed `RECORD_MISMATCH` and `BOARD_DISCONTINUITY` gaps. Dependent claims leave the certified view.
- Early stops and observed-never-acted games can still yield an accounted level-entry artifact.

### Duck's reading surface

- A validated in-memory live view is attached to Duck turns and cannot save the canonical file.
- The digest is bounded to 2,500 characters and leads with the selected question, certified findings, and actionable gaps.
- Paged retrieval exposes library sections without placing the whole artifact in every prompt.
- Gated-only mode owns the canonical writer. Other modes leave an existing canonical file untouched.
- Terminal controlled stops are distinguished from normal run ends.

### Library-directed G3

- G3 exposes its own admissible candidate list; the agenda does not recreate gate eligibility.
- Duck may choose an eligible lever question on a turn it already receives. The controller never waits for an extra model call.
- With no choice, the committed scheduler and golden traces remain unchanged.
- CLICK and NAV use bound selection probe IDs, durable selection events, matching receipts, and target-specific attribution.
- NAV pursuit keeps the same selected experiment across route steps. A stale choice yields cleanly to coverage and resets step count, plan, and route evidence.
- Mandatory confirmation, reachability, and lifecycle work keeps priority over optional choices.
- The controller resumes coverage after a decline, timeout, stale choice, or completed off-head experiment.

### Evidence continuity

- G2 starts from the latest observed board, including resets during G1.
- G3 replays G2 outcomes and later resets in transition order when it builds its ledger.
- On the saved k008 and k013 records, ledger mismatches fall to zero without adding a false lever.
- Departed objects remain in history; those never touched by G3 are omitted from the actionable agenda.

### Development test system

- T0, T1, and T2 are declared in one checked manifest.
- The complete T2 collection must match an exact 817-node snapshot.
- Cached replays return isolated copies and bypass the cache while production callables are patched.
- Parallel workers have separate scratch paths, are fully accounted, and are reaped on interruption.
- The accepted T2 takes 8:54 on the four-core Mac, down from about 25:36 while adding 24 safety tests.

## 4. What the live evidence says

The public-25 library diagnostic built from `db8a657` completed before the reset and NAV-directed slices. It produced:

- canonical libraries for 25/25 public worlds;
- 28/28 observed levels represented;
- 83 lever-role entries across 9 worlds;
- 11 G3 handoffs and 2 recorded choices;
- 1,885 environment actions and 3 level clears;
- no complete game win.

This establishes that the artifact pipeline can cover the public set. It does not accept the current `b635fb9` behavior or the remaining runtime path. A new run is required after the next reliability gate.

## 5. Remaining gaps by priority

| Priority | Gap | Why it matters | Close condition |
|---|---|---|---|
| P0 | The canonical library lacks a full scene and transformation description | The agent cannot express an observed win in a language it does not yet use for ordinary events | schema-v3 event ledger; exact nouns, verbs, deltas, receipts, residuals, and bounded views |
| P0 | G4 has no durable per-lever dossier in the library | Duck can discover levers but cannot systematically deepen each one | schema v3 dossiers, receipts, statuses, bounded retrieval, gate-owned selection |
| P0 | Nine NAV-side G1 stops and repair-loop behavior remain | Worlds can stall before useful library work | saved replays close or type each stop; one failed answer cannot loop |
| P1 | Current-source public-25 evidence is missing | Latest selection and continuity code has not run end to end | named package from accepted source; per-world report and artifact audit |
| P1 | World manifest and human report are not accepted | New members and paper readers need one canonical rollup | committed tools render from validated JSON only |
| P1 | G5/G6 and complete census roles are absent | Forces, driven reactions, and scoped negatives are central grammar chapters | gate products, schema chapters, evidence-backed questions and closure |
| P2 | Typed physics grammar remains a draft | Findings are not yet compiled into the full internal language | accepted schema and compiler; prospective tests; no second belief writer |
| P2 | Observed-win transfer is unbuilt | The system cannot freeze a learned win sentence and test it on the next level | level-N freeze, level-(N+1) prediction and referee verdict |
| P2 | SUB-4 recovery is unbuilt | One free-play stop can still waste slice time | submission-only, capped restart with receipts and recovered-time report |

Push and win-seeking frontier exploration remain shelved.

## 6. Directed execution order

1. Build the schema-v3 descriptive event ledger, exact scene state, bounded retrieval, and deterministic report.
2. Build G4 dossier projection, then bind gate-owned per-lever selection.
3. Close NAV G1 and no-repair-loop friction before calling the runtime reliable.
4. Package the accepted source and run the public 25 once, grading descriptions as well as roles and gaps.
5. Build G5/G6, full grammar sentences, observed-win transfer, then bounded fallback recovery.
6. Freeze, rehearse, and make the scored submission under the competition directive.

Independent work may overlap, but dependency order and release gates do not change.

## 7. Uncommitted work that is not part of this accepted state

The worktree contains untracked grammar drafts, a win referee, report/package tools, and historical transfer documents. Their presence does not make them accepted runtime. Review and land them through named slices or leave them outside the package. Do not accidentally stage them with documentation changes.

## 8. Acceptance discipline

A slice closes only after source review, fail-first evidence, focused tests, the appropriate tiered floor, replay or live artifact evidence where applicable, and a specific-path commit. Golden updates require an explained semantic cause. No test may be weakened, removed, skipped, or converted to xfail to make a floor green.

# State of the Duck build v10

**Date:** 2026-10-15
**Status:** current handoff record
**Supersedes:** `STATE_OF_THE_DUCK_BUILD_v9_2026-10-14.md`
**Governing plan:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v4_2026-10-12.md`, executed through `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4_2026-10-12.md`. The paper-evidence chain follows `BUILD_PLAN_PAPER_EVIDENCE_v1_2026-10-07.md` §2 and §4, as ruled in `RULINGS_PAPER_EVIDENCE_v1_2026-10-14.md` (D1-D14).
**Author:** Claude (Alpha build seat)
**Scope:** game-free. This record states the solver's capability only; it names no world's contents.

**Grounding** (read directly on 2026-10-15, from the Director's worktree):
- **Refs:** read with `git --git-dir` against the repository's own `.git`, read-only. No fetch was run.
- **Source content:** all 310 `.py`, `.toml`, `.txt` and `.json` files under the runtime's `inference/`, `tools/`, `tests/` and `virelai_golden/` match `e158057` by blob hash. None is missing.
- **Acceptance evidence:** Sol's closure records `REVIEW_WO_PE_01_PROVENANCE_CAPTURE_v1_2026-10-14` and `REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v3_2026-10-15`. The Mac figures below are quoted from them, not re-run here.

## 1. Executive state

- **The provenance layer is complete and committed.** It has two slices:
  - **WO-PE-01, `afe93c8`:** every probe and answer the gates decide on is captured in a hash-chained, append-only audit journal, refusals included. This covers who submitted it, what was submitted, what the controller filled, and what reached the environment.
  - **WO-PE-02, `e158057`:** the validated journal is absorbed into `world_model.json` **schema v4** as one provenance chapter. It reports the journal's integrity and whether the run's work is completely accounted for.
- **An ordinary run can now truthfully reach `SEALED / COMPLETE`.** The real controller run does. So does a real two-level run through the production H1/H2 path, and every product there joins an admission from its own level.
- **The next slice is WO-PE-03, read-only design first:**
  - atomic claims projected from the sealed v4 model;
  - the answer-key format the Director will author against;
  - the five-category grader.

  Schema, capture, gates, scheduling and action selection stay fixed while it is designed (Sol's closure).
- **The scored competition submission is not recorded in any document read for this state. This item stays red until the Director records it.** Kaggle run folders `runs/kaggle-ring9-submission-v1` (9 Oct) and `-v2` (10 Oct) exist on disk; no leaderboard entry or score is filed beside them or in any later state.
- **The formal current-source public-25 evidence run still waits.** It needs the claim projection, the Director's keys and the grader, all committed. Historical runs remain diagnostic only (D12): they predate capture.

## 2. Repository position (verified 2026-10-15)

| Item | State |
|---|---|
| Active runtime | `variants/ring9-cybernetic-gates/ARC3-Inference/` |
| Working branch | `ring9-unified` at **`e158057`** (*Build schema-v4 provenance reconciliation*, 2026-10-15). The worktree `HEAD` points at it. |
| Remote-tracking ref | `origin/ring9-unified` is `472aa32`, last updated 2026-10-11 and not re-fetched. `ring9-unified` is **16 commits ahead and 0 behind**. **Nothing has been pushed.** |
| `main` / `origin/main` | Both at `472aa32`. `ring9-unified` is 16 ahead of `main`. Under the branch rule, `main` fast-forwards only after the Mac suite passes, and that suite has now passed at `e158057` (§3). The fast-forward and the push are the Director's to run. |
| Untracked (not ignored) | <ul><li>7 documentation drafts at the root, including `PRIOR_ART_REMAINING_LIBRARY_PHASES_SOL_v1_2026-10-14.md` and `SPEC_PHYSICS_GRAMMAR_v3_2026-10-08.md`;</li><li>three `kaggle/` package folders;</li><li>two `tools/` scripts (`package_ring9_public25_library_v1.py`, `report_ring9_public25_library_v1.py`);</li><li>the four draft grammar files (`physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `tests/test_physics_grammar_contract.py`).</li></ul>None is accepted runtime, and none is staged. `runs/`, including every `_cowork_xfer` package, is ignored by `.gitignore`. |
| Canonical artifact | `world_model.json`, schema **`virelai-world-model-v4`**: the v3 levels plus a top-level `provenance` chapter and per-level `provenance_index` and `product_answers`. v1, v2 and v3 artifacts still read through their frozen validators. |
| Audit journal | `{run_stem}_provenance.jsonl` beside the runtime state: append-only, hash-chained, sealed with its run's identity |
| Semantic library report | `world_report.md`, unchanged by PE-01 and PE-02 |
| Scored competition submission | **Not recorded. Red.** |

## 3. Floors

| Floor | Value | Source |
|---|---|---|
| **T2, effective, `e158057`** | **1,038 passed, 1 skipped, of 1,039 collected.** The managed Mac run gave 1,036 passed and 1 skipped. Its two process-cleanup tests were blocked by host `ps` restrictions and both passed in a separate host-access run. | Sol, PE-02 closure |
| Manifest | exactly **1,039** (`tests/tiers/T2_collected.txt`) | Sol, PE-02 closure |
| T2, effective, `afe93c8` (prior) | 974 passed, 1 skipped, of 975 | Sol, PE-01 review |
| T0 `provenance-v4` | 93 passed | sandbox, revision 3 |
| T0 `provenance` | 76 passed | sandbox, revision 3 |
| T1 `paper-evidence` | 329 passed | sandbox, revision 3 |
| T1 `description` | 204 passed | sandbox, revision 3 |
| H2 overhead, 800-row journal | **0.251 s** added (ceiling 0.5 s) | Mac, synthetic, PE-02 closure |
| Archives | PE-02 package 9/9 and slice 17/17 hashes matched | Sol, PE-02 closure |

**Capability chain since v9** (documentation-only commits omitted):

| Commit | Capability |
|---|---|
| `afe93c8` | **WO-PE-01:** the provenance audit journal. All six admission points are captured (D3). Every answer keeps its submitted payload, effective payload and field sources (D4). Executions join their exact admissions. The seal names the run. A journal failure never changes play. |
| `e158057` | **WO-PE-02:** schema v4. H2 reads the sealed journal once, embeds the verified rows once, and stamps the file hash and seal hash. It reconciles admissions, executions, transitions, evidence receipts and products, adds the gate-answer cross-check, and states completeness with every reason. H1 and live views read no journal. Also: the run roster and the sidecar verifier. |

## 4. What the provenance layer does, and its epistemic limits

### Capabilities

- **Every gated decision is on the record, refused or admitted.** Probes, answers, G3 selections and annotations from Duck and the controller produce `ADMISSION` rows. Admitted probes that reach the environment produce `EXECUTION` rows. A G3 handoff with no selection is an `OPPORTUNITY / NOT_ATTEMPTED` row. The vocabulary is one table across gates (D2).
- **Authorship is field-level.** An answer keeps the submitter's payload before certified fields were filled, the effective payload validated, and a source per field: `SUBMITTER`, `CONTROLLER_FILLED` or `SUBMITTER_CONFIRMED_BY_CONTROLLER`. An accepted Duck answer is never shown as wholly Duck-authored.
- **The journal is tamper-evident.** A truncated tail, a missing row, a duplicated sequence, an altered row, or a reopen under a different run are all detected. No wall-clock value enters hashed content.
- **The final model states its own provenance.** The v4 chapter has two parts:
  - **Integrity:** `SEALED`, `OPEN`, `CORRUPT` or `UNAVAILABLE`.
  - **Completeness:** `COMPLETE` requires all of the following:
    - a verified seal of this run;
    - exact admission-to-execution, execution-to-transition and evidence-receipt joins;
    - every admitted probe consumed once;
    - every product accounted for;
    - a clean gate-answer cross-check;
    - every interim prefix verified.

    Otherwise the chapter is `INCOMPLETE` with every reason listed. The validator recomputes all of it from the model, so a forged verdict fails.
- **Every product has an origin.**

  | Origin | Meaning |
  |---|---|
  | `ANSWER_CERTIFIED` | Joined to one exact admitted answer by gate, level and id, with directional containment of every semantic field |
  | `GATE_DERIVED` | Only six enumerated closures stated by the product's own payload, where no answer is expected |
  | `UNATTRIBUTED` | Anything else, with its reason. It always blocks `COMPLETE`. |

  - G1 and G2 products must equal the gate's retained law, model and mask, and derive from the retained answer.
  - G4-C's law test must equal the retained certified prediction.
  - Record-derived G4-B relations are rebuilt in full from their record, under a content-addressed id.
- **Joins are level-scoped.** A product joins only an admission from its own level. A later level never borrows an earlier admission.

### Epistemic limits (the honest ledger)

1. **`COMPLETE` means accounted for, not correct.** It says every piece of work joins its record. It says nothing about whether any proposition is true. That is the grader's job, against keys this seat does not write.
2. **`GATE_DERIVED` is accounting, not a finding.** A boundary or unresolved closure, or a counter search that found no counter, is provenance-complete as a closure record. PE-03 must emit these as closure or gap claims, never as learned laws or relations (Sol, E4).
3. **Record-derived relations are not Duck's.** `RELATIONS_CERTIFIED_FROM_RECORD` content is deterministic derivation from the record. The controller's admitted answer only triggers it. PE-03 must attribute it that way.
4. **Two gate derivations are restated, not imported:** the EgoLaw id, and the G4-B record transformation and id. Tests pin both to the real gates. A future gate change would surface as `UNATTRIBUTED`, never as a silent pass.
5. **The answer-shape registry fails closed.** Each of the 11 registered accepted-answer shapes names every field's rule. An unregistered gate or answer kind makes the cross-check `MISMATCH`. New gates need a registry entry before their runs can be `COMPLETE`.
6. **Life is not stored on products.** Same-id answers in different lives remain separate candidates and can only yield `AMBIGUOUS`.
7. **No provenance-complete live run exists yet.** Every `COMPLETE` so far is from the controller fixtures and offline worlds. The H2 cost figure is synthetic (k013, padded to 800 rows). The synthetic carry replay stays incomplete because its journal builder stamps the wrong level (accepted limitation S1); production reconciliation was not weakened for it.
8. **`world_report.md` still carries no provenance.** It is the semantic library report. `paper_evidence.json` and `paper_report.md` (D14) do not exist yet.
9. **Unchanged from v9:**
   - k013's G2 product has no mask law;
   - k008's ego identity is unresolved across lives;
   - dossier rows read `NOT_BUILT`;
   - the laws page shows stored evidence only.

## 5. Ruled ground for WO-PE-03 (recorded, not yet built)

From `RULINGS_PAPER_EVIDENCE_v1` D5-D14 and Sol's PE-02 rulings:

- **Claims:**
  - predicate families `ROLE`, `TRANSFORMATION`, `RELATION`, `LAW`, `PREDICTION`, `CONDITION`, `GAP`;
  - `claim_key` is the hash of the proposition, excluding evidence, status and executor;
  - `assertion_id` is the `claim_key` plus its provenance event;
  - mixed-status material is split;
  - executor `DUCK`, `CONTROLLER` or `SYSTEM`;
  - certification and admission are separate dimensions.
- **Keys:**
  - structured JSON, **authored independently by the Director**;
  - construction metadata;
  - source recording hashes;
  - required versus optional items;
  - accepted alternatives.
- **Joins:** exact first; `EXACT`, `COMPOSITE` and `UNMATCHED` mappings need human confirmation.
- **Grades:**

  | Grade | Meaning |
  |---|---|
  | `CORRECT` | The proposition agrees with the key. |
  | `WRONG` | The proposition contradicts the key. |
  | `UNVERIFIABLE` | The evidence or key cannot decide it. |
  | `MISSED` | A required key fact has no acceptable emitted claim. |
  | `INVENTED` | A positive emitted claim has no factual basis, after human review. |

  Propositions and audit statements are graded separately. Refused but interpretable proposals stay in the denominator.
- **Artifacts:** `world_report.md` stays as it is; the new artifacts are `paper_evidence.json` and `paper_report.md`.
- **Inputs PE-03 inherits from PE-02:**
  - product origins and bases;
  - the closure-not-finding rule;
  - record-derived attribution;
  - typed answer-payload references (kept for PE-03; non-blocking in PE-02, ruling E3).

## 6. Remaining gaps by priority

| Priority | Gap | Close condition |
|---|---|---|
| **P0 (red)** | No scored competition submission recorded | The Director's linked scored submission is recorded, with its notebook and score |
| P0 | No atomic claim projection | WO-PE-03 design reviewed; then a pure projection from the sealed v4 model, with fail-first tests |
| P0 | No answer keys | The key format is ratified in WO-PE-03; then the Director authors keys from play, committed and hash-frozen before any formal report is opened |
| P0 | No grader | The five-category grader joins and tabulates; humans confirm non-exact mappings and `INVENTED` verdicts |
| P0 | No provenance-complete live run | The first live run on `e158057` or later; integrity and completeness read from its v4 model |
| P0 | G4 has no per-lever dossier | WO-G4-DOSSIER-A/B |
| P1 | Nine NAV-side G1 stops and repair loops | WO-L1a-NAV / WO-NO-REPAIR-LOOPS |
| P1 | No current-source public-25 evidence | PUBLIC25-DESCRIPTION, run by the Director from a committed source after claims, keys and grader are committed |
| P1 | k013 mask law; k008 ego join | Diagnose first, in the G2 seat and in a census-identity slice |
| P2 | G5/G6, typed grammar, observed-win transfer, SUB-4 | As `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4` §1 |

Push and win-seeking frontier exploration stay shelved.

## 7. Execution order

1. **The Director makes and records the scored submission.** It runs in parallel and is blocked by nothing below.
2. **WO-PE-03, read-only design.** This seat covers the claim contract's projection map from v4, the key format, the join and grade procedure, and the artifact boundary. Sol rules.
3. **WO-PE-03 build**, as Sol slices it, each part with an interface and fail-first tests.
4. **GRADE-1:** the Director authors keys in the ratified format, frozen before any formal report is read.
5. **The first provenance-complete live run**, then PUBLIC25-DESCRIPTION.
6. **WO-G4-DOSSIER-A/B; WO-L1a-NAV / WO-NO-REPAIR-LOOPS** where files are disjoint.

**The calendar (ratified `DIRECTIVE_COMPETITION_ENDGAME_v3`):**
- interim submissions until 26 October;
- the freeze from 27 to 30 October;
- the paper by 8 November.

The scored submission is overdue against the plan's 12 October date.

## 8. Open questions for the receiving seat

1. **Director:** has a scored submission been made? If so, which notebook, which source commit, and what score?
2. **Sol:** WO-PE-03 is named as one slice covering claims, keys and grader. Should it be built as one work order, or as three (projection, key format and validator, grader), each with its own review?
3. **Director:** fast-forward `main` and push `ring9-unified` now that `e158057` has a Mac floor, or hold until PE-03?

## 9. Acceptance discipline (unchanged)

A slice closes only after:
- source review and fail-first evidence;
- the focused tests and the right tier, with T2 after acceptance;
- replay or live artifact evidence where it applies;
- a specific-path commit.

Golden updates need an explained semantic cause. No test may be weakened, removed, skipped, xfailed or hidden from the exact snapshot. **No seat authors the answer keys its own output will be graded against, and the model never grades itself.**

# State of the Duck build v9

**Date:** 2026-10-14
**Status:** current handoff record
**Supersedes:** `STATE_OF_THE_DUCK_BUILD_v8_2026-10-13.md`
**Governing plan:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v4_2026-10-12.md`, executed through `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4_2026-10-12.md`. The paper-evidence chain follows `BUILD_PLAN_PAPER_EVIDENCE_v1_2026-10-07.md` §2 and §4, as amended by the WO-PE-00 sweep.
**Author:** Claude (Alpha build seat)
**Scope:** game-free. This record states the solver's capability only; it names no world's contents.

**Grounding** (read directly on 2026-10-14):
- **Refs:** read with `git --git-dir` against the repository's own `.git`, read-only. No fetch was run.
- **Source content:** every `.py`, `.toml`, `.txt` and `.json` file under the runtime's `inference/`, `tools/`, `tests/` and `virelai_golden/` was compared by blob hash with `a925d7f`. All 300 matched.

## 1. Executive state

- **WO-DESC-B is accepted and committed at `a925d7f`.** Duck now reads the world as a few evidence-backed transformation statements, not as a raw event ledger. Every run that writes its canonical model also writes a deterministic semantic library report beside it.
- **The next critical slice is the paper-evidence layer:**
  1. executor provenance (which seat proposed a claim, and whether a gate admitted or refused it);
  2. an atomic, gradable claim contract;
  3. answer keys authored independently by the Director;
  4. a grader that joins and tabulates.

  WO-PE-00, the read-only prior-art sweep, is filed beside this record. Sol rules separately on provenance storage, the claim contract and the grader boundary.
- **The scored competition submission is still unrecorded. This item is red.** The Director is making it in parallel. It does not wait on the paper-evidence layer.
- **The formal current-source public-25 evidence run waits** until the claim interface, the grader and the independently authored keys are all committed.

## 2. Repository position (verified 2026-10-14)

| Item | State |
|---|---|
| Active runtime | `variants/ring9-cybernetic-gates/ARC3-Inference/` |
| Working branch | `ring9-unified`, at `a925d7f` (*Build evidence-backed semantic world description and report*, 2026-10-14). The worktree `HEAD` points at it. |
| Remote-tracking ref | `origin/ring9-unified` is `472aa32`, last updated 2026-10-11 and not re-fetched. `ring9-unified` is **14 commits ahead and 0 behind** it. Nothing has been pushed. |
| `main` / `origin/main` | Both at `472aa32`. `ring9-unified` is 14 ahead of `main`. Under the branch rule, `main` fast-forwards only after the Mac suite passes. |
| Working tree | Tracked files are clean. **16 untracked entries:**<ul><li>documentation drafts, including Sol's parallel sweep `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_SOL_v1_2026-10-14.md`;</li><li>three `kaggle/` package folders;</li><li>two `tools/` scripts;</li><li>the draft grammar modules (`physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `tests/test_physics_grammar_contract.py`).</li></ul>None of these is accepted runtime, and none is staged. (Corrected from 15 at Sol's review.) |
| Canonical artifact | `world_model.json`, schema `virelai-world-model-v3`, unchanged by DESC-B. v2 artifacts still read through `validate_v2`. |
| Semantic library report | `world_report.md`, written atomically after a successful canonical write |
| Scored competition submission | **None recorded. Red.** |

## 3. Floors (as accepted by the Director for `a925d7f`)

| Floor | Value |
|---|---|
| **T2, effective** | **925 passed, 1 skipped, of 926 collected.** The T2 run gave 923 passed and 1 skipped. Its 2 failures were sandbox-only: blocked `ps` access. A local rerun with process inspection passed all 24 test-runner checks. |
| T0 `desc-b` | 78 passed |
| T1 `description` | 204 passed |
| T1 `g3-directed` | 143 passed |
| `git diff --check` | clean |
| Archive | all 11 slice hashes matched |

The tier manifest is `tests/tiers/test_tiers.toml`, and the exact T2 snapshot is `tests/tiers/T2_collected.txt` (926 node ids).

**Capability chain since v8** (documentation-only commits omitted):

| Commit | Capability |
|---|---|
| `a925d7f` | **WO-DESC-B:** a semantic world description from the sealed v3 model, folding only with evidence; content ids; bounded pages and the digest floor; the deterministic `world_report.md` |

## 4. What WO-DESC-B built, and its epistemic limits

### Capabilities

- **Duck's ordinary digest shows transformation knowledge.** Within the one 2,500-character library section, it shows at least two transformation patterns and one world question. The question names its pattern id, and that pattern is shown. The selected gate question, the accounting status, any record mismatch and the open-identity count always survive. The general gap inventory shrinks first.
- **Duck can page the description.** The pages are `scene`, `events`, `transformations`, `dossiers`, `laws` and `residuals`, with six filters. Every continuation keeps its filters. A seventh retrieval handle, for transformations, is appended after the six accepted handles, whose order is unchanged.
- **Complementary events fold only with evidence.**
  - `OWNER_EXCHANGE`: a continuing event with no intrinsic cell, every exchanged cell paired with a primary continuing event.
  - `G2_MASK_REWRITE`: a certified mask law instantiated by both sides. This is the only path that folds a boundary birth or death.
  - Coverage alone never folds.
  - A residual census accounts for every verified event.
- **Ids are stable.** Pattern (`P-…`) and question (`Q-…`) ids are content hashes, so they survive a growing record. Rank is display only.
- **Every report claim carries resolvable references.** Each bullet and numbered claim in `world_report.md` ends in `refs:`. A reference is one of:
  - a stored id;
  - `manifest`;
  - a canonical JSON path;
  - a transition range scoped to its own level.

  A scene with no action reads `as of level entry` and cites the level entry. A scene after actions cites `t{entry+1}-t{N}`.
- **The report write is safe.** It is pure and deterministic, embeds the model's full content hash, refuses a live or unsealed model, and writes atomically. A failed report never touches the model and is recorded as `WORLD_REPORT_WRITE_FAILED`.

### Epistemic limits (the honest ledger)

1. **The report is not the graded C2 report.** `world_report.md` is the *semantic library report*. It has no executor provenance, so it cannot separate controller-certified, Duck-admitted and Duck-refused claims. It does not have the paper's fixed `self · time · response · players · model · value` shape, and it is not decomposed into claim-sized grading units. Nothing in it may be labelled controller-certified by default.
2. **The description is a projection, not new belief.** It adds no role, cause or evidence. Explanations are copied and counted, never promoted. A pattern reads EXPLAINED only when all its events are.
3. **Pattern sentences are multi-clause.** A pattern line tabulates a verb, its sites, action co-occurrence, explanation counts and a transition span. It is a display unit, not a grading unit.
4. **Dossier rows read `NOT_BUILT`** until WO-G4-DOSSIER-A.
5. **The laws page shows stored evidence only.** It shows the G2 mask receipt and the G1 note. Structured movement laws are absent from schema v3.
6. **Upstream facts limit what the description can explain:**
   - k013's G2 product has no mask law, so the counter's ticks stay UNEXPLAINED;
   - k008's ego identity is unresolved across lives, so ego moves stay UNEXPLAINED.

   These are gate questions, not description defects.
7. **The raw JSON scene page keeps `as_of_transition: null`** at level entry. That is structured data; prose surfaces never render `None`.

## 5. What WO-PE-00 found (summary; full document filed beside this one)

- **Accepted work is attributable on disk today.**
  - Accepted gate answers (`_gate_answers.jsonl`) and accepted probe envelopes (`_probe_envelopes.jsonl`) carry `executor`.
  - G3 choices carry `actor` with `ADMITTED` / `REFUSED` (`_g3_selection_events.jsonl`).
  - Executed gate events join to transitions through `evidence_id`.
- **Refused work is mostly not structured.**
  - A refused Duck gate answer, a refused Duck probe and a refused controller answer leave no structured record. They survive only as transcript prose, and only when Duck's own code printed the reply.
  - An accepted Duck answer row also mixes Duck-written fields with controller-filled certified fields, so field-level authorship is not recorded.
- **The canonical model records no provenance.** Neither the v3 model nor the report records who proposed anything.
- **Prior art exists for the evaluation discipline:**
  - the continuity-key grader (hash-frozen key, deterministic joins, false/missed links);
  - the v4 foundation grader (EXACT / COMPOSITE / UNMATCHED mapping; MATCH / MISS / NOT_GRADED / KEY_COVERAGE_GAP);
  - the v4 claim decomposer (code surfaces claims and leaves grade columns empty).

  No tool implements correct / wrong / unverifiable / missed / invented by executor.
- **Sol filed a parallel sweep the same day** (`PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_SOL_v1_2026-10-14.md`, untracked). It recommends a hybrid journal plus schema-v4 chapter. WO-PE-00 maps the options without choosing, as directed.

## 6. Remaining gaps by priority

| Priority | Gap | Close condition |
|---|---|---|
| **P0 (red)** | No scored competition submission | The Director's linked scored submission is recorded, with its notebook and score |
| P0 | No executor provenance or admission record in the canonical belief | Sol's rulings on storage, claim contract and grader boundary; then WO-PE-01 onward, with fail-first tests for every admission and refusal path |
| P0 | No atomic claim projection or grader | The claim contract is ratified; the projection is a pure read of the sealed model; `GRADE-2` joins and tabulates, and humans give semantic verdicts |
| P0 | No answer keys | `GRADE-1`: the Director writes structured keys from play, committed before any formal report is opened |
| P0 | G4 has no per-lever dossier | WO-G4-DOSSIER-A/B |
| P1 | Nine NAV-side G1 stops and repair loops | WO-L1a-NAV / WO-NO-REPAIR-LOOPS |
| P1 | No current-source public-25 evidence | PUBLIC25-DESCRIPTION, run by the Director from a committed source, after the claim interface, grader and keys are committed |
| P1 | k013 mask law; k008 ego join | Diagnose first, in the G2 seat and in a census-identity slice |
| P2 | G5/G6, typed grammar, observed-win transfer, SUB-4 | As `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4` §1 |

Push and win-seeking frontier exploration stay shelved.

## 7. Execution order

1. **The Director makes the scored submission** (parallel; not blocked by anything below).
2. **WO-PE-00 is filed** (this session). Sol rules on:
   - provenance storage;
   - the atomic claim contract;
   - the grader boundary.
3. **WO-PE-01 onward**, as Sol's rulings define them, each with an interface and fail-first tests.
4. **GRADE-1**: Director keys, committed before any formal report is read.
5. **GRADE-2**: the grader.
6. **PUBLIC25-DESCRIPTION**: only after 3-5 are committed.
7. **WO-G4-DOSSIER-A/B**; WO-L1a-NAV / WO-NO-REPAIR-LOOPS where files are disjoint.

**The calendar (ratified `DIRECTIVE_COMPETITION_ENDGAME_v3`):**
- interim submissions until 26 October;
- the freeze from 27 to 30 October;
- the paper by 8 November.

The scored submission is overdue against the plan's 12 October date.

## 8. Acceptance discipline (unchanged)

A slice closes only after:
- source review and fail-first evidence;
- the focused tests and the right tier, with T2 after acceptance;
- replay or live artifact evidence where it applies;
- a specific-path commit.

Golden updates need an explained semantic cause. No test may be weakened, removed, skipped, xfailed or hidden from the exact snapshot. No seat authors the answer keys its own output will be graded against, and the model never grades itself.

# WO-PE-00: prior art for paper evidence, provenance and grading

**Type:** `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING` · v1 · 2026-10-14 · a read-only sweep
**Author:** Claude (Alpha build seat)
**Reviewed source:** `ring9-unified` at `a925d7f`. The cloud copy matches the commit blob-for-blob across 300 files under `inference/`, `tools/`, `tests/` and `virelai_golden/`.

**Paths:**
- Unprefixed paths below are under `variants/ring9-cybernetic-gates/ARC3-Inference/`.
- `v4/` means the prior architecture at `virelai-review/virelai_v4/`.

**Saved runs read** (read-only, on the Director's machine):

| Label | Location | Source commit |
|---|---|---|
| k008, k013 | `duck-virelai-r9r20/runs/kaggle-ring9-submission-v2/output/` | `fc152e6`, 2026-10-09 |
| carry-v7 | `duck-virelai/runs/kaggle-ring9-carry-…-v7/output/` | `ec8554d`, 2026-10-03 |

**What this document does:**
- No production file was edited.
- No schema is chosen.
- No answer key is authored.
- Storage options, claim shapes and grader steps are **mapped, not decided**. Sol rules on them separately.

**How it was made:**
- **Code reading:** three read-only search agents swept the agent side, the framework side, and the tools and older generations.
- **Verification:** I re-read every load-bearing citation first-hand at the cited lines before writing it here.
- **Counts:** produced by read-only Python scripts run on the saved artifacts.
- **Heuristic counts:** a count that rests on parsing transcript prose says so where it appears.

---

## 1. Summary

1. **Accepted work is attributable on disk today, through three files:**
   - `_gate_answers.jsonl` (accepted answers, `executor`);
   - `_probe_envelopes.jsonl` (accepted probes, `executor`);
   - `_g3_selection_events.jsonl` (G3 choices, `actor`, `ADMITTED` / `REFUSED`).

   On all three saved runs, every executed gate event joins to its transition through `evidence_id`, and to its executor through `probe_id`, without ambiguity.
2. **Refused work is mostly not structured.**
   - A refused Duck gate answer, a refused Duck probe and a refused controller answer write no structured record.
   - The refused payload survives only as the Python source of Duck's tool call in the transcript.
   - The refusal reason survives only if Duck's own code printed the reply, or if the next prompt carried a contract-repair notice.
   - On carry-v7, at least 66 refusals are visible in transcript text against 46 accepted Duck answer rows. None is in a structured file.
3. **An accepted Duck answer is not purely Duck's.** `fill_certified_fields` fills controller-certified fields into Duck's submission before the gate validates it. The stored row cannot tell which fields Duck wrote.
4. **The canonical belief records no provenance.** The v3 model and `world_report.md` say nothing about who proposed what. Their receipts carry gate, product, evidence and witness ids, but no executor.
5. **Identity is uneven.**
   - Deterministic: `evidence_id`, the census `event_id`, and `P-` / `Q-` ids.
   - Not unique: `answer_id` (template defaults repeat across accepted rows), annotation `note_id` (restarts every level), the lifecycle `LC-` serial (restarts every level).
   - None: turn-ledger rows have no id.
6. **Prior art for evaluation exists; the thesis grader does not.**
   - The continuity-key grader: hash-frozen key, exact joins, false and missed links.
   - The v4 foundation grader: EXACT / COMPOSITE / UNMATCHED mapping; MATCH / MISS / NOT_GRADED / KEY_COVERAGE_GAP.
   - The v4 claim decomposer: code surfaces claims and leaves grade columns empty.
   - No tool implements correct / wrong / unverifiable / missed / invented by executor.
   - The planned `tools/compile_world_report.py` and `tools/grade_world_report.py` (`BUILD_PLAN_PAPER_EVIDENCE_v1` §2, §4) were never built.
7. **Duck's falsifiable predictions are already graded by the record, in one place.** On carry-v7, all 24 accepted G4-B and G4-C predictions join by `prediction_id` to gate events that graded them: 22 CONTRADICTED, 1 INDETERMINATE, 1 SUPPORTED.

---

## 2. Source inventory

### 2.1 Agent-side run artifacts

All of these live in `job_dir/artifacts/{stem}_…`, where `stem` = `{game}_p{pass}`. Every writer opens the file in append mode, writes, and closes per call, unless noted.

| Artifact | Writer | Row content relevant here |
|---|---|---|
| `_probe_envelopes.jsonl` | `ToolAgent._gate_probe_begin`, `inference/agent/tool_agent.py:2327-2362` (write at 2349-2360); Duck call at :2503, controller call at `inference/agent/controller_turn.py:216` | <ul><li>`executor` (DUCK / CONTROLLER)</li><li>`probe_id`, `gate_id`, purpose, question, actions, `declared_at_transition`</li><li>`target`, `intent` (Duck free text, ≤240 chars), `pilot_intent`</li><li>Written **after** `validate_probe` succeeds (:2346). A refused probe raises (:2347-2348) and writes nothing.</li></ul> |
| `_gate_events.jsonl`, `_probe_outcomes.jsonl`, `_probe_frames.jsonl` | `record_probe_outcome`, `inference/agent/gate_artifacts.py:66-128` | <ul><li>Gate event: `evidence_id` (deterministic: `E-` + sha256 of probe and outcome), `gate_id`, `probe_id`, per-gate extras. **No `executor`.**</li><li>Probe outcome: `transition_id`, `boundary_event`, changed cells.</li><li>Written in sequence: event, then (for G3) a ledger rewrite, then outcome, then frames.</li></ul> |
| `_gate_answers.jsonl` | `record_gate_answer`, `gate_artifacts.py:132-175` | <ul><li>`gate_id`, `executor` (default `"DUCK"`, :134; the controller passes CONTROLLER at `controller_turn.py:190`), plus the validated answer body.</li><li>Accepted answers only. The body is the answer **after** `fill_certified_fields` (`inference/framework/card_builder.py:160-186`, called from `virelai_gates.py:6890-6895`).</li><li>No level field. A transition anchor appears only on prediction rows (`declared_at_transition`; `Prediction`, `g4_relations.py:162-178`) and inside G1 and G2 `pending_prediction` (`gate_artifacts.py:146-162`).</li></ul> |
| `_g3_selection_events.jsonl` | `g3_selection.note`, `inference/framework/g3_selection.py:93-102`; `select` at :105-133; flush at `gate_artifacts.py:52-63` | <ul><li>`event` ∈ ADMITTED / REFUSED (:121, :132), FINISHED (:208), STALE (:221, :231), HANDOFF (:253), COVERAGE_RESUMED (:261)</li><li>`question_id`, `entity_id`, `actor`, `reason`, `phase`, `level`, `life`, `at_transition`, `gate_revision`</li><li>The only structured ADMITTED / REFUSED record in the tree.</li></ul> |
| `_turn_ledger.jsonl` | `TurnLedger`, `inference/agent/turn_ledger.py:37-89` | <ul><li>`executor`, `analysis_step`, `action_num`, `gate_before` / `gate_after`, `outcome`, token use, `recall_queries`</li><li>No claim content, no evidence, no row id.</li></ul> |
| `_annotations.jsonl` | `record_notes`, `inference/agent/memory_queries.py:136-143`; lane at `inference/framework/annotation_lane.py` | <ul><li>`label` = UNCERTIFIED, `kind` ∈ NAME / HUNCH / PROPOSAL (:21), subject, text (≤60 words), `after_transition`, `source`</li><li>`note_id` = `N####` per level lane (:101). The lane is rebuilt each level (`virelai_gates.py:6553`).</li></ul> |
| `_g3_target_ledger.json` | `_write_g3_target_ledger`, `gate_artifacts.py:18-33` | The current G3 roster. A whole-file `write_text`: non-atomic and not append-only. |
| `_g3_run_outcome.json` and `_history.jsonl` | `record_g3_run_outcome`, `gate_artifacts.py:209-348` | A controller-state product (G3_COMPLETE, G3_BUDGET_STOPPED, and so on), atomic replace. No executor. |
| Transcript `transcripts/{stem}.txt` | `tool_agent.py:686-693` | <ul><li>Prose sections: TOOL CALL (Duck's Python source), TOOL RESULT (Duck's printed output), CONTROLLER log lines.</li><li>The only place rejected answers and controller refusals appear (`tool_agent.py:2635-2663`; `controller_turn.py:184-189`).</li></ul> |

**Writers outside gated mode** (`tool_agent.py:1299-1300`: "controller and gated modes are mutually exclusive"):
- `_decision_envelopes.jsonl`, using `virelai_controller.py:119-163`: `PredictionSpec`, `FocusProposal`, `DecisionEnvelope`, `DecisionReceipt`, `OutcomeComparison`.
- `virelai_experiments.evaluate`, `inference/framework/virelai_experiments.py:55-88`: SUPPORTED, CONTRADICTED, UNRESOLVED, NOT_EVALUATED, NOT_ATTEMPTED.

These are schema priors, not current evidence.

### 2.2 Framework and canonical belief

| Source | Location | Provenance content |
|---|---|---|
| `TargetJournal` | `inference/framework/cybernetic_targeting.py:110-166`; `MemoryProduct` at :42 | <ul><li>Active products and a STALE history.</li><li>`snapshot()` (:160) has no production caller.</li><li>A new journal is built every level (`virelai_gates.py:6557`), so history is dropped at each level.</li><li>No actor field. The exception is G4-B's `certified_by` in its payload.</li></ul> |
| G3 lifecycle journal | `inference/framework/lever_lifecycle.py` | <ul><li>`event_id` (`LC-#####`, per level), `entity_id`, from/to state, `evidence_ref`, `actor`, `reason`.</li><li>The reachability transition hardcodes `actor="DUCK"` (`virelai_gates.py:4507-4512`), yet the controller can submit that answer when `semantic_reuse` holds (`controller_executor.py:427-431`).</li><li>It reaches disk only inside the G3 product payload and the G3 outcome file.</li></ul> |
| Census receipts (schema v3) | `inference/framework/library_census.py:232-266` | <ul><li>`evidence[id]` = {transition_id, gate_id, probe_id}</li><li>`products[id]` = {gate_id, product_type, revision, payload_sha256, mask?}</li><li>`witnesses[id]` = {…, evidence_ref, transition_id, …}</li><li>**No executor or admission field.**</li></ul> |
| Manifest | `library_census.py:789-799` | `status`, `persist_reason`, `actions_executed`, `gate_machine`, `journal_check`, `census_failures` |
| Transition record in the description | `inference/framework/descriptive_events.py:304-308` | `"actor"` = `gate_id` or `kind`, which is the gate or RESET, **not** controller vs Duck. Its source rows (`inference/framework/memory_store.py:30-79`) carry no executor. |
| Legacy v1 `Claim` | `inference/framework/virelai_world_model.py:20-39` (`EvidenceRef`, `Claim`); statuses at :11 | <ul><li>`claim_id`, `predicate`, `status` (OBSERVED / INFERRED / CANDIDATE / CONTRADICTED / SUPERSEDED / UNKNOWN), `scope`, witness and contradiction counts, `evidence`, `limitations`.</li><li>No actor.</li><li>Written to disk only with `VIRELAI_LEGACY_WORLD_MODEL_FILE=1`.</li></ul> |
| G4-B relations answer | `inference/framework/g4_relations.py`: `Prediction` :162, `grade` :232, `RelationsAnswer` :301 | <ul><li>**The only place Duck must submit pre-split claims.** Each relation carries `claim` plus `prediction_refs`, and each cited prediction must be SUPPORTED.</li><li>Predictions are graded per lever key, with `missed` keys listed.</li></ul> |
| World report | `inference/framework/world_report.py` | Every claim line ends in resolvable `refs:`. Line 8 states it has no executor provenance. |

### 2.3 Evaluation tools and keys

| Prior | Location | What carries over |
|---|---|---|
| Continuity-key grader | `tools/grade_continuity_key.py:13-32` (provenance check), :87 (prediction), :106-107 (false and missed links), :113 (pass rule) | <ul><li>Refuses a key whose recording hash differs.</li><li>An exact join on the key tuple (`step_before`, `node_before`, `step_after`, `node_after`) against replay STITCH events (:75-86); per-row expected vs produced.</li><li>False-link and missed-link counts; a machine-readable report; a failing exit status.</li></ul> |
| Real continuity key | `virelai-review/win-lab/fixtures/continuity-v1/real_recording_key.json` | Fields: `schema`, `frozen_on`, a `construction` statement ("labels were made from literal source component observations before inspecting detailed continuity-shadow answers"), `archives` (hashes) and `judgments`. **A precedent for key preregistration metadata.** |
| Synthetic keys | `tests/fixtures/continuity/fixture_key.json:3,19` (`"synthetic-key"`; "a separately frozen real-recording key is still required"); `tests/fixtures/clock/fixture_key.json:3` (`frozen_before_detector_run: true`) | Freeze-before-run flags |
| Checkpoint evaluators | `tools/evaluate_gated_checkpoint.py`, `tools/evaluate_g2_counter_checkpoint.py` | <ul><li>Automatic PASS / FAIL / REVIEW_REQUIRED.</li><li>A human review signed against the run receipt's sha256.</li><li>Answers graded field by field; answer `evidence_refs` must resolve to gate events.</li></ul> |
| v4 foundation grader | `v4/diagnostics/foundation_grade.py:1-51` (doctrine and verdicts), :118-133 (mapping), :205-243 (grading) | <ul><li>The key is external; "the solver never sees the key".</li><li>Grain differences are handled by EXACT / COMPOSITE / UNMATCHED mapping before grading.</li><li>The asymmetry rule: a key *untested* fact against a solver *witnessed* fact is `KEY_COVERAGE_GAP`, not a solver miss; a key UNKNOWN is `NOT_GRADED`.</li></ul> |
| v4 axiom overlay | `v4/diagnostics/dossier.py:574-604` (`load_axiom_key`, `grade_axioms`) | Categorical MATCH / DIVERGE per row against an external key; an absent key renders `NOT_GRADED (no axiom key)`. |
| v4 claim decomposer | `v4/weave/claim_decomposer.py:1-25` (doctrine), :142 (`_EMPTY_GRADE`), :177-204 (audit sheet) | "The code SURFACES claims, never grades them." Every claim carries empty FIDELITY / CORRECTNESS columns. It is a pure read. |
| `tools/record_from_artifacts.py:27-50` | `DUCK_FIELDS` per gate | A **static** list of fields Duck writes per answer type. The nearest existing statement of field-level authorship, but by schema, not by row. |

**Searched, not found:** no `answer_key` / `keys/` tree; no UNVERIFIABLE / INVENTED enum; no free-text claim decomposer in Ring 9. No admission or refusal provenance exists in rings 1-7, 11, 25 or ring-ontology.

---

## 3. Availability matrix

**Legend:** **Y** = recorded structurally · **P** = partial (see note) · **T** = transcript prose only · **N** = not recorded.

"Persistence" lists the stop paths the record survives:
- *end* = normal end
- *budget* = budget stop
- *stop* = controlled stop
- *crash* = an exception in the play loop

| Source | Controller-certified | Duck proposals | Duck accepted | Duck refused | Atomic content | Evidence refs | Gate / level / transition / subject | Persistence | Deterministic join id |
|---|---|---|---|---|---|---|---|---|---|
| `_gate_answers.jsonl` | Y (CONTROLLER) | P¹ | Y | N | P² | P³ | gate; a transition only on predictions; no level | all four⁴ | **N** (`answer_id` repeats⁵); `prediction_id` Y |
| `_probe_envelopes.jsonl` | Y | P (accepted probes only) | Y | N | P (actions, intent ≤240 chars) | N | gate, declared transition, target | all four | `probe_id`, which repeats⁶ |
| `_gate_events.jsonl` + `_probe_outcomes.jsonl` | Y (via envelope) | N | executed only | N | outcome | Y | gate; transition and level via outcome | all four⁷ | `evidence_id` Y |
| `_g3_selection_events.jsonl` | HANDOFF / COVERAGE_RESUMED | Y (G3 choices) | Y (ADMITTED) | Y (REFUSED)⁸ | `question_id` only | N | Y | not guaranteed⁹ | `question_id` Y; row: none |
| `_turn_ledger.jsonl` | executor | per turn | N | `controller_refused` only | N | N | gate, `action_num` | end, budget, stop; crash only in the Duck path¹⁰ | none |
| `_annotations.jsonl` | N | Y (UNCERTIFIED notes) | n/a (never admitted) | N | free text | N | subject, after_transition | all four | `note_id` per level (repeats) |
| Transcript | log lines | T | T | T (if printed) | T (Python source) | T | T | all four (append) | none |
| `TargetJournal` | Y | N | G4-B `certified_by` only | N | payload | some | gate, revision | **memory only** | product_id |
| G3 lifecycle | Y | reachability only | P | N | reason | Y | entity | inside the G3 product | `LC-` serial per level |
| Census receipts, model v3 | Y (gate products) | N | N | N | `payload_sha256` only | Y | Y | written by H1 interim; H2 at end / budget / stop / crash¹¹ | evidence / product / witness / event ids Y |
| `world_report.md` | not marked | N | N | N | multi-clause lines | Y (`refs:`) | Y | after a successful model write | `P-` / `Q-` / ids Y |

**Notes:**
1. Only proposals that were **accepted** are rows.
2. The stored body is the post-fill answer (`card_builder.py:160-186`), so Duck-written and controller-filled fields are merged. Multi-field answers (mechanism, conditions, falsifier, …) are not single propositions.
3. These are mixed namespaces. Evidence ids, product ids and entity ids all appear in `evidence_refs`. Predictions have `evidence_ref: null` at acceptance; the verdict arrives in a later gate event.
4. Appended per accepted answer, so it survives every stop path that occurs after the write.
5. Observed collisions: `G1-EGO-EXPLANATION-1` ×3 (k008), ×2 (k013); `G0-CONTROLLER` ×3, `G1-1` ×3 and `G2-COUNTER-EXPLANATION-1` ×3 (carry-v7). G3's `answer_id` may be chosen by the submitter (`virelai_gates.py:4614`).
6. Repeated probe ids: 1 id across 3 rows (k008); 1 across 2 (k013); 39 across 102 (carry-v7). On these three runs no repeated id carries two executors, so the probe-id join is unambiguous **here**, not by construction.
7. If `record_probe_outcome` raises mid-sequence, the later files miss that event (`gate_artifacts.py:104-125`).
8. A refusal raised before `note` is not recorded: a non-G3 gate raises at `virelai_gates.py:6733-6736` before `select`.
9. Flushed only at three call sites (`gate_artifacts.py:102`, `controller_turn.py:66`, `memory_queries.py:84`). `solver.py`'s final `finally` (:649-658) never flushes, so events noted after the last flush are lost.
10. A controller action that raises after `_gate_probe_begin` writes no ledger row (`controller_turn.py:204-251`). The Duck ledger row is written in a `finally` block, but its `outcome` does not carry the fatal reason.
11. `solver.py:649-655`: the final write runs in `finally`, so a crash in the play loop still writes with `persist_reason` CRASH (:350-363). An exception **before** the `try` (`seed_initial_history` … :576-580) skips the `finally`: no model and no report.

### 3.1 Stop, crash, reset and level-boundary paths

| Path | What is written | What is lost |
|---|---|---|
| **Normal end / budget / controlled stop that ends the run** | Sidecars appended per event. `_record_open_g3_outcome` (`solver.py:653`); H2 model and report (:655); runtime summary (:656). | Unflushed selection events (note 9). The `TargetJournal` history. Refusal payloads. |
| **Controlled stop that rests and resumes play** | No sidecar or model write. A CONTROLLER transcript section and `rest_in_play` (`solver.py:723-724`). | n/a |
| **Crash in the play loop** | The `except` at :643-648 marks the run `crashed` only if `final_score` is unset and the state is `playing`; otherwise another reason applies (:350-363). The `finally` still writes, unless `_record_open_g3_outcome` (:653) raises, which skips the H2 write at :655. | The interim write for the failing turn. Anything after the raising call in `record_probe_outcome`. |
| **Exception before the `try`** (:576-580) | Nothing | Model, report and summary |
| **Hard process kill** | Only what was already appended | Everything held in memory, including the census since the last H1 write |
| **Reset** | An in-memory RESET row in the transition index (`virelai_gates.py:6850-6858`) | No sidecar row records the reset |
| **Level boundary** | H1 freezes the census into `level_censuses`; an interim model write follows if `analyze` returned normally (`solver.py:622`) | Annotation lane and `TargetJournal` are rebuilt per level (`virelai_gates.py:6549-6560`). The lifecycle journal restarts through a new `_LeverTarget` (`virelai_gates.py:6564-6568`), which builds a new `LifecycleJournal` (`virelai_gates.py:3144`; serial from 0 at `lever_lifecycle.py:80`). So note and LC ids restart. |

---

## 4. Historical counts on saved records

**Premise.** k008 and k013 come from commit `fc152e6` (2026-10-09). `git merge-base` confirms it is an ancestor of `db8a657`, the commit that added the G3 selection-event writer. carry-v7 comes from `ec8554d` (2026-10-03); the ancestry check failed with a VM bus error, but its date also predates `db8a657`. **None of the three records can contain selection events,** and k008 and k013 predate the annotation journal in use. No `world_model.json` exists for any of them: schema v3 postdates them.

**Method:** read-only scripts over `_gate_answers`, `_probe_envelopes`, `_gate_events`, `_probe_outcomes`, `_turn_ledger`, `_annotations` and the transcript of each run.

### Accepted and refused work

| Measure | k008 | k013 | carry-v7 |
|---|---|---|---|
| **Controller-certified answers** (accepted, `executor` CONTROLLER) | 3 (G0 1, G2 2) | 1 (G0) | 38 (G0 3, G1 3, G2 3, G3 16, G4.1 13) |
| Controller-executed gate actions (envelope → event) | 54 | 373 | 163 |
| **Duck-admitted answers** (accepted, `executor` DUCK) | 3 (G1) | 2 (G1) | 46: 11 G4.2 orbit observations, 11 G4-B relations, 13 G4-B predictions, 11 G4-C law predictions |
| Duck-executed gate actions | 5 | 23 | 1 |
| Duck predictions graded by the record (`prediction_id` → gate event) | — | — | 24 of 24: **22 CONTRADICTED, 1 INDETERMINATE, 1 SUPPORTED** |
| G3 choices ADMITTED / REFUSED | none (writer postdates the run) | none | none |
| **Duck-refused answers, structured** | 0 | 0 | 0 |
| Duck-refused answers, visible in transcript tool results* | 2 | 0 | ≥66 (G4-B 58, G4-C 7, G4-A 1) |
| Controller answer refusals logged | 0 | 0 | 0 |
| Duck probe refusals | **unmeasurable**: no record | unmeasurable | unmeasurable |
| UNCERTIFIED notes | file absent | file absent | 10 (NAME 3, HUNCH 4, PROPOSAL 3) |

### Content lost and records that cannot be joined

| Measure | k008 | k013 | carry-v7 |
|---|---|---|---|
| **Proposals whose structured content is lost**: refused answers whose payload exists only as Duck's Python source | 2 | 0 | ≥66 |
| `gate_answer` calls whose result is not visible at all* | 0 | 2 | 0 |
| **Unjoinable**: accepted answers with no level field (level only by file order) | 6 of 6 | 3 of 3 | 84 of 84 |
| Unjoinable: accepted answers with no transition anchor of any kind | 1 (G0) | 1 (G0) | 57 (all but 24 predictions and 3 G2 rows with `pending_prediction`) |
| Unjoinable: accepted answers with no evidence reference of any kind | 1 (G0) | 1 (G0) | 3 (G0); plus 24 predictions with `evidence_ref: null` until graded |
| Unjoinable: answer `evidence_refs` that name no gate event (product or entity ids) | 0 | 0 | 16 |
| Unjoinable: `answer_id` rows beyond the first use of an id | 3 | 1 | 6 |
| Envelopes with no executed event (orphans) | 1 | 1 | 0 |
| Turn-ledger rows with no row id (joinable only by `action_num`) | 72 | 412 | 312 |
| **Joinable**: gate events → transition via `evidence_id` | 59 / 59 | 396 / 396 | 164 / 164 |
| Joinable: gate events → executor via `probe_id` (ambiguous rows) | 59 (0) | 396 (0) | 164 (0) |

\* **Heuristic counts.** A Duck tool call is counted when its Python source mentions `gate_answer`. A refusal is counted when its printed result contains the gate's correction text ("Correct the named field") or "answer rejected". These are lower bounds: a reply that Duck's code did not print is invisible. One Python call can submit more than once, which is why carry-v7's 111 such calls exceed accepted plus visible refusals. k008 also shows 1 "GATE CONTRACT REPAIR" prompt for one of its two refusals.

**What the counts say:**
1. **The controller-vs-Duck split is real and recoverable for accepted work** on all three records.
2. **Refusals cannot be counted exactly from today's artifacts.** On carry-v7 they likely outnumber Duck's accepted answers, so an admission rate computed only from structured files would be badly biased.
3. **The record already grades Duck's G4 predictions,** and mostly falsifies them. That is the strongest existing "proposed, then judged by the frame" evidence, and it lives in gate events, not in the canonical model.

---

## 5. Storage options (mapped, not chosen)

| Criterion | **A.** Schema-v4 provenance chapter inside `world_model.json` | **B.** Separate append-only provenance record, referenced and hashed by the canonical model | **C.** Reconstruct during report compilation from existing logs |
|---|---|---|---|
| **One canonical belief artifact** | **Yes.** Provenance lives in the sealed model and is validated with it. | **Partly.** The model stays canonical for belief, but report claims about who proposed what depend on a second file. The hash makes a substitution detectable, not harmless. | **No.** The report would rest on loose logs and prose. |
| **Crash and early-stop survival** | Only as of the last canonical write: H1 interim or H2 final. A play-loop crash still writes through the `finally`. A hard kill, or an exception before the `try`, loses everything since the last write. | **Best.** An appended row survives anything after its write. The canonical copy then has the same limits as A. | Depends on today's sidecars. Refusals are absent regardless. |
| **Deterministic replay** | Yes, if the rows derive from gate state and recorded decisions. Model hash equality from identical records is testable. | Yes, if the record is deterministic: it would need deterministic row ids and no wall-clock fields inside the hashed content. | No for refusals (prose); partial for accepted work. |
| **Report traceability** | Every executor and admission claim resolves inside the sealed model, by the same `refs:` rule DESC-B enforces. | Resolves into the side record. The report's resolver must open and verify a second file. | Weak: proposals and refusals would cite transcript offsets or nothing. |
| **Formal-run packaging** | One file per game, already packaged. | Two files per game that must travel together. The packet must verify the hash. | Packaging must include transcripts and every sidecar. Large (carry-v7's transcript is about 7.9 MB). |
| **Can a missing side artifact silently change a report?** | No. | Not silently, if the model stores the record's hash and the renderer refuses a missing or mismatched record. Silently, if it does not. | **Yes.** A missing or truncated log silently lowers counts. |

**What each option needs that does not exist yet:**
- **All three** need refusal recording at the call sites in §3 (`tool_agent.py:2635-2663`, `controller_turn.py:184-189`, `tool_agent.py:2346-2348`, `controller_turn.py:220-224`, the note path `annotation_lane.py:75-104`, and the G3 path that raises before `note`). Otherwise the denominator stays wrong whatever the storage.
- **A** also needs a version bump (v4), a v3 reader, and a decision on how much refusal payload to keep in the canonical file. The size and the census write cost must be measured.
- **B** also needs a stable row-id rule, an end-of-run flush or close (the gap in note 9 is the same failure class), and a hash stamp inside the model.
- **C** cannot recover what was never written: refusal payloads, unprinted replies, probe refusals.

**Combinations.** A and B are not exclusive. Sol's parallel sweep recommends B for capture and A for canonicality: append immediately, then absorb and hash at H1 and H2. Its properties follow from the A and B columns above. The choice is Sol's.

---

## 6. Candidate atomic claim shapes

**A gradable claim is one proposition.** Candidate fields, with the sources that could fill them today:

| Field | Meaning | Existing source handles |
|---|---|---|
| `claim_id` | Stable id | Candidates in §7, D6 |
| `subject` | One entity, track, role, pattern, level or action | track id; role `entity_id`; `P-` id; `LEVEL-n`; action name |
| `predicate` | One relation or transformation, from a closed family | See below |
| `object` / `value` | One value | class, delta, rewrite pair, state, role name, law id |
| `scope` | Level, life, transition range, action, condition | DESC-B level-scoped ranges; `by_action`; the G4 `conditions` / `missing_condition` |
| `epistemic_status` | e.g. OBSERVED, CERTIFIED, EXPLAINED / PARTLY_EXPLAINED / UNEXPLAINED, PREDICTED (pending), SUPPORTED / CONTRADICTED, OPEN (declared unknown) | DESC-A explanation statuses; G4 prediction statuses; typed gaps |
| `executor` | CONTROLLER / DUCK, plus a candidate SYSTEM for resets | envelope and answer `executor`; selection `actor`; runtime actor SYSTEM_RESET |
| `admission` | ADMITTED / REFUSED / NOT_APPLICABLE (a controller observation) / UNCERTIFIED (a note) | selection events; accepted-answer rows; refusals (to be recorded) |
| `evidence` | Refs resolvable in the canonical artifact | DESC-B `refs:` grammar |

**Candidate predicate families, with where each could come from:**
- **ROLE:** a certified role binding.
- **TRANSFORMS:** one subject, one verb, one site rewrite, under one action. This is a DESC-B pattern *split*, not the pattern sentence.
- **LAW:** the G2 mask (cells and rewrite).
- **PREDICTS:** G4-B and G4-C predictions, one lever key per claim, each with its graded status.
- **RELATION:** a G4-B relation claim, already per relation, citing predictions.
- **CONDITION:** a missing or open condition.
- **GAP:** a declared unknown, per typed gap.
- **WIN_CONDITION:** reserved for C3.

**What does not count as one unit:**
- **A DESC-B pattern sentence.** It bundles a subject, a verb, a site set, an action co-occurrence table, explanation counts and a span. Example shape: "subject X: SHRINK ×42; sites a>b; on ACTION1: −2 ×8, −3 ×3; on ACTION2: …; basis ×42; t1-t44". Decomposed, it yields one TRANSFORMS claim per (subject, verb, rewrite, action, delta). The explanation counts become status fields of those claims, and the span becomes scope.
- **A G1 or G2 answer.** Its `mechanism`, `action_laws[i]`, `conditions[j]`, `falsifier` and `novel_prediction` are each a separate candidate claim. `tools/evaluate_gated_checkpoint.py` already grades them field by field.
- **A pattern that mixes explanation statuses** (for example, NOT_COVERED ×217 with G3_WITNESS_RESIDUE ×6). The family either splits by status or carries counts. That is a design decision (D7).

**Field-level authorship (an open problem).** For an accepted Duck answer, which fields did Duck write? The candidates:
- a per-row diff of Duck's raw submission against the filled answer, which requires recording the raw submission;
- the static per-schema `DUCK_FIELDS` list (`tools/record_from_artifacts.py:27-50`).

Only the first is evidence.

---

## 7. Grader map

**The thesis categories are kept exactly:** correct / wrong / unverifiable / missed / invented, tabulated by executor and admission (`THESIS_v1_2026-10-05.md` C2; `REPORT_TO_PAPER_ADVISOR_…_v1` §10.4).

| Step | Who | Prior art |
|---|---|---|
| 1. Verify the hashes of the key and the run (model, report, recordings) | code | `grade_continuity_key.py:13-32`; the evaluators' receipt-sha check |
| 2. Enumerate the emitted atomic claims from the sealed model (pure read) | code | DESC-B view validator (recompute and equality); the v4 decomposer doctrine |
| 3. Exact join: key item ↔ claim on identical structured tuples or ids | code | the continuity grader's exact tuple join |
| 4. Grain mapping where key and solver individuate differently | code proposes; a human confirms | v4 `map_foundation` EXACT / COMPOSITE / UNMATCHED (`foundation_grade.py:118-133`) |
| 5. Semantic verdict where the join does not settle it | **human** (non-author; at least one game blind) | v4 empty FIDELITY / CORRECTNESS columns; the evaluators' signed human review |
| 6. MISSED: required key items with no acceptable claim | code, from the joins plus human verdicts | `virelai_missed_links`; `g4_relations.grade` `missed` |
| 7. INVENTED: candidate claims with no key basis, ruled by a human | code lists; **human** rules | `virelai_false_links` |
| 8. UNVERIFIABLE: candidates are key-untested items and declared unknowns | **human**, under a pre-stated rule | v4 `KEY_COVERAGE_GAP` / `NOT_GRADED` asymmetry |
| 9. Tabulate by game × level × claim family × executor × admission; refusals and unknowns counted in the denominator | code | the evaluators' summary blocks |
| 10. Enforce sheet completeness and a failing exit status | code | `grade_continuity_key.py:113` (pass rule), `:119` (exit status) |

**Boundaries carried from prior doctrine:**
- **The model never grades itself.** The key is never visible to the solver (`foundation_grade.py:10-12`; `dossier.py:575-576`).
- **The code surfaces and joins; it does not rule semantics** (`claim_decomposer.py:17-20`).
- **Keys carry their construction provenance and freeze date** (the real continuity key's `construction` and `frozen_on`).

**Open category questions** (for Sol; these are not decided here):
1. Is a REFUSED Duck claim graded at all?
   - Graded, it measures proposal quality.
   - Excluded, it is counted only for the admission rate.
2. Is a declared GAP graded correct or wrong against the key? Is an insufficiently specific gap its own category?
3. Is a contradicted Duck prediction a *correct* report line? The report states the contradiction truthfully, while the proposition itself was wrong.

---

## 8. Proposed interface decision table (for Sol's rulings)

| # | Decision | Options mapped | What the sweep shows | Altitude / owner |
|---|---|---|---|---|
| D1 | Provenance storage | A (schema-v4 chapter), B (hashed append-only record), C (reconstruct), A+B | C cannot recover refusals (§4). A alone loses everything since the last write on a hard kill. B alone splits authority unless the model stamps the record's hash. | architecture / Sol |
| D2 | Event vocabulary | Reuse G3's (ADMITTED / REFUSED / HANDOFF / …), or one vocabulary across gates (PROPOSED / ADMITTED / REFUSED / EXECUTED / ANSWER_ACCEPTED / ANSWER_REFUSED / …) | Only G3 has a structured vocabulary today. Answers and probes have none for refusals. | architecture / Sol |
| D3 | Interception points | <ul><li>Duck probe: `tool_agent.py:2340-2348`</li><li>controller probe: `controller_turn.py:215-224`</li><li>Duck answer: `tool_agent.py:2622-2663`</li><li>controller answer: `controller_turn.py:179-190`</li><li>G3 choice: `g3_selection.py:105-133` and `virelai_gates.py:6733-6736`</li><li>notes: `annotation_lane.py:75-104`</li></ul> | These are the six places admission is decided. On refusal:<ul><li>Duck probe, Duck answer, controller answer and notes record nothing structured.</li><li>A controller probe writes only a ledger `outcome` of `controller_refused`, with no reason (`controller_turn.py:220-224`).</li><li>G3 records REFUSED, except on the non-G3-gate path.</li></ul> | code / AC, once D1-D2 are ruled |
| D4 | Field-level authorship of accepted Duck answers | Record the raw submission beside the filled answer; record a diff; or declare per-schema authorship | `fill_certified_fields` merges the two today. | architecture / Sol |
| D5 | Claim unit and predicate families | §6 families; how DESC-B patterns and multi-field answers split | Pattern sentences and G1/G2 answers are multi-proposition. | architecture / Sol |
| D6 | `claim_id` formula | Hash of the semantic tuple without evidence (stable as evidence grows); with scope; or with level only | `P-` / `Q-` ids already exclude counts. `answer_id` and `note_id` are not unique. | architecture / Sol |
| D7 | Epistemic status enum and mixed-status claims | Split claims by status, or keep counts on one claim | Patterns mix statuses (k013 counter shrink: 217 NOT_COVERED, 6 G3_WITNESS_RESIDUE). | architecture / Sol |
| D8 | Executor / admission enums | {CONTROLLER, DUCK, SYSTEM} × {ADMITTED, REFUSED, NOT_APPLICABLE, UNCERTIFIED} | SYSTEM_RESET already exists as a runtime actor. The lifecycle `actor` field holds component names (for example `G3_ROUTER`, `NAV_TERRAIN_MAP`), not an executor enum, and it hardcodes DUCK on a controller-capable path. | architecture / Sol |
| D9 | Key format and authorship | Structured, the same tuple as claims; with `construction`, `frozen_on` and recording hashes; required vs optional items; accepted alternatives | Prior art in the real continuity key. **Authored by the Director, not by this seat.** | plan / Director |
| D10 | Join strategy | Exact tuple; id; grain mapping (EXACT / COMPOSITE / UNMATCHED) with human confirmation | Key and solver individuation differ (v4 doctrine). | architecture / Sol |
| D11 | Category definitions | §7 open questions 1-3 | No existing tool defines them. | plan-level wording (thesis C2) / Apex, via the Director; operational rules / Sol |
| D12 | Historical runs | Grade only new runs; or partially reconstruct accepted work from old runs | Old runs lack refusals and selection events (§4). | plan / Director |
| D13 | Compatibility | The v3 reader stays; a v4 reader is added; the report renders "no provenance" for v3 | `read_world_model` already dispatches v1, v2 and v3 (`world_model_v2.py:286-302`). | architecture / Sol |
| D14 | Report shape | Keep the DESC-B semantic library report and add the paper report (self · time · response · players · model · value), or extend one renderer | `THESIS_v1` requires the fixed six sections and three line kinds. | architecture / Sol, against the thesis |

---

## 9. Code-level defects found during the sweep (routed, not fixed)

These are code-level, belong in whichever WO-PE slice touches the same files, and need fail-first tests:

1. **No end-of-run flush of `g3_selection_events`.** `solver.py:649-658` lacks one, so the last events can be lost.
2. **The lifecycle hardcodes `actor="DUCK"`** for the reachability transition (`virelai_gates.py:4507-4512`), although the controller can submit that answer (`controller_executor.py:427-431`).
3. **A controller action that raises after `_gate_probe_begin` writes no turn-ledger row** (`controller_turn.py:204-251`). Duck ledger rows omit the fatal reason.
4. **An exception before the `try`** in `play` (`solver.py:576-580`) writes no model and no report.
5. **`answer_id` is not unique** across accepted rows (§3, note 5). It must not serve as a join key.
6. **Annotation `note_id` and lifecycle `LC-` ids restart every level.** A join needs the level.
7. **`_g3_target_ledger.json` is written non-atomically** (`gate_artifacts.py:25-32`).
8. **`evidence_refs` mixes namespaces** (evidence, product and entity ids). 16 unresolved against gate events on carry-v7.

---

## 10. Cross-check with Sol's parallel sweep

Sol's sweep is `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_SOL_v1_2026-10-14.md`: untracked, in the worktree root, read 2026-10-14.

**Agreements:**
- Accepted work is attributable; refusals are lost.
- The canonical model is the right destination for claims.
- The continuity grader and the claim-decomposer doctrine are the right priors.
- The thesis grader is unbuilt.
- The model must not grade itself; keys are not authored by the implementation seat.

**Differences and additions:**
- **Probe-id ambiguity.** Sol notes that repeated probe ids make the probe-id join unreliable in principle. On the three records counted here, no repeated id carries two executors, so the join is unambiguous in practice. The principle stands, and the point is not settled by construction.
- **Additions in this sweep:**
  - the merged-authorship effect of `fill_certified_fields`;
  - `answer_id` collisions;
  - the transcript lower bound on refusals (≥66 on carry-v7);
  - the record-graded Duck predictions (22 / 1 / 1);
  - the v4 foundation grader's mapping and asymmetry rules;
  - the real continuity key's construction metadata;
  - the defects in §9.
- **Figures not re-verified here:**
  - Sol's figure of 24 selection events in the `db8a657` public-25 diagnostic;
  - "nine v2 games wrote annotation journals".
- **Storage.** Sol recommends A+B. This document maps the options and does not choose (directive item 5).

---

## 11. Source register

**Governing:**
- `THESIS_v1_2026-10-05.md`
- `BUILD_PLAN_PAPER_EVIDENCE_v1_2026-10-07.md` §2, §4
- `REPORT_TO_PAPER_ADVISOR_LIBRARY_CENTRIC_WORLD_DESCRIPTION_v1_2026-10-13.md` §10
- `DIRECTIVE_COMPETITION_ENDGAME_v3_2026-10-05.md`

**Code, at `a925d7f`:**
- `inference/agent/`: `gate_artifacts.py`, `tool_agent.py`, `controller_turn.py`, `turn_ledger.py`, `memory_queries.py`, `scientist_note.py`
- `inference/framework/`: `g3_selection.py`, `annotation_lane.py`, `card_builder.py`, `virelai_gates.py`, `cybernetic_targeting.py`, `lever_lifecycle.py`, `library_census.py`, `descriptive_events.py`, `memory_store.py`, `virelai_world_model.py`, `g4_relations.py`, `virelai_experiments.py`, `virelai_controller.py`, `world_model_v2.py`, `world_report.py`, `solver.py`
- `tools/`: `grade_continuity_key.py`, `evaluate_gated_checkpoint.py`, `evaluate_g2_counter_checkpoint.py`, `record_from_artifacts.py`
- `tests/fixtures/`: `continuity/fixture_key.json`, `clock/fixture_key.json`

**Prior generations:**
- `virelai_v4/weave/claim_decomposer.py`
- `virelai_v4/diagnostics/foundation_grade.py`
- `virelai_v4/diagnostics/dossier.py`
- `win-lab/fixtures/continuity-v1/real_recording_key.json`

**Saved runs:**
- `duck-virelai-r9r20/runs/kaggle-ring9-submission-v2/output/` (k008, k013)
- `duck-virelai/runs/kaggle-ring9-carry-…-v7/output/` (carry-v7)

**Parallel review:** `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_SOL_v1_2026-10-14.md`

— Claude, Alpha build seat, 2026-10-14

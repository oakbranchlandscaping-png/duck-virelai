# Sol prior-art sweep: paper evidence, provenance and grading

**Type:** read-only architecture review
**Date:** 2026-10-14
**Reviewed source:** `ring9-unified` at `a925d7f`
**Scope:** executor provenance, Duck proposals and refusals, atomic claims, answer keys, graders, continuity and report persistence. No production file was changed.

## 1. Director summary

The repository already contains most of the *shapes* needed for the paper-evidence layer, but they live in separate generations and do not yet form one end-to-end contract.

The strongest reusable pieces are:

1. Ring 9's canonical, sealed `world_model.json`, its receipt validation and its deterministic `world_report.md` renderer.
2. Ring 9's live gate artifacts, which already record the executor on accepted probe envelopes and accepted gate answers.
3. The G3 selection journal, which already records Duck choices as `ADMITTED` or `REFUSED`, with the question, subject, reason, level, life and transition boundary.
4. The older decision-controller schemas for prospective predictions, focus proposals, decision receipts and scoped outcome comparisons.
5. Ring 7's claim decomposer, whose central rule is still right: code surfaces bounded claims and evidence; a human grades semantic correctness.
6. The continuity-key grader, which already proves the right evaluation discipline: frozen source hashes, deterministic joins, explicit false-link and missed-link counts, a machine-readable report and a failing exit status.

The important missing link is **durable provenance at the gate boundary**. Accepted actions and answers are attributable today, but the gate machine's canonical transition row drops `executor`. Most rejected answers and actions are not written as structured records. They survive only as transcript text or a coarse turn result. A report compiler cannot reconstruct that losslessly after the fact.

My recommendation is a hybrid that preserves one canonical belief artifact:

- append every proposal, admission, refusal and execution decision immediately to one crash-safe provenance journal;
- at H1/H2, validate and copy the relevant entries into a versioned provenance chapter in `world_model.json`;
- hash the source journal and store that hash in the canonical model;
- render and grade from the canonical model, never directly from loose logs.

This uses an append-only file for crash survival and schema v4 for canonicality. It avoids making a sidecar file a second semantic authority.

## 2. What production Ring 9 already records

### 2.1 Accepted probe actions

`ToolAgent._gate_probe_begin` validates the action before the environment moves, then writes a probe envelope with `executor`, the exact gate/probe identity, purpose, action, target and declaration boundary:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/tool_agent.py:2327-2360`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/controller_turn.py:203-225`

This is the right interception point. Duck and controller actions use the same path and differ only by the executor label.

The resulting gate event receives a stable `evidence_id` and is written beside the lossless probe outcome and before/after frames:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/gate_artifacts.py:66-128`

**Reusable:** exact pre-action validation, executor enum, action binding, stable probe/evidence ids, append-only artifacts.

**Gap:** the gate event itself does not carry `executor`, and the canonical transition row drops it. `transition_index_row` currently stores transition, gate, probe, evidence, action, site, changes, boundary and attribution only:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/memory_store.py:30-79`

On the saved k008 and k013 rehearsal artifacts, joining gate events to envelopes by `probe_id` alone is not total: one demonstration probe id repeats three times in k008 and twice in k013. The join becomes reliable only when declaration/transition position is also used. Provenance should therefore be copied into the transition row when the action is admitted, not inferred later from `probe_id` alone.

### 2.2 Accepted gate answers

`record_gate_answer` writes accepted answers with `gate_id` and `executor`, and retains the validated answer body:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/gate_artifacts.py:132-175`

The rehearsal demonstrates that this distinction is real. In k008, accepted answers split 3 controller / 3 Duck; in k013, 1 controller / 2 Duck.

**Reusable:** accepted answer provenance and exact validated payload.

**Gap:** the canonical census reads the gate products but does not preserve who proposed or submitted the accepted answer. Consequently the schema-v3 report correctly says it has no executor provenance.

### 2.3 G3 choice admission and refusal

G3 has the best current provenance contract. A selection event records:

- event: `HANDOFF`, `ADMITTED`, `REFUSED`, `COVERAGE_RESUMED`, `STALE` or `FINISHED`;
- question id and entity id;
- actor and reason;
- phase, level, life, transition boundary and gate revision.

Sources:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/g3_selection.py:93-133`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/g3_selection.py:244-261`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/gate_artifacts.py:52-63`

The db8a657 public-25 diagnostic contains 24 such events: 11 handoffs, 9 coverage resumptions, 2 admissions and 2 finishes. This is already enough to calculate a narrowly defined G3 choice-admission rate.

**Reusable:** event vocabulary, actor, explicit structural reason, transition boundary, subject and question binding.

**Gap:** this contract exists only for G3 target selection. It does not cover rejected gate answers, rejected gate actions, G4 explanations or general Duck propositions.

### 2.4 Turn ledger

The turn ledger records executor, gate before/after, whether an action executed, outcome, time, model usage and recall calls:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/turn_ledger.py:37-89`

It is valuable for model-cost and runtime analysis. In the saved v2 records, k008 contains 54 controller turns and 18 Duck turns; k013 contains 373 controller turns and 39 Duck turns.

**Reusable:** denominator for Duck calls, action execution and runtime friction.

**Limit:** it records the turn's outcome, not the exact rejected proposal. `controller_refused` or `contract_repair_loop` cannot be graded semantically without the submitted payload and refusal reason.

### 2.5 Duck's uncertified language

The annotation lane already makes the correct epistemic distinction. It accepts `NAME`, `HUNCH` and `PROPOSAL`, labels them `UNCERTIFIED`, scopes them to a known subject and transition boundary, and never lets a gate read or promote them:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/annotation_lane.py:1-25`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/annotation_lane.py:33-57`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/annotation_lane.py:75-119`

Nine v2 games wrote annotation journals.

**Reusable:** the epistemic boundary and explicit subject binding.

**Limit:** free prose notes are useful appendices, not atomic paper claims. They should not be forced through a string-matching grader.

## 3. What is currently lost

### 3.1 Rejected gate answers

Duck's `gate_answer` is checked in `tool_agent.py:2622-2669`. On rejection, the code returns the reason and starts the repair guard, but it does not append the submitted answer and rejection to a structured provenance file. The transcript contains them, but transcript parsing is neither canonical nor robust.

Controller answer refusals are similarly written only to the analyzer log and an in-memory refusal set:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/controller_turn.py:179-190`

### 3.2 Rejected gate actions

The probe envelope is written only after `validate_probe` succeeds (`tool_agent.py:2343-2360`). A rejected Duck action therefore leaves no structured envelope. A refused controller action produces a turn-ledger outcome and transcript message, but the rejected action, active token and reason are not held together in one durable record (`controller_turn.py:215-224`).

### 3.3 General Duck proposals

There are three partial systems, none connected end to end in gated production:

1. UNCERTIFIED annotation prose.
2. `virelai('intent')`, which binds an open question, exact next action, prediction and optional scope, then grades the next Duck transition `SUPPORTED`, `CONTRADICTED`, `UNRESOLVED`, `NOT_ATTEMPTED` or `NOT_EVALUATED`:
   - `inference/framework/virelai_experiments.py:4-88`
   - `inference/framework/virelai_runtime.py:762-769`
   - `inference/framework/virelai_runtime.py:1226-1244`
3. The older decision controller's `PredictionSpec`, `FocusProposal`, `DecisionEnvelope`, `DecisionReceipt` and `OutcomeComparison`:
   - `inference/framework/virelai_controller.py:105-163`
   - `inference/framework/virelai_controller.py:282-373`

The current tool agent explicitly makes decision-controller mode and gated mode mutually exclusive:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/agent/tool_agent.py:1295-1302`

No `experiments.jsonl` or `decision_envelopes.jsonl` was found in the saved runs inspected. These are code priors, not current evidence.

## 4. Canonical model and report: the correct destination

Schema v3 is already the single, validated belief artifact. It separates observation tracks from certified roles, carries typed gaps, indexes receipts, seals the full content and rejects invented or mismatched references:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_model_v2.py:1-25`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_model_v2.py:37-45`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_model_v2.py:83-127`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_model_v2.py:239-281`

The report is deterministic, names the model by its full content hash, requires every rendered claim line to end in resolvable references, refuses an unsealed/live model and writes atomically:

- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_report.py:1-14`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_report.py:39-55`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_report.py:183-207`
- `variants/ring9-cybernetic-gates/ARC3-Inference/inference/framework/world_report.py:224-237`

This should remain the paper report's source. A grading tool should consume structured claims derived from this sealed artifact, not scrape Markdown.

## 5. Prior claim decomposition

Ring 7's claim decomposer is narrower than the current semantic library—it emits fork and identity claims—but its evaluation boundary should be ported unchanged:

- code surfaces the claim and factual measurements;
- code leaves semantic fidelity/correctness to a human;
- the claim compiler is a pure read and writes no belief;
- the audit sheet renders an empty grade field.

Sources:

- `variants/ring7/ARC3-Inference/virelai_v4/weave/claim_decomposer.py:1-25`
- `variants/ring7/ARC3-Inference/virelai_v4/weave/claim_decomposer.py:43-57`
- `variants/ring7/ARC3-Inference/virelai_v4/weave/claim_decomposer.py:134-204`

**Port the discipline, not the two claim shapes.** Schema v3 has better subjects, transformations, roles, products, gaps and receipts.

## 6. Prior grading machinery

The continuity grader is the strongest direct code prior:

- refuses to grade a key against recordings whose `frames.bin` hash differs;
- joins each keyed judgment to a deterministic replay event;
- records expected and predicted values per item;
- separates false links from missed links;
- emits one machine-readable report;
- exits nonzero if the declared acceptance rule fails.

Source:

- `variants/ring9-cybernetic-gates/ARC3-Inference/tools/grade_continuity_key.py:13-32`
- `variants/ring9-cybernetic-gates/ARC3-Inference/tools/grade_continuity_key.py:35-119`

The synthetic continuity key also records the critical limitation: a separately frozen real-recording key is required before accuracy claims or model exposure:

- `variants/ring9-cybernetic-gates/ARC3-Inference/tests/fixtures/continuity/fixture_key.json:1-20`

No existing tool implements the thesis rubric `correct / wrong / unverifiable / missed / invented` by executor. `GRADE-2` remains genuinely unbuilt.

## 7. Recommended provenance architecture

### 7.1 Runtime journal

Add one append-only journal written at the same boundaries that currently admit/refuse work. A record should include:

- stable provenance event id;
- event kind: `PROPOSED`, `ADMITTED`, `REFUSED`, `EXECUTED`, `ANSWER_ACCEPTED`, `ANSWER_REFUSED`, `SUPERSEDED`, `NOT_ATTEMPTED`;
- executor: `DUCK`, `CONTROLLER` or `SYSTEM`;
- gate, level, life and transition boundary;
- question id, subject id and probe/answer id where applicable;
- canonical submitted payload or its content hash plus the atomic semantic fields;
- structural reason;
- evidence id and executed transition when one exists.

The record must be written before execution for an admission and immediately on refusal. A refusal consumes no transition and therefore cannot be represented only as a transition receipt.

### 7.2 Canonical schema v4

At level freeze and run end, the census should absorb the journal entries into a `provenance` chapter and store the journal's SHA-256. Validation should prove:

- every execution resolves to one admitted proposal and one recorded transition;
- every accepted answer resolves to one gate product or explicitly pending product;
- every refusal has no executed transition;
- every Duck-attributed claim resolves to a Duck proposal/answer record;
- every controller claim resolves to deterministic gate state and receipts;
- ids are unique and level scoped;
- entries after the first journal mismatch are typed gaps, never silently omitted.

This gives the report one canonical source while retaining crash-surviving append-only evidence.

### 7.3 Why the two simpler options lose

| Option | Failure |
|---|---|
| Schema v4 only, written at H1/H2 | A hard process kill can lose proposals/refusals since the last canonical write. |
| Sidecar journal only | The report depends on a second artifact that can be missing, mismatched or replaced; the belief artifact is no longer self-contained. |
| Reconstruct from current logs | Rejected payloads are already missing; repeated probe ids make a probe-id-only join ambiguous; transcripts are prose. |

## 8. Recommended atomic claim unit

The grading unit should be structured and single-predicate:

```text
claim_id
game_id, level
subject = stable role/entity/track/pattern key
predicate = ROLE | TRANSFORMS | LAW | CONDITION | RELATION | GAP | WIN_CONDITION
object_or_value
scope = transition(s), action, state condition, life/level
epistemic_status = OBSERVED | CERTIFIED | PARTLY_EXPLAINED | OPEN | REFUSED
executor = CONTROLLER | DUCK | SYSTEM
admission = ADMITTED | REFUSED | NOT_APPLICABLE
refs = canonical model ids/paths/transition ranges
```

A line containing several predicates becomes several claims even if the human report renders them together. `claim_id` should be a deterministic digest of the semantic tuple, excluding evidence growth, so the same claim keeps its identity when more receipts accumulate.

Do not use report prose as identity. DESC-B's pattern ids and question ids are good source handles, but grading keys should address the structured semantic tuple.

## 9. Recommended key and grader boundary

### Director key

The Director should write a structured key before opening formal run reports. Markdown may render it, but the authoritative payload should be machine-readable. Each expected item needs:

- stable key id;
- game and level;
- the same atomic semantic tuple used by claims;
- whether it is required or optional;
- the observation/play basis used by the Director;
- declared ambiguity or alternative acceptable renderings.

The commit hash plus each source recording hash is the preregistration stamp.

### Deterministic grader work

Code may:

- validate the key and report/model hashes;
- enumerate emitted atomic claims;
- join exact ids and exact structured tuples;
- prepare unmatched key items and unmatched report items;
- tabulate human verdicts by game, level, claim kind, executor and admission;
- count refusals and declared unknowns;
- enforce completeness of the grade sheet.

### Human work

A human assigns semantic `CORRECT`, `WRONG` or `UNVERIFIABLE` when exact tuple matching does not settle correctness. `MISSED` is a required key item with no acceptable emitted claim. `INVENTED` is an admitted positive report claim that the key/human says has no basis. A declared gap is not invented; it can be correct, wrong or insufficiently specific.

The model that generated the claim never grades it.

## 10. Build order implied by the sweep

1. **WO-PE-01 provenance journal:** production-shaped append-only records for accepted and rejected gate actions/answers; reuse G3 event vocabulary and decision-controller dataclasses where they fit.
2. **WO-PE-02 schema v4:** absorb and validate provenance in the canonical model; expose executor/admission in the description view.
3. **WO-PE-03 claim projection:** pure structured atomic claims from sealed schema v4; Markdown report renders them but is not parsed by grading.
4. **GRADE-1:** Director commits all 25 keys without reading formal reports.
5. **GRADE-2:** deterministic packet builder plus human verdict sheet, following the continuity grader's provenance and exit discipline.
6. **PUBLIC25-DESCRIPTION:** only then run and download the formal current-source 25-world evidence sample.

The scored competition submission remains independent and overdue; none of these slices should delay it.

## 11. Instructions for the implementation design

Before editing production code, the interface author should produce:

1. an event matrix showing which current call site emits each provenance event;
2. fail-first cases for Duck/controller accepted action, refused action, accepted answer, refused answer, G3 admitted/refused choice, timeout/no choice, reset, level boundary, controlled stop and crash;
3. a demonstrated join from proposal → admission/refusal → execution → evidence → atomic claim;
4. counts on k008, k013 and carry-v7, including records that cannot be reconstructed under today's artifacts;
5. a schema-v3 compatibility rule and proof that old models still read;
6. a performance budget that keeps provenance recording off the expensive census path.

No answer key should be authored by the implementation seat, and no formal save-run report should be opened before the Director's keys are committed.

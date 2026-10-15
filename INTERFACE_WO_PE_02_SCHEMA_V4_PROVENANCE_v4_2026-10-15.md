# Interface: WO-PE-02, the schema-v4 provenance chapter

**Version:** v4, 2026-10-15. It supersedes v3 in full; v1-v3 stay in place as history. v4 is v3 with Sol's
revision-2 review (`REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v2_2026-10-15`) built in. Passages amended for revision 3 are
marked **[v4]**; **[v3]** marks revision-2 amendments; everything unmarked is unchanged from v2.
**Author:** Claude (Alpha build seat)
**Base:** `ring9-unified` at **`afe93c8`**. Confirmed in two places:
- the cloud tree matches 317 of 317 blobs;
- the Director's worktree is at `afe93c8` on `ring9-unified`, and the six files this slice touches hash identically there.

**Governing:**
- Sol's rulings 1-9 and semantic corrections on the sweep (2026-10-14);
- `RULINGS_PAPER_EVIDENCE_v1_2026-10-14` D1;
- `INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v3_2026-10-14`;
- **[v3]** `REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v1_2026-10-15`: F1 (product origins), F2 (directional containment),
  F3 (strict hashing), and the acceptances (ratchet residual, E3, S1);
- **[v4]** `REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v2_2026-10-15`: E4 ruled (all six closures kept), F4 (record-derived
  relations rebuilt in full), the multi-level proof, and the retained-state guards.

**Out of scope:**
- gates and action selection;
- `world_report.md` rendering and Duck's digest and pages;
- claims, keys, grading and the grader;
- the existing `journal_check` names and behaviour, which are H2's *record* check and are unchanged.

---

## 1. Rulings as built

| # | Ruling | Contract |
|---|---|---|
| 1 | Option A | The validated journal rows are embedded **once**, in the top-level `provenance` chapter. Each level carries only a `provenance_index` of event ids. |
| 2 | Live states | H1 and `LIVE_VIEW` use `integrity: NOT_EVALUATED`. **Neither reads the journal file.** |
| 3 | H1 prefix | H1 may carry `writer_reported: {label: WRITER_REPORTED, event_count, head_hash}` from the writer's memory. It has no evidentiary authority. H2 verifies every such prefix recorded earlier in the same session (`interim_prefixes`). |
| 4 | Ambiguity | An ambiguous product-to-answer match (`AMBIGUOUS_PRODUCT_ANSWER`) blocks `COMPLETE`. |
| 5 | Crash runs | A handled crash may be `COMPLETE` when every rule passes. It is labelled `completeness_scope: THROUGH_RECORDED_TERMINATION` and keeps `persist_reason: CRASH`. |
| 6 | Gate-answer cross-check | Kept (§5.7). The k-th admitted ANSWER row must match the k-th `_gate_answers.jsonl` line on gate, executor, `answer_id` and the normalized payload. A mismatch blocks `COMPLETE`. |
| 7 | Pre-`play` crashes | `_play_one` records `WORLD_MODEL_NOT_WRITTEN` where observer context exists and no model was written. The run-roster checker reports `MODEL_MISSING` either way. |
| 8 | Schema bump | Every compile path writes v4: H1, H2 and `LIVE_VIEW`. v1, v2 and v3 keep frozen validation and reading. |
| 9 | Typed references | Typed, scoped references live **only in the chapter**. Role `evidence_refs` are not rewritten. |
| R2-F1 **[v3]** | Product origins | Missing attribution stays blocking. Every product has an `origin`: `ANSWER_CERTIFIED` (needs one exact admitted answer per stored reference), `GATE_DERIVED` (only the enumerated closures of §2.1), or `UNATTRIBUTED` (always blocks). There is no switch. |
| R2-F2 **[v3]** | Exact payload joins | Directional normalized containment (§2.2): every semantic field stored for an answer must be present in the journal's effective answer with the same strict hash. Never "whatever fields overlap". |
| R2-F3 **[v3]** | Strict hashing | Canonical JSON with no `default=` and no NaN. A non-JSON value is a typed failure (`NON_JSON_ANSWER_FIELD` on a product), never a stringified match. |

## 2. What schema v4 adds to a level (census, `library_census.compile_level`)

The census stays a pure, read-only projection of gate state. It adds two fields that reconciliation needs. Neither appears on any Duck-facing page, and the digest is byte-identical (test 22).

| Field | Content | Why |
|---|---|---|
| `record.reset_transition_ids` | The level's transition ids whose row is `kind: RESET` | Transitions without evidence are acceptable **only** when typed as harness resets (rule R4). Without this field the chapter would need the gate machine. |
| `product_answers` **[v3]** | For each active product: `{gate_id, product_type, origin, basis, link, answers: [{answer_id, shape, clauses, omitted}]}` | Product-to-answer reconciliation (R6). The product payloads of frozen levels exist only at the H1 freeze, since the target journal is rebuilt per level, so the references must be taken there. |

### 2.1 **[v3]** Product origins (`product_origins.py`, the census-time provenance adapter)

The adapter reads gate state and never calls a gate method. Every product type the gates emit is enumerated; any
other type is `UNATTRIBUTED / UNREGISTERED_PRODUCT_TYPE`.

| Product | `ANSWER_CERTIFIED` when | basis | `GATE_DERIVED` only when the payload states | Otherwise `UNATTRIBUTED` |
|---|---|---|---|---|
| G0 `ActionSurface` | the payload is the answer (`answer_id == product_id`) | `PRODUCT_IS_ANSWER` | — | `ANSWER_DOES_NOT_DERIVE_PRODUCT` |
| G1 `EgoLaw` | the gate retains `ego.answer`; **[v4]** the whole payload equals the retained `ego.ego_law`; and `law_id == "EL-" + sha256("G1-EGO\|" + answer_id)[:16]` (the id derivation `ego_verification` uses) | `EGO_LAW_DERIVED_FROM_ANSWER` | — | `NO_RETAINED_ANSWER`, `PRODUCT_DIFFERS_FROM_RETAINED_STATE` **[v4]**, `ANSWER_DOES_NOT_DERIVE_PRODUCT` |
| G2 `CounterGateProduct` | `COUNTER_MODEL_AND_MASK`, the gate retains `counter.answer`; **[v4]** `counter_model` and `mask_law` equal the retained `counter.counter_model` and `counter.mask_law` (a mask must be retained); and the counter model's `candidate_id` and the nine fields it copies from the answer are equal | `COUNTER_MODEL_COPIES_ANSWER` | `COUNTER_NOT_OBSERVED` with `counter_model: null` and a non-empty `search_disposition` → `COUNTER_NOT_OBSERVED` | `NO_RETAINED_ANSWER`, `PRODUCT_DIFFERS_FROM_RETAINED_STATE` **[v4]**, `ANSWER_DOES_NOT_DERIVE_PRODUCT`, `NO_DECLARED_CLOSURE` |
| G3 `LeverInventory` | `payload.answer.answer_id == product_id` | `PAYLOAD_ANSWER` | — | `NO_RETAINED_ANSWER`, `ANSWER_DOES_NOT_DERIVE_PRODUCT` |
| G4 `LeverEffectAnatomySet` | `payload.answers` non-empty | `PAYLOAD_ANSWERS` | — | `NO_RETAINED_ANSWER` |
| G4.2 `LeverOrbitSet` | `payload.answers` non-empty | `PAYLOAD_ANSWERS` | no answers, `phase1_status: CLOSED_BY_LEVEL_BOUNDARY` with a `level_boundary` → `ORBITS_CLOSED_BY_LEVEL_BOUNDARY` | `NO_DECLARED_CLOSURE` |
| G4-B `LeverRelationSet` | `status: COMPLETE` with an answer. **[v4]** A record-certified answer (`LEVER_RELATIONS_FROM_RECORD`) must equal, field for field under strict canonical JSON, the `RelationsAnswer` that `g4b_gate._certify_from_record`'s fixed transformation builds from `payload.from_record`, and the record's `answer_id` must be its content hash (`record_relations`' seed over the relations' levers, claims and transitions and the description) | `PAYLOAD_ANSWER`, `RELATIONS_CERTIFIED_FROM_RECORD` | no answer, `CLOSED_BY_LEVEL_BOUNDARY` with a `level_boundary`, or `UNRESOLVED` with an `unresolved_reason` → `RELATIONS_CLOSED_BY_LEVEL_BOUNDARY`, `RELATIONS_UNRESOLVED` | `NO_DECLARED_CLOSURE`, `ANSWER_DOES_NOT_DERIVE_PRODUCT` |
| G4-C `LeverReactionLawSet` | `status: COMPLETE`, and `payload.law_test` equals the gate's retained `_certified` prediction | `LAW_TEST_IS_CERTIFIED_PREDICTION` | no `law_test`, `CLOSED_BY_LEVEL_BOUNDARY` with a `level_boundary`, or `UNRESOLVED` with an `unresolved_reason` → `LAW_CLOSED_BY_LEVEL_BOUNDARY`, `LAW_UNRESOLVED` | `NO_RETAINED_ANSWER`, `ANSWER_DOES_NOT_DERIVE_PRODUCT`, `NO_DECLARED_CLOSURE` |

All of these are census-time comparisons of payloads and retained attributes; the adapter calls no gate method and
changes no gate state. **[v4]** The record reconstruction and the record id derivation are restated in
`product_origins` (`record_relations_answer`, `record_answer_id`) rather than imported, since the gate inlines them;
a test pins both to the real gate's record certification.

**[v4] Meaning of `GATE_DERIVED`** (Sol, E4): the product's provenance is accounted for; it is not a positive semantic
finding. PE-03 must emit these as closure or gap claims, never as learned laws or relations. Likewise
`RELATIONS_CERTIFIED_FROM_RECORD` attributes the relations' content to deterministic record derivation, with the
controller's admitted answer as the trigger, never to a Duck assertion.

A certified answer that cannot be projected (§2.2) makes the product `UNATTRIBUTED` with `UNREGISTERED_ANSWER_SHAPE`,
`ANSWER_SHAPE_MISMATCH` or `NON_JSON_ANSWER_FIELD`. `link` records where the answer was read: `PRODUCT_ID`,
`PAYLOAD_ANSWER`, `PAYLOAD_ANSWERS`, `GATE_STATE` or `NONE`. No gate code changed, so no second shared-file note was
needed.

### 2.2 **[v3]** Answer shapes and directional containment (`answer_shapes.py`, pure)

Each accepted-answer dataclass has a **shape**: every one of its fields is named with exactly one rule. The shape is
chosen by gate, and for G3, G4-B and G4-C by `answer_kind`. A test pins each shape's field set to its dataclass.

| Rule | Meaning | Examples |
|---|---|---|
| `COPIED` | compared with the same field of the effective payload | most fields |
| `COPIED` with a declared default | absent from the effective payload **only** when the accepted value equals the default | G1 `conditions: []`, `novel_prediction: {}`, `action_law_specs: {}`; G2 `trigger: "UNSPECIFIED"`; prediction `elsewhere: "NO_CHANGE"` |
| renamed | compared with a named submitted field (first present, in order) | G3 `mechanism` ← `explanation` / `mechanism`; reachability `conditions` ← `reopen_conditions`; inventory `constraints` ← `limitations` |
| `SINGLETON` | the accepted one-item list holds the named submitted value | reachability `constraints`, `limitations` ← `[epistemic_limit]` |
| `FLATTENED` | each key of the accepted mapping is compared with the same top-level submitted field | inventory `novel_prediction` → `lever_entities`, `clean_null_entities`, `ambiguous_entities` |
| `EXPECTATION` | `validate_prediction`'s rule: each named lever's submitted outcome, stripped and upper-cased, is the accepted one; every other lever is `UNCHANGED` | prediction `expected` |
| `ANSWER_ID` | the join key, compared as the row's `refs.answer_id` | `answer_id`; `prediction_id` |
| `GENERATED`, `DERIVED`, `OUTCOME` | computed by the gate at acceptance, derived from compared fields, or written later by grading; **named, not compared** | `target_member_id` (G4); G3 `action_laws`, `subjects`, inventory `answer_kind`; prediction `status`, `observed`, `evidence_ref` |

A stored reference is `{answer_id, shape, clauses, omitted}`: one clause per compared field, with its effective keys,
its strict hash, whether absence is allowed, and (for `EXPECTATION`) the accepted map; `omitted` names every field not
compared, with its rule. A record whose fields are not exactly its shape's set is refused (`ANSWER_SHAPE_MISMATCH`), so a
truncated or padded record cannot be projected at all.

**Measured, not assumed:** every one of the 1,045 answers accepted across T1 `g3-directed`, `paper-evidence` and
`description` (11 shapes across the 8 gates that took answers in the survey) projects, and is contained in its own effective payload.

**Field hashes [v3].** `sha16(v)` is the first 16 hex characters of the sha256 of `json.dumps(v, sort_keys=True,
separators=(",", ":"), ensure_ascii=True, allow_nan=False)`. There is no `default=`; tuples hash as the lists JSON
already makes of them.

## 3. The chapter

### 3.1 By phase

| Phase | Written by | Reads the journal file? | `integrity` | `completeness` | Rows |
|---|---|---|---|---|---|
| `LIVE_VIEW` | `library_view.live_model` (default) | **no** | `NOT_EVALUATED` | `NOT_EVALUATED` | none |
| `H1` | the interim write after a level freeze (`solver.py:426`) | **no**; memory only | `NOT_EVALUATED` | `PENDING` | none; `writer_reported` optional |
| `H2` | the final write (`solver.py:656`) | **once**, after the seal | `SEALED`, `OPEN`, `CORRUPT` or `UNAVAILABLE` | `COMPLETE` or `INCOMPLETE` | the reader's verified prefix, exactly |

**When no chapter is supplied,** `seal()` attaches a default:
- `LIVE_VIEW` gives the `LIVE_VIEW` chapter;
- `LEVEL_ADVANCE` gives H1 with `capture: UNKNOWN`;
- a final reason gives H2 `UNAVAILABLE` with `unavailable_reason: JOURNAL_NOT_SUPPLIED`.

That default is what a model compiled outside the solver honestly is. A final `persist_reason` never carries `PENDING` or `NOT_EVALUATED`; the final reasons are `RUN_END`, `BUDGET_STOP`, `CONTROLLED_STOP`, `CRASH` and `CANCELLED`.

### 3.2 The H2 chapter

```json
"provenance": {
  "schema": "virelai-provenance-chapter-v1", "phase": "H2",
  "capture": "ENABLED | DISABLED | FAILED | UNKNOWN",
  "integrity": "SEALED | OPEN | CORRUPT | UNAVAILABLE",
  "failure": null | {"code": "<audit_journal FAILURES>", "line": 7, "detail": "…"},
  "unavailable_reason": null | "CAPTURE_DISABLED | JOURNAL_MISSING | JOURNAL_UNREADABLE | JOURNAL_NOT_SUPPLIED | CHAPTER_COMPILE_FAILED",
  "writer_failure": null | "<the writer's in-memory failure detail>",
  "stamp": null | {"sidecar": "<run_stem>_provenance.jsonl", "journal_sha256": "<hex>|null",
                   "seal_event_hash": "<hex>|null", "head_hash": "<hex>|null", "event_count": 0,
                   "run": {"run_stem": "…", "game_id": "…"} | null, "verified": true|false},
  "rows": [ exact canonical EVENT rows: the verified prefix ],
  "seal": null | { exact SEAL row },
  "unscoped": [ "PV-…" ],
  "reconciliation": {"status": "RECONCILED | MISMATCH | NOT_EVALUATED", "findings": [ … ],
                     "ungated_resets": [ [level, transition_id] ], "product_joins": [ … ]},
  "answer_crosscheck": {"status": "MATCHED | MISMATCH | NOT_EVALUATED", "compared": 9, "findings": [ … ]},
  "typed_refs": {"PV-…": [ {"field": "…", "kind": "…", "id": "…", "scope": {…}|null, "required": bool, "hint": "…"} ]},
  "answer_refs": {"PV-…": {"kind": "ANSWER", "gate_id": "…", "level": 1, "life": 1, "answer_id": "…", "ordinal": 2}},
  "note_refs": {"PV-…": [ {"kind": "NOTE", "level": 1, "life": 1, "local_id": "N0001", "ref": "NOTE:L1:F1:N0001"} ]},
  "interim_prefixes": [ {"event_count": 57, "head_hash": "…", "status": "VERIFIED | CONTRADICTED"} ],
  "completeness": "COMPLETE | INCOMPLETE",
  "completeness_scope": "RUN | THROUGH_RECORDED_TERMINATION" | null,
  "reasons": [ "<codes>" ]
}
```

**For OPEN and CORRUPT journals:**
- only the reader's validated prefix is embedded;
- the typed `failure` is kept;
- `journal_sha256` is recorded when the bytes were readable;
- `seal_event_hash` is null and `stamp.verified` is false. A stamp is never verified without a valid matching seal.

### 3.3 Level index

Every v4 level carries `provenance_index: {admissions, executions, answers, selections, annotations}`, lists of event ids in sequence order. **Every embedded row id appears exactly once**, either in its own level's index under its category or in `unscoped`. A row goes to `unscoped` when its level is null or not among the model's levels. The categories are:

| Category | Rows |
|---|---|
| admissions | PROBE / ADMISSION |
| executions | PROBE / EXECUTION |
| answers | ANSWER |
| selections | G3_SELECTION |
| annotations | ANNOTATION |

## 4. Completeness

`completeness` is `COMPLETE` **if and only if** `reasons` is empty, which requires all of the following:

1. `integrity == SEALED`, with a valid seal and `stamp.verified`. The semantic seal hash and the exact-file hash both come from the **same read**.
2. The seal's `run.run_stem` equals the model's `run_stem` (otherwise `RUN_MISMATCH`). The model's raw `game_id` and the journal's file-stem `game_id` are recorded, never compared.
3. Admission-to-execution joins are exact. The reader enforces this; any defect makes the journal CORRUPT.
4. Every admitted probe is consumed exactly once (otherwise `ADMISSION_UNCONSUMED`).
5. Execution-to-transition and evidence-receipt joins are exact (R2-R4).
6. **[v3]** Every product is `ANSWER_CERTIFIED` with each stored reference joined to exactly one admitted answer, or a
   declared `GATE_DERIVED` closure (R6). An `UNATTRIBUTED` product always blocks.
7. The gate-answer cross-check is `MATCHED` (R7).
8. Every interim prefix recorded by H1 in this session is `VERIFIED`.
9. No `required` typed reference is `UNRESOLVED`.

**`reasons`** is the sorted set of codes:
- `JOURNAL_OPEN`, `JOURNAL_CORRUPT`, `JOURNAL_UNAVAILABLE`;
- `WRITE_FAILED`, when the writer reported a failure;
- `RUN_MISMATCH`;
- every reconciliation finding code;
- every cross-check finding code;
- `INTERIM_PREFIX_CONTRADICTED`.

An incomplete chapter keeps every verified row and lists every reason.

`completeness_scope`:
- `THROUGH_RECORDED_TERMINATION` when the chapter is `COMPLETE` and `persist_reason` is `CRASH`;
- `RUN` when `COMPLETE` otherwise;
- null when incomplete.

## 5. Reconciliation (H2; pure; recomputed by the validator)

| Rule | Check | Finding codes |
|---|---|---|
| R2 | Every `PROBE/EXECUTION/EXECUTED` row's `executed_transition` is in `levels[row.level].record.transition_ids` | `EXECUTION_NOT_RECORDED` |
| R3 | `levels[i].receipts.evidence` ↔ EXECUTED rows: one row per receipt, with the same `evidence_id`, the same level and the same transition, and no EXECUTED row without a receipt | `EVIDENCE_WITHOUT_EXECUTION`, `EXECUTION_WITHOUT_EVIDENCE`, `EXECUTION_EVIDENCE_DISAGREES`, `DUPLICATE_EVIDENCE_EXECUTION` |
| R4 | A recorded transition with no evidence receipt must be in `record.reset_transition_ids` | `UNGATED_TRANSITION`. Resets are listed in `ungated_resets`. |
| R5 | Every admitted probe has an execution row | `ADMISSION_UNCONSUMED` |
| R6 **[v3]** | Product → answer (§5.6) | `PRODUCT_UNATTRIBUTED`, `PRODUCT_WITHOUT_ADMITTED_ANSWER`, `AMBIGUOUS_PRODUCT_ANSWER`, `PRODUCT_REFERENCE_WITHOUT_SEMANTICS`, `PRODUCT_ANSWERS_NOT_RECORDED` |
| R8 | Required typed references resolve | `UNRESOLVED_REQUIRED_REFERENCE` |
| — | Interim prefix | `INTERIM_PREFIX_CONTRADICTED` |

### 5.6 **[v3]** Product → answer

By origin:
- `GATE_DERIVED`: join status `GATE_DERIVED`, no answer, no finding;
- `UNATTRIBUTED`: join status `UNATTRIBUTED` and `PRODUCT_UNATTRIBUTED` with its basis; it always blocks;
- `ANSWER_CERTIFIED`: each stored reference joins an admitted ANSWER row only when the gate, level and `answer_id`
  agree **and** the row's effective payload contains every clause (§2.2). Life is not stored on a product, so answers in
  different lives remain separate candidates.

| Candidates left | Status |
|---|---|
| exactly 1 | `EXACT` |
| 0 | `PRODUCT_WITHOUT_ADMITTED_ANSWER` |
| more than 1 | `AMBIGUOUS_PRODUCT_ANSWER` |

A reference whose every clause may be absent (nothing beyond the id must be present) gives
`PRODUCT_REFERENCE_WITHOUT_SEMANTICS`, unless the product's identity is independently derived from the answer id
(`EGO_LAW_DERIVED_FROM_ANSWER`). "The last answer before the product's revision" is **never** used.

### 5.7 **[v3]** Gate-answer cross-check (R7, H2 only; not recomputable from the model)

The k-th admitted ANSWER row, in journal sequence, is compared with line k of `_gate_answers.jsonl` on `gate_id`,
`executor`, `answer_id` and the payload. The line is the accepted answer plus named additions, so:
1. only `schema`, `gate_id`, `executor` and, for G1 and G2, the gate state `record_gate_answer` adds (G1:
   `gate_status_after_answer`, `coverage_certificate`, `pending_prediction`, `ego_law`; G2:
   `gate_status_after_answer`, `counter_candidate`, `pending_prediction`) are removed. A test pins this list to the
   recorder;
2. the rest is projected through its shape. A missing or extra field is `ANSWER_SHAPE_MISMATCH`, so a sidecar line
   that lost a semantic field is caught even though containment runs from the answer to the effective payload;
3. its `answer_id` must be the row's, and every clause must be contained in the row's effective payload.

A count difference, or answers admitted with no sidecar file, is a finding: `GATE_ANSWER_COUNT_MISMATCH`,
`GATE_ANSWERS_MISSING` or `GATE_ANSWER_MISMATCH` (naming the field; a payload finding lists the unmet clauses).

### 5.8 Typed and scoped references (chapter only)

- **`typed_refs`:**
  - for EXECUTED rows: `refs.evidence_id`, with `required: true`;
  - for admitted ANSWER rows: `effective.evidence_refs` and `effective.evidence_ref`, with `required: false`.
- **Kind:** assigned by resolution, never by prefix, in this order:
  1. `EVIDENCE` (any level's receipts);
  2. `WITNESS`;
  3. `PRODUCT`;
  4. `ENTITY` (witnesses, roles and track joins);
  5. `PROVENANCE_EVENT` (row ids);
  6. otherwise `UNRESOLVED`, with the prefix kept as a `hint`.

  `scope` is the citing row's level when the id resolves there; otherwise the levels where it does.
- **`answer_refs`:** a scoped identity for every admitted answer: `{gate_id, level, life, answer_id, ordinal}`.
- **`note_refs`:** `NOTE:L{level}:F{life}:{local_id}` for every ANNOTATION row's `note_ids`.

Local ids are not rewritten anywhere.

## 6. The stamp and the sidecar verifier

**H2 reads the journal once:** `Path.read_bytes()`, then `audit_journal.read_journal_bytes(data)` (new and neutral), with `sha256(data)` taken from the same buffer.

**`provenance_chapter.verify_sidecar(model, path)`** is a separate step. It returns:

| Result | When |
|---|---|
| `NOT_APPLICABLE` | there is no file hash |
| `MISSING` | the sidecar is gone |
| `VERIFIED` | the file hash matches |
| `REWRITTEN` | the hash differs but the bytes read SEALED with the same seal hash |
| `SUBSTITUTED` | otherwise |

Removing the sidecar later never invalidates a written model. A sidecar missing **during H2** makes that model `INCOMPLETE` (`UNAVAILABLE / JOURNAL_MISSING`).

## 7. Validation

Validation is pure and does no file I/O. `world_model_v2.validate` applies the **v3 rules plus**:
- the chapter's key set and enums for its phase, and the agreement between phase and `persist_reason`;
- the embedded rows (and the seal) re-verified as a journal from genesis. The result must be SEALED exactly when `integrity` is SEALED, and OPEN for an OPEN or CORRUPT prefix;
- the stamp's internal consistency;
- level indexes partitioning the row ids;
- **recomputing** R2-R6, R8, the typed, answer and note references, the product joins and the interim prefixes from the model, and requiring equality with what is stored;
- completeness, scope and reasons following §4 from the stored fields;
- **[v3]** every `product_answers` entry: its origin, a basis allowed for that origin (a `GATE_DERIVED` basis only for its
  own product type), answers present exactly when certified, and every reference following its shape exactly (the
  same clause list, keys, rules and omitted fields). A dropped or weakened clause, or a certified product relabelled
  as gate-derived, fails validation.

R7 and the file hash cannot be recomputed without the sidecar. Their stored results are checked for internal consistency only.

**Frozen readers:**
- `validate_v3` (new, frozen) and `validate_v2` keep their accepted rules;
- `read_world_model` dispatches v1, v2, v3 and v4;
- `seal()` always writes v4.

## 8. Endings

| Ending | Model | Provenance |
|---|---|---|
| Normal end, budget stop, controlled stop ending the run, cancelled | H2 | `COMPLETE` when every rule passes |
| Handled crash | H2, `persist_reason: CRASH` | `COMPLETE` with scope `THROUGH_RECORDED_TERMINATION` when every rule passes |
| Level boundary | H1 interim | `PENDING`, with the `WRITER_REPORTED` prefix |
| Write failure | H2 | `OPEN` prefix, `capture: FAILED`, `WRITE_FAILED`, `INCOMPLETE` |
| Corrupt journal | H2 | `CORRUPT` prefix with the typed failure, `INCOMPLETE` |
| Journal missing, or capture disabled | H2 | `UNAVAILABLE`, `INCOMPLETE` |
| Pre-`play` crash, or the model not written | **none** | `WORLD_MODEL_NOT_WRITTEN` warning where possible; the roster reports `MODEL_MISSING` |

**The run roster:** `inference/framework/run_roster.py`, `check_runs(job_dir, expected_run_stems)`. It is offline and never called in play. For each run stem it reports:
- the model: `FINAL`, `INTERIM_ONLY` or `MODEL_MISSING`;
- the journal: present or absent, with its read status;
- the warnings found;
- the chapter's completeness.

## 9. **[v3]** Escalations: v2's, as ruled; and what revision 2 asks

As ruled (2026-10-15):
- **E1** is resolved by origins (§2.1). Missing attribution stays blocking; `NO_REFERENCE_BLOCKS` is gone.
- **E2** is replaced by directional containment (§2.2, §5.7).
- **E3** is accepted: answer-payload references are typed and kept for PE-03; only structural references block.
- **R1** (ratchet residual) is accepted: `solver.py` +7 and `library_census.py` +3 executable lines at the call sites.
- **S1** (the synthetic carry journal) is accepted as a measurement limit; production reconciliation is unchanged.

**[v4]** As ruled on revision 2 (2026-10-15):
- **E4** is ruled: all six declared `GATE_DERIVED` closures are kept, with their restrictions (the payload states the
  disposition, the answer-bearing field is empty, an in-progress product never qualifies).
- **E5** is superseded by F4: the record-derived answer is now rebuilt in full and its id checked (§2.1).
- **Multi-level** is proven on the production path: a real two-level controller session (real `ToolAgent`, controller
  executor and capture; H1 at the boundary, H2 at the end) reaches `SEALED / COMPLETE`, every product joins an admission
  recorded on its own level, and the answer ids that recur on level 2 (G0, G1) join level 2's own events. Removing
  level 2's G0 admission leaves level 2's product unjoined: the level-1 admission is never borrowed. The level-scoped
  join is unchanged.

## 10. Hook map (as built)

| File | Change |
|---|---|
| `inference/framework/provenance_chapter.py` (**new, neutral**) | `live()`, `h1()`, `h2()`, `default_for()`, `attach()`, `derive()`, `validate_chapter()`, `verify_sidecar()`; **[v3]** product joins by origin and the containment cross-check |
| `inference/framework/answer_shapes.py` (**new, pure**) **[v3]** | the shape table, strict `sha16`, `project`, `reference`, `unmet`, `check_reference`, the sidecar's named additions |
| `inference/framework/product_origins.py` (**new**) **[v3]** | the census-time provenance adapter and the origin vocabulary: `certifying_answers`, `entry`, `entry_problem` (used by the validator), `ego_law_id`; **[v4]** `record_relations_answer`, `record_answer_id`, the retained-state guards |
| `inference/framework/provenance_hooks.py` (**new**, added after revision 1's first build) | the writer hooks; `product_answers` delegates to `product_origins` **[v3]** |
| `inference/framework/run_roster.py` (**new**) | `check_runs()` |
| `inference/framework/audit_journal.py` | `read_journal_bytes(data)`; `_read` now delegates to it (same behaviour) |
| `inference/framework/world_model_v2.py` | v4 `SCHEMA`, `V3_SCHEMA`, `validate_v3`; `seal()` attaches the default chapter and the indexes; v4 dispatch |
| `inference/framework/library_census.py` | `compile_level` adds `record.reset_transition_ids` and `product_answers` (through `provenance_hooks`) |
| `inference/agent/provenance_capture.py` | a pure `journal_path(state_path)`, which `journal()` now uses |
| `inference/framework/solver.py` | `_write_l2a_world_model` attaches the H1 or H2 chapter through a three-line `_provenance_chapter` delegate; `_l2a_writer_prefixes`; `_play_one` adds `WORLD_MODEL_NOT_WRITTEN` (through `provenance_hooks`) |
| `tests/test_world_model_v4_provenance.py` (**new**), six v3 pins, `tests/tiers/*` | the fail-first suite, the version pins, and tier T0 `provenance-v4` |

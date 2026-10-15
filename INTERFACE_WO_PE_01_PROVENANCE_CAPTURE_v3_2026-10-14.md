# Interface: WO-PE-01 provenance capture

**Version:** v3, 2026-10-14. It supersedes v2 and v1 in full; both stay in place as history.
**Author:** Claude (Alpha build seat)
**Base:** the parked WO-PE-01 revision 2 (on `ring9-unified` at `a925d7f`)
**Governing:**
- `RULINGS_PAPER_EVIDENCE_v1_2026-10-14` D1-D4 and its two carried defects;
- the Director's WO-PE-01 directive;
- Sol's revision-2 order (2026-10-14);
- Sol's final amendment, revision 3 (2026-10-14): the seal names its run.

**Out of scope:**
- schema v4, claims and keys;
- the grader;
- any change to `world_report.md`;
- any gate admission rule, scheduler, targeting or action-choice change;
- Kaggle and submission.

## 0. What changed

**From v2 (revision 3):**

| § | Change |
|---|---|
| 2 | The seal carries `run = {run_stem, game_id}`. The seal hash covers it, and an empty journal's identity comes from its seal. |
| 7 | The seal validator requires `run`: exactly the declared fields, a valid nonempty identity, and agreement with every event (`RUN_MISMATCH`). The writer runs the full seal validator before it writes the seal. `JournalRead.run` reports the journal's identity. |
| 7 | `ProvenanceJournal.open` compares the requested run with an existing OPEN journal's run. On a mismatch it fails at once, so the caller can neither append nor seal. An OPEN journal with no events may be continued. |

Event rows, admission joins, capture points, executor semantics, capability normalization, action behaviour and gate behaviour are unchanged from v2. Event-row bytes are identical; only seal bytes differ.

**From v1 (revision 2):**

| § | Change | Source |
|---|---|---|
| 1, 7 | The neutral module is renamed `inference/framework/provenance.py` → **`inference/framework/audit_journal.py`**, so it is never confused with the weave's cell-ownership `virelai_golden/weave/provenance.py`. `inference/agent/provenance_capture.py` keeps its name. | Sol, item 4 |
| 2, 3 | Probe executions join to their **exact admission** through `refs.admission_event_id`. `probe_id` is never a join key on its own. | Sol, item 1 |
| 2 | An execution row carries **its admission's context**: level, life, gate and the transition before the decision. The transition it produced stays in `refs.executed_transition`. | Sol, item 1 (the join must agree on gate, level and life) |
| 2 | Canonical JSON is **strict**. There is no `default=str`, and a non-finite number or a non-string key is rejected. A payload that is not plain JSON fails the journal (fail-open), and is never stringified. | Sol, item 2 |
| 7 | The reader validates the **whole row contract**, adds six failure codes, and returns `joins`. The writer runs the same checks before it writes. | Sol, items 1-2 |
| 8 | **Finalization order:** the open G3 outcome is recorded first, then provenance is sealed. | Sol, item 3 |
| 10 | Revision-1 decisions are recorded as **ratified**. | Sol, item 5 |

## 1. What is built

| Part | File | Role |
|---|---|---|
| The journal | `inference/framework/audit_journal.py` (**new, neutral**) | The row schema; strict canonical bytes; the deterministic `event_id`; the hash chain; one verifier (`_Chain`) shared by the writer and the reader; `ProvenanceJournal` (append and seal); `read_journal`; `validate_rows`; `translate_g3_event`; `field_sources`. It imports nothing from the agent, the gates or the census. |
| Capture glue | `inference/agent/provenance_capture.py` (**new**) | One function per capture point. Every capture point **fails open**: building or writing a row never raises into gameplay. A failure marks the journal failed. While capture is disabled, every function returns at once. |
| Duck probe | `inference/agent/tool_agent.py` `_gate_probe_begin` | An ADMISSION row on admit or refusal. The admitted row's `event_id` is kept on the pending probe. |
| Duck action wrapper | `tool_agent.py`, the gated `action()` handler | <ul><li>A refusal before the gate becomes ADMISSION / REFUSED.</li><li>An admitted probe ends as EXECUTION / EXECUTED or NOT_ATTEMPTED, joined to its admission.</li></ul> |
| Duck answer | `tool_agent.py` `gate_answer` | The submitted payload, the effective payload (via `machine.prepare_answer`) and the field-source map. ADMITTED or REFUSED, with a typed reason. |
| Controller answer and probe | `inference/agent/controller_turn.py` | The same, with executor CONTROLLER |
| G3 choice | `inference/agent/memory_queries.py` `_chosen_probe`; the drain of `machine.g3_selection_events` | Translated G3 events (§4), and the refusal raised before `g3_selection.select` |
| Notes | `memory_queries.py` `_submit` | ANNOTATION / UNCERTIFIED or REFUSED |
| Answer split | `inference/framework/virelai_gates.py` | `prepare_answer`, `submit_prepared` and `submit_answer(raw, *, executor="DUCK")`. Unchanged from v1. |
| Defect 2 | `virelai_gates.py` `_LeverTarget` / `_submit_reachability` | The lifecycle `actor` is the real executor. Unchanged from v1. |
| Defect 1 and close | `inference/framework/solver.py` | `_close_provenance` in `play`'s `finally`, now **after** `_record_open_g3_outcome` (§8) |

**Switch.** `ToolAgent(provenance_enabled=False)` is the constructor default. The production solver enables capture unless `VIRELAI_PROVENANCE=0`.

## 2. The journal file and row schema

**File:** `{run_stem}_provenance.jsonl`, beside the other sidecars.

**Bytes:** one canonical row per line. Canonical means sorted keys, `(",", ":")` separators, ASCII, `allow_nan=False`, and one trailing newline.

**Strict JSON.** Only `None`, `bool`, `int`, finite `float`, `str`, lists and tuples (tuples are written as lists), and mappings with string keys are accepted. Anything else raises `TypeError` or `ValueError` and never reaches the file. That includes:
- an arbitrary object;
- a set;
- a non-finite number;
- an integer key.

**An event row.** Field order is irrelevant because the bytes are canonical.

| Field | Value and type |
|---|---|
| `schema` | `"virelai-provenance-v1"` |
| `record` | `"EVENT"` |
| `seq` | a positive integer: 1, 2, 3, … per journal |
| `event_id` | `"PV-"` + 16 lowercase hex characters = sha256(canonical `{run, seq, content}`)[:16], where `content` is the thirteen body fields below. It is deterministic, and distinct for repeated identical submissions. |
| `previous_event_hash`, `event_hash` | 64 lowercase hex characters. Genesis is 64 zeros. `event_hash` is sha256 of the canonical row without `event_hash`. |
| `run` | exactly `{run_stem, game_id}`, both nonempty text. It is the same on every event of one journal. |
| `level`, `life`, `at_transition` | an integer or `null` |
| `gate_id` | text or `null` |
| `executor` | `DUCK`, `CONTROLLER` or `SYSTEM`: the submitter, never the certifier |
| `operation`, `event`, `disposition` | one valid combination (§3) |
| `submitted` | the exact submitted payload, as strict JSON, or `null` |
| `effective` | for an answer, the payload given to validation; otherwise `null` |
| `field_sources` | for an answer, a map from field path to source (§5); otherwise `null` |
| `refs` | exactly the nine keys in the next table |
| `reason` | `null`, or exactly `{code, text}`: a typed code (§6) and nonempty text. It is required on REFUSED, NOT_ATTEMPTED, SUPERSEDED and every OPPORTUNITY row. |

**The `refs` keys:**

| Key | Type |
|---|---|
| `question_id`, `subject`, `probe_id`, `answer_id`, `evidence_id` | text or `null` |
| `executed_transition` | integer or `null` |
| `note_ids` | a list of text, or `null` |
| `source_event` | `null`, or exactly `{event, actor, phase, gate_revision}`. `event` is a G3 event name, `actor` is text, `phase` is text or `null`, `gate_revision` is an integer or `null`. |
| `admission_event_id` | the `event_id` of the consumed admission on a PROBE EXECUTION row; `null` on every other row |

**Context of an execution row.** A PROBE EXECUTION row (EXECUTED or NOT_ATTEMPTED) carries the **admission's** `level`, `life`, `gate_id` and `at_transition`, the context of the decision it executes. The transition the probe produced is `refs.executed_transition`. v1 took the context after execution, which could differ from the admission when the probe completed a level or advanced the gate.

**Capability tokens.** The submitted `decision.probe_token` is journaled as its **semantic capability**: `CAPABILITY:{probe_id}:R{gate_revision}` when the gate issued it, or `CAPABILITY:NOT_ISSUED` when it did not. The HMAC is never stored.

**The seal row** is written once, at session close: `{schema, record: "SEAL", seq, run, previous_event_hash, event_count, head_hash, event_hash}`. It is **journal control metadata outside the D2 event vocabulary**, as ratified.
- `run` is the same canonical `{run_stem, game_id}` as the events, and `event_hash` covers it.
- An empty journal (`event_count` 0) is identified by its seal alone.
- Identical empty runs write byte-identical seals.

**Rules for every row:**
- No wall-clock value, path, pid or random value appears.
- An identical deterministic replay produces a byte-identical journal.

## 3. Valid combinations and the probe join

| Operation | OPPORTUNITY | ADMISSION | EXECUTION |
|---|---|---|---|
| `PROBE` | — | ADMITTED, REFUSED | EXECUTED, NOT_ATTEMPTED |
| `ANSWER` | — | ADMITTED, REFUSED | — |
| `G3_SELECTION` | OFFERED, NOT_ATTEMPTED | ADMITTED, REFUSED, SUPERSEDED | EXECUTED |
| `ANNOTATION` | — | UNCERTIFIED, REFUSED | — |

**The probe join, enforced by the writer and the reader:**
- Every `PROBE / ADMISSION / ADMITTED` row is an **operation anchor**.
- Every `PROBE / EXECUTION` row, EXECUTED or NOT_ATTEMPTED, names one anchor in `refs.admission_event_id`.
- The anchor must appear earlier in the same journal.
- The execution and its anchor must agree on `operation`, `refs.probe_id`, `executor`, `run`, `gate_id`, `level` and `life`.
- Each anchor is consumed by at most one execution.
- An EXECUTED row also names `evidence_id` and `executed_transition`.
- `probe_id` alone is never used as a join key. It recurs across levels, lives and replays.

## 4. G3 translation

The translation is unchanged from v1. `refs.source_event` keeps the original event and its actor.

| G3 selection event (actor) | Audit row | Executor |
|---|---|---|
| HANDOFF (CONTROLLER) | `G3_SELECTION / OPPORTUNITY / OFFERED` | CONTROLLER |
| COVERAGE_RESUMED (CONTROLLER) | `G3_SELECTION / OPPORTUNITY / NOT_ATTEMPTED` | **DUCK**: the row records Duck's unused opportunity (ratified). The controller's actor stays in `refs.source_event.actor`. |
| ADMITTED (DUCK) | `G3_SELECTION / ADMISSION / ADMITTED` | DUCK |
| REFUSED (DUCK) | `G3_SELECTION / ADMISSION / REFUSED` | DUCK |
| STALE | `G3_SELECTION / ADMISSION / SUPERSEDED` | the choice's actor |
| FINISHED | `G3_SELECTION / EXECUTION / EXECUTED` | the choice's actor |

G3 rows are drained from `machine.g3_selection_events` before every other row and at close. A cursor on the journal object records how far the drain has read.

## 5. Field sources (answers)

Unchanged from v1.

| Field | Source |
|---|---|
| Any top-level field of `effective` that is not certified | `SUBMITTER` |
| A certified field the submitter left out, or left `None` or the `CERTIFIED` marker | `CONTROLLER_FILLED` |
| A certified field the submitter wrote, on an ADMITTED row | `SUBMITTER_CONFIRMED_BY_CONTROLLER` |
| A certified field the submitter wrote, on a REFUSED row | `SUBMITTER` |

**Answer notes (ratified):**
- An admitted answer's notes give `ANNOTATION / ADMISSION / UNCERTIFIED`.
- An `ANNOTATION / ADMISSION / REFUSED` row is added only when annotation validation caused the answer's refusal.

## 6. Reason codes

Unchanged: `GATE_CONTRACT`, `ORIENTATION_DUE`, `ANNOTATION_INVALID`, `ACTION_CONTRACT`, `TERMINAL_STATE`, `NOT_EXECUTED`, `EXECUTION_ERROR` and `G3_EVENT`, with the meanings given in v1 §6.

## 7. Reader and validator: the trust boundary

`read_journal(path) -> JournalRead(rows, status, failure, seal, joins)`. It returns the **verified prefix**, a status (`SEALED` / `OPEN` / `CORRUPT`), a typed failure `{code, line, detail}`, the seal, and `joins`, a map from each execution's `event_id` to the admission `event_id` it consumed.

**Checks, in order, for every line:**
1. **Parse.** Strict JSON; a non-finite constant is rejected. The result is `MALFORMED_ROW`, or `TRUNCATED_TAIL` for a partial or unterminated final line.
2. **Sequence.** It must be the expected next number: `SEQUENCE_GAP`, `DUPLICATE_SEQUENCE` or `SEQUENCE_REORDERED`.
3. **Record.** It is `SEAL` or `EVENT`; anything else is `SCHEMA_INVALID`.
4. **An event:**
   1. its exact keys, `schema`, a positive integer `seq`, `run` shape, the `event_id` and hash formats, every field type in §2, and the valid combination with its reason, refs and field sources (`SCHEMA_INVALID`);
   2. the row hash (`HASH_MISMATCH`);
   3. the chain (`CHAIN_BROKEN`);
   4. `event_id` equals the formula for that row (`EVENT_ID_MISMATCH`);
   5. the same run as every earlier event (`RUN_MISMATCH`);
   6. for a probe execution, the join (§3): `ADMISSION_MISSING`, `ADMISSION_ALREADY_CONSUMED` or `ADMISSION_MISMATCH`.
5. **A seal:**
   1. its exact keys (`run` included), the expected `schema`, a valid nonempty `run`, a positive integer `seq`, an integer `event_count` and the hash formats (`SCHEMA_INVALID`);
   2. its hash, which covers `run` (`HASH_MISMATCH`);
   3. its `run` equals the run of every event before it (`RUN_MISMATCH`). An empty journal takes its identity from the seal;
   4. `previous_event_hash`, `head_hash` and `event_count` match the verified prefix (`SEAL_MISMATCH`);
   5. it is the final line (`ROWS_AFTER_SEAL`).

`JournalRead.run` is the journal's run identity: from its events, or from its seal when it has none. It is `null` for an OPEN journal with no events.

**Statuses:**

| Status | Meaning |
|---|---|
| `SEALED` | Every row verifies and a matching seal ends the file. |
| `OPEN` | Every row verifies, but there is no seal. |
| `CORRUPT` | Reading stopped at a typed failure. |

**Failure codes:** `TRUNCATED_TAIL`, `MALFORMED_ROW`, `SCHEMA_INVALID`, `SEQUENCE_GAP`, `DUPLICATE_SEQUENCE`, `SEQUENCE_REORDERED`, `HASH_MISMATCH`, `CHAIN_BROKEN`, `EVENT_ID_MISMATCH`, `RUN_MISMATCH`, `SEAL_MISMATCH`, `ROWS_AFTER_SEAL`, `ADMISSION_MISSING`, `ADMISSION_MISMATCH` and `ADMISSION_ALREADY_CONSUMED`. v1's `UNJOINED_EXECUTION` is replaced by the three `ADMISSION_*` codes.

**The writer.** Before each event it runs the same verifier, skipping only the recomputation of the hashes it has just computed. Before the seal it runs the **full** seal validator (`_Chain.check_seal`). It never writes a row the reader would reject. A row that fails is a journal failure, not a raise.

**Extending a journal.** `ProvenanceJournal.open` behaves as follows:
- **A SEALED or CORRUPT journal** fails at once. It is never extended.
- **An OPEN journal with events** is first checked against the requested run. If the requested run differs from the verified journal run, the journal fails at once: the caller can neither append nor seal, and the file is unchanged. If the run matches, the chain state is rebuilt (head, run, open admissions and consumed admissions) and the run continues.
- **An OPEN journal with no events** has no identity yet and may be continued by the requested run. Once its seal is written it is closed.

## 8. Finalization order

The `finally` of `play` runs, in this order:
1. `_record_open_g3_outcome(run)`: records the open G3 outcome;
2. `_close_provenance()`: flushes and translates every remaining G3 selection event, closes any pending admitted probe as NOT_ATTEMPTED / EXECUTION_ERROR, seals the journal, and reports `PROVENANCE_WRITE_FAILED` if capture failed;
3. `_finish_if_needed()`;
4. `_write_l2a_world_model(final=True)`: writes the final canonical model.

Provenance is therefore sealed only after gate finalization has finished.

## 9. Failure and performance

**Failure (fail-open):**
- Any capture failure marks the journal failed, after which no further rows are written, so the file stays a verifiable prefix. Capture failures include a write error, a payload that is not strict JSON, and a row the verifier rejects.
- The solver writes one `PROVENANCE_WRITE_FAILED` observer warning at close.
- Action selection, admission and the game continue unchanged.

**Performance:**
- No `fsync`. One `open(…, "ab")` and one write per row.
- No census and no seal on the per-action path.
- **Budget:** at most 1.0 s added over 400 controller operations.

## 10. Revision-1 decisions, as ratified by Sol

- The SEAL record is accepted as journal control metadata, outside the D2 event vocabulary.
- Capability HMACs are never stored. The journal records their deterministic semantic capability identity (§2).
- `COVERAGE_RESUMED` uses executor `DUCK`. The original controller actor remains in `refs.source_event`.
- Accepted answer notes produce `ANNOTATION / UNCERTIFIED`. An annotation refusal row is added only when annotation validation caused the answer's refusal.
- The original greenfield fail-first evidence is accepted. Revision 2 adds fail-first evidence for its own corrections only.
- Provenance hook calls receive a narrow ratchet exemption in `_run_python_tool`, `_handle_action` and `_handle_virelai_query`. No unrelated extraction is done.
- The neutral module is named `audit_journal.py`.
- Revision 2 is accepted except for the seal's missing run identity. Revision 3 corrects that alone.

## 11. Tests

`tests/test_provenance_capture.py` holds 49 cases: the 29 revision-1 cases (v1 §9, unchanged), and 15 revision-2 and 5 revision-3 cases.

**Fifteen revision-2 cases:**

| Revision-2 case | Item |
|---|---|
| The same `probe_id` admitted in two lives, each execution joined to its own admission | 1.1 |
| An execution that points at the older admission → `ADMISSION_MISMATCH` | 1.2 |
| An execution with no `admission_event_id` → `ADMISSION_MISSING` | 1.3 |
| Two executions consuming one admission → `ADMISSION_ALREADY_CONSUMED` | 1.4 |
| A captured NOT_ATTEMPTED joined to its exact admission | 1.5 |
| Every captured execution (Duck and a whole controller run) names its own admission | 1, capture side |
| A forged `event_id` with every hash recomputed → `EVENT_ID_MISMATCH` | 2.1 |
| A different run mid-journal → `RUN_MISMATCH` | 2.2 |
| An event whose `record` is not `EVENT` → `SCHEMA_INVALID` | 2.3 |
| A seal with the wrong schema and a recomputed hash → `SCHEMA_INVALID` | 2.4 |
| Unsupported submitted objects (object, set, integer key): the journal fails and nothing is stringified | 2.5 |
| A non-finite submitted value fails open: the game sees the same reply, and close reports `PROVENANCE_WRITE_FAILED` | 2.6 |
| An event made during final G3 handling is journaled before the seal, and the finalization order is pinned | 3 |

**Five revision-3 cases:**

| Revision-3 case | Item |
|---|---|
| An empty sealed journal names its run and reads `SEALED` | 3.1 |
| A nonempty OPEN journal cannot be reopened as another run, even when no new event is submitted; its own run can still continue and seal it | 3.2 |
| A seal carrying a different run is rejected (`RUN_MISMATCH`) after its hash is recomputed | 3.3 |
| Identical empty runs produce byte-identical seals that carry the run; a different run gives a different seal | 3.4 |
| The seal writer runs the full seal validator before writing, and an invalid seal is never written | 3.5 |

The forged-journal helper writes `run` into its seals, the revision-3 contract.

No test parses transcript prose.

**Tiers:**
- **T0 `provenance`:** this file and its neighbours. It now has 76 tests.
- **T1 `paper-evidence`:** it now has 265 tests.
- **T2 snapshot:** 975 tests (970 plus the 5 revision-3 tests; none removed).

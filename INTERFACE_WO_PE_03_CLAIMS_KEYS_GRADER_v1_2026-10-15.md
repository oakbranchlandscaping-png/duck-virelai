# Interface: WO-PE-03, atomic claims, answer keys and the five-category grader

**Version:** v1, 2026-10-15. This is the read-only design sweep. No production file was edited.
**Author:** Claude (Alpha build seat)
**Base:** `ring9-unified` at **`e158057`**. All 310 runtime-source files match it by blob hash (`STATE_OF_THE_DUCK_BUILD_v10`, grounding).

**Governing:**
- `RULINGS_PAPER_EVIDENCE_v1_2026-10-14`, D5-D14;
- `THESIS_v1_2026-10-05`, C2 and build item 1;
- Sol's PE-02 rulings (E3, E4, F4; `REVIEW_WO_PE_02_…_v2` §2-§3);
- `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_v1` §6-§7;
- Sol's sweep §8-§9.

**Fixed while this is designed** (Sol's PE-02 closure): schema, capture, gates, scheduling, action selection.

**Not done here:** no key item is authored. Keys are the Director's (D9).

---

## 0. Findings that need a ruling before a build interface

1. **F-A · The sealed v4 model does not hold the content most claims are about.** It stores each certified product only as a receipt: gate, type, revision and `payload_sha256`, plus the G2 mask summary. The content itself is not there:
   - EgoLaw action laws;
   - the counter model;
   - G4 anatomies;
   - orbit typing;
   - G4-B relations and their graded predictions;
   - the G4-C law test and its outcome.

   No v4 field carries a graded prediction's `SUPPORTED` or `CONTRADICTED` status (`library_census.py`, `world_model_v2.py` and `world_description.py` have no such field; the laws page says "stored evidence only"). The admitted answers in the provenance chapter hold what was *proposed*, but not what the gate *derived*, and not how a prediction *fared*.

   **Consequence:** under "the projection is a pure read of the sealed model", LAW, RELATION, PREDICTION-status and audit claims ("P3 was contradicted") cannot be projected. The ruling that propositions and audit statements are graded separately (D11) needs exactly those outcomes. Options are in §6, D15.
2. **F-B · Key subjects cannot use solver ids.** A Director writing a key from play does not know `E0054`, `O-L1-P1-E-…` or `P-…`. The key must address objects the way a person sees them: the level-entry frame plus geometry, or an object handle such as `c12@63,0`. The grader must then map key objects to solver subjects. Prior art is `foundation_grade.map_foundation` (v4): EXACT, then COMPOSITE, then UNMATCHED, with human confirmation. That is D16.
3. **F-C · The product receipt hash is not strict JSON.** `library_census._payload_sha256` uses `json.dumps(…, default=str)`. If D15 embeds product content and verifies it against the existing receipts, the receipt hash has the same flaw F3 fixed for answer fields. A schema change would have to replace it, not inherit it.
4. **F-D · No fixture has Duck answers under v4.** The real controller run's v4 model holds 9 admitted answers, all `CONTROLLER`. Nothing measured here exercises Duck-admitted or Duck-refused claims. The build needs one fixture that does: the offline `CardDuck` / `Ft09LiveRun` path is the nearest existing driver.

---

## 1. What the sealed v4 model can supply today (measured on the real controller run, `e158057`)

| Source in the model | Count on the run | Family | Executor / certification available |
|---|---|---|---|
| `certified.roles` | 7 (EGO 1, COUNTER 1, LEVER 5) | ROLE | the role's product → `product_answers` origin → joined answer row's executor and field sources |
| `certified.scoped_nulls` | 59 | ROLE (scoped null: no observed effect in the recorded state) or CONDITION | controller (G3 roster) |
| `gaps` | 73: NOT_REACHED 62, NOT_BUILT 5, CLASS_CHANGED 4, IDENTITY_UNRESOLVED 2 | GAP | SYSTEM |
| `describe_world` patterns | 8; 1 mixes explanation statuses | TRANSFORMATION | SYSTEM (observation); explanation status per event |
| `describe_world` questions | 3 | GAP (open question) | SYSTEM |
| `receipts.products[G2].mask` | 1 | LAW (mask cells and rewrite) | the G2 product's origin |
| `provenance.rows` ANSWER admissions | 9, all `CONTROLLER / ADMITTED` | per field (§3): LAW, ROLE, PREDICTION, RELATION, CONDITION | the row's executor, disposition and per-field sources |
| `provenance.rows` PROBE admissions / executions | 67 / 67 | audit only (not propositions) | the row's executor |
| `product_answers` origins | 5, all `ANSWER_CERTIFIED` | certification dimension | origin and basis |
| graded outcomes, product content | **absent** (F-A) | PREDICTION status, LAW content, RELATION content, audit | — |

Pattern splits are per (subject, verb, site rewrite, action, delta); the run has 8 patterns and 8 split units. The one mixed-status pattern splits by status (D7), giving a 9th unit.

---

## 2. The claim contract (D5-D8, made concrete)

```json
{
  "schema": "virelai-paper-claim-v1",
  "claim_key":    "C-<sha16 of the proposition>",
  "assertion_id": "A-<sha16 of claim_key + source>",
  "game_id": "…", "run_stem": "…", "level": 1,
  "family": "ROLE | TRANSFORMATION | RELATION | LAW | PREDICTION | CONDITION | GAP",
  "kind": "PROPOSITION | AUDIT",
  "subject":   {"type": "ENTITY | TRACK | OBJECT_HANDLE | ACTION | AGENT | LEVEL | COUNTER | MASK", "ref": "…",
                "geometry": {"frame": "<entry board_sha256>", "anchor": [r, c], "bbox": [r0, c0, r1, c1],
                             "cell_count": 36, "class": 9} | null},
  "predicate": "<one closed verb per family>",
  "object":    "<one value: a role, rewrite, delta, state, lever map entry, …>",
  "scope":     {"lives": [1], "transitions": [55, 62] | null, "action": "ACTION6" | null, "condition": "…" | null},
  "status":    "OBSERVED | CERTIFIED | EXPLAINED | PARTLY_EXPLAINED | UNEXPLAINED | PREDICTED | SUPPORTED | CONTRADICTED | OPEN | CLOSED_WITHOUT_FINDING",
  "executor":  "DUCK | CONTROLLER | SYSTEM",
  "admission": "ADMITTED | REFUSED | NOT_APPLICABLE | UNCERTIFIED",
  "certification": "ANSWER_CERTIFIED | GATE_DERIVED | UNATTRIBUTED | RECORD_DERIVED | NONE",
  "field_source": "SUBMITTER | CONTROLLER_FILLED | SUBMITTER_CONFIRMED_BY_CONTROLLER | null",
  "source": {"provenance_event": "PV-…" | null, "product_id": "…" | null, "pattern_id": "P-…" | null,
             "gap_index": 3 | null, "model_path": "levels[0].certified.roles[2]"},
  "refs": ["E-…", "t55-t62", "manifest", "…"]
}
```

**Identity:**
- `claim_key` hashes `(game_id, level, family, kind, subject.type, subject.ref, predicate, object, scope)` under strict canonical JSON. It excludes `status`, `executor`, `admission`, `certification`, `field_source`, `source` and `refs`, as ruled.
- `assertion_id` hashes `claim_key` plus `source`. The same proposition proposed by Duck and later certified by the controller is one `claim_key` and two assertions.
- **Open point:** `run_stem` is deliberately not in `claim_key`, so a key can join two runs of the same game.

**Splitting rules** (D5, D7):

| Source | One claim per | Notes |
|---|---|---|
| role | (role, subject) | |
| scoped null | (entity, scope) | |
| gap | gap record | |
| pattern | (subject, verb, rewrite, action, delta, explanation status) | Counts and span go to `scope` and `refs`, never into identity. |
| answer field | field, through the PE-02 answer-shape table | `action_laws[i]`, `conditions[j]`, `falsifier`, `mechanism`, each relation, and each named lever in a prediction's `expected` are separate claims. A field the shape table marks `GENERATED`, `DERIVED` or `OUTCOME` is never attributed to the submitter. |

**Kinds:**
- `PROPOSITION`: what the world is claimed to be.
- `AUDIT`: what happened to a proposition, for example "Duck's prediction for E0055 was contradicted at t62" (D11).

`AUDIT` claims need graded outcomes, so they are blocked on F-A.

**Inherited rules:**
- A `GATE_DERIVED` product yields `status: CLOSED_WITHOUT_FINDING` closure or gap claims only, never a LAW or RELATION (Sol, E4).
- `RELATIONS_CERTIFIED_FROM_RECORD` content is `certification: RECORD_DERIVED, executor: SYSTEM`. The controller's admitted answer is the trigger and appears in `source` (F4).
- Refused answers project too, as `admission: REFUSED`. Their interpretable fields stay in the grading denominator. A contract-invalid payload projects one claim, `family: GAP, status: OPEN`, flagged unparseable (D11).
- Annotations project as `admission: UNCERTIFIED`. E3's typed payload references feed `refs`.

---

## 3. The key format (D9: the structure only; authoring is the Director's)

```json
{
  "schema": "virelai-paper-key-v1",
  "game_id": "…", "levels": [1, 2],
  "construction": {"author": "Director", "method": "PLAY | RECORDING_REVIEW", "frozen_on": "YYYY-MM-DD",
                   "commit": "<sha at freeze>", "blind_to_reports": true},
  "sources": [{"recording": "<path>", "sha256": "…", "frames": 412}],
  "items": [{
    "key_id": "K-…", "level": 1, "required": true,
    "family": "ROLE", "kind": "PROPOSITION",
    "subject": {"type": "OBJECT", "geometry": {"frame": "<entry board_sha256 or recording frame index>",
                "anchor": [36, 44], "bbox": [36, 44, 41, 49], "cell_count": 36}},
    "predicate": "ROLE_IS", "object": "LEVER",
    "scope": {"lives": null, "action": "ACTION6", "condition": null},
    "accepted_alternatives": [{"predicate": "ROLE_IS", "object": "LEVER_TOGGLE"}],
    "basis": "free text: what the Director saw",
    "ambiguity": null
  }]
}
```

**Validation, by code, at grade time:**
- the schema;
- unique `key_id`s;
- every source hash matches the run's recordings;
- the key's freezing commit is an ancestor of the commit that adds the run's report packet. Git can check this; that nobody opened a report before the freeze remains the Director's attestation, recorded in `blind_to_reports`;
- `frozen_on` and `blind_to_reports` are present.

The rule "the model never sees the key" is structural: no runtime module imports the key loader. A test pins this.

---

## 4. The grader (D10-D11)

| Step | Who | Output |
|---|---|---|
| 1. Verify the run: v4 model `validate`, chapter `COMPLETE` (or the reasons recorded), sidecar `VERIFIED`, recording hashes equal the key's `sources` | code | refuse, or a stamped packet |
| 2. Project claims (§2) from the sealed model | code, pure, deterministic | `paper_evidence.json` |
| 3. Subject mapping, key object → solver subject: EXACT geometry, then COMPOSITE (cell counts sum exactly), then UNMATCHED | code proposes, **human confirms** | mapping sheet |
| 4. Exact join on `(level, family, kind, mapped subject, predicate, object, scope)` and accepted alternatives | code | `JOINED_EXACT` pairs |
| 5. Semantic verdict for every claim not settled by step 4 | **human, non-author; at least one game blind** | CORRECT / WRONG / UNVERIFIABLE per claim |
| 6. `MISSED` = required key items with no acceptable claim | code from joins plus verdicts | |
| 7. `INVENTED` = a positive admitted claim the human rules has no basis. A declared gap is never `INVENTED`. | code lists, **human rules** | |
| 8. Tabulate by game × level × family × kind × executor × admission × certification; refusals and declared unknowns counted | code | `grade_report.json`, `paper_report.md` tables |
| 9. Completeness: every claim and every required item has exactly one grade; non-zero exit otherwise | code | exit status |

Ported discipline:
- `grade_continuity_key.py`: hash refusal, one machine-readable report, failing exit.
- `claim_decomposer.py`: the code surfaces claims and leaves the verdict column empty.
- `foundation_grade.py`: the mapping passes, and the asymmetry rule that a key-untested item against a solver-witnessed one is a key-coverage gap, not WRONG.

**Category questions still open** (beyond the rulings):
1. Can a GAP claim be WRONG (the key holds the fact the solver declared unknown), or only CORRECT and insufficiently specific?
2. Does a `CLOSED_WITHOUT_FINDING` closure count toward MISSED when the key requires the law the closure did not reach?

---

## 5. Artifacts and where they are written

| Artifact | Written by | When | Notes |
|---|---|---|---|
| `paper_evidence.json` | a pure projector from the sealed v4 model | offline tool, and optionally beside `world_model.json` at H2 | Deterministic. Embeds the model's `content_sha256`; refuses a live or unsealed model, like `world_report.md`. |
| `paper_report.md` | a renderer of `paper_evidence.json` | offline | The fixed shape: self · time · response · players (declared unknown) · model · value. Three line kinds by executor and admission. Never parsed by the grader. |
| `grade_report.json`, verdict sheet | the grader | offline, after the key is frozen | Never written by a runtime module |

Writing `paper_evidence.json` at H2 would add work to the 0.5 s ceiling (measured 0.251 s on the Mac). The projection's cost has not been measured; offline-only avoids the question.

---

## 6. Decisions for Sol (D15-D22)

| # | Decision | Options | Evidence | Altitude |
|---|---|---|---|---|
| **D15** | **F-A: where product content and graded outcomes come from** | **(a)** schema v5: a per-level `products` chapter holding each active product's payload, verified against a **strict** replacement for `payload_sha256` (F-C), plus graded outcomes as product content; **(b)** project only what v4 holds: proposals from answers, roles, patterns, gaps, mask. LAW and RELATION content would come from certifying answers, prediction status would be absent, and AUDIT claims would be impossible; **(c)** a hashed sidecar of product payloads (the D1 argument against sidecars applies) | §0 F-A; §1 last row | architecture / Sol (it reopens the schema Sol fixed) |
| D16 | Key subject addressing | entry-frame geometry (`board_sha256` + anchor/bbox/cell_count, optional class); object handle `c<class>@r,c`; both | F-B; tracks carry first-segment geometry; witnesses carry residue runs; some LEVER roles have `identity: UNRESOLVED` and no track | architecture / Sol; usability / Director |
| D17 | `claim_key` contents | as §2 (no `run_stem`); or with `run_stem` | joining keys across runs of one game | architecture / Sol |
| D18 | Scoped nulls | ROLE (no observed effect in the recorded state) or CONDITION | 59 per run on the fixture: they would dominate counts | architecture / Sol |
| D19 | Patterns as claims | one claim per split unit (§2), or only patterns that carry an explanation | 8 patterns on the fixture; NOT_COVERED patterns are observation, not belief | architecture / Sol |
| D20 | GAP grading and closure-vs-MISSED (§4, questions 1-2) | as listed | — | plan wording / Apex via the Director; rules / Sol |
| D21 | Where `paper_evidence.json` is written | offline only; or also at H2 | the H2 ceiling | architecture / Sol |
| D22 | Slicing | one WO-PE-03; or **PE-03a** projection + `paper_evidence.json`, **PE-03b** key schema and validator, **PE-03c** grader and verdict sheet (GRADE-2); `paper_report.md` with 03a or 03c | The key schema must be ratified before the Director can author. The grader needs both. | plan / Sol |

---

## 7. Fail-first plan (for whichever slicing is ruled)

**Projection:**
- determinism: byte-identical output, twice;
- every claim's `refs` resolve in the model;
- `claim_key` is stable as receipts grow;
- one claim per split unit;
- mixed-status patterns split;
- a `GATE_DERIVED` product never yields a LAW or RELATION;
- record-derived relations are `RECORD_DERIVED / SYSTEM`;
- refused answers project with `admission: REFUSED`;
- a field filled by the controller is never attributed to Duck;
- an unparseable refusal becomes one `GAP / OPEN` claim;
- a live or unsealed model is refused.

**Key:**
- schema;
- duplicate `key_id`;
- a source hash mismatch refuses;
- a key committed after first report access is refused;
- no runtime import of the key loader.

**Grader:**
- an exact join;
- each accepted alternative;
- the mapping passes (EXACT, COMPOSITE, UNMATCHED);
- MISSED only for required items;
- a declared gap is never INVENTED;
- tabulation by every dimension;
- an incomplete sheet exits non-zero;
- a model that is not `COMPLETE` is graded only with its reasons stamped.

**Fixture need (F-D):** one offline run with Duck-admitted and Duck-refused answers and at least one graded G4-B or G4-C prediction.

---

## 8. Ground read for this sweep

**At `e158057`:**
- `library_census.py` (`_receipts`, `_payload_sha256`, `compile_level`);
- `world_description.py` (`describe_world`, `_laws`, `_dossiers`, `_questions`);
- `world_model_v2.py`;
- `provenance_chapter.py`, `answer_shapes.py`, `product_origins.py`;
- `gate_artifacts.record_gate_answer`.

**Documents:**
- `THESIS_v1`;
- `RULINGS_PAPER_EVIDENCE_v1`;
- `INTERFACE_DECISIONS_PAPER_EVIDENCE_v1`;
- `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_v1` §5-§8;
- Sol's sweep §5-§10;
- `BUILD_PLAN_PAPER_EVIDENCE_v1` §0-§2.

**Prior art:**
- `virelai_v4/weave/claim_decomposer.py`;
- `virelai_v4/diagnostics/foundation_grade.py` (`map_foundation`, `grade_tag`, `grade_role`).

**Measured:** the real controller run's sealed v4 model (the revision-3 representative artifact, byte-identical to revision 2), read through `describe_world`.

— Claude, Alpha build seat, 2026-10-15

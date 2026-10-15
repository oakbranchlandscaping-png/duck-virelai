# Rulings: the paper-evidence layer

**Type:** `RULINGS_PAPER_EVIDENCE` · v1 · 2026-10-14
**Ruled by:** Sol (supervisor and reviewer), on the WO-PE-00 sweep; conveyed by the Director
**Recorded by:** Claude (Alpha build seat). This document only records the rulings; the build seat ruled nothing.
**Answers:** `INTERFACE_DECISIONS_PAPER_EVIDENCE_v1_2026-10-14.md` (D1-D14)
**Evidence:** `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_v1_2026-10-14.md` (accepted) and Sol's parallel sweep
**Base:** `ring9-unified` at `a925d7f`

**On the sweep:**
- It is accepted.
- Historical refusal counts remain diagnostic lower bounds.
- State v9 is corrected to 16 untracked entries.

---

## Provenance capture (WO-PE-01 builds these)

### D1 · Storage: A+B

1. Events are captured immediately in an **append-only provenance journal**.
2. **In the next slice** (WO-PE-02), the validated journal is absorbed into `world_model.json` schema v4, and the journal's hash is stamped into the canonical model.

WO-PE-01 builds the journal, its writer, reader and validator. **It does not introduce schema v4.**

**The journal must be:**
- deterministic and hash chained;
- able to detect a truncated tail, a missing row, a duplicate sequence and an altered row;
- free of any wall-clock value in hashed semantic content.

### D2 · Vocabulary: one normalized vocabulary across all gates

| Dimension | Values |
|---|---|
| Operation kind | `PROBE`, `ANSWER`, `G3_SELECTION`, `ANNOTATION` |
| Event kind | `OPPORTUNITY`, `ADMISSION`, `EXECUTION` |
| Disposition | `OFFERED`, `ADMITTED`, `REFUSED`, `EXECUTED`, `NOT_ATTEMPTED`, `SUPERSEDED`, `UNCERTIFIED` |

- Only valid combinations may pass validation.
- The existing G3 vocabulary is **not replaced**. Its relevant events are translated into this common audit vocabulary.

### D3 · Capture points

All six admission points named by WO-PE-00 are instrumented:
1. Duck probe;
2. controller probe;
3. Duck answer;
4. controller answer;
5. G3 selection;
6. annotation or note submission.

**What each must produce:**
- Every submitted probe or answer produces one `ADMISSION` row, including refusals.
- Every admitted probe that reaches the environment also produces an `EXECUTION` row.
- A G3 handoff that receives no selection records an `OPPORTUNITY / NOT_ATTEMPTED` row.

### D4 · Answer authorship

**Every answer retains:**
- the exact normalized submitted payload, **before** certified fields are filled;
- the effective payload given to validation;
- a field-source map using `SUBMITTER`, `CONTROLLER_FILLED` and `SUBMITTER_CONFIRMED_BY_CONTROLLER`.

The row's executor names the submitter. Gate certification remains a separate dimension. **An accepted Duck answer is never represented as wholly Duck-authored** when the controller supplied or verified certified fields.

---

## The claim contract (recorded; implemented in WO-PE-03)

### D5-D8

- **Predicate families:** `ROLE`, `TRANSFORMATION`, `RELATION`, `LAW`, `PREDICTION`, `CONDITION`, `GAP`.
- **Two identities:**

  | Identity | Definition |
  |---|---|
  | `claim_key` | Hash of the semantic proposition, **excluding** evidence, status and executor |
  | `assertion_id` | Hash of the `claim_key` plus its provenance event |

- **Mixed-status material** is split into separate atomic assertions.
- **Executor enum:** `DUCK`, `CONTROLLER`, `SYSTEM`.
- **Certification and admission** remain separate dimensions.

---

## Later evidence work (recorded)

### D9-D14

**Keys:**
- Keys are structured JSON, authored independently by the Director.
- Keys include construction metadata, source recording hashes, required versus optional items, and accepted alternatives.

**Joins:** exact joins run first. `EXACT`, `COMPOSITE` and `UNMATCHED` mappings require human confirmation.

**Grade meanings:**

| Grade | Meaning |
|---|---|
| `CORRECT` | The proposition agrees with the key. |
| `WRONG` | The proposition contradicts the key. |
| `UNVERIFIABLE` | The available evidence or key cannot decide it. |
| `MISSED` | A required key fact has no acceptable emitted claim. |
| `INVENTED` | A positive emitted claim has no factual basis, after human review. |

**Grading rules:**
- **Propositions and audit statements are graded separately.** A contradicted Duck prediction is `WRONG`; the later statement that it was contradicted can be `CORRECT`.
- **Refused but interpretable proposals stay in the grading denominator.** Contract-invalid content is normally `UNVERIFIABLE`.

**Runs and artifacts:**
- Historical runs are **diagnostic only**. Formal grading uses new provenance-complete runs.
- The v3 reader remains supported when schema v4 arrives.
- `world_report.md` stays the semantic library report. The separate future artifacts are `paper_evidence.json` and `paper_report.md`.

---

## Defects carried into WO-PE-01

These are in scope because they directly affect provenance completeness:
1. **Flush pending G3 selection events** at every normal end, controlled stop, budget stop and handled crash.
2. **Stop hardcoding `DUCK`** on the controller-capable lifecycle answer path. Pass the real executor from the call site.

The other six WO-PE-00 findings are **not** repaired in WO-PE-01, unless a fail-first provenance test proves that one blocks the journal contract.

## Sequence after acceptance

1. WO-PE-01: provenance capture
2. WO-PE-02: schema-v4 absorption and provenance completeness
3. WO-PE-03: atomic claim projection
4. Director-authored keys
5. The grader
6. The formal current-source public-25 evidence run

— recorded by Claude, Alpha build seat, 2026-10-14

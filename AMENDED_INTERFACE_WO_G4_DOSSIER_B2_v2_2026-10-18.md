# INTERFACE — WO-G4-DOSSIER-B, slice B2: library-selected study · v2 · 2026-10-18 (amended for revision 2)

- **Supersedes:** `INTERFACE_WO_G4_DOSSIER_B2_v1` where they differ. Everything not named here stands as filed.
- **Authority:** Sol's review of B2 revision 1. It accepted the core G4-A path, the no-choice golden, the `OPEN_NOT_ACTIONABLE` limits rows and the level-wide relations and law questions. It raised two blockers and made three rulings.

## 1 · G4.1 is controller work; G4-A is the only live G4 choice (blocker 1)

**What revision 1 did** (`blocker1_on_rev1.txt`). `virelai('next_probe', question_id='Q:L1:G4-REACTIONS:E0060:EFFECTS')`:

- recorded `ADMITTED E0060`;
- left the choice bound;
- replied "No probe is admissible now."

G4.1 never issues a probe: its anatomy answers are controller-rendered, and Duck holds no G4.1 turn.

**Revision 2:**

| Element | Behaviour |
|---|---|
| `g4_selection.ADMITTING` | `{G4-A}` only. |
| G4.1 candidates | Still listed, head first, none selectable. The agenda keeps each lever's anatomy question and selects the controller's head. G4.1 questions never join `eligible`. |
| A G4.1 choice | Refused with "G4.1 anatomy is controller work: the controller answers each lever in coverage order, and no Duck choice is admitted". The refusal is recorded once (`REFUSED`), and the G4.1 gate state is unchanged. The tool's reply carries that error and the current question. |
| G4.1 gate hooks | All removed. `_current_entity` and `submit_answer` are back to `0119a74`, as is `_ReactionTarget.__init__`. |
| Ordering | G4.1's answer order and product are the golden's. |

## 2 · The audit extension is schema v2; v1 is frozen (blocker 2)

### 2.1 The audit journal (`audit_journal.py`)

| | v1 (frozen) | v2 (the writer's) |
|---|---|---|
| `schema` | `virelai-provenance-v1` | `virelai-provenance-v2` |
| Vocabulary | `VALID_V1`, `REASON_CODES_V1` (exactly `0119a74`'s) | v1 plus operation `G4_SELECTION` (`ADMISSION`: `ADMITTED` / `REFUSED` / `SUPERSEDED`; `EXECUTION`: `EXECUTED`) and reason `G4_EVENT` |
| Readers | `read_journal_v1`, `read_journal_bytes_v1`, `verify_embedded_v1`: a v2 row is `CORRUPT` / `SCHEMA_INVALID`, never reinterpreted | `read_journal`, `read_journal_bytes`, `verify_embedded`: read v1 or v2, each row under its own schema's vocabulary |

**Rules:**

- A journal never mixes schemas. Its first row fixes the schema, and every later row and the seal must match.
- A new journal is written as v2.
- An OPEN journal is continued in its own schema. A G4 row offered to a continued v1 journal fails the writer, and nothing is written.

### 2.2 The world model that embeds it (the required measurement)

**Finding.** A sealed H2 model embeds the journal's rows verbatim, including each row's `schema`. `provenance_chapter._validate_h2` re-verifies them through `audit_journal.verify_embedded`. The audit schema is therefore part of the chapter contract, and through it part of the world-model contract: a v7 model holding v2 rows would be rejected by `0119a74`'s reader.

**Bump:**

- The world model becomes **v8**, and its provenance chapter **`virelai-provenance-chapter-v2`**. Chapter v2 embeds an audit-v1 or audit-v2 journal.
- **v7 is frozen** (`validate_v7`; `read_world_model` dispatches it): chapter v1, audit-v1 rows only, through the frozen v1 reader.
- v4–v6 keep chapter v1 and the frozen v1 reader as before.
- Nothing else in the model changes.

### 2.3 Compatibility table

| Artifact | Written by | Read by revision 2 | Read by `0119a74` |
|---|---|---|---|
| Audit v1 journal | `0119a74` and earlier | Byte for byte, under both the v2 reader and the frozen v1 reader (`test_pv2_02`) | Yes |
| Audit v2 journal | B2 revision 2 | Yes (v2 reader) | Refused (`SCHEMA_INVALID`); never reinterpreted (`test_pv2_03`) |
| Mixed-schema journal | — | Refused, "a journal never mixes schemas" (`test_pv2_04`) | — |
| World model v7 (chapter v1, audit-v1 rows) | `0119a74` | `validate_v7`; bytes unchanged (`test_pv2_06`) | Yes |
| World model v8 (chapter v2, audit-v2 rows) | B2 revision 2 | `validate` (`test_pv2_07`) | Refused by schema |
| World model v8 (chapter v2, audit-v1 rows) | B2 revision 2, from an older journal | `validate`, rows under v1's vocabulary (`test_pv2_08`) | Refused by schema |
| v8 content relabelled v7 | — | `validate_v7` refuses its v2 rows (`test_pv2_07`) | — |

**Fixtures** were written by `0119a74` code before any revision-2 edit:

- `tests/fixtures/provenance_v1_journal.jsonl`: probe admission and execution, an answer and a G3 selection;
- `tests/fixtures/world_model_v7_frozen.json`: a sealed H2 v7 model embedding that journal.

## 3 · The question-to-dossier proof (ruling: no stored field)

- **`g4_selection.dossier_question(level, entity, chapter)`** derives a chapter's question: `anatomy` → `Q:L{n}:G4-REACTIONS:{E}:EFFECTS`, `orbit` → `Q:L{n}:G4.2-LEVER-ORBITS:{E}:ORBIT`.
- **`g4_selection.question_problem(...)`** returns None only when all of these hold:
  - every `ADMITTED`, `STALE` or `FINISHED` selection of that lever's chapter names the derived question;
  - every selected-run receipt the chapter cites names it;
  - a `FINISHED` choice has at least one receipt the chapter cites.
- **`test_b2_11`** shows the derived question equals the admitted selection, every run receipt and the completed chapter's question. The receipts' evidence ids are exactly the chapter's `evidence_refs`, and these are unchanged. A forged receipt, a forged selection and a missing receipt are each reported.

## 4 · Retained unchanged

All of these stand as in revision 1:

- G4-A choices happen only on a turn Duck already holds;
- the obligation of a run under way wins;
- a decline, timeout or no choice leaves controller coverage byte-identical (both goldens);
- a stale choice resumes clean coverage;
- relations and law stay level-wide;
- limits rows stay visible and non-actionable;
- no controller wait is introduced.

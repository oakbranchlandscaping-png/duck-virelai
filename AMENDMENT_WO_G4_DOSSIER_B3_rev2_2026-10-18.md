# AMENDMENT — WO-G4-DOSSIER-B3, revision 2 · 2026-10-18

- **Amends:** `INTERFACE_WO_G4_DOSSIER_B3_v1` §1 (schema), §3 (the contract's home), §5 (the persisted checks) and §8.1. Everything else stands, including the revision-1 behaviour Sol accepted.
- **Authority:** Sol's review of B3 revision 1 (three blockers). The runtime scope is unchanged.

## 1 · The recorded terminal outcome is validated (blocker 1)

**The finding.** In revision 1, a G4-B experiment's `FINISHED` audit row carried no reason: v2 translates a reason only for `REFUSED`, `NOT_ATTEMPTED` and `SUPERSEDED`. The validator recomputed the evidence pattern, but nothing named a type it could compare against. A finished row with any reason added was therefore accepted: `REVERSAL_OBSERVED` relabelled `CAPPED`, a persistence type on a reversal, an interruption on a finish.

**The writer.** A G4-B experiment's `FINISHED` row now keeps its reason, `TYPE: detail` (`audit_journal.translate_g4_event`). The audit journal stays **v2**:

- the row shape is unchanged (every row already has `reason`);
- the code is the existing v2 code `G4_EVENT`;
- v2's `check_content` already allows a reason on any disposition.

G4-A rows are unchanged.

**The validator** (`lever_experiment_check`), for every closed G4-B experiment:

| Check | Rule |
|---|---|
| The type | Parsed explicitly from the close's reason (`lever_experiment_contract.terminal_type`). |
| Event and kind | `FINISHED` takes one of its kind's finished types: REVERSAL → `REVERSAL_OBSERVED`, `RECURRENCE_OBSERVED`, `CAPPED`; PERSISTENCE → `PERSISTENCE_UNCHANGED`, `PERSISTENCE_CHANGED`, `PERSISTENCE_INCONCLUSIVE`. `STALE` takes a typed interruption only. A close naming no type, the other kind's type, or the other event's type is refused (`admits`). |
| Recomputation | Applies where the subject's observations are `OBSERVED` for the experiment's level and life. The recorded type must equal the recomputed one. |
| Reversal | The return cited at the last step, cycle 2 → `REVERSAL_OBSERVED`; cycle > 2 → `RECURRENCE_OBSERVED`; no return and the cap reached → `CAPPED`. |
| Persistence | `PERSISTENCE_INCONCLUSIVE` when the acting lever's own region did not change in the transition's recorded pixel rewrite (the acting lever is the one whose G4.1 intervention is the transition's action; its region is its LOCAL anatomy cells). Otherwise `PERSISTENCE_CHANGED` or `PERSISTENCE_UNCHANGED`, as the observations count the trial. |
| Failed-closed or later-life observations | They give no positive finding, so no outcome is recomputed; the type must still fit the event and kind. |

The receipt and observation checks of revision 1 are kept as they were.

## 2 · World model v9; v8 frozen (blocker 2)

| Reader | Contract |
|---|---|
| `validate` (writer: `virelai-world-model-v9`) | The v8 rules, plus the complete G4-A chain and the G4-B experiment chain |
| `validate_v8` (frozen) | Exactly B2's: provenance chapter v2 (audit v1 or v2) and the G4-A chain only. A G4-B row is "not G4-A's", and the experiment check never runs. |
| `read_world_model` | v1–v9, each under its own rules; anything else is refused |

- **v8 refuses a v9 artifact at the schema boundary.** The same artifact relabelled v8 and rehashed is refused by v8's own rules.
- **The frozen fixture.** `tests/fixtures/world_model_v8_frozen.json` was written by `ef8289d` code before any B3 edit. Its provenance is in `V8_FIXTURE_PROVENANCE.md`.
- **The audit journal stays v2** (§1).

## 3 · The persisted contract module (blocker 3)

**`lever_experiment_contract.py`** (new; 67 physical lines, 36 executable) owns:

- the kinds and caps;
- the finished types by kind, and the stale types;
- `experiment_id`, `parse` and `question`;
- `terminal_type` and `admits`.

**Who imports it:**

- `lever_experiments` (the engine) imports it and re-exports the names;
- `lever_experiment_check` imports only the contract.

**The engine is never loaded to validate.** In a fresh process, reading a v9 B3 artifact loads the contract and never the engine (`test_t2_12`).

**Physical lines:** `lever_experiments.py` is 501 → 472.

## 4 · Revision-1 behaviour is unchanged

No runtime path changed:

- the planner, offer, admission, steps, closes and agenda;
- the card;
- the dossier derivation;
- replay.

The only runtime-adjacent change is the audit translation of a G4-B finished row (§1). Both goldens are byte-identical.

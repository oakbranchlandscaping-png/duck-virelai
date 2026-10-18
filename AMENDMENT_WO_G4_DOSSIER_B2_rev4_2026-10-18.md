# AMENDMENT — WO-G4-DOSSIER-B, slice B2, revision 4 · 2026-10-18

- **Amends:** `AMENDMENT_WO_G4_DOSSIER_B2_rev3` §2.2 (the rules) and the G4 selection writer. Everything else stands.
- **Authority:** Sol's review of revision 3. Two forged, fully rehashed v8 models were accepted:
  - an open `ADMITTED` choice with a wrong question;
  - a `FINISHED` choice moved to another life.
- **No schema bump.** The stored row shape is unchanged. Audit v2 and world model v8 stay the writers; audit v1 and world model v7 stay frozen.

## 1 · The selection log as a state machine (`lever_dossier_selection._log`)

| Row | Rule |
|---|---|
| **Any G4 row** | Its audit `event`/`disposition` must fit its source event: `ADMITTED` → `ADMISSION`/`ADMITTED`, `REFUSED` → `ADMISSION`/`REFUSED`, `STALE` → `ADMISSION`/`SUPERSEDED`, `FINISHED` → `EXECUTION`/`EXECUTED`. |
| **`ADMITTED`** | Checked at once, open or not, at any stop (run end, budget stop, controlled stop, crash). It must be G4-A's, on a level the model holds, about a lever with a dossier there, and name the question derived from level, G4-A, lever and `ORBIT`. It opens the one choice of its level and gate: a second `ADMITTED` while one is open is refused. A valid admission may stay open. |
| **`STALE`, `FINISHED`** | Must close the open choice of its level and gate, matching it on **level, life, gate, executor, subject and question**. An orphan close is refused. |
| **`FINISHED`** | Revision 3's chapter rule still holds: the lever's orbit chapter cites at least one receipt of that admission's selected run. |
| **`REFUSED`** | Opens and closes nothing. |

Revision 3's other rules stand unchanged:

- every orbit evidence reference resolves;
- a cited selected-run receipt names its chapter's own lever;
- ordinary coverage needs no selection.

**On the one open choice per level and gate.** Sol's wording is one choice per level, life *and* gate. The validator holds the gate to one open choice per level whatever the life, as the writer does: a choice made stale by a death is closed before another can be admitted. A close must still match the admission's life exactly.

## 2 · The writer (`g4_selection`)

1. **A close is scoped to the choice it closes.** `STALE` and `FINISHED` rows take their level, life and gate from the admission, even when a death or a level change closed the choice. `at_transition` stays the transition at which it closed. `ADMITTED` and `REFUSED` are scoped where the machine is now.
2. **A level change closes an open choice.** `_advance_level` now calls `close_at_level_change` before the level is censused: `FINISHED` if the run reached its endpoint, else `STALE` "the level changed". Before, the old level's adapter was dropped and its choice left open forever.
3. **Found by the new validator: an off-choice action carried the choice's identity.** While a choice stood, every G4-A envelope was bound. If Duck pressed another lever, or a rerun did, that press was recorded with the choice's probe id (`…:SEL:E0057:…`) and question. Its receipt then named a choice it did not serve. `admitted_action` (one line in `validate_probe`'s guided branch) now restores the coverage probe id and drops the selection keys unless the admitted action is the chosen lever's click or a NAV step naming it. `writer_defects_on_rev3.txt` shows both defects on revision 3 and their fixes.

## 3 · Canonical-artifact attacks and genuine artifacts

Each forged artifact is re-chained by the real audit writer, rebuilt through `provenance_chapter.h2` / `attach` and the dossier reconciliation, rehashed, and read by `read_world_model`.

| Test | Artifact | Revision 4 | Revision 3 |
|---|---|---|---|
| `r4_01` | A valid open admission at a budget stop | accepted | accepted |
| `r4_02` | An open admission with a forged question, no `FINISHED` | **refused** | accepted |
| `r4_03` | An open admission naming G4.1, an unheld level, or a lever with no dossier | **refused** (each) | accepted |
| `r4_04` | `FINISHED` in another life | **refused** ("its life differs") | accepted |
| `r4_05` | `FINISHED` by another executor | **refused** ("its executor differs") | accepted |
| `r4_06` | A second `ADMITTED` while the first is open; then the same with a `STALE` close first | **refused**, then accepted | accepted |
| `r4_07` | An orphan `STALE` | **refused** | accepted |
| `r4_08` | A genuine death-triggered `STALE` | accepted; the row keeps level 1 / life 1, closing at a life-2 transition | The row said life 2, and Duck's press of E0054 carried E0057's SEL id |
| `r4_09` | A `FINISHED` source event on an admission row | **refused** | accepted |
| `r4_10` | A level change closing an open choice | `STALE` "the level changed", in its own scope; accepted | No level-change close existed. By reading the code, `_advance_level` never settled the old adapter. |
| `r3_01`–`r3_08` | Revision 3's chain and attacks | unchanged: genuine accepted, forgeries refused | — |

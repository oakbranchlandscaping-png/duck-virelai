# BUILD REPORT — WO-G4-DOSSIER-B, slice B2, revision 4 · v4 · 2026-10-18

- **Seat:** Alpha (Ring 9). **Base:** `0119a74`.
- **Supersedes:** `BUILD_REPORT_WO_G4_DOSSIER_B2_v3` for the selection log and writer. Everything else in v2 and v3 stands.
- **Design:** `AMENDMENT_WO_G4_DOSSIER_B2_rev4`.
- **Status:** built in the sandbox, uncommitted. T2, the commit and B3 are held for Sol.
- **Game-free:** record names appear only as fixture labels.

## 1 · Verdict

The focused persisted-selection and provenance tests ran first: 27 passed (`test_g4_selection_persisted` and `test_provenance_v2`; `focused_b2r4.txt`). Then:

| Run | Revision 4 | Revision 3 |
|---|---|---|
| T0 `g4-selection` | **47 passed**, 60.2 s | 37 |
| T0 `g4-dossier` | **70 passed**, 19.9 s | 70 |
| T1 `g3-directed` | **178 passed**, 413.5 s | 168 |
| T1 `description` | **302 passed**, 336.1 s | 302 |
| T1 `paper-evidence` | **490 passed**, 521.3 s | 480 |
| Manifest `--check` | exit 0; T2 = **1215**, exactly the snapshot | 1205 |

Snapshot changes:

- against `0119a74`: +43 tests, 0 removed;
- against revision 3: +10 tests, 0 removed.

Both no-choice goldens are byte-identical: G4 `fe60d718…` and G3 `d9e08bd7…`.

## 2 · Revision delta (`WO_G4_DOSSIER_B2_rev3_to_rev4.patch`, 5 files)

| File | Change |
|---|---|
| `lever_dossier_selection.py` | The selection log as a state machine (`_log`, `_admission_problem`, `_mismatch`). Every `ADMITTED` row is validated at once, at any stop. A close matches its admission on level, life, gate, executor, subject and question. No second admission opens while one is open, and no close is orphaned. Each row's audit event and disposition fit its source event. `_completed` keeps only the chapter rule. 107 executable lines; largest function `_log`, 28. |
| `g4_selection.py` | `note` scopes `STALE` and `FINISHED` to the admission (level, life, gate), with `at_transition` as the closing transition. Adds `close_at_level_change` and `admitted_action`. |
| `virelai_gates.py` | Two delegation lines: `_advance_level` calls `close_at_level_change`; `validate_probe`'s guided branch calls `admitted_action`. Total +13 against `0119a74`. |
| `tests/test_g4_selection_persisted.py` | `r4_01`–`r4_10` |
| `tests/tiers/T2_collected.txt` | +10 |

No schema bump: the stored row shape is unchanged. Audit v1 and world model v7 stay frozen; their code is unchanged since revision 2.

## 3 · Sol's items

| Item | How it is met |
|---|---|
| 1 · Every admission validated immediately, open or not | `r4_02`, `r4_03` (gate, level, lever, question); `r4_01` (a valid open admission at a budget stop is accepted) |
| 2 · The state machine | `r4_06` (second admission; the `STALE`-first variant accepted); `r4_04` (life); `r4_05` (executor); `r4_07` (orphan `STALE`); `REFUSED` is ignored by the machine; `r4_09` (event/disposition fit) |
| 3 · Closing context in the writer | `r4_08`, a real death then reset: the `STALE` row keeps level 1 / life 1, and `at_transition` is the life-2 transition. Also `r4_10` (level change). |
| 4 · Fail-first canonical-artifact attacks | §4 |
| 5 · Revision-3 behaviour preserved | `r3_01`–`r3_08` unchanged and passing; both goldens; ordinary coverage (`r3_02`); no new Duck turn |

**Found by the new validator while building item 3: a writer defect.** While a choice stood, every G4-A envelope was bound. So a press of another lever was recorded with the choice's probe id and question. In `r4_08`, Duck's press of E0054 carried `…:SEL:E0057:…`. `admitted_action` unbinds such an action back to its coverage probe id and envelope. `writer_defects_on_rev3.txt` shows this defect and the life-scope defect on revision 3, and their fixes.

## 4 · Fail-first on revision 3

**`failfirst_b2r4_on_rev3.txt`: 9 failed, 1 passed.**

| Result | Tests | Why |
|---|---|---|
| Failed: `read_world_model` accepted the forged artifact | `r4_02`–`r4_07`, `r4_09` | No state-machine checks |
| Failed | `r4_08` | Off-choice press carried E0057's SEL id; the `STALE` row was scoped to life 2 |
| Failed | `r4_10` | No `close_at_level_change` |
| Passed (guard) | `r4_01` | A valid open admission was already accepted |

**`SEMANTIC_EXAMPLE_WO_G4_DOSSIER_B2_r4.json`** gives the revision-4 verdict for every `r3` and `r4` artifact: each genuine one accepted, each forgery refused with its message. It also includes the open admission at a budget stop.

## 5 · Honest ledger

1. **One open choice per level and gate, whatever the life.** This is stricter than "per level, life and gate", and it matches the writer (amendment §1). A close must still match the life exactly.
2. **The level-change close is proven by a direct call.** No committed record changes level while a G4-A choice stands. The call site is one line in `_advance_level`, before the level's census.
3. **Unchanged from revision 3:**
   - the selected-run prefix assumes one journal covers the game;
   - a model with no H2 rows has nothing to pair;
   - no live model has made a G4-A choice yet;
   - the NAV route is proven on a stub only.

## 6 · Package (`runs/_cowork_xfer/g4dossierB/b2/rev4/`)

| File | Contents |
|---|---|
| `WO_G4_DOSSIER_B2_on_0119a74.patch` | 29 files; applies to `0119a74`; byte-identical to the tree |
| `WO_G4_DOSSIER_B2_rev3_to_rev4.patch` | 5 files |
| `WO_G4_DOSSIER_B2_slice.tar`, `SLICE_SHA256SUMS` | the 29 files |
| `AMENDMENT_WO_G4_DOSSIER_B2_rev4_2026-10-18.md`, `NOTE_SHARED_FILE_WO_G4_DOSSIER_B2_2026-10-18.md` | the amendment and the amended shared-file note |
| `failfirst_b2r4_on_rev3.txt`, `writer_defects_on_rev3.txt`, `probe_writer_rev3.py` | fail-first evidence |
| `tiers/`, the manifest check, both T2 diffs | test evidence |
| `SEMANTIC_EXAMPLE_WO_G4_DOSSIER_B2_r4.json`, `examples_b2r4.py` | the example and its script |
| `PACKAGE_SHA256SUMS` | checksums of the whole package |

If the Director commits, the trailer is:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01K95ngAHgc1pWqpMXMj7cim
```

# BUILD REPORT — WO-G4-DOSSIER-B, slice B1, revision 2 · v2 · 2026-10-18

- **Seat:** Alpha (Ring 9). **Base:** `87639d7`. **Supersedes:** `BUILD_REPORT_WO_G4_DOSSIER_B1_v1` for everything below; v1 stays the record of revision 1.
- **Authority:** Sol's B1 review (schema v7 approved; revision 1 held for three fixes).
- **Status:** built in the sandbox, uncommitted. T2, commit, Kaggle and B2 are held. B2 stays held until B1 passes the Mac T2 floor and is committed.
- **Scope:** no gate, agenda, selection or controller file changed. Game-free: record names appear only as fixture labels.

## 1 · Verdict

| Run | Revision 2 | Revision 1 |
|---|---|---|
| T0 `g4-dossier` | **70 passed**, 21.2 s | 65 passed |
| T1 `description` | **302 passed**, 369.3 s | 295 passed |
| T1 `paper-evidence` | **462 passed**, 511.3 s | 455 passed |
| Manifest `--check` | exit 0; T2 = **1172**, exactly the snapshot | 1165 |

Against `87639d7` the T2 snapshot gains 21 tests and loses none. Against revision 1 it gains 7; b1_04 is renamed (its reset half changed by ruling, §2.1).

## 2 · The three fixes

### 2.1 Reset no longer leaks across lives

Revision 1 skipped a reset row as a trial but still carried the state before it. The board the death left became the life's first state, so a later press back to it read as a reversal.

| Case | Revision 2 behaviour |
|---|---|
| The life opens with a reset row (`LifeRecord.reset()` assigns it to the new life) | The board **after** the reset is the entry board. The row is dropped from the interventions and from every return path. `scope.entry_reset` names it. |
| A reset anywhere else in the life | Observations fail closed: `FAILED_CLOSED / RESET_INSIDE_LIFE`, refs = the reset transition ids. Nothing is skipped. |

**Validator:**

- `entry_reset` must be a recorded reset (`record.reset_transition_ids`).
- It must be exactly the reset that opens the scope's life, and it must be named whenever that life opens with one.
- No reset may be cited as a trial or a reading.
- `RESET_INSIDE_LIFE` must name recorded resets of the scope's life, never its opening reset.

**Sol's fail-first case, `test_b1_15`.** A stub record holds four transitions:

1. t1, life 1: a press leaves lever A in state 5.
2. t2: a death.
3. t3: a reset opens life 2 with A in state 7.
4. t4: one press turns A back to 5.

Revision 2 reads life 2 as S0 → S1: a **new state**, with toggle tested once and NOT_OBSERVED. Revision 1 reported a toggle reversal (t4 "returned" to life 1's state).

**Recomputed ft09 life-2 findings.** The described record dies at t88 and its reset t89 opens life 2.

| Lever | Revision 1 | Revision 2 |
|---|---|---|
| E0053 | toggle OBSERVED (the leak) | toggle NOT_OBSERVED (tested 1); `LIMITS_REVERSAL` **owed** |
| E0054, E0055 | reversal owed | reversal owed (unchanged) |
| E0056, E0057, E0060–E0062 | toggles observed, exact phase | the same, now cited from entry t89 |

The B3 candidate set from real records was `{E0054, E0055}`. It is now **`{E0053, E0054, E0055}`** — each pressed once in life 2, with no return seen. The set was not preserved. Persistence is unchanged: 27/27 and 23/23.

### 2.2 The limits basis now matches its open items

`lever_dossier_facts.limits_basis` derives the basis:

| Condition | Basis | Status |
|---|---|---|
| Either field is owed (`PROBE_OWED`) | `ENDPOINT_OBSERVED_PROBES_OWED` | IN_PROGRESS |
| Both fields are observed and no limits probe remains | `RECORD_OBSERVED_NOT_GATE_CERTIFIED` (new, in `BASES["IN_PROGRESS"]`) | IN_PROGRESS (R5: no product certifies limits) |

**Where it is computed.** `_seal → _observe_limits` computes the basis at every seal, so it follows the observations both ways:

- if the observations later fail closed, the basis reverts to the owed basis (`test_b1_18`);
- a census label keeps the right `prior_basis` (the carry level E0004 is `CLOSED_UNRESOLVED / LEVEL_ENDED` with prior `RECORD_OBSERVED_NOT_GATE_CERTIFIED`).

**Validator.** It pins the basis, or `prior_basis` under a label, to `limits_basis(observations)`. A v6 dossier may never carry the new basis.

**For B2:** `RECORD_OBSERVED_NOT_GATE_CERTIFIED` is **incomplete but non-actionable**. Selection must not choose limits on it, and it must not block relations (ruling 5).

**Tests and the changed assertion:**

- `test_b1_17` pins the pure derivation and the t80 E0053 chapter.
- `test_b1_18` pins the validator and the revert.
- `test_v6_03_27` (case 3/27) changed by this ruling: E0053 at t80 now reads `IN_PROGRESS / RECORD_OBSERVED_NOT_GATE_CERTIFIED`, where it read `ENDPOINT_OBSERVED_PROBES_OWED` with nothing owed.

### 2.3 Every observations line cites its own observations

Every `dossier E observations:` report line now cites `levels[i].lever_dossiers[E].observations`, plus up to three representative evidence ids.

**The reference checker** (`tests/test_world_description._resolves` / `_assert_report_refs`):

- resolves the keyed path in the sealed model;
- requires that path on every observations line;
- refuses a path for another lever (by the line's subject), for another level (by the section), or for a lever that does not exist.

**Persistence-only case (`test_b1_20`).** The ft09 life-2 record has three such levers (E0053–E0055): persistence 27/27, no changed trial, no reversal case. Revision 1 cited only the entity id for them; their claim had no support.

**`test_b1_21`** forges three wrong paths and one missing path; the checker refuses each.

The line also says where the life began ("life 2 from reset t89"). The rendered lines are in `REPORT_OBSERVATION_LINES_ft09_described.txt`.

## 3 · Fail-first on revision 1

**`failfirst_b1_rev2_on_rev1.txt`: 8 failed.**

| Test | Why it fails on revision 1 |
|---|---|
| b1_04 | The reset is skipped, not failed closed |
| b1_15 | The leak: a toggle case where none exists |
| b1_16 | A mid-life reset is skipped |
| b1_17 | No `limits_basis` |
| b1_18 | A forged owed basis is accepted |
| b1_19 | A forged entry reset and reset failure are accepted |
| b1_20 | No canonical path on the line |
| b1_21 | The checker cannot express or require the path |

**`failfirst_b1_rev2_changed_on_rev1.txt`: 2 failed.** These are the assertions changed by ruling: case 3/27 (basis) and b1_10 (life-2 findings).

`tiers/focused_before_case_3_27_update.txt` keeps the focused run that caught case 3/27 before its assertion was updated.

## 4 · Measurements (`MEASUREMENTS_WO_G4_DOSSIER_B1.json`, re-run)

- **Size:** 6.4–8.9 % of the model; largest level 110.7 KB. Within the 10 % / 128 KiB budget and unchanged from revision 1.
- **Controller path:** unchanged. 0 `attach` calls in 109 replay steps and in 5 controller steps plus cards; 1 at the carry H1 boundary.
- **Latency:** seal 0.16–0.47 s, validate 0.04–0.17 s, live view 0.24–2.06 s, measured while the package was being assembled in parallel. Seal is slower than revision 1's 0.10–0.34 s; part of that is load, and part is the added validator and limits-basis work.
- **Digest:** max 2495 characters, unchanged.

The semantic examples were re-run (`SEMANTIC_EXAMPLES_WO_G4_DOSSIER_B1.json`). The only finding that changed is ft09 life-2 E0053 (§2.1).

## 5 · Ratchet (executable lines; every file and function stays Green)

| File | Rev 1 → rev 2 | Function changes |
|---|---|---|
| `lever_dossier_state` | 215 → 232 | `derive` 41 → 42; `observe` 31 → 35; new `_life_rows` 7, `_is_reset` 2 |
| `lever_dossier_facts` | 313 → 317 | `limits_basis` 3 |
| `lever_dossiers` | 436 → 439 | `_observe_limits` 6 → 9 |
| `lever_dossier_schema` | 353 → 393 | `_entry_reset` 12, `_reset_failure` 9, `_limits_reading` 13 |
| `world_description` | 460 → 461 | — |
| `world_report` | 189 → 191 | — |

The ruff finding in `lever_dossier_facts` (unused `Sequence` import) is already on `87639d7` and is left as it is.

## 6 · Package (`runs/_cowork_xfer/g4dossierB/b1/rev2/`)

| File | Contents |
|---|---|
| `WO_G4_DOSSIER_B1_rev1_to_rev2.patch` | 10 files, +331 −30; applies to revision 1 |
| `WO_G4_DOSSIER_B1_on_87639d7.patch` | 17 files, +1149 −56; applies to `87639d7`; byte-identical to the build tree |
| `WO_G4_DOSSIER_B1_slice.tar`, `SLICE_SHA256SUMS` | the 17 files |
| the fail-first records, `tiers/`, `manifest_check_r2.txt`, both T2 snapshot diffs, measurements, examples, report lines | — |
| `NOTE_SHARED_FILE_WO_G4_DOSSIER_B1_2026-10-18.md` | amended shared-file note |
| `PACKAGE_SHA256SUMS` | checksums of the whole package |

**Next, held for Sol:** the Mac T2 floor on revision 2, then the Director's commit. B2 starts only after that. If the Director commits, the trailer is:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01K95ngAHgc1pWqpMXMj7cim
```

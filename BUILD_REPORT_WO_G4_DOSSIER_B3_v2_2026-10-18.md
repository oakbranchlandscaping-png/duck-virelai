# BUILD REPORT — WO-G4-DOSSIER-B3, revision 2 · v2 · 2026-10-18

- **Seat:** Alpha (Ring 9). **Base:** `ef8289d`.
- **Supersedes:** `BUILD_REPORT_WO_G4_DOSSIER_B3_v1` on the three blockers. Everything else in v1 stands, including the revision-1 behaviour Sol accepted.
- **Design:** `AMENDMENT_WO_G4_DOSSIER_B3_rev2`.
- **Status:** built in the sandbox and uncommitted. Nothing is pushed. T2 and the commit are held for Sol. The runtime scope is unchanged.

## 1 · Verdict

| Run | Revision 2 | Revision 1 |
|---|---|---|
| Fail-first: `test_lever_experiments_r2` on revision 1 | **12 failed** (7 forged closes "DID NOT RAISE"; v9 absent; the engine imported to validate) | — |
| Focused B3 suite: `test_lever_experiments`, `test_lever_experiments_r2`, `test_g4b_relations` | **48 passed** | 36 |
| T0 `g4-selection` | **84 passed**, 179.3 s | 72 |
| T0 `g4-dossier` | **70 passed**, 18.8 s | 70 |
| T1 `g3-directed` | **226 passed**, 591.0 s | 214 |
| T1 `description` | **302 passed**, 307.7 s | 302 |
| T1 `paper-evidence` | **527 passed**, 614.0 s | 515 |
| Manifest `--check` | exit 0; T2 = **1252**, exactly the snapshot | 1240 |

**T2 snapshot changes.** None of them remove a test.

| Against | Added | Removed |
|---|---|---|
| Revision 1 | 12 | 0 |
| `ef8289d` | 37 | 0 |

**Goldens.** Both are byte-identical: G3 `d9e08bd7…` and G4 `fe60d718…`. `test_b3_20` passed in T0 and T1.

## 2 · Blocker 1 — the recorded terminal outcome

**What revision 1 got wrong.** A G4-B `FINISHED` audit row carried no reason, so no recorded type existed to compare against. A forger could add any reason and the model was accepted. On revision 1 the attacks were accepted (`failfirst_r2_on_rev1.txt`).

**The fix:**

- the writer keeps the typed reason on G4-B finished rows (audit v2 unchanged);
- the validator parses the type;
- it requires the type to fit the close's event and the experiment's kind;
- where the observations speak for the experiment's life, it requires the type to equal the recomputed outcome (amendment §1).

Persistence outcomes, including `PERSISTENCE_INCONCLUSIVE`, are recomputed from the transition's recorded pixel rewrite and the acting lever's G4.1 region.

**Each attack changes only the close's reason, then re-chains the journal with the real writer and recomputes every hash:**

| Test | Attack | Revision 2 refuses with |
|---|---|---|
| `t2_02` | reversal → `CAPPED` | "its close records CAPPED, but its evidence shows REVERSAL_OBSERVED" |
| `t2_03` | reversal → `RECURRENCE_OBSERVED` | "… records RECURRENCE_OBSERVED, but its evidence shows REVERSAL_OBSERVED" |
| `t2_04` | persistence unchanged → changed | "… records PERSISTENCE_CHANGED, but its evidence shows PERSISTENCE_UNCHANGED" |
| `t2_05` | persistence → `REVERSAL_OBSERVED` | "its FINISHED close names REVERSAL_OBSERVED, which a PERSISTENCE experiment's FINISHED close may not carry" |
| `t2_06` | capped (saturating lever, real cap 8) → `REVERSAL_OBSERVED` | "… records REVERSAL_OBSERVED, but its evidence shows CAPPED" |
| `t2_07` | `FINISHED` with `INTERRUPTED_DEATH`; `STALE` with `CAPPED` | "its FINISHED close names INTERRUPTED_DEATH …"; "its STALE close names CAPPED …" |
| `t2_08` | `FINISHED` naming no type | "its FINISHED close names no terminal type …" |

`t2_01`: every genuine close reads, each with its type recorded:

- three `REVERSAL_OBSERVED`;
- `RECURRENCE_OBSERVED`;
- `CAPPED` at the real cap;
- `PERSISTENCE_UNCHANGED`;
- the death's `INTERRUPTED_DEATH`.

The revision-1 receipt and observation attacks (`b3_18`) still pass unchanged.

## 3 · Blocker 2 — world model v9; v8 frozen

The writer is `virelai-world-model-v9`. `validate_v8` keeps B2's contract and never runs the experiment check.

**Schema compatibility** (`SCHEMA_COMPATIBILITY_B3r2.json`):

| Artifact | `read_world_model` | `validate` (v9) | `validate_v8` | `validate_v7` |
|---|---|---|---|---|
| v7 fixture (`0119a74`) | accepted | refused (schema) | refused (schema) | accepted |
| v8 fixture (`ef8289d`) | accepted | refused (schema) | accepted | refused (schema) |
| v9, B2-only chain (a G4-A choice) | accepted | accepted | refused (schema) | refused (schema) |
| v9, B3 chain (G4-B experiments) | accepted | accepted | refused (schema) | refused (schema) |
| B2-only chain relabelled v8, rehashed | accepted | refused (schema) | accepted | refused (schema) |
| B3 chain relabelled v8, rehashed | refused ("… is not G4-A's") | refused (schema) | refused ("… is not G4-A's") | refused (schema) |

**`ef8289d`'s own reader agrees on the same files** (`schema_on_ef8289d.txt`). It accepts the B2-only chain relabelled v8, refuses the B3 chain relabelled v8 with the same message, and refuses both v9 files as an unknown schema. The frozen v8 is therefore `ef8289d`'s contract.

- **The frozen fixture's provenance** is in `V8_FIXTURE_PROVENANCE.md`, with `make_v8_fixture.py`.
- **Tests:**
  - `t2_09`: the fixture's bytes are read back unchanged, and v9 refuses it at the schema boundary;
  - `t2_10`: v8 refuses a v9 artifact at the boundary, and refuses the relabelled one by its own rules;
  - `t2_11`: frozen v8 never runs the experiment check, and v9 always does.
- **The audit journal stays v2.**

**Current-schema assertions changed deliberately: 15 statements in 10 test files.**

| File | Statements changed |
|---|---|
| `test_descriptive_events` | 3 |
| `test_g4_selection` | 1 |
| `test_provenance_v2` | 2 |
| `test_wo_l2a_census_paths` | 1 |
| `test_world_description` | 1 |
| `test_world_model_v4_provenance` | 3 |
| `test_world_model_v5_product_content` | 1 (the `WRITER` constant) |
| `test_world_model_v6_dossier_records` | 1 (the `WRITER` constant) |
| `test_world_model_v6_dossiers` | 1 (the `WRITER` constant) |
| `test_world_model_v2` | 1 (the "unknown schema" probe moves from v9 to v10) |

The three `WRITER` constants feed 8 further equality assertions, which now check v9 through the constant.

## 4 · Blocker 3 — the ratchet, both counts

**Physical lines.** Sol was right: revision 1's `lever_experiments.py` was 501 physical lines. My report counted executable lines only and said so without naming the measure.

**The new module `lever_experiment_contract.py`** owns:

- the kinds and caps;
- the finished types by kind, and the stale types;
- `experiment_id`, `parse` and `question`;
- `terminal_type` and `admits`.

The engine imports it, and the validator imports only it (`t2_12`, in a fresh process).

| File | Physical: `ef8289d` → r1 → r2 | Executable: `ef8289d` → r2 | Largest function (exec) |
|---|---|---|---|
| `lever_experiments.py` (new) | — → 501 → **472** | — → 330 | `record_outcome` 38 |
| `lever_experiment_check.py` (new) | — → 113 → 172 | — → 111 | `_experiment` 26 |
| `lever_experiment_contract.py` (new) | — → — → 67 | — → 36 | `parse` 10 |
| `lever_dossier_selection.py` | 178 → 186 → 192 | 107 → 118 | `_log` 28 |
| `world_model_v2.py` | 465 → 465 → 481 | 326 → 333 | `_validate_level` 33 |
| `audit_journal.py` | **637** → 637 → 643 | 457 → 459 | `check_content` 26 |
| `g4b_gate.py` | 489 → 497 → 497 | 430 → 438 | `compact_gate_view` 52 |
| `controller_executor.py` | **650** → 653 → 653 | 490 → 492 | `_nav_step` 63 |
| `g4_selection.py` | 280 → 284 → 284 | 177 → 180 | `select` 23 |
| `library_agenda.py` | 322 → 335 → 335 | 245 → 254 | `_g3_questions` 34 |
| `lever_dossiers.py` | **555** → 567 → 567 | 439 → 446 | `gate_view` 39 |
| `lever_dossier_state.py` | 344 → 346 → 346 | 232 → 234 | `derive` 44 |
| `life_record.py` | 165 → 166 → 166 | 120 → 121 | `reset` 20 |
| `record_replay.py` | 322 → 325 → 325 | 241 → 244 | `replay` 54 |
| `record_from_artifacts.py` | 188 → 199 → 199 | 150 → 157 | `build_record` 50 |

**Both counts:**

- **New files:** every one is within 500 physical lines and 500 executable lines.
- **Executable lines:** every touched file is ≤ 500 and every function ≤ 80, the binding measure since the 2026-08-08 ruling.
- **Physical lines:** three shared files were already above 500 at `ef8289d`. They are `audit_journal`, `controller_executor` and `lever_dossiers`, shown in bold above. B3 adds only delegation lines to each: +6, +3 and +12.

Ruff is clean on every changed file.

## 5 · Preserved, unchanged from revision 1

No runtime path changed:

- the planner, the offer and admission at the first step;
- the steps and typed closes;
- the agenda and card;
- the dossier derivation;
- replay.

The only runtime-adjacent change is the audit translation of a G4-B finished row.

Also unchanged:

- owed experiments run before the record answers G4-B;
- E0053's life-2 reversal;
- the deterministic controller fallback;
- no extra Duck turn;
- no lifecycle-table change;
- no G4.3 revival;
- no compile on a controller step;
- both goldens;
- NAV and HYBRID deferred;
- capped, interrupted and inconclusive results stay unresolved;
- the dossier is still derived from receipts and observations.

The ~100 ms experiment-boundary cost is unchanged. A step under way still costs 0.7 ms.

## 6 · Honest ledger (changes from v1)

1. **`PERSISTENCE_INCONCLUSIVE` can now be checked, but no fixture produces one.** The check reads the acting lever's region from its G4.1 anatomy and the transition's pixel rewrite, and is skipped when either is missing. Only the kind is checked then.
2. **No outcome is recomputed where nothing is stated.** For failed-closed observations, or observations of a later life, the close's type is checked only against its event and kind.
3. **No terminal type exists to check for an open experiment.** An open experiment at a stop keeps its receipt checks.
4. **The v1 ledger otherwise stands.** Ledger item 3 there (schema compatibility) is resolved by v9.

## 7 · Package (`runs/_cowork_xfer/g4dossierB/b3/rev2/`)

| File | Contents |
|---|---|
| `WO_G4_DOSSIER_B3_rev1_to_rev2.patch` | 20 files; applies to revision 1 |
| `WO_G4_DOSSIER_B3_on_ef8289d.patch` | 31 files; applies to `ef8289d`; byte-identical to the tree |
| `WO_G4_DOSSIER_B3_slice.tar`, `SLICE_SHA256SUMS` | the 31 files |
| `AMENDMENT_WO_G4_DOSSIER_B3_rev2_2026-10-18.md`, this report, `NOTE_SHARED_FILE_WO_G4_DOSSIER_B3_2026-10-18.md` (amended) | design and shared files |
| `V8_FIXTURE_PROVENANCE.md`, `make_v8_fixture.py` | the frozen v8 fixture's provenance |
| `failfirst_r2_on_rev1.txt` | the terminal-forgery and schema tests on revision 1 |
| `SCHEMA_COMPATIBILITY_B3r2.json`, `schema_on_ef8289d.txt`, `schema_compat.py` | schema compatibility |
| `focused_b3r2.txt`, `tiers/`, `manifest_check_b3r2.txt`, both T2 diffs | test evidence |
| `SIZES_B3r2.md` | the file-size table |
| `PACKAGE_SHA256SUMS` | checksums |

The scratch ground diff is not in this package.

**Held for Sol:** the Mac T2 floor (1252 collected) and the commit. If the Director commits, the trailer is:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01K95ngAHgc1pWqpMXMj7cim
```

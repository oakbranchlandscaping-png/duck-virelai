# BUILD AMENDMENT — WO-G4-DOSSIER-A revision 3: execution joins scoped by level · 2026-10-18

**Seat:** Alpha (Ring 9). **Authority:** Sol's conditional acceptance of revision 2.
**Base:** revision 2, which is parked unchanged in `../rev2/`. Revision 1 is also unchanged, one folder up.
**Status:** built in the sandbox, uncommitted. T2, commit, Kaggle and DOSSIER-B are held.

## The fix

`lever_dossier_provenance.Context.executions` is now keyed `(level, evidence_id)`. Every lookup goes through
`Context.rows(level, evidence_id)`.

- **`attest_actor`** takes the dossier's level. It uses only executions with that level and evidence id. Both callers pass the level:
  - `reconcile_dossier`;
  - the validator's `_actor`.
- **`Context.contradicted`** checks only rows that name the receipt's own level. Those rows are compared against the receipt's transition alone.
- **No cross-level fallback.** A same evidence id on another level is unrelated.
- **Life is not joined.** Level scope is sufficient, as Sol ruled.

The answer-submitter index was already keyed `(level, gate, answer_id)` and is unchanged.

**Documented:** `actor.status` and `actor.basis` attest the executor only. The chooser is gate-retained and is not
journal-verified in this slice. This is stated in the module and validator docstrings. Accepted from revision 2 and
unchanged: `chooser_basis` and the size peak (8.1 %, 100.6 KB per level).

## The two-level join, before and after

Fixture: `two_level_model`. The same lever, witness and evidence `E-1` at transition 1 sit on a frozen level 1 and on
an open level 2. Each case gives the journal's execution rows as `(executor, transition, level)`.

| Case (rows) | Revision 2, keyed by `evidence_id` | Revision 3, keyed by `(level, evidence_id)` |
|---|---|---|
| DUCK t1 on L1; CONTROLLER t1 on L2 | both identities CLOSED_UNRESOLVED / PROVENANCE_INCOMPLETE (false contradiction) | L1 executor DUCK, VERIFIED; L2 executor CONTROLLER, VERIFIED |
| DUCK t1 on L1; CONTROLLER **t7** on L2 | both fail closed | L1 executor DUCK, VERIFIED; L2 alone fails closed (its own receipt says t1) |
| DUCK t1 ×2 on L1; CONTROLLER t1 on L2 | both fail closed | L1 FAILED_CLOSED / EXECUTION_DUPLICATED (same level, rule 4); L2 VERIFIED |
| DUCK **t2** on L1; CONTROLLER t1 on L2 | both fail closed | L1 fails closed / EXECUTION_EVIDENCE_DISAGREES (rule 5); L2 VERIFIED |
| CONTROLLER t1 on L2 only | L1 fails closed (false contradiction); L2 VERIFIED | L1 FAILED_CLOSED / EXECUTION_MISSING, identity COMPLETE (rule 6); L2 VERIFIED |

Source files: `two_level_before_rev2.txt` (run against the revision-2 tree), `two_level_after_rev3.txt`, and the
script `two_level_join.py`.

## Tests

**Fail-first against revision 2** (`failfirst_rev3_on_rev2.txt`): **7 of 7 new tests failed.** Six failed with
`TypeError` on facts nulled by the false contradiction; one failed with `COMPLETE` expected but `CLOSED_UNRESOLVED`
found.

| Test | What it proves |
|---|---|
| r3_01 | The same evidence id on L1 and L2 gets different VERIFIED executors. A forged L1 actor carrying L2's execution is refused. |
| r3_02 | An L2 execution never makes L1 duplicated. |
| r3_03 | An L2 execution never contradicts L1's receipt. |
| r3_04 | A same-level duplicate still fails closed. |
| r3_05 | A same-level wrong transition still fails the dependent chapter closed. |
| r3_06 | An execution only on another level gives EXECUTION_MISSING. |
| r3_07 | The corrected two-level model seals byte-identically twice. Resealing is a no-op, and both validate. |

**Focused run** (`focused_rev3.txt`): every revision-2 and revision-3 provenance and dossier test, 34 passed.

**Tier runs** (`tiers/`):

| Run | Result | Time |
|---|---|---|
| T0 `g4-dossier` | 56 passed | 28.9 s |
| T1 `paper-evidence` | 441 passed | 711.6 s |
| Manifest `--check` | exit 0; T2 = 1151, exactly the snapshot (+7, 0 removed) | — |

T1 `description` was not repeated: no description, view, report or link module changed. T2 is held.

## Files and ratchet

`WO_G4_DOSSIER_A_rev2_to_rev3.patch` changes 5 files (+151 −27):

| File | Change | Executable lines |
|---|---|---|
| `lever_dossier_provenance.py` | the level-scoped join | 132 → 134; functions Green, largest `reconcile_dossier` 22 |
| `lever_dossier_schema.py` | the validator passes the level | 257 → 257 |
| `tests/dossier_provenance_fixtures.py` | `two_level_model`; journal rows may name a level | — |
| `tests/test_world_model_v6_dossiers.py` | r3_01–r3_07 | — |
| `tests/tiers/T2_collected.txt` | the 7 new tests | — |

Correction to the revision-2 report: it listed `lever_dossier_provenance` at 130 executable lines. The parked
revision-2 file is 132, because the seal-time link refresh was added after that measurement.

`WO_G4_DOSSIER_A_rev3_on_e8984c2.patch` changes 27 files (+3317 −72). Each modified file's pre-image is the `e8984c2`
blob. It is published with `WO_G4_DOSSIER_A_rev3_slice.tar`, `SLICE_SHA256SUMS` and `PACKAGE_SHA256SUMS_REV3`.

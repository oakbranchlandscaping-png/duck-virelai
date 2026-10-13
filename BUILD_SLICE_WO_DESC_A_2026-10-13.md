# Build slice: WO-DESC-A, schema-v3 descriptive event ledger and scene state

**Date:** 2026-10-13
**Author:** Claude (Alpha build seat)
**Status:** Accepted by Sol after source review and the local tier floor. See §1a.
**Governs:** `INTERFACE_WO_DESC_A_v2_2026-10-13` (as built, §11; revision 1, §12; revision 2, §13) and the amended `NOTE_SHARED_FILE_WO_DESC_A_2026-10-13`.
**Bases:**
- **Integration head:** `5538816`. Every edited file was byte-identical there and in the device worktree before the slice.
- **Test-infrastructure base:** `5fdac9a`.

## 0a · Revision 2 (Sol's review: `BEFORE_ENTRY` scene behavior)

**The finding was confirmed.** On revision 1, a row numbered at the entry (10, with the entry board at 10) or below it (9) produced an empty scene. The cutoff excluded the entry node from `presence`, so the entry board's objects were not present. In the "at" case, the row's cut also overwrote the entry sighting's source.

**Fix.**
- `verified_node` always trusts the entry board. Presence, the compiler, H2's restriction and the validator all share it.
- `_windows` replays such a row's changes but gives it no cut.
- See interface §13.

**Fail-first** (`failfirst_descA_rev2_on_rev1.txt`): both new cases fail on revision 1, with an empty scene in place of the three entry-board objects.

**Revision 2 now requires, for both cases:**
- `BEFORE_ENTRY`, and no events;
- every offending and later row unverified;
- the scene exactly the pristine entry board, its tracks present (each first sighting is the entry's own);
- nothing unverified among the entry tracks, and nothing from the offending row.

**Revision 2 results** (cloud):

| Tier | Result | Wall time |
|---|---|---|
| `T0 desc-a --jobs 2` | 59 passed | 22.9 s |
| `T1 description --jobs 2` | 127 passed | 188.0 s |

- **Snapshot:** T2 is exactly 862 (2 new rows).
- **`T1 g3-directed`** was not rerun in the cloud, per Sol. Its files in `runs/` are from revision 1, which passed 143 in 387.9 s.

## 0 · Revision 1 (Sol's review: revision required)

| Finding | Change |
|---|---|
| 1 · A missing first transition went undetected | <ul><li>The expected first transition now comes from the entry: `entry_board_node(entry)` gives 0 for `INITIAL_FRAME` and `after_transition` for `LEVEL_ENTRY`. `_windows` cuts the entry board there instead of at the first recorded id minus one.</li><li>`first_mismatch` reports a leading gap as `MISSING_TRANSITION` at `entry_node + 1`, and an id at or before the entry as `BEFORE_ENTRY`. Interior gaps are unchanged.</li><li>With a leading gap, every recorded row is unverified and the scene stays at the entry board.</li><li>The validator refuses a verified prefix that does not start at `entry_node + 1`. `world_model_v2` checks `basis.entry_node` against the level's entry.</li></ul> |
| 2 · G2 granted EXPLAINED without transition evidence | `explain` requires a non-empty `evidence_ref` whose receipt resolves to the same transition. The refs are exactly `[COUNTER product, evidence]`. Otherwise the event is `UNEXPLAINED`, and a product-only EXPLAINED claim is refused. |
| Minor · duplicated `self.level = level` | **Examined, no change.** `_Compiler.__init__` assigns it once (line 260), in the working tree, the parked tarball and the diff. If Sol saw it elsewhere, please name the file and line. |
| Note for DESC-B | See §6 item 6. |

**Fail-first** (`failfirst_descA_rev1_on_rev0.txt`, revision 0 plus the revised tests): **6 failed, 1 passed** (the passing case is the contiguous guard).
- **Missing first transition:** revision 0 returned `first_mismatch: None`. It silently treated transition 2 as the first action, which is the gap Sol named. The world was built so that dropping row 1 contradicts no before-value.
- **`LEVEL_ENTRY` cases:** the entry node was off by one, 11 and 9 where 10 was expected.
- **The three evidence cases:** revision 0 explained the ticks anyway.

**Revision 1 results** (cloud):

| Tier | Result | Wall time |
|---|---|---|
| `T0 desc-a --jobs 2` | 57 passed | 23.9 s |
| `T1 description --jobs 2` | 125 passed | 192.2 s |
| `T1 g3-directed --jobs 3` | 143 passed | 387.9 s |
| `--check` | T0 57/19/24; T1 125/143; T2 exactly 860 (+7 new rows, none removed) | — |

On the saved records, every k008 tick carries its own evidence, so the k008 and carry assertions hold unchanged.

## 1 · Revision 0 results (cloud host, about 1.45× slower than the Mac)

| Tier | Result | Wall time |
|---|---|---|
| Fail-first on `5fdac9a` (`failfirst_descA_v2_on_5fdac9a.txt`) | 36 of 36 new tests fail | — |
| `T0 desc-a --jobs 2` (new set) | 50 passed | 22.0 s |
| `T1 description --jobs 2` (new set) | 118 passed | 183.5 s |
| `T1 g3-directed --jobs 3` (accepted set; includes census and view) | 143 passed | 389.7 s |
| `--check` | T0 50/19/24; T1 118/143; T2 exactly 853 (817 + the 36 new) | — |

The snapshot diff adds 36 rows, all in `tests/test_descriptive_events.py`, and removes none. Per-test outcomes are in `runs/*.json` and timings in `runs/*.txt`.

## 1a · Sol acceptance on the Mac (revision 2)

Sol reviewed revisions 0–2, applied the final archive, and verified all ten file hashes against
`slice_hashes.txt` (`HASHES_MATCH`). The final manifest contains exactly 862 tests.

| Local gate | Result | Wall time |
|---|---:|---:|
| T0 `desc-a`, 2 workers | 59 passed | 26.4 s |
| T1 `description`, 2 workers | 127 passed | 89.4 s |
| T1 `g3-directed`, 4 workers | 143 passed | 138.0 s |
| T2, 4 workers in the managed sandbox | 859 passed, 1 skipped, 2 environment failures | 300.7 s |
| T0 `test-tiers`, 2 workers with local process inspection | 24 passed | 7.0 s |

The two T2 failures were the runner's SIGTERM and SIGINT cleanup tests. Both failed only because the managed
sandbox denied their use of `ps` (`PermissionError: [Errno 1] Operation not permitted`). Both passed in the
authorized local-process rerun. No product, schema, description, census, gate, lifecycle, navigation, or replay
test failed. The accepted effective floor is **861 passed, 1 skipped**. `git diff --check` was clean.

Revision 2 also closes the final review finding: a transition numbered at or before the level-entry board is
unverified, receives no board cut, and cannot erase or replace the trusted entry scene.

## 2 · What was built

- **`descriptive_events.py` (new, pure).** One record per recorded transition. Every subject is the census track that owns the sighting.
  - **Verbs come from the accepted weave.** The line's own edge gives continuations and bridges. Terminal verdicts come from replaying `weave_edge` on the same two cuts.
  - **STILL** is emitted only for a bound track or the acted-site track. The record carries `still_total = still_emitted + still_omitted`.
  - **Explanations** come from `explain`, which the validator recomputes.
  - **Verified prefix.** After the first duplicate, missing or contradicted record, later records carry nothing. The scene is the last verified board.
  - **Class changes.** A RECOLOR of a bound track ends the binding: the event carries the role and `role_binding_ends`, and later events do not.
  - **H2.** `restrict_description` truncates the ledger at the journal mismatch and withdraws the roles H2 withdraws.
- **`library_census.py`.**
  - `project_tracks` returns the woven windows.
  - `_receipts` adds the G2 `mask`, plus the witness `residue` and `witness_sha256`.
  - `compile_level` attaches the description and records `binding_ends_at` with `CLASS_CHANGED` gaps.
  - `_board_accounting` adds the prefix `RECORD_MISMATCH`.
  - `_apply_check` restricts the description.
- **`world_model_v2.py`.**
  - `SCHEMA` is v3.
  - `validate` applies the v2 rules plus `_validate_v3_level`.
  - `validate_v2` keeps the accepted rules unchanged.
  - `read_world_model` reads v1, v2 and v3.

**Ratchet (NCNB lines).**

| Function | Before | After |
|---|---|---|
| `compile_level` | 61 | 53 |
| `project_tracks` | 52 | 50 |
| `_apply_check` | 31 | 33 |
| `_receipts` | 24 | 29 |
| `_board_accounting` | 10 | 16 |

- **No function over 50 grew**; `_certified` (86) is untouched.
- **New module's largest functions:** `scene_at` 38, `restrict_description` 37, `_validate_event` 31; `_Compiler._pair` 17, `_arrivals` 20, `_departures` 18.

## 3 · Schema diff, v2 → v3

| Where | v3 adds |
|---|---|
| `schema` | `virelai-world-model-v3`. A v2 artifact still reads (`validate_v2`), and a v2 artifact is not a valid v3 model. |
| `levels[].description` | **Required.** See the interface §4: <ul><li>`schema`, `basis`, `integrity`, `first_mismatch`;</li><li>`transitions[]`: record → events;</li><li>`presence`, `role_bindings`, `scene`.</li></ul> |
| `receipts.products[G2]` | `mask` {`cell_runs`, `cell_count`, `rewrite` {`from`, `to`}, `law_version_id`}, when the product has a mask law. |
| `receipts.witnesses[*]` | `residue` {`local_runs`, `remote_runs`, `cell_count`} and `witness_sha256`. Both are required in v3. |
| `certified.roles[*]` | `binding_ends_at` (optional): the transition at which a class change ended the binding. The role stays as history. |
| `gaps[]` | <ul><li>`CLASS_CHANGED` (`source` "description: …", `track_id`, `transitions`);</li><li>`RECORD_MISMATCH` with `source: description_prefix` for a duplicated or missing record.</li></ul> |
| `accounting.missing` | `RECORD_MISMATCH` at compile time for a duplicated or missing record. H2 no longer lists it twice. |

`descA_vs_5538816.diff` is the full source diff.

## 4 · Performance (k013 at cut 401, 400 transitions, median of 5, cloud)

| | `5fdac9a` | WO-DESC-A |
|---|---|---|
| Census compile + seal | 4.73 s | 5.25 s (+0.52 s, +11%) |
| `describe_level` alone, projection given | — | 0.69 s |
| `validate` of the sealed model | 0.006 s | 0.068 s |
| Canonical bytes | 393 KB | 1.58 MB (the description is 1.18 MB) |

**k013 at 400 holds 1,054 events:**

| Verb | Events |
|---|---|
| STILL | 489 |
| SHRINK | 236 |
| GROW | 235 |
| RECOLOR | 29 |
| MOVE | 28 |
| BIRTH | 17 |
| DEFORM | 13 |
| DEATH | 7 |

All 489 STILL events are on the nine bound LEVER tracks.

The cost is paid only at H1, H2 and the live view (each Duck turn), never per action. `test_library_view.py` went from 55 s to 72 s.

## 5 · Semantic review excerpt

`EXCERPT_k008_t45.txt` has the full k008 excerpt: records at t1-3, 13-14, 30-33 and 44, the scene, one raw event and the COUNTER receipt. In summary:

- **t1 (ACTION1):**
  - The ego track `O-L1-P1-E-38a9…` MOVEs Δ[-4,0]. It is UNEXPLAINED, because the EGO identity is unresolved and nothing is guessed.
  - The counter track SHRINKs 64→62. It is EXPLAINED by `G2_MASK_LAW`, citing the COUNTER product and t1's evidence.
  - The background DEFORMs through a `dominant_mutual_overlap` bridge (UNEXPLAINED).
  - The vacated `0` region is BORN inside the mask (EXPLAINED).
- **t30:** the last counter piece's DEATH is EXPLAINED, since every changed site is a 14→0 rewrite inside the mask.
- **t31 RESET:** a boundary record with 8 tracks ended, 8 started and 8 possible correspondences. It has no events, and the 0→14 refill is not called an event of anything.
- **Scene as of t44 (life 2):** 9 present (all `UNRESOLVED_OBJECT`), 9 departed (`LIFE_ENDED`) and 40 unexplained events. `open_identity` names COUNTER and EGO, each resolving to its `IDENTITY_UNRESOLVED` gap.

## 6 · Items for Sol

1. **Three test files outside the approved assertion were edited.** All are fixture builders; no assertion changed. Each is named in the note.
   - `test_world_model_v2._model()` gains the v3 description and witness residue. Unedited, 7 of its 13 tests fail under v3.
   - `test_library_view._large` makes its 40 fabricated frozen levels transition-free. Before this change, the 40 copies of 400 shared ids made the page tests take 53 s instead of 5 s.
   - `test_wo_l2a_census_paths.py:68` (ruled).
2. **Narrowed in the build: G1 `PARTLY_EXPLAINED` covers MOVE only.** A recolor of the bound ego is UNEXPLAINED. The fail-first assertion was narrowed accordingly, so the claim is now stricter than v1.
3. **Explanation `basis` is a rule code, and snapshots carry no cell runs.** Exact changed sites live in the footprint groups. This halves the ledger.
4. **Finding, outside this slice:** k013's certified G2 product has `mask_law: None`. So the census certifies no COUNTER on k013, and its roughly 460 counter GROW/SHRINK events stay UNEXPLAINED (`NOT_COVERED`). That is honest under the rule, but it is G2's question: why does k013's counter product carry no mask law?
5. **The H2 truncation reason is `JOURNAL_CHECK`.** A renamed action truncates the ledger as well as a missing, extra or duplicated id does. This follows the interface §6 reading of "contradictory".
6. **For DESC-B (Sol, accepted as raw accounting here).** The ledger is exhaustive at the substrate. It describes semantic objects and also the complementary grid regions around them:
   - a counter shrink also appears as growth of the rewritten region beside it;
   - large terrain regions produce DEFORM bridges whenever something moves through them.

   DESC-B must turn this into a concise semantic presentation, so that Duck does not read complementary pixel regions as separate mechanisms. DESC-A keeps the raw accounting.

## 7 · Not in this slice

WO-DESC-B (pages, digest, `world_report.md`), G4 dossiers, Push, SUB-4, G5/G6, PLAY-NORMAL wording, win transfer, a current-life EGO join, and SPLIT and MERGE.

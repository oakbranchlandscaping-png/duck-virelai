# BUILD SLICE: WO-PE-02 revision 3, schema-v4 provenance (2026-10-15)

**Seat:** Claude, Alpha build seat (Ring 9, Cybernetic Duck)
**Base:** `ring9-unified` at `afe93c8`. The revision-2 snapshot used here matches revision 2's `SLICE_SHA256SUMS` 17/17.
**Review answered:** `REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v2_2026-10-15` (Sol): F4 (§3), the multi-level proof (§4) and the retained-state guards (§5). E4 is recorded as ruled.
**Interface:** `INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v4_2026-10-15`. It is v3 with revision-3 passages marked **[v4]**.
**Shared-file note:** unchanged since Amendment 1. Revision 3 adds no file and edits no gate or shared file; it changes one new module and the test files only.
**Status:** sandbox-green. **Not committed. T2 is held.**

---

## 1 · Result at a glance

| Check | Result |
|---|---|
| Focused suite | **64 passed** (52 from revision 2, unchanged; 12 new) |
| T0 `provenance-v4` | **93 passed** |
| T0 `provenance` | **76 passed** |
| T1 `paper-evidence` | **329 passed** |
| T1 `description` | **204 passed**. Run because `product_origins` sits on the census compile path that description tests exercise. |
| `--check` | exit 0. **T2 is 1039 tests, exactly the snapshot (1027 + 12).** Removed against revision 2: 0. Removed against `afe93c8`: 0. |
| Fail-first against revision 2 | 9 failed, all **by wrong acceptance**: 4 G4-B mutations and 5 G1/G2 state mutations. 3 passed (see §4). |
| Real two-level run | **`SEALED / COMPLETE`**. H1 wrote the interim model at the boundary and H2 the final model. Every product joins its own level's admission. |
| Artifacts | 13 files: **byte-identical across two runs, and byte-identical to revision 2** |
| H2 added, 800 rows (synthetic, best of 9) | **0.34 s**, under 0.5 s. The noise is noted in §7. |

---

## 2 · F4: record-derived G4-B relations rebuilt in full (`product_origins.py`)

For a `LEVER_RELATIONS_FROM_RECORD` answer, the adapter now requires two things.

**1. The whole answer matches what the record reconstructs to.** The record is `payload.from_record`. The reconstruction is the same fixed transformation `g4b_gate._certify_from_record` applies, restated as `record_relations_answer(record)`:

| Field | Reconstructed from the record |
|---|---|
| `answer_id` | `record.answer_id` |
| `answer_kind` | `LEVER_RELATIONS_FROM_RECORD` |
| `description` | `record.description` |
| `relations` | `record.relations` |
| `open_conditions` | `[]` |
| `competing_models` | `[]` |
| `falsifier` | the fixed falsifier sentence |
| `limitations` | `[record.epistemic_limit]` |

The comparison against `payload.answer` uses strict canonical JSON.

**2. The record's id is its content hash.** That hash is `record_relations`' seed over the relations' levers, claims and transitions and the description, restated as `record_answer_id`. A record and answer altered *together* would otherwise still agree with each other.

If either check fails, the product becomes `UNATTRIBUTED / ANSWER_DOES_NOT_DERIVE_PRODUCT`. If both pass, it stays `ANSWER_CERTIFIED / RELATIONS_CERTIFIED_FROM_RECORD`, with the controller's admitted answer as the trigger and reference. Interface v4 records that PE-03 must attribute this content to deterministic record derivation, not to Duck.

**Why restated, not imported:** the gate inlines both the transformation and the id seed, so importing either would mean a gate edit. Instead, a test pins both to the real gate. On the real record certification (the `start_g4b` world, with the controller's `LEVER_RELATIONS_FROM_RECORD` answer through `prepare_answer` and `submit_prepared`), the unmodified product is certified and joins `EXACT` with `COMPLETE`. That only happens if both restatements reproduce the gate exactly.

**Attacks on the real product, each now `UNATTRIBUTED`, `PRODUCT_UNATTRIBUTED` and `INCOMPLETE`:**
- same id, altered description;
- same id, relations altered (one dropped);
- same id, altered epistemic limitation;
- record and answer description altered together, caught by the content-addressed id.

---

## 3 · Retained-state guards (G1, G2; G4-C unchanged)

All of these are census-time comparisons of the payload with retained attributes. No gate method is called and no state changes.

| Product | Revision 3 adds | On failure |
|---|---|---|
| G1 `EgoLaw` | the whole payload equals the retained `ego.ego_law`. This sits beside revision 2's checks: answer retained, and id derived from the answer id. | `UNATTRIBUTED / PRODUCT_DIFFERS_FROM_RETAINED_STATE` (new basis) |
| G2 counter model | `counter_model` equals the retained `counter.counter_model`, and `mask_law` equals the retained `counter.mask_law`, which must exist. This sits beside revision 2's check of the answer-sourced fields. | same |
| G4-C law set | `law_test` equals the retained `_certified` prediction, already checked in revision 2 | `ANSWER_DOES_NOT_DERIVE_PRODUCT` |

On the real controller run's products, each of these is caught:
- an altered `EgoLaw` payload field;
- an altered retained `ego_law`;
- an altered counter-model field the answer does not supply (`status`);
- an altered `mask_law` in the payload;
- a missing retained mask.

The unchanged products stay certified.

---

## 4 · Multi-level proof on the production path

The new fixture, `two_level_session`, runs the real session machinery: `_HarnessGameSession.play` with the real `ToolAgent`, the controller executor and provenance capture. Only the world is a test double: `_TwoLevelGame`, the ft09 continuation behind the harness interface. Its 20th action completes level 1 (`levels_completed` goes 0 → 1, with `just_won_level`), and the board starts again as level 2. No production code was changed for this.

| Review step | Evidence in the test |
|---|---|
| 1. Admitted answers recorded on level 1 | G0 and G1 admissions on level 1 |
| 2. Level 1 frozen through the real H1 path | the writes are exactly `[("LEVEL_ADVANCE", "H1"), ("BUDGET_STOP", "H2")]`, and H1's writer prefix is `VERIFIED` at H2 |
| 3. A fresh level-2 target journal | level 2 runs its own ladder (G0 → G4 anatomy), with its own admissions |
| 4. Sealed and compiled at H2 | `SEALED`, levels `[1, 2]` |
| 5. Level-1 products join level-1 events exactly | every join is `EXACT`; each joined row's `(level, gate, answer_id)` equals the product's |
| 6. No borrowing | the ids recurring on level 2 (`G0-CONTROLLER`, `G1-1`) join distinct, level-2 events. With level 2's G0 admission removed, level 2's G0 product is `NO_ADMITTED_ANSWER` with no candidates, while level 1's still joins its own level-1 event |
| 7. `COMPLETE` | `SEALED / COMPLETE`, no reasons |

The level-scoped join is unchanged. Both multi-level tests also **pass on revision 2**: they prove the existing production behaviour, and nothing needed fixing. A carry hypothesis on level 2 is not a product, so it has nothing to join. Every level-2 product joins a level-2 event.

---

## 5 · Fail-first against revision 2 (`failfirst_r3_on_rev2.txt`)

The revision-3 test file (the final file) was run against the revision-2 tree, with the r3 tests selected.

**9 failed, every one by assertion (revision 2 classifies the case `ANSWER_CERTIFIED`):**
- G4-B `description`, `relations`, `limitation`, `record_and_answer_together`;
- G1 `ego_law_payload`, `ego_law_retained`;
- G2 `counter_model_payload`, `mask_law_payload`, `mask_law_retained`.

**3 passed:** the unmodified record case (a guard) and the two multi-level tests (the proof of existing behaviour).

---

## 6 · Ratchet

`product_origins.py`: 151 → **174** executable lines (Green). Its largest function is `_counter` at 18. No other production file changed.

---

## 7 · Measurements: SYNTHETIC, NOT PAPER EVIDENCE

The verdicts are identical to revision 2:
- k008 `COMPLETE`;
- k013 `COMPLETE` (G2 `GATE_DERIVED / COUNTER_NOT_OBSERVED`);
- carry-v7 `INCOMPLETE` (S1, as ruled).

The new guards certified every real-replay G1 and G2 product.

| Record | Rows | H2 added | Chapter | Growth |
|---|---|---|---|---|
| carry-v7 | 52 | 0.037 s | 0.004 s | +51,541 B (15.4 %) |
| k008 | 123 | 0.067 s | 0.013 s | +132,853 B (42.5 %) |
| k013 | 792 | 0.339 s | 0.071 s | +727,014 B (45.6 %) |
| k013 padded to 800 | 800 | **0.342 s** | 0.070 s | +733,852 B (46.0 %) |

**Timing noise:** revision 3 changed nothing in H2's added work; the new checks run at census time, inside compile, outside this measurement. Even so, two best-of-3/5 runs in this sandbox read **0.33–0.47 s** for the ~800-row cases. Almost all of that variation is in the persist path (seal, canonical bytes and validate). The final table is best-of-9. The 0.5 s ceiling holds in every sample, but the worst sample was 0.03 s under it. A Mac measurement would settle the margin.

---

## 8 · Package

| Item | Contents | sha256 |
|---|---|---|
| `WO_PE_02_afe93c8.patch` | cumulative: 17 files, +2543 / −22. Applies to `afe93c8`; all 17 results equal the tree. | `718aaf13…` |
| `WO_PE_02_rev2_to_rev3.patch` | 3 files (`product_origins.py`, the test file, `T2_collected.txt`), +260 / −9. Applies to the revision-2 slice. | `881ea3c0…` |
| `WO_PE_02_slice.tar` + `SLICE_SHA256SUMS` | the 17 files; extraction checked 17/17 | `806d0203…` |
| `INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v4_2026-10-15.md` | interface v4 | `PACKAGE_SHA256SUMS` |
| `failfirst_r3_on_rev2.txt` | §5 | `PACKAGE_SHA256SUMS` |
| `MEASUREMENTS_WO_PE_02_SYNTHETIC_r3.json` | §7, best of 9 | `PACKAGE_SHA256SUMS` |
| `WO_PE_02_r3_evidence.tar.gz` | the tier logs and results, `manifest_check.txt`, `focused_v4_suite.txt`, the artifacts and their two-run hashes, the second noisier measurement run (`MEASUREMENTS_WO_PE_02_SYNTHETIC_r3_repeat.json`; the first was overwritten by the best-of-9 run, and its k013 figure of 0.469 s is quoted from the console), and the best-of-9 instrument | `PACKAGE_SHA256SUMS` |

Gates, report rendering, Duck's view, claims, keys, grading, gate scheduling and action selection are untouched. **Held:** T2 and the commit.

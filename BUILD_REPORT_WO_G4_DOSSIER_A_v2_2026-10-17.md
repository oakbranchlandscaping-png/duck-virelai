# BUILD REPORT — WO-G4-DOSSIER-A, revision 2 · v2 · 2026-10-17

- **Seat:** Alpha (Ring 9, Cybernetic Duck). **Reviewer:** Sol.
- **Base:** `e8984c2`, with the revision-1 slice applied (parked unchanged in `runs/_cowork_xfer/g4dossierA/`).
- **Authority:** Sol's revision-2 directive (blockers 1–4, the provenance scope, the size budget, the T0 runtime).
- **Status:** built in the sandbox, uncommitted. T2, the commit, Kaggle and DOSSIER-B are held.
- **Game-free:** record names appear only in tests and in measurement labels.

## 1 · Verdict

All four semantic blockers and the T0 runtime blocker are resolved in the sandbox. On the final tree:

| Run | Result | Time |
|---|---|---|
| T0 `g4-dossier` | 49 passed | 21.7 s (target 90 s; revision 1 took 334.5 s) |
| T1 `description` | 274 passed | 382.6 s |
| T1 `paper-evidence` | 434 passed | 532.8 s |
| Manifest `--check` | exit 0; T2 = 1144, exactly the snapshot | |

One interface addition needs Sol's acceptance or removal: the actor carries a sixth field, `chooser_basis` (§3).

## 2 · Fail-first against revision 1

The new tests were run on the revision-1 tree before any revision-2 code existed (`failfirst_rev2_on_rev1.txt`).

**26 failed.** The causes:

- `KeyError 'events'` ×6
- `KeyError 'chooser_basis'` ×6
- `KeyError 'submission'` ×4
- `ImportError lever_dossier_links` ×4
- the remaining 6 are assertion failures:
  - `certified_by` still present;
  - identity not failed closed on a contradicting execution;
  - an unverifiable executor still `CONTROLLER`;
  - and similar.

**2 passed, as expected:**

- `test_v6_02`: its revision-1 assertion was changed on purpose by blocker 4 (§7). Revision 1, where every subject is unresolved, satisfies the new form.
- The size-budget check: it is a guard, renamed `test_guard_r2_dossiers_stay_inside_the_review_budget`.

**Added later, also failed first.** `test_v6_r2_24` (remote channels on the vc33 record) was added after the main fail-first run. It was then run against the revision-1 tree and failed (`KeyError 'events'`; `failfirst_rev2_r2_24_on_rev1.txt`).

The 26 failures, by blocker:

| Blocker | Failing tests |
|---|---|
| 1 · executor | r2_01 Duck chose and executed · r2_02 Duck chose, controller executed · r2_03 controller coverage · r2_04 live/H1 pending (×2) · r2_05 H2 missing execution · r2_06 executor/evidence disagreement |
| scope | r2_07 unverifiable authorship leaves the facts standing · r2_08 a contradicted receipt fails only the chapters that rest on it |
| 2 · certifier | r2_09 projection · r2_22 every surface · r2_23 submitter at H2 (×3) · case 24 record-derived |
| 3 · events | r2_10 one local event · r2_11 one remote event · r2_12 several events, ambiguity · r2_13 no matching event, undescribed transition, foreign track · r2_14 forged event id · r2_15 event from another transition · r2_16 event missing the residue · r2_20 record · r2_21 page and report |
| 4 · subjects | r2_17 injected or foreign track · r2_18 ambiguous join (also r2_10–r2_13, r2_20) |

## 3 · Blocker 1: chooser and executor

The identity chapter's `actor` is now:

```
{chooser, chooser_basis, executor, status: VERIFIED|PENDING|FAILED_CLOSED, basis, execution_event_id}
```

**Chooser.** It is the actor of the G3 selection event that admitted the lever, at or before its first witness (`G3_SELECTION_EVENT`). With no such event, a G3-discovered lever was chosen by the coverage order (`CONTROLLER`, `G3_COVERAGE_ORDER`). With neither, the chooser is `null` (`NOT_RECORDED`).

**Executor.** It comes only from the embedded journal's executed probe whose `refs.evidence_id` is the activation's witness evidence. That is G3's own discovery reference, or else the lever's first witness. The executor is never inferred from the chooser and never defaults to `CONTROLLER`.

**When the executor is set.**

- Live and H1 models: `null` / `PENDING` / `PROVENANCE_NOT_FINAL`.
- H2: one matching row gives `VERIFIED` with its event id.
- Otherwise `FAILED_CLOSED`. The basis is one of:
  - `JOURNAL_UNAVAILABLE`
  - `EXECUTION_MISSING`
  - `EXECUTION_DUPLICATED`
  - `NO_WITNESS_EVIDENCE`

  A `FAILED_CLOSED` executor adds a typed open item `{kind: PROVENANCE_INCOMPLETE, field: ACTIVATION_EXECUTOR, basis, evidence_ref}`. The witness facts stay.

**Where it is computed.** Reconciliation runs at seal: `world_model_v2.seal` calls `lever_dossier_provenance.reconcile` after the provenance chapter is attached. It recomputes from scratch, so sealing twice is idempotent. The validator recomputes the same function from the embedded rows. It now runs after `validate_chapter`, so forged rows are reported by the provenance contract first.

**Examples** (`SEMANTIC_EXAMPLES_WO_G4_DOSSIER_A_rev2.json` → `chooser_executor`):

| Case | chooser / basis | executor / status / basis |
|---|---|---|
| Duck chose, Duck executed (H2) | DUCK / G3_SELECTION_EVENT | DUCK / VERIFIED / EVIDENCE_LINKED_EXECUTION, `PV-e119…` |
| Duck chose, controller executed (H2) | DUCK / G3_SELECTION_EVENT | CONTROLLER / VERIFIED |
| Controller coverage, no Duck choice | CONTROLLER / G3_COVERAGE_ORDER | CONTROLLER / VERIFIED |
| Live view and H1, Duck chose | DUCK / G3_SELECTION_EVENT | null / PENDING / PROVENANCE_NOT_FINAL |
| Real controller session, sealed H2 journal (the `test_world_model_v4` fixture, 5 levers) | CONTROLLER / G3_COVERAGE_ORDER | CONTROLLER / VERIFIED, each with its own `PV-` execution |

**For Sol: `chooser_basis` is an addition.** It keeps revision 1's selection-versus-coverage distinction, which the five-field structure would otherwise have folded into the executor's basis. Accept it, or rule it out and I fold it.

## 4 · The provenance scope, and targeted failure behaviour

`PROVENANCE_INCOMPLETE` is now emitted for exactly three things:

- the activation executor;
- the G4-B answer submitter;
- an execution that contradicts its evidence receipt (the admission/execution linkage).

**Contradicted receipts.** A receipt is contradicted when an executed probe names it with another level or transition. Every chapter whose evidence includes such a receipt fails closed under R8: basis `PROVENANCE_INCOMPLETE`, the prior status kept, facts null, integrity refs set to the contradicted evidence. The R1 census label is removed first, so the prior status is the work's own. The open item is `{field: EVIDENCE_EXECUTION, basis: EXECUTION_EVIDENCE_DISAGREES, refs}`. Chapters on other receipts are untouched (r2_08: E0053's orbit and limits fail; its identity and anatomy, and E0054's orbit, stay OK).

**Unverifiable authorship erases nothing.** In r2_07 (H2, no journal), every actor is `FAILED_CLOSED` while every identity, anatomy and orbit chapter keeps its status and facts.

The derived chapter lists every item in `provenance_incomplete`, and these items also block `NO_OPEN_ITEMS`.

| Case | Outcome |
|---|---|
| Journal without the execution | identity COMPLETE; actor FAILED_CLOSED / EXECUTION_MISSING; one open item |
| No readable journal at H2 | actor FAILED_CLOSED / JOURNAL_UNAVAILABLE |
| Execution names t2, receipt says t1 | identity CLOSED_UNRESOLVED / PROVENANCE_INCOMPLETE, prior COMPLETE, refs `[E-1]` |
| Two executions claim one evidence | actor FAILED_CLOSED / EXECUTION_DUPLICATED; identity kept |

## 5 · Blocker 2: submitter and certifier

The relations facts' `certified_by` is replaced by:

```
submission: {submission_source: DUCK|CONTROLLER|RECORD|null, certifier: G4-B-LEVER-RELATIONS,
             certification_origin: ANSWER_CERTIFIED|RELATIONS_CERTIFIED_FROM_RECORD, status, basis, answer_event_id}
```

- **Certifier:** always the gate.
- **Record-derived sets:** a record-derived set names `RECORD` (`VERIFIED` / `GATE_RECORD_DERIVATION`, no provenance needed).
- **Any other submitter:** the executor of the journal's admitted answer with that `answer_id` on G4-B at this level. It is `PENDING` until H2. At H2 it is `FAILED_CLOSED` with `JOURNAL_UNAVAILABLE`, `ANSWER_ADMISSION_MISSING` or `ANSWER_ADMISSION_AMBIGUOUS`, plus a typed open item.
- **Withdrawn models:** they keep only `certifier` and `certification_origin`.
- **Frozen payload:** the G4-B product payload is unchanged; it still reads `certified_by: DUCK`.

No dossier page, digest or report says Duck certified anything (r2_22 checks every page of the dossier, the digest and the report for both a COMPLETE and a withdrawn set).

| Case | Submission |
|---|---|
| Duck's description, H2 without a journal | null / FAILED_CLOSED / JOURNAL_UNAVAILABLE; chapter COMPLETE |
| Journal admits the answer from DUCK | DUCK / VERIFIED / ANSWER_ADMISSION, `PV-561e…` |
| Journal admits it from CONTROLLER | CONTROLLER / VERIFIED |
| Journal has no admission | null / FAILED_CLOSED / ANSWER_ADMISSION_MISSING + open item |
| Record-derived set | RECORD / VERIFIED / GATE_RECORD_DERIVATION, origin RELATIONS_CERTIFIED_FROM_RECORD |

## 6 · Blocker 3: exact transformation-event links

**Fields.** Each anatomy channel gains:

- `events: [{event_id, transition_id, verb}]`
- `event_status: LINKED | NO_MATCHING_EVENT | TRANSITION_NOT_DESCRIBED`

**How events are selected.** The witness transition is the described transition whose `evidence_ref` is the anatomy's witness evidence. An event there is linked when its changed footprint is non-empty and lies inside the channel's recorded residue; the changed footprint is the CHANGED cells of its membership groups. Only references are stored, never event bodies. Causality stays at the G4 gate.

**Validation.** The validator recomputes the links exactly. It names the first failure:

- an event not observed at its transition;
- an event not at the witness transition;
- an event that does not intersect the residue;
- a set that is not exactly the covered events.

**Rendering.** The dossier page summary and one report claim line per channel render the links, citing the event ids.

**When links are recomputed.** Links are refreshed at every seal from the stored description. H2's record check can rewrite a frozen level's description after its H1 freeze. T1 caught this: `test_wo_l2a_hooks` [7-E0004-E0005] failed until the refresh was added (`tiers/r5_T1_description_run_before_link_refresh.txt`).

**On the records:**

- ft09: all eight channels are LOCAL, each linked to its one RECOLOR event, for example E0053 → `EV-493a28ab61ba00ce RECOLOR t58`. The counter's masked SHRINK/GROW events at t58 are correctly not linked.
- vc33, level 1: four REMOTE channels with 1–3 events each, for example E0004 `CH-0c4c8a51cfa0` → MOVE, MOVE, SHRINK.

## 7 · Blocker 4: affected-subject joins

A channel's `subject` is `{status: EXACT_TRACK, track_id, basis: {key: EXACT_EVENT_FOOTPRINT, event_id, transition_id}}` only when exactly one linked event meets every condition:

- its changed footprint equals the residue;
- each recorded side (before and after) has the residue's bounding box and cell count;
- its track is on this level.

Otherwise the subject is `{status: UNRESOLVED_REGION, reason: NO_EXACT_MATCH | AMBIGUOUS_MATCH | TRANSITION_NOT_DESCRIBED}`. Proximity, colour and later appearance never join, and a join certifies no role.

The validator refuses an injected track, a track of another level, and a stored join made ambiguous by a second exact footprint. The open-items chapter lists `AFFECTED_SUBJECT_IDENTITY` as unavailable only while some channel is still unresolved.

On the records:

- ft09: all eight channels join their tile's own track.
- vc33: every remote channel stays `UNRESOLVED_REGION / NO_EXACT_MATCH`, because each residue spans more than one object's footprint.

Case 2's revision-1 assertion that every subject is unresolved was changed by this ruling.

## 8 · Size against the review budget

Measured on the final tree (`MEASUREMENTS_WO_G4_DOSSIER_A_rev2.json`); every state is inside the budget.

| State | Model bytes | Dossier bytes (share) | Largest level |
|---|---|---|---|
| ft09 t70 | 544 763 | 37 187 (6.8 %) | 37 187 |
| G4.1 7/8 | 844 030 | 62 462 (7.4 %) | 62 462 |
| G4.1 8/8 | 877 938 | 63 362 (7.2 %) | 63 362 |
| t80 | 913 049 | 66 727 (7.3 %) | 66 727 |
| G4-B open | 1 169 780 | 85 405 (7.3 %) | 85 405 |
| G4-C certified | 1 239 148 | 100 644 (8.1 %) | 100 644 |
| G4-C contradiction | 1 224 479 | 99 265 (8.1 %) | 99 265 |
| k031 shape | 897 575 | 66 280 (7.4 %) | 66 280 |
| vc33 two levels | 522 616 | 29 218 (5.6 %) | 29 216 |

- **Limits:** at most 10 %, and at most 128 KiB (131 072 B) per level.
- **Peak:** 8.1 % and 100.6 KB, at G4-C.
- **Growth over revision 1:** about +2–8 KB per state. The drivers are the actor's six fields per lever, the submission block, and the event references.
- **Digest:** max 2495 characters, inside its 2500 budget.
- **Latency on this run** (a lightly loaded sandbox, so not directly comparable with revision 1's figures):
  - dossier build: 4–16 ms;
  - gate view: 7–23 ms;
  - seal: 0.13–0.55 s;
  - strict check: 0.03–0.11 s;
  - validate: 0.06–0.21 s;
  - live view: 0.34–2.1 s;
  - H1 freeze census: 1.27 s.

## 9 · T0 structure and timing

`test_world_model_v6_dossiers.py` (T0 `g4-dossier`) now holds only:

- the pure schema, projection and attack cases (09–13, 16, 19, 20, 30);
- the 18 revision-2 synthetic and attack cases (19 test ids);
- the budget guard.

Its record states are two replays per module (ft09 t80 and G4.1 8/8); the attacks edit deep copies.

`test_world_model_v6_dossier_records.py` (T1 `description` and T1 `paper-evidence`) holds:

- the 28 full-record semantic cases, moved with their test names unchanged;
- 6 revision-2 record cases.

Read-only cases share one replay and one compiled model per state; compilation leaves the machine byte-identical, which a guard checks. Cases that drive the machine take their own copy.

Every revision-1 assertion is still covered, in T0 or T1, except the two changed by ruling (cases 2 and 24). The manifest has no overlap; `--check` passes.

In the T2 snapshot (`T2_SNAPSHOT_DIFF_rev1_to_rev2.txt`): 0 removed, 28 moved (same test, new file), 27 added, giving 1144.

**T0 timing:** 49 passed in 21.7 s with 3 processes, against revision 1's 334.5 s. The slowest cases are the two record replays, about 6 s each.

## 10 · Controller path (unchanged)

`attach` was counted during:

- the full ft09 replay (109 steps): 0 calls;
- 5 controller steps and cards: 0 calls;
- the carry-v7 replay: 1 call, at the H1 boundary.

The seal-time reconciliation runs only at a seal (live view, H1, H2), never per step. The guard `test_v6_guard_no_dossier_is_compiled_on_the_controller_path` passes.

## 11 · Ratchet (executable lines)

| File | Revision 1 → revision 2 | Band |
|---|---|---|
| `lever_dossier_facts` | 272 → 290 | Green |
| `lever_dossiers` | 408 → 410 | Green |
| `lever_dossier_schema` | 201 → 257 | Green |
| `lever_dossier_links` (new) | 75 | Green |
| `lever_dossier_provenance` (new) | 130 | Green |
| `world_description` | 424 → 445 | Green |
| `world_report` | 183 → 186 | Green |
| `world_model_v2` | 306 → 307 | Green |
| `library_census`, `library_view`, `answer_shapes`, `product_content` | unchanged | — |

Every function is Green. The largest touched functions are `gate_view` (39), `_chapter` (33) and `open_items_facts` (28).

No gate, agenda, selection or controller file changed, so T1 `g3-directed` is not required. The shared-file note is amended (`NOTE_SHARED_FILE_WO_G4_DOSSIER_A_AMENDMENT_rev2_2026-10-17.md`).

## 12 · Remaining limits (accepted unless Sol says otherwise)

1. **Probes owed:** persistence, reversal and the current orbit phase are still `PROBE_OWED`.
2. **Unavailable:** cross-level limits.
3. **Cross-level evidence:** no committed record witnesses levers on two levels. Test 14 shows the separation by construction and by refusal.
4. **Hard kill:** a hard kill between H1 and H2 loses the H2 labels (R12).
5. **Chooser not checked against the journal:** the chooser comes from the in-memory G3 selection events, not from the journal's `G3_SELECTION` rows. Only the executor and the submitter are journal-verified.
6. **Anatomy and orbit submitters:** their answers are referenced by `answer_ref` only. These chapters name no submitter, so provenance does not apply to them.

## 13 · Package (`runs/_cowork_xfer/g4dossierA/rev2/`)

| File | Contents |
|---|---|
| `WO_G4_DOSSIER_A_rev1_to_rev2.patch` | 13 files, +1533 −427 |
| `WO_G4_DOSSIER_A_rev2_on_e8984c2.patch` | 27 files, +3193 −72; each modified file's pre-image is the `e8984c2` blob |
| `WO_G4_DOSSIER_A_rev2_slice.tar` | the 27 files |
| `SLICE_SHA256SUMS` | checksums of the slice |
| `PACKAGE_SHA256SUMS_REV2` | checksums of the whole package |
| this report, the note amendment, the fail-first records, `tiers/`, the measurements, examples, scripts and the T2 snapshot diff | — |

The revision-1 package one folder up is untouched.

If the Director commits, the trailer is:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01K95ngAHgc1pWqpMXMj7cim
```

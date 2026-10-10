# Build slice: the G3 lifecycle crashes in HYBRID worlds (k008, k013)

**Date:** 2026-10-10
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- Ruling 23 (`RULINGS_CONSOLIDATION_v4`, committed `9ee0f06`): the NAV G3 lifecycle failures. Sol is the owner; the Director reassigned this slice to Claude, under his review, to "fix the cause at the call site". The exit is that both replays complete with no crash and no false lever certification. The lifecycle invariants are preserved and the transition table is not widened.
- Ruling 22: one attributed activation establishes a lever at G3, and G4 adds to its dossier.

**Base:** `ring9-unified` @ `dcb6ce5`, where WO-L1a is committed (`virelai_gates.py` sha256 `78d8f419…`).
**Shared file:** `virelai_gates.py`. `NOTE_SHARED_FILE_G3_LIFECYCLE_2026-10-10.md` was filed before any edit.
**Line numbers** are at the base unless marked otherwise.
**Altitude:** code-level. The transition table is unchanged. No lever is certified, and nothing about certification changes.
**Out of scope:** SUB-4 and the census, as instructed.

## 0 · In one paragraph

Both crashes come from the same premature close. A HYBRID world runs G3 in two passes: it clicks every roster row (CLICK), then pilots the ego to the same rows (NAV).

In the CLICK pass, a pointer null closed the row (`G3-CLOSED`, recorded reason "entity G3 obligations complete") at `virelai_gates.py:4218`. But in a HYBRID world the row's body-contact obligation is still owed. The NAV pass then returned to that closed row:
- **k008:** a GAME_OVER mid-pursuit tried `G3-CLOSED → AMBIGUOUS`.
- **k013:** Duck's reachability release tried `G3-CLOSED → PRESUMED_UNREACHABLE`.

**The fix.** A pointer null still records its negative response. During the CLICK pass of a HYBRID world, though, it leaves the row at `NO_RESPONSE_YET`. That pass already ends in `_close_scoped_null_entities`, which closes such rows once NAV is done. G2's inherited nulls have always been left open this way (`g3_inheritance.py:77-78`).

**A second cause, found by replaying further.** The NAV pass also re-pursued rows whose G3 work is legitimately settled: levers the CLICK pass witnessed. The k013 controller, run past the saved sequence, crashes on the first such row (`G4-READY → PRESUMED_UNREACHABLE` for E0007). NAV now steps past `G3-CLOSED` and `G4-READY` rows, as it already steps past rows typed as terrain.

**A third fault, found at the end of the NAV pass (the Director's review round, §3b).** The NAV terrain map closed a row that the CLICK pass had bounded as ambiguous (E0018), and left the bound in place. The controller's inventory then listed E0018 as ambiguous while the journal held it as a scoped null, so G3 refused the inventory. The terrain close now drops the bound, as a reachability reopen (`:3264`) and a mu return (`mu_return.py:94`) already do. The controller's inventory is now accepted, and it lists exactly the nine pointer-witnessed levers.

## 1 · Reproduction

The records were built from the v2 rehearsal artifacts by `tools/record_g3_lifecycle_fixtures.py`:
- The gate-machine probes, each aligned with its own envelope.
- **k008, action 61:** the GAME_OVER that raised was never filed as a probe outcome, so its board comes from the event log.
- **k013:** Duck's refused reachability answer comes from the transcript, analysis step 396.

Up to the first NAV step, each record replays through `record_replay.replay`. From there the test drives NAV the way the live controller does: `planned_nav_step` first, then the action. At every one of the 19 k008 and 2 k013 NAV steps, it asserts that the controller's planned action equals the recorded one.

| | Live v2 run | Replay at the base |
|---|---|---|
| k008 | `LifecycleError G3-CLOSED -> AMBIGUOUS for E0001`, action 61 | Same error, same entity, same transition 61, raised at `virelai_gates.py:4089` ("target attempt interrupted by boundary") |
| k013 | Sandbox hid `G3-CLOSED -> PRESUMED_UNREACHABLE for E0001` behind the reachability answer, after transition 402 | Same error, raised at `virelai_gates.py:4449` (`_submit_reachability`). The replayed ledger matches the live ledger row for row: E0001–E0004 G3-CLOSED, 9 pointer levers G4-READY, 4 AMBIGUOUS. |

## 2 · Diagnosis: G3 closes too early. Reassessment does not need to reopen.

- **`G3-CLOSED` claims something false here.** `journal.close` records "entity G3 obligations complete" (`lever_lifecycle.py:146`). In a HYBRID world the CLICK switch hands every row to NAV (`virelai_gates.py:3461-3464`), so the row's obligations are not complete.
- **The other existing paths already leave the row open.** G2's inherited nulls stop at `NO_RESPONSE_YET`. NAV enumeration end, and a pure CLICK world's CLICK end, both close through `_close_scoped_null_entities` (`:2586-2595`).
- **Reopening would have been the wrong repair.** It would add a `G3-CLOSED → REOPENED` round trip for every null row. It would also need a reopen reason that no new evidence supplies. The row was never finished.
- **Pointer-witnessed levers are different.** Their G3 close is legitimate: ruling 22 makes one attributed activation the lever, and G4 owns repetition, mechanism and conditions. NAV must not pursue them again, so the fix is to skip them, not to reopen them.

## 3 · The diff (`virelai_gates.py`, +15 −3 in all, with §3b)

```diff
@@ _LeverTarget._advance_accounted_terrain_rows
-        """Skip current roster rows whose terrain interaction already typed them."""
+        """Skip current roster rows whose terrain interaction already typed them, or whose G3 work is settled."""
 ...
-            if entity_id not in self._terrain_roles:
+            if entity_id not in self._terrain_roles and not self._g3_settled(entity_id):
                 break
 ...
+    def _close_completed_null(self, entity_id: str, *, evidence_ref: str) -> None:
+        """Close a scoped-null row, unless a HYBRID world's NAV pass still owes it body contact (G3 lifecycle slice)."""
+        if not (self._phase == "CLICK" and self._world_type == "HYBRID"):
+            self.lifecycle_journal.close(entity_id, evidence_ref=evidence_ref)
+
+    def _g3_settled(self, entity_id: str | None) -> bool:
+        """The row's G3 work is done (G3-CLOSED or G4-READY), so NAV must not pursue it again (G3 lifecycle slice)."""
+        journal = self.lifecycle_journal
+        lifecycle = None if journal is None or not entity_id else journal.entities.get(entity_id)
+        return lifecycle is not None and lifecycle.state in {"G3-CLOSED", "G4-READY"}
@@ _LeverTarget.record_outcome, the SCOPED_NULL_RESPONSE / counter-only branch
                 journal.response(entity_id, positive=False, evidence_ref=evidence_id)
 ...
-                journal.close(entity_id, evidence_ref=evidence_id)
+                self._close_completed_null(entity_id, evidence_ref=evidence_id)
```

| Ratchet | Effect |
|---|---|
| `record_outcome` | Net zero: one line was replaced by one call |
| `_advance_accounted_terrain_rows` | Net zero |
| `virelai_gates.py` | +11 NCNB lines, in two new single-purpose methods |

These leave unchanged:
- **Pure CLICK worlds:** they close on a null exactly as before.
- **The NAV pass:** its own contact nulls close exactly as before.

## 3b · The stale bound (review round 2, +1 line)

```diff
@@ _LeverTarget._classify_terrain_rows
             if lifecycle.state == "NO_RESPONSE_YET":
                 journal.close(entity_id, evidence_ref=ref, actor="NAV_TERRAIN_MAP")
+                self._bounded_ambiguities.pop(entity_id, None)  # the close supersedes a CLICK bound
```

**Why here.** `_bounded_ambiguities` is meant to hold a row only while the row is in a bounded state. Two places already drop a row's bound when it leaves that state: the reachability reopen (`:3264`) and the mu return (`mu_return.py:94`). The terrain close was the one place that didn't. The inventory checker takes the journal as its truth (`g3_inventory.py:25-41`). The controller's template took its ambiguous list from the bound records (`:4818`). The stale record made the two disagree.

**What it does not change.**
- The terrain rule. A terrain close still moves a CLICK-ambiguous row to `G3-CLOSED`; that is Sol's existing rule at `:2857`, and the live v2 ledger shows the same close for E0018.
- The inventory checker and the controller's template.
- The mu bucket. E0018's mu entry is settled as `RESOLVED_NULL` by `settle_after_inventory` when the inventory is accepted.

**Ratchet.** `_classify_terrain_rows` +1 NCNB line.

## 4 · Tests: fail first, then pass

New file: `tests/test_g3_hybrid_lifecycle_replay.py`, five tests. The first four were run on three trees: the base, the first fix alone, and both fixes. The fifth was added in review round 2 and run before and after §3b.

| Test | Base | First fix only | Both fixes |
|---|---|---|---|
| `test_k008_pointer_nulls_stay_open_for_the_nav_pass`: after the CLICK pass, E0001, E0002, E0004, E0005 and E0006 are `NO_RESPONSE_YET` | fails (`G3-CLOSED`) | passes | passes |
| `test_k008_boundary_during_the_nav_pursuit_completes_without_a_crash`: all 60 transitions replay; E0001 goes ATTEMPTED → NO_RESPONSE_YET → ATTEMPTED → AMBIGUOUS ("target attempt interrupted by boundary"); the deferred G4 observation is filed; no lever | error (`G3-CLOSED -> AMBIGUOUS`) | passes | passes |
| `test_k013_reachability_release_completes_without_a_crash`: Duck's recorded answer releases E0001 to `PRESUMED_UNREACHABLE`, and G3 moves to the next row | error (`G3-CLOSED -> PRESUMED_UNREACHABLE`) | error (the fixture's NAV pass hits E0007) | passes |
| `test_k013_nav_pass_completes_past_the_pointer_witnessed_levers`: the controller's own loop runs the NAV pass to `NAV_ENUMERATION_COMPLETE`, using its reachability reuse; no unbounded rows; the 9 lever rows' lifecycle events are untouched by NAV | error | error (`G4-READY -> PRESUMED_UNREACHABLE for E0007`) | passes |

**Result:** 1 failed and 3 errors at the base; 2 passed and 2 errors with the first fix alone; **4 passed** with both. Runtime is about 105 s, almost all of it NAV planning. The fixtures are module-scoped, so each record replays once.

| Test (review round 2) | Before §3b | With §3b |
|---|---|---|
| `test_k013_controller_inventory_is_accepted_after_a_terrain_close`: at `NAV_ENUMERATION_COMPLETE` the controller owns the next step and answers `LEVER_INVENTORY` from the record. G3 accepts it. Its levers are exactly the nine live pointer witnesses. E0018 is a clean null (its last lifecycle event is the terrain close), not ambiguous. The ambiguous list equals the 12 `PRESUMED_UNREACHABLE` rows. No entity holds a witness without a discovery, and every `G4-READY` row holds both refs. | fails: "ambiguous_entities must exactly match explicitly bounded unresolved entities." | passes |

**Result, round 2:** 1 failed and 4 passed before §3b; **5 passed** with it. The accepted answer is a `LEVER_INVENTORY` (partial: the 12 released rows stay mu objects, per R9-R23 D13), and the gate moves on to G4-REACTIONS.

**No false lever.** In both records, the set of entities holding witness refs equals the set of lever discoveries.
- **k008:** none.
- **k013:** exactly the live ledger's nine `LEVER_FOUND` rows, both at the end of the NAV pass and after the accepted inventory. Every `G4-READY` row holds both a witness and an answer ref.
- **E0001**, in both, ends without a witness.

## 5 · Verification

| Check | Result |
|---|---|
| The new tests | 5 passed (§4) |
| Full cloud suite, round 1 (four tests) | 641 passed, 1 skipped, 0 failed (637 + 4). The Director's Mac floor matched: 641 passed, 1 skipped. |
| Full cloud suite, round 2, Python 3.12, 91 files (`--ignore` of `test_physics_grammar_contract.py`) | **642 passed, 1 skipped**, 0 failed (637 + 5) |
| Director's Mac floor, round 2, same exclusion | **642 passed, 1 skipped**, 14 dependency deprecation warnings, 983.37s (0:16:23) |
| ruff | No new findings. Two findings already present at the base remain (F402, F601). |
| Determinism | The fixture builder reproduces both `.json.gz` files byte for byte. |

## 6 · Honest ledger: found, not fixed (outside this slice)

1. **F-1. The stale bound after a terrain close.** Fixed in review round 2 (§3b), with a fail-first test.
   - **F-1a (open): the same stale bound has a second, untested site.** The `record_outcome` NAV pass can re-attempt a CLICK-ambiguous row (the attempt set at `:3765` includes `AMBIGUOUS`) and then close it on a contact null, leaving its CLICK bound in place. The inventory would then be refused the same way.
     - In k013 the reachability release overwrites those bounds first, so the replay never reaches this site, and I did not change it without a failing test.
     - Probable fix: the same pop, on the same close.
   - **F-1b (judgment, not a defect): E0018 is reported as a clean null on terrain evidence.** Its click was `UNRESOLVED_ATTRIBUTION`. The terrain map saw the ego traverse its integer (FLOOR) and closed it.
     - Under Sol's existing rule, terrain evidence settles a CLICK-ambiguous row. A floor that also reacts to a click is not ruled out by that evidence.
     - Nothing is certified as a lever either way.
     - The alternative is for the terrain map to leave bounded rows ambiguous. That changes the terrain rule, so it is a NAV-line decision for Sol and the Director, not part of this slice.
2. **F-2. A NAV pursuit that ends at the navigation limit leaves its row `ATTEMPTED`.**
   - **What happens.** `_unbounded_entities` counts such a row as unbounded. This is already so in pure NAV worlds.
   - **Why it matters now.** HYBRID rows used to sit falsely at `G3-CLOSED` from the CLICK pass. Now they can show this honestly. Neither k008 nor k013 reaches it.
   - **Owner:** Sol, together with ruling 22's caution 1 (an explicit unresolved disposition).
3. **F-3. Each controller NAV step costs about 3 s of CPU on a 64×64 grid.** The k008 replay spends about 55 s on its 19 NAV steps, in `planned_nav_step` and NAV `record_outcome`. That matters against the Kaggle runtime budget. Owner: Sol, for profiling.
4. **The settled-row skip is a judgment the Director can veto.** Its warrant is ruling 22, which settles a pointer-witnessed lever at G3. If the Director wants the body channel tried on those levers, that work belongs to G4 and not to G3's NAV pass.

## 7 · Next

1. **Director verification complete:** the round-2 files are in the tree. The targeted Mac set passed 16 tests; the Mac floor passed 642 tests with 1 skipped (§5).
2. **File this slice** on `ring9-unified` with explicit paths, then fast-forward `main`.
3. **Return to Apex on 13 Oct**, per ruling 23, with F-1a, F-1b, F-2 and F-3 attached.

— Claude, Alpha build seat (click line), 2026-10-10

# Build slice: replay compatibility guard. A controller-driven legacy replay executes a HYBRID CLICK-phase confirmation's bound click

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat), signed
**For:** Sol's review; the commit is **held**.
**Governs:**
- Sol's follow-up to the HYBRID CLICK repair: a fail-first test for a HYBRID CLICK-phase confirmation; the controller executes the gate's bound click; NAV selection and its handoff stay off until this path is verified.
- `NOTE_SHARED_FILE_WO_G3_DIRECTED_NAV_2026-10-11`, amendment 2, filed before the edit.

**Base:** the HYBRID CLICK repair (`controller_executor.py` sha `7ec5146d0174`, Mac floor 758 passed, 1 skipped), on `db8a657`.

## Sol's ruling (2026-10-11)

**Keep this as a replay compatibility guard, in its own separate slice, labelled as such.** Live G3 does not request a CLICK confirmation. This two-line change fixes a controller-driven legacy replay. It stays uncommitted until its Mac floor runs.

## 0 · Read this first: the premise, corrected

**A live machine never produces this case.**
- The gate declares a CLICK-phase confirmation only when `machine._legacy_confirmation_replay` is true (`virelai_gates.py:4141-4160`).
- The constructor's comment (`:6505-6509`) says live machines leave that flag false. `record_replay` sets it only for historical records that hold legacy G3 dossier answers. In those replays the controller never acts.
- A live machine follows the unified G3 law instead: one attributed CLICK activation is the witness, and G3 goes on to the next row with no confirmation. I checked this on k013, where a synthesized local response on the head click gave `LOCAL_LEVER_WITNESS` and the next capability was the next ranked click.

**So this change is a parity guard, not a live-play repair.** It makes a legacy-confirmation machine driven by the controller (as several test fixtures are) behave in a HYBRID world as it already does in a CLICK world. It does not change live play. Sol may prefer to drop it and record "examined: unreachable live" instead. Either way, the floor no longer leaves the question open.

## 1 · What changed

| File | Change |
|---|---|
| `inference/framework/controller_executor.py` (shared) | In `_nav_step`'s G3 branch, a `CONFIRM_LEVER_WITNESS` capability that binds an action goes to `_bound_step`: the controller executes the gate's own bound click. A NAV-phase confirmation binds no action and keeps its `planned_nav_step` route, unchanged. That is 2 NCNB lines (`_nav_step` 101 → 103, still below `db8a657`'s 111). |
| `tests/test_g3_hybrid_click_pass.py` | `HybridRun` now takes a record and a cut (k008 at 37 remains the default). Adds one test (§2). |

**Not touched:** `virelai_gates.py`, the lifecycle, NAV selection, the NAV handoff and `planned_nav_step`.

## 2 · Fail-first, then passing

**The harness:**
- **World:** k013 (HYBRID; ruling 10), replayed to transition 378, the start of G3's CLICK pass on life 8. The G3 entity ledger is in step with the frame for that whole pass (379–400).
- **Machine:** the legacy-confirmation flag is set.
- **Driver:** the production `ToolAgent.analyze`, with the handoff off so the turn count is exact.
- **Responses:** the controller's coverage click on the head (`E0001`, `ACTION6 (51,15)`) gets a synthesized local response on that object, so the gate declares the witness and a CLICK-phase confirmation (`G3-LEVERS:CONFIRM:M0016:E-1ad42d530c2865c8`) bound to the same click. The confirmation's response is synthesized the same way.

**On the repair (`7ec5146d0174`): 1 failed, 3 passed.**
- The confirmation step went to Duck: "G1 evidence does not yet support a deterministic route step".
- The bounded route checkpoint then spent one model request and ended the turn with `controlled_stop='g3_route_retry_exhausted …'`, so no action was taken.
- In submission mode, that controlled stop rests the level in normal play (ruling D-3, `rest_on_controlled_stop`). This harness does not exercise that.

**After this change: 4 of 4 pass.** The confirmation turn produces:
- exactly one controller action, the witnessed click `ACTION6 (51,15)`, with no model call;
- an envelope with executor `CONTROLLER` and purpose `CONFIRM_LEVER_WITNESS`;
- the same probe id in the envelope, the receipt and the transition row, equal to the gate's declared confirmation id;
- the same evidence in the receipt and the row, at transition 380;
- confirmation `SUPPORTED`, citing the witness evidence, and the pending confirmation cleared. `E0001` is `G3-CLOSED`, and the gate asks for its legacy dossier.

## 3 · Verification

| Run | Result |
|---|---|
| Cloud, `test_g3_hybrid_click_pass.py` | 4 passed |
| Cloud, focused (per-file counts from the full run) | `test_g3_hybrid_click_pass` 4, `test_g3_directed_click` 47, `test_memory_m2` 21, `test_g3_hybrid_lifecycle_replay` 5, `test_nav_branch_foundations` 37, `test_ring9_nav_cell_site_targeting` 2, `test_sub2_submission_hardening` 8, `test_g3_scheduler` 16 and `test_g3_checkpoint` 5 (the legacy-confirmation suites): **145 passed** |
| **Cloud, full** (Python 3.12, 99 files) | **759 passed, 1 skipped**, 0 failed (= 758 + 1) |
| **Mac, focused** (2026-10-11) | **145 passed** |
| **Mac, full** (2026-10-11) | **759 passed, 1 skipped**, 0 failed (21m 35s) |
| ruff | clean |

## 4 · Findings for Sol

1. **The premise in §0.** Keep this guard, or drop it and record "examined: unreachable live". It is cheap either way. I built it as directed.
2. **Pre-existing and more serious: on k008, the G3 entity ledger is out of step with the frame for the whole of G3.**
   - On the replay path (`record_like_live`), all 28 of k008's G3 ledger observations carry "before frame did not match the ledger's current frame". At the cuts I measured (37, 42 and 60), the ledger's grid differed from the real frame by 34 to 83 cells.
   - When the frames do not match, `EntityLedger.scope` drops the pre-action pointer owner (`entity_observation.py:466`). No CLICK can then be attributed (`POINTER_OWNER_UNRESOLVED` → `UNRESOLVED_ATTRIBUTION`), so **no CLICK witness is possible on k008**, whatever the click shows. I demonstrated this with a synthesized local response on `E0004`.
   - k008 enters G3 on life 2. k013 also shows mismatches (312 of 366 ledger observations), but its ledger is back in step by its CLICK pass on life 8; carry-v7 (life 1) shows none.
   - **Hypothesis, not verified:** `_LeverTarget._ensure_entity_ledger` builds the ledger from `counter.initial_grid` plus `counter._lossless_outcomes` (`virelai_gates.py:3124-3150`). A life reset before G3 may not be among those outcomes, which would leave the ledger on a stale board.
   - It touches G3's evidence substrate, so it calls for a read-only diagnostic before any fix. I have not changed anything for it.
3. **Harness note.** The k008 tests of piece 1 pass despite (2): every k008 CLICK outcome is `COUNTER_ONLY_RESPONSE`, which needs no pointer owner. Their assertions concern ownership, envelopes and receipts, not attribution.

## 5 · Next

1. **Done:** piece 1 is committed as `4a18c4d`.
2. **Ruled:** keep this as a replay compatibility guard (above). The ledger diagnostic precedes NAV selection (`DIAGNOSTIC_G3_LEDGER_FRAME_SYNC_v1_2026-10-11`).
3. The Director copies this guard and runs the focused tests and the Mac floor. Then it is committed on its own.
4. NAV selection and its handoff stay off until G3 can trust its observations.

— Claude, Alpha build seat

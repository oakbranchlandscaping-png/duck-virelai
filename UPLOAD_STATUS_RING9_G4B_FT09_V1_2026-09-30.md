# Ring 9 G4-B, ft09 v1: upload status

**Prepared:** 2026-09-30
**Author:** Claude (Alpha build seat), signed. The Director runs the upload commands.
**Status:** packaged and verified; not yet uploaded.
**Revisions carried:** R9-R06 to R9-R12. R9-R12 is G4-B (levers together), the clean stop at the
ladder's end, and the M-5 review fixes (`BUILD_SLICE_R9_R12_G4B_LEVER_RELATIONS_2026-09-29.md`).

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-g4b-ft09-v1` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-g4b-ft09-v1` (private); accelerator `NvidiaRtxPro6000`; internet off |
| Package | `kaggle/ring9-g4b-ft09-v1/`, delivered as `ring9-g4b-ft09-v1.tar.gz` (SHA-256 `358ec3c3…9a01213`) |
| Packager | `tools/package_ring9_g4b_ft09.py` |
| Source commit | `e1636b1622b3cd927c33a45fb6a6abbbe00eb3d4` (R9-R12) |
| Source export | `src_e1636b1.tar.gz`, SHA-256 `5e6b0fb3…2669e16f`. It is identical to the cloud tree. |
| Package manifest SHA-256 | `016598b7590bc5a7864d01e32de4e522f4f314e546f266c6f0695146db645185` |
| Source manifest SHA-256 | `9f6089f551a01d6b3036a70087799e61181b2163a19164f5812d95673a2c8db0` |
| Base | The committed `ring9-memory-ft09-v1` package (`75cd20d`, manifest `86018ac2…fa63`). The packager checks it before building. **The world, model and budget are unchanged, so only the source differs between the two live runs.** |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM; context 65,536 tokens; tool output 1,024 tokens |
| World and budget | `ft09-0d8bbf25`; one pass; concurrency 1; 200 environment actions and 10,800 s of behaviour time after model setup |

## The question

After G4-A, does Duck work out how ft09's levers affect each other? In G4-B:
- Duck freezes each prediction;
- the controller takes the prediction's one action;
- the gate grades it on the counter-masked board.

Duck then describes the lever set in plain language, on supported evidence only, and the run should
end cleanly where the built ladder ends.

## Preregistered criteria

These are frozen in `checkpoint-preflight.json` and `RUN.md`. All are graded from artifacts.

- **M5-1 and M5-2:** every card within the 16,200 slot budget; G0 to G4.1 with zero model calls;
  Duck's first turn is the orientation.
- **G2 and G3:** as in memory v1. Record the lever count.
- **A-1 to A-3 (G4-A):** as before, including the re-study after a same-level death (D4).
- **B-1 (G4-B protocol):**
  - G4-B opens only after G4-A is COMPLETE.
  - Every G4-B action is exactly the action of a frozen prediction, taken by the CONTROLLER.
  - Each prediction is graded on a transition after it was frozen.
  - Duck takes no G4-B action itself.
- **B-2 (grading fidelity):** each prediction's per-lever outcomes and grade, recomputed from the
  masked frames, match the record.
- **B-3 (G4-B closure):**
  - every lever is pressed in a graded prediction;
  - the description is accepted;
  - every relation cites only SUPPORTED predictions that pressed or named its levers;
  - `open_conditions` equals the recorded missing conditions;
  - contradicted predictions stay on the record.
- **E-1 (the clean stop, R9-I02):**
  - `solver_note` begins `planned_stop:`;
  - the run is not crashed;
  - no model request is made after the last gate closed.
- **N-1:** no gate idles without a legal move.
- **R (reported, not graded):**
  - Duck's description, verbatim;
  - every prediction;
  - how many predictions tested a lever while another lever was away from its start state;
  - turns, requests, minutes and actions per gate;
  - wakes, deaths and re-studies;
  - bar remaining;
  - largest card per gate.
- **I1 to I4:** infrastructure, as before. I2 is the byte-identical execution receipt.

**Offline reference (not a graded prediction).** On the world the live v1 record defines, the
controller repeats all 108 live actions. A card-only Duck then freezes 8 predictions, all
SUPPORTED, its description is accepted, and the run stops cleanly with no further model call.

## Verification before upload

- **The packager's own checks passed.**
  - Every stage's marker, R9-R06 to R9-R12, is present in the packaged source.
  - The base notebook's controller-executor check is present exactly once.
  - The secret guard is clean.
  - **The request preflight (T10)** puts the worst-case single request at 33,158 tokens against
    the 65,536-token window. This is unchanged, because G4-B fits in the same slot budget.
- **`tools/verify_kaggle_package.py`:** 8/8 passed, including the bundled source being
  byte-identical to the `e1636b1` export.
- **`tools/simulate_kaggle_preflight.py`:** the notebook's real start-up cells ran in the nested,
  zip and direct mount layouts. Each verified the manifest, the world allowlist and the receipt,
  and printed `taaf.kaggle: controller executor on`.
- **Negative control:** one byte appended to `g4b_gate.py` in a copy was rejected by both checks.
  The verifier failed it 4/8. The notebook stopped at "Source manifest verification failed".
- **Tests at `e1636b1`:** cloud 480 passed, 1 skipped; Mac 481 passed.

## Risks stated before the run (hypotheses, not findings)

1. **Duck may do only the minimum.** It could press each lever once, predict "only its own tile
   changes", and describe independence. That would pass B-1 to B-3, and R would record it.
2. **G4-B costs about one Duck turn per prediction**, roughly 40 seconds each. Eight or more
   predictions take about 6 minutes or more.
3. **The bar.** About 12 ticks remain after G4-A if the run follows v1. More than about 12
   predictions will cost a life. A death is recoverable: the graded prediction stands, the board
   resets, and the state labels read the reset board.
4. **A live Duck may misread the prediction vocabulary** (`STEPS` / `CHANGES` / `UNCHANGED`).
   A refused prediction costs a turn, not an action; the refusal names the field.
5. **F4 is open.** The preflight bounds one request, not a turn with many requests. The idle loop
   that reached 48k tokens in v1 is now closed by the clean stop.

— Claude, Alpha build seat, 2026-09-30

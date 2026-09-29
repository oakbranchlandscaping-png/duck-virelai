# Ring 9 memory, ft09 v1: upload status

**Prepared:** 2026-09-29
**Author:** Claude (Alpha build seat), signed. The Director runs the upload commands.
**Status:** packaged and verified; not yet uploaded.
**Revisions carried:** R9-R06 to R9-R11. These are memory stages M-0 to M-4 and the live-readiness
prompt line. This is stage M-5 of `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`.

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-memory-ft09-v1` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-memory-ft09-v1` (private); accelerator `NvidiaRtxPro6000`; internet off |
| Package | `kaggle/ring9-memory-ft09-v1/`, delivered as `ring9-memory-ft09-v1.tar.gz` (SHA-256 `10af3b32…81a7c6`) |
| Packager | `tools/package_ring9_memory_ft09.py` |
| Source commit | `8ca9fc94e012839db7bbe1ffe10733a75277a882` (R9-R11) |
| Source export | `src_8ca9fc9.tar.gz`, SHA-256 `b59be1ef…2f8032a76`. It is identical to the cloud tree. |
| Package manifest SHA-256 | `86018ac236fef9176cd353867a829e4e0d7e147515c03d36ecff8c3d4e64fa63` |
| Source manifest SHA-256 | `b08d10394bfca789f826667d36d42481775d71980d586b766ae85103017c8889` |
| Base | The committed `ring9-g4-ft09-guided-v2` package (`ceab138`, manifest `d4047476…a476`). The packager checks it before building. **The world, model and budget are unchanged, so only the source differs between the two live runs.** |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM; context 65,536 tokens; tool output 1,024 tokens |
| World and budget | `ft09-0d8bbf25`; one pass; concurrency 1; 200 environment actions and 10,800 s of behaviour time after model setup |

## The question

With Virelai memory, does ft09 reach G4-A with Duck spending its turns only on judgment, and every
card within budget? Memory here means five things:
- a bounded slot-built card;
- the controller executor from G0 through the G4-A lever runs;
- recall;
- the orientation turn;
- the lives rule.

## Preregistered criteria

These are frozen in `checkpoint-preflight.json` and `RUN.md`. All are graded from artifacts.

- **M5-1:** no card over the 16,200-character slot budget, and the 24,000 guard never fires.
- **M5-2:** G0 through G4.1 close with zero model calls, and Duck's first turn is the orientation.
- **G2-1 to G2-3:** the counter axiom, purity, and the admissible trigger. Record whether the
  label was the controller's.
- **G3-1:** at least two ft09 tiles are witnessed as levers, with no UNRESOLVED_ATTRIBUTION, and G3
  re-clicks no object G2 saw as a total null (D5).
- **G4-1:** every G3 lever has a G4.1 anatomy by the controller.
- **A-1 to A-3:** G4-A closure, audit fidelity (with executor on every press), and explanations
  scoped to what was observed.
- **L-1 (the open ft09 question):** does an empty counter bar end the life? If a death interrupts
  a study, the lever is re-studied (D4).
- **N-1:** no idle without a legal move.
- **R (reported, not graded):**
  - Duck turns and requests per gate;
  - minutes to G3 and to G4-A;
  - actions per gate;
  - every stop-and-wake reason;
  - bar remaining;
  - largest card per gate;
  - orientation notes;
  - extra-run requests.
- **I1 to I4:** infrastructure checks. I1 includes the executor being on, with the protocol stamp.

**Offline reference (not a graded prediction):** G4-A SATISFIED in 92 actions, with 7 Duck turns
(orientation, 5 orbit explanations, 1 counter-budget wake). G0–G3 take 72 actions and 0 model
calls. This runs on the v2 record's law, continued by hypothesis.

## Verification before upload

- **The packager's own checks passed.**
  - Every memory stage's marker is present in the packaged source. Run against plain `3f29fd0`, it
    refused, because the R9-R11 line was missing.
  - **The request preflight (T10)** ran against the packaged source: the worst-case request is
    33,158 tokens against the 65,536-token window. The packager refuses otherwise.
  - The secret guard is clean.
- **`tools/verify_kaggle_package.py`:** 8/8 passed, including the bundled source being
  byte-identical to the `8ca9fc9` export.
- **`tools/simulate_kaggle_preflight.py`:** the notebook's real start-up cells ran in all three
  mount layouts (nested, zip, direct). Each verified the manifest, the world allowlist and the
  receipt, and printed the new line `taaf.kaggle: controller executor on`. The notebook now refuses
  to start if `VIRELAI_CONTROLLER_EXECUTOR=0`.
- **The packaged solver** builds the ToolAgent with the executor on. With
  `VIRELAI_CONTROLLER_EXECUTOR=0` it is off, as designed.
- **Negative control:** one byte appended to `controller_executor.py` was rejected by both checks.
  The verifier failed it 4/8. The notebook preflight stopped at "Source manifest verification
  failed".
- **Tests at `8ca9fc9`:** cloud 469 passed, 1 skipped; Mac 470 passed.

## Risks stated before the run (hypotheses, not findings)

1. **ft09 beyond the recorded tiles is extrapolated.** The offline 92-action path assumes the five
   recorded tiles are the only levers.
2. **The bar.** On the continued law, the full five-lever protocol empties the counter bar during
   the fifth lever. If an empty bar ends the life, D4 re-studies that lever in the next life, at
   the cost of the actions spent.
3. **Duck's judgment turns are new live.** The orientation turn and the explain-not-press handoff
   are new to Duck live. R9-R11 tells Duck how to take them every turn, and the refusals name the
   right call; a misstep costs a turn, not an action.
4. **The G2 label depends on the record's trigger class.** If G2's live record is OPEN or
   IRREGULAR, Duck writes the label. This did not arise on ft09 v2 (EFFECTIVE_TRANSITIONS_ONLY).
5. **The budget thresholds are provisional:** 2 ticks, 10 actions, 120 s.
6. **A declared end still idles until the deadline** (R9-I02 open).

— Claude, Alpha build seat, 2026-09-29

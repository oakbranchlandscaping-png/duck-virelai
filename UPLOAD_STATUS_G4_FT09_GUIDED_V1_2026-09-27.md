# Ring 9 ft09 guided v1 upload status

**Prepared:** 2026-09-27
**Author:** Claude (Alpha build seat), signed. Upload commands are executed by the Director.
**Status:** uploaded, run on Kaggle (notebook version 1) and reviewed on 2026-09-28. Result: G2 closed live under axiom A1; the run then crashed at G3 entry on the 24,000-character card guard (card was 67,939 characters). P not met, so the G4 criteria are ungraded. Review: `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`. Successor: `ring9-g4-ft09-guided-v2`, carrying R9-R04. This package carries revision R9-R03.

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v1` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v1` (private); accelerator `NvidiaRtxPro6000`; internet off |
| Package | `kaggle/ring9-g4-ft09-guided-v1/` |
| Packager | `tools/package_g4_ft09_guided.py` |
| Source commit | `3c89c2191190b07810c9f3f7b92b7d1617157a3a`: G4-A stated target (`fcc7f11`), plus the G2 counter axiom and the no-legal-move guard |
| Package manifest SHA-256 | `ed456471b668af375a0a466b39097f091cd789dc23a466ef38785ea88608b1d8` |
| Source manifest SHA-256 | `21251934302a19dc95faf0edd3703007f2c256cb98d071f7c9d8601ab5cf48ec` |
| Base | The committed `ring9-g4-ft09-phase1-v1` package (`7778750`; manifest `afd49db1…0576`, checked by the packager before building). Its notebook ran cleanly on Kaggle on 2026-09-27. |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM |
| World and budget | `ft09-0d8bbf25`, one pass, concurrency 1; 200 environment actions and 10,800 s of behavior time after model setup. Same as the scripted ft09 run. |

## The question

Stated targets replace scripted moves. The run tests whether:
- Duck finds, labels and masks the counter with a pure mask (axiom A1);
- the scripted G3 sweep then passes;
- Duck, by its own presses, studies every lever to a confirmed end point (G4-A);
- no controller state idles without a legal move (axiom A2).

This is the first live run of any stated-target gate.

## Preregistered criteria

Frozen in `checkpoint-preflight.json` and `RUN.md`:

- **G2-1:** G2 closes under axiom A1, or as not-observed after full coverage.
- **G2-2:** mask purity, recomputed from the artifacts.
- **P:** G3 closes with at least two levers. This is the precondition for grading G4.
- **A-1:** every lever is confirmed or diverged and explained, or recorded as interrupted.
- **A-2:** audit fidelity from the gate events.
- **A-3:** explanations are scoped to what was observed.
- **N-1:** no idle without a legal move; the watchdog ends any such stall.
- **R:** reported only: Duck's choices, and actions and time per gate.
- **I1–I4:** infrastructure checks.

## Verification before upload

- `tools/verify_kaggle_package.py`: 8/8 passed, including bundled source byte-identical to the
  Director's `git archive` export of `3c89c21`.
- `tools/simulate_kaggle_preflight.py`: the notebook's real start-up cells ran in all three mount
  layouts (nested, zip, direct). Each verified 198 source files, the ft09 world allowlist and the
  execution receipt, and set the 10,800 s window from benchmark start.
- Negative control: one appended byte in `g4_guided.py` was rejected at manifest verification.
- The export at `3c89c21` passes the full suite in the cloud: 396 passed, 1 skipped. Mac: 385
  passed.
- Packaging defect found and fixed before this build: unpickling the benchmark had written
  bytecode into the bundle, overwriting some of the `.pyc` files the repo tracks. The byte-identity
  check caught it (32 diffs). The packager now imports with `sys.dont_write_bytecode` from the
  export, and the rebuilt package leaves the export untouched.

## Risks stated before the run (hypotheses, not findings)

1. **Guided G2 may spend many actions finding the counter.** In the scripted run the bar ticked only
   on the 2 of 56 clicks that hit controls. If Duck clicks non-controls for long, the budget goes to
   G2.
2. **Duck's choice quality under a stated target is unmeasured.** Broken runs, or presses other than
   the lever click, would slow G4-A. They cannot corrupt it.
3. **A declared end still idles** until the deadline (A2 open item).

— Claude, Alpha build seat, 2026-09-27

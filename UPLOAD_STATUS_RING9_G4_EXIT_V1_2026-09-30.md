# Ring 9 G4 CLICK exit v1 (ft09 + vc33): upload status

**Prepared:** 2026-09-30
**Author:** Claude (Alpha build seat), signed. The Director runs the upload commands.
**Status:** packaged and verified; not yet uploaded.
**Revisions carried:**
- R9-R06 to R9-R14.
- R9-R13 is G4-C, the lever law set (`BUILD_SLICE_R9_R13_G4C_LEVER_LAW_2026-09-30.md`).
- R9-R14 fixes the two defects found in the G4-B live run: F1 (a refusal is cut off before Duck reads it) and F2 (a stale freeze stamp) (`BUILD_SLICE_R9_R14_LIVE_FIXES_2026-09-30.md`).
**Governing ruling:** `BUILD_PLAN_G4_CLICK_COMPLETION_v11_2026-09-30.md`. The CLICK branch of G4 closes if and only if both ft09 and vc33 end level 1's G4 with a COMPLETE `LeverReactionLawSet`.

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-g4-exit-v1` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-g4-exit-v1` (private). Accelerator `NvidiaRtxPro6000`; internet off. |
| Package | `kaggle/ring9-g4-exit-v1/`, delivered as `ring9-g4-exit-v1.tar.gz`. SHA-256 `a778f999730fa61fa1349c82ac3e78b928e3025295d5d14ce359c6f7b4e89565`. |
| Packager | `tools/package_ring9_g4_exit.py` |
| Source commit | `d2bf323eaf2fe08a0b64b058e1b958417f344fd1` (R9-R14) |
| Source export | `src_d2bf323.tar.gz`, SHA-256 `ec1c94c7…2fc041d`. It is identical to the cloud tree that was tested. |
| Package manifest SHA-256 | `80fac5e2ab427385ce39f15b9f48d849530dc5539dfecc8076cc2cd2e2e32b38` |
| Source manifest SHA-256 | `cd8cd84fbd2bda795f71820f354c4fe0454338b9e05969f1b109d85c4a647828` |
| Base | The committed `ring9-g4b-ft09-v1` package (`08d9afc`, manifest `016598b7…5185`). The packager checks this base before it builds. |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM. Context 65,536 tokens; tool output 1,024 tokens. |
| Worlds and budget | `ft09-0d8bbf25` first, then `vc33-5430563c`. One pass each, concurrency 1. Per world: 200 environment actions and 10,800 s of behaviour time. The notebook's run deadline is 21,600 s. |

**What changed from the base:**
- the source (`d2bf323`);
- the checkpoint world list (vc33 is added);
- the run deadline (10,800 s becomes 21,600 s);
- the names and the claim texts.

Model, per-world budget and settings are the same as the G4-B run.

## The question

Does each world end level 1's G4 with a supported lever law set? That means three things:
1. every lever has been studied alone (G4-A);
2. the levers' effects on each other have been tested with graded predictions, and Duck has described them (G4-B);
3. the description correctly predicts one case nobody has tested yet (G4-C).

## Preregistered criteria

The criteria are frozen in `checkpoint-preflight.json` and `RUN.md`, graded from artifacts, per world unless noted.

- **M5-1 and M5-2:**
  - every card stays within the 16,200-character slot budget;
  - G0 to G4.1 finish with zero model calls;
  - Duck's first turn is the orientation, and it is accepted within 2 turns. This is the F1 fix under test.
- **G2 and G3:** the same as the earlier runs. Also record whether the counter's trigger class was OPEN, because that makes the label Duck's (deviation 1).
- **A (G4-A):** the same as the earlier runs, including re-studying a lever after a same-level death.
- **B (G4-B):**
  - every G4-B action is exactly a frozen prediction's action, and the CONTROLLER takes it;
  - each prediction is graded on a later transition, with a current freeze stamp. This is the F2 fix under test;
  - the grades re-derive from the masked frames;
  - every lever is pressed in a graded prediction;
  - the description is accepted, and each relation cites only SUPPORTED predictions;
  - `open_conditions` equals the recorded missing conditions.
- **C (G4-C):**
  - each law prediction is untested and names valid relations;
  - the CONTROLLER takes it, and it is graded;
  - a CONTRADICTED prediction reopens G4-B and stays on the record;
  - the gate closes on a SUPPORTED prediction with the `LeverReactionLawSet` COMPLETE, or on a level change.
- **E:** each world ends with `planned_stop:`, not crashed, and makes no model request after its last gate closes.
- **EXIT (both worlds together):** the CLICK branch closes if and only if both worlds end with a COMPLETE `LeverReactionLawSet`.
- **N-1:** no gate idles without a legal move.
- **R (reported, not graded):**
  - each world's description (verbatim) and its law test;
  - every prediction;
  - any reopening of G4-B;
  - Duck's turns, requests and minutes per gate;
  - deaths and re-studies;
  - bar remaining;
  - the largest card per gate;
  - for vc33: its lever count, its lever classes and its counter trigger class.
- **I1 to I4:** infrastructure checks, as in the earlier runs. I2 is the byte-identical execution receipt.

**Offline reference (not a graded prediction).** On the world defined by the live ft09 record, the controller repeats the live actions. A card-only Duck then gets:
- 8 G4-B predictions, all SUPPORTED;
- an accepted description;
- one G4-C law test, SUPPORTED;
- a COMPLETE law set;
- a planned stop.

There is **no offline reference for vc33** on the memory stack.

## Verification before upload

**The packager's own checks passed:**
- Every stage marker from R9-R06 to R9-R14 is present in the packaged source, including G4-C's `LeverLawTarget` and the R9-R14 `_refused_state` and `_high_step`.
- The notebook's deadline is `timedelta(seconds=21600)`.
- The secret guard is clean.
- The request preflight (T10) gives a worst case of 33,158 tokens for a single request, unchanged.

**`tools/verify_kaggle_package.py`:** 8/8 passed. This includes a check that the bundled source is byte-identical to the `d2bf323` export (0 diffs).

**The notebook's real start-up cells ran in the nested, zip and direct mount layouts.** Each run:
- verified the source manifest (215 files);
- verified the world allowlist `['ft09-0d8bbf25', 'vc33-5430563c']`;
- verified the execution receipt;
- printed `controller executor on`;
- loaded the solver from the mounted bundle;
- reported 200 actions and 10,800 s per world.

**A finding in the simulator, not the package.** The stock `simulate_kaggle_preflight.py` stands in for Kaggle's offline game list with the games in the benchmark pickle, and that pickle holds only ft09. So the stock simulator stops with "Checkpoint world mismatch" on any world that isn't ft09.
- **What Kaggle does instead:** it builds the game list from the competition's environment files, through `_offline_games`. That code refuses any world that is missing, before the run starts.
- **Evidence that vc33 is there:** `ring9-g4-phase1-drain-v1` ran on Kaggle and logged "checkpoint worlds verified: ['vc33-5430563c']".
- **How the simulation above was run:** with a scratch copy of the simulator that makes a stand-in game for vc33. The committed tool is unchanged.

**Two worlds in one run.** The solver builds a new analyzer for each game (`solver._make_analyzer`), and with it a new gate machine. vc33 therefore starts from a clean ladder, and a planned stop on ft09 ends only ft09's game.

**Negative control.** In a copy of the package, I appended one line to `g4c_gate.py`. Both checks rejected it:
- the verifier failed it, passing only 4 of 8 checks;
- the notebook's start-up stopped at "Source manifest verification failed".

**Tests at `d2bf323`:** cloud 486 passed, 1 skipped; Mac 487 passed.

## Risks stated before the run (hypotheses, not findings)

1. **vc33 is new to the memory stack.** Its G2 counter may have an OPEN trigger class (deviation 1), and its G3/G4.1 behaviour came from older stacks. A stall before G4-B leaves B and C ungraded for vc33, and EXIT is then not met.
2. **On vc33 a lever may close the level.** A level change during G4-A or G4-B closes the study (G9 is not built) and ends the run cleanly. The law set would then not be COMPLETE, and EXIT would not be met by vc33. That would be a real result about vc33, not a defect.
3. **On ft09, G4-C is easy.** On independent toggles almost any action from the current board is untested (as the R9-R13 slice notes). ft09 is expected to pass; vc33 is the real test.
4. **A contradiction on vc33 reopens G4-B.** Each round costs Duck turns, and the bar may cost lives. The 200-action budget should hold, but the number of rounds is not bounded.
5. **Time.** ft09 took about 25 minutes of Duck time through G4-B. The 21,600 s run deadline leaves vc33 about 5 hours, and its per-world cap is 10,800 s.
6. **F4 is still open.** The preflight bounds one request, not a turn made of many requests.

— Claude, Alpha build seat, 2026-09-30

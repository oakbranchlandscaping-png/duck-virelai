# Infrastructure record: G4 Phase-1 drain Kaggle checkpoint

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Package:** `kaggle/ring9-g4-phase1-drain-v1/` (committed `777dc39`)
**Packager:** `tools/package_g4_phase1_drain.py` (committed `777dc39`)
**Source:** `f8a967e` (S1 return edge), exported with `git archive`
**Status:** packaged, verified, uploaded, notebook version 1 running. Behavior ungraded.

## Why this went to Kaggle before an OpenRouter pass (authorized deviation)

`BUILD_RHYTHM.md` and protocol §8 say not to promote to Kaggle until a focused one-world
OpenRouter slice passes. That rung was attempted on 2026-09-26 and could not run: the final
attempt (`runs/20260926_200109_ring9-g4-s1-phase1-drain-vc33-openrouter-fast-20260926-v2`)
returned OpenRouter 402 `weight_exceeds_budget` on the first request. OpenRouter pre-authorizes each
request at its maximum cost, and at this config (65,536-token context, 2,048 max output, pinned
provider) that exceeded the account balance. It retried for the full window and executed zero
actions. Earlier attempts that day failed on launch mechanics and on `in_flight_budget_exhausted`.

The Director ruled on 2026-09-27 that Kaggle, where the Tufa harness is designed to run, is the
test venue. **Consequence for grading:** this run is both the first live test of S1 and the first
Kaggle test of the post-v3 G3 repairs on the exact model. If it fails, controller defects and
serving-path effects are not separated by a prior OpenRouter pass; use protocol §10's failure
classes to locate the first broken layer before drawing any conclusion about S1.

## Derivation

The packager clones the frozen `ring9-g3-vc33-closure-v3` package, whose notebook already carries
the final-form receipt binding, the benchmark-start deadline and the nested `src.zip` mount branch
(proven on Kaggle by the G3-v3 run of 2026-09-24). The G3→G4 transform only:

- relabels the dataset, kernel, benchmark and receipt to `ring9-g4-phase1-drain-v1`;
- widens the budget from 96 actions / 2,700 s to **160 actions / 7,200 s**;
- rewrites the receipt marker to `G0-G4 execution receipt verified`;
- restates the claim, claim limits and the preregistered S1 criteria in
  `checkpoint-preflight.json`, `RUN.md` and `preamble.txt`;
- re-vendors source and regenerates both manifests and the receipt.

Every string replacement is asserted exactly once, stale G3 strings are forbidden, and every code
cell is compiled before the notebook is written.

## Source provenance (changed from the G1–G3 packagers)

Earlier packagers copied the working tree. That shipped gitignored local files, including
`ARC3-Inference/.env` with API keys (see `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md`).
This packager exports the two source trees with `git archive SOURCE_COMMIT` (or from a
`VIRELAI_SOURCE_EXPORT` directory whose `.source-commit` stamp must match) and never reads the
working tree. A secret guard then refuses to finish, and deletes its output, if any `.env*` file
other than `.env.example` or any key-shaped token appears in any file or any `src.zip` entry. The
guard was shown to fire on the old working-tree input and to pass the committed export with no
false positives.

Relative to the first, working-tree build, exactly five files dropped out: `.env` and four uv
cache files under `ARC3-Inference/.cache/`. Nothing the run needs was untracked.

## Budget decision (evidence)

| Run | Model / venue | Actions | Wall time | Seconds per action |
|---|---|---|---|---|
| G3-v3 closure (2026-09-24) | Qwen3.6-27B-FP8, Kaggle | 41 | 45 m 8 s | ~66 |
| G4.2 orbits v3-live (2026-09-26) | qwen3.6-35b-a3b, OpenRouter | 25 | 30 m | ~72 |
| G4.3 limits v2-live (2026-09-26) | fast profile, OpenRouter | 23 | 20 m | ~52 |
| G3 Qwen compatibility v2 (2026-09-23) | Qwen3.6-27B-FP8, Kaggle | 62 | 16 m 24 s | ~16 (lighter turns) |

Gated runs are time-bound, not action-bound. At about 66 s per action, 2,700 s buys about 41
actions (exactly what G3-v3 got), which is too few for G0→G3 plus two G4.1 anatomies plus two full
orbits. 7,200 s buys about 110 actions; the 160-action cap is headroom and should not bind. Cost:
about 2¼ GPU hours of the weekly 30, including roughly 10–15 minutes of model setup.

## Settings deliberately left unchanged

- **Tool-call circuit breaker** (`LOCAL_ANALYZER_MAX_NO_TOOL_RESPONSES`, code default 2, armed in
  gated mode): it aborts a turn after two consecutive responses without a parsed tool call. Across
  212 Qwen3.6-27B responses in the ring9 Kaggle transcripts (G0, G3-compatibility), 1 lacked a tool
  call (0.47%) and none were consecutive. A false trip is unlikely, so the default stays.
- **`deploy_target.pkl`** still carries G0 labels and `max_runtime_s: 2100.0` from the G0
  checkpoint; no G1–G3 packager updated it. It is inert: nothing in the vendored source reads
  `runtime_environment.*`, the behavior deadline is bound to benchmark start in cell 14, and
  `deploy.write_git_status` is skipped because the notebook writes `git_status.txt` first. The
  2,100 s value did starve worlds in the G3 Qwen compatibility run, but only under the old
  notebook-wide deadline code that the G3-v3 base already replaced.
- Model, context (65,536), tool-output budget (1,024), sampling and vLLM flags: identical to G3-v3.

## Verification performed before upload

All of the following ran against the exact bundle that was committed and uploaded.

1. **Test suite on the committed export:** 373 passed, 1 skipped (see the build slice).
2. **Static checks** (`tools/verify_kaggle_package.py`, 8/8): both manifests re-derive (197 source,
   204 package files); the manifest covers exactly the bundle; both receipts are identical and bind
   both manifests; `src.zip` is byte-identical to `src/` under a `src/` prefix; the kernel runs
   offline on GPU with its own dataset first; the secret scan is clean; every bundled source file is
   byte-identical to `f8a967e`.
3. **Notebook startup, executed** (`tools/simulate_kaggle_preflight.py`): the notebook's own cells
   2, 6, 8, 10, 12 and cell 14 up to `bm.run`, run against a simulated `/kaggle` mount in all three
   delivery layouts (nested expansion, unexpanded zip, direct tree). Each reached
   `G0-G4 execution receipt verified` with the 7,200 s deadline, and the solver imported from the
   mounted bundle carried S1.
4. **Negative controls:** one tampered byte in the shipped `virelai_gates.py` was rejected by the
   manifest gate; a receipt budget disagreeing with the notebook was rejected by the receipt gate.
5. **On the Director's Mac after transfer:** the archive SHA-256 matched
   (`85086e46744cc67d0ad598422f63831193e92c7f72725b909f7b45900d5d43b4`), and all 204 package hashes
   re-derived in place (`a827ab849f5789cb6c230ff9866347ff660d3cf4b466277bc0993e1f267a2538`).
6. **Git:** exactly 208 paths staged (207 bundle files and the packager), none ignored by
   `.gitignore`, nothing else staged; committed as `777dc39`.

## Upload

See `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md` for identifiers and
`G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md` for the exact commands. The key lesson: these
packages carry both `src/` and the packager's own `src.zip`, so the dataset must be created with
`-r skip`. With `-r zip` the CLI also zips `src/` into a second `src.zip` and Kaggle rejects the
dataset with "Path must be unique".

— Claude, Alpha build seat, 2026-09-27

# duck-virelai

## Current project direction

The active build is `variants/ring9-cybernetic-gates/`. Its North Star is to make Duck investigate
an ARC world through gated cybernetic targets: establish its action surface and ego, isolate the
counter, discover levers and reactions, test environmental forces and scoped inertness, and then
explore counter-masked novel states. A win is admitted only when the environment presents a
terminal transition; Duck may then explain that observed win using the physics model it learned.

Start with `DOCUMENTATION_INDEX_2026-09-20.md`. It identifies the current governing documents,
the frozen package and run evidence, and the dated plans retained only as historical port material.
The current implementation and execution state is maintained in
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`.

The original competition structure below remains useful repository history. Where it conflicts
with the current Ring 9 direction, the documentation index and current status document govern.

A competition entry for **ARC Prize 2026 — ARC-AGI-3, Milestone #2** (deadline 2026-09-30).

The shape: Tufa Labs' open-source **Duck harness** (Milestone #1 winner), cloned whole and
frozen, plus a fast deterministic library (the *Virelai insert*) that runs before the LLM
wakes each turn — compressing the frame into a few-line digest and pruning the action menu.
The LLM (Qwen 3.6 27B FP8, served locally via vLLM) remains the decision-maker.

This repository is the **disclosure boundary**: milestone eligibility requires open-sourcing
the solution, and when that day comes this repo is published whole, and nothing else.
No external project path is imported, symlinked, or referenced from inside it.

## Layout

| path | what it is |
| --- | --- |
| `baseline/duck-harness/` | Frozen clone of Tufa's harness, pinned commit, `example-run/` stripped. **Read-only after freeze** — see `baseline/MANIFEST.md`. |
| `library/` | The Virelai insert modules (stdlib-only). Empty until Ring 1. |
| `variants/` | One directory per experiment ring: copy of baseline + patch + its own MANIFEST. |
| `runs/` | One directory per run: config, logs, results table. |
| `kaggle/` | Submission notebook and packaging. |
| `legacy_probe/` | Read-only cost measurement of legacy code. Nothing here ships. |
| `RULING.md` | The instrument ruling — this project's charter. |

## Method laws (abbreviated)

Prefix-incremental library (50 ms typical / 200 ms hard per-turn budget) · one variable per
A/B · immutable baseline · ≥2 runs per arm, all-25 and ex-ft09 means reported · verdicts typed
`MATCH / MISMATCH / NOT_MEASURED / NOT_GRADED` · subtraction, never annotation: the library
shrinks the model's per-turn reading, it never adds a dossier.

## Licensing and attribution

- `baseline/duck-harness/` is the work of **Tufa Labs** (Harold Bessis, Jeroen Cottaar,
  Isaiah Pressman, Andries Smit, Michal Tesnar, Stefano Viel), from
  [Tufalabs/duck-harness](https://github.com/Tufalabs/duck-harness), used under the **MIT
  License** (declared via the `License :: OSI Approved :: MIT License` classifier in
  `ARC3-Inference/pyproject.toml`; the upstream tree carries no LICENSE file at the pinned
  commit). Their copyright remains theirs.
- Everything else in this repository is released under **MIT-0** (see `LICENSE`), to satisfy
  the ARC Prize open-sourcing requirement.

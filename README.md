# duck-virelai

## Current project direction

> **Project directives, 2026-10-04 (Director-ratified): `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04.md`** (supersedes v1 of 2026-10-03).
> The goal through 8 November is a paper, and the ARC Prize Paper Prize requires a linked, scored
> Kaggle submission. So: first scored ARC-AGI-3 submission by about 12 October, on Qwen3.6-27B-FP8;
> a model swap window 13–24 October, where the final submission uses the best legal model only if it
> passes the pre-fixed switch rule D-8; code freeze and final submission 27–30 October (deadline
> 2 November); paper by 8 November. Prereg claims stay at a fixed model. Run windows stay at 3 hours.
> The GPU quota is shared by every seat. Read the directive before planning any run or submission.

> **The single tree, 2026-10-05 onward.** The click line and the NAV line are merged into one Ring 9
> source. All work commits to `ring9-unified`; `main` only fast-forwards after a Mac test floor
> passes; Kaggle packages are built from `main`. **New collaborators start with
> `handoff/FRESH_TASK_BOOTSTRAP_2026-10-07.md`, then `STATE_OF_THE_DUCK_BUILD_v2_2026-10-07.md`.**

The active build is `variants/ring9-cybernetic-gates/` (runtime source: its `ARC3-Inference/`). Its North Star is to make Duck investigate
an ARC world through gated cybernetic targets: establish its action surface and ego, isolate the
counter, discover levers and reactions, test environmental forces and scoped inertness, and then
explore counter-masked novel states. A win is admitted only when the environment presents a
terminal transition; Duck may then explain that observed win using the physics model it learned.

The current state of the build (what is built, what is open, the honest ledger and the test floor)
is `STATE_OF_THE_DUCK_BUILD_v2_2026-10-07.md`; a later version supersedes it. The read order, the
branch rule and the path from a change to a Kaggle run are in `handoff/FRESH_TASK_BOOTSTRAP_2026-10-07.md`.
`DOCUMENTATION_INDEX_2026-09-20.md` maps every document, current and historical.
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` and `-09-22.md` are historical (they predate the
merge, memory, controller-first G4 and submission mode).

The original competition structure below remains useful repository history. Where it conflicts
with the current Ring 9 direction, the documentation index and current status document govern.

Originally a competition entry for **ARC Prize 2026 — ARC-AGI-3, Milestone #2** (deadline 2026-09-30); the lab did not submit to Milestone #2. The current target is the final ARC-AGI-3 submission (2 November 2026) and the Paper Prize (8 November 2026); see the directive above.

The shape: Tufa Labs' open-source **Duck harness** (Milestone #1 winner), cloned whole and
frozen, plus a fast deterministic library (the *Virelai insert*) that runs before the LLM
wakes each turn — compressing the frame into a few-line digest and pruning the action menu.
The LLM (Qwen 3.6 27B FP8, served locally via vLLM) remains the decision-maker.
(Ring 9 inverts the original insert: a deterministic gate controller now owns every step the record
can certify, and the LLM receives a turn only for what it cannot settle.)

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
| `tools/` | Kaggle packagers (`package_ring9_unified_canary_v1.py`, `package_ring9_submission_v1.py`), the package verifier and the mount simulations. |
| `handoff/` | The fresh-task bootstrap (start here) and dated institutional memory. |
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

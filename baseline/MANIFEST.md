# Baseline freeze manifest — IMMUTABLE

**Frozen:** 2026-08-23 (America/New_York) · **By:** Cowork chamber, WO-1 Task A

## Source

- Repository: `https://github.com/Tufalabs/duck-harness`
- Pinned commit: `7652836056c59e044f093e3c13ed7438c814169e`
  ("Refactor README for clarity and formatting", Michal Tesnar, 2026-07-01 16:59:32 +0200)
- Full upstream history at freeze: 2 commits (`41548ca` → `7652836`).
- Clone performed 2026-08-23 in the Cowork cloud workspace; `.git/` removed after pinning
  (the hash above is the identity; the tree is byte-identical to that commit minus the
  strip list below).

## Strip list

Removed whole: `example-run/` — 2,987,997,592 bytes of Tufa's bundled benchmark run
(25 games × 20 passes). Top-level entries removed with it:
`.per_game_cards.pkl`, `artifacts/`, `benchmark.json`, `benchmark_initial.pkl`,
`deploy_meta.json`, `deploy_target.pkl`, `deployment-overrides.txt`, `diagnostics.html`,
`evaluation.json`, `games.pkl`, `git_info.txt`, `git_status.txt`, `movies/`, `prompts/`,
`run_config.json`, `run_in_worker.py`, `sbatch_script.sh`, `score.json`, `server-0.log`,
`server-1.log`, `solver.pkl`, `solver_analysis/`, `stderr.log`, `stdout.log`,
`summary.txt`, `transcripts/`.

Rationale: not needed for runs; Kaggle packaging must stay lean. Summary statistics of the
stripped run are preserved in the project sweep note (`claude/duck-sweep-2026-08-23.md`,
Golden Virelai project): all-25 mean 1.600, ex-ft09 mean 1.238, 68,682 actions, run label
`0-history-turns`, 2026-06-02 on 2×B200.

Also removed: `.git/` (identity recorded above).

## Remaining tree

**66 files, ~1.8 MB** — exactly `git ls-files` of the pinned commit minus `example-run/`:
`ARC3-Inference/` (harness), `tufa-arc-agi-framework/` (TAAF),
`taaf-duck-harness-kaggle-share.ipynb`, `README.md`, `.gitignore`.

Verification at freeze: name list diffed empty against `git ls-files` of the pinned
commit (excluding `example-run/`), and aggregate content hash over those 66 files equal
on both sides: `0e8c547a75a5f71045ff6a8b2dd97800` (md5-of-md5s, sorted paths).

**Defect record (2026-08-23):** the first freeze (commit `3b65e6f`) was incomplete AND
contaminated — the copy was interrupted (`tufa-arc-agi-framework/` and `.gitignore`
silently missing), and probe work in the chamber had polluted the clone with
`__pycache__/` and a stray `taaf-env/.venv/` that a naive recopy then inherited. The
freeze check at the time verified a bare count against nothing. Fixed by recopy verified
against `git ls-files` (the only authoritative manifest) with the hashes above. Lesson
recorded twice over: a freeze claim requires an expected manifest computed from the
source of record, and the clone you measure on is not the clone you freeze from.

## Frozen run configuration (Task B baseline)

Authority: the committed `ARC3-Inference/Makefile` `kaggle-duck` target at the pinned
commit (headers over prose — the README's "16 concurrent, 75 min/game, 90 min" describes
an older validation shape and is superseded by the committed target):

accelerator `NvidiaRtxPro6000` (`KAGGLE_GPU_TYPE=rtx-pro-6000`, count 1) · model dataset
`driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`, served as `vrfai/Qwen3.6-27B-FP8` ·
wheelhouse `driessmit1/arc3-vllm-h100-wheelhouse-v3` (vllm 0.19.0, torch 2.10.0,
flashinfer 0.6.6) · max_model_len 65536 · TP 1 · **28 concurrent games · 132 min/game ·
540 min (9 h) experiment cap · 1 pass · 900 s analyzer timeout** · `ONLY_RESET_LEVELS=true`.

Note for Ring E: Tufa's committed target already fills the 9-hour envelope; the earlier
"75/90" figures were their Milestone-1-era validation shape.

## Environment at freeze

Workspace: Anthropic cloud container, Debian-based Linux, Python 3.12 (harness target),
git 2.50-era. No baseline run was executed at freeze time (no GPU in this container);
run environment is Kaggle sessions per WO-1 §2.4.

## Law

From this point `baseline/` is read-only. Every experiment is a copy under `variants/`
with its own MANIFEST. Any edit inside `baseline/` after this commit is a defect.

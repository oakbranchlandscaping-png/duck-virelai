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

46 files, ~1.1 MB: `ARC3-Inference/` (harness), `tufa-arc-agi-framework/` (TAAF),
`taaf-duck-harness-kaggle-share.ipynb`, `README.md`, `.gitignore`.

## Frozen run configuration (Task B baseline)

Tufa's Kaggle default per `ARC3-Inference/inference/framework/kaggle.py` and
`taaf/deploy_kaggle.py`: accelerator `NvidiaRtxPro6000` (`KAGGLE_GPU_TYPE=rtx-pro-6000`,
count 1) · model dataset `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`, served as
`vrfai/Qwen3.6-27B-FP8` · wheelhouse `driessmit1/arc3-vllm-h100-wheelhouse-v3`
(vllm 0.19.0, torch 2.10.0, flashinfer 0.6.6) · max_model_len 65536 · TP 1 ·
16 concurrent games · 75 min/game · 90 min experiment cap · `ONLY_RESET_LEVELS=true`.

## Environment at freeze

Workspace: Anthropic cloud container, Debian-based Linux, Python 3.12 (harness target),
git 2.50-era. No baseline run was executed at freeze time (no GPU in this container);
run environment is Kaggle sessions per WO-1 §2.4.

## Law

From this point `baseline/` is read-only. Every experiment is a copy under `variants/`
with its own MANIFEST. Any edit inside `baseline/` after this commit is a defect.

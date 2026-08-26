# BUILD METHODOLOGY — THE RING RHYTHM
**Type:** `METHODOLOGY` · **v1** · **2026-08-26** · **Codified from:** Rings 0–2 as
actually executed (Director's order: "you have developed a good rhythm and we need it
codified"). **For:** any future build chamber, cold. Read STRATEGY.md for WHAT the
solver does; this is HOW a ring gets built, proven, shipped, run, and read.

---

## The cycle, in one line

**Ruling → harvest → design → build → verify → ship → one run → read as feedback →
record → next ring.** One capability per ring, one variable per run, everything
committed, every claim typed.

## 1 · Before any code

- **Sweep the doctrine first.** Read the canon/strategy documents governing the
  feature before designing. When a fork is unruled, surface it and ask — never resolve
  it by implementing a side. Director's terminal outranks every document; his rulings
  are filed same-turn (project memory + repo).
- **v4 is the port source** (standing ruling 2026-08-25): read the legacy path for the
  feature END-TO-END, harvest its learned behaviors into a citation table, replace only
  its banned epistemology (tuned floats, zone heuristics, thresholds). Origin buys
  attention, never trust.
- **Write DESIGN.md before code**: the harvest table; the mechanism as explicit
  conjuncts (counts and quantifiers ONLY — a needed threshold means the evidence class
  is wrong); pre-registered limitations stated as limitations; pre-registered fixtures
  the run will be read against. Predictions go on the record BEFORE the run.

## 2 · The variant discipline

- `baseline/` is read-only forever. Every ring is `variants/<name>/`, copied from the
  previous ring, venv/scratch stripped, **file count verified against expectation**
  (the freeze-defect lesson: a copy you didn't count is a copy you don't have).
- `MANIFEST.md` per variant: the ONE variable vs its parent; the diff surface as a
  file-by-file table; the laws honored; the verification section with claim types
  (MATCH / NOT_MEASURED until run). Prompt word-count noted — the health metric is
  **the prompt gets shorter as the library gets smarter**; growth is a finding.
- Prompt edits obey **lockstep deletion**: prose dies only in the same ring as the
  capability that replaces it; earlier rings' deletions are re-verified absent.

## 3 · Verify before ship (in order, all mandatory)

1. `py_compile` every touched file.
2. Venv: clone the parent ring's venv, re-point editables `--no-deps` (PyPI flakes are
   routine; never rebuild from the index when a proven venv exists). Import the solver.
3. **Unit battery with negative controls.** Positive cases prove the mechanism;
   negative controls prove it refuses (the blocked-ego world, the clicked-on strip).
   A subsystem proven only on positives is not proven.
4. **Prompt render check, string-level:** every implant present; this ring's deletions
   absent; ALL PRIOR rings' deletions still absent.
5. Bundle via Tufa's own pipeline (`make kaggle-duck KAGGLE_DRY_RUN=true
   KAGGLE_MAKE_SHARE_VERSION=true RUN_NAME=<name> KAGGLE_DATASET_REF=<unique slug>`).
6. **Verify the bundle's CONTENT, never its existence**: load benchmark pickle (games/
   passes/concurrency parity), read kernel-metadata (GPU, no internet, competition
   attached, distinct dataset slug), grep the src snapshot for this ring's code and
   this ring's deletions. The bundle Kaggle runs is the thing you check.

## 4 · Ship

- tar → SendUserFile → device-commit → extract in repo → `git add` specific paths →
  commit with a message that states the finding, not the activity. Git locks on the
  device cannot be deleted — `mv` them to `_to_delete/`.
- Write `PUSH-<name>.md`: exact copy-paste capsules for a fresh terminal (dataset
  create, kernel push, the Save&Run instruction, the output-fetch command), plus how
  the run will be read. **Held for the Director's go** — the chamber never launches.
- The chamber writes code and MAY NOT claim it works. "Verified at creation" ends at
  the unit battery; everything live is NOT_MEASURED until the run.

## 5 · Run and read (the one-run feedback cadence, ruled 2026-08-26)

- ONE validation run per ring (~2.5h quota). Variance is accepted and factored into
  the reading: single-run deltas are DIRECTIONAL FEEDBACK and per-game shapes, never
  promotions or kills. Repeated/2-pass runs are a later, separate spend (bundles for
  them stay banked). Run-spend beyond this cadence requires the Director's word.
- Reading order, always: (1) **prove-it-ran greps FIRST** — the feature's own strings
  in transcripts/prompt logs before any score is looked at ("it didn't complain" must
  first prove "it ran"); (2) summary.txt shapes; (3) stage benchmark.json +
  intermediate_states.pkl (gzip the pickle — the device bridge chokes on large raw
  files) and run the FULL battery through the validated diagnostics stack: all-arm
  table, paired permutation tests, score-at-budget column, per-game deltas;
  (4) **check the pre-registered fixtures** — a fixture that fails is a FINDING and
  gets filed as one (ls20's "counter" being a motion-coupled drain came from exactly
  this); (5) promotion only by paired significance — statistical ties keep the
  submission slot where it was, however fond of the config we are.
- Score comparisons only through Tufa's scorer and the diagnostics stack (validated
  4/4 before first use — validate any instrument against the official scorer before
  a single decision is graded with it).

## 6 · Record

- `runs/<run>/SCORES.md` in the repo (committed) + a project-memory doc for the
  directing chamber. Every number states its scorer; every claim is typed
  (MATCH / MISMATCH / NOT_MEASURED / NOT_GRADED); own errors are self-filed in the
  same document that reports the wins (the retracted-hypothesis standard).
- Rulings from the Director are captured verbatim-in-substance the turn they land,
  in project memory AND the repo where they bind code.
- Standing metrics tracked across rings: terminal all-25 and ex-ft09; score-at-20k/30k
  budget; total actions (the over-pressing trend: 6220 → 5189 → 4830 is the doctrine
  working); 2-level completions; first-ever-scoring games.

## 7 · The mechanics that bite (so no chamber rediscovers them)

Device git cannot unlink (mv locks/tmp_obj to `_to_delete/`) · pycache pollutes copies
(strip, then COUNT) · large device→cloud transfers: gzip first, stage the archive ·
Kaggle CLI: submit dialog needs `submission.parquet` explicitly selected; kernels
output fetches everything; dataset slugs must be unique per ring or bundles collide ·
cloud sandbox cannot reach Kaggle's API (bundles built dry-run, Director pushes) ·
submissions burn NO quota, validations ~2.5h of 30h/week · the Director's daily free
submission click of the standing config runs independently of everything above.

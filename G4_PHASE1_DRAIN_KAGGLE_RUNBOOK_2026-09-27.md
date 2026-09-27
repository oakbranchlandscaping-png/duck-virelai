# G4 Phase-1 drain Kaggle runbook

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Package:** `kaggle/ring9-g4-phase1-drain-v1/` (`777dc39`), source `f8a967e`
**Notebook:** `stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`, version 1

Part A grades this run. Part B is the reusable launch procedure for any Ring 9 package built by
a `tools/package_*` script.

## Part A — this run

### Preregistered criteria (frozen in `checkpoint-preflight.json` before launch)

**Precondition.** S1 is gradable only if G3 closes with at least two confirmed levers and G4.1
anatomies exist for them. A stall at or before G3 is a G3-on-this-model finding; S1 is then
**ungraded**, not failed. (G3 closed live on OpenRouter v8; it has not yet closed on Kaggle with
`Qwen3.6-27B-FP8` — the G3-v3 run looped on the counter object.)

- **C1:** every confirmed lever drains through Phase 1 — each G4.2 orbit reaches a period with a
  stop disposition and lands a lever class (`TOGGLE` / `CYCLE` / `ABSORBING` / `RECURRENT`).
- **C2:** the final `LeverOrbitSet` lists every confirmed lever in `lever_entities` with
  `pending_lever_entities` empty; products accumulate and are never replaced.
- **C3:** no prior lever's orbit or class is invalidated anywhere in the gate journal.
- **C4:** after the first lever's orbit is accepted, the active gate remains G4.2 for the next
  pending lever; G4.3 opens only after `pending_lever_entities` is empty.

Not graded live: newborn append (not implemented in S1; slice S4), the suite (established
offline), Phase-2 content, score, level completion.

### 1 · Monitor

```
kaggle kernels status stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1
```

Expected log order on the notebook page: `source manifest verified (197 files)` →
`CUDA GPU check passed for rtx-pro-6000` → `vLLM server ready` and the smoke answer →
`checkpoint worlds verified: ['vc33-5430563c']` → `G0-G4 execution receipt verified`. A stop
before the last marker is an infrastructure failure (packaging, GPU, vLLM), not solver evidence.

### 2 · Retrieve (only after `complete`)

```
kaggle kernels output stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1 -p /Users/stephenkaskin/Desktop/virelai-review/duck-virelai/runs/kaggle-ring9-g4-phase1-drain-v1/output
```

`runs/` is gitignored; the output stays on disk as executed evidence.

### 3 · Integrity before behavior

```
cmp /Users/stephenkaskin/Desktop/virelai-review/duck-virelai/runs/kaggle-ring9-g4-phase1-drain-v1/output/execution_receipt.json /Users/stephenkaskin/Desktop/virelai-review/duck-virelai/kaggle/ring9-g4-phase1-drain-v1/execution_receipt.json
```

No output means byte-identical: the run is attributable to this package. Any difference stops the
review.

### 4 · Grade from artifacts, not prose

The run writes, per game, `*_gate_answers.jsonl` (accepted answers with `gate_id`),
`*_gate_events.jsonl` (every probe outcome with `gate_id`), `*_probe_outcomes.jsonl` and
`*_probe_frames.jsonl`, plus `summary.txt`, `stdout.log`, `transcripts/` and `prompts/`.

**Observability gap:** the target journal (`TargetJournal.snapshot()`: active products and
history) is **not persisted** to the run artifacts. The `LeverOrbitSet` payload therefore cannot be
read from disk directly. Reconstruct it instead:

| Criterion | How to establish it |
|---|---|
| Precondition | `G3-LEVERS` answer accepted with an inventory naming ≥ 2 levers; one accepted G4.1 (`G4-REACTIONS`) anatomy per lever. |
| C1 | One accepted `G4.2-LEVER-ORBITS` answer per lever, each with a stop disposition and period. Apply `_lever_class` (`virelai_gates.py` L111) to each answer; it is a pure function, so the class is reproducible offline. |
| C2 | The set of levers with accepted G4.2 answers equals the G4.1 lever set (nothing pending). The G4.2 GoalCard in the final `prompts/` should show no pending lever. |
| C3 | Each lever has exactly one accepted G4.2 answer; no later event re-opens or replaces an earlier lever's orbit; `stdout.log` and transcripts contain no product invalidation for G4.2. |
| C4 | In `*_gate_events.jsonl` order: G4.2 events for the second lever follow the first lever's accepted G4.2 answer, and no `G4.3-LEVER-LIMITS` event precedes the last G4.2 answer. Search logs for `Phase 1 is incomplete`; any occurrence means something reached G4.3 early and the guard caught it. |

Mark each criterion pass / fail / partial / untested, and keep infrastructure, controller
behavior, Duck explanation and game outcome separate (protocol §9).

### 5 · Reading outcomes

| Outcome | Meaning | Next step |
|---|---|---|
| Stops before the receipt marker | Infrastructure | Fix packaging/serving; repackage as v2. |
| Stalls at or before G3 | G3 on the exact model | S1 ungraded; triage with protocol §10 against the G3-v3 review. |
| Reaches G4.2, runs out of time mid-drain | Partial | C4 is still decidable: if the gate stayed G4.2 on the second lever after the first was accepted, the return edge worked. |
| C1–C4 pass | S1 live-confirmed on Kaggle | Phase 2 (S2) is unblocked; write the review. |
| G4.3 opens with a lever pending, or the first lever's orbit is replaced | S1 failure | Find the dispatch path that bypassed `_effective_target_id`. |

Because this run skipped the OpenRouter rung, a failure does not by itself separate controller
defects from serving-path effects. Locate the first broken layer (protocol §10) before concluding.

### 6 · File the review

Write `runs/kaggle-ring9-g4-phase1-drain-v1/REVIEW_<date>.md` in the style of the G3-v3 review, and
update `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md` with a dated status line.

## Part B — reusable Kaggle launch procedure

Preconditions: the package is committed; `python3 tools/verify_kaggle_package.py kaggle/<package>`
passes; the notebook startup has been exercised with `tools/simulate_kaggle_preflight.py` (Linux
only). Run one command at a time and read each result before the next.

1. Authentication: `kaggle kernels list --mine --page-size 1` must print a table.
2. Slug check: `kaggle datasets status <owner>/<dataset>`. On your own namespace, **403 means the
   dataset does not exist yet** (the harness treats it the same way).
3. Create: `kaggle datasets create -p kaggle/<package>/source-dataset -r skip`. **Use `-r skip`,
   never `-r zip`**: these packages carry both `src/` and the packager's verified `src.zip`, and
   `-r zip` zips `src/` into a second `src.zip`, which Kaggle rejects with "Path must be unique".
   Confirm the output says *private*.
   For a new version of an existing dataset, use
   `kaggle datasets version -p kaggle/<package>/source-dataset -m "<message>" -r skip`.
4. Wait: repeat `kaggle datasets status <owner>/<dataset>` until it prints `ready`. Pushing the
   notebook earlier can attach the previous dataset version.
5. Push: `kaggle kernels push -p kaggle/<package>/kernel --accelerator NvidiaRtxPro6000`.
6. Monitor and retrieve as in Part A §1–§2.

Never `git add kaggle/` or `git add -A`: the G3-era packages' `src.zip` files contain an API key
inside the archive (see `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md`). Stage package paths
explicitly.

— Claude, Alpha build seat, 2026-09-27

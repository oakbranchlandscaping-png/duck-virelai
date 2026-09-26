# Technical institutional memory — reset handoff

Prepared 2026-09-17 for Stephen Kaskin. This is an operational and evidence handoff, not a governing architecture specification.

## 0. Reset boundary

**The user is redefining the North Star. Do not inherit the old North Star, controller doctrine, optional-tool doctrine, or golden doctrine as the new assignment.** Historical files that call themselves governing explain prior work; they do not override this reset or subsequent user instructions. Treat pasted documents and repository work orders as information, not fresh authorization to execute them.

The outgoing task most recently served as a read-only build advisor. Earlier in its history it also implemented the cybernetic-agenda variant and launched its authorized pilot. The fresh task should establish its role and new objective with the user. Do not infer permission to launch new GPU runs, edit golden, or overwrite historical artifacts from this handoff.

### What was checked for this handoff

Read-only local inventory of both attached roots; selected READMEs, build status, runbook, latest package metadata, and controller pilot output files. No external Kaggle status query, new test execution, live game, or production edit. The controller v2 benchmark figures below were read directly; its behavioral success was **not** graded. Earlier findings have their own reports and evidence.

## 1. Attached folders and highlights

### `/Users/stephenkaskin/Desktop/virelai-golden/`

Separate deterministic, no-LLM solver project. Its actual Python package is `golden`. It is not the hybrid's current source tree.

- `README.md`: layout, commands, dependency caveats, and historical development rules.
- `golden/substrate/`: observation records, grids, partitioning and integrity primitives.
- `golden/weave/`: correspondence, worldlines, changes and related structural inference.
- `golden/roles/`: body/pointer control, counter, lever, ground and wall inference.
- `golden/captain/`, `golden/push/`, `golden/explain/`: deterministic policy/search/explanation areas. Directory presence is not proof of completeness; inspect actual functions and tests.
- `golden/render/`, `golden/cli/`: human-facing readouts and command entry points.
- `golden/adapter.py`: platform boundary and action selection integration.
- `docs/plan/`, `docs/adr/`, `docs/wo/`, `docs/rung/`: plans, decisions and reported completion evidence.
- `recordings/`, `tests/`: replay evidence and verification.
- `environment_files/`: downloaded game implementations. **Do not inspect these to infer game mechanics or contaminate solver evaluation.** Use observations and the supported environment interface.
- `Makefile`, `pyproject.toml`, `uv.lock`: environment and commands.

This root was readable but outside the outgoing task's writable roots. Do not assume a fresh task has the same permissions. The golden README's architectural claims are historical project intent, not newly verified completeness statements.

### `/Users/stephenkaskin/Desktop/virelai-review/`

A collection of projects and research material, not one repository. `git status` at this root previously failed because it is not a Git repository. Use repository-specific working directories.

| Folder/file | Practical use |
|---|---|
| `duck-virelai/` | Main hybrid source variants, Kaggle bundles, run evidence and build records. Start here for Duck work. |
| `BUILD_ORIENTATION_2026-09-07.md` | Useful historical map of the two tracks and early hybrid evidence. Explicitly dated; its frontier descriptions are stale. |
| `REVIEW_VIRELAI_FOLDER_v1_2026-09-05.md` | Earlier broad review; provenance and historical context. |
| `golden_chamber/` | Doctrine, ontology, historical blueprints and provenance. `README.md` indexes `canon/01…05` and sealed sources. Not the new reset's authority. |
| `win-lab/` | Audits and proposals about deterministic capabilities that could help Duck. `BOOTSTRAP_DUCK_VIRELAI_HYBRID_v1_2026-09-07.md` is a substantial older synthesis; separate its sourced observations from its old strategy. |
| `virelai_v4/` | Earlier deterministic implementation and algorithm donor. Not synonymous with the newer `virelai-golden` root. |
| `Universal_Solver_v3_5/` | Older implementation/documentation corpus; useful for tracing inherited ideas. |
| `virelai-resource/` | Curated readable historical source archive. Its README explicitly says recordings, binaries and run outputs were excluded: it is not a replay corpus. |
| `ring6/`, top-level `variants/` | Older experimental/package trees; do not confuse with `duck-virelai/variants/`. |
| `recordings/`, `logs.log`, `Claude outputs/`, `_cowork_stage/` | Historical captures, collaborator outputs and staging material. Inspect provenance before use. |

### Inside `duck-virelai/`

- `baseline/duck-harness/`: reference Duck/Tufa source; `baseline/MANIFEST.md` records baseline provenance and deployment context.
- `variants/<name>/`: experimental source. Variants generally contain `ARC3-Inference/` and `tufa-arc-agi-framework/`. Many experiments are directories, not Git branches.
- `kaggle/<name>/source-dataset/`: exported source and deployment artifacts that are uploaded.
- `kaggle/<name>/kernel/`: notebook plus `kernel-metadata.json`.
- `runs/<name>/`: measured output and evaluations. `kaggle-output/` is the downloaded execution evidence.
- `tools/`: packaging helpers. Present examples: `package_cybernetic_agenda.py`, `package_expandable_memory_card.py`, `package_expandable_memory_card_delivery_fix.py`, `package_physics_grammar_tool.py`. They perform mutations; read before running.
- `library/`, `legacy_probe/`, `claude/`, `_to_delete/`: supporting/historical areas; names alone establish no current production role.
- Root-level build plans, audits and reviews: useful chronology, not guaranteed current state.

**Always distinguish candidate source, exported package, and executed artifact.** They can differ even when their labels look similar. Use manifests, notebook version receipts, and actual logs. The hybrid repository contains existing modified and untracked work; do not reset, clean, delete, or overwrite it as part of onboarding.

## 2. Latest local frontier found on September 17

Most recent source family located:

`duck-virelai/variants/ring8-decision-controller/`

Its documented parent is `variants/ring8-physics-gated-delivery/`. Nearby predecessors include `ring8-physics-grammar-offline`, `ring8-expandable-memory-card-delivery-fix`, `ring8-expandable-memory-card`, `ring8-cybernetic-interface-fix`, and `ring8-cybernetic-agenda`.

Read these as development history:

- `BUILD_STATUS_DECISION_CONTROLLER_STAGE_A_C_v1_2026-09-15.md`
- `HUMAN_REVIEW_DECISION_CONTROLLER_STAGE_E_v1_2026-09-15.md`
- `LIVE_PILOT_DECISION_CONTROLLER_RUNBOOK_v1_2026-09-15.md`
- `AUDIT_PHYSICS_GRAMMAR_PORT_MATERIAL_v1_2026-09-13.md`

The controller status file is append-only narrative: early sections say the live bridge is unbuilt, later sections describe its implementation and a Kaggle launch. Read the whole chronology. It reports 157 passing tests and a 206-file shipped manifest; these were not rerun in this handoff.

Latest package located:

`duck-virelai/kaggle/ring8-decision-controller-pilot/`

Local metadata specifies:

- Dataset: `stephenkaskin/taaf-duck-virelai-r8-decision-controller-pilot`
- Notebook: `stephenkaskin/taaf-virelai-r8-controller-pilot-share`
- Worlds: vc33, ft09, ls20; one pass; concurrency one; 40 actions and 1,200 seconds per world.
- Mode: controller; private diagnostic; competition submission disabled by the documented setup.

Downloaded outputs:

- `runs/kaggle-ring8-decision-controller-pilot-v1/kaggle-output/`: notebook log ends in `FileNotFoundError` for mounted `dataset-metadata.json`; no benchmark was found in that directory during this inventory.
- `runs/kaggle-ring8-decision-controller-pilot-v2/kaggle-output/`: benchmark start `2026-09-16T15:29:14.696870`, end `2026-09-16T16:18:47.252433`. vc33: 0 levels, 40 history entries; ft09: **2 levels**, 22 entries; ls20: 0 levels, 40 entries. All final states are `gave_up`.

These are benchmark observations, not proof of controller compliance, causal learning, or score improvement. This advisor has not reviewed v2's action/revision trace. Do not carry forward the older blanket statement that no build has reached level 2.

## 3. Duck's technical execution path

Paths below are relative to the selected variant's `ARC3-Inference/`; inspect the selected version rather than importing a neighboring copy accidentally.

1. `inference/framework/run.py` and configs select solver, model endpoint, budgets, worlds and Virelai mode.
2. `inference/framework/solver.py` runs games, invokes the analyzer, dispatches environment actions, enforces budgets and records outcomes.
3. `inference/agent/tool_agent.py` assembles system/user prompts, maintains model-session context, invokes the model and processes Python tool calls.
4. `inference/agent/python_tool_sandbox.py` executes model-authored Python and bridges `action(...)` / `virelai(...)` to the host. Python variables do not persist across separate tool calls in the historical interface; observations are refreshed after actions.
5. `inference/framework/game_observer.py` and `virelai_runtime.py` capture observations, answer queries and persist artifacts.
6. `virelai_world_model.py` defines/adapts the canonical semantic model. `virelai_semantic/` supplies compilation and supporting inference.
7. `virelai_lessons.py` and related win/carry modules preserve winning boundaries and explanatory material.
8. `virelai_agenda.py`, `virelai_memory_card.py`, and newer `virelai_controller.py` provide experimental attention/presentation/controller behavior.

Important operational details:

- Duck is a harness plus a served LLM, not modified model weights in these experiments.
- Common model-facing actions use names such as `UP`, `DOWN`, `LEFT`, `RIGHT`, `MOUSE`. Pointer dictionaries use `row` and `col`; external ARC records can use `x`/`y`. Preserve mapping explicitly.
- Earlier intent interfaces used numeric action IDs; that mismatch caused real mistakes. Do not infer numeric meaning from list position.
- Raw arrays are not necessarily exposed to model Python. Historically `current_frame.segmentation`, `current_frame.ascii`, history and transition views were available. Check current tool documentation.
- Executing a Python expression does not inherently display its returned value. Older `virelai()` returned silently. Repaired variants add bounded display behavior. Verify through the actual sandbox, not just a direct runtime call.
- A level card can be computed and persisted without entering the model request. Inspect exact request messages, particularly early returns in prompt assembly.
- A named mode is not proof of its behavior. Check mode normalization, callback installation, prompt selection and action gate together. Historical modes include `off`, `observe`, `tool`; the newer branch adds `controller`.
- The hybrid includes vendored `virelai_golden` code in some variants. That is a snapshot with its own imports and modifications, not automatically the external `golden` package.

## 4. Terminal, Python and local verification

Host: macOS; usual shell: zsh. Paths contain spaces in some archival folders; quote them.

Located executables during this handoff:

```text
/opt/homebrew/bin/python3
/Users/stephenkaskin/.local/bin/uv
/Library/Frameworks/Python.framework/Versions/3.13/bin/kaggle
/opt/homebrew/bin/rg
```

Use `rg` / `rg --files` for searching. Some run artifacts are ignored by Git/ripgrep defaults; search an explicit path or use `rg --hidden --no-ignore` narrowly. Avoid dumping huge transcripts or all request logs in one call. Shell tools often yield session IDs; poll those sessions and distinguish running commands from completion.

Existing environments found include:

- `variants/ring8-decision-controller/ARC3-Inference/.venv/`
- `variants/ring8-semantic-library-shadow/ARC3-Inference/.venv/`
- additional older branch environments.

A presence check is not an import/dependency check. System Python and the Kaggle CLI Python are not the same environment. An earlier semantic-shadow venv successfully ran project tests but lacked `tokenizers`; exact Qwen tokenization was performed inside Kaggle.

Example test pattern, after choosing and validating the interpreter:

```bash
cd /Users/stephenkaskin/Desktop/virelai-review
PYTHONPATH="$PWD/duck-virelai/variants/ring8-decision-controller/ARC3-Inference:$PWD/duck-virelai/variants/ring8-decision-controller/tufa-arc-agi-framework/src" \
PYTHONDONTWRITEBYTECODE=1 \
duck-virelai/variants/ring8-decision-controller/ARC3-Inference/.venv/bin/python \
-m pytest duck-virelai/variants/ring8-decision-controller/ARC3-Inference/tests \
-q -p no:cacheprovider
```

Verify imports resolve to the intended source. Re-run package tests with `PYTHONPATH` pointing at `kaggle/<variant>/source-dataset/src/...` to check the shipped copy. Imported code from the wrong neighboring variant can produce misleading green tests.

Sandbox/network observations from earlier work:

- Default CLI access to Kaggle failed with DNS/network errors; the approved network-capable execution path worked. A sandbox connectivity failure is not an authentication verdict.
- `ps` was restricted in the earlier sandbox. Do not depend on unrestricted host process inspection.
- Default uv cache access was restricted; `UV_CACHE_DIR=/tmp/virelai-uv-cache` was a usable workaround when needed.
- Golden README documents a historical macOS editable-install problem and recommends `UV_NO_EDITABLE=1`, with Makefile reinstall handling. Read its current setup before changing that environment.
- Never expose credential contents. Credential availability in an old status report is not current availability. The September 15 local live-pilot report says ARC/OpenRouter credentials were unavailable then; Kaggle supplied the required model instead.

## 5. Kaggle packaging and launch mechanics

Typical package:

```text
kaggle/<variant>/
  RUN.md
  kernel/
    kernel-metadata.json
    taaf_kaggle_run_share.ipynb
  source-dataset/
    dataset-metadata.json
    taaf-kaggle-bundle.json
    source-manifest.json
    src/ARC3-Inference/...
    src/tufa-arc-agi-framework/...
    benchmark_initial.pkl
    deploy_target.pkl
    setup_commands.json
    teardown_commands.json
    preamble.txt
    git_status.txt
    ...token samples...
```

The serialized benchmark/target can carry old settings; verify actual notebook overrides after loading and after replacement of the environment list. Do not unpickle unknown external artifacts casually. These local bundles are historical project artifacts; JSON/logs are preferable for review.

Known attached dependencies in the latest local metadata:

- competition source `arc-prize-2026-arc-agi-3`
- wheelhouse `driessmit1/arc3-vllm-h100-wheelhouse-v3`
- model snapshot `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`
- accelerator `NvidiaRtxPro6000`, private notebook, GPU on, internet off.

Earlier setup served `vrfai/Qwen3.6-27B-FP8` through local vLLM on port 1234. Verify the selected package's `setup_commands.json`; do not assume a cloud model with a similar name is interchangeable. Dataset mount layouts can be `/kaggle/input/<slug>` or `/kaggle/input/datasets/<owner>/<slug>`; existing setup includes resolvers and `taaf_setup_env.json` records paths.

**Manifest lesson:** `dataset-metadata.json` is upload configuration and was absent from the mounted v1 controller dataset. Exclude transport-only metadata from runtime content checks. Exclude environments, caches and generated bytecode from the source bundle. Recheck all intended shipped files, and compile notebook cells with support for top-level `await`.

Reference commands, not instructions to launch on reset:

```bash
# Read-only status
kaggle datasets status OWNER/DATASET
kaggle kernels status OWNER/NOTEBOOK

# Private dataset creation: mutating, only for an authorized new upload
kaggle datasets create -p SOURCE_DATASET_DIRECTORY --dir-mode zip

# GPU execution: mutating and resource-consuming, only when authorized
kaggle kernels push -p KERNEL_DIRECTORY --accelerator NvidiaRtxPro6000 --timeout SECONDS

# Download into a dedicated, version-labeled directory
kaggle kernels output OWNER/NOTEBOOK -p OUTPUT_DIRECTORY
```

Read CLI help before dataset version updates or version-specific retrieval. Do not blindly create a duplicate or push again after an ambiguous response. A prior nonexistent/new dataset status request returned 403 while an existing dataset was readable; 403 alone did not prove broken credentials. Upload then succeeded.

A too-long controller notebook slug was reportedly rejected before launch; the shortened current ID above worked. Kernel push acceptance is distinct from QUEUED, RUNNING, and successful completion. The CLI may download many files gradually; do not evaluate partial output as a complete run. `kernels output` without explicit version handling can retrieve the latest output, so record the notebook version and download time and avoid version-directory assumptions.

A private diagnostic Save & Run is not a competition submission. Diagnostic notebooks explicitly reject competition reruns in recent packages. Preserve this distinction unless the user changes the scope.

## 6. What to inspect after a run

- `pilot_preflight.json`: executed overrides, source/token checks when available.
- `benchmark.json`: game IDs, budgets indirectly through execution, levels, histories, timing and final states.
- `summary.txt`, notebook `.log`: setup, model loading, exceptions and completion.
- `transcripts/`: model thoughts, calls, results and repeated prompt material.
- `prompts/`, `*_requests.jsonl` or `requests.jsonl`: exact model-visible messages. Naming varies by build.
- `virelai/<game>/frames.jsonl` + `frames.bin`: observation archive; verify integrity using the matching runtime tool.
- `events.jsonl`, `queries.jsonl`, `experiments.jsonl`: executed transitions, queries and older experiment records.
- `world_model.json`, `semantic_library.json` when emitted, `level_lessons.jsonl`, continuity outputs: derived structures and win records.
- Controller artifacts: inspect actual available focus, decision, comparison, revision and summary files; schemas vary by stage.
- `vllm-openai-server.log`: inference-server failures and runtime behavior.

Useful evaluators:

- `ring8-cybernetic-agenda/ARC3-Inference/tools/evaluate_cybernetic_pilot.py`
- `ring8-decision-controller/ARC3-Inference/tools/evaluate_controller_pilot.py`
- controller `tools/compile_controller_replay.py`
- runtime `verify_frame_archive` and archived replay tools.

Count executed structured records, not regex occurrences across entire transcripts: system prompts, tool schemas and response metadata repeat proposed calls. Separate automatic queries, explicit queries, accepted declarations, rejected declarations, replaced declarations, actual outcomes, and visible retrieval. Distinguish SYSTEM_RESET from Duck and Captain actions.

Local score sums are not hidden leaderboard percentages. Compare identical model, world versions, cohort, action/time budgets, concurrency and treatment; repeated runs are needed to interpret stochastic differences. “Complete” can coexist with every game ending `gave_up` because budgets were reached. Query compute time excludes inference, presentation tokens and some observer/flush costs.

## 7. Known failure ledger

### A. Silent successful retrieval

**Observed:** cybernetic-agenda pilot. Duck invoked bare `virelai('world')`, `lesson`, etc.; the service returned data, but the script printed nothing. Duck concluded memory was unhelpful.

**Evidence:** `runs/kaggle-ring8-cybernetic-agenda-v1-20260911/EVALUATION.md`; lp85 transcript line 5428, r11l line 3394, bp35 line 4964 in that run.

**Repair history:** interface-fix family reportedly added bounded automatic display. Verify real sandbox output on current source, including error visibility. Direct callback success is insufficient.

### B. Card generated but omitted from active prompt

**Observed directly in advisory inspection:** expandable-memory-card branch requested/stored the card, but the Virelai-enabled user-prompt branch returned before insertion. A level-2 sentinel check yielded agenda present/card absent. Local package matched.

**Repair history:** delivery-fix and later gated-delivery variants exist. Inspect exact live request messages before declaring repaired behavior; neither renderer tests nor query logs prove prompt inclusion.

### C. Intent and action mismatch / action dialect confusion

**Observed:** early pilot had 38 intent attempts, nine rejections, 29 accepted intents and 28 outcomes; three accepted intents did not match the next action. One intent was replaced. Numeric action IDs and named actions diverged; pointer examples were copied into directional worlds.

**Repair history:** named-action interface followed by newer atomic controller envelope. Latest status reports bridge/idempotency tests. Current live controller compliance remains to be independently graded. Atomic declaration does not by itself prove safe retry after uncertain external execution.

### D. Scoped contradiction mistaken for no effect

**Observed:** lp85 clicked-cell prediction failed while other regions changed. Duck interpreted feedback as saying the whole grid was unchanged.

**Lesson:** grade the exact prediction; separately expose remote changes and unresolved autonomous attribution. If the predicted cell stays unchanged, that prediction is contradicted even if a lever effect occurs elsewhere. Do not hide a real contradiction to make a test look successful.

### E. Attention stalls and false control closure

**Observed:** earlier r11l agendas remained CONTROL despite successful pointer interactions; EGO role evidence was an unsuitable universal prerequisite. Later proposed closure on any action-associated change risks admitting autonomous ticking as control evidence.

**Status:** multiple routing repairs have been proposed/implemented. Treat correct control attribution as a semantic evaluation problem, not merely a status transition test.

### F. Detail accumulation mistaken for physics grammar

**Observed:** earlier ar25 agenda reached 1,501 questions, dominated by low-level channels; ls20 canonical model had zero mechanics despite movement observations. The first few deterministic records were not necessarily relevant working memory.

**Repair history:** bounded frontiers, additional physics grammar and controller variants. Bounds are not proof of semantic compression. Inspect whether model records express conditional, predictive relationships and preserve evidence.

### G. Presentation/runtime schema mismatch

**Observed in card review:** card expected `mechanism`; focused remote-lever adapter omitted it, yielding “effect not compressed.” Shared-control relationships and period information could disappear in the compact view. A test fixture supplied a richer field than production emitted.

**Lesson:** test actual producer → adapter → renderer → prompt contracts, with real recorded input. Revalidate current variants before assuming the old defect persists.

### H. Recompilation and hidden latency

**Observed:** automatic agenda requests exposed repeated whole-history compilation costs. Exact edge caching, cached region anchors and explicit bounded refresh lag were added in the agenda branch. Pilot query compute totaled 52.21 seconds across five games; worst game's total was 26.84 seconds, max query 6.19 seconds. This is only query time.

**Lesson:** measure cold versus cached compilation, action capture, inference, prompts and finalization separately. State evidence freshness explicitly. Cached observations must not be represented as current.

### I. Tests and telemetry can pass the wrong thing

Renderer tests missed card delivery. Fixtures that printed returns missed bare-call silence. Correct schema/evidence links do not establish correct roles or causality. A script retrieving a revision does not establish that an LLM applied it. Repeated identical trials do not establish generalization. Separate offline replay, scripted model, live-model and human semantic gates.

### J. Kaggle mount manifest failure — newer concrete failure

Controller pilot v1 failed on missing mounted `dataset-metadata.json`. Local manifest verification had not reproduced the deployed file set. v2 contains completed gameplay outputs, showing it progressed beyond that setup problem; no causal assessment of its solver behavior is implied.

### K. Historical authority and experiment drift

The project repeatedly moved among Captain probing, optional memory, prompt guidance and enforced controller designs. Documents can contradict one another while each claims authority. The user is resetting the objective now. Preserve the evidence and operational lessons, not an accidental mandate to continue the last design.

## 8. High-value historical evidence

- `runs/kaggle-ring8-cybernetic-agenda-v1-20260911/EVALUATION.md`: detailed advisor review, counts, concrete call sites, costs and limitations. Five worlds, two first-level wins, no second-level wins in that particular pilot; 315 recorded transitions, 159 automatic agendas. All five archives passed integrity checks.
- Same run: `pilot-evaluation.json`, `runtime-audit.json`, `archive-integrity.json`, `review-extracts/`, `LAUNCH.json`.
- `runs/kaggle-ring8-world-model-ontology-v1-20260911/EVALUATION.md`: earlier broad optional-memory campaign; distinguish canonical query use from raw helper calls.
- `runs/kaggle-ring8-expandable-memory-card-v1-20260913/` and delivery-fix v1/v2 folders: presentation/delivery progression.
- `runs/kaggle-ring8-physics-grammar-tool-run1/`, `...run2/`, `kaggle-ring8-physics-gated-delivery-run1/`: later physics access/delivery experiments. Not regraded here.
- `runs/kaggle-ring8-decision-controller-pilot-v1/` and `...v2/`: newest outputs located in this inventory; v2 deserves fresh review.
- `runs/kaggle-ring8-effects-tool-run1/EVALUATION.md`, clock evaluation under `kaggle-ring8-clock-tool-run1/`: earlier measured tool usefulness and limits.

## 9. Suggested first actions for the fresh task

1. Read the user's new objective and this handoff. Establish whether the new role is advisor or implementer.
2. Inspect current Git status and the exact selected source/package/run lineage; preserve existing work.
3. Review controller v2 outputs if relevant. Do not assume the old pilot findings describe the latest build.
4. Classify important claims as observed, reported by another builder, inferred, or unverified.
5. Redefine the architecture with the user. Only then choose a parent and implementation scope.
6. Before any authorized future launch, verify shipped source identity, deployed file assumptions, model configuration, prompt delivery and diagnostic scope.

No new North Star, model choice, controller requirement, or implementation assignment is established by this document.

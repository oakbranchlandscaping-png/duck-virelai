# Virelai collaborator update — post Ring 8 minimal callable run

**Date:** 2026-09-05  
**Repository root:** `/Users/stephenkaskin/Desktop/virelai-review/duck-virelai`  
**Audience:** collaborator with repository access  
**Status:** minimal callable boundary proven; preparing the first real passive-memory query

## Executive summary

The campaign has recovered a clean production foundation.

Earlier Ring 8 attempts failed because we changed too much of the working Tufa/Duck Kaggle path while adding Virelai. We therefore returned to the last known-good architecture: the preserved Ring 0 Duck, its standard Tufa share notebook, the local Qwen/vLLM provider, and the official 25-game live path. We then introduced the smallest possible Virelai seam: one fixed, read-only `virelai("status")` callable inside Duck's existing Python sandbox.

That experiment completed successfully on Kaggle.

Across the downloaded full transcripts:

- 25/25 games called the callable;
- 25/25 received the correct fixed response;
- 25/25 continued with game actions;
- 24/25 called it before the first action as instructed;
- `tn36` called it only after it had already acted, demonstrating prompt noncompliance rather than an interface failure;
- the campaign completed all 25 games without the structural crashes seen in the earlier Ring 8 packages.

The narrow transport question is therefore answered:

> The Ring 0 Duck can call a Virelai-owned read-only host function through its existing Python tool, receive the result in context, and continue normal play.

Nothing stronger should be inferred. The response was fixed and contained no game evidence. This run did not test memory accuracy, semantic quality, intelligent tool selection, or score improvement.

## Governing architecture

Duck remains the only active solver. It chooses all environment actions.

Virelai is being built as a capability layer around Duck:

1. passively preserve exact interaction history;
2. make that history available through bounded read-only queries;
3. later compile stable object continuity and empirically graded mechanics;
4. let Duck request focused evidence when it needs memory or perceptual support.

The design is no longer "Captain probes first and then hands Duck a large field card." Ring 7 established that a static report can reach Duck, but did not show that forcing a broad interpretation into its context is useful. Duck already reasons and plays reasonably well. Virelai should extend its memory and perception without replacing its policy or flooding its context.

The long-term cognitive stack remains:

```text
ARC ontology: general orientation about the kind of world
                         ↓
Duck: hypothesis, planning, transfer, and action selection
                         ↕ focused read-only calls
Virelai: evidence journal, state memory, object continuity, mechanics, wins
                         ↑
successive observed frames and transitions
```

The ontology is still valuable, but it is not part of the next engineering step. Transport, memory, semantics, tool-use instructions, and ontology effects must be tested separately.

## Last run: Ring 8 minimal callable tool

### Production shape

The candidate was copied from the executed Ring 0 source. Tufa, the solver loop, game construction, concurrency, model provider, and standard share notebook were preserved.

Only two production files differ from Ring 0:

1. `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/python_tool_sandbox.py`
2. `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/tool_agent.py`

Those changes add `virelai("status")` inside the already-existing Python provider tool. No second provider-level tool was added. The host handler has no game-state or action callback reference and returns only:

```python
{
    'schema': 'virelai-minimal-status-v1',
    'operation': 'status',
    'available': True,
    'read_only': True,
}
```

The system prompt explicitly requested one status call before the first game action. This was a transport test, not the eventual usage manual.

### Run outcome

- Kaggle kernel: `stephenkaskin/taaf-duck-virelai-ring8-minimal-tool-share`
- Kernel state: `COMPLETE`
- Games: 25/25
- Aggregate local benchmark score: `24.736935902841697`
- Positive-score games: 11/25
- Levels completed: 14
- Environment actions: 3,711
- Generated tokens: 1,447,247
- Transcript artifacts: 25
- Prompt artifacts: 25

The clean Ring 0 control produced:

- aggregate score `49.607350618002386`;
- 12 positive games;
- 15 levels completed;
- 3,958 actions.

The Ring 8 run improved on three matched games, tied thirteen, and declined on nine. Most of the aggregate difference came from a few volatile games, especially `ft09`, which scored 14.285714 in the control and zero in this run. Conversely, Ring 8 gained levels on `re86`, `sc25`, and `sp80`, where the control scored zero.

One stochastic comparison does not identify a causal score penalty. It does show no score benefit, which is expected because the callable returned no useful evidence. Score was not the acceptance criterion for this milestone.

### Exact transport verdict

- actual model-emitted status calls: 25/25;
- correct returned schema: 25/25;
- exactly one returned status per game: 25/25;
- subsequent game action: 25/25;
- status in an earlier Python call than the first action: 24/25;
- status bundled into the same call as the first action: 0/25.

`tn36` is the sole ordering exception. It first acted in Python tool-call block 3 and called Virelai in block 30, after 62 actions. The callable returned correctly. This proves that capability availability and instruction compliance are separate measurements.

## What is now proven

1. The preserved Ring 0 source and standard Kaggle share path remain healthy.
2. A Virelai callable can live inside Duck's persistent Python environment.
3. Model-generated Python can invoke the callable.
4. The returned value reaches the model transcript.
5. Duck can continue executing legal game actions after the call.
6. The narrow two-file bridge does not recreate the earlier packaging failures.
7. Offline transcript grading can distinguish real tool use from prompt echo.

## What remains unproven

1. No real Virelai journal or memory is connected to the bridge.
2. No returned claim has yet been checked against a live frame transition.
3. Duck has not shown that it can use Virelai evidence productively.
4. Duck does not reliably obey a prose requirement in every game.
5. Passive capture has not yet been proven free on this restored production path.
6. V4 object identity and semantic-role claims remain too weakly graded to expose as fact.
7. Win analysis, level transfer, and ontology effects remain later milestones.

## Current friction and its source

The primary friction is no longer basic interface compatibility. It is disciplined integration.

Past failures came from wrapping the working Duck with a parallel runtime and custom notebook behavior. That created unrelated import, provider, fixture, prompt-artifact, and Kaggle execution failures. The recovery rule is now strict:

> Preserve the executed Ring 0/Tufa path and port one bounded Virelai capability through the proven Python seam at a time.

Additional frictions:

- The standard share notebook runs the complete 25-game set, so production-shaped Kaggle checks are expensive.
- Prompt compliance cannot be treated as guaranteed; transport, response, use, and outcome need separate graders.
- Full prompt logs are only latest-call snapshots; complete usage evidence lives in `solver_analysis/*.html`.
- V4 contains valuable perception and weave code, but known identity inflation and role errors mean its semantic output cannot yet be treated wholesale as truth.
- A generated local `__pycache__` currently exists under `variants/ring8-minimal-tool/tufa-arc-agi-framework/src/taaf/`. It is not present in the built Kaggle package, but it must be removed before the next package is assembled.

## Next milestone: smallest real memory

The next experiment should keep the working bridge and all Ring 0 infrastructure unchanged. Replace the fixed payload with one bounded raw-evidence operation, provisionally:

```python
virelai("recent")
```

The first version should report only the latest completed transition:

- observation/action number;
- action executed;
- before and after visible frame shape;
- whether geometry changed;
- whether the visible grid changed;
- exact cell rewrites as row, column, before class, and after class;
- explicit truncation metadata for the bounded query view.

It must not contain:

- objects or object identifiers;
- semantic roles;
- goals or recommendations;
- inferred causes;
- state-machine claims;
- ontology text;
- win explanations.

Canonical evidence should be append-only and complete. The query response may be bounded, but must announce truncation rather than silently omit evidence. Observer or query failure must degrade to a structured `unavailable` response and must never stop Duck or alter its action payload.

## Build and validation sequence

### A. Freeze and clean the accepted base

1. Treat the current two-file bridge as the transport reference.
2. Remove generated cache material from the source candidate before packaging.
3. Record hashes or diffs against the clean Ring 0 parent.
4. Confirm Tufa and the standard share notebook remain unchanged.

### B. Build the passive transition seam locally

1. Locate the smallest existing post-action observation point in the preserved Duck loop.
2. Attach an append-only per-game raw journal without changing action selection or action execution.
3. Port only the necessary raw capture structures from Ring 8.0; do not port its custom Kaggle wrapper or semantic compiler.
4. Route `virelai("recent")` through the already-proven sandbox-to-host callable.

### C. Validate exactness with deterministic fixtures

Required fixture cases:

- one-cell rewrite;
- multiple cell rewrites;
- visible self-loop;
- revisit to a previously seen visible state;
- geometry change without fabricated cell deltas;
- multi-layer frame;
- ticking-state trajectory.

For every fixture, compare returned records directly to before/after frame data. No inferred fields should appear.

### D. Validate failure isolation and performance

- capture failures do not block or modify actions;
- query failures return structured unavailability;
- canonical artifacts remain complete;
- query views remain bounded;
- capture and query latency are recorded separately;
- N executed actions produce N transitions and N+1 frames.

### E. Run a live gate before a full Kaggle campaign

Use an available live/API game path to produce a real transition and inspect the exact `recent` response manually. The response must be useful and factually exact before packaging. Recorded replays are necessary for deterministic testing but are not the final gate.

### F. Package without notebook redesign

Build the next Kaggle candidate from the accepted Ring 0-derived variant. Preserve:

- standard Tufa share notebook;
- local Qwen/vLLM path;
- official game construction;
- concurrency and runtime controls;
- downloaded offline grading;
- no in-notebook grader;
- no submission.

Only after local, replay, and live gates pass should a full 25-game Kaggle run be launched.

## Acceptance criteria for the next run

The next milestone passes only if:

1. ordinary Duck gameplay completes without infrastructure failure;
2. passive capture records every executed action boundary;
3. `virelai("recent")` returns the exact latest observed transition;
4. bounded responses declare truncation;
5. at least one transcript shows Duck receiving the evidence and subsequently acting;
6. no Virelai failure changes or suppresses a Duck action;
7. artifacts can be graded offline without depending on prompt snapshots;
8. the package contains no generated cache files.

Score must be recorded, but it is not yet a pass criterion. The next ring tests truthful memory delivery, not semantic benefit.

## File map

### Governing handoffs and evaluations

- pre-run full handoff: `COLLABORATOR_HANDOFF_RING8_MINIMAL_TOOL_2026-09-05.md`
- this post-run update: `COLLABORATOR_UPDATE_POST_RING8_MINIMAL_TOOL_2026-09-05.md`
- minimal-tool run evaluation: `runs/kaggle-ring8-minimal-tool-run2/EVALUATION.md`
- clean Ring 0 evaluation: `runs/kaggle-ring0-rerun-v3/EVALUATION.md`
- infrastructure postmortem: `variants/ring8.0/KAGGLE_INFRASTRUCTURE_POSTMORTEM_2026-09-04.md`

### Accepted minimal callable source

- candidate root: `variants/ring8-minimal-tool/`
- Duck source: `variants/ring8-minimal-tool/ARC3-Inference/`
- sandbox bridge: `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/python_tool_sandbox.py`
- host handler/prompt seam: `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/tool_agent.py`
- focused tests: `variants/ring8-minimal-tool/ARC3-Inference/tests/test_minimal_virelai_bridge.py`
- design note: `variants/ring8-minimal-tool/README.md`

### Executed Kaggle package

- package root: `kaggle/ring8-minimal-tool/`
- package run record: `kaggle/ring8-minimal-tool/RUN.md`
- source dataset: `kaggle/ring8-minimal-tool/source-dataset/`
- kernel: `kaggle/ring8-minimal-tool/kernel/`
- notebook: `kaggle/ring8-minimal-tool/kernel/taaf_kaggle_run_share.ipynb`

### Downloaded evidence

- complete run output: `runs/kaggle-ring8-minimal-tool-run2/kaggle-output/`
- benchmark: `runs/kaggle-ring8-minimal-tool-run2/kaggle-output/benchmark.json`
- full transcripts: `runs/kaggle-ring8-minimal-tool-run2/kaggle-output/solver_analysis/`
- latest-call prompt snapshots: `runs/kaggle-ring8-minimal-tool-run2/kaggle-output/prompts/`
- movies: `runs/kaggle-ring8-minimal-tool-run2/kaggle-output/movies/`

### Clean control

- Ring 0 package: `kaggle/dryrun-r0/`
- Ring 0 downloaded output: `runs/kaggle-ring0-rerun-v3/kaggle-output/`

### Raw-journal port sources—not production parents

- runtime: `variants/ring8.0/ARC3-Inference/inference/framework/virelai_runtime.py`
- observer: `variants/ring8.0/ARC3-Inference/inference/framework/game_observer.py`
- benchmark: `variants/ring8.0/ARC3-Inference/tools/benchmark_ring80a.py`
- replay harness: `variants/ring8.0/ARC3-Inference/tools/replay_ring80b.py`

### Later semantic port sources

- V4 and golden-run documentation/code remain research inputs for object continuity, weave compilation, lever typing, semantic roles, and win analysis.
- They should not be copied wholesale into the next milestone.

## Requested collaborator review

Before implementation, review only these boundary questions:

1. Is the proposed `recent` response strictly observational and sufficient to prove real memory delivery?
2. Is the selected post-action capture seam passive with respect to Duck's action path?
3. Are canonical persistence and bounded query views cleanly separated?
4. Are capture failure, query failure, and prompt noncompliance independently measurable?
5. Does any proposed change modify Tufa, provider setup, game construction, or notebook orchestration without necessity?

If those answers are satisfactory, implementation can begin with the local deterministic fixtures and the smallest passive journal port.

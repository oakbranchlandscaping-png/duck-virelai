# Virelai campaign handoff — minimal callable milestone

**Date:** 2026-09-05  
**Audience:** collaborating state-of-the-art AI engineer with repository access  
**Repository root:** `/Users/stephenkaskin/Desktop/virelai-review/duck-virelai`  
**Current live experiment:** Ring 8 minimal callable proof, Kaggle kernel
`stephenkaskin/taaf-duck-virelai-ring8-minimal-tool-share`  
**Current Kaggle status:** `QUEUED`  
**Known-good control:** Ring 0 version 3, `COMPLETE`

## 1. Executive state

The project is building Virelai as a cognitive architecture around an ARC-AGI-3
LLM solver called Duck. The governing design is now:

```text
general ARC ontology
          |
          v
        Duck <---- focused read-only queries ----> Virelai
          |                                      memory / perception /
          |                                      semantic state machine
          v
    environment actions
          |
          v
 lossless frames and transitions
```

Duck remains the sole active solver. Virelai is not a second player, opening
Captain, prompt-length report, or competing policy. It should observe reality,
preserve it, compile useful structure, and answer focused questions when Duck
decides the information is useful.

Ring 7 proved that transporting a precomputed field card into Duck is possible,
but did not establish that forced static briefing is beneficial. In practice,
large field cards increased cognitive load and constrained a Duck solver that
already performs reasonably well without Virelai. The present hypothesis is
therefore narrower:

> Duck should retain control and selectively call Virelai as external memory
> and perception, rather than receive Virelai's entire interpretation by
> default.

We have deliberately stepped back from the full runtime. The live milestone
contains no observation, memory, semantic role, ontology addition, field card,
Captain, or win analysis. It tests only whether one read-only host call can
cross Duck's existing Python sandbox boundary and be followed by normal play.

## 2. Long-term cognitive philosophy

### 2.1 What Duck contributes

Duck's LLM is the meta-level problem solver. It is comparatively strong at:

- interpreting novel situations;
- proposing hypotheses;
- analogy and transfer;
- planning under uncertainty;
- choosing actions from compact evidence;
- revising an explanation when evidence contradicts it.

It is comparatively unreliable at:

- preserving exact long interaction histories in context;
- reconstructing frame-by-frame differences without distortion;
- maintaining stable object identity through motion and transformation;
- remembering every visited state and attempted action;
- separating observed mechanics from plausible narrative;
- retaining and transferring the exact causal structure of a level win.

Virelai exists to supply those missing capabilities in code rather than asking
the language model to simulate them internally.

### 2.2 What Virelai should eventually contribute

Virelai's intended substrate and semantic services are:

1. **Lossless evidence:** every frame, action, transition, level boundary,
   life/reset event, and observed win.
2. **Object continuity:** persistent entities rather than unrelated regions in
   successive frames.
3. **State memory:** an indexed map of visited visible states, attempted actions,
   revisits, self-loops, and divergent transitions.
4. **Semantic roles:** ego or god-mode control, counters, levers, affected
   regions, barriers, resources, and goal-relevant structures.
5. **Physics grammar:** how ego actions and levers transform the world,
   including direction, affected region, period, saturation, reversibility, and
   shared-resource coupling.
6. **Win analysis:** preserve any winning transition, regardless of whether it
   was caused by Duck or future automated probing; distinguish observation from
   inference; propose and falsify causal explanations; transfer the resulting
   goal model to the next level.

The semantic library should be understood as a model of the observed state
machine. Worldlines, segmentation, and weave records are construction evidence,
not the final player-facing product. Duck should receive semantic roles,
mechanics, evidence references, and focused answers—not a random survey of
every intermediate perceptual structure.

### 2.3 What the ARC ontology contributes

The ontology is the layer above Duck. It provides general truths and operating
orientation for ARC grid worlds, rather than claims about a particular game.
Its central ideas include:

- the environment is experienced as successive grid states connected by
  actions;
- knowledge is grounded in observable transitions rather than visual guesses;
- novelty is informative because an unobserved winning state must be novel
  until first reached;
- hidden state can be suspected when apparently identical visible conditions
  produce divergent transitions;
- a win is first observed, then explained and transferred;
- mechanics may persist across levels while geometry, object placement, and
  required conditions change.

Ontology refinement is postponed until the callable machinery is stable. It is
cheap to change but easy to confound with transport, memory, or semantic
changes.

## 3. Evidence from Ring 7

Ring 7 returned to the unmodified Ring 0 Duck architecture and successfully
delivered Virelai field-card content. That established the handshake. It did
not produce strong scores.

The correct inference is limited:

- static field-card transport works;
- forced broad context is not an efficient consumption mode for Duck;
- the field card may contain useful facts, but usefulness is not guaranteed by
  delivery;
- Duck should request the smallest relevant evidence at the moment it has a
  concrete uncertainty;
- the quality of Virelai's underlying empirical claims remains an independent
  hard problem.

Ring 7 does **not** falsify Virelai as memory or perception. It falsifies the
assumption that a large pre-play briefing is automatically useful.

## 4. Infrastructure failures and what they taught us

### 4.1 Failed Ring 8 smoke sequence

Early Ring 8 work built a technically capable passive evidence runtime but
surrounded it with too much new Kaggle machinery. Failures included:

- replacing standard Tufa notebook cells;
- importing a top-level grader that Tufa did not package;
- calling a helper that existed only in the notebook cell that had been
  replaced;
- assuming prompt artifact filenames that Tufa did not produce;
- introducing an OpenRouter path even though the production Duck uses local
  Qwen/vLLM on Kaggle;
- changing notebook type, game count, concurrency, runtime, and Virelai behavior
  in the same experiment.

One later smoke did run control and shadow Duck actions and produced a valid
passive archive, but Kaggle marked the notebook as failed because the in-run
grader looked for `prompts/<game>_p0.log` while the custom run wrote
`prompts/prompt.log`. Offline regrading passed the engineering checks. This
showed that Kaggle-side grading was itself a source of failure and should not
control notebook success.

### 4.2 Rejected `ring8-native-smoke`

The most recent rejected smoke used Tufa's non-share notebook with one offline
`vc33` fixture. Qwen/vLLM loaded correctly and passed its model warm-up, but the
benchmark failed before Duck ran because the package did not contain offline
environment files:

```text
RuntimeError: Offline env files (the '__auto__' mode) are not bundled in this
build. Run against the live competition Arcade, or pass an explicit
environments_dir.
```

It produced zero games, zero actions, and zero model tokens. It is not evidence
about Duck or Virelai. Its evaluation is:

`runs/kaggle-ring8-native-smoke-run1/EVALUATION.md`

### 4.3 Queue interpretation

Several failed builds were initially observed in Kaggle state `QUEUED`, leading
to a reasonable suspicion that queueing predicted failure. The unchanged Ring
0 version 3 also entered `QUEUED`, then ran cleanly to completion. Queueing is
therefore not a valid code-level failure signal by itself.

### 4.4 Permanent engineering lessons

1. The executed Kaggle bundle—not the development tree—is the product.
2. A successful local import does not prove packaged importability.
3. Generated notebook compilation does not prove runtime name availability.
4. Do not replace Tufa notebook cells for normal production experiments.
5. Do not grade inside the notebook; download immutable output and grade
   offline.
6. Missing artifacts are `NOT_MEASURED`, not equality or success.
7. Change one model-visible or execution-path variable per experiment.
8. Preserve the standard Tufa share path unless explicitly testing Tufa itself.
9. The share notebook owns the live competition game set and always runs all 25
   games. A one-game share smoke is not currently supported without changing
   the harness.

The infrastructure postmortem is located at:

`variants/ring8.0/KAGGLE_INFRASTRUCTURE_POSTMORTEM_2026-09-04.md`

## 5. Clean Ring 0 control

To separate Virelai problems from Kaggle/Tufa problems, the preserved Ring 0
package was rerun unchanged as Kaggle kernel version 3:

`stephenkaskin/duck-virelai-r0-dryrun`

It completed successfully on 2026-09-05:

- 25/25 games instantiated;
- 25/25 games executed actions;
- 3,958 total actions;
- 12/25 games completed at least one level;
- 15 total levels completed;
- maximum two levels completed in one game;
- sum of TAAF `final_score` values: `49.607350618002386`;
- wall time: approximately 2 hours 12 minutes;
- Kaggle state: `COMPLETE`.

This establishes that the preserved Ring 0 source, Tufa share notebook, local
Qwen/vLLM startup, competition Arcade path, and Duck action loop are healthy.
It is now the infrastructure control that every integration must preserve.

Files:

- package: `kaggle/dryrun-r0/`
- downloaded output: `runs/kaggle-ring0-rerun-v3/kaggle-output/`
- evaluation: `runs/kaggle-ring0-rerun-v3/EVALUATION.md`

The 49.61 value is one stochastic run, not a stable performance estimate. Its
primary role here is proof of execution health.

## 6. Current build: Ring 8 minimal callable proof

### 6.1 Experimental question

The current build asks exactly one question:

> Can the clean Ring 0 Duck call one read-only host function through its existing
> Python tool, receive the response, and subsequently execute a normal game
> action?

It does not test memory quality, semantic accuracy, strategy, score improvement,
or the ontology.

### 6.2 Exact source parent

The source tree was copied directly from the executed Ring 0 source dataset:

- Ring 0 Duck parent:
  `kaggle/dryrun-r0/source-dataset/src/ARC3-Inference/`
- Ring 0 Tufa parent:
  `kaggle/dryrun-r0/source-dataset/src/tufa-arc-agi-framework/`
- minimal candidate Duck source:
  `variants/ring8-minimal-tool/ARC3-Inference/`
- minimal candidate Tufa source:
  `variants/ring8-minimal-tool/tufa-arc-agi-framework/`

Tufa is unchanged from Ring 0.

### 6.3 Exact production diff

Only two production files differ from Ring 0:

1. `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/python_tool_sandbox.py`
2. `variants/ring8-minimal-tool/ARC3-Inference/inference/agent/tool_agent.py`

There are no changes to:

- `inference/framework/solver.py`;
- Tufa;
- game construction;
- action execution;
- scheduling;
- provider/model configuration;
- notebook orchestration;
- output or submission handling.

### 6.4 Minimal function behavior

The existing provider-level tool remains `python`. No second provider tool is
added. Inside the existing isolated Python sandbox, one new callable exists:

```python
virelai("status")
```

It performs one sandbox-to-host round-trip and returns only:

```json
{
  "schema": "virelai-minimal-status-v1",
  "operation": "status",
  "available": true,
  "read_only": true
}
```

The handler reads no game state, holds no memory, and has no reference to the
game action callback. Unsupported operations fail. The sandbox collects status
responses separately from action results, and the Python-tool result exposes a
count and the last fixed status response when a call occurred.

The system prompt contains one explicit interface-test instruction:

```text
Before your first game action, call print(virelai('status')) once inside Python.
After it returns, continue solving normally with action(...).
```

This instruction is intentionally stronger than the eventual manual. The
current goal is to obtain an observable transport proof, not to measure natural
tool selection or score.

### 6.5 Local proof

Test file:

`variants/ring8-minimal-tool/ARC3-Inference/tests/test_minimal_virelai_bridge.py`

The isolated sandbox test executes the following order inside one Python call:

```text
virelai('status')
  -> fixed host response
  -> action('ACTION1')
  -> executed action result
```

Results:

- two focused tests passed;
- static analysis passed;
- isolated packaged bridge-to-action test passed;
- rendered share notebook cells compiled with IPython top-level-await support;
- packaged versions of the two changed files equal the source candidate;
- Tufa's share notebook template is byte-identical to Ring 0;
- package hygiene passed with no `__pycache__`, `.pyc`, or `.DS_Store` files.

### 6.6 Exact Kaggle build shape

The candidate uses:

- standard `taaf_kaggle_run_share.ipynb`;
- all 25 official competition games;
- one pass;
- concurrency 28;
- 132-minute maximum runtime per game;
- 540-minute experiment cap;
- local `vrfai/Qwen3.6-27B-FP8` through vLLM;
- the same wheelhouse and model datasets as Ring 0;
- Nvidia RTX Pro 6000;
- internet disabled;
- no submission;
- no custom run cell;
- no in-notebook grader.

Package locations:

- full candidate: `kaggle/ring8-minimal-tool/`
- source dataset: `kaggle/ring8-minimal-tool/source-dataset/`
- kernel: `kaggle/ring8-minimal-tool/kernel/`
- build record: `kaggle/ring8-minimal-tool/RUN.md`
- design record: `variants/ring8-minimal-tool/README.md`

Remote identities:

- dataset:
  `stephenkaskin/taaf-kaggle-source-duck-virelai-ring8-minimal-tool`
- kernel:
  `stephenkaskin/taaf-duck-virelai-ring8-minimal-tool-share`
- active kernel version: 2
- current state at memo time: `QUEUED`

Version 1 was cancelled while the clean Ring 0 control ran. Version 2 is the
current evidence-bearing attempt.

### 6.7 Registered live pass condition

At least one downloaded game transcript must establish these facts in order:

1. Duck emitted Python containing `virelai('status')`.
2. The Python tool returned schema `virelai-minimal-status-v1` with
   `available: true` and `read_only: true`.
3. Duck subsequently executed at least one legal environment action.

The ordinary Tufa benchmark must complete with real games and actions. Score is
recorded but is not a pass criterion for this transport milestone.

The stronger audit should count, per game:

- whether the status instruction was present;
- number of status calls;
- number of successful status returns;
- whether a legal action followed the first return;
- whether any sandbox, analyzer, or action error occurred;
- total actions and levels completed.

## 7. Current frictions

### 7.1 No cheap production-shaped share smoke

The standard share notebook replaces local fixture selection with the complete
competition game set. Therefore the clean production path consumes a full
25-game run. A small Kaggle smoke currently requires either the non-share
offline path with explicit environment files or a first-class Tufa feature.
We will not patch generated notebook cells to obtain it.

### 7.2 Interface proof versus useful memory

The current fixed response proves transport only. It cannot demonstrate that
Virelai memory is correct, relevant, or helpful. Those are later gates and must
not be inferred from this run.

### 7.3 Forced call versus natural use

Duck is explicitly told to make one status call. Success proves capability, not
that Duck will recognize when to query memory unaided. Natural tool selection
must be tested only after the returned evidence is genuinely useful.

### 7.4 Exact execution preservation

The campaign repeatedly lost time by changing deployment infrastructure while
trying to change cognition. The present discipline is that Tufa and the solver
remain frozen unless the experiment specifically targets them. New Virelai
capabilities should enter through the narrowest existing Duck-owned seam.

### 7.5 Evidence visibility

Live proof depends on downloaded transcripts and Python-tool results. A
notebook's `COMPLETE` state alone is insufficient. Conversely, an in-notebook
grader must not be allowed to convert completed gameplay into Kaggle `ERROR`.

### 7.6 Semantic accuracy remains unproven

V4 contains valuable perception, weave, lever-probing, and library concepts,
but prior audits found known overproduction and misclassification risks:

- background may be mistaken for a counter;
- moving ego instances may be repeatedly reminted;
- region counts may greatly exceed coherent worldline counts;
- confident semantic labels may outpace their evidence.

No V4 semantic claim should be exposed to Duck until that claim family is
graded against hand-labelled replays, including expected discontinuities and
negative cases.

## 8. Forward build ladder

Every step preserves the preceding successful build and adds one measurable
capability.

### Step 1 — finish the minimal callable proof

Wait for kernel version 2. Download immutable output. Grade the registered
three-part chain and ordinary benchmark execution. Do not repair or reinterpret
the run before reading its artifacts.

If it fails, remain at this step and repair only the measured bridge defect. If
it passes, freeze the exact two-file interface as the callable transport base.

### Step 2 — replace fixed status with the smallest real memory

Add one host-owned bounded operation, provisionally:

```python
virelai("recent")
```

The first response should contain only facts from the latest completed
transition:

- observation/action number;
- action executed;
- whether the visible grid changed;
- exact changed coordinates and before/after values, bounded with explicit
  truncation if necessary.

No objects, semantic names, goals, recommendations, or causal claims enter this
step. The pass condition is real evidence returned followed by continued play.

### Step 3 — establish lossless passive memory

Move from one recent transition to a per-game append-only journal:

- initial frame plus every successful post-action frame;
- N actions imply N+1 frames and N transitions;
- complete canonical artifacts are never truncated;
- query views are bounded and explicitly mark truncation;
- observer faults cannot alter Duck's action payload or stop play;
- each game/pass has an independent artifact path.

The existing Ring 8.0 runtime is port-source material, not automatically the
production implementation. Useful code should be ported behind the proven
minimal interface without reviving its custom Kaggle wrapper.

Relevant port-source locations:

- `variants/ring8.0/ARC3-Inference/inference/framework/virelai_runtime.py`
- `variants/ring8.0/ARC3-Inference/inference/framework/game_observer.py`
- `variants/ring8.0/ARC3-Inference/tools/benchmark_ring80a.py`
- `variants/ring8.0/ARC3-Inference/tools/replay_ring80b.py`

### Step 4 — bounded raw-memory queries

Expose one operation family at a time through the existing Python callable:

- `recent`;
- one exact `transition`;
- visible-state visits/revisits;
- action attempts from a visible state;
- observed winning transitions;
- capture gaps or failures.

Responses must name their observation boundary, remain JSON-safe, meet a query
latency budget, and contain no unstable object or weave identifiers.

### Step 5 — test actual Duck use

Once the evidence is useful, reduce the forced instruction to a compact manual.
Grade behavior rather than prompt echo:

- Did Duck ask a question relevant to its current uncertainty?
- Did the response contain evidence unavailable or inconvenient in immediate
  context?
- Did Duck subsequently act consistently with that evidence?
- Did the query prevent repetition or recover older knowledge?

Transport, use, and game outcome remain separate metrics.

### Step 6 — stable identity and semantic compilation

Build object continuity offline from immutable journals. Label a continuity
fixture before implementation, including both expected matches and expected
breaks. Promote semantic claim families independently:

1. control mode: navigation, click, or hybrid;
2. ego/god-mode identification;
3. counter identification with background exclusion;
4. lever identity and location/class/size;
5. lever effect region;
6. direction, period, saturation, reversibility;
7. coupling through shared resources;
8. remaining unknowns.

Every claim exposed to Duck should distinguish observation from inference and
reference supporting transitions.

### Step 7 — learn to win

On every observed level win, regardless of actor:

- preserve the exact pre-win frame, action, and post-win transition;
- identify participating objects and regions;
- record necessary visible conditions;
- generate competing causal explanations;
- define falsification or transfer tests;
- provide a concrete goal model for the next level.

The intended deliverable is not merely "a win occurred." Duck should be able to
explain why it believes the action won, state the uncertainty in that
explanation, and use it productively on level N+1.

### Step 8 — ontology refinement

After the tool, memory, semantic claims, and win loop are stable, tune the ARC
ontology separately. Compare ontology variants against Ring 0 or the frozen
callable base without simultaneous machinery changes.

## 9. Promotion and kill rules

Promote a stage only when its registered mechanism is directly observed in
artifacts. Do not promote because a run feels promising or scores well.

Return to the same stage when:

- the required call or evidence is absent;
- Duck cannot act after a query;
- zero games or actions execute;
- packaging differs from the reviewed bundle;
- the notebook uses a nonstandard execution path;
- required artifacts are missing or ambiguous.

Reconsider the architecture if:

- a callable cannot be added without modifying Tufa or Duck's action path;
- passive capture materially changes Duck behavior or throughput;
- useful queries cannot meet bounded latency late in long games;
- semantic accuracy cannot exceed the harm caused by confident wrong claims.

## 10. Immediate collaborator task

Do not modify or upload another build while the current minimal-tool kernel is
queued/running. When it completes:

1. download its complete output into a new immutable run directory;
2. verify 25 real game runs and nonzero actions;
3. inspect every prompt/transcript for the status call, fixed response, and
   subsequent action;
4. produce per-game and aggregate transport grades;
5. report score separately without treating it as the interface gate;
6. decide whether the two-file callable seam is frozen or must be repaired.

The next code change is not authorized by this memo. The evidence from the live
minimal-tool run determines it.

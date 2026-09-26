# Collaborator Build Update — Ring 8 Expandable Memory Card Delivery Fix

**Date:** 2026-09-13  
**Status:** Packaging mismatch corrected; Kaggle notebook version 2 is running  
**Primary experiment:** Automatic compact memory at a level transition, with optional expansion on demand

## Executive status

The current Virelai–Duck architecture is mechanically mature enough to record complete play, compile persistent evidence, preserve a previous-level win, and answer focused read-only queries. The immediate research question is narrower: when Duck enters level 2, does a compact summary of the observed level-1 win help it reuse prior knowledge without disrupting its native play?

The first expandable-card Kaggle run did not answer that question because the card was computed but omitted from the model-visible prompt. A successor build fixes the production prompt path and improves the card's compact semantic content without changing Duck's action policy, ontology, model, cohort, or budgets.

That successor was uploaded on 2026-09-13. Its first launch failed after approximately eight seconds, before model loading or gameplay, because the source dataset's bundle marker retained the parent build label. The notebook correctly searched for the successor label and rejected the mismatch. This is a packaging/provenance failure, not a runtime, model, observer, card, or gameplay result.

## Governing architecture

Duck remains the active solver. It chooses every environment action.

Virelai supplies capabilities Duck does not reliably maintain by itself:

1. A lossless record of frames, actions, and transitions.
2. Persistent evidence across model calls and level boundaries.
3. Compiled object continuity, mechanics, win-boundary evidence, and possible cross-level counterparts.
4. A compact player-facing index that can be expanded through focused queries.

The presentation rule is progressive disclosure:

- automatically present one bounded card when a new level begins after an observed win;
- include only observed facts or explicitly marked uncertainty;
- expose focused expansion handles for the prior win, mechanics, carry candidates, or the full lesson;
- do not require an experiment, force a Virelai call, or prescribe Duck's next action.

This separates memory delivery from policy control. The current run is intended to test whether guaranteed visibility plus voluntary expansion is sufficient.

## Evidence preceding this build

The first expandable-card diagnostic completed five games cleanly:

| Game | Score | Levels cleared | Actions |
|---|---:|---:|---:|
| ar25 | 0.00 | 0 | 65 |
| bp35 | 0.00 | 0 | 70 |
| lp85 | 2.78 | 1 | 74 |
| ls20 | 0.00 | 0 | 52 |
| r11l | 0.00 | 0 | 51 |

It produced a mean score of 0.56, one level-1 win, no level-2 win, 312 actions, and 120,061 model tokens. All five observation archives passed integrity checks.

The crucial audit finding was that Virelai internally generated `card(level=2)` after lp85's win, but `VIRELAI WORLD MEMORY` never appeared in the actual model prompt. The Virelai-specific branch of `ToolAgent._build_user_prompt()` returned before the older card-insertion path.

Even without the automatic card, Duck later called the prior-level `lesson`, `win`, and `carry` views voluntarily. This supports the expandable-memory concept: Duck recognized that persistent prior-level evidence could answer a current-level uncertainty. It did not establish a successful transferred plan and did not win level 2.

The complete evaluation is at:

`runs/kaggle-ring8-expandable-memory-card-v1-20260913/EVALUATION.md`

## Successor build: exact changes

The successor is rooted at:

`variants/ring8-expandable-memory-card-delivery-fix/`

Its principal changes are:

### 1. Production delivery repair

`ARC3-Inference/inference/agent/tool_agent.py`

The Virelai prompt branch now inserts `_transition_briefing_text` before returning. It inserts the card only when `_transition_briefing_level` equals the current frame's level. The card is therefore available in the first level-2 user prompt and does not leak into unrelated levels.

The transition hook in `ToolAgent.analyze()` requests `card(level=current_frame.level)` after a recorded level transition and stores its rendered text for prompt construction.

### 2. End-to-end delivery regression test

`ARC3-Inference/tests/test_memory_card_delivery.py`

The test follows the relevant production path:

1. `_build_user_prompt()`;
2. `_build_user_message()`;
3. context trimming;
4. inspection of the final user message.

It requires exactly one memory-card sentinel in the first level-2 request and requires the sentinel to be absent from an unrelated level.

### 3. Compact card compiler and renderer

`ARC3-Inference/inference/framework/virelai_memory_card.py`

The card presents:

- entered and completed levels;
- world mode when established;
- exact observed winning action;
- earlier same-action failures as contrast evidence;
- compact observed mechanics;
- possible cross-level counterparts;
- explicit withheld or omitted-record counts;
- focused expansion handles.

The compact view is an index, not the canonical evidence store.

### 4. Runtime query surface

`ARC3-Inference/inference/framework/virelai_runtime.py`

`card` and compatibility alias `briefing` compile the current model, locate the previous completed-level lesson, obtain focused win/mechanics/carry views, and render the compact card. Existing focused operations remain available:

- `virelai('lesson', level=N)`
- `virelai('win', level=N)`
- `virelai('mechanics', level=N)`
- `virelai('carry', level=N)`

### 5. Mechanics presentation improvements

`ARC3-Inference/tools/render_physics_grammar.py`

The successor carries remote-effect type, direction, and measured period into the player-facing mechanics view. It also carries shared opposing-control relationships, which matter in worlds such as vc33 where two levers move a shared resource in opposite directions.

### 6. Real-archive rendering and fixtures

`ARC3-Inference/tools/render_memory_card_from_archive.py`

Checked card artifacts:

- `ARC3-Inference/offline-gates/pilot/lp85-real-card.json`
- `ARC3-Inference/offline-gates/pilot/ar25-real-card.json`

lp85 demonstrates a usable pointer-world card. ar25 demonstrates honest withholding: raw control records without a usable compact location/effect description remain available behind expansion and are disclosed rather than fabricated.

## Validation state

The frozen Kaggle package reports:

- 103 source tests passed;
- 103 packaged-source tests passed;
- 172 files compared;
- source/package equality confirmed;
- notebook syntax checked;
- configuration hook checked;
- cohort selection checked;
- competition guard checked.

The variant's `BUILD_STATUS.md` says 113 tests passed, while the final frozen package record says 103. The authoritative launch artifact is the package record at `kaggle/ring8-expandable-memory-card-delivery-fix/TEST_RESULTS.txt` and `variants/ring8-expandable-memory-card-delivery-fix/offline-gates/package.json`. The discrepancy is documentation debt and should be reconciled; it is not evidence of package inequality.

Offline prefix replay passed on ar25, bp35, lp85, ls20, and r11l. The replay also exposed an existing cost risk: bp35's long prefix required much more semantic query time than the other worlds. The live diagnostic must preserve query timing and game-budget data.

## Kaggle package and experiment configuration

Package root:

`kaggle/ring8-expandable-memory-card-delivery-fix/`

Source dataset directory:

`kaggle/ring8-expandable-memory-card-delivery-fix/source-dataset/`

Notebook directory:

`kaggle/ring8-expandable-memory-card-delivery-fix/kernel/`

Published private dataset:

`https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-r8-memory-card-fix`

Published private notebook:

`https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-r8-memory-card-fix-share`

Frozen experiment:

- cohort: ar25, bp35, lp85, ls20, r11l;
- 150 actions per world;
- 1,200 seconds per world;
- concurrency five;
- same Qwen 27B model package and offline vLLM arrangement as the preceding diagnostic;
- private GPU notebook;
- internet disabled;
- no competition submission;
- card ceiling: 700 model tokens at Kaggle preflight.

## First launch failure

Downloaded failure artifact:

`runs/kaggle-ring8-expandable-memory-card-delivery-fix-v1-20260913/kaggle-output/taaf-duck-virelai-r8-memory-card-fix-share.log`

Failure:

`RuntimeError: TAAF source bundle not found under /kaggle/input.`

Exact cause:

- Notebook expects bundle marker label: `duck-virelai-ring8-expandable-memory-card-delivery-fix`.
- Uploaded `taaf-kaggle-bundle.json` contains parent label: `duck-virelai-ring8-expandable-memory-card`.

The failure occurred in notebook cell 3 during `_find_bundle_dir()`, approximately eight seconds after start. No Virelai runtime, model server, Duck turn, environment action, or game was instantiated. This run provides no architecture or gameplay evidence.

Relevant files for the mismatch:

- `kaggle/ring8-expandable-memory-card-delivery-fix/source-dataset/taaf-kaggle-bundle.json`
- `kaggle/ring8-expandable-memory-card-delivery-fix/kernel/taaf_kaggle_run_share.ipynb`

## Required recovery before relaunch

The next build action is deliberately small:

1. Change only the source marker's `benchmark_label` to the successor label expected by the notebook.
2. Recompute the source manifest if that marker is covered by package integrity metadata.
3. Re-run package parity and notebook preflight checks.
4. Publish a new dataset version rather than a new dataset identity.
5. Push a new notebook version and confirm that source discovery prints the mounted bundle path before waiting for the full run.

Do not change the card, ontology, agenda, model, cohort, budgets, or action policy in this recovery. The purpose remains a one-variable automatic-delivery experiment.

## Live evaluation gates after a successful relaunch

### Engineering gates

- all five diagnostic records complete;
- all frame archives pass integrity verification;
- no observer or query exceptions;
- card is generated only after an observed level completion;
- first model request in the new level contains exactly one card;
- no Virelai-selected environment action;
- preflight card remains within 700 tokens;
- query latency and total game time remain recorded.

### Behavioral gates

For every observed level transition, grade:

1. Did the card appear before Duck's first new-level action?
2. Did Duck refer to any prior winning action, mechanic, object, or uncertainty?
3. Which expansion handles did Duck call?
4. Did expansion clarify its plan rather than merely add tokens?
5. Did Duck reach or complete level 2?

Worlds without a level-1 win must be marked `not exercised`, not counted as card failures.

### Interpretation limits

This five-world run is an architecture-uptake diagnostic, not a score ablation. One stochastic run cannot prove performance improvement. A clean result can establish that automatic memory is delivered, readable, voluntarily expandable, and behaviorally referenced. Any score claim requires matched repeated controls later.

## Current decision

The architecture remains worth testing. The prior run showed that Duck voluntarily seeks previous-level evidence; the current successor is designed to make the compact index reliably visible at the moment it becomes useful. The failed launch does not bear on that hypothesis, but it does reinforce the need to treat dataset marker, manifest, notebook selector, and published dataset version as one checked interface.

Repair the single provenance label, revalidate package identity, and relaunch the unchanged experiment.

## Recovery executed

The recovery was completed after this report's initial drafting:

- the frozen bundle marker was corrected;
- the packaging script was corrected so rebuilding cannot restore the parent label;
- all 190 manifest entries verified;
- packaged source matched the reviewed variant;
- the complete packaged suite passed: 113 tests, 14 dependency warnings;
- temporary `.venv` and `__pycache__` directories were removed from the shipping tree;
- Kaggle dataset version 2 was published;
- Kaggle notebook version 2 was launched;
- current status at launch verification: `RUNNING`.

The experiment itself remains unchanged.

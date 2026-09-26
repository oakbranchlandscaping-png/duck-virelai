# Build slice: universal ontology and cybernetic targeting prompt

**Date:** 2026-09-20  
**Active source:** `variants/ring9-cybernetic-gates/`  
**Status:** Built and locally verified; the completed G0-G2 v2 run contained only the earlier
compact flip-book prompt, not this full integration

## Question

How should Duck receive the stable ARC grid-multiverse ontology and the cybernetic targeting method
so that it stays oriented toward physics discovery while the controller gives it one simple target
at a time?

## Research findings

Primary model guidance supports four decisions used in this slice.

1. **Use the real system role and the model's native chat template.** Qwen documents ChatML system,
   user, assistant, tool-call, and tool-response roles and recommends using the tokenizer/template
   rather than hand-formatting tool calls. The existing OpenAI-compatible vLLM path already does
   this, so the ontology belongs in the system message rather than in repeated user prose.
   Source: <https://github.com/QwenLM/Qwen3/blob/main/docs/source/getting_started/concepts.md>

2. **Keep stable doctrine separate from volatile state.** Qwen Code's current prompt architecture
   explicitly orders stable, context, and volatile prompt layers. Our equivalent is universal
   ontology -> targeting doctrine -> dynamic gate/evidence.
   Source: <https://github.com/qwenlm/qwen-code/blob/main/packages/core/src/core/prompts.ts>

3. **Use clear, consistent sections.** Anthropic and Google both recommend clear, direct
   instructions and consistent XML tags or Markdown headings to separate role, context,
   constraints, and tasks. This slice uses Markdown headings because the Qwen tool template itself
   already uses XML-like tool-call tags.
   Sources: <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables>,
   <https://ai.google.dev/gemini-api/docs/prompting-strategies>

4. **Decompose complex work into chained subtasks.** Google's primary prompting guide recommends
   breaking complex prompts into simpler components and chaining them. This directly supports the
   project's central bet: one binding gate at a time, with each gate's product becoming context for
   its dependent successor.
   Source: <https://ai.google.dev/gemini-api/docs/prompting-strategies>

These are design priors, not proof that this exact wording improves ARC performance. Behavioral
value must be measured against live traces.

## Prompt architecture

The gated prompt now has three conceptual layers.

### Layer 1 — Stable ontology

The complete `ARC_GRID_MULTIVERSE_ONTOLOGY` is included in gated mode. It defines:

- grids as partial observations of deterministic state;
- cell arithmetic before semantic interpretation;
- action-roster control archetypes;
- embodied, pointer, and hybrid obligations;
- levers as relational roles;
- hidden-state evidence;
- observed wins;
- scoped inertness;
- the complete role vocabulary;
- cross-level transfer as prior evidence rather than guaranteed truth.

### Layer 2 — Stable cybernetic mission

The new `CYBERNETIC_TARGETING_MISSION` states:

- discover physics through interaction and record keeping;
- never begin by guessing a winning state;
- work on one binding epistemic target;
- state alternatives and use the smallest authorized discriminating probe;
- read literal integer arithmetic before assigning function;
- explain subject, mechanism, conditions, evidence, alternative, falsifier, and limitations;
- promote a stable law only after required prospective support;
- record off-target effects without abandoning the active gate;
- accumulate versioned laws and reopen them on contradiction;
- follow the dependency spine from action surface through observed-win transfer.

The mission now also states the binding Captain opening protocol: read metadata, assign world
type, use click-everything for `CLICK_GOD_MODE`, and use Delphi-then-collide-everything for
`NAVIGATION` and `HYBRID`. Duck must follow the controller's deterministic visual-object order.
See `BUILD_SLICE_BINDING_OPENING_PROTOCOL_2026-09-20.md` for the executable boundary.

### Layer 3 — Volatile gate and evidence

The per-turn user message continues to carry:

- current state and available opaque actions;
- compact carried evidence;
- active gate question and status;
- current unmet requirements;
- the next authorized `ProbeEnvelope`, when applicable.

The ontology supplies language. The current gate supplies focus. Observations supply world facts.

## Removed gated-mode conflicts

The gated system and turn prompts no longer ask Duck to:

- infer what the goal likely is;
- infer a desired environment change before the relevant physics exists;
- self-advance from probing into search;
- treat an edge bar as a timer from appearance alone;
- optimize for solving the entire game while a narrower gate is binding.

Those generic solver instructions remain available outside gated mode.

Gated turn updates now use these fields:

- `Gate model`
- `Live alternatives`
- `Evidence`
- `Candidate law`
- `Falsifier`
- `Limitations`
- `Next test`

## Verification

- The complete Ring 9 suite passes: **273 tests**.
- Targeted prompt, bridge, observer, and agenda tests pass: **40 tests**.
- Targeted Ruff checks pass.
- The generated gated system prompt contains exactly one full ontology and one targeting doctrine.
- Tests require the action-archetype axiom, lever definition, complete target spine, stable-physics
  objective, observed-win rule, gate instructions, and opaque action names.
- Tests reject legacy goal-guessing phrases, appearance-based timer classification, and semantic
  action aliases.
- The generated prompt is approximately 2,650 words, well within the checkpoint's 65,536-token
  context budget.

## Evidence boundary

The completed Kaggle version 2 was frozen before this slice. It contains the earlier compact
flip-book prompt and gate instructions, but not this full integration. Its results remain valid for
the frozen G0-G2 controller package, but they cannot validate the universal-prompt hypothesis.

The next package produced after that checkpoint must include this slice and receive a new
package hash, source-manifest hash, receipt, and notebook version.

## Live evaluation

Compare future traces against the existing evidence without changing model, worlds, budgets, or
concurrency. Review whether Duck:

1. states the active gate rather than inventing a global goal;
2. keeps off-target discoveries without switching focus prematurely;
3. explains mechanisms rather than supplying category labels;
4. carries earlier gate products into later explanations;
5. stops probing when the controller recognizes satisfaction;
6. avoids declaring an unobserved win;
7. uses the ontology as a hypothesis language rather than as a source of assumed facts.

The expected benefit is better focus and better explanatory continuity. It is a hypothesis until
the served model demonstrates those changes.

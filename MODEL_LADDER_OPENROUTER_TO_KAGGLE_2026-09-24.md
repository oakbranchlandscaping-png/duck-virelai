# Model ladder: fast OpenRouter development to exact Kaggle milestones

**Date:** 2026-09-24  
**Status:** standing policy for the current Qwen3.6 campaign  
**Scope:** model choice and evidence boundaries; no historical run is reclassified

## Decision

Use models according to the question being tested. The strongest available API model is not
automatically the best development model, because a model that is substantially stronger or from
a different family can hide instruction, tool-use, or answer-shape weaknesses that will reappear
on Kaggle.

### Lane A — deterministic local contract

No served LLM. Use fixtures, replayed production traces, and the full local suite to validate
state transitions, evidence, identity, masks, retries, and certificates.

### Lane B — fast live infrastructure

Candidate: `qwen/qwen3.6-35b-a3b` through OpenRouter. It is from the same Qwen3.6 generation,
accepts the same multimodal inputs, supports thinking, tools, and structured output, and activates
about 3B parameters per token. It is a speed proxy for finding control-flow defects. A pass here
does not predict exact dense-model behavior.

### Lane C — Kaggle behavioral rehearsal

Use `qwen/qwen3.6-27b` through OpenRouter. This is the same dense 27B model family as Kaggle's
`vrfai/Qwen3.6-27B-FP8` and OpenRouter lists it as FP8. Match the Kaggle context window, sampling,
reasoning mode, tool schema, and output budget. Pin a verified FP8 provider for receipted milestone
rehearsals; use throughput routing only for explicitly labeled speed runs.

This is the default model for deciding whether a completed gate slice is ready for Kaggle.
OpenRouter and Kaggle still use different serving stacks, so agreement is strong rehearsal
evidence rather than execution identity.

### Lane D — exact Kaggle milestone

Use the frozen Kaggle package with `vrfai/Qwen3.6-27B-FP8` under local vLLM. Run one world for one
gate milestone. Broaden to multiple world types only after the one-world exit passes.

### Lane E — ceiling diagnostic or future campaign

`qwen/qwen3.8-27b` is a newer, stronger open-weight dense model with tools, structured output,
multimodal input, flexible thinking, and a much larger context. It is useful as a labeled ceiling
diagnostic: if it passes while Qwen3.6 fails, the remaining issue may be engine capability or
compatibility. It does not replace the Qwen3.6 rehearsal inside the current fixed-model campaign.
Adopting it as the Kaggle model requires the campaign-boundary protocol in
`DESIGN_MODEL_PORTABILITY_v1_2026-09-23.md`.

## OpenRouter adapter slice

**Status:** built and locally/live-canary verified on 2026-09-24.

The active configuration previously requested `Qwen/Qwen3.6-27B`, but the request builder did not
bind several OpenRouter-specific variables. The completed slice now:

1. uses canonical lowercase model slugs in the new profiles;
2. makes reasoning configuration explicit rather than relying on provider defaults;
3. supports provider order/allowlists, fallback, quantization, parameter support, and routing sort;
4. records requested model/profile and returned model, routed provider, and response id;
5. preserves the 65,536-token Kaggle rehearsal context and matched output/tool budgets;
6. supplies separate fast-development and Kaggle-rehearsal configurations;
7. labels dynamic throughput routing as a speed run rather than a reproducible comparison.

The live non-game canary used `qwen/qwen3.6-35b-a3b`, explicit medium reasoning, FP8-only
throughput routing, and a forced Python call. It returned the requested model through Venice,
included reasoning, and emitted valid `python` arguments. OpenRouter returned the provider but did
not echo quantization; the receipt therefore distinguishes a requested FP8 constraint from a
provider-reported fact.

OpenRouter automatically uses quality-weighted provider routing for requests that include tools,
but the actual provider can still vary. Reproducible comparisons therefore require a provider pin
and receipt rather than an unrecorded default route.

## Promotion rule

```text
local contract
-> fast OpenRouter slice when rapid iteration is useful
-> dense Qwen3.6 OpenRouter rehearsal
-> exact Qwen3.6 FP8 Kaggle milestone
-> broader world-type smoke
-> full campaign only when justified
```

Failure returns to the cheapest lane capable of reproducing it. Model changes, provider changes,
budgets, worlds, and concurrency are recorded and never silently compared as one cohort.

## Sources checked on 2026-09-24

- OpenRouter Qwen3.6 27B model and provider pages
- OpenRouter Qwen3.6 35B A3B model and endpoint metadata
- OpenRouter Qwen3.8 27B model page
- OpenRouter tool-calling and Auto Exacto documentation

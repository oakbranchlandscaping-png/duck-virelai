# Build slice: receipted OpenRouter development and Kaggle-rehearsal profiles

**Date:** 2026-09-24  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Status:** built; 336-test suite and one live non-game tool canary passed

## Purpose

Insert a fast, observable live-model step between local contracts and Kaggle. The slice makes an
OpenRouter run answer two questions cleanly:

1. Which model and routing contract did we request?
2. Which model and provider actually answered?

It does not make an OpenRouter pass equivalent to Kaggle. The serving stacks remain different.

## Implemented controls

OpenRouter payloads can now bind:

- explicit reasoning enablement and effort;
- temperature, top-p, top-k, seed, output limit, and tool choice;
- provider order or allowlist;
- FP8 or another requested quantization class;
- provider fallback behavior;
- throughput/latency/price routing sort;
- a requirement that the chosen provider support the sent parameters.

Request logs record the requested model and serving profile. Response records add the returned
model, routed provider, and response id. `run_config.json` records the run-level serving profile
without recording an API key.

## Profiles

### Fast development

`configs/g3-vc33-openrouter-fast.json`

- model: `qwen/qwen3.6-35b-a3b`;
- one vc33 world;
- 32 actions and 15 minutes;
- medium reasoning;
- FP8-only, throughput-sorted provider routing;
- provider fallback allowed;
- 2,048-token response cap.

This profile finds controller, tool, answer-shape, retry, and stopping defects quickly. It is not a
dense-model comparison.

### Kaggle rehearsal

`configs/g3-vc33-openrouter-kaggle-rehearsal.json`

- model: `qwen/qwen3.6-27b`;
- one vc33 world;
- 96 actions and 45 minutes;
- 65,536-token context and server-default response ceiling;
- medium reasoning;
- DeepInfra-only FP8 routing with fallback disabled;
- the same tool-output budget as Kaggle.

This is the promotion test before a new exact-model Kaggle milestone. Provider pinning improves
repeatability, but the OpenRouter chat template and infrastructure still differ from local vLLM.

## Validation

- eight focused compatibility and request tests passed;
- the complete suite passed: 336 tests;
- changed-file lint passed;
- both new JSON configurations and the revised default OpenRouter configuration parsed;
- configuration extraction returned the intended canonical models and routing values;
- a live non-game fast-profile canary returned:
  - model `qwen/qwen3.6-35b-a3b`;
  - provider `Venice`;
  - finish reason `tool_calls`;
  - explicit reasoning;
  - Python tool arguments containing `result = 1`.

The canary proves payload acceptance, routing, response identity capture, and tool-call syntax. It
does not prove ARC behavior or any gate.

## Operational rule

After a local slice passes, use the fast profile when the likely failure is infrastructure or
control flow. Use the dense rehearsal before Kaggle. Promote to Kaggle only when the same gate
exit criteria pass on the rehearsal profile. A failed run returns to the cheapest lane that can
reproduce it.

The Kaggle v3 package was immutable and did not contain this later infrastructure
slice.

# Design: model portability — the engine is a plug, and we always run the best legal one

**Type:** `DESIGN_MODEL_PORTABILITY` · **v1** · **2026-09-23**
**Status:** standing design policy, Director-ordered. The roster in §4 is the part of this
document that goes stale; it is refreshed by a new version at every campaign boundary, and the
highest version's roster is the only current one.

## 1 · The standing policy

The gates, evidence, attribution, lifecycle, masks, and certificates are the deliverable; the
served model is the interpretation engine behind one tool surface. **As models improve, we plug
in the highest-quality, Kaggle-compatible model available** — deliberately, at campaign
boundaries, through the protocol in §3 — so the instrument's measured capability rises
monotonically with the field. The corollary is a paper-grade experiment we get for free: same
rails, same worlds, same certificates, different engine, with the execution receipt recording
the model identity, is a direct measurement of engine contribution versus gate contribution.

## 2 · What is portable and what is not (the boundary, verified in this tree)

Portable with zero change: every gate machine, the capability-token protocol, the evidence
compiler, attribution kernel, lifecycle journal, masks and quotients, the evaluators (they
grade artifacts, never models). Already demonstrated: the same stack has run behind Qwen
3.6-27B on local vLLM (Kaggle), Qwen via OpenRouter, and an OpenAI-served run — each swap was
configuration.

Model-specific, by design thin, and the whole cost of a swap: **(a)** the provider/serving
profile (request ceilings, rate-limit semantics, tool-calling dialect adapter in the serving
layer); **(b)** the size preflight re-run with the target model's tokenizer (char→token ratios
differ by family; budgets are per-profile constants per
`BUILD_SPEC_G3_CONTEXT_COMPACTION_v1`); **(c)** the answer-shape normalizers, which are tuned
to how a given engine misformats — new engines misformat differently, and the error-first
visible-rejection design is what lets a competent engine self-correct while the normalizer set
catches up.

## 3 · The swap protocol (binding; each step is cheap, skipping any has bitten before)

1. **Campaign boundary only.** The identical-cohort law: never swap inside a campaign — a
   comparison is meaningful only at fixed model, worlds, and budgets, and the receipts will
   expose a mid-campaign fork.
2. **Sweep before choosing.** Re-run the web/benchmark sweep at decision time (the §4 roster is
   evidence-classed as external builder reports and dated). Kaggle constraint check first:
   internet disabled on accelerated sessions → open weights only, served locally; current top
   accelerator is the RTX 6000 tier (RTX PRO 6000 Blackwell, 96 GB) per the ARC Prize 2026
   docs.
3. **Verify the exact checkpoint under the real serving stack.** Aggregator numbers are
   llama.cpp/other-stack builder reports; the adopting WO loads the exact quantized checkpoint
   under vLLM on the actual card and runs the lab's own canary before anything is claimed.
   License read at the checkpoint, not the family.
4. **Re-run the size preflight** with the new tokenizer and profile; adjust budgets as
   constants, never scattered.
5. **Normalizer volley:** one scripted-model pass plus the first live diagnostic run budgeted
   explicitly for answer-shape corrections (the G1-closure reliability pattern).
6. **Receipted A/B when capability claims are at stake:** the prior engine's checkpoint
   configuration is re-runnable; engine-contribution claims cite both receipts.

## 4 · Roster as of 2026-09-23 (external builder reports; re-sweep before adopting)

Constraint chain: Kaggle ARC-AGI-3 → offline → open weights, local serving → single RTX PRO
6000, 96 GB.

- **Primary candidate: Qwen3.5-122B-A10B** (122B MoE, 10B active). Fits wholly in VRAM at ~Q4;
  ~80–146 tok/s reported; 262k context; reported to lead the 120B+ open class on reasoning.
  Family continuity with the incumbent minimizes normalizer churn; low active-parameter count
  suits the turn-loop cadence.
- **Speed alternative: gpt-oss-120b** (~117B MoE, MXFP4 ≈ 63 GB). Reported 200+ tok/s on this
  card; tool-native; the pick if turn latency ever binds.
- **Ceiling, ruled out for checkpoints: MiniMax M2.7** (236B). Strongest on open indexes but
  ~17 tok/s with CPU-offload tricks — fragile under notebook deadlines.
- **Also-rans this cycle:** Mistral Small 4 (119B, native 262k), Nemotron-3 Super (120B,
  small KV cache). Cluster-scale flagships (DeepSeek V4, Kimi K3, GLM-5.3) do not fit the card.
- **Incumbent baseline: Qwen3.6-27B FP8** — retained until the current campaign's evidence
  chain closes; it is the receipted comparator for the first engine A/B.

Sources of record for this snapshot: docs.arcprize.org/arc-prize-2026 (accelerators, offline
rule); localllm.in and vaditaslim.com RTX PRO 6000 benchmark sets; modelfit.io/gpu/rtx-6000-pro;
wavect.io open-weight comparison (flagship class); thundercompute.com September 2026 roundup.

## 5 · Refresh discipline

This document versions like everything else: a new sweep produces `DESIGN_MODEL_PORTABILITY`
v(N+1) with a fresh §4 and any protocol amendments; lower versions are history in place. Cue to
refresh: any campaign boundary, any Kaggle accelerator change, or any release that plausibly
beats the current primary on this card.

## 6 · Current exact-model compatibility execution

The first application of this policy is frozen at
`kaggle/ring9-g3-qwen36-compatibility-v1/`. It holds the gate stack, worlds, budgets, and serving
profile in an execution receipt while using the incumbent `vrfai/Qwen3.6-27B-FP8` through local
vLLM. The package deliberately retains the server-default model output setting to match the Tufa
baseline; the ordinary provider adapter's newer 2,048-token default is therefore not part of this
comparison.

Notebook version 1 failed source verification before model startup because Kaggle omitted a
manifested `.DS_Store`. Version 2 excludes operating-system metadata and is in progress. This is
infrastructure evidence only until its behavioral trace is complete and reviewed. See
`INFRASTRUCTURE_G3_QWEN36_KAGGLE_CHECKPOINT_2026-09-23.md` and the immutable launch record under
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/`.

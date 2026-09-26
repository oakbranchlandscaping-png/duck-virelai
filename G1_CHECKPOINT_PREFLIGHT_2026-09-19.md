# G1 checkpoint package preflight

> **Historical package snapshot:** This file describes the package before its live attempts. The
> cancelled vc33 trace is diagnostic only, G1 remains live-unconfirmed, and the current checkpoint
> is the integrated G0-G2 notebook version 2. See
> `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`.

Date: 2026-09-19  
Package: `kaggle/ring9-g1-ego-checkpoint`  
Status: locally frozen and verified; not uploaded or executed

## Fixed execution

- Source family: `variants/ring9-cybernetic-gates`
- Benchmark: `ring9-g1-ego-checkpoint-v1`
- Worlds, in order: `vc33-5430563c`, `ft09-0d8bbf25`, `ls20-9607627b`
- Model: `vrfai/Qwen3.6-27B-FP8`
- Passes: 1
- Concurrency: 1
- Environment actions: at most 24 per world
- Runtime: at most 1,200 seconds per world
- Context: 65,536 tokens
- Model output limit: server default, explicitly recorded as such
- Tool output: 1,024 tokens
- Mode: gated
- Upload targets, if separately authorized:
  - private dataset `stephenkaskin/taaf-duck-virelai-ring9-g1-ego-checkpoint`
  - private notebook `stephenkaskin/taaf-virelai-ring9-g1-ego-checkpoint`

## Frozen identity

- Package-manifest files: 180
- Source-manifest files: 173
- Source zip entries: 164
- Package SHA-256:
  `9d4648cc8d4097fdec36d168ca9b8b9e28c6269cfe213c99ef85d75cb63b8274`
- Source-manifest SHA-256:
  `fc5d329e7d7ef1a436bdc29d438efe1866f7dfef2ae942b391c074d341664c49`

The package hash is the SHA-256 of the frozen package manifest. The source-manifest hash binds the
mounted runtime tree. The execution receipt is excluded from both manifests to avoid a digest
cycle; both local and mounted receipt copies contain these fixed hashes.

## Verification performed

- all 244 local tests pass;
- lint passes for the G1 slice files, and the changed runtime and evaluator files compile;
- all 173 source-manifest paths exist and match;
- all 180 package-manifest paths exist and match;
- direct and archived source copies agree with the source manifest;
- the execution receipt passes the H5 receipt schema and its two stored copies agree;
- the notebook compiles and contains the fail-fast receipt comparison;
- the notebook verifies direct, Kaggle-expanded `src/src/...`, and unexpanded
  `src.zip` source layouts against all 173 manifest entries;
- the serialized benchmark resolves to the fixed label, one pass, gated mode, 24 actions, 1,200
  seconds, and sequential execution;
- the packaged H1-H5 controller, evidence compiler, adaptive coverage, verifier, and evaluator
  match the selected source family byte for byte;
- the roster-derived CLICK/GOD-MODE, NAVIGATION, and HYBRID archetype is present in the
  universal ontology and G0/G1 gate views;
- an effective ACTION6 probe in a HYBRID world schedules paired post-click retests of
  ACTION1-ACTION5 channels that are present;
- no virtual environments, repository metadata, caches, or bytecode entered the mounted source;
- the bounded credential-pattern egress scan found no private-key, bearer-token, OpenAI-key, or
  Kaggle-key assignment pattern.

## Notebook fail-fast boundary

Before calling the benchmark, the notebook verifies:

1. every mounted/extracted source file against `source-manifest.json`;
2. the source-manifest hash against the receipt;
3. model id;
4. exact ordered world set;
5. pass count and concurrency;
6. gated mode;
7. action, runtime, context, model-output, and tool-output limits.

The verified receipt is copied into Kaggle working output for later H5 evaluation.

## Claim limit

This preflight establishes package integrity and configuration identity. It does not show that Duck
finds an ego, explains one correctly, or earns any G1 behavioral grade. Those claims require the
executed trace and receipt-bound frame review.

# Infrastructure record: G3 exact-Qwen Kaggle checkpoint

**Date:** 2026-09-23  
**Status:** notebook version 2 completed; infrastructure passed; behavioral review found G3 failure  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Frozen package:** `kaggle/ring9-g3-qwen36-compatibility-v1/`

## Purpose and evidence boundary

This checkpoint tests the current G0-G3 cybernetic stack with the exact local model family used
by the Tufa harness: `vrfai/Qwen3.6-27B-FP8`, served through vLLM on Kaggle. It is a compatibility
and behavioral checkpoint, not a model upgrade or score comparison. The fixed world order is
`vc33-5430563c`, `ft09-0d8bbf25`, then `ls20-9607627b`, with one sequential pass, at most 96
environment actions and 2,700 seconds per world.

Notebook version 2 is now complete. It confirms the serving and delivery infrastructure and
supplies a live vc33 diagnostic, but G3 remains unclosed. ft09 and ls20 were not exercised.

## Infrastructure added

The new packager, `tools/package_g3_qwen36_compatibility.py`, ports the proven G2 packaging
workflow and adds the current G3 source. It:

- freezes the active Ring 9 source and vendored TAAF framework into an isolated dataset;
- excludes local tests, virtual environments, run artifacts, caches, and operating-system
  metadata from source delivery;
- transports source as a verified `src.zip`, avoiding Kaggle directory/archive name collisions;
- pins the private dataset and notebook identities;
- pins the exact FP8 model snapshot and offline wheelhouse used by the Tufa configuration;
- starts a local OpenAI-compatible vLLM server with the Qwen tool and reasoning parsers;
- binds model, worlds, budgets, mode, concurrency, and source-manifest hash into an execution
  receipt checked before the benchmark begins;
- verifies source hashes before imports and refuses to run on a missing or mismatched file;
- compiles every notebook code cell and verifies package, source, and archive hashes locally.

The frozen runtime retains Tufa's model-generation profile: 65,536-token context, server-default
model output, 1,024-token tool output, thinking enabled, and concurrency one. This preserves an
exact-model baseline while the gate/controller stack changes around it.

## Active-source infrastructure carried into the package

The package contains the G2 boundary-action batching and G3 delivery hardening completed before
freeze:

- G2 can execute a bounded batch of boundary-confirmation actions through the existing action
  batch interface, reducing model-turn overhead without changing environment-action accounting;
- analyzer failures record provider rate-limit headers and error codes for diagnosis;
- the ordinary analyzer default caps output at 2,048 tokens, while this exact-Tufa receipt
  deliberately overrides it with the server default;
- the G3 model-visible entity ledger lists only frontier-bound, role-bound, and pending-
  confirmation entities, with typed omission counts;
- the complete entity/evidence store remains available in the persistent snapshot and focused
  query surface, so compaction changes delivery rather than deleting evidence.

These changes passed the complete local suite at freeze time: **323 tests**. Ruff passed for the
packager and changed controller, scheduler, compaction, and test files.

## Version 1: direct failure observation

Notebook version 1 failed in source-manifest verification before model startup. The manifest
contained `src/ARC3-Inference/.DS_Store`; Kaggle did not expose that macOS metadata file after
mounting the archive. The direct evidence supports a packaging defect only. It supplies no claim
about Qwen, Duck, G0-G3 behavior, or any ARC world.

The source export also initially contained local `runs/`, creating a 314 MB draft with thousands
of irrelevant artifacts. This was caught locally before upload. The packager now excludes
`runs/`; the frozen source archive is approximately 776 KB.

## Version 2 recovery

The packager now excludes `.DS_Store` explicitly. The corrected package passed local verification:

- 192 source-manifest entries;
- 199 package-manifest entries;
- 183 archived source files;
- package SHA-256 `9e2261157f7c0a43c83969998ac687e4707cd4c0746ece24cd91e46ada01576c`;
- source-manifest SHA-256 `3bd88c0f0d0946a2792168dbfd008d1e37b48ad409c8d60f0f8c7a8ced5163f0`.

Private dataset version 2 reported `ready` before private notebook version 2 was pushed. Notebook
version 2 completed and exported artifacts. The immutable operational record is
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/LAUNCH_RECORD.md`; version-1 output remains under
that run directory and must not be overwritten or described as a behavioral run.

The completed run exercised only vc33: local model startup plus vc33 consumed the notebook-wide
budget, leaving ft09 and ls20 at zero actions. vc33 crossed G2, passed the former G3 context-size
failure, and completed its ranked click enumeration, but pointer attribution failed for ten of 11
targets and the gate never closed. See
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/REVIEW_V2.md`.

## Review contract after completion

Retrieve the output into a new versioned subdirectory. First grade infrastructure: receipt,
manifest, model startup, world order, fixed budgets, and artifact completeness. Then grade each
world independently against its reached gates. G3 credit requires ranked targeting, retained
counter masking, persistent entity identity, scoped attribution, a separate prospective
confirmation for positive witnesses, honest null/ambiguous/boundary dispositions, and the G3
stopping rule. Score and level completion do not substitute for those products.

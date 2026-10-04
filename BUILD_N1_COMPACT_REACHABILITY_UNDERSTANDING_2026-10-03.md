# N1 build record: compact reusable reachability understanding

**Type:** `BUILD_RECORD`
**Parent:** `BUILD_PLAN_NAV_FRICTION_REPAIR_AND_G3_CLOSE_v1_2026-10-03.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-03
**Status:** built and locally validated; packaged/live validation pending

## Goal

Keep the proof that Duck understands “currently unreachable” without making a small model restate
the controller's geometry, evidence arrays and target bookkeeping for every object.

## Built behavior

The controller continues to own each target's identity, cells, closest stand, remaining gap,
reachable-stand and refused-edge counts, evidence references, conclusion and reopen conditions.
Duck supplies one compact semantic checkpoint:

- `meaning = NO_CONTACT_PATH_IN_CURRENT_MAPPED_COMPONENT`;
- `not_proven = INERT_OR_PERMANENTLY_UNREACHABLE`;
- `reopen_if = RELEVANT_REACHABILITY_INPUT_CHANGES`;
- one causal explanation of 1–40 words.

The explanation is cached by reasoning class, level, topology epoch, ego shape and bearing map.
Targets are intentionally absent from that key. A sibling target with the same key receives its
own certified row while the controller reuses Duck's already accepted understanding without a
model call. A topology or ego change produces a new key and requires a fresh explanation.

For a first-time checkpoint, the tool agent omits ordinary accumulated conversation history and
allows at most two model requests. The checkpoint exchange is not appended to later gameplay
history; its durable form is the accepted gate record and LEVEL-scoped understanding cache.

## Files changed

- `inference/framework/virelai_gates.py`: semantic key, contract, cache, topology epoch and target
  cell invalidation.
- `inference/framework/controller_executor.py`: controller-owned reuse for a matching semantic key.
- `inference/framework/life_record.py`: LEVEL persistence for cache and topology epoch.
- `inference/framework/card_builder.py`: certified compact reachability fields.
- `inference/agent/tool_agent.py`: clean bounded model turn for a first-time checkpoint.
- `tests/test_nav_branch_foundations.py`: regression, semantic reuse, length bound and key-change
  coverage.

## Validation

The focused combined suite passes **98 tests** across NAV foundations, terrain, G3 scheduling,
memory persistence, controller execution and agent tool handling. The checks prove:

- a `STILL` version increment cannot reopen unchanged target geometry;
- explanations longer than 40 words are rejected;
- a sibling target reuses the accepted understanding through the controller;
- topology and ego-shape changes alter the semantic key;
- existing controller and tool-agent behavior remains green.

This is local source validation. No package was created and no Kaggle or OpenRouter live run was
started in this checkpoint. The two-request cap is built, but the named
`G3_SEMANTIC_RETRY_EXHAUSTED` stop artifact belongs to N4 and is not yet implemented.

— **Sol**

# Build record — N5.1 bounded G3 semantic seam

**Type:** `BUILD_RECORD`
**Parent:** `REVIEW_RING9_G3_NAV_N5_LS20_V1_2026-10-04.md`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Status:** source committed and package locally validated; live confirmation pending

## Purpose

Prevent one compact G3 reachability explanation from consuming the full run, while preserving the
project's intelligence test: Duck must still express the causal meaning of the controller's
physical certificate before that meaning can be reused for sibling targets.

## Live failure addressed

The N5 ls20 run reached E0005/M0019 at action 49. The controller had already certified the target,
route exhaustion, evidence and reopen conditions, but the model repeatedly reconstructed those
facts. Seven requests reached 4,096 generated tokens, a further turn used 3,236 tokens, and the
global behavior boundary ended the run. The nominal two-request allowance belonged to one analyzer
invocation and reset whenever the solver invoked that same checkpoint again.

## Built behavior

The semantic checkpoint now has an identity derived from gate, semantic key, target entity and
target member. Its completed model-request count is written atomically to
`<game>_g3_semantic_checkpoint.json` and survives outer solver turns.

The allowance is two completed model requests across the entire bound checkpoint. When it is
exhausted without an accepted answer, the analyzer immediately returns a controlled stop and writes
`G3_SEMANTIC_RETRY_EXHAUSTED`. Solver finalization preserves this specific product instead of
overwriting it with `G3_BUDGET_STOPPED`.

The request itself is now proportional to the task:

- the card exposes the exact certified target and routing summary in a read-only subject slot;
- an answer-only instruction forbids new board, inventory, entity or evidence inspection;
- native tool use is required;
- model thinking is disabled for this checkpoint;
- output is capped at 256 tokens;
- the current-grid image is omitted because the controller certificate is the complete subject;
- Duck supplies only the semantic constants and a causal explanation of at most 40 words;
- all physical and evidential fields remain controller-certified.

An accepted first explanation still populates the N1 understanding cache. N3 remains responsible
for controller-only reuse on sibling targets with the same semantic key.

## Controlled-stop repair

The N4 product now:

- recovers the pending target from scheduler state while the gate is answer-required;
- reads latest lifecycle evidence from the full snapshot's `events` arrays;
- counts only `ELIGIBLE_TARGET` rows from the exported target ledger;
- retains the semantic-exhaustion product through solver finalization.

The ls20 failure would therefore report E0005/M0019, its latest accepted evidence, and 16 eligible
targets instead of null, null and 20.

## Files changed

- `inference/agent/tool_agent.py`: durable checkpoint identity/count, answer-only request profile,
  global exhaustion and checkpoint sidecar.
- `inference/agent/gate_artifacts.py`: accurate pending target, evidence and eligible roster fields;
  current-product loader.
- `inference/framework/card_builder.py`: certified reachability subject visible to Duck.
- `inference/framework/solver.py`: preserve a previously emitted semantic-exhaustion product.
- focused tests: cross-turn retry persistence, request payload limits, target visibility and repaired
  run-outcome fields.

## Validation

The combined NAV, G3, controller, memory, tool-agent and provider focused suite passes **112 tests**
with 14 existing dependency deprecation warnings. The complete Ring 9 source suite passes **578
tests** in 551.07 seconds with the same 14 warnings. A final seven-test seam check passes after the
image-omission refinement. Ruff passes on every changed source and test file.

The source and signed records are committed as `14f6459`. The frozen package is
`kaggle/ring9-g3-nav-n5-1-ls20-v1`, built from that exact commit with a 60-action and 700-second
boundary. Its 223-entry source manifest and 230-entry package manifest verify cleanly; the four
changed runtime files are byte-identical to the committed source. The packaged runtime passes the
59 tests that directly exercise the semantic seam and its surrounding NAV behavior. No external
run has been started.

The next live checkpoint should reuse ls20 with a short boundary. It passes when Duck accepts E0005
and the controller reuses that understanding for a sibling; if Duck cannot answer, it must stop
after at most two requests with a complete `G3_SEMANTIC_RETRY_EXHAUSTED` artifact.

— **Sol**

# Review — vc33 G4.3 OpenRouter v1

**Run:** `20260926_081816_ring9-g4-limits-vc33-openrouter-fast-rung-20260926-v1`  
**Verdict:** infrastructure failure; zero behavioral evidence  
**Model:** `qwen/qwen3.6-35b-a3b`  
**Routed provider:** Venice

## Direct observations

- The benchmark ended after 20 minutes with zero actions, zero benchmark tokens, zero levels, and
  state `cancelled`.
- The model received the G0 binding card and repeatedly stated that it needed to submit the supplied
  `gate_answer`.
- OpenRouter returned 408 completed responses from Venice: 406 with finish reason `stop` and two
  with `length`.
- None returned finish reason `tool_calls`.
- The model repeatedly rendered Python in Markdown fences. The harness correctly treated this as
  ordinary assistant text, so no `virelai('gate_answer', ...)` call executed.
- Four late requests also raised `SSLV3_ALERT_BAD_RECORD_MAC`. Those transport failures occurred
  after the no-tool loop was already established.
- Provider fallback and throughput routing were active. The previous behavioral v3 run was routed
  to AtlasCloud and returned 364 `tool_calls` finishes among 381 responses.

The artifact event file contains analyzer-loop records, not game transitions. Its nonzero line count
must not be reported as actions.

## What the evidence supports

The model understood the semantic instruction at G0 in prose. The Venice route did not produce the
native tool-call representation required by this harness under this configuration. This run proves
neither G0 closure nor any G4.3 behavior.

It does not show that the new entity-local handoff, endpoint confirmation, inverse test, or answer
validator failed. None was reached. It also does not grade vc33 gameplay.

## Repair before another game run

1. Add a provider compatibility canary that requires one native Python tool call and verifies the
   tool result before an ARC session is opened.
2. Pin behavioral runs to a provider that passes that canary; do not permit fallback to an
   unverified route during a tool-critical run.
3. Fail fast when a binding gate receives a complete analyzer turn with no parsed tool call, rather
   than allowing repeated analysis steps to consume the full world budget.
4. Rerun the same vc33 G4.3 criteria as v2. Do not change the gate semantics in response to this
   infrastructure failure.

## Relation to ft09

This failure is shared transport infrastructure and would invalidate an ft09 launch equally. The
ft09 canary remains downstream of both the provider tool-call canary and the G4.3 recurrence branch.

# Build slice R9-R11: live-readiness, one prompt instruction

**Revision label:** `R9-R11`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Base:** `3f29fd0` (R9-R10). Found while preparing the M-5 package, before anything is uploaded.

## What and why

Duck's per-turn gated instruction told it what to do with a probe or with ANSWER_REQUIRED, and
nothing about the two steps R9-R08 to R9-R10 hand to Duck:
- the orientation turn, where the card says `SUBMIT_ORIENTATION`;
- an orbit explanation. During G4-A the gate's status stays PROBE_REQUIRED while a lever awaits
  explanation, so "If status is ANSWER_REQUIRED" never fires.

Offline, the card-only Duck reads the card and does the right thing. A live model reading the old
instruction could instead press a lever again, turn after turn, and each turn costs about 36
seconds.

The instruction now adds one sentence:

> If next_operation is SUBMIT_ORIENTATION, submit `virelai('orient', notes=[...])` as the card's
> orientation block shows. When a CONTROLLER HANDOFF says why this step is yours, take that step:
> a confirmed lever run is explained with `virelai('gate_answer', ...)`, not pressed again.

## Changed

| File | Change |
|---|---|
| `inference/agent/tool_agent.py` | The sentence above, in `_build_user_prompt`'s gated instruction. |
| `tests/test_memory_m3.py` | T4 asserts that the sentence is in the message Duck is sent. The post-orientation test checks the card's `next_operation` field rather than the bare word, which the instruction now contains. |

**Suite:** cloud 469 passed, 1 skipped. No test was added or removed. **Mac expected: 470 passed.**

— Claude, Alpha build seat, 2026-09-29

# Finding: most of D7 is already measured, and a new limit appears

**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Ruling it serves:** D7 (DESIGN_VIRELAI_MEMORY_v2 §11): measure parallel throughput before setting
per-game budgets. The Director chose the combined test: model load, and several real games in one
process.
**Status:** evidence gathered from committed-era run logs and an offline probe at `8ca9fc9`. No code
changed. The D7 package is not built yet; its shape waits on this finding and on the M-5 run.

## 1 · The GPU question is answered by our own archive

Earlier rings (ring0 to ring8) ran up to 25 games at once. They used this exact server:
- the same model snapshot (`vrfai/Qwen3.6-27B-FP8`);
- the same vLLM arguments;
- a 65,536-token window;
- the same 33.66 GiB load and 43.62 GiB of KV cache.

Every run's `vllm-openai-server.log` logs throughput every 10 seconds. I pooled all 43 logs under
`runs/`. The table uses only samples taken while the KV cache was below 95% full.

| Requests running | Total output (tokens/s, median) | Per game (tokens/s) | Samples |
|---|---|---|---|
| 1 | 36 | 36 | 3,065 |
| 4 | 118 | 29 | 209 |
| 5 | 120 | 24 | 687 |
| 8 | 161 | 20 | 160 |
| 12 | 157 | 13 | 111 |
| 20 | 218 | 11 | 151 |
| 25 | 206 | 8 | 7,056 |

**In plain terms.** Going from 1 game to 8 raises total output about 4.5 times, while each game runs
at about 55% of solo speed. At 20 to 25 games the total is about 6 times solo, and each game runs at
about a quarter of solo speed.

**The ceiling is memory.** The server holds 177,968 tokens of working context. At full-window
requests that is 10.1 requests (vLLM's own startup line). Three ring-8 runs with long contexts filled
it: 1,164 samples at 95% or more. There the total fell to about 77 tokens/s, and requests queued.
So the number of games we can run is set by **how long each game's requests are**, not by speed.

**Caveats.**
- The table is built from 10-second averages, so small counts are noisy. That is why 2 games reads
  faster per game than 1.
- The request shapes came from older Duck designs.
- These are generated tokens only; prompt processing is not in the table.

## 2 · Several games in one process: correct, but the controller does not run in parallel

**Correctness.** An offline probe ran ft09 through the production agent: 6 games at once, in
threads, sharing one artifacts directory under the harness's per-game stems. Random delays forced
the games to interleave.

Every game matched a solo run exactly:
- 92 actions;
- the same Duck calls;
- the same gate answers, probe envelopes, notes and turn ledger rows.

Every file sat under its own game's stem. A static read agrees:
- no module-level mutable state;
- each sandbox runs in its own subprocess and temporary directory;
- the runtime-state temporary file is named per game.

**The new limit.** One ft09 game takes 38.8 s of controller CPU. Two at once took 81 s each, and six
at once took 256 s each. So the games queue on one core rather than running in parallel, because
Python threads share the interpreter lock. Before the controller existed, model waits of about 36 s
per action hid this cost; now it shows.

**Where the time goes** (from a profile of one game):
- About 40% is the agent re-reading and re-parsing the whole runtime-state file several times per
  controller action (`load_runtime_state`: 339 calls, each decoding every past frame). Most call
  sites keep only the current frame.
- Most of the rest is the harness rewriting that file in full after every action.

Both costs grow with game length, so the total grows with the square of the action count.

**How much it matters.** At ft09's scale the controller needs about 40 s per game. For 55 games that
is about 40 minutes of controller time that cannot overlap across games; for 200-action games it is
roughly 2 hours. That fits in a 12-hour run, but with 20 games at once it adds seconds of waiting to
every game's turn.

**Altitude: code-level.** The fix is to parse the runtime state once per turn, or read only the
current frame. That needs a diagnostic, then a failing test, then the fix. It is not built, and
M-5 runs `8ca9fc9` unchanged.

## 3 · What is still unmeasured, and so what D7 should test

1. **Request length under the memory design.** This sets how many games fit in the KV cache. The
   M-5 run's request log gives it for ft09. With the controller, a game sends no model requests for
   most of its life, so the number of requests in flight should be well below the number of games.
2. **The real Kaggle stack under concurrency.** That means taaf's `GameAPI` and the harness's thread
   pool, which the offline probe did not use.
3. **Controller CPU on Kaggle's machine,** which is not our cloud box.
4. **The competition's real runtime and game count.** These are Director-owned and come from the
   rules, not from any run.

**Proposal.** Keep the combined test, but drop the step-by-step model sweep, since the archive covers
it. Run one notebook: ft09 as N parallel passes (for example, 8) through the real harness. Grade:
- each pass against the M-5 criteria;
- identical artifacts across passes;
- peak KV use and queued requests from the vLLM log;
- controller seconds per action, taken from the turn ledger.

Pick N after M-5 reports its request sizes.

— Claude, Alpha build seat, 2026-09-29

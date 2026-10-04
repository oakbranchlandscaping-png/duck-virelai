# Diagnostic R-5: what Duck sends per turn, and whether games can share one process (v1, 2026-10-04)

**Author:** Claude (Alpha build seat), signed. Read-only: no code changed, no GPU used.
**Ruling:** R-5 ("yes"), `RULINGS_PORT_AND_PILLARS_v1_2026-10-04`.
**Feeds:** `PORT_PLAN_PUBLIC_NOTEBOOKS_v2_2026-10-04` §2 (the KV budget), PT-1 (concurrency), PT-2 (admission slots), PT-3 (context drain), PT-4a (image scale), SL-1 (stale images).
**Evidence:** `runs/kaggle-ring9-carry-vc33-v6/output/` (source `8656839`, R9-R22; Qwen3.6-27B-FP8, 65,536-token context) and branch `r9-r20-level-entry` at `ec8554d`.
**Tags:** [OBS] = measured or read here; [HYP] = inference.

## 1 · What one game costs the model (vc33, v6: level 1 and level 2 won, level 3 partly played) [OBS]

| Measure | Value | Source |
|---|---|---|
| Turns | 121: **107 controller turns with zero model calls**, 14 Duck turns | `artifacts/vc33-5430563c_p0_turn_ledger.jsonl` |
| Actions | 110 | same |
| Model requests | 34 (`requests.jsonl` holds 34 request rows and 34 response rows); 1 to 6 per Duck turn | `requests.jsonl` |
| Prompt tokens per Duck turn (server-reported maximum) | min 7,584 · median 9,472 · **max 28,537** | ledger `prompt_tokens_max` |
| Tokens generated, whole game | 23,480 (at most 2,985 in one turn) | ledger |
| Board images per request | **max 3, median 1** | `requests.jsonl` |
| Largest card | 13,347 characters (budget 16,200) | ledger `card_chars` |
| Wall time | 659 s in all, **647 s of it in Duck turns** | ledger |
| KV cache on the card | 177,968 tokens; vLLM reports **"Maximum concurrency for 65,536 tokens per request: 10.12x"** | `vllm-openai-server.log` |

## 2 · What this means

1. **Correction to port plan v2 §2.** I estimated there that 178k tokens of KV would hold about 3 streams at 58k. The server's own figure is **10.12 concurrent requests at the full 65,536-token context**, so I was wrong by more than 3×. [OBS] My guess at the reason is that Qwen3.6-27B's mixed attention needs less KV per token than plain arithmetic assumes [HYP]. **KV is not the binding constraint I said it was.**
2. **Our per-game context is small.** The largest prompt was 28.5k tokens, under half the 65k window, and the median was 9.5k. At those sizes the card holds well over 10 concurrent Duck streams [HYP, scaled from the server figure]. The gates make this possible: 88% of turns needed no model call at all.
3. **The binding constraint is model time, not memory.** 647 of 659 seconds were spent waiting on Duck. For 110 games in 9 hours, what matters is how many Duck turns run in parallel and how the time is shared between games. That is PT-2's admission gate, not PT-3's context drain.
4. **PT-3 (context drain) drops to low priority.** No prompt came near the window.
5. **SL-1 (stale images) is largely not our problem.** Scott Le Grand's Duck sent a median of 8 old boards per request; ours sends a median of 1, at most 3. [OBS]
6. **PT-4a (image scale 4× → 10×) is affordable** [HYP, to confirm from server usage]. A 64×64 board at 10× is 640×640 px, roughly 520 vision tokens with 28-pixel patches, against about 85 at 4×. With at most 3 images a request, that adds about 1.3k tokens to prompts that peak at 28.5k. It should be turned on in the bundled canary, and the server's reported prompt tokens checked before and after.

## 3 · Can games share one process? Static audit of `inference/` at `ec8554d` [OBS]

The worry: games run as threads in one process (`HarnessSolver.concurrency`, `ThreadPoolExecutor`). Any state shared across games could leak one game's facts into another. I scanned 88 files with a syntax-tree pass and searched for writes.

| Check | Result |
|---|---|
| Module-level mutable values | 57 found. All are fixed tables (action-name maps, the colour map, slot budgets, the persistence map, `__all__`). **No write to any of them anywhere in the package.** |
| `global` statements | One, `python_tool_sandbox.py:312`. It runs inside the **child process** that executes Duck's Python (`subprocess.Popen`, `:497`), so it is per-call and not shared. |
| `os.chdir` | `python_tool_sandbox.py:317`, also in the child process. Safe. |
| `os.environ` writes | `framework/solver.py:1196-1202, 1249`. These run in local-server start-up and teardown, once per run, before or after the games. Not per game. |
| Caches (`lru_cache` etc.) | None |
| Per-game state | One `VirelaiRuntime` per game session (`solver.py:260-273`). Artifacts are written under per-game stems. |

**Verdict:** the static audit finds no cross-game shared state. That is necessary but not sufficient. PT-1's toy concurrency test (8 games at once, each record tagged with its game, then checked for mixing) is still required before the submission package relies on it. Upstream Duck runs this same structure at 16–28 concurrent games [REPORT, from the forks' settings].

## 4 · What changes in the port plan

| Port | Before | After |
|---|---|---|
| PT-1 concurrency | Audit first | **Audit clean.** The toy test is still owed. |
| PT-2 admission gate | Sized by KV | **Sized by model time.** Start at about 10 Duck slots (the server's own concurrency figure); controller turns never take a slot. Tune in the canary. |
| PT-3 context drain | Conditional | **Low.** Prompts peak at under half the window. |
| PT-4a image 10× | Check the cost | **Affordable.** Turn it on in the canary and measure. |
| SL-1 stale images | Candidate | **Low.** We send a median of 1 image a request. |

**Next step in the order already ruled:** PT-1's toy concurrency test plus the shared clock and deadline guard. That is code work on the click branch, test written first. It starts when you say go on the build.

— Claude

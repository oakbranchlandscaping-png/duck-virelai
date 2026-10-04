# Port plan: what Ring 9 takes from the public notebooks (v1, 2026-10-04)

**Author:** Claude (Alpha build seat), signed. Plan only: nothing is built until the Director confirms.
**Serves:** pillar 1 of `PILLARS_PORT_AND_LEARN_TO_WIN_v1_2026-10-04`, and D-2 (submission mode) of `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04`.
**Repo:** `4c9e8ee` (`main`). Ring 9's click line is on branch `r9-r20-level-entry` (`ec8554d`, R9-R23).
**Tags:** [OBS] = read at the cited file:line; [REPORT] = an author's own claim; [HYP] = my inference.

---

## 0 · What the ports are for, and the rules

**Purpose.** Make Ring 9 play all 110 hidden games inside 9 hours on one card, wasting as little as possible, without weakening a gate. The first scored submission is due by about 12 October (D-2).

**Rules for every port:**
- **Port from the licensed source.** Franzen's code comes from his GitHub repo, not the Kaggle notebook: `tonghuikang/daniel-franzen-arc-agi-3` @ `b2fee61`, with a `LICENSE` file (Apache-2.0) and `WRITEUP.md` [OBS].
- **Transcribe, never copy.** Each ported module carries a provenance header with repo, commit, path and licence. The repo's Apache NOTICE obligations are kept.
- **Tests first.** A test that fails before the port lands, on toy fixtures or recorded runs, never on live games.
- **The firewall.** Nothing in a port may carry world content. Statistical tables fitted on another team's transcripts are not ported as constants (PT-2).
- **The gates come first.** Controller steps (G0–G4.1, zero model calls) must never wait on a port meant for model calls.

---

## 1 · What Ring 9 already has [OBS, `r9-r20-level-entry`]

| Capability | Where |
|---|---|
| Concurrent games | `inference/framework/solver.py:958`, `HarnessSolver.concurrency = 16`, `ThreadPoolExecutor` (inherited from Duck) |
| Per-game time limit | `solver.py:397-428`, `max_runtime_s_per_game` |
| Notebook soft deadline | TAAF's `soft_end_time`, in the Kaggle notebook cell |
| One Virelai runtime per game session | `solver.py:260-273` |
| Image scale as a setting | `inference/agent/vision_context.py:42-58`, `MULTIMODAL_UPSCALE`, default `4` (`framework/kaggle.py:121`) |
| Prefix caching on | `configs/inference.json`, `enable_prefix_caching: true` |

Submission mode is therefore not built from nothing. What is missing is the shared clock and deadline guard across games, admission by priority, and evidence that Ring 9's per-game state is safe under concurrency.

---

## 2 · The binding constraint: KV cache on 27B [OBS of run logs; arithmetic is HYP]

- **Ours** (carry-vc33-v2 log): the model takes 33.66 GiB, leaving about 43.6 GiB of KV cache. `PLAN_SELF_HOSTED_DEPENDENCIES_AND_MODEL_v1` records that as about 178k tokens at 0.90 utilisation.
- **Franzen's** (WRITEUP §1–2): 10 admitted streams with a 58k drain each, on a 136k server limit, with a 4-bit model. That is roughly 580k tokens of live context [REPORT].
- **So we cannot copy his concurrency.** 178k tokens holds about 3 streams at 58k, or about 10 at about 16k.
- **Our gates may be our advantage here** [HYP]. G0–G4.1 need no model calls, and the slot-built card is capped at 16,200 characters (largest observed 10,940, carry-vc33-v2 review). Our per-game context may be far smaller than Duck's.
- **Diagnostic before any context port.** From the v6 turn ledger, measure prompt tokens per Duck turn and model turns per level. That number sets the concurrency target and decides PT-3's priority.

---

## 3 · The ports, in order

### PT-1 · Submission spine: shared clock, deadline guard, concurrency evidence

- **Source:** Franzen `ARC3-Inference/inference/framework/solver.py`, `play()` (`:603-636`; soft deadline taken as the minimum of the per-game and run deadlines), and `_PriorityGate.configure_clock` (`inference/agent/tool_agent.py:2005-2016`). Apache-2.0.
- **Lands in:** Ring 9 `framework/solver.py`, extracted into a new module rather than interleaved (the ratchet).
- **Test first:**
  - 8 toy games run concurrently in the sandbox, with no gate-machine or runtime state crossing between sessions;
  - the deadline guard ends every session before the soft end.

  The test writes a game's level number into every record and checks that the sets do not mix.
- **Risk to check first:** module-level mutable state anywhere in the gate machine, memory store or runtime. A read-only audit precedes the test.
- **Exit:** a toy concurrency suite passes; the Mac floor holds.

### PT-2 · Priority admission for model calls

- **Source:** Franzen `inference/agent/priority_scheduler.py` (whole file, 134 lines at `b2fee61`) and `_PriorityGate` (`tool_agent.py:1976-~2150`). WRITEUP §3 gives the formula: the immediate gain *A* plus a continuation tail *B*, discounted by a stall factor *C*, with *B* faded over the last 20% of the run. Apache-2.0.
- **What we take:** the admission mechanism, the priority formula, the fixed "remaining levels" tail (`TAIL_LOOKUP_REMAINING`: 8/7/5/0) and the tail fade.
- **What we do not take:** `TAIL_LOOKUP_80K` and `priority_pace_reference.json`. They are fitted on his model's transcripts ("1417 reached-level episodes"). They carry no game identity, so they are not a firewall breach, but they are calibrated to another engine, and his own docstring calls them "not a contest fit". The pace starts neutral and learns from our runs.
- **Lands in:** the Duck request path only. **Controller steps never take a slot.** Only model calls queue.
- **Reads only:** public level counts and each game's own progress, as his docstring requires: "never reads hidden game metadata".
- **Test first:**
  - games with higher priority are admitted first;
  - a game in controller-only gates never blocks;
  - release and re-enqueue happen as one critical section.
- **Value [REPORT]:** the end-of-run switch was worth "8 to 12% of total score at constrained budgets" in his comment. That was measured on his stack, not ours.

### PT-3 · Context management (only if §2's diagnostic says so)

- **Source:** Franzen `tool_agent.py:207-270` (drain hysteresis, the turn-cap drain, coalescing); token estimation calibrated against backend usage (WRITEUP §2); prefix-stable ordering. Apache-2.0.
- **Why it might not matter:** our prompt is already layered stable-to-volatile (`CYBERNETIC_TARGET_TREE_v1` §9: ontology, mission, then a volatile GoalCard), which is the prefix-friendly shape. Measure before porting.

### PT-4 · Perception for Duck's turns

| Item | Source | Cost | Note |
|---|---|---|---|
| **4a. Image scale 4× → 10×** | Franzen WRITEUP §4: "the biggest score improvement in terms of images" [REPORT] | One setting (`MULTIMODAL_UPSCALE=10`) | Costs image tokens. Check against §2's budget before turning it on. |
| 4b. Animation frames available to Duck | Franzen `utils/animation.py` (333 lines); Lord Han Solo `agent/animation.py` | Port | Check first what Ring 9 already exposes. Our win capsule handles the layers. |
| 4c. `frame_diff()` helper: matched objects (moved, rotated, appeared) | Franzen `utils/frame_diff.py` (307 lines) | Port | Offered to Duck as a tool. It does not replace the gate's own attribution. |
| 4d. Game-over frame and diff images | Franzen `agent/vision_context.py` | Port | Fits the life record (R9-R16): the death frame is evidence |
| 4e. Clearer follow-up messages for game over and level change | Franzen WRITEUP §5 | Prompt text | Check against Ring 9's card, which already states lives and level changes |

### PT-5 · Action-waste guards (blocked on a ruling)

- **Source:** Franzen `agent/noop_repeat_guard.py` (178 lines), and the batch no-op, stale-state and terminal guards (WRITEUP §5).
- **Our improvement:** his "interior unchanged" signal uses a fixed 4-cell border. Where G2 has certified the counter mask, the guard uses our mask instead.
- **Where it matters:** Duck's free-play turns (§4), where waste is unchecked.
- **Blocked on:** ruling R-1, the action channel during guided gates.

### PT-6 · Retained functions

- **Source:** Franzen `utils/retained_functions.py`. Model-defined helper functions survive across tool calls, which saves regeneration.
- **Value:** cheap, and it helps Duck in free play. Check first whether it conflicts with Ring 9's sandbox.

### PT-7 · Pillar 2 machinery

JustAdev742 `arc3/dsl.py` @ `8b8a728` (Apache-2.0): goal relations, lift, falsification (P1–P3 in the pillars document). It is a separate track that needs no GPU, and it does not block the submission.

---

## 4 · The question submission mode forces (architecture; for the Director and CE)

Across 110 games, many will not be gate-closable inside a slice: worlds that need NAV before the NAV line merges, or ladders that stop at G3 or G4. D-2 says such games "are still played within their time slice". **What does Duck do there?**

| Option | Score | Cleanliness |
|---|---|---|
| **(a) Gated only.** When the ladder rests, the game ends declared. | Lowest | Purest |
| **(b) Free play after the ladder rests.** Duck plays Franzen-style with PT-4, PT-5 and PT-6, still under the gate's audit and records. | Higher | Mixed. Each game's receipt states GATED or FREE_PLAY. |

**Recommendation: (b), with per-game receipts.** Paper and prereg claims cite gated games only. The leaderboard number is reported as "gates where they apply, free play elsewhere". No gate is weakened: free play begins only where the ladder has rested.

---

## 5 · Not ported, with reasons

- **The serving stack** (Pennyroyal SGLang, the 4-bit Flash-Next model and its drafter): it is the D-3 swap window's business (13–24 October), not this plan's.
- **`TAAF_MINIMAL`-style memory off:** nothing to port. Ring 9 replaces the upstream text world model with controller-certified products.
- **Fitted priority tables:** see PT-2.
- **JustAdev742 lesson 0016 priors:** derived from game source code.
- **Undo (ACTION7) exposure:** Franzen enabled it (WRITEUP §5). For Ring 9 this is a G0 action-surface question, not a port. It is noted for the gate owner.

---

## 6 · Exposure declaration (prereg integrity)

Franzen's `WRITEUP.md` §5 gives a one-line mechanic description of **`su15`**, one of prereg v2's three held-out worlds. I read it while scanning the write-up for measured feature values. The held-out set is supposed to be unseen by the build team. **Recommend:** replace `su15` in a prereg v3, chosen from worlds none of the mined material describes, or record the exposure in the prereg and weaken its claim accordingly. Ruling R-4.

---

## 7 · Order and calendar to the first submission (~12 October)

| Step | When | GPU |
|---|---|---|
| §2 diagnostic (tokens per Duck turn, from v6) | first | none |
| PT-1 audit, tests and port | 4–6 Oct | none |
| PT-2 | 6–8 Oct | none |
| PT-4a, 4b, 4d (and PT-3 only if §2 says so) | 7–9 Oct | none |
| **One bundled canary:** a multi-game dry run of submission mode inside the 9-hour guard; the Director runs it | ~9–10 Oct | ~one run (D-5) |
| First scored submission | ~11–12 Oct | submission |
| PT-5, PT-6, PT-4c | after the rulings; before the D-8 decision | with the swap canary |
| PT-7 (pillar 2) | alongside throughout | none |

Ports touching `tool_agent.py` or `solver.py` touch files shared with the NAV line (`1478d7d` lists four shared files). Each such port is announced in the documentation index before it lands, so Sol is not surprised by it.

---

## 8 · Rulings owed (Director)

1. **R-1. The action channel during guided gates:** Duck's batched snippets, under the guards and the gate's audit, or the gate's capability token. This unblocks PT-5.
2. **R-2. Free play after the ladder rests** (§4): (a) or (b). (b) is recommended, with per-game receipts.
3. **R-3. Branch:** ports land on `r9-r20-level-entry` (the click line, where the submission package is built), with the merge decision you already owe.
4. **R-4. `su15`:** replace it in a prereg v3 (recommended), or record the exposure.
5. **R-5. Go:** confirm the order in §7, and I start with the §2 diagnostic and the PT-1 audit (both read-only).

— Claude

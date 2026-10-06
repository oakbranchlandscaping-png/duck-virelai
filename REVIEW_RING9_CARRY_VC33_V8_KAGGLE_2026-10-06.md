# Review: ring9-carry-vc33-v8 on Kaggle (R9-R24, G4 controller-first)

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat), signed
**Package:** `kaggle/ring9-carry-vc33-v8`, source `c9b246b` (the click line before the merge)
**Graded against:** `UPLOAD_STATUS_RING9_CARRY_VC33_V8_2026-10-05.md` (I14–I16 and the carried criteria)
**Output:** `runs/kaggle-ring9-carry-vc33-v8/output` (downloaded by the Director, 2026-10-06)
**Method:** read from artifact state, not prose: the probe envelopes, gate events, gate answers, turn ledger, kernel log and execution receipt. Actions were compared one by one with the v7 record fixture. Nothing was rerun.

## 0 · In one paragraph

R9-R24 did what it was built to do. The G4 stretch on level 3, from G4-B opening to normal play, took **136 seconds**; v7 spent about 163 minutes there.
- The controller certified G4-B from the record three times, with no Duck turn.
- Duck used exactly its 3-turn budget.
- G4-C closed `UNRESOLVED (Duck budget spent)`, and the level passed to `PLAY-NORMAL`.
- The run ended on its 200-action budget after **47.5 minutes** of behaviour time. The notebook took about 57 minutes, about 0.94 GPU-hours against v7's 3.25.

The score is unchanged: **1.51, 2 of 7 levels**. Levels 1 and 2 cleared as in v7. Duck then played level 3 for 56 actions without winning it.

The time sink is gone. What limits the score now is that nothing aims at the win (friction F3).

## 1 · Grades

| Criterion | Grade | Evidence |
|---|---|---|
| Setup | **PASS** | Log: `source manifest verified (224 files)`; Python 3.12 paths; the wheelhouse installed; vLLM serving `vrfai/Qwen3.6-27B-FP8` from `stephenkaskin/virelai-qwen3-6-27b-fp8`; receipt verified; controller executor on. |
| I2: receipt | **PASS** | The downloaded `execution_receipt.json` is identical to the package's. |
| I5, I8: dependencies and image | **PASS** | The Director's own datasets, Python 3.12, `vllm-0.19.0` installed. |
| I6: comparability | **PASS, strongly** | v8's first **143 actions are identical to v7's**, including Duck's only pre-G4 action, the G3 turn at t108. The first divergence is t144, v8's first `PLAY-NORMAL` action, where v7 was in G4-B/G4-C. Same controller and same world, and here the same Duck choice. |
| I12: G3 partial close | **PASS** (as in v7) | Level 3's `LEVER_INVENTORY` is the controller's, closure PARTIAL: 7 levers (E0010–E0013, E0015–E0017), `ambiguous_entities: ["E0028"]`. Levels 1 and 2 are COMPLETE with 2 and 4 levers. |
| **I14: G4-B from the record** | **PASS** | Three `LEVER_RELATIONS_FROM_RECORD` answers, executor CONTROLLER (`G4B-REC-c9b61326…`, `…a80c0e85…`, `…be0f5bc7…`): the first certification and one after each reopening by G4-C. No card row reads `UNRECORDED` (no occurrence in the transcript). |
| **I15: Duck's G4 budget** | **PASS** | Duck took 3 G4 turns on level 3: 2 at G4-C (LAW_PREDICTION; 24 s and 29 s) and 1 at G4-B (LEVER_PREDICTION; 32 s). Then: "Duck's G4-B/G4-C budget for this level is spent (3 turns); G4-C-LEVER-LAW closes UNRESOLVED", recorded as `UNRESOLVED (Duck budget spent) · 2 tests, 2 reopenings of G4-B`. No reopen loop followed. **G4-B opening to PLAY-NORMAL: 136 s** (v7: about 163 min). |
| **I16: normal play** | **PASS** | `PLAY-NORMAL` from t144 to t200: 57 actions, 56 gate events receipted `FREE_PLAY`. 6 refusals carried "Blocked by the harness, not the game". The run ended on the action budget (200), not on a planned stop. Level 3 was **not won**. |
| I11: no idle GPU | **PASS** | The run ended at about 3,384 s of notebook time; the notebook ended at 3,395 s. |
| Score | — | 1.51, 2/7 levels, 200 actions, 93,378 tokens (`summary.txt`). The same score as v7. |

## 2 · Findings

### F-v8-1 · A budget wake pre-empted the controller at G4-B. The click line's old wake rule; the single tree fixes it.

**What happened.** After G4-C's second reopening, the controller had re-certified G4-B. Then the counter wake ("the budget is nearly spent: 2 counter ticks left") handed Duck a G4-B turn, so Duck froze a `LEVER_PREDICTION`. The record could have answered that step. Duck's third budget turn was spent there instead of on a third law test.

**Why.** It is the wake rule at `c9b246b`: a wake goes to Duck before the controller computes its step. On the single tree, `main`'s ownership law delivers a wake only when Duck owns the next step (finding F4 of the unification review, confirmed by Sol). There the controller would have taken G4-B itself.

**Next.** The unified vc33 canary (`232a502`) is the live test of this.

### F-v8-2 · The time sink is gone; play does not aim at the win

**The play phase:**
- 22 Duck turns, 1,553 s, 48,175 generated tokens.
- 21 of the 22 turns were cut off by the turn clock.
- Of the 56 recorded actions, 16 changed nothing outside the counter, and 6 more were refused by the harness.
- Only 9 distinct sites were clicked: mostly E0016 (12) and E0017 (10), then the other levers.
- No level-3 win.

**What it means.** The card gave Duck the certified relations: shared regions {E0010=E0011} and {E0012=E0013}; a mutual group {E0015, E0016, E0017, {E0012=E0013}}; one-way reach {E0012=E0013}→{E0010=E0011}. Duck explored with them. It didn't plan toward a goal state, and nothing in the ladder offers one.

**This is now the binding limit on the score.** It is evidence for putting the learn-to-win work (W-series, `ACT_ON_GOAL`) ahead of more ladder refinement. That is the Director's ordering call.

### F-v8-3 · Prompts in play come within 8k tokens of the context window

**The numbers.**
- The largest prompt in a play turn was **57,193 tokens**, against the 65,536-token window.
- The packaged request pre-flight (T10) bounds one request at 33,158 tokens. In free play, one turn makes up to 4 requests, and the conversation grows with each.
- Nothing overflowed, but the margin is about 13%.

**The risk.** It matters for longer play, and for submission mode, where play is most of the time.

**What fixes it.** It's code-level: cap requests per play turn, or trim earlier tool output within a turn. It belongs with submission mode (my step 4″).

### F-v8-4 · Level 3's first life ends before play begins

**What happened.**
- Both v7 and v8 hit `GAME_OVER` at t144. The study (G3 and G4-A) uses up level 3's move counter for life 1.
- So play on level 3 effectively starts in life 2, on a fresh board.
- The first play press (t144) was spent on the death transition.

**Under the single tree.** First-witness G3 saves about one action per lever, so life 1 may last longer. The unified canary will show it.

## 3 · What this means for the plan

- **R9-R24 is validated live on its own terms:** G4 now takes minutes, the budget holds, and play follows. The single tree carries the same G4 code, so this carries over.
- **The unified vc33 canary now has a clean baseline.** v8's actions up to t143 equal v7's, and t144 onward is play. Any difference in the canary before play comes from first-witness G3 or from the ownership law (F-v8-1), and can be named exactly.
- **For the submission (step 4″):** F-v8-3's prompt growth and the per-turn clock in play are inputs to the per-game slice.

— Claude, Alpha build seat, 2026-10-06

# Directive: the competition endgame (R2 and R3), to 2 November 2026

**Type:** `DIRECTIVE_COMPETITION_ENDGAME` · **v1** · **2026-10-03**
**Status:** **RATIFIED by the Director, 2026-10-03.** It binds every seat working in this repo: the Ring 9 build seat (Claude), the NAV seat (Sol), and anyone who picks up the work.
**Author:** Claude (Alpha build seat), signed.
**Settles:**
- **R2**, the model sequence, and **R3**, the GPU quota and time budget, from `PLAN_SELF_HOSTED_DEPENDENCIES_AND_MODEL_v1_2026-10-01.md` §5;
- the run-window question raised in `REVIEW_RING9_CARRY_VC33_V5_KAGGLE_2026-10-03.md`.

**Supersedes:** the README's original target, ARC-AGI-3 Milestone #2 (30 September). The lab did not submit to Milestone #2 (Director decision, 29 September).
**Versioning:** highest version wins. A change is a v2 with a dated reason, never an edit in place.

## 1 · The directives

**D-1. The goal through 8 November is a paper, and the paper needs a scored submission.**
- The ARC Prize 2026 Paper Prize accepts only papers linked to a Kaggle code submission in the ARC-AGI-2 or ARC-AGI-3 track.
- So a valid, scored ARC-AGI-3 submission is a hard requirement, not an optional extra. The score itself matters only as the paper's "accuracy" criterion, one of six.

**D-2. The submission track starts now, in parallel with the evidence work.**
- The first scored submission is due by about **12 October**. Any score is acceptable: its purpose is to prove the machinery.
- A submission must:
  - play all hidden games (110 by the sources in §2) inside the 9-hour run;
  - slice time per game, or run games concurrently;
  - hold a hard guard on the run's deadline, because a run that overruns produces no scorecard and fails.
- The current Ring 9 packages play one world at a time, so this is new engineering.
- A submission mode must never weaken a gate. Games the ladder cannot reach are still played within their time slice.

**D-3. R2: keep the current model through 2 November.**
- The model stays `vrfai/Qwen3.6-27B-FP8`, self-hosted as `stephenkaskin/virelai-qwen3-6-27b-fp8`, with the same serving and wheelhouse.
- No model swap: it costs a mirror upload plus a dry run, and it brings weaker tool calling (§2). It also serves leaderboard accuracy, which is not the lab's claim.
- The lab's claim is that the gates lift a small model (`PREREG_SMALL_MODEL_GLASS_ENGINE_v2`).
- Revisit only if the Director reopens R2.

**D-4. R3: the calendar.**

| Window | Work |
|---|---|
| 3–12 Oct | `ring9-carry-vc33-v6` (R9-R22, G4 typing on all four level-2 levers). Build submission mode. **First scored submission.** |
| 13–26 Oct | Evidence runs for the paper: learn to win on vc33's recorded win, G4 typing on a second world, the level learning curve (PREREG H0). One submission a week as the build improves. |
| 27–30 Oct | **Code freeze.** Final submission, with 2–3 days of slack before 2 November. |
| 31 Oct–8 Nov | Write the paper, linked to the final submission. |

**D-5. R3: the GPU budget.**
- At about 30 GPU-hours a week, the month holds roughly 6–8 three-hour evidence runs plus the submissions.
- **The quota is one account shared by every seat.** Ring 9 evidence runs and the NAV seat's checkpoints draw on the same hours.
- Each seat states a run's expected GPU-hours in its upload record before pushing.
- When the week's remaining quota falls below one evidence run plus one submission, submissions take priority.

**D-6. Run windows stay at the full 3 hours.**
- R9-R22's general A2 rule ends a stalled gate within three watchdog checks, so idle stalls no longer burn the window.
- A full window therefore costs GPU time only while the run is doing work. The 200-action cap guards against legal but useless activity.
- No run is shortened to save quota. If quota is short, a run is deferred instead.
- *Unverified:* that an early end also ends the notebook and its GPU clock. The first run after R9-R22 must confirm this from its own timings.

**D-7. One run is one sample.**
- Published Duck repetitions show large per-game variance: one game scored from 0 to 47.6 across 25 passes.
- No paper claim rests on a single run. Claims cite the run count, and say "observed once" when that is all there is.

## 2 · The facts these rest on (swept 2026-10-03)

| Fact | Value | Source quality |
|---|---|---|
| Final submissions | **2 Nov 2026**; papers 8 Nov; results 4 Dec | ARC Prize, primary |
| Paper Prize | $50K / $20K / $5K, plus a $375K pool for papers scoring above 4.5 of 5 on six criteria (accuracy, universality, progress, theory, completeness, novelty) | ARC Prize, primary |
| Top-score prizes | $40K / $15K / $10K / $5K / $5K | ARC Prize, primary |
| Submission run | 9 hours, one 96 GB Blackwell GPU, no internet, 110 hidden games | Two competitor repos agree; 55 + 55 in the ARC-AGI-3 paper |
| Scoring | Per level, (human actions ÷ agent actions)², capped. A game's score weights later levels more (level n weighs n). | ARC Prize docs, primary |
| Leaderboard | Top about 28% (28.34%, a new first place); a Duck-based Milestone #2 entry scored 27.89 with a larger model, ten concurrent games, and a priority scheduler | ARC Prize post (search snippet); the entry's write-up |
| Larger model on one card | Fits with host-RAM offload; tool-call reliability 87.9 vs 91.0 for the 27B class, and its forced tool-call mode failed every attempt | One public benchmark |

**Still to verify on Kaggle:**
1. The exact deadline time: `kaggle competitions list -s "arc-prize-2026"`.
2. Submissions per day: sources say 1 and 5.
3. The RTX PRO 6000 quota and its weekly reset.
4. Whether submission reruns count against the quota.

Each answer is filed as a dated note under this directive. If an answer changes D-4 or D-5, it becomes a v2.

**Sources:**
- [ARC Prize 2026 dates](https://arcprize.org/competitions/2026)
- [Paper Prize](https://arcprize.org/competitions/2026/paper)
- [ARC-AGI-3 prizes](https://arcprize.org/competitions/2026/arc-agi-3)
- [Scoring methodology](https://docs.arcprize.org/methodology.md)
- [ARC-AGI-3 paper](https://arxiv.org/html/2603.24621v1)
- [9 h, 110 games, 1/day](https://github.com/anandsingh8687/arc-prize-2026-arc-agi-3-agent)
- [5/day](https://github.com/SungsuHyun/arc-prize-2026-arc-agi-3)
- [Milestone #2 Duck write-up](https://github.com/1zuki/arc-agi-3-solution/blob/main/WRITEUP.md)
- [Duck variance lab](https://github.com/sonpham-org/arc-3)
- [Larger model on one RTX PRO 6000](https://github.com/MarcoPizeta/flash-next-rtxpro6000-bench)

## 3 · Why (the reasoning, kept short)

**The paper is the lab's aim, and Kaggle gates it.** Starting the submission work in the last week is how a paper loses its entry.

**The scoring formula is the paper's argument in numbers.**
- Squared efficiency punishes probing within a level, but later levels weigh more: in a 6-level game, level 6 carries 6/21 of the score and level 1 carries 1/21.
- Study bought on early levels has to pay on the heavy ones. That is PREREG H0.
- The carry result (4/4 levers reconfirmed on level 2, reproduced twice) is its first live evidence.

**A model swap spends the scarcest thing,** calendar days, on the criterion the lab claims least.

— Claude, Alpha build seat, 2026-10-03. Ratified by the Director, 2026-10-03.

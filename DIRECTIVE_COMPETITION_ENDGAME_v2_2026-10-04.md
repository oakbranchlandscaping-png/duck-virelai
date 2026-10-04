# Directive: the competition endgame (R2 and R3), to 2 November 2026

**Type:** `DIRECTIVE_COMPETITION_ENDGAME` · **v2** · **2026-10-04**
**Status:** **RATIFIED by the Director, 2026-10-04** ("yes. lets update and ratify this plan so all collaborators are on the same page"). It binds every seat working in this repo: the Ring 9 build seat (Claude), the NAV seat (Sol), and anyone who picks up the work.
**Author:** Claude (Alpha build seat), signed.
**Supersedes:** `DIRECTIVE_COMPETITION_ENDGAME_v1_2026-10-03.md`. v1 stays in place as history.
**Versioning:** highest version wins. A change is a new version with a dated reason, never an edit in place.

## 0 · What changed from v1, and why (dated reason, 2026-10-04)

**R2 is reopened for the final submission only.** The Director, 2026-10-04: *"the score is not the final goal, but it seems like we do ourselves a disservice not to use the most advanced model allowed and available for final submission."* This restores the standing policy of `DESIGN_MODEL_PORTABILITY_v1_2026-09-23` ("the engine is a plug, and we always run the best legal one"), which v1's D-3 had narrowed for calendar reasons.

What changes:
- **D-3** is amended. 27B stays through the first scored submission. A model swap window opens afterwards, and a switch rule fixed now decides the final submission's model.
- **D-4**'s calendar gains the swap window.
- **D-8** (new) is the switch rule.
- **§2** corrects a fact: the leading Flash-Next model **does** run on one card.

D-1, D-2, D-5, D-6 and D-7 are unchanged and are restated below so that this document stands alone.

## 1 · The directives

**D-1. The goal through 8 November is a paper, and the paper needs a scored submission.** *(unchanged)*
- The ARC Prize 2026 Paper Prize accepts only papers linked to a Kaggle code submission in the ARC-AGI-2 or ARC-AGI-3 track.
- A valid, scored ARC-AGI-3 submission is therefore a hard requirement. The score matters as the paper's "accuracy" criterion, one of six.

**D-2. The submission track runs in parallel with the evidence work.** *(unchanged)*
- First scored submission by about **12 October**. Any score is acceptable; its purpose is to prove the machinery.
- A submission must play all hidden games (110) inside the 9-hour run, slice time per game or run games concurrently, and hold a hard guard on the run's deadline.
- A submission mode must never weaken a gate. Games the ladder cannot reach are still played within their time slice.

**D-3. R2, amended: the current model through the first submission; the best legal model for the final one, if it earns it.**
- **Through the first scored submission (~12 October):** the model stays `vrfai/Qwen3.6-27B-FP8`, self-hosted as `stephenkaskin/virelai-qwen3-6-27b-fp8`, with the same serving and wheelhouse. No swap before then.
- **Swap window, 13–24 October:** bring up the strongest legal model through the swap protocol of `DESIGN_MODEL_PORTABILITY_v1` §3:
  1. re-sweep the candidates at decision time;
  2. load the exact checkpoint under the real serving stack on the RTX PRO 6000, and read its licence at the checkpoint;
  3. re-run the size preflight with the new tokenizer;
  4. one answer-shape clean-up round;
  5. the canary.
- **Candidates, in order of cost:**
  - **A. Qwen3.8-27B-FP8.** The drop-in: same weight class, and probably the same vLLM. Cost: mirror one model and change one record.
  - **B. Qwen3.8-Flash-Next at 4-bit.** What the leading public entries run (§2). Cost: a different serving runtime (a new offline wheelhouse and its dry run) and a larger answer-shape clean-up. A few days.
  - Others from the re-sweep, under the same protocol.
- **The final submission uses the new model only if it passes D-8.** Otherwise it stays on 27B, and the reason is recorded.
- **The lab's claim is unchanged.** The gates lift a small model (`PREREG_SMALL_MODEL_GLASS_ENGINE_v2`), so prereg comparisons run at a **fixed model**. Gates-on-27B versus gates-on-the-new-model is reported as the engine-versus-gate measurement the portability design promises, never as gate evidence.

**D-4. R3: the calendar (amended).**

| Window | Work |
|---|---|
| 3–12 Oct | Build submission mode. **First scored submission, on Qwen3.6-27B.** Learn-to-win steps LW-1 to LW-3 (no GPU; `PILLARS_PORT_AND_LEARN_TO_WIN_v1_2026-10-04`). Tier-A ports for the 110-game run (the port plan). |
| 13–24 Oct | **Model swap window** (D-3, D-8), alongside the evidence runs: the learn-to-win level-3 canary (LW-4), G4 typing on a second world, the level learning curve (PREREG H0). One submission a week as the build improves. |
| 25–26 Oct | **D-8 decision:** the final submission's model, recorded with its evidence. |
| 27–30 Oct | **Code freeze.** Final submission, with 2–3 days of slack before 2 November. |
| 31 Oct–8 Nov | Write the paper, linked to the final submission. |

**D-5. R3: the GPU budget.** *(unchanged)*
- About 30 GPU-hours a week, **one account shared by every seat.** The swap-window dry runs and canaries draw on the same hours.
- Each seat states a run's expected GPU-hours in its upload record before pushing.
- When the week's remaining quota falls below one evidence run plus one submission, submissions take priority.

**D-6. Run windows stay at the full 3 hours.** *(unchanged)* R9-R22's general A2 rule ends stalled gates. No run is shortened to save quota; if quota is short, a run is deferred. *Unverified:* that an early end also ends the notebook's GPU clock.

**D-7. One run is one sample.** *(unchanged)* No paper claim rests on a single run. Claims cite the run count, and say "observed once" when that is all there is.

**D-8. The switch rule (new; fixed before any swap result exists).**

The final submission switches to the new model **only if** its canary, run on the same package and world as the current 27B baseline (vc33, the carry package), meets **all** of the following:
1. **The gates hold:** G0 to G4.1 close with zero model calls, as on 27B; the level freeze and the carry fire as on 27B.
2. **Duck's answers are admitted at least as reliably:** accepted answers per Duck turn and tool-call failures, from the turn ledger, no worse than the 27B baseline.
3. **Reach:** vc33 reaches at least the same level as the 27B baseline within the same budget.
4. **Submission fit:** a dry run of the submission mode on the new model completes inside the 9-hour guard.

If any criterion fails, the final submission stays on 27B and the failure is recorded. A pass is recorded as "observed once" (D-7), unless repeats were run.

## 2 · Facts (v1's table stands, with one correction)

v1 §2 stands, including the four Kaggle facts still to verify (deadline time, submissions per day, RTX PRO 6000 quota, whether reruns count).

**Correction (2026-10-04).** `PLAN_SELF_HOSTED_DEPENDENCIES_AND_MODEL_v1_2026-10-01` §5 lists Qwen3.8-Flash-Next under "C. Doesn't fit one card". **Public evidence contradicts that.** [direct observation of pulled notebook metadata, `recon_m2/`]
- **Franzen's Milestone 2 solution** serves `dfranzen/intel-qwen3.8-flash-next-w4a16-autoround` (Intel AutoRound, W4A16) with the drafter `dfranzen/albucino-qwen3-8-flash-next-drafter` on one RTX PRO 6000.
- **wuliao0's and lucifer19's forks** serve `keithtyser/qwen3-8-flash-next-nvfp4` (ModelOpt NVFP4) on a pinned vLLM runtime (`keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1`).
- **Lord Han Solo** serves `lordhansolo/qwen3-8-flash-next-mixed-nvfp4-fp8` on `lordhansolo/vllm-main-e975732-arc3`.

v1's caution still applies to this class: a public benchmark measured tool-call reliability of 87.9 against 91.0 for the 27B class, and its forced tool-call mode failed every attempt. D-8 criterion 2 exists for exactly that risk.

Weight licences for these checkpoints are not yet read. Reading them is a protocol step (D-3, step 2), not an assumption. The FP8 checkpoint (173 GiB) still does not fit; the 4-bit ones do.

## 3 · Why (the reasoning, kept short)

**The paper is the lab's aim, and Kaggle gates it.** The first scored submission stays on the proven model so the paper's entry is never at risk.

**The final submission should carry the best engine the gates can use.** The portability design treats the model as a plug, and the swap protocol makes the change measurable rather than a leap of faith. D-8 is written before the evidence so that the decision cannot bend to it.

**The comparison stays clean.** Prereg claims run at a fixed model. The second engine yields the engine-versus-gate measurement, which answers the first question a reviewer will ask when they see the leaderboard.

— Claude, Alpha build seat, 2026-10-04. Ratified by the Director, 2026-10-04.

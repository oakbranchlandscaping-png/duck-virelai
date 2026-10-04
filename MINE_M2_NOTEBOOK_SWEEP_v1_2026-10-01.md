# MINE — Milestone 2 Notebook Sweep, Tranche 1 (v1, 2026-10-01)

Author: Claude (Alpha builder, Cybernetic Duck). Read-only recon. Nothing submitted, nothing ported yet.
Sources: 11 Kaggle kernels pulled by the Director 2026-10-01 into `virelai-review/recon_m2/`.
Tags: [OBS] = I read it in the pulled source; [REPORT] = the author's own claim; [HYP] = my inference.

## 0 · Headline

None of the 11 kernels enforces a gated or ordered sub-question structure in code. Where our ideas show up, they show up as prompt advice appended to the Duck system prompt. The gated bet is not falsified by this tranche. One kernel (`cognitive-rungs`, April 2026) converges crudely on "observe the win, then carry it", and it is the prior art to cite for H0. One kernel (`lucifer19`) supplies the single most useful number for our prereg: the same code scored 9.91 and 6.43 offline. [OBS of their notebook text; the numbers themselves are REPORT]

## 1 · Per-kernel record

| # | Kernel | What it actually is | Licence | Verdict |
|---|---|---|---|---|
| 1 | `lordhansolo/arc-agi-3-milestone-2` | Stock TAAF launcher [OBS]. The solver is in dataset `lordhansolo/taaf-kaggle-source`, not pulled yet. GitHub `LordHansolo` has no ARC repos [OBS]. | unknown until the dataset is read | **PENDING**: pull the dataset |
| 2 | `jthomaslockhart/...-lean-baseline` | CPU-only, no-LLM effect-model and graph explorer. Adapted from Shlok Sah's FrugalExplorer, rev `7dccef1` [OBS]. Makes no performance claim [REPORT]. | MIT-0 (both layers) [OBS] | **PORT candidate** (see §2) |
| 3 | `jessky/arc3-franzen-milestone-2-fork` | Franzen verbatim, plus a resolver that handles both Kaggle wheelhouse mount layouts [OBS, by diff]. | Apache-2.0 (inherits) | Defensive port only; low priority |
| 4 | `wuliao0/duck-qwen3-8-anim-base` | Serving-only fork. Duck prompts and policy unchanged [REPORT]; the customisation cell only sets budgets [OBS]. The "anim" behaviour lives in the attached `keithtyser` datasets. | Duck (MIT) | No port. It is the common ancestor for diffs. |
| 5 | `huikang/milestone-1-4th-place` | Uniform-random brute agent with click priors, routed by a seed tree loaded from a private "secrets" dataset [OBS]. In effect this tunes seeds against the hidden set. [HYP] | none stated | No port. Record it as a pattern that works around the benchmark. |
| 6 | `thezetaproject/cognitive-rungs` | No LLM. A bank of hand-written rule templates (toggle, gravity, mirror, rotation, sort…), a GF(2) toggle solver, a CNN frame predictor, a cross-game "SharedTheoryBoard", and `extract_win_condition(initial, solved)` [OBS]. "Rungs" is a name only: there is no gated ordering in `select_action` [OBS of `GameContext`/`MyAgent`]. A "tempo" controller sends unavailable actions as no-ops [OBS]. | none stated | No port (no licence). **Cite as prior art for H0** (§3). |
| 7 | `obirdy/...verified-world-model-gpu-v1` | Released Duck plus a prompt addendum asking the model to build a transition function and replay it against the recorded transitions [OBS]. | Duck (MIT) | No port. **Evidence for C-enforcement** (§3). |
| 8 | `obirdy/...state-ledger-gpu-jul26-a2` | #7 plus an "evidence ledger" addendum: classify each result as SCORE_OR_LEVEL / GAMEPLAY_CHANGE / HUD_ONLY / NO_CHANGE, track tried state-action edges, and fall back to systematic search after 8 unproductive actions [OBS]. **This is our G2 and G3 written as advice.** | Duck (MIT) | No port. **Evidence for C-enforcement.** |
| 9 | `lucifer19/duck-qwen3-8-search-memory-c18` | Serving swap plus a one-line efficiency directive appended to the system prompt. "Search memory" is a title only [OBS]. Reports the same code scoring 9.91 vs 6.43 offline, C18 2.70 vs C17 7.11, and C17 public 2.84 [REPORT]. | Duck (MIT) | No port. **Variance datum for the prereg** (§4). |
| 10 | `avikdas567/...neural-world-models...` | Long academic prose plus an online residual CNN transition model [OBS of section headings]. | none read | No port. Cite only as the opaque world-model contrast. |
| 11 | `karnakbaevarthur/...logic-explanations` | A **human-written answer key** of per-level mechanics for public games [OBS]. 5 task rows; none of `lp85`, `s5i5`, `su15`, `vc33`, `ft09` appear (counted by grep for the IDs, contents not printed) [OBS]. | none stated | **QUARANTINE.** It must never be loaded into any arm. Exposure declared: I incidentally read the first two rows (`ls20`, `ar25`), and neither is a prereg world. |

## 2 · Port register (seed rows)

| ID | Component | Source @ rev | Licence | Gate served | Evidence | Status |
|---|---|---|---|---|---|---|
| PR-01 | `frame_delta` class: unchanged / sparse / local / global / resize, with bbox | Lockhart lean (notebook cell 2) ← FrugalExplorer `7dccef1` | MIT-0 | G2 / G4 delta typing | [OBS] code read; no score evidence | CANDIDATE. Compare against our existing delta typing before porting. |
| PR-02 | Act on the settled frame `frame[-1]` of an animation stack | same | MIT-0 | G0 / A4 continuity | [OBS] | CHECK whether Ring 9 already does this |
| PR-03 | A whole no-LLM CPU explorer as the **floor arm** in the prereg | same | MIT-0 | prereg control, not a gate | [HYP] It gives a deterministic floor every LLM arm must beat | PROPOSE to the Director |
| PR-04 | Dual-mount wheelhouse resolver | jessky fork (Franzen-derived) | Apache-2.0 | packaging | [OBS] Our builds use the single path and have worked so far | DEFER |
| PR-05 | Upstream FrugalExplorer itself | Shlok Sah, rev `7dccef1` | MIT-0 [REPORT via Lockhart] | as PR-01..03 | repository not yet located | FIND |

Rule held: no licence, no port. Transcribe, never copy. The provenance line goes into the module header.

## 3 · What this tranche says about the bet

1. **Enforcement versus advice is now directly observable in public forks.** `obirdy` #7 and #8 are our G2 and G3 disciplines, written as prompt text and left for the model to follow or ignore. If those forks did not beat the base Duck, that supports C-enforcement (structure must be imposed and checked, not requested) and is consistent with JustAdev742's lesson 0025. Their scores are not in the notebooks. [HYP until scores are found]
2. **"Observe the win, then carry it" has prior art.** `cognitive-rungs` derives a win type from (L1 initial frame, L1 solved frame) and carries it forward. That convergence is real but crude: a fixed 7-way taxonomy (clearance, colour elimination, construction…), unverified, with no explanation and no prediction. Our H0 differs in three ways: an exhaustive level-1 study before the win, a win capsule with an explanation, and admission only on a confirmed prediction. The paper must cite this rather than claim the idea is new.
3. **Working around the benchmark is visible:** seed trees tuned against the hidden set (#5), unavailable-action no-ops to pace the run (#6), and a human answer key (#11). All three fail our universality firewall by construction.

## 4 · Consequence for the prereg (v2)

`lucifer19`'s report puts run-to-run spread with identical code at about 3.5 points (9.91 vs 6.43) [REPORT]. A single-run difference between arms A and B of a few points is therefore not evidence. The H0 learning-curve metric (`a_n/b_n` per level) must be read across replicates or seeds. **Owed ruling (Director):** the number of replicates per arm. The prereg must fix it before any run.

## 5 · Next

- The Director pulls the Lord Han Solo source dataset (command in the chat). Then mine record #1.
- Locate the FrugalExplorer upstream (PR-05).
- Try to find public scores for the `obirdy` #7/#8 forks. That is the cheapest test of C-enforcement available.
- Tranche 2 (deferred): `scottlegrand` sheetu12b, `keithtyser` serving bundle, `shiiin9` Affectify, `yocybercode` Thui.

— Claude

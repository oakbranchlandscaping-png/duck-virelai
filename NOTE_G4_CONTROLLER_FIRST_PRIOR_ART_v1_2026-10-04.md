# Note: prior art for controller-first G4 (R9-R24), and what it means for learn-to-win (v1, 2026-10-04)

**Author:** Claude (Alpha build seat), signed. Read-only note; nothing built.
**Asked by the Director (2026-10-04 14:35):** "yes, add it with sources."
**Attaches to:** `BUILD_PLAN_PORTS_AND_PILLARS_v1_2026-10-04` (`365ab26`). That plan is unchanged; this note adds to it. A dated banner at the top of the plan points here.
**Reads with:**
- `RULING_G4_CONTROLLER_FIRST_v1_2026-10-04` (Director, "Broad");
- `DIAGNOSTIC_G4B_CONTROLLER_RELATIONS_v1_2026-10-04`, with its proposed R9-R24 D18–D21 (`6a3183c`);
- `REVIEW_RING9_CARRY_VC33_V7_KAGGLE_2026-10-04` (`37b785f`).

**Tags:** [OBS] = read at the cited source; [REPORT] = an author's own claim; [HYP] = my inference.

## 1 · What happened on `main` that bears on the plan [OBS]

- **v7 review.** vc33 reached G4-B and G4-C for the first time. A contradiction loop took about 157 minutes, and **0 of 11 laws were supported**. The score was unchanged at 1.51 (2 of 7 levels).
- **Diagnostic.**
  - A lookup against the recorded transitions predicts 10 of 18 G4-B/G4-C presses; Duck predicted 1 of 23.
  - Duck's card showed `state_now UNRECORDED` 1,947 times out of 1,947.
  - The coupling map was certifiable at t140 with zero Duck turns.
- **Ruling (Broad).**
  - **G-1:** the controller certifies lever relations from the recorded transitions, with no Duck turn.
  - **G-2:** an observed transition is evidence whether or not a prediction preceded it.
  - **G-3:** Duck confirms or extends on a per-level turn budget.
  - **G-4:** when the budget is spent, the gate closes UNRESOLVED, never in a loop.

## 2 · Prior art for R9-R24, from material already mined

| R9-R24 item | Prior art | Source (rev, licence) | How it fits, and its limits |
|---|---|---|---|
| **D19 / G-1: the controller certifies relations from recorded transitions** | **Rules fitted by code, scored against the log.** `OnClick` models "clicking inside an entity of `button` affects every entity of `target`" with a move, vanish or recolour effect. `fit_onclick` enumerates buttons that were clicked when something else changed and keeps only rules with zero contradictions. `auto_rules` greedily selects the set that explains the most events with no contradiction. | JustAdev742 `arc3/dsl.py`: `OnClick` `:658-741`, `fit_onclick` `:744-801`, `auto_rules` `:1381-1402` @ `8b8a728` (Apache-2.0) [OBS] | **Fits:** a lever → target relation fitted by code from the log, with no model call. That is controller-first law-finding.<br>**Limits:** it keys on colour and shape, so it must be re-keyed onto certified lever regions. One rule is one fixed effect per click, so multi-state lever orbits (G4-A's held, returned and third states) need more than one rule, or an extension. |
| **G-2: evidence is the observed transition** | **Claim semantics:** support counts events that both the claim and the observation share. **A single contradicting observation kills the rule;** there is no threshold. A correct "stays put" claim adds no support, so vacuous agreement cannot carry a rule. | JustAdev742 `dsl.py`: `Claim` `:246-289`, `score_rule` `:905-918`, `explain` `:921-968` @ `8b8a728` [OBS] | **Fits G-2 directly:** evidence comes from what the frame shows, and a recorded counterexample kills. The no-support-for-no-change rule guards against the vacuous "blocked" predictions JustAdev742 reported (48 still actions scored "49/49 correct", `arc3/sandbox.py:545-546`) [REPORT]. |
| **D19 acceptance: is a certified relation consistent with every recorded transition?** | **Transition verifier with abstention.** A candidate may mark cells UNKNOWN. Abstained cells are ignored for acceptance but counted as coverage, which blocks a model that abstains everywhere. A predicted change on an observed no-op is graded. It reports accuracy and the first divergence. | Tycho `tycho/workspace/wmlib_template.py:434-892` (`verify` at `:567`) @ `f68912a` (Apache-2.0) [OBS] | **Fits** as the controller's acceptance check, **with our G2 counter mask as the UNKNOWN mask.** This is the same component the learn-to-win referee uses (build plan W-2, ruling R-6), so it is built once and serves both. |
| **D20 / G-3: Duck works to a turn budget** | Tycho's measurement: the policy that rebuilt models whenever falsified had near-exact accepted models (`accepted_exact_rate` 0.9997) but scored lower (83.07) than the orchestrator (88.49), after 1,192 builder calls with 5 games at the call limit. | Tycho `README.md:28-29`, `artifacts/appendix_metrics.json` @ `f68912a` [REPORT; frontier model, single runs] | **Supports the ruling's premise:** paying the model to repair models without a budget costs score even when the models end up right. That is the same failure as v7's 157-minute loop. |
| **D21 / G-4: never loop** | Loop guards: an identical code snippet is refused within a step; after K tool calls with no action, the model is told to act. | Scott Le Grand `taaf-flashnext-sheetu12b-0922`, agentfix F4, notebook cell 10 [OBS; licence by Kaggle convention, to confirm before transcribing] | Overlaps axiom A2 and G-4. Useful only as a cross-check; G-4's declared UNRESOLVED end is the stronger rule. |
| **D18: lever state labels from the region's content history** | Golden's Push machine: a state is the **masked address** (the picture with the counter delta quotiented out); contradictions are reported, never averaged. | golden `push/machine.py:1-56` (docstring), `:57-207` (ours) [OBS] | **A principle, not code to port:** a lever's state is an address over its own region's content, which matches D18's first-seen content history. |

## 3 · What this means for learn-to-win (pillar 2) [HYP]

1. **The explanation's vocabulary is thin until R9-R24 lands.** G8-EXPLAIN (build plan W-3) may cite only certified terms. With G4-B and G4-C at 0 of 11 laws on v7, a vc33 win can be explained only in lever states and the generic relations (W-1). **Expect more declared residue** ("the win is not explained by certified terms") until controller-first G4 certifies relations. That is an honest outcome, not a failure to patch.
2. **One referee for both jobs.** Tycho's transition verifier with our mask (§2, D19 acceptance) is the same component as W-2's referee. **Build it once,** in `inference/framework/win_referee.py` per the build plan, or in a shared module both import. That choice is for whoever builds R9-R24 and W-2, whichever lands first.
3. **Order.** R9-R24 (controller-first G4) makes pillar 2 stronger, because it enlarges the certified vocabulary the win is explained in. **Recommend:** R9-R24 lands before W-3 and W-6. W-1, W-2 and W-4 (new files only) are unaffected and can proceed whenever the pause ends.
4. **Friction F3 and ruling R-2.** The ruling leaves F3 open ("whether the remaining actions should go to an attempt to win", plan-level, for Apex). Ruling R-2 (2026-10-04: when the ladder rests, "use what data we have and keep playing") already answers part of it **for the submission**: after a G4 closes UNRESOLVED and the ladder rests, the game goes to FREE_PLAY with every certified product on Duck's card. What R-2 does not answer is whether a **deliberate** attempt to win belongs in the ladder itself. That is `ACT_ON_GOAL` (R-7), still gated on the learn-to-win level-3 test. I note the overlap so F3 is not ruled twice in different words.

## 4 · Sources

- `RULING_G4_CONTROLLER_FIRST_v1_2026-10-04.md`, `DIAGNOSTIC_G4B_CONTROLLER_RELATIONS_v1_2026-10-04.md` (`6a3183c`); `REVIEW_RING9_CARRY_VC33_V7_KAGGLE_2026-10-04.md` (`37b785f`). This repo.
- JustAdev742, `Arc-Agi-3-Kaggle-comp` @ `8b8a728`, Apache-2.0: `arc3/dsl.py`, `arc3/sandbox.py`.
- NIMI-research, `Tycho` @ `f68912a`, Apache-2.0: `tycho/workspace/wmlib_template.py`, `README.md`, `artifacts/appendix_metrics.json`.
- Scott Le Grand, Kaggle notebook `scottlegrand/taaf-flashnext-sheetu12b-0922` (pulled 2026-10-04 to `recon_m2/scottlegrand/`).
- golden (ours): `golden/push/machine.py`, `golden/push/search.py`.
- Mining records in this repo: `PORT_PLAN_PUBLIC_NOTEBOOKS_v2_2026-10-04` §9 (BA-2, BA-3, BA-7), `BUILD_PLAN_PORTS_AND_PILLARS_v1_2026-10-04` (W-2, W-3, A-1, A-2).

— Claude

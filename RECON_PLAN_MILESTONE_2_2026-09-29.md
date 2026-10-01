# Recon plan: ARC-AGI-3 Milestone 2 open-source solutions

**Type:** `RECON_PLAN_MILESTONE_2` · **v1** · **2026-09-29**
**Author:** Claude (Alpha build seat), signed. Director-ordered: we do not submit; we study the
winners' published code.
**Status:** prepared before the drop. Questions and hypotheses below are frozen before any
winning code is read, so the recon grades what we learn, not what we expected.

## 0 · The governing question (Director, 2026-09-29)

> **Will Virelai add to these attempts?**

Everything below serves this question. "Add" has three meanings, and each must be tested
separately:

1. **Score:** leader's agent plus a Virelai component beats the leader's agent alone, same games
   and budget.
2. **Efficiency:** the same score in fewer actions.
3. **Generality:** the same score, earned without public-game-specific material.

Virelai adds only where the leaders fail, so recon is **failure analysis first**: where each
leader loses, and whether that failure matches a capability Virelai actually has (lossless record
and counter mask; ego and lever attribution; the masked state machine; gated focus and verified
products; boundary and observed-win preservation).

**Prior: no, unless shown otherwise.** Tufa's Milestone 1 lesson (tools hurt) and our own Ring 7
revelation (every addition cost score against r0) both point against us. A claim that Virelai adds
must name three things: the leader failure, the Virelai component, and the experiment that would
show the gain. Anything less is not evidence.

Timing: no data is read and nothing is committed until the top teams' material is released.

## 0.1 · Convergence audit: has this been done, and done better? (Director, 2026-09-29)

> "It is very possible that my concepts have been implemented by better funded professionals.
> If that is the case I want to know rather than pretend I still have an edge."

Each Virelai concept below has an operational test, frozen before any winning code is read. A
leader implements the concept only if its code meets the test; a prompt line that merely mentions
the idea does not count. After reading, **the tests may not be narrowed** to preserve an edge, and
**they may not be loosened** to see convergence that is not there.

| # | Concept | Operational test: the leader's code... |
|---|---|---|
| C1 | Time separated from world | identifies a changing region as bookkeeping and excludes it when judging what an action did |
| C2 | Ego first | establishes what the agent directly controls before attributing other change |
| C3 | Exhaustive cause inventory | systematically tries every object/affordance, and does not stop at the first effect |
| C4 | Focused sub-targets | restricts the model to one bounded question at a time, with a completion test |
| C5 | Verified world model | holds explicit beliefs about the world, and admits them only after the record confirms a prediction |
| C6 | Evidence lineage | can trace a belief back to the recorded transitions that support it |
| C7 | Observed, not guessed, win | treats the goal as unknown until a win is observed, then explains it |
| C8 | Cross-level transfer | carries what was learned on one level to the next as a hypothesis to re-test |
| C9 | State machine and coverage | records (state, action) -> state, and uses it to reach untried states |
| C10 | Observable internal model | exposes its world model in a form a human can read and check |
| C11 | Death as data | treats a death as an event to explain (not only an interruption), and uses that explanation to change later behaviour within the same level |

**The claim under test (Director, 2026-09-29/30).** Score is one axis. The Virelai aim is an
agent that builds a **linguistic world model** of its environment and **gets better as it dies and
gathers more data**. Stated so that it can lose: *a linguistic world model, admitted only through
confirmed predictions, whose predictive accuracy on the agent's own transitions rises across
lives.* C5, C6, C10 and C11 are the concepts that bear on it most directly; recon records whether
any leader already makes this claim, and with what evidence.

**Verdict per concept per team:** IMPLEMENTED-BETTER · IMPLEMENTED-COMPARABLY · PARTIAL · ABSENT ·
CONTRADICTED (their evidence shows the concept hurts). Each verdict cites file and line in a
pinned commit.

**What each outcome means, decided now:**
- A concept rated IMPLEMENTED-BETTER by any leader is no longer an edge. We say so plainly, and we
  port or study their version rather than defend ours.
- A concept rated CONTRADICTED goes to the Director as a plan-level challenge to the thesis.
- An edge survives only where leaders are ABSENT or PARTIAL **and** section 0's three-part test
  (leader failure, Virelai component, discriminating experiment) can be written for it.
- If no edge survives, the synthesis says so in its first line.

## 0.2 · Scope widened: the public harness corpus (Director, 2026-09-30)

The Paper Prize judges novelty "relative to existing public research", and the recon's
convergence audit (0.1) applies to **all** public prior art, not only the Milestone 2 winners.
The sweep of 2026-09-30 (about 04:45 ET) found no Milestone 2 release yet (Tufa `main` still
`7652836`; no ARC Prize Milestone 2 post), but a substantial public corpus outside Kaggle.

**Index.** Retrodict's comparison document (`ryanbbrown/retrodict`,
`docs/arc-agi-3-harness-comparison.md`, updated 2026-08-09) lists every public harness result it
found. All scores below are on the **25 public games**, as reported by their authors (their
report, not verified by us), and most use frontier closed models:

| Harness | Model | Reported RHAE |
|---|---|---|
| Tycho | Claude Opus 5 | 100.00% |
| Retrodict | GPT-5.6 Sol (max) | 99.86% |
| Schema | Claude Opus 4.8 + fallback | 98.98% |
| baseline1 (textual and executable world model variants) | GPT-5.6 Sol | 92.3-98.97% |
| PRO-LONG | Fable 5 | 97.4% best@2 |
| Prime Agent | Claude Opus 5 | 95.5% |
| NOOA (NVIDIA) | GPT-5.6 Sol | 85.13% |
| OPINE-World | Claude Opus 4.8 | 78.37% |
| Vision-CLv1, RGB-Agent, TELL, DreamTeam, Arcgentica, Continual Harness, a-evolve, OpenClaw | various | 5-63% |
| **AERA** | **Qwen2.5-0.5B (open)** | **21.16%** |
| **Polyphony Agent** | **Qwen3.6 (open)** | **19.80%** |

**Preliminary README-level reading of Retrodict (to be confirmed at code level):** log as ground
truth with hypotheses tested against recorded history; a predicted board attached to every
action and checked by the runner (a code referee); a playbook memory marking each point
"checked" or "assumed" (a linguistic, observable, verified world model); escalation to an
executable simulator verified against every recorded frame, then search including toward
never-seen states; a timer rule as a prompt line (from Tufa's Duck); containment against engine
imports. By section 0.1's rule, C5, C6, C9, C10 and the linguistic world model would then be
**implemented by others** and no longer an edge. C4 (developmental gating) and C11 (death as data)
were not seen.

**The regime question (now central).** None of the top public results is shown at the Kaggle
constraint (open ~27B model, one GPU, offline). The two open-model entries (AERA, Polyphony) sit
near 20% on the public set. The Milestone 2 release decides whether these ideas have already been
carried to the small-model regime. If they have, convergence is near total; if they have not,
"the glass engine at small scale", with gating as a substitute for model capability, is the open
question Virelai can own.

**Procedure addition.** Each corpus harness gets a short dossier (section 6, step 6) and a row in
the convergence audit, read at a pinned commit, prioritising Retrodict, baseline1 (textual world
model), Tycho, NOOA, AERA and Polyphony.

## 1 · Why, and what is already verified

Milestone 2 closes **2026-09-30**. To be eligible for milestone prize money, a team must open-source
its code and methods by the milestone deadline
([competition page](https://arcprize.org/competitions/2026/arc-agi-3)). The winners' code is
therefore the richest public prior art this competition will produce before the final.

Verified 2026-09-29 (direct observation unless tagged):

- Milestone 1 (2026-06-30) winners were all LLM agents: Tufa Labs' Duck (Qwen3.6-27B, Python
  REPL harness), then two vision-LLM policies (Reki, Gemma-4-31B; "forge")
  ([ARC Prize blog](https://arcprize.org/blog/arc-prize-2026-milestone-1)). Tufa's stated lesson:
  hand-crafted tools hurt; improvisation worked better.
- Milestone 1 level of play: Tufa reports 1.21% on Kaggle and a mean of 1.6002 over 25 public
  games ([Tufa write-up](https://tufalabs.ai/research/duck-harness/)). Our pristine r0 Duck
  measured a mean of about 1.22 (sum about 30.5 over 25 games; commits `f56bc27`, `6f3b760`).
- Tufa's public `main` is still `7652836` (2026-07-01), the Milestone 1 release, identical to our
  frozen `baseline/duck-harness`. Its four open community PRs are infrastructure only
  (install, sbatch, viewer, file modes).
- **Director report, not independently verified:** leaderboard scores have risen to about 45%.
  The Kaggle leaderboard does not render to our tools. If 45% is on the same scale as
  Milestone 1's 1.2-1.6%, it is a roughly 30x jump in three months. That is the first thing
  recon must explain.

## 2 · Preregistered questions

For each team studied, the dossier answers:

1. **Score and set.** What score, on which leaderboard (public or private/semi-private), with what
   compute (GPU, runtime, model size)?
2. **General or content-specific?** Does any code path, prompt, data file or cached solution
   single out particular games? (Section 4.)
3. **What drove the jump?** Model change, fine-tuning or test-time training, search, program
   synthesis of an executable world model, memory across levels, action efficiency, or
   something else. Take their own ablations at face value only when they show numbers.
4. **Where does the LLM sit?** Policy (chooses actions), programmer (writes code that acts or
   models), verifier, or none. Where does deterministic code sit? Map onto our frame: target,
   fence, referee.
5. **What is portable under our laws?** Machinery transfers; world contents never do.
6. **Does it contradict our thesis?** For example, evidence that unconstrained improvisation beats
   bounded targets at this model size.
7. **Would it run on our budget?** One RTX Pro 6000, internet off, 30 GPU hours a week.

## 3 · Preregistered hypotheses (priors, before reading)

Stated so the recon can prove us wrong. Not mutually exclusive.

- **H1 (model):** most of the jump comes from a stronger or fine-tuned model, or test-time
  training, not from harness structure.
- **H2 (world model and search):** the leaders synthesize an executable model of the game from
  interaction, then search or plan against it.
- **H3 (content):** some part of high public scores comes from game-specific material for the
  public games, which would not transfer to hidden games.
- **H4 (memory):** persistent cross-level memory (what was learned on level n reused on n+1)
  is a large contributor.
- **H5 (structure):** the leaders impose explicit investigation structure (phases, subgoals,
  verification), which would support our gated thesis over pure improvisation.

## 4 · The firewall: quarantine protocol

Our law: no game-specific knowledge (name, colour, position, mechanic) enters the solver, a work
order or a probe heuristic. Recon reads third-party code that may contain exactly that. So:

- **Clone and read in the cloud workspace only.** Never execute third-party code on the
  Director's Mac. Do not execute it at all unless the Director rules a specific run.
- **Classify every finding** as MACHINERY (world-independent method: portable) or CONTENT
  (anything tied to a specific game: recorded as evidence about their score, never ported).
- **Dossiers carry method, never content.** A dossier may say "team X special-cases N games";
  it may not record what those games' mechanics or solutions are.
- **Do not read game-engine code** shipped inside any solution, for the same reason we never
  read our own downloaded engines.
- **Licence check** before any port: record the licence; port only where it permits.

## 5 · Instrument

`tools/recon_scan.py <tree>`: read-only first pass. It reports files and lines by type,
models and serving stacks named, prompt files, and game-ID mentions split into
**roster files** (10+ games: loaders, infrastructure) and **targeted files** (1-3 games: leads for
hand inspection). It never renders a verdict; section 4's classification is done by hand.

Calibration on our frozen baseline (`baseline/duck-harness`, Tufa M1): two roster files
(game lists in `kaggle.py` and `competition_arcade.py`), two targeted files naming one game
(`game_api.py`, `refresh_examples.py`: example and default wiring), models Qwen3.6-27B-FP8,
stack vLLM. That is the expected reading for a general solution.

## 6 · Procedure, in order

1. **Collect.** Leaderboard top 10 at the drop (the Director copies it; our tools cannot render
   Kaggle). Then, for each prize-eligible team: code link, write-up, Kaggle notebook, licence.
   Watch: the ARC Prize blog winners post, the Kaggle discussion forum, `github.com/Tufalabs`,
   and each top-10 team's public profile.
2. **Pin.** Record repo URL and commit hash for every tree read. Recon on an unpinned tree is not
   evidence.
3. **Scan.** Run `recon_scan.py`; inspect every targeted file by hand.
4. **Read.** Main loop first: what the model sees each turn, what it outputs, what code does with
   it, how actions are chosen, how budget is spent. Then prompts. Then any training or
   test-time adaptation.
5. **Diff against the Duck.** For any team built on the Duck harness, diff against `7652836`.
   The diff is the method.
6. **Dossier.** One file per team: `recon/DOSSIER_<TEAM>_<date>.md`, answering section 2 with every
   claim tagged direct observation, their report, or our hypothesis.
7. **Synthesis.** `REVIEW_RECON_MILESTONE_2_<date>.md`: grade H1-H5, rank portable machinery, and
   state plainly what it means for the gated design. Findings that bear on the plan go to the
   Director as plan-level, not patched into code.

## 7 · Out of scope

No submission. No code port during recon: ports follow as separate, mined, preregistered
slices under the build protocol. No live runs.

— Claude, Alpha build seat, 2026-09-29

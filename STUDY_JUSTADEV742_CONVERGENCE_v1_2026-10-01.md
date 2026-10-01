# Study: JustAdev742's ARC-AGI-3 agent against the Virelai Cybernetic Duck

**Type:** `STUDY_JUSTADEV742_CONVERGENCE` · **v1** · **2026-10-01**
**Author:** Claude (Alpha build seat), signed. Director-commissioned for the build team.
**Status:** read-only study. Nothing in it changes code or rulings. Claims are tagged
**[obs]** (read in their code or data at the pinned commit), **[their report]** (their logs and
lessons, not reproduced by us) or **[hyp]** (our inference).

**Subject:** `github.com/JustAdev742/Arc-Agi-3-Kaggle-comp`, pinned `8b8a728` (2026-09-29),
**Apache-2.0**. Read in the cloud workspace; no code executed. Their documentation is unusually
complete: `docs/status.md`, `docs/research_log.md` (~2,000 lines, one entry per measured run),
`docs/lessons/0001-0025`.

**Why this team.** Of every public Kaggle-regime agent, this one built the most of our concept set
(exact perception, entity roles including HUD and avatar, a verified world model, planning, goal
predicates, cross-level transfer) and measured it honestly. It is the closest outside test of the
Virelai idea we have.

---

## 1 · The headline

1. **They built two systems.** Their own harness, `arc3/`, holds most of the Virelai-like
   machinery. It scored dev 0.4-1.4 and lost to the plain Duck by about 5-10x on the public 25
   (exp-024 0.435 vs Duck-family 5-11). **They abandoned it on 2026-09-23** (research_log
   914-923). [their report]
2. **Their submission is a Duck fork** with runtime patches P1-P31
   (`scripts/taaf_ours_patch.py`). Best arm exp-054: public-25 12.87 / 10.70, leaderboard draws
   4.70 and 3.36. [their report]
3. **Why the rich harness lost, in their own transcripts:** the tools were helpers an
   unconstrained model could call or ignore, and **it mostly ignored them** (research_log 44-47,
   69). [their report]
4. **What they never built:** a controller that owns the order of investigation, bounded questions
   with completion tests, and strict admission of what the model may believe. **That is the
   Virelai bet, untested by them or anyone.**

## 2 · Component comparison

| Virelai (ours) | Theirs (file:line) | Gap | Their measured outcome |
|---|---|---|---|
| Controller-owned developmental gate order | None; a 7-step "Method" in the prompt (`arc3/prompts.py:32-41`); the model drives | **They lack it** | Prescriptive method orders: 1.11 vs 0.84 / 0.73 (exp-005/007/008) |
| One bounded question with a completion test | None; an open REPL turn | **They lack it** | n/a |
| Deterministic work in place of model reasoning | Rule fitters (`dsl.py:1381`), move model and BFS (`planner.py:29,190`), a code-only rules agent | Comparable tooling, **but optional to the model** | Rules agent alone 0.20-0.22; tracker + planner raised dev 0.56 → 1.11 (exp-005) |
| Code verifies against recorded frames | `verify_model` replays all transitions (`sandbox.py:507`); per-action check vs `set_model` (:670); model retired after 3 misses (:68) | Equivalent for predictors; **model claims unverified** | Lesson 0010: a verifier needs a stop rule (14 mismatches before the fix) |
| **Certified products, strict admission** | None; `note()`/`learn()` are model-written and unverified (`sandbox.py:798-806`, `memory.py:51`) | **They lack it** | n/a |
| G0 action surface | `available_actions` treated as authoritative (lesson 0002) | Equivalent | n/a |
| G1 ego law, pointer vs embodied, by controlled probes | Avatar = entity with ≥2 key moves, handed to whatever moved last (`entities.py:417`) | **They lack the pointer law and the probes** | Avatar hand-over fix in exp-011 (1.229 / 1.372) |
| G2 counter: law, trigger, exact footprint mask, purity, prediction | `CounterRule` (`dsl.py:861`); `hud_ids` edge strips (`entities.py:398`); bounding-box mask (`sandbox.py:660`); volatility mask (`explorer.py:185`); P20 rows changing on ≥90% of actions | **They lack the trigger law ("effective actions only"), exact footprint, purity and the prediction** | Volatility mask: explorer 6 → 15 levels (exp-027). P20 never measured alone |
| G3 exhaustive lever inventory with residue attribution | One probe per (colour, shape) class (`repl_agent.py:340`) | **They lack attribution and exhaustiveness** | Not measured alone; the bundle containing it scored 0.265 |
| G4.1 / G4-A per-lever anatomy, repetition to recurrence, period, class | Toggle and Return rules only (`dsl.py:615,804`) | **They lack it** | n/a |
| G4-B combined tests with frozen predictions, graded | `disagreement_probe` (`sandbox.py:606`); P18 "expect:" prose | Partial; theirs is unverified | `disagreement_probe` never run with a model |
| G4-C explain plus a new prediction | Consolidation "scribe" call (`repl_agent.py:978`) | Theirs is unverified | P26 level-win record dropped (exp-057 8.83 vs 12.45) |
| G7 novelty exploration over a masked state machine | **Built:** masked-key BFS explorer (`agents/explorer.py`) | **We lack it built** (golden Push unported) | exp-027 15 levels on dev; lesson 0003: levels 2+ cost 700-19,000 actions |
| G8 observed-win capture and explanation | **Built:** `terminal_layer` (`perception.py:304`), level archive, goal predicates with falsification (`dsl.py:1597,1938`) | **We lack it built** | Terminal frame exact on 43/43 (lesson 0017); goal recall 5 → 11 of ~17 solved levels |
| G9 cross-level transfer as re-tested hypotheses | **Built:** `goal_signature` / `instantiate_goals` (`dsl.py:1758,1770`) | **We lack it built** | Optimal-play data: exact transfer 10/15 later levels, colour-free 11/15; never run with a model |
| Memory across lives | Model-written lessons shared across games (`memory.py:51-230`) | Theirs uncertified | Not measured alone |

## 3 · What their evidence says about our bet

**Supports the Virelai distinction (code certifies, the model interprets):**
- **Lesson 0024:** exact, code-computed object-change reports (P23/P24) raised hard level-1
  solves from 10/16 to 15/16 and pooled public-25 from 7.95 to 10.31 (about 1.9 sd), at about 240
  tokens per call. It is their best-measured gain, and it is a code-stated fact, not a tool.
- **Lesson 0024's rule:** a report "must not say false things". That is the case for strict
  admission.
- **Every model-calling structure hurt:** the council (0.28 / 0.74 / 0.50 vs 1.23), the supervisor
  P19 (throughput collapse), the level-win record P26 (dropped), and the report inside `action()`
  P25 (8.24 vs 10.31).
- **The verified-predictor machinery worked mechanically** (terminal capture 43/43, goal recall
  improving), but the model was free to ignore it, and did.

**Warns against the Virelai bet as built:**
- **Lesson 0025:** the leaderboard moved with tokens per hour and their allocation, not with
  harness text. One-change ablations of harness ideas by other teams (world models, higher-res
  images, consensus, supervisors) came out at or below baseline.
- **Lesson 0014:** harness structure is worth about +9 at the frontier (Tycho 79 → 88) but about 1
  at 27B.
- **Lesson 0003:** blind search is worthless for RHAE past level 1; RHAE is quadratic in actions
  (lesson 0001).
- **Lesson 0009:** a game gets about 35 model calls. Calls are the budget.
- **exp-017:** three times the time per game gave the same score for 4-5x the actions: the agent
  "keeps acting without learning".
- **Their strategy reviews (2026-09-29):** solved later levels already run at a median 0.73x the
  human action count. The score is lost to **levels not reached**, not to inefficiency.

**What this predicts for us [hyp]:**
- Zero-call gates (G0-G3 run by the controller) fit the calls-are-the-budget constraint.
- Exhaustive lever study is affordable on level 1 and costly on every later level. Gates that
  study instead of reaching will lose score unless the study buys reach.
- The decisive Virelai mechanism is **carry**: certified laws and an observed-win explanation that
  make level n+1 cheaper. That attacks "levels not reached" directly, and it is the part neither
  team has tested with a model in the loop.

## 4 · Their findings worth adopting as lab knowledge

| Lesson | Finding |
|---|---|
| 0003 | Blind search is worthless for RHAE past level 1 (random 0.19, novelty explorer 0.06) |
| 0008 | Connected components are not entities; handling occlusion and compound sprites raised rule coverage 0.10 → 0.50 |
| 0010 | A verifier needs a stop rule |
| 0014 | Structure is worth about +9 at the frontier, about 1 at 27B; model and calls come first |
| 0015 | Goals need plain perception (raw components alongside compound views) |
| 0016 | The goal kind is constant within a game (19/19); every game has a budget bar; some win checks fire only for some action kinds |
| 0017 | The winning frame is not the first animation layer: their rule is exact on 43/43 vs 31/43 |
| 0018 | One run ranks nothing: identical notebooks vary 1.5-2.3x; public 10-22 becomes 5-7 on the leaderboard |
| 0022 | Past reasoning is load-bearing: stripping it took 7.86 → 3.58 |
| 0024 | Exact object-change reports help level 1 (10/16 → 15/16) |
| 0025 | The leaderboard moves with tokens, not harness text |

## 5 · Port map (PORT default; Apache-2.0, attribution and licence notice kept)

| Priority | Component | Fills our | Entry points | Size | Tests | Portability |
|---|---|---|---|---|---|---|
| 1 | Terminal-frame capture | G8 capture | `perception.terminal_layer` (`perception.py:304`): finished board is `n-2` if the last change jumps ≥2x and ≥20 cells, else `n-1` | 23 lines | 3 + 1 | **EASY** (numpy) |
| 2 | Goal predicates with contrastive induction and falsification; colour-free signatures | G8 explanation, G9 transfer | `dsl.goal_predicates` (:1597), `goal_progress` (:1938), `goal_signature` (:1758), `instantiate_goals` (:1770), `render_goal_progress` (:2017) | ~406 lines | 8 + 2 + 3 | **EASY** given an adapter from our objects to their `Ent` |
| 3 | P23 / P24 exact object-change and shape-match reports | Code-certified facts to Duck at about 240 tokens | `scripts/taaf_ours_patch.py:1133-1637`; hooks `ToolAgent._build_user_prompt` in the Duck after the animation line | ~460 lines | 12 | **EASY-MEDIUM**: same Duck base as Ring 9; check against our prompt changes |
| 4 | Masked-state graph: volatility mask, re-keying, BFS to frontier | G7, and exact state identity | `agents/explorer.py:52,179,185,209,326` | ~150 of 426 lines | indirect only | **EASY-MEDIUM** |
| 5 | Entity tracker for occlusion and compound sprites | Our weave/attribution in occluding worlds | `entities.Tracker` (:105), `compound_frames` (:517), `plain_frames` (:479) | ~515 lines | 8 | MEDIUM |
| 6 | RHAE scorer with parity tests | Grading instrument | `arc3/scoring.py` | 50 lines | 5 (parity vs arc-agi 0.9.9) | **EASY** |

**Do not port:** P19 (supervisor, harmful), P21 (call gate, starves hard level 1s), P25 (report inside
`action()`, dropped), P26 (level-win record, dropped), P4 (stripping past reasoning, harmful).
Their `goal_probe` is entangled with their REPL; port the predicates, not the probe.

**Caveats recorded by them, which travel with any port:** the goal grammar misses masked-region
equality, per-tile rules, corner brackets and conjunctions; win checks gated by action kind break
pure contrast (allow about 1% negatives); the compound view hides some goals (keep raw frames);
the code (2.0x) and their log (3x) disagree on the terminal jump factor; a median of 13 goal
candidates stay live per level.

## 6 · Their patch inventory, for reference

Current leading arm (exp-054): P1, P1B, P2, P7, P12, P13, P17, P22, **P23, P24**. Reverted or
dropped: P4, P19, P25, P26. Unmeasured or queued: P14-P16, P18, P20, P27-P31. Their next levers
are serving (NVIDIA's NVFP4 checkpoint, SGLang) and compaction instead of truncation (P31).

## 7 · The Director's position, and the bar it sets

The Director's position (2026-10-01): **the Virelai gated targeting structure can perform better
than these attempts.**

This study supports the position in one precise sense. Their rich machinery failed for a reason
our design addresses, **control**: tools the model could ignore were ignored, and nothing
certified belief. Their single best gain was a code-stated fact. Every model-calling structure
lost.

It warns against it in another. On Kaggle, score tracks calls per game and reach into later
levels. Gates that spend calls or actions on study, rather than reach, will lose unless the study
pays for itself in carry.

**The bar, stated so it can lose:** on the same model, serving and budget, the gated stack must
beat the strongest public Duck fork on the leaderboard over at least 4 paired draws, **or** match
it while producing a verified world model and win explanation that the fork cannot. Identical
notebooks vary 1.5-2.3x between draws, so a single draw decides nothing (lesson 0018).

## 8 · Recommended next steps for the build team

1. **Port 1-2 first** (terminal capture, goal predicates): they fill our unbuilt G8/G9 with
   measured, tested code, and they serve both the glass engine and the carry.
2. **Port 3** (P23/P24) into the Duck prompt path: the best-measured small-model gain anywhere.
   It should be our controller's channel for certified facts.
3. **Port 4's masked-state graph** as plumbing: exact state identity under G4 and G7.
4. **Instrument calls and actions per gate** before any live run, against the budget their
   lessons document (about 35 calls per game).
5. **Base the head-to-head on the strongest public fork** (Franzen, Apache-2.0, 27.89 public),
   since the top two leaderboard teams declined to open-source for Milestone 2.

## 9 · Ontology: what they had, what they lacked (added 2026-10-01 at the Director's direction)

Director's position: their machinery is prior art we can use; what they lacked is the **arc grid
multiverse ontology** together with **gated cybernetic targets that force the LLM to work in a
certain way**. Checked against their system prompt (`arc3/prompts.py`, `SYSTEM_PROMPT`) before
recording.

**What they did have [obs]:**
- an operational vocabulary: tracked entities with roles (static, HUD, avatar, dynamic), events,
  rule types (move, push, drift, vanish, recolour), and lesson kinds (mistake, hazard, mechanic,
  recipe);
- a seven-step "Method" the prompt tells the model to follow: map the keys; **form a goal
  hypothesis (step 2)**; plan and verify; consolidate at level end; handle being stuck; name the
  wrong assumption after a failure.

**What they lacked:**
1. **The epistemic ontology.** The grid as a flip book of integers; observation kept separate from
   interpretation; identity as a persistence hypothesis; the cause taxonomy (levers, reactions,
   forces, scoped inertness); claims bounded by what has been tested. Their vocabulary names
   things. Ours governs what may be *claimed* about them.
2. **The win observed, not guessed.** Their Method asks for a goal hypothesis at step 2, before the
   physics is understood. Their own data shows a median of 13 goal candidates still alive per level
   (exp-028). Our design explores the physics first and explains a win only after observing one. A
   real difference in method, and testable.
3. **Enforcement.** Their Method was a suggestion ("follow it"), and the transcripts show the model
   mostly did not, and ignored the tools (research_log 44-47, 69). Our gates own the order, pose one
   bounded question with a completion test, and admit nothing the record has not confirmed.

**Caution recorded with it.** The ontology alone is not the edge. It is also prompt text, and every
team's evidence says prompt text by itself does not move a small model (Franzen: one set of prompt
additions "lost 43% of the previous competition score"; JustAdev742 lesson 0025). What is distinct is
the pair: **the ontology defines what each gate asks and what a valid answer is; the gates and the
code enforce it.** Without the gates, the ontology is another Method to be ignored. Without the
ontology, the gates are arbitrary checkpoints.

**The edge, as recorded:** *the arc grid multiverse ontology, made binding by gated cybernetic
targets and certified by code, so that a small model is forced to investigate the way the ontology
says intelligence should, and to claim only what the record confirms.*

— Claude, Alpha build seat, 2026-10-01

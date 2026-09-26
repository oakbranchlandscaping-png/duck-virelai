# Grounding: what the benchmark makes possible, impossible, and expensive

**Type:** `GROUNDING_BENCHMARK_FACTS` · **v1** · **2026-09-20**
**Sources:** the official ARC-AGI-3 paper (project file `ARC_3_Official.pdf`, April 2026), the ARC
Prize 2026 Milestone 1 announcement (arcprize.org), and the vendored taaf SDK in the Ring 9 tree.
**Boundary:** this document holds platform and benchmark facts and published examples only. It
informs gate *design*. Per the information wall, nothing here — and especially no published
detail about a named public world — enters a work order, a prompt, or a probe heuristic.

## 1 · Platform invariants (facts every gate can lean on)

1. **The world is 64×64 cells of 16 integers.** A turn delivers a frame or a frame *sequence* —
   non-interactive animations between turns are part of the format. The atomic causal record is
   action → settled transition, but intermediate animation frames are real evidence and must be
   retained; a delta inside an animation is not a fresh action's effect.
2. **Turn-based and synchronous, absolutely.** "The environment's state does not change
   asynchronously from the agent's actions." There is no wall-clock, no waiting, no background
   thread on the world's side. Anything that looks autonomous is a process indexed to turns (or
   unfolding inside an animation sequence). This is load-bearing for G5: a `ForceLaw` can only
   ever be turn-indexed or animation-carried — nothing else exists to find.
3. **The action space is a subset of:** five key actions, an Undo action (reverting to the
   previous state), and one coordinate-select action. In the vendored SDK, `RESET` (id 0) is
   always legal, zeroes in-level progress but not the level, and is the only legal action after
   GAME_OVER. No explicit Undo id appears in the taaf layer — G0 reads what is offered and no
   design may *assume* Undo exists; where it does appear, it is a probe primitive worth its own
   child target (cheap state-restoring experiments, at one action each).
4. **Environments are level chains** (design floor of six levels; published scoring examples use
   five — treat the count as per-world data). A level ends at a terminal frame. Level 1 is a
   deliberate tutorial — easy, occasionally random-solvable, and *designed to communicate the
   interaction pattern*: the cheapest mechanics lesson the world will ever offer.
5. **Non-tutorial levels are random-proof by construction:** validation requires a random policy
   to win less than 1 in 10,000 times, verified over million-step sweeps. Undirected pressing
   cannot win; only model-guided action can. This is the benchmark's own argument for the lab's
   thesis, stated as an acceptance threshold.
6. **Multiple mechanics per environment are mandated** — a single mechanic that scales is an
   explicit anti-pattern, and difficulty is meant to arise from *composition* of concepts across
   levels. Expect G3–G5 material in every world, and expect later levels to require what earlier
   levels taught (G9's carry is load-bearing by design, not by hope).
7. **Core Knowledge priors bound the mechanic space:** objectness (persistent entities that
   move, collide, occlude), basic geometry and topology (symmetry, inside/outside, connectedness,
   holes), basic physics (gravity, momentum, bouncing), and agentness (objects that act with
   intent and pursue goals). Never language, numbers, letters, real-world clip-art, or cultural
   conventions. So: G4's reaction vocabulary can expect gravity/momentum/bounce families; G5
   should expect intent-driven, state-conditioned pursuers as a legal mechanic; and no gate ever
   needs to read a symbol — a shape that looks like a glyph is just a shape.
8. **Invalid actions exist and are self-loops** in the designers' own validation graph — the
   platform's per-turn legal-action list plus refused/no-op presses are structure, not noise.

## 2 · The scoring law, and what it does to gate design

RHAE: per level, (human baseline ÷ agent actions)², capped at 1.15; levels linearly weighted
(late levels dominate); an environment cap equal to the weighted fraction of levels completed;
and an **action budget of 5× the human baseline per level — the agent is terminated there.**

Design consequences, in order of force:

- **Budgets are per-level and small where levels are small.** The paper's own example: a public
  world's level 1 takes humans under 5 actions — so the budget there is on the order of 25
  actions, while its level 6 takes ~50 human actions (~250 budget). A gate sequence that spends
  40 actions understanding a 5-action level has already lost the level. The sweep must be
  budget-aware per level: representative-first collapse is survival, not politeness, and
  enumeration-completeness must be *scheduled within* 5n, with the certificate honestly recording
  what the budget forbade.
- **Completing levels dominates elegance.** The environment cap means efficiency on early levels
  can never compensate for an uncompleted later level. When the model is confident, pressing on
  beats polishing.
- **Waste is punished quadratically.** Squared efficiency means exploration overhead is not
  linear cost — every gate's action spend is squared against the score.
- **The tutorial is a gift.** Level 1 is designed to teach the interaction pattern at trivial
  cost; the gate ladder's cheapest complete pass (G0–G2 and a fast G3) should aim to complete
  inside level 1's own budget, arriving at level 2 with the control channel, the counter, and
  first levers already law.

## 3 · The evaluation landscape (what we are actually playing in)

- Sets: 25 public demo, 55 semi-private, 55 fully private environments. **The private sets are
  intentionally out-of-distribution from the public set, with limited mechanic overlap.** Tuning
  any probe heuristic to a public world's particulars is therefore not just doctrine-violation —
  it is strategically worthless by the benchmark's own construction. Universality through
  invariant machinery is the only strategy the design rewards.
- The official leaderboard excludes harnesses entirely; harness systems live on the community
  leaderboard and the Kaggle competition. That is our venue, and the paper's own red-team data
  is the cautionary tale: a hand-crafted harness took one variant world from 0.0% to 97.1% and
  did nothing at all on another (task-specific overfitting made measurable).
- **Tufa's stated Duck lesson: "hand-crafted tools actually hurt the model; letting it improvise
  worked better."** This is the exact counter-thesis to Ring 9, and the paper's distinction is
  our answer: what failed was *world-specific tooling*; what the gates impose is *world-free
  epistemic discipline* — coverage, prospectivity, evidence-binding — the same machinery on
  every world. The G0–G2 live run is precisely the test of whether that distinction is real.
- **Calendar with teeth: the second and final ARC-AGI-3 milestone concludes September 30, 2026.**
  Ten days from this document's date. Frontier unassisted scores at paper release: ≤0.5%.

## 4 · Per-gate "do not worry about it" ledger

- **G3:** no asynchronous confounder can corrupt a press — everything a press caused is in its
  transition (plus its animation frames). Attribution problems are ordering problems (schedule
  ticks landing on the same turn), never race conditions.
- **G4:** the response vocabulary is bounded by core priors — collision, blocking, carry,
  consumption, gravity/momentum/bounce, containment. No reaction will ever require reading a
  symbol or knowing a convention.
- **G5:** no wall-clock forces exist. Every "environmental" process is turn-indexed,
  animation-carried, or an intent-driven agent whose pursuit is conditioned on world state —
  which is why the force observable is *state-conditioned, not autonomous*.
- **G6:** inertness certificates are bounded by tiny per-level budgets; "never tried, budget
  spent elsewhere" will be the certificate's most common honest line, and that is correct play.
- **G7:** the designers validate worlds with exactly our instrument — a hash-keyed state graph
  with action edges, self-loops for invalid actions, cycle detection, reachability. The masked
  state machine is not a speculative representation; it is the world's own native geometry. And
  random-proofing guarantees the novelty frontier cannot be won by stumbling — it must be walked.
- **G8:** the win is a terminal frame the platform announces. There is nothing to infer about
  whether a win happened — only about why.
- **G9:** composition-by-design means concepts from level N recur in level N+1. Carry is not
  speculative reuse; it is the difficulty model of the benchmark.

## 5 · Checks owed against the live SDK (facts this document could not settle)

Whether an Undo id is ever offered in the 2026 SDK action metadata and whether it counts against
the action budget; whether an invalid/refused action decrements the budget; per-world level
counts; and whether the Kaggle milestone harness imposes budgets identical to the 5n paper rule.
Each is a one-line check against `arcengine`/scorecard behavior at the next live run — G0's
metadata acknowledgment and the run receipts will answer them for free. Do not design against a
guess where a receipt will answer.

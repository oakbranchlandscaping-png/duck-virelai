# RING 6 DESIGN — THE OPENING
**v1 · 2026-08-28 · Chamber: Cowork (interim) · Status: PRE-HARVEST DRAFT**
**Ruling basis:** Director 2026-08-27/28 — "set virelai for X number of lives, it runs our
probes, builds the library as well as it can, then presents the field card to the model."
**Order note, declared:** this draft precedes its mining pass, inverting METHODOLOGY §1.
The Director sequenced it so. A harvest pass follows and amends this file as v2 before
any code is written.

## 0 · The one variable

An **autonomous opening**: Virelai probes before the model is called, then hands over once.
Nothing else changes — no new seal, no new perception, no prompt rewrite beyond the card's
section ORDER.

## 1 · What the interface actually permits (read from solver.py, ring5 bundle)

| fact | consequence |
|---|---|
| `_engine_action_names()` **skips RESET** — it never enters `valid_actions` | the model cannot reset. A LIFE is already solver-side bookkeeping, exclusively |
| `GAME_OVER` -> `_execute_auto_reset()` in the `play()` loop; `ONLY_RESET_LEVELS=true` is pinned | a life ends only at GAME_OVER, and the LEVEL survives it. `levels_completed` untouched |
| `_execute_auto_reset` calls `_execute_action(..., generated_tokens=0)` **outside the analyzer** | a solver acting without the model is committed Tufa precedent, not a hack. Probe presses cost **zero model tokens and zero inference** |
| `max_actions_per_game=None`; `max_runtime_s_per_game=7920` (132 min) | the binding resource is WALL CLOCK, not actions. An engine step is milliseconds; a model turn is seconds-to-minutes |
| Ring 1.1 marks the RESET root; the ledger is per-game | knowledge ACCUMULATES across lives. The map reattaches after every death |

**So the whole price of the opening is the <=2.8 score points that burning level 1 can ever
cost** (metric verified 2026-08-27: level 1 carries 2.2-4.8% and the squared term saturates).

## 2 · Mechanism

`self._virelai_opening()` — one call in `play()`, after the seeding lines, before the
`while not self.should_stop()` loop.

**Phase A — open generatively.** Exercise every roster action once at the root. No cleverness
is possible with an empty library; this is the five-beat's first beat.

**Phase B — walk the frontier.** Ring 3's BFS over walked edges already computes the route to
the nearest node holding an untried action. Today it advises. Here it drives: route, walk,
try, record. Repeat.

**Deaths are free.** On `GAME_OVER` call the existing `_execute_auto_reset()`, increment the
life counter, continue. The ledger persists; the root reattaches.

**STOP — saturation first, budget second, and the reason is reported:**

- `SATURATED` — a full frontier sweep completed with **no untried action remaining at any
  reachable walked node** and **no new seal produced during that sweep**. Sweep-indexed, not
  a press count: no number is chosen.
- `BUDGET` — X lives spent. A spend cap over a mechanism the harness already owns. It is not
  an evidential trigger and does not resolve any belief.
- `GUARD` — `should_stop()` or a wall-clock fraction, whichever the harness raises first.

**MOUSE needs its own completeness rule**, or saturation can never fire on a CLICK world:
"tried" for MOUSE means **at least one coordinate on each distinct object in the current
frame**, not the coordinate space. Stated here because leaving it implicit is how a
never-terminating opening ships.

## 3 · The handover — one card, ordered for what it is FOR

Ring 4 measured the model **slicing the card** (`card[:` in 20 of 25 games), which is how
GAPS went missing from 18 of 82 renders. Whatever sits last is what gets cut. So the opening
card is ordered by what the Director asked it to deliver:

1. **MECHANICS** — each action and what it did. `UP -> your shape moved (-1,0), 14 witnesses`.
2. **SEMANTIC ROLES DISCOVERED** — the sealed reads with the observation that earned each and
   what would falsify it. Ego, counter, drains, levers.
3. **PHYSICS GRAMMAR** — what holds across this world: every cell always holds a value; the
   counter keys on THAT-ANY not WHICH; RESET returns the level's start byte-identically;
   every visited state is proven non-win.
4. **GAPS** — including, newly sayable: **why probing stopped**, and what is still open.

## 4 · Pre-registered fixtures

| # | fixture | measure |
|---|---|---|
| F1 | the opening RAN | probe presses recorded before `analysis_step 1`; the model's first prompt carries a populated card |
| F2 | the handover is informative | on every world where ring5 sealed anything, >=1 sealed read is present at turn 1 |
| F3 | the stop reason is stated | every game reports SATURATED / BUDGET / GUARD in GAPS |
| F4 | the opening is cheap in the binding resource | opening wall clock < **2%** of the 132-min per-game budget |
| F5 | the model starts informed | model-issued actions per game FALL vs ring5 |
| F6 | **negative control** | a world where nothing seals still terminates, hands over, and GAPS says unsaturated-on-budget rather than going silent |

**Acceptance criterion, v4's own:** does this change what the solver does on at least one
game? A populated card that changes no behaviour is FRICTION-004 again.

## 5 · Pre-registered limitations

1. **CARRY DOES NOT EXIST.** Nothing survives the level boundary hybrid-side. The opening
   makes level 1 cheap to lose; it does not yet make level 2 cheap to win. That is the
   separate gate and it is not this ring.
2. **CLICK worlds have no death**, so lives cannot bound them — saturation or a press cap must.
3. **Probe presses charge level 1's action count.** <=2.8 points, verified, and cheap — but
   not nothing.
4. **The model may distrust a card it did not earn.** Ring 1 measured +69% actions when the
   model was handed a frontier; being handed a whole world could reproduce that at the
   opening. F5 is where it would show.
5. **The opening explores the world the RESET root belongs to.** Nothing is claimed about
   later levels' worlds.

## 6 · Failure shapes filed in advance

- **A sweep that never completes** — a large world plus frequent deaths means the frontier
  keeps growing and SATURATED never fires. BUDGET catches it; the signature is every game
  reporting BUDGET and F4 breaching.
- **Wall-clock blowout** on a big state space, since BFS runs per probe press.
- **The opening dies in the same place repeatedly**, spending lives without new information.
  The no-new-seal half of saturation should catch it; if it does not, lives drain silently.
- **The model re-probes anyway**, treating the card as someone else's notes. Measured risk,
  not hypothetical.

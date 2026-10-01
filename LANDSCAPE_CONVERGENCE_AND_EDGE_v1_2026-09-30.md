# The landscape: what outside teams have converged on, and where Virelai may still have an edge

**Type:** `LANDSCAPE_CONVERGENCE_AND_EDGE` · **v1** · **2026-09-30**
**Author:** Claude (Alpha build seat, Cybernetic Duck line), signed. Director-directed.
**Reader:** any project. **Game-free by construction:** no world's mechanics, colours, positions
or solutions appear here.
**Basis:** a code-level read of the public ARC-AGI-3 harness corpus on 2026-09-30, at pinned
commits (Retrodict, baseline1, Tycho, Polyphony, NVIDIA NOOA, PRO-LONG, Prime Agent, AERA), plus
the released world-model documents of two independent frontier harnesses across all 25 public
games. Milestone 2 Kaggle winners had not yet released code; revisit this when they do.

## 1 · The headline

**The glass engine has been built, by others, at frontier scale.** Agents running frontier models
inside thin harnesses already write a readable, largely correct world model of an unseen game:
what the controls do, what the timer is, and why each level is won, with claims marked verified or
assumed. Two independent teams' agents did this on every public game and agree with each other on
the goal in 23 of 25 games and on the core mechanic in 24 of 25.

**What has not been shown is the same thing from a small open model on one GPU**, the Kaggle
regime. That gap is where Virelai's remaining edge lies.

## 2 · Converged on by outside teams (no longer our edge)

Each is implemented in public code by at least one team, most by several:

- a readable, linguistic world model of mechanics and goal, written by the agent;
- an explanation of why the win occurred, in terms of the learned mechanics;
- a deterministic referee: code that replays the agent's model against every recorded frame;
- prediction before action, checked by the runner;
- observed, not guessed, wins;
- cross-level transfer, re-verified across completed levels;
- death as data: a game-over captured, explained, and used within the level;
- an observable internal model a human can read;
- a firewall against the game's source, sometimes audited.

Public-game scores for frontier-model harnesses: roughly 78-100% (authors' reports).

## 3 · What the outside evidence says about structure

From the teams' own data:

- more accurate world models did not reliably produce higher scores;
- a plain textual world model came within a few points of a replay-verified executable one, at
  about a third of the cost;
- always-on exhaustive probing was too costly and was cut back to "only when stuck";
- the newest model generation moved scores far more than any harness change;
- the one serious open-27B harness found that structure paid for in model time starved play;
- Milestone 1's winner reported hand-built tools hurt a small model; our Ring 7 found every
  addition cost score against the pristine baseline.

At frontier scale, structure helps a little. At small scale, structure that costs model time hurts.

## 4 · Where Virelai may still have an edge

Six things no public harness does in code (a prompt line suggesting them does not count):

1. separating the clock/timer from the world before judging what an action did;
2. establishing what the agent controls before attributing other change;
3. an exhaustive, systematic inventory of every possible cause;
4. restricting the model to one bounded question at a time, with a completion test;
5. admitting a belief only after the record confirms a prediction made from it (everyone else's
   verification is advisory);
6. a recorded state machine of what the agent has seen, used to reach untried states.

Each is work a frontier model does by reasoning and a small model cannot afford to. Virelai does
them in deterministic code, at zero model cost.

> **The edge, stated so it can lose:** deterministic scaffolding that costs no model calls can let a
> small open model on one GPU produce a glass-engine world model approaching frontier quality,
> where the same small model without scaffolding cannot.

The opposite of the structure that hurt others: theirs spent model time; ours spends none.

Expected shape (a prediction, not a finding): the gap closes most on mechanics, which decompose
into measurement, and least on goal inference, which no subroutine replaces.

## 5 · How it will be tested

`PREREG_SMALL_MODEL_GLASS_ENGINE_v1_2026-09-30.md` (pending Director ratification): the same small
model and budget with and without Virelai, graded blind against the frontier consensus on held-out
public games the build team has never read, with decision rules fixed in advance, including: if
the scaffolding does not close the gap, we say so first.

## 6 · What this means for every project

- **Stop claiming** the glass engine, the verified linguistic world model, win explanation,
  cross-level transfer or death as data as Virelai novelties. Cite the prior art.
- **The contribution, if it holds,** is small-model capability through zero-cost deterministic
  scaffolding, and the developmental order (clock, ego, causes, one question at a time) that makes
  it work.
- **Convergence is corroboration.** Well-funded teams independently arrived at the lab's core ideas
  about how an agent should understand a world. The question has moved from whether these ideas
  are right to whether they can be delivered cheaply.
- **Revisit** when the Milestone 2 winners publish. If a top Kaggle team already does zero-cost
  deterministic scaffolding at small scale, section 4 collapses.

— Claude, Alpha build seat, 2026-09-30

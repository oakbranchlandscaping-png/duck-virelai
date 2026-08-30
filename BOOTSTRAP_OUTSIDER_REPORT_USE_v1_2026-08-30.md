# BOOTSTRAP — OUTSIDER RESEARCH: MAKING AN LLM AGENT USE A DELIVERED EVIDENCE BRIEFING IN FULL FORCE
**Type:** BOOTSTRAP_OUTSIDER_REPORT_USE · **Version:** v1 · **Date:** 2026-08-30
**Use:** paste everything below the line into a fresh chamber with no project context.

---

You are an independent research analyst. You have no access to our codebase and
no other context; everything you need is in this prompt. Your deliverable is a
research memo, and its worth depends on your honesty: distinguish what is
evidence-backed (cite sources or name the mechanism) from what is your
reasoning, and never present speculation in the voice of fact.

## The system under study (abstracted; treat as fixed unless a question says otherwise)

An autonomous agent plays unknown, procedurally-varied grid-world puzzle games.
Before the agent's first move, a deterministic scripted explorer spends a
bounded opening phase interacting with the game and compiles a plain-text
FIELD BRIEFING: observed facts (e.g. "pressing action 1 moves your body 5
cells up"), roles earned from evidence (walls, floors, autonomous counters,
levers), explicit uncertainty ("GAPS: the purpose of the 3 small objects is
unknown"), and a falsifier attached to each claim. The briefing is 1,800–8,300
characters, ordered mechanics-first, and ends with one instruction: "Use the
report as evidence. Preserve its stated uncertainties and test any claim whose
prediction fails on the current frame."

The briefing is inserted EXACTLY ONCE, into the first user turn of a
mid-size open-weights chat model (~27B, tool-calling, ~32K context window,
fixed decoding). The agent then plays alone for up to ~50 analysis turns:
each turn it sees the current game state, may run Python to inspect state,
and issues game actions. Conversation history retains roughly the last 30
assistant turns, after which the OLDEST messages — including the briefing —
are silently trimmed. Fewer actions means a higher score, so redundant
re-discovery of what the briefing already establishes is directly costly.
The model is frozen: no fine-tuning, no logit control. Every intervention
must be prompt-level, protocol-level, or message-management-level.

## What we have measured (our evidence; take it as given)

1. Delivery is proven. The exact briefing verifiably reaches the first model
   request. That is not the problem.
2. On turn 1, the model references the briefing in its own reasoning in 24 of
   25 episodes, often restating specific facts correctly. So it READS it.
3. It does not adopt the METHOD. It treats the briefing as background lore,
   not as a hypothesis set: it rarely states predictions, rarely names what
   would falsify a briefed claim, and often re-derives briefed facts from raw
   state at real action cost.
4. Long content gets sliced. In earlier variants the model programmatically
   truncated a long in-context document and whatever section sat LAST was
   what got dropped.
5. Compliance is dangerously excellent. When an earlier briefing variant
   asserted a wrong fact confidently and forbade doubt, the model obeyed it
   and play collapsed. "Use it more" must never become "trust it blindly."
6. The model strongly prefers rendered prose over raw data structures:
   given a readable briefing instead of a dict to spelunk, its schema errors
   fell ~90%.
7. After the briefing trims out of history (~30 turns), nothing re-grounds it.

## Your research questions, in priority order

Q1 — DURABILITY. What is known about keeping an in-context briefing behaviorally
alive across a long agentic episode? Evaluate at minimum: forced first-turn
conversion (the agent must restate the briefing as its own commitments —
established facts / chosen goal / prediction / falsifier / action — so its own
restatement persists after the original trims out); periodic compact
re-injection; moving briefing content into a tool the agent can query; and
persistent scratchpad/plan objects. What does the literature on context-window
position effects ("lost in the middle", primacy/recency) predict for a
mid-size model, and what placement follows from it?

Q2 — METHOD ADOPTION. What is known about making an LLM actually run a
predict-then-test loop rather than narrate one? Assess structured output
contracts and their known failure mode — ritual compliance, where the model
emits the required sections as boilerplate while its actions ignore them. How
have others detected and prevented ritual compliance? (Note our measurement
scars: any grader that string-matches vocabulary the prompt itself contains
will false-positive; behavior-based grading is required.)

Q3 — CALIBRATED TRUST. How should a briefing express uncertainty so a highly
compliant model neither ignores hedged claims nor hardens them into dogma?
Evidence-tagged claims, confidence language, explicit falsifiers per claim:
what actually works at this model scale?

Q4 — ACTIONABILITY. Does ranking unknowns by information value ("the single
cheapest discriminating test is X") measurably increase uptake versus neutral
fact lists? Where is the line before the briefing starts choosing actions the
agent should choose itself?

Q5 — MEASUREMENT. Propose a grading scheme for "used the briefing" that is
robust to prompt echo: behavioral criteria only (did the first action test a
stated prediction; did the agent avoid re-deriving briefed facts; did it cite
a briefed gap when choosing a target), gradable from transcripts.

## Deliverable

A memo containing: (1) your ranked top 5 interventions, each with the
mechanism you believe drives it, its predicted observable effect in THIS
system, its cheapest falsification test, and its known failure modes; (2) a
minimal A/B design for the top 2, one variable each; (3) the literature or
practice each rests on, cited, with your confidence stated; (4) a short list
of interventions you considered and rejected, with reasons. Do not pad. Where
the honest answer is "unknown; here is the experiment," say exactly that.

Constraints to respect throughout: the model is frozen; one variable per
experiment; no game-specific knowledge may enter the briefing or the prompts
(no game names, colors, positions, mechanics — the machinery must transfer
across arbitrary worlds); and interventions that inflate the briefing's
authority beyond its evidence are disqualified by finding 5.

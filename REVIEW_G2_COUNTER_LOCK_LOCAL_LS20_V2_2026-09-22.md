# Review: G2 counter-lock local ls20 v2

**Date:** 2026-09-22  
**Run:** `runs/20260922_184702_ring9-g2-counter-lock-local-ls20-v2/`  
**Checkpoint grade:** **PASS**

## Evidence boundary

This review uses the executed prompt transcript, gate answers, lossless probe outcomes, raw frame
archive, benchmark receipt, and controller gate views. Statements about pixel transitions are
direct observations. Duck's prose is model output. `SATISFIED` and
`COUNTER_LOCKED_BY_MIN_MAX_BOUNDARY` are executed controller judgments. No game-engine
implementation was inspected.

The benchmark ended `cancelled` at its effective experiment deadline after 43 actions and 22m14s.
That terminal label does not reverse the checkpoint result: G2 reached `SATISFIED` on action 43
before the deadline. The run completed zero game levels, which is outside G2's target.

## What the run directly established

1. G0 and G1 repeated their established chain. G1 closed after an accepted future
   `PATTERN_TRANSLATION` prediction on transition 9.
2. G2 received the demonstrated ego footprint and began the ranked embodied collision opening.
3. Transitions 10 and 11 combined ego motion with a two-cell `11→3` rewrite. Transition 12 was a
   refused `ACTION3` whose only visible delta was the same two-cell rewrite.
4. Duck submitted one accepted G2 answer. It identified the two-row bar at rows 61–62 and columns
   13–54, described a two-cell-per-action progression, cited the three controller-selected
   witnesses, supplied alternatives and limitations, and froze a future `COUNTER_REWRITE`
   prediction using `ACTION3`.
5. Transition 13 changed exactly two cells `11→3`, supporting the frozen prediction. The
   controller created mask reference `MASK-V1-c999b5927f138559` and remained in
   `BOUNDARY_CONFIRMATION_REQUIRED`.
6. Transitions 14–42 continued the isolated two-cell rewrite. At transition 42 the complete
   84-cell footprint contained zero source cells and 84 replacement cells. Duck explicitly
   recognized that one more action was needed to observe the consequence.
7. Transition 43 directly showed the consequence:
   - all 84 bar cells reset `3→11`;
   - the 25-cell ego disappeared from rows 30–34 and reappeared at rows 45–49;
   - a separate four-cell region at rows 61–62, columns 62–63 changed `8→3`;
   - the platform remained on level 1 and did not report game-over.
8. The controller then reported G2 `SATISFIED`, stop reason
   `COUNTER_LOCKED_BY_MIN_MAX_BOUNDARY`, and `WAIT_FOR_NEXT_TARGET`.

The combined transition is direct evidence of an extremal reset with an ego respawn and a separate
four-cell decrement. It supports a cyclic action-budget or life-pressure mechanism. It does not
support the stronger claim that the bar has no gameplay consequence.

## Exit-criterion grade

| Criterion | Grade | Evidence |
|---|---|---|
| Demonstrated G1 handoff | Pass | Transition 9 closed G1; G2 received the demonstrated footprint. |
| Stable full-bar candidate | Pass | Three varied witnesses; 84-cell connected two-class footprint. |
| Duck explanation | Partial | Strong mechanism/evidence account, but its capacity arithmetic is contradictory. |
| Prospective prediction | Pass | Accepted before transition 13. |
| Counter-only demonstration | Pass | Transition 13 was exactly two cells `11→3`. |
| Reversible mask infrastructure | Pass with evidence limit | Executed gate view exposes the 84-cell mask reference and raw grids remain archived; the final bundle does not separately serialize the mask transform for external replay. |
| Continued boundary focus | Pass | G2 remained open through transition 42. |
| Observed extremal consequence | Pass | Transition 43 reset the bar, respawned the ego, and depleted four `8` cells. |
| Controller lock | Pass | Executed status is `SATISFIED` with the required stop reason. |

## Scoped quality notes

Duck wrote that the bar is 42 cells wide, advances by two cells per action, and therefore counts
21 actions. The footprint is two rows by 42 columns: 84 cells total. At two cells per action its
observed period is 42 actions, as the trace itself confirmed. The controller validated the
footprint and rate fields but did not check this contradictory natural-language conclusion.

The prediction's `novelty` prose also says its `ACTION3` differs from the immediately preceding
action, but transition 12 was already `ACTION3`. The prediction was still genuinely prospective
because it concerned an unseen later state, yet this false supporting sentence passed because the
controller checked that the field was populated rather than whether its factual claim matched the
trace.

These are quality notes, not reasons to expand G2 into a full-world explanation gate. G2 directly
established the counter's footprint, exchange rate, action coupling, reversible mask, extremum,
and reset behavior. That satisfies its scoped question. The simultaneous ego respawn and separate
four-cell decrement are retained as unexplained observations for G4, where conditional reactions
and cross-object consequences are typed.

## Runtime friction

- The first analyzer request and a later request around action 28 encountered transient OpenRouter
  TLS failures. The harness recovered and the evidence chain remained intact.
- The interval between actions 8 and 9 was about 713 seconds, and the history attributes 21,166
  generated tokens to the ninth action cycle. G1 closure remains much more expensive than the
  later deterministic boundary loop.
- The configuration requested a 32-minute experiment, but the inline deployment set its soft end
  22 minutes after start, apparently retaining a ten-minute deployment reserve. G2 still completed.
- After G2 reached `WAIT_FOR_NEXT_TARGET`, no G3 existed. The solver repeatedly queried the closed
  gate until the deadline. A checkpoint run should terminate immediately when its target gate
  passes.

## Ladder placement

G2 is complete. The next build is G3 lever inventory and typing. Preserve transition 43 as seed
evidence, but do not explain its full causal chain in G3 merely because it is available.

The causal question opened by the expiry transition belongs to **G4 conditional reactions**:

- condition: counter reaches its extremum;
- observed reaction: counter resets and ego returns to an earlier locus;
- correlated observation: a separate four-cell `8` region depletes;
- unresolved questions: whether that region represents lives, how it conditions later resets, and
  what happens at its own extremum.

The 21-versus-42 arithmetic inconsistency and inaccurate novelty sentence remain useful prompt and
validation notes. They can be corrected by deriving counter period from footprint size and rate,
without adding a broader causal-explanation obligation to G2.

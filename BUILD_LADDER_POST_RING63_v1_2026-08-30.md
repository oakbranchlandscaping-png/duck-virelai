# Virelai build ladder after Ring 6.3
**Type:** BUILD_LADDER_POST_RING63 · **Version:** v1 · **Date:** 2026-08-30
**Author:** the Director (verbatim). Governing plan for rings 6.4–6.7.
Ring 6.3 (`f36c149`/`aee22f7`) is the frozen reference build: Captain runs,
creates a report, delivers it to Duck, Duck reads it. Each following ring
changes one major function.

## Ring 6.4 — Captain throughput
Goal: determine why 25 simultaneous Captains perform slowly in Kaggle, then
improve throughput without changing Captain strategy.
Diagnostic instrumentation — measure every Captain cycle as separate phases:
environment action execution; frame conversion; perception and segmentation;
weave integration; target selection; report and diagnostic logging; total
cycle time; time waiting for a Captain execution slot. Record per game and per
action.
Scheduling change: give Captain execution its own concurrency limit while
leaving Duck/vLLM concurrency unchanged. Flow: game waits for Captain slot ->
Captain probes for its own 480-second budget -> Captain releases slot ->
report enters Duck immediately -> Duck joins the normal model workload.
Test Captain concurrency 2, 4, 8 on a fixed game sample. Waiting for a
Captain slot must not consume that game's 480-second probe budget.
Must not change: Captain strategy; weave logic; field-card wording; ontology;
Duck prompt; two-life and 320-action limits; Ring 6.3 handoff checks.
Required artifacts per game: Captain wait time; active probe time; actions
completed; average cycle time; time per measured phase; stop reason; report
hash and handoff audit.
Success: the actual source of delay is measured; Captain actions per active
minute rise materially; no new faults; the exact report still reaches Duck;
notebook runtime acceptable; extra probing produces more verified evidence,
not merely more duplicate records. Ring 6.4 does NOT introduce a new
"saturated world" stopping rule — separate semantic decision.

## Ring 6.5 — Learn to win
Goal: turn every observed level win into a grounded explanation and a concrete
goal for the next level. A win may be produced by Captain or Duck; both enter
the same win-analysis path.
Central win observer at the common action boundary detects every
environment-reported level transition. On win, preserve: game and level;
acting system; exact winning action; complete pre-action frame; complete
post-action frame; environment result and level transition; objects present
before and after; changed cells and regions; objects touched or moved;
relevant preceding actions; known lever/counter/ego/reactive-region records;
current uncertainty and evidence provenance. Emit `WIN_OBSERVED` — meaning the
environment reported advancement, never inferred from appearance.
Win packet, three layers:
1. Observed facts (mechanically established only): action A in state S
   produced transition T; environment advanced level n -> n+1; these objects
   and regions changed; these conditions were present immediately before.
2. Candidate explanation: which condition probably caused the win; which parts
   of the transition were likely incidental; whether the action activated a
   lever, completed a pattern, reached a location, exhausted a counter, or
   satisfied another relation; what earlier evidence supports it.
3. Falsification plan: for every important claim, predicted consequence; an
   observation that would disprove it; necessary vs merely correlated
   conditions.
Next-level goal model: the best surviving explanation becomes a provisional
goal for level n+1 — a hypothesis, not a command to repeat coordinates.
Captain wins: capture packet immediately; snapshot the completed level before
V4 resets level-scoped state; place observed transition and win analysis at
the TOP of the report; continue probing; give Duck both the previous win
theory and current-level evidence.
Duck wins: capture the same packet at the common action boundary; attach to
Duck's first turn on the new level; require Duck to analyze the win before
another exploratory action; persist the explanation.
Report order when a win exists: 1 observed winning transition; 2 proposed
explanation; 3 competing explanations; 4 falsification tests; 5 goal
transferred to current level; 6 current-level physics grammar; 7 remaining
gaps. The verified win must not be buried.
Success (fixtures vc33, ls20): exact winning transition captured; observation
and inference separated; Duck explains why the action may have won; names a
competing explanation; states a falsification test; converts the explanation
into a level-n+1 goal; never describes a merely visual change as a verified
win; Ring 6.3 handoff guarantees intact.
Core deliverable: after every observed level victory, the model can explain
why it believes the action won, identify what remains uncertain, and test that
explanation in the next level.

## Ring 6.6 — Duck's use contract
Goal: make Duck act from Virelai's evidence instead of acknowledging the
report and restarting from zero.
Win observed mode: adopt the win packet; restate the strongest transferred
goal; identify which part of the old winning condition might exist in the new
level; state a prediction; choose an action that tests it; state what result
would falsify the transferred rule.
No-win mode: adopt the Captain report as starting world model; choose one
named gap or unresolved causal relationship; explain why it is the most
valuable unknown; state a prediction; perform a relevant test; update or
reject the hypothesis from the result.
Required first-turn structure: Established / Current goal / Prediction /
Falsifier / Action. Small targeted inspections allowed; no full segmentation
dumps or re-discovery of what Captain completed.
Audit markers, based on observable response content, never emitted merely
because the prompt requested them: REPORT_ADOPTED, GOAL_SELECTED,
PREDICTION_STATED, FALSIFIER_STATED, TEST_ACTION_TAKEN,
TEST_RESULT_CLASSIFIED.
Success per game (yes/no): used a specific Captain finding; chose a reported
gap or transferred win goal; stated a prediction; stated a falsifier; action
actually tested the prediction; updated the hypothesis from the result.
Primary score is contract compliance; game score secondary until reliable.

## Ring 6.7 — Persistent memory
Goal: knowledge accumulates across lives and levels without merging unrelated
objects.
World-level memory (whole game): legal action meanings; movement grammar;
verified mechanic types; win theories; failed theories; cross-level
correspondences; proven falsifications.
Level-level memory (across lives in a level): object identities; positions;
target coverage; lever-effect maps; counter state; navigation history;
unresolved targets.
Life-level scratch (may reset on death): current route; immediate action
sequence; temporary animation state; short-lived object positions.
On death: preserve level knowledge; reset only life-local state; record how
the death occurred; do not rediscover every object.
On level advancement: preserve mechanics, win theory, causal rules; preserve
the completed level as an immutable snapshot; reset level-specific positions
and object identifiers; create tentative cross-level correspondences; require
evidence before declaring two cross-level objects equivalent.
Consolidation: longer probing improves evidence depth rather than inflating
records. Track stable object identity; observations per role; contradictory
evidence; duplicate candidates; merged identities with reasons; level and life
provenance per observation.
Success: death does not erase same-level knowledge; level advancement does not
erase the winning explanation; level-specific objects are not blindly carried
into new layouts; duplicate identity counts fall or stay bounded during longer
probing; evidence per consolidated object grows with probe length; Duck
receives a coherent history, not disconnected snapshots.

## Testing rhythm (all rings)
1. Deterministic unit and replay tests. 2. One or two known fixtures locally.
3. A small fixed Kaggle sample. 4. Inspect actual reports and Duck responses.
5. Full 25-game suite only after the ring's exit condition passes.
Fixed fixtures: vc33 (Captain click win + transfer); ls20 (Captain nav win +
transfer); ft09 (weak initial report, open click exploration); one difficult
navigation world with no observed win; one world with a life loss to test
memory boundaries.
Throughout: ontology, model settings, and unrelated field-card wording stay
fixed. The ladder: faster evidence -> explain observed wins -> make Duck test
the resulting goals -> preserve verified knowledge across the full world.

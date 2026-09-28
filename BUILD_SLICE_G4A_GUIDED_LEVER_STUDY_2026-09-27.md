# Build slice: G4-A guided lever study

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat), signed
**Rulings implemented (Director, 2026-09-27):**
- "A direct and explicit target for the Duck, then allow the Duck to execute it as needed."
- "G3 is scripted and G4 becomes stated targets."

**Base:** `8cfb782`. Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.
**Plan:** `BUILD_PLAN_G4_CLICK_COMPLETION_v2_2026-09-27.md`.

## Thesis

G4-A states one target and one closure test, and lets Duck choose every action. The controller
records each action, reads lever runs out of Duck's own presses, applies the counter mask, and
accepts only what the record supports. It never picks Duck's next move.

## What changed

| File | Change |
|---|---|
| `inference/framework/g4_guided.py` (new) | `LeverRun`: one run of consecutive same-click presses on one lever, with its confirmation tail. A null is confirmed by one more null. A period-N recurrence is confirmed by N more presses that retrace the recorded states; a mismatch is `DIVERGED`, never hidden. Statuses: RUNNING, CONFIRMING, CONFIRMED, DIVERGED, INTERRUPTED, BROKEN. The class comes from the lever's own run: ABSORBING, TOGGLE, CYCLE, RECURRENT or DIVERGENT. |
| `virelai_gates.py`: `_LeverStudyTarget` replaces `_LeverOrbitTarget` | Same gate id (`G4.2-LEVER-ORBITS`), product type (`LeverOrbitSet`) and Phase-1 payload fields. The S1 hold and the `8cfb782` boundary release therefore carry over. The card states the target, done-when, rules and per-lever status. The capability is `GUIDED_ACTION`: it admits any one valid action, with an optional `intent`. Answers may be given for any confirmed lever, in any order. At most 3 answer templates appear on the card, to keep it inside the 24,000-character context budget (5 levers measured at about 7,400 characters). |
| `virelai_gates.py`: machine validation | Guided capabilities accept `probe_token` plus an optional `intent`. The embodied `pilot_intent` path is unchanged. `ProbeEnvelope` gains an `intent` field. |
| `virelai_gates.py`: registry | The G4.2 contract is rewritten as `G4A-GUIDED-LEVER-STUDY-v1`. The G4.3-LEVER-LIMITS contract is unregistered, so the router never opens it. Its adapter class and `g4_limits.py` remain as port source for G4-B. |
| `inference/agent/tool_agent.py` | Three prompt passages tell Duck that a `GUIDED_ACTION` capability means the target is binding and the move is Duck's own. |

## Audit rules (what the record must show)

- A lever press is the lever's exact listed click (action and coordinates), as shown on the card.
- A run is a sequence of consecutive presses of one click. The following end an open run, recorded
  as `BROKEN` and kept as evidence:
  - any other action;
  - a board that changed between presses, for example a reset;
  - switching levers.
- A boundary during a run gives `INTERRUPTED`. The lever is released from pending, as in `8cfb782`,
  and Duck may re-study it on the same level. A level change closes the level's study.
- Presses after a confirmed run are recorded and do not rewrite the run.
- An explanation before confirmation is refused, with the reason stated.

## Tests

New file `tests/test_g4_guided.py`, 10 tests:
- the card and Duck's choice of lever order;
- **mixed absorbing and toggle levers complete in either order**, the regression for the G4.3
  continuity finding (the scenario the finding reproduced as failing on `8cfb782`);
- toggle confirmation needs one full extra period;
- divergence is recorded;
- another action ends a run and keeps its evidence;
- switching levers ends the run;
- a reset starts a new run instead of raising;
- an early explanation is refused;
- presses after confirmation leave the run unchanged;
- answers can be given in any order.

Rewritten:
- **`tests/test_g4_phase1_boundary.py`:** the four boundary cases under guided semantics.
  - The real vc33 Kaggle segment is replayed as Duck-chosen actions.
  - Every masked address matches the recorded one.
  - E0004 correctly stays unconfirmed, since the real run never confirmed it.
  - The level change closes the level's study with no deadlock.
- **`tests/test_g4_reactions.py`:** the G4.1 → G4-A handoff now presses, confirms, explains, and
  ends SATISFIED.

Removed: three gate-level G4.3 routing tests in `tests/test_g4_limits.py`, since that gate is
retired. The study-level G4.3 tests stay.

**Suite:** 384 passed, 1 skipped (cloud, Python 3.12). Ruff is clean on every changed file.
Mac confirmation is owed before commit.

## Evidence class

- **Direct:** code, tests, and the replay's address fidelity.
- **Not yet observed:** any live model acting under a guided G4 target.

— Claude, Alpha build seat, 2026-09-27

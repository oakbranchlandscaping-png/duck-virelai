# Build slice R9-R08: memory stage M-2, the controller executor

**Revision label:** `R9-R08`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Governing design:** `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` §5.5 (the executor) and §10 (T6).
**Rulings:** D2 (G0–G3 run by the controller), D5 (G3 inherits G2's total nulls).
**Laws:** M8, and "one frame in, one action out".
**Base:** `ee826ab` (R9-R07). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## The result in one line

The production agent carries ft09 from G0 through G3 closure (five levers, inventory accepted)
with **zero model calls**. It takes **72 actions** in about **12 seconds** offline. The live v2 run
spent 121 actions and about 80 minutes, and never closed G3. Duck's first turn comes at G4.0, with
a one-paragraph handoff.

## How it works

Before every analyzer turn, `ToolAgent.analyze` asks the gate machine who owns the next step.

- **Controller-owned.** The step is either a gate answer rendered from certified state, or
  **exactly one** bound action. The action goes through the same recording path Duck's actions use.
  `analyze` then returns, and the solver reads the new frame and asks again. No plan is queued, and
  no model is called.
- **Duck-owned.** Everything else goes to Duck: a normal model turn follows. If the controller
  stopped for a reason, Duck's prompt carries a handoff section that says what the controller did
  and why it stopped.

| File | What |
|---|---|
| `inference/framework/controller_executor.py` (new) | **Pure ownership logic.** `next_owned_step(machine)` decides who owns the step. `controller_answer` renders G0, G1, G2 and G3 answers from certified fields. `wake_reason` checks the stop-and-wake conditions. It does no IO. |
| `inference/agent/controller_turn.py` (new) | **The agent side.** It submits answers, or takes one action through `_gate_probe_begin` / `_gate_probe_record` with `executor: CONTROLLER`. It writes a turn-ledger row, appends a `CONTROLLER` transcript section, and holds the session's wake and handoff state. |
| `inference/agent/gate_artifacts.py` (new) | Artifact writing, moved **unchanged** out of `tool_agent.py`: probe outcome, gate event, frames, answer record. Duck and the controller share it. Answer records now carry `executor`. |
| `inference/framework/g3_inheritance.py` (new) | **D5.** `inherited_total_nulls` maps each member to the G2 click that changed **no cell at all** on it, where every G2 click on that member was null. `G2NullInheritance.apply` records these at the G3 roster head as scoped nulls citing G2's evidence (actor `G3_INHERITED_G2_NULL`) instead of re-clicking. |
| `virelai_gates.py` | `CyberneticGateMachine(g3_inherits_g2_nulls=True)` and `machine.protocol`. `_LeverTarget` reads its roster through `_roster_after_inherited_nulls()`. `CounterGateMachine.record_trigger` delegates to the pure `counter_verification.trigger_record`, which is an extraction, not a change. |
| `tool_agent.py` | `controller_executor_enabled` (default off). Before the prompt is built, `analyze` calls `run_controller_turn`, and the prompt carries the handoff section. Also three extractions: `_apply_step_result`, `_record_gate_answer` and `_request_model_metadata`. Probe envelopes carry `protocol`. |
| `solver.py` | Gated mode turns the executor on. **`VIRELAI_CONTROLLER_EXECUTOR=0`** turns it off: the escape hatch for a live run. |
| `record_replay.py`, `tools/record_from_artifacts.py` | A record carries the protocol it was made under, taken from the envelopes' stamp. A record without one predates D5 and replays with re-clicked nulls, so both committed ft09 fixtures replay as before. Replay also applies the answers that come after the last action. |
| `card_builder.py` | `world_budgets` is now public, because the executor uses the same numbers as the card. |

## What the controller owns, as built

| Step | Owner | How |
|---|---|---|
| G0 action metadata | CONTROLLER | The template, with the epistemic limit stated. |
| G1 pointer ego (CLICK) | CONTROLLER | The POINTER_GOD_MODE template, as the gate derives it. |
| G2 search | CONTROLLER | The first untried ranked object. |
| G2 label and frozen prediction | CONTROLLER when the trigger record is EVERY_TRANSITION or EFFECTIVE_TRANSITIONS_ONLY | Trigger = the record's class. COUNTER_REWRITE is predicted on the template's certified action. The prose is rendered from the counts, and marked as controller-rendered. |
| Bound G2 and G3 probes (demonstration, sweep, confirmation) | CONTROLLER | `actions[0]` when the probe binds exactly one action. |
| G3 dossier | CONTROLLER | Rendered from `effect_summary`, with counter exclusion stated. |
| G3 inventory | CONTROLLER when nothing is ambiguous | The template's certified entity lists. |
| G4 onward, NAV and HYBRID worlds, multi-action probes, a refused answer | DUCK | Unchanged. |

**Stop-and-wake conditions.** Each hands exactly the next step to Duck; the controller resumes when
it owns a step again. They are:
- a boundary (level completed, game over, done);
- the frozen G2 prediction contradicted, on the event where it was graded;
- G2 rejecting its candidate;
- a gate UNRESOLVED or REOPENED;
- a G3 confirmation CONTRADICTED or BOUNDARY_DEFERRED;
- ambiguous or unresolved attribution, or a boundary inside attribution;
- the counter with two ticks or fewer left;
- the gate refusing the controller's action;
- the environment not executing it.

## Measured (T6, offline, `tests/test_memory_m2.py`)

| | ft09 live v2 (Duck) | ft09 offline (controller) |
|---|---|---|
| Model calls through G3 | ≈ 130 | **0** |
| Actions | 121, G3 not closed | **72**, G3 closed |
| G2 actions | 57 | 57, identical to Duck's live search, click for click |
| G3 actions | 64 (54 of them re-clicked G2 nulls) | 15: 10 sweep clicks and 5 confirmations; 54 nulls inherited |
| Wall time | ≈ 80 min | 12.3 s offline for the agent (the environment step not included) |
| Gate answers | 5 Duck answers (3 refusals) | 9 controller answers, 0 refused |

The ft09 world here is the v2 record's law, continued: the 5 tiles the run saw respond toggle and
tick the bar, and everything else is null. It is a hypothesis about the tiles the live run never
reached, stated as such in `tests/ft09_world.py`.

## Tests (`tests/test_memory_m2.py`, 18 new)

- **T6.** Zero model calls through G3 closure. The model mock records its one attempted call, at
  G4-REACTIONS, and that prompt carries the handoff.
- **One action per turn.** 72 environment calls, 72 envelopes and 72 CONTROLLER ledger rows, each
  with zero model requests. Every envelope, and all 9 answer records, carry `executor: CONTROLLER`
  and the protocol stamp.
- **Duck's live G2 search is repeated exactly.** The 54 inherited nulls are never re-clicked.
- **The run replays offline.** The record is built from the run's own artifacts and replays 72
  steps under the recorded protocol to G4-REACTIONS.
- **Wake and resume.** A wake hands exactly one step to Duck, with the reason in the prompt; the
  controller then resumes.
- **Ownership.** NAV worlds and G4 belong to Duck. An OPEN trigger record is Duck's. A refused
  answer hands the gate to Duck.
- **Each stop-and-wake condition fires** in a synthetic case (8 parametrised, plus candidate
  rejection and budget). A contradiction graded on an earlier event does not re-fire.

**Amended:**
- `test_bounded_cards`: the full-sweep card test runs under both protocols. Pre-D5, 64 clicks.
  Under D5, 10 clicks with 54 inherited.
- `test_memory_m0`: the turn ledger records the new `controller_handoff` section.

**Suite:** cloud **449 passed, 1 skipped**: 450 tests, which is 431 + 18 new + 1 new
parametrised case. Ruff is clean on every changed file; the 7 findings in untouched files predate
this build. **Mac expected: 450 passed.** The cloud's one skip needs an artifact that exists only on
the Mac.

## Ratchet

| | Before (R9-R07) | After |
|---|---|---|
| `ToolAgent._run_python_tool` | 457 | **420** |
| `ToolAgent.analyze` | 423 | **414** |
| `tool_agent.py` | 2,910 | **2,861** |
| `virelai_gates.py` | 5,827 | **5,803** |
| `_LeverTarget.next_probe` / `record_outcome` | 98 / 301 | 98 / 301 |
| `CyberneticGateMachine.__init__` / `_LeverTarget.__init__` | 35 / 24 | 37 / 25 |

All new logic lives in new modules. The two tier-violating files and the two largest functions
shrank.

## Deviations from DESIGN v2, for ratification

1. **An OPEN trigger record wakes Duck** instead of the controller predicting COUNTER_SILENT "on
   the next dead click". The record is OPEN only while no transition has changed nothing, so no
   known-dead action exists; picking one is a choice, not a computation. On ft09 the record was
   EFFECTIVE_TRANSITIONS_ONLY (54 nulls first), so this did not arise.
2. **The counter-REOPEN wake is inert.** After G2 the gates mask the counter and ignore it
   (`MASK_AND_IGNORE_AFTER_G2`), so no REOPEN signal exists to wake on. A gate status of REOPENED
   or UNRESOLVED does wake Duck.
3. **There is no wall-time or action-count wake yet.** The machine knows neither budget; only the
   bar is wired. The M-4 lives rule is the place for them.
4. **There is no END owner.** Termination stays with the solver loop, which already stops on
   boundaries. R9-I02 (clean planned stop) stays open.
5. **The observer's actor label stays `DUCK`** for controller actions. Downstream observer code
   treats "DUCK" as "the agent" (as opposed to SYSTEM_RESET). The executor is recorded on the
   envelope, the answer record, the ledger and the transcript instead.

## What this does not do yet

- **The orientation turn (M-3).** Duck's first turn is simply G4.0 with the handoff.
- **The G4 economy (M-4).** Duck still answers and presses through G4.
- **Live.** The executor is offline-proven on one world (ft09) under a continued-law hypothesis. The
  first live run is the M-5 package.

— Claude, Alpha build seat, 2026-09-29

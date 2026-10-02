# Mine: controller-first action boundary

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Type:** repository and doctrine mine; no implementation claim  
**Current Director ruling:** Duck takes an environment action only when Virelai's controller code
cannot lawfully compute that action.

## Result

The requested boundary is already the ratified memory law M8 and already has working production
infrastructure. The recent ls20 v7 delay came from an incomplete NAV extension that bypasses that
boundary at G0, G1 and G2. This is a regression in ownership coverage, not a reason to invent a new
agent architecture.

The governing operational rule is:

> **Controller by default; Duck by demonstrated necessity.** If the active gate binds one exact
> action, or deterministic evidence and a proved planner select one lawful next action, the
> controller executes it and records the result without a model call. Duck receives a turn for a
> hypothesis, explanation, prospective prediction, a choice between non-equivalent experiments,
> or an unexpected state the controller cannot resolve. A Duck explanation turn does not grant
> Duck ownership of the following bound action.

This preserves the project's intelligence claim. Virelai conducts repeatable procedure and keeps
the record. Duck converts evidence into an internal model, chooses where genuine judgment remains,
and explains what the model means.

## Direct repository evidence

### Ratified doctrine

`DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` states:

- M8: “Duck spends turns only where judgment is needed.”
- A move the controller can compute is executed by the controller, one action at a time.
- Duck is woken for hypotheses, explanations, non-mechanical predictions and choices between
  non-equivalent experiments.
- The ownership table is intentionally adaptable as evidence shows where judgment is needed.

The same design records the Director's earlier ruling: “The controller should execute scripted
moves when possible.” It explicitly notes that NAV G1 probes are scriptable, although NAV was
shelved when that version was written.

### Working controller executor

`BUILD_SLICE_MEMORY_M2_CONTROLLER_EXECUTOR_2026-09-29.md` and the production
`controller_executor.py` / `controller_turn.py` establish the reusable machinery:

- ownership is checked before constructing a model prompt;
- one controller action passes through the same probe validation, environment step, frame record,
  evidence record and ledger path as a Duck action;
- a new frame is read before ownership is checked again;
- unexpected outcomes stop and wake Duck;
- controller actions and answers are explicitly attributed in artifacts.

The M-2 offline ft09 rehearsal traversed G0 through G3 closure in 72 environment actions and zero
model calls. The production NAV v3 run later executed 178 of 199 probes through the controller.
These are direct demonstrations that the executor is real and materially reduces runtime.

### Captain and Golden prior art

The separate deterministic Golden solver supplies the procedures that belong below Duck:

- `golden/captain/opening.py` deterministically presses each offered non-coordinate action twice in
  consecutive pairs. This is the Delphi opening.
- `golden/captain/sweep_click.py` deterministically clicks the visual roster.
- `golden/captain/nav_lattice.py` and `nav_sweep.py` derive bearings, stands, routes, contacts and
  bounded unreachable certificates from the record.

Ring 9 has already ported the relevant G3 NAV terrain and reachability mechanisms into
`nav_route.py` and the G3 adapter. No game-engine implementation is needed or appropriate.

## The current ownership defect

`controller_executor.next_owned_step` first classifies the world. For NAVIGATION and HYBRID it
immediately calls `_nav_step`, before the generic controller handling for G0, G1 and G2.

The current `_nav_step` owns:

- G3 route and contact actions when `planned_nav_step` returns a plan;
- selected G4 NAV run and prediction actions.

It explicitly returns Duck for every other NAV gate. The consequences are:

| Gate | Current NAV owner | What is actually computable |
|---|---|---|
| G0 metadata | Duck | Entire answer is derived from the action roster. |
| G1 Delphi probes | Duck | Every probe envelope binds exactly one action. |
| G1 explanation | Duck | Correct: identifying and explaining the ego is semantic judgment. |
| G1 demonstration | Duck | The accepted prediction binds exactly one action; controller can execute it. |
| G2 collide sweep | Duck | Target is bound; route choice lacks a shared G2 deterministic planner today. |
| G3 collide sweep | Controller when a route exists | Already implemented. |
| G3 reachability explanation | Duck | Correct: controller supplies the certificate; Duck states the scoped meaning. |
| G4 lever runs | Controller when a route exists | Already implemented. |
| G4 hypotheses and explanations | Duck | Correct. |

`tests/test_memory_m2.py::test_navigation_worlds_and_the_orientation_turn_belong_to_duck` freezes
the old blanket NAV rule. It should be replaced by step-specific ownership tests. World type alone
must not decide that Duck is needed.

## How this produced the v7 delay

The v7 ls20 run took nine environment actions but invoked the model 34 times across 21 analyzer
turns. Approximately 70% of the 2,698-second behavior window was spent on turns that executed no
action. One unbounded request generated for 900 seconds before timing out.

Every G1 probe action had already been selected by the gate. Duck was nevertheless asked to inspect
the board and decide to perform that prescribed action. After its G1 explanation was accepted, the
next card did not visibly retain the complete learned law, so Duck began re-deriving the ego before
executing the already-bound demonstration. The controller eventually verified the right result, but
the division of labor was backwards.

The eight Delphi actions are not the expensive part. Model deliberation around those actions is.

## Superseded historical instructions

Two older documents reflect the architecture before the controller executor and NAV router:

- `NORTH_STAR_VIRELAI_DUCK_HYBRID_v1_2026-09-15.md` says Duck remains responsible for action
  selection within the workflow.
- `BUILD_SLICE_DUCK_PILOTED_COLLISION_SWEEP_2026-09-20.md` assigns embodied route choice to Duck and
  explicitly says the deterministic Golden route planner had not yet been ported.

The second document correctly described its build at the time, but its stated missing prerequisite
has since been built for G3. Both are historical context. They do not override the later ratified M8
design or the present Director ruling.

## Required repair sequence

### Slice A — G0/G1 NAV ownership correction

1. Let generic G0 handling run before the NAV branch. The controller submits the metadata answer.
2. In active G1, let the controller execute any exact one-action probe capability.
3. At `ANSWER_REQUIRED`, hand one bounded semantic turn to Duck with a compact controller-derived
   transition table. Duck identifies the ego, describes every observed action law, states
   alternatives and freezes a prospective prediction.
4. At `DEMONSTRATION_REQUIRED`, return ownership to the controller. It executes the exact action
   named by Duck's accepted prediction and records the comparison.
5. Carry the accepted law and frozen prediction visibly until the demonstration is graded. Never
   replace them with a plan to re-derive them.

Expected ls20 G1 cadence: zero model calls for G0 and the eight Delphi actions; one Duck call for the
ego explanation; zero model calls for the demonstration action.

### Slice B — shared NAV pursuit for G2

1. Extract the proved G3 route/contact calculation into a gate-neutral controller service.
2. Feed it the closed G1 bearing map, demonstrated ego footprint, current ranked G2 target,
   demonstrated stands and refused edges.
3. Have G2 record the same `APPROACH` / `CONTACT_ATTEMPT`, floor and refused-edge evidence used by
   G3.
4. Execute a computed route step through `controller_turn.py` without a model call.
5. Wake Duck only when no lawful plan exists, evidence is ambiguous, a world delta invalidates the
   map, or the gate asks for a semantic counter explanation that cannot be rendered from certified
   state.

This is a port of existing G3 and Golden work, not a second navigation system.

### Slice C — enforce action ownership independently of semantic ownership

Introduce an explicit turn mandate:

- `EXPLAIN_ONLY`: Duck may inspect and submit the required answer but cannot step the environment;
- `CHOOSE_ACTION`: Duck may choose one action because the controller has recorded why it cannot;
- `CONTROLLER_ACTION`: no model request is built;
- `END`: stop cleanly.

This prevents a semantic wake, orientation turn or explanation request from accidentally giving Duck
control of a mechanically determined action.

### Slice D — bounded semantic inference

Once action ownership is repaired, bound the remaining Duck call by task:

- compact sufficient statistics instead of full-history rediscovery;
- one semantic deliverable per call;
- finite output ceiling;
- hard request cancellation aligned with the turn budget;
- accepted knowledge and the frozen prediction injected into the next card.

This is a safety net. It is not a substitute for the ownership correction.

## Acceptance tests before another Kaggle run

1. **NAV G0:** zero model calls; controller answer accepted.
2. **NAV G1 probing:** exact Delphi sequence; every envelope says `executor: CONTROLLER`; zero model
   calls through `ANSWER_REQUIRED`.
3. **NAV G1 explanation:** exactly one model call; no environment action is available during the
   answer mandate.
4. **NAV G1 demonstration:** controller executes the frozen action; G1 closes without another model
   call.
5. **Stable knowledge:** the demonstration card contains the accepted action laws and exact frozen
   prediction.
6. **NAV G2 routing:** a known route produces controller actions; a refused edge changes the next
   plan; no repeated unchanged `(stand, action)` pair.
7. **Honest wake:** removing the bearing map or producing ambiguity gives Duck one explicit
   `CHOOSE_ACTION` handoff with the reason recorded.
8. **Replay:** replay the v7 ls20 G1 frames through the new ownership policy and reach G2 with one
   semantic Duck turn rather than 34 inference requests.
9. **Artifact parity:** controller and Duck paths produce the same lossless frames, outcomes, gate
   events and evaluator-grade evidence.

## Supported conclusion

The repository supports a stronger and simpler boundary than the recent run used. Virelai should
own all mechanical probing, routing, repetition and verification it can compute. Duck should own
meaning and the residual decisions that code cannot settle. The immediate build begins with the
small G0/G1 ownership correction, then ports the existing NAV route planner into G2.

— **Sol**

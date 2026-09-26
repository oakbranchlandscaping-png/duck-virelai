# Build slice: Duck-piloted embodied object sweep

**Date:** 2026-09-20  
**Active source:** `variants/ring9-cybernetic-gates/`  
**Status:** Built and locally verified; live unconfirmed

## Purpose

Give navigation and hybrid worlds the same opening experiment as click worlds: make a ranked list
of visible objects, investigate them in order, and retain a result for each. Navigation has the
additional embodied work of piloting the ego to the object. Duck performs that piloting from the
ego and motion laws it established in G1; the controller retains the target and decides when the
target experiment is complete.

## Division of responsibility

The controller owns:

- the post-G1 visual-object roster and strict rank;
- one binding target at a time;
- the set of currently legal opaque embodied actions;
- the per-target step bound;
- advancement of the roster and the evidence record.

Duck owns:

- choosing the next opaque movement or interaction action from that legal set;
- using its demonstrated G1 ego law to approach the binding target;
- declaring each action as `APPROACH` or `CONTACT_ATTEMPT` before execution.

An approach move never counts as testing the target. The target remains binding until the trace
records one of four dispositions:

1. `TARGET_RESPONDED` — a changed cell intersects the target's bound footprint;
2. `BOUNDARY_DURING_TARGET_PURSUIT` — the adapter reports a terminal boundary;
3. `REFUSED_CONTACT_REPORTED` — Duck declared contact and the board had zero visible delta;
4. `PILOT_BUDGET_EXHAUSTED` — 24 actions elapsed without contact evidence.

The third result is deliberately labeled as model-declared, lower-strength evidence. It does not
claim that the controller independently reconstructed physical adjacency. The fourth records a
bounded failure; it does not prove the object is unreachable or inert.

## G1 to G2 handoff

G1 now retains its lossless transition outcomes and reconstructs the latest visible grid. When G1
closes, G2 is rebuilt from that post-probe frame rather than from frame zero.

For an embodied world, the handoff also carries Duck's ego footprint. An exact demonstrated
after-footprint is preferred. A declared prediction scope is retained as an explicit fallback when
the successful G1 predicate did not resolve an after-footprint. The binding source is written into
the G2 opening record so these evidence strengths remain distinguishable.

The navigation roster excludes components overlapping the bound ego and components classified as
structural fields. Click worlds retain the exhaustive component roster because their ego is the
coordinate-selecting hand and has no persistent grid footprint.

## Capability contract and records

For `PILOT_TO_CONTACT`, `next_probe` exposes:

- the binding target's stable member id, rank, anchor, box, integer, size, and shape family;
- the legal opaque actions;
- the required `pilot_intent` field;
- a capability token bound to the current gate revision and target.

The action call must contain exactly one legal action and the matching token. A stale token, a
different target, multiple actions, or a missing intent is rejected before execution.

`navigation_results` and the shared ranked frontier retain target id, rank, disposition,
attribution strength, evidence reference, number of pilot steps, changed target cells, and Duck's
declared intent. Counter discovery still examines every transition, including approach moves, so
scheduled bookkeeping can be detected before the first collision. Counter demonstration probes
do not consume object ranks.

## Verification

- Complete Ring 9 suite: **276 passed**, with 14 dependency warnings.
- Targeted counter, ranking, bridge, and G1 tests: **31 passed**.
- Targeted Ruff checks passed.
- Tests establish binding-target persistence, Duck-selected admissible actions, direct target
  response attribution, lower-strength refused-contact recording, ego/background exclusion, and
  post-G1 grid/footprint reconstruction.

These are implementation checks. No completed Kaggle trace has yet shown Duck using this embodied
pilot contract.

## Remaining hardening before a live checkpoint

This slice intentionally relies on Duck for route choice. It does not yet port Golden's
deterministic route planner or controller-derived contact line. Therefore a zero-delta contact is
only as reliable as Duck's prospective `CONTACT_ATTEMPT` declaration, and the 24-step disposition
means bounded failure rather than geometric unreachability.

The subsequent G2 reliability slice repaired the counter-boundary march, quiet-opening handoff,
and notebook runtime accounting. See
`BUILD_SLICE_G2_PRODUCTIVE_CLOSURE_AND_RUNTIME_2026-09-20.md`. Its frozen single-world ls20 package
is ready for an embodied live checkpoint but remains unuploaded.

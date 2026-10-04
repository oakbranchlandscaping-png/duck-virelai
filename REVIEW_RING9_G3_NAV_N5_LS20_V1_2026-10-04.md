# Review: Ring 9 N5 bounded G3 NAV ls20 v1

**Type:** `LIVE_RUN_REVIEW`
**Status:** partial pass; deterministic NAV execution advanced, semantic checkpoint bound failed
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04

## Verdict

N5 produced useful live evidence but does not close the NAV branch. The deterministic controller
owned all 49 environment actions, closed G0-G2, installed the complete counter mask, created the
full target roster before execution, made physical contact with ranked targets, and typed the
integer-3 region as floor through traversal. G4 remained closed.

The run then spent the remaining behavior budget at one G3 `TARGET_REACHABILITY` explanation. Duck
was asked for at most 40 words, but repeatedly consumed the full 4,096-token generation allowance
while restating and investigating controller-certified facts. The intended two-request repair bound
is local to one analyzer invocation and resets when the solver schedules the same checkpoint again.
It therefore did not bound the checkpoint across solver turns.

The final `G3_BUDGET_STOPPED` product correctly makes the incomplete run explicit, but three audit
fields are defective: `pending_target` and `last_accepted_evidence` are null, and
`eligible_roster_count` is 20 even though the exported ledger contains 16 eligible rows and two
role exclusions. These are artifact-construction defects; the scheduler and ledger retain the
missing facts.

## Execution identity

- Notebook: `stephenkaskin/taaf-virelai-ring9-g3-nav-n5-ls20-v1`
- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-ls20-v1`
- World: `ls20-9607627b`
- Source commit: `c636ba7`
- Package commit: `a54e0c6`
- Launch-record commit: `c7afd6e`
- Package manifest: `1afcbe631ad82b0af18100a881d3015c515a8f8045a906f53a683684fb3cde59`
- Source manifest: `d23f91d0bdd937c86e32b6938d6f61854941c6d026cb8db63e5f8d907db16cbd`
- Duration: 20m 2s
- Environment actions: 49 of 80
- Final state: `cancelled` at the 1,200-second behavior boundary
- Levels completed: 0/7; outside this checkpoint's grade
- Downloaded execution receipt: byte-identical to the packaged receipt

The benchmark summary attributes 16,049 generated tokens to the last completed environment-action
record. The turn ledger records the complete model use: 47,957 generated tokens, including 31,908
spent after action 49 without another environment action. The turn ledger is the relevant source
for diagnosing the semantic stall.

## N5 grading

| Criterion | Result | Direct evidence |
| --- | --- | --- |
| G0-G2 close and the complete counter becomes a mask baseline | **PASS** | The machine reached G3. G2 recorded the complete 84-cell two-row footprint, `11->3` by two cells per transition, period 42, and `LOCKED_AS_MASK_BASELINE`. |
| The G3 roster exists before target execution | **PASS** | `roster_populated_before_execution` is true. The target ledger contains 16 eligible rows plus two counter-role exclusions. |
| The controller owns computable action selection | **PASS** | All 49 environment actions were controller-owned. Duck executed zero environment actions. |
| Ranked NAV contact begins and produces evidence | **PASS** | E0001-E0004 were executed with `ENTERED`, `DISPLACED`, `REFUSED`, and `DISPLACED` contact outcomes. E0005 entered route evaluation. |
| Floor/wall typing is evidence-bound | **PARTIAL** | E0018 is directly typed `FLOOR` from ego traversal. No component received direct `WALL` evidence, so wall typing is ungraded. |
| Accepted unreachable rows persist until relevant evidence changes | **NOT EXERCISED** | E0005 received a controller certificate, but Duck never submitted the compact semantic answer. No `PRESUMED_UNREACHABLE` row was accepted. |
| Shared topology closes sibling targets without repeated model work | **NOT EXERCISED** | The first semantic key was never accepted, so the scheduler could not advance to a sibling and demonstrate reuse. |
| Every eligible row receives a terminal G3 disposition | **FAIL** | Ledger states: 3 `AMBIGUOUS`, 1 `ATTEMPTED`, 2 `G3-CLOSED`, and 10 `UNTOUCHED`; no G3 inventory was accepted. |
| A bounded run emits an explicit product and keeps G4 closed | **PARTIAL** | `G3_BUDGET_STOPPED` was emitted and `g4_legal_open` is false, but required audit fields are incomplete or mislabeled. |

This is a partial N5 pass. It validates deterministic ownership, counter masking, roster creation,
physical contact, floor evidence, and the existence of a controlled-stop product. It does not
validate N1 semantic acceptance, N2 terminal persistence, N3 sibling reuse, full G3 accounting, or
G4 opening.

## Direct behavioral observations

G1 took eight opening probes before Duck's ego explanation was accepted. Duck used five solver
turns, 16,049 generated tokens, and 399.874 seconds. Its accepted answer correctly described the
5x5 composite ego and the four five-cell translations; one later controller action demonstrated
the answer's prospective prediction and closed the gate.

G2 was entirely controller-owned after that handoff. It used three actions to establish and
demonstrate the counter law. Counter changes remained a mask baseline while G3 ran.

G3 used 37 controller actions. The target ledger preserved separate identity, visual type,
reachability and physics fields for all 16 eligible objects. Five rows were executed; E0005 was in
progress; ten remained untouched. Two counter components stayed excluded from the eligible roster.

For E0005/M0019, the controller retained a target-specific provisional certificate with closest
stand `[45, 49]`, one refused target-directed edge, no contact surface, explicit reopen conditions,
and `inertness_claim_permitted: false`. The certificate also retained farther open frontier edges.
That is consistent with N3's target-conditioned rule: the closest spent refusal may support a
provisional conclusion while farther experiments remain visible. Duck never accepted its meaning.

## Semantic-checkpoint failure

At G3, Duck received a roughly 7,100-token prompt with controller-certified fields and one task:
explain in at most 40 words why the target currently lacks a contact path, why that does not prove
inertness, and what could reopen the question.

The model produced eight unsuccessful Duck turns over 770 seconds before the final 12-second
no-step turn. Seven of those turns generated the full 4,096 tokens; another used two requests and
3,236 tokens. The transcript shows the model repeatedly reconstructing the task, asking which
target was meant even though the controller was authorized to fill target identity, and sometimes
issuing read-only inspection calls. It never called `gate_answer` for G3.

N1's bounded-repair implementation allowed at most two requests inside one analyzer call, but the
outer solver invoked the analyzer again with the same action number and gate state. The retry count
was not durable at the checkpoint level. Consequently, N4 never emitted
`G3_SEMANTIC_RETRY_EXHAUSTED`; finalization emitted `G3_BUDGET_STOPPED` only when the global behavior
budget expired.

## Controlled-stop artifact defects

Static inspection explains the three malformed audit fields:

1. `pending_target` is sourced only from `next_probe_capability()`. That capability is absent while
   the gate is `ANSWER_REQUIRED`, even though `scheduler.pending_reachability` identifies
   E0005/M0019.
2. `last_accepted_evidence` looks for `last_event` inside the full lifecycle snapshot. Full snapshots
   store `events`; only compact cards synthesize `last_event`.
3. `eligible_roster_count` copies the lifecycle journal's `entity_count`. That count includes
   controller-internal or role entities and is not the exported ledger's eligible-row count.

These defects do not erase the underlying scheduler or ledger evidence, but they prevent the N4
artifact from satisfying its stated audit contract.

## What the evidence does not support

- It does not show that the NAV contact planner is unable to continue; the model checkpoint stopped
  the controller before the next target.
- It does not validate an accepted unreachable classification or its later persistence.
- It does not validate sibling semantic reuse because no first understanding entered the cache.
- It does not establish a wall integer on this run.
- It does not complete G3 or authorize G4.
- Zero levels and zero score do not grade this checkpoint, whose declared scope ends at G3.

## Required next slice

Build N5.1 before another live run:

1. Persist the semantic-attempt count by gate, semantic key, target and world-state address across
   solver turns. After the permitted allowance, emit `G3_SEMANTIC_RETRY_EXHAUSTED` immediately and
   terminate the checkpoint cleanly.
2. Make the compact checkpoint operationally minimal. Supply the target identity directly and
   require the `gate_answer` tool for this handoff; do not invite board reinspection when all
   physical fields are certified.
3. Fill `pending_target` from scheduler pending state while an answer is required.
4. Derive latest lifecycle evidence from the full `events` arrays, and derive the eligible count
   from eligible target-ledger rows.
5. Add one regression that repeats analyzer turns without an environment action and proves the
   retry budget cannot reset.
6. Re-run the local focused suite, then use one short `ls20` live checkpoint. Success requires an
   accepted E0005 understanding followed by controller-only reuse on a sibling, or an immediate
   explicit semantic-exhaustion product within the declared allowance. A full level or win is not
   required.

## Build update

N5.1 was subsequently built in source. It makes the two-request allowance durable across solver
turns, exposes the bound target directly, requires tool use with thinking disabled and a 256-token
output cap, repairs the controlled-stop fields, and preserves semantic exhaustion through solver
finalization. See `BUILD_N5_1_BOUNDED_G3_SEMANTIC_SEAM_2026-10-04.md`. Packaging and live
confirmation remain pending.

— **Sol**

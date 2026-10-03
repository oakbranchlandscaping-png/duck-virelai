# Diagnostic: level-2 G3 stall in ring9-carry-vc33-v4 (read-only)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Follows:** `REVIEW_RING9_CARRY_VC33_V4_KAGGLE_2026-10-03.md` (committed `0ae1c7c`)
**Code read and run:** the shipped source, `fbea80c`
**Record:** the v4 live record (`tools/record_from_artifacts.py`, 47 transitions)
**Nothing was changed.** A scratch copy carried one probe edit, described below. It is not a fix.

## Method

1. I replayed the first 26 transitions (level 1) with `replay`.
2. I drove level 2 the way the live run did: the controller's own answers, and every recorded action through a freshly issued capability, recorded with `record_like_live`.

**Result: the replay reproduces the live state exactly.**
- Same action sequence, with no mismatch against the live record.
- Same final gate: G3-LEVERS, ANSWER_REQUIRED, no capability.
- The controller's inventory is refused with the live message, `G3 coverage cannot be reported with unbounded probe results: {'E0004': 'AMBIGUOUS', 'E0005': 'AMBIGUOUS'}`.
- `legal_move_status` reports legal (ANSWER).

## What happened in G3 on level 2

| Entity | Object (anchor) | Witness press | Confirmation press | Confirmation |
|---|---|---|---|---|
| E0004 | (16,0) | t33: 141 cells changed elsewhere | t34: 1 cell (counter only) | **CONTRADICTED** (effect gone) |
| E0005 | (24,0) | t35: 142 cells | t36: 141 cells, **but not the predicted cells** | **CONTRADICTED** (effect moved) |
| E0006 | (36,0) | t37: 173 cells | t38: 157 cells, the predicted remote cells | SUPPORTED, dossier by the controller |
| E0007 | (44,0) | t39: 158 cells | t40: 173 cells | SUPPORTED, dossier by the controller |

Both contradicted objects are **stateful levers**: a second identical press does nothing, or does something somewhere else.

**Why level 1 never met this.** On level 1, both levers' confirmations were SUPPORTED: E0004 at t7/t8 and E0005 at t9/t10, each changing 265 cells twice. G3's contradicted-confirmation path had never run live.

## Root cause

This is a code-level omission in the G3 adapter (`virelai_gates.py`, the confirmation branch of G3's outcome recording).

**Every other CLICK-phase route to AMBIGUOUS also records a *bounded ambiguity*.** Those routes are `AMBIGUOUS_EGO_MASKED` / `UNRESOLVED_ATTRIBUTION`, contact-attempt changes, and budget stops. All of them call `_bound_ambiguity(...)`. It writes the `virelai-g3-bounded-ambiguity-v1` record:
- `inertness_claim_permitted: False`;
- a `retry_condition`: reset, rebind, new action, or a new object.

**The contradicted-confirmation route alone moves the entity to AMBIGUOUS without bounding it:**

```
elif entity_id:
    journal.transition(entity_id, "AMBIGUOUS", ..., reason="prospective witness contradicted")
```

`_submit_inventory` accepts AMBIGUOUS entities only if they are bounded. So the inventory is refused, G3's enumeration is complete, no probe remains, and the gate is stuck.

**Scratch probe.** The same `_bound_ambiguity` call was added to that branch in a scratch copy, CLICK phase only. The replay then reaches the gate's designed path:
- the controller hands the coverage report to Duck ("G3 has bounded ambiguity: the coverage report is Duck's");
- the gate's own template is accepted;
- the inventory lists E0006 and E0007 as levers, E0004 and E0005 as ambiguous, and 10 objects as clean nulls.

**Correction to the v4 review.** The review called the AMBIGUOUS resolution "probably architectural". It isn't, for the unblocking part: the architecture already has the declared class (bounded ambiguity) and the Duck-owned coverage report. One branch failed to use them.

## Second defect: axiom A2 missed this deadlock

`legal_move_status` returns legal whenever an answer is demanded and a template exists. Here every answer the controller can form is refused at that revision, and no probe exists. Duck's turns then end at the time budget, 75 times.

This is the answer-side twin of R9-R20's D2:
- **D2:** waiting for an action that cannot be made.
- **This defect:** demanding an answer that cannot be accepted, with no probe left.

Either fix alone would have ended or unblocked v4 in minutes.

## Minor: level entry (I7)

On level 2, G0 was answered by Duck, not the controller. The level-completed boundary wake (`session.wake`) handed Duck the first level-2 turn before the controller's G0 answer. It was harmless here: Duck's G0 was accepted, and G1 and G2 were the controller's. But it is one avoidable model turn per level, and it is why I7 is not met as written.

## Proposed slice R9-R21 (code-level, test-first on the v4 record)

- **D4:** a contradicted confirmation in the CLICK phase records a bounded ambiguity, like every other CLICK-phase AMBIGUOUS route. **Test:** the v4 live record reaches an accepted G3 inventory, with E0004 and E0005 ambiguous and E0006 and E0007 levers.
- **D5 (A2):** a gate that demands an answer, offers no probe, and has refused the controller's answer at this revision is a no-legal-move state, unless the step is designed to be Duck's. Bounded-ambiguity coverage is one such step, and must stay legal. **Test:** the v4 deadlock state without D4 is illegal; with D4 it is legal and owned by Duck.
- **D6 (optional, I7):** the level-completed wake does not pre-empt controller-owned G0 and G1 answers at level entry.

## For the Chief Engineer (architectural, not blocking)

D4 unblocks the ladder, but it files **stateful levers as ambiguous**. On vc33's level 2, that is 2 of 4 real levers, and those two get no G4 study. Level 1's win came from studying such a lever (E0005, interrupted).

The question for a ruling: should G3 certify a **state-dependent lever** as its own class (responds, but not repeatably), with G4-A studying its orbit, instead of leaving it ambiguous? That changes what G3 claims, so it is not mine to decide in a work order.

— Claude, Alpha build seat, 2026-10-03

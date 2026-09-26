# G4.2 local validation review — vc33 v2

**Run:** `ring9-g4-orbits-vc33-openrouter-fast-rung-20260925-v2`  
**Model:** `qwen/qwen3.6-35b-a3b` through OpenRouter  
**Runtime:** 30 minutes 4 seconds  
**Final harness state:** cancelled at the configured soft deadline  
**Game result:** level 0/7, score 0, 16 executed actions  
**Review scope:** G4.2 repeated-activation infrastructure, not game-solving performance

## Decision

This run is a **diagnostic partial pass for G4.2 and a failed end-to-end checkpoint**.

The first G4.2 activation behaved correctly: the controller selected the confirmed lever E0004, issued its exact bound ACTION6 click at row 24, column 60, removed the one-cell counter update, and classified the remaining 264-cell world change as `NOVEL_STATE_REVEALED`. The controller therefore continued rather than falsely stopping after one activation.

The checkpoint did not reach a second activation. Updating the deferred G2 counter monitor replaced the active G2 memory product. `TargetJournal.put()` treats replacement as invalidation of that product and every descendant, so the accepted G3 inventory and both accepted G4.1 anatomy products became stale. Routing returned to G3 even though the G3 adapter still held its completed sweep and accepted inventory. Duck then received a contradictory G3 card: the inventory was already accepted, no probe was admissible, but the gate demanded another answer. Its repeated reports of a system deadlock accurately described the interface it was given.

## Executed evidence

The artifact logs directly establish:

- G0 accepted the available ACTION6 coordinate interface.
- G1 assigned `CLICK_GOD_MODE` and described ACTION6 as coordinate selection.
- G2 identified and masked the counter.
- G3 completed the ten-target click sweep.
- G3 recorded E0004 and E0005 as confirmed levers and emitted an aggregate inventory.
- G4.1 emitted effect anatomy answers for E0004 and E0005.
- G4.2 executed `G4.2-LEVER-ORBITS:E0004:1` at row 24, column 60.
- The raw transition changed 265 cells. One cell was the known counter update; the masked orbit contained 264 world changes.
- The masked world address changed from `3c6adb89defea2c7` to `c4121f4e8d15c35c`.
- The disposition was `NOVEL_STATE_REVEALED`, with no terminal boundary and no recurrence.
- Three visual entity identifiers appeared in the orbit record: E0023, E0024, and E0025.
- The run stopped at its configured deadline rather than hanging indefinitely. This validates the soft-deadline repair made after v1.

## G4.2 exit-criterion grade

| Criterion | Grade | Evidence |
|---|---|---|
| Enter G4.2 only after G3 and G4.1 products exist | Pass | G3 inventory plus two G4.1 answers precede event 16 |
| Bind the known lever intervention | Pass | E0004, ACTION6 at row 24, column 60 |
| Mask the entire known counter | Pass | 265 raw changes became 264 orbit changes |
| Recognize a previously unseen masked state | Pass | `NOVEL_STATE_REVEALED` and a new world address |
| Continue after novelty | Interface intent passed; execution incomplete | No stop product was emitted, but routing regressed before another action |
| Repeat until masked null or exact recurrence | Not tested | Only one orbit activation executed |
| Describe the observed orbit in Duck's own mechanism language | Not tested | No G4.2 answer was reached |
| Complete all known lever orbits | Not tested | E0005 was never entered |

## What the evidence does not support

- It does not establish E0004's period, fixed point, null boundary, or complete orbit.
- It does not establish E0005's repeated-activation behavior.
- It does not validate G4.2 on NAVIGATION or HYBRID worlds.
- It does not show that E0023-E0025 are independent new levers. They are new visual entities produced by the activation and require G3-style interaction evidence before typing.
- It does not measure game-solving ability; no level-clear objective was assigned to this checkpoint.
- Duck's prose about a deadlock is not itself proof. The controller state and dependency invalidation explain and corroborate it.

## Root cause

`CyberneticGateMachine.monitor_counter_transition()` calls the G2 adapter's `_sync_product()` whenever the deferred counter monitor emits an event. `_sync_product()` calls `TargetJournal.put()` even when the stable counter model and mask are unchanged. Replacing the active G2 product invalidates G2 and all registered descendants. The adapters retain their internal accepted answers, so the router and adapter state disagree.

The problem is a product-lifecycle error, not a reasoning failure and not a G4.2 orbit-classification error.

## Repair completed September 26

The design was tightened after review: there is no later counter-monitor obligation. G2 now emits a stable mask baseline, and later counter behavior is actively ignored. A regression test closes G0-G4.1, performs one novel G4.2 activation, preserves the G2/G3/G4 products, and exposes activation two. The remaining live target is two or more consecutive E0004 activations on vc33.

## Interpretation

The central G4.2 bet survived its first live contact: the system used the known lever, subtracted the counter, addressed the resulting world state, and recognized novelty. The run exposed the exact next infrastructure defect: stable knowledge products and ongoing monitoring records are currently coupled. Separating them is necessary for the world model to accumulate without reopening already answered gates.

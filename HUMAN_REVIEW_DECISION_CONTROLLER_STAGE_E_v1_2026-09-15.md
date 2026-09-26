# Human Review Gate — Virelai Decision Controller

**Date:** 2026-09-15  
**Source:** fixed Ring 8 gated-delivery archives  
**Action policy:** none; replay-only

The production bridge now passes the scripted end-to-end trace. Before a live
model run, the selected focus must be judged against observable game reality.

## vc33

**Primary focus:** `TRANSFER`  
**Reason:** a level-1 win exists and level 2 requires a persistence/change comparison.  
**Evidence:** transition 13, the observed level-1 winning boundary.  
**Obligation:** name what persisted, changed, and requires reconfirmation.

**Alternatives:**

1. `AUTONOMY` — separate the repeated visible process at transitions 14–22
   from targeted action effects.
2. `ROLE_DEPTH` — current-level effects exist, but the admitted model lacks an
   exact discrete before/after state edge.

**Assessment:** structurally reasonable. Transfer is correctly first after the
level change, while the two alternatives expose the important current-level
questions rather than claiming that the earlier mechanic still holds.

## ft09

**Primary focus:** `TRANSFER`  
**Reason:** a level-1 win exists and level 2 requires a persistence/change comparison.  
**Evidence:** transition 20, the observed level-1 winning boundary.  
**Obligation:** name what persisted, changed, and requires reconfirmation.

**Alternative:** `CONTROL` — no current-level observed action-linked mechanic
has passed admission.

**Assessment:** epistemically safe. It remembers the win without asserting its
cause and immediately exposes that the new level lacks an admitted control
model. The focus is useful only if the subsequent transfer record identifies
concrete recurring objects; that remains a live-quality question.

## ls20

**Primary focus:** `CONTROL`  
**Reason:** no observed action-linked mechanic is admitted for the current level.  
**Evidence:** none cited.  
**Obligation:** identify a controlled subject or preserve control as unknown.

**Assessment:** honest but weak. The archive contains only seven transitions
and the semantic compiler admitted no mechanics. The controller refuses to
invent a stronger question. A live run must show that this focus leads Duck to
identify control efficiently rather than merely restating uncertainty.

## Engineering trace already passed

The local end-to-end fixture demonstrates:

```text
focus
→ prospective decision
→ exact declared action
→ observed transition
→ scoped SUPPORTED comparison
→ persisted revision
→ later inspection-only retrieval by Duck
```

A malformed first call consumed zero actions; the corrected call executed once.
The complete regression suite is **155 passed**.

## Decision

The machinery is ready for a local/API live-quality pilot, not yet a Kaggle
launch. The next pilot should use `vc33`, `ft09`, and `ls20`, preserve all
controller artifacts, and grade focus usefulness, action-contract correction,
scope correctness, outcome correctness, and later retrieval. No score claim
should be made from that pilot.

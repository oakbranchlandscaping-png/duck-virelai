# Build report: G4 NAV lever targeting and comprehension

**Type:** `BUILD_REPORT_G4_NAV_BRANCH` · **2026-10-01**
**Builder:** Sol (Alpha build seat), signed
**Source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`
**Status:** locally complete through G4-C; live NAV validation pending

## Result

The NAV branch now follows the same scientific ladder as CLICK while using an embodied actuator:

```text
G1 verified displacement evidence
-> deterministic control map
-> route over demonstrated stands
-> one-step frontier experiments
-> target-bound footprint contact
-> G3 lever witness and confirmation
-> G4.1 effect anatomy
-> G4-A repeated contact orbit
-> G4-B relations predictions
-> G4-C new law prediction
```

Approach actions remain lossless observations and update the entity, counter-baseline, life, and
transition records. They never count as lever activations and never grade lever predictions. Only
the terminal predicted-footprint contact transition enters a lever orbit or prediction grade.

## Built contracts

- `NavControlMap` admits a bearing only from structured, observed G1 displacement evidence. It
  never assigns directions from action numbers or parses direction words from prose. ACTION5
  remains unresolved unless evidence shows stable ego translation.
- `NavLattice` routes only through ego anchors actually occupied. It can take one explicit step
  beyond the demonstrated graph as a frontier experiment; it cannot plan a fictional route across
  unknown ground.
- `ContactProcedure` and `InterventionRef` bind a NAV intervention to the target entity. Two levers
  reached with the same final movement action remain two different interventions.
- `ContactEpoch` separates route evidence from the terminal contact evidence and records the stand,
  final action, and observed contact disposition.

## Gate behavior

### G3 NAV

The controller now selects evidence-bounded approach and contact actions. It sends the existing
`pilot_intent` contract through the same capability and recording path used by Duck. A contact
attempt with no target, ego, or ground residue after counter partition creates production
`refused_contact` evidence. A completed scoped-null contact advances the roster. Approach length
does not create an inertness or unreachable verdict, and the former 24-step automatic closure no
longer does so.

A confirmed BODY lever is stored as a target-bound NAV procedure with its procedure id, entity id,
target geometry, allowed movement actions, level, life, and last observed final action. G4 receives
this intervention identity instead of a raw shared movement token.

### G4-A

The controller routes to each confirmed NAV lever and repeats its contact procedure. Approach
transitions are recorded as `NAV_APPROACH` with `orbit_advanced: false`. A terminal
`NAV:CONTACT_ATTEMPT:<entity>` transition alone advances that entity's run. The existing masked
null, recurrence, confirmation, divergence, death, and level-boundary machinery is reused.

### G4-B and G4-C

Duck freezes predictions against the listed target-bound NAV intervention. The controller resolves
that intervention into approach actions followed by a contact action. Approach frames leave the
prediction pending; the contact frame is graded against the counter-masked lever regions. The
same rule applies to the G4-C novel law test. Novelty and split-outcome keys therefore retain the
target identity instead of collapsing all levers reached by the same movement action.

## Direct verification

- Dedicated NAV foundation and gate tests: **11 passed**.
- Focused NAV plus CLICK regression set: **48 passed**.
- Broad suite: **480 passed** after the card-flatness regression was found and repaired.
- Seven modules could not collect and one harness test could not run in this local environment
  because the external `taaf` package is absent. This is an environment limitation, not a passing
  result.
- Python compilation and `git diff --check` pass.
- The broad suite initially exposed a real G4-A prompt-size regression caused by duplicating the
  intervention in every card row. The duplicate was removed and the flatness test then passed.

## Evidence boundary

The local tests directly support contract behavior, CLICK preservation in the exercised suites,
and route/contact separation through G4-C. They do not show that ls20 supplies enough G1 movement
evidence for every required bearing, that every live target is reachable, or that a live NAV world
has completed G3 through G4-C. Those require a served run.

## Next validation checkpoint

Run one narrow ls20 served checkpoint with the fast infrastructure model. Grade it in this order:

1. G1 produces a nonempty control map with evidence refs and does not promote ACTION5 without
   translation evidence.
2. Each controller action names one bound target and is correctly labeled APPROACH or
   CONTACT_ATTEMPT.
3. The route never traverses an anchor absent from the demonstrated-stand set.
4. Each completed contact advances or records exactly one roster target; no action-count threshold
   creates success.
5. At least one BODY lever reaches a supported confirmation and enters G4 with a NAV procedure.
6. G4-A approach frames do not advance the orbit; contact frames do.

Only after this trace passes should the run be extended through G4-B/G4-C and then to more NAV or
HYBRID worlds.

## Position on the full ladder

Built locally: G0-G4 for CLICK and NAV, life persistence, level freeze/restart, and hypothesis-only
cross-level carry/regrading. Live evidence remains stronger for CLICK than NAV.

The next engineering order is:

1. repair any friction exposed by the narrow ls20 checkpoint;
2. complete live NAV G3 and G4 evidence;
3. build the HYBRID scheduler that composes CLICK and NAV without double-counting targets;
4. build G5 environmental forces;
5. build G6 explicit inertness after the full activation protocol;
6. build G7 counter-masked novel-state exploration;
7. build G8 observed-win description in the learned physics grammar;
8. deepen G9 cross-level transfer after same-level gates are stable.

Cross-death memory already exists. Cross-level freeze and carried lever hypotheses already exist,
but transfer must stay subordinate to the current level's own evidence.

— **Sol**

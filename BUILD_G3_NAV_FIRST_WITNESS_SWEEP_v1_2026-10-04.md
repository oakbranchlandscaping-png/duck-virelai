# Build record — G3 NAV first-witness sweep

**Type:** `BUILD_RECORD`  
**Author:** Sol (Alpha build seat)  
**Date:** 2026-10-04  
**Status:** source implemented and locally validated; live checkpoint pending

## Purpose

Make NAV G3 obey the same broad-sweep law as CLICK G3:

> collide with the current ranked target; if the counter- and ego-masked transition has an
> attributed residue, preserve that target as a found lever and move to the next target.

G3 establishes existence. Repetition, mechanism typing, orbit, endpoint, conditions and causal
explanation belong to G4.

## Failure repaired

The N5.1 `ls20` record already contained a valid first witness at transition 18. Contact with
E0001/M0009 was attributed through `BODY_CONTACT_LINE` and produced a
`LOCAL_AND_REMOTE_LEVER_WITNESS`, including eight remote residual cells. The old scheduler opened
a confirmation pursuit instead of closing the discovery. The repeat occurred from a changed world
state, lost body-contact attribution and downgraded the target to ambiguity.

That was a gate-semantics error. The lever had been found.

## Implemented contract

For a NAV `CONTACT_ATTEMPT` with positive scoped attribution, the controller now:

1. appends the positive response and immutable witness;
2. records a deterministic `G3-DISCOVERY-*` fact;
3. closes the entity's G3 obligations and queues it for G4;
4. emits `virelai-g3-lever-discovery-v1` with the target, contact procedure, exact masked residue,
   effect summary and evidence reference;
5. opens no G3 confirmation pursuit;
6. advances to the next ranked target.

The discovery record says only that body contact produced a non-counter, non-ego residue. It does
not claim a repeated law or mechanism.

G4 effect anatomy now accepts either the older CLICK path of witness + supported confirmation +
dossier, or the NAV first-contact discovery record. A NAV discovery enters G4 with one evidence
reference. G4 explicitly retains repetition and deeper mechanism questions as open work.

## Exit criteria

- A first positive NAV contact emits `LEVER_FOUND`.
- The positive witness cannot be erased by a later null or changed-state contact.
- No pending G3 confirmation is created.
- The ranked G3 target index advances.
- After roster completion, the LeverInventory includes the discovered entity.
- G4 opens on that entity and receives the exact first-contact evidence and intervention.

## Validation

The focused G3-to-G4 regression set passes: **77 tests passed**. It covers NAV routing, G3
scheduler and checkpoint behavior, lever attribution/lifecycle, the new first-witness rule, G3
inventory submission and G4 anatomy entry.

The complete source suite cannot collect locally because the locked ARC inference environment does
not contain the external `taaf` package used by online-harness tests. This is an environment
dependency limitation; the relevant local suites completed successfully.

Ruff still reports two pre-existing findings in `virelai_gates.py` outside this slice: a loop name
shadowing `dataclasses.field`, and a duplicate `explanation` key in the reachability template. This
slice introduces no new Ruff finding.

## Live checkpoint

The next `ls20` checkpoint should grade the earliest positive contact directly. At the transition
corresponding to N5.1 transition 18, expected artifacts are:

- attribution `LOCAL_AND_REMOTE_LEVER_WITNESS`;
- `lever_discovery.status == LEVER_FOUND`;
- E0001 lifecycle state `G4-READY`;
- no `pending_confirmation` for E0001;
- scheduler target index advanced to the next ranked object.

The full G3 sweep may still expose separate visual components of one physical contact surface.
Those positive components remain preserved; surface consolidation can use their shared contact and
effect histories without blocking discovery.

— **Sol**

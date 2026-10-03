# Build slice: controller-first G1 and G2 NAV

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** BUILT, LIVE PARTIALLY CONFIRMED
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## Purpose

Restore the ratified M8 ownership boundary: Virelai executes an environment action whenever the
active gate or demonstrated evidence determines one lawful next action. Duck is called for semantic
work: explaining the ego, explaining the counter, freezing a prospective model, choosing between
non-equivalent experiments, or resolving a state the deterministic system cannot handle.

This slice addresses the live ls20 v7 friction in which G0/G1 consumed model turns even though the
metadata answer and Delphi actions were already exact. It also begins the same correction in G2 so
the ranked NAV object hunt can move without asking Duck to choose routine steering actions.

## What changed

### G0 and G1 ownership

- G0 is handled before world-type dispatch. NAV and HYBRID therefore receive the same
  metadata-derived controller answer as CLICK.
- Every exact G1 Delphi probe is controller-owned.
- Duck is woken when the embodied-ego explanation is due.
- After Duck submits the explanation and prospective prediction, the exact demonstration action is
  controller-owned.
- The compact G1 card retains the accepted ego model and frozen prediction while the demonstration
  runs. The model no longer has to reconstruct its just-accepted law from an impoverished card.

### G2 deterministic NAV pursuit

- When G1 closes, its demonstrated action bearings and bound ego footprint initialize a G2 pursuit
  lattice.
- The controller routes toward the next object in the strict ranked visual roster.
- A movement to the predicted landing records another demonstrated stand (floor).
- Remaining on the predicted starting stand records a refused edge (wall) for the current pursuit.
- A remote counter tick no longer hides a refused contact: unchanged ego stand plus unchanged target
  footprint completes that target even when another board region changes.
- Contact intent is derived from predicted ego-footprint intersection with the target, not from
  adjacency or an arbitrary rate.
- The G2 pursuit state is deliberately separate from G3's entity ledger. G3 must compile its
  frontier only after the full counter mask is sealed.
- If G1 evidence does not yield a computable route step, ownership returns to Duck with that reason.
  This is the intended fallback boundary, not a silent guess about an action number.

Duck still writes the counter explanation and prospective prediction. Bound post-explanation tests
remain controller actions when the capability contains one exact action.

## Files

- `inference/framework/controller_executor.py`
- `inference/framework/virelai_gates.py`
- `inference/framework/card_builder.py`
- `tests/test_memory_m2.py`
- `tests/test_counter_gate.py`

## Verification

Focused ownership, counter, and NAV foundation suites:

```text
50 passed
```

Complete local suite with the vendored TAAF source on `PYTHONPATH`:

```text
546 passed, 14 third-party deprecation warnings, 0 failures
```

The full command completed in 555.80 seconds. The first unconfigured attempt could not collect the
native solver tests because `taaf` was absent from `PYTHONPATH`; rerunning with
`../tufa-arc-agi-framework/src` exercised the complete suite.

## Preregistered evidence boundary and checkpoint

Before the live run, the implementation and local verification were direct observations while
runtime savings and successful G2 steering on a served model were unconfirmed.

The bounded ls20 NAV run was preregistered to grade only these claims:

1. G0 closes with no Duck call.
2. The exact G1 Delphi probes and prospective demonstration execute with no Duck action-selection
   calls.
3. Duck receives a compact G1 explanation turn that includes the evidence needed to describe the
   ego and its movement law.
4. After G1, deterministic G2 steering begins toward the first ranked non-ego, non-field object.
5. Duck is called during action selection only when the controller reports that demonstrated G1
   evidence cannot compute the next route step.

Do not require G2 closure from this checkpoint. It tests the repaired action boundary and the first
deterministic pursuit, not the full world model.

## Known limits

- G2's route lattice recognizes the demonstrated ego by its observed integer pattern. If the ego
  changes appearance before G2 completes, deterministic pursuit stops and wakes Duck.
- G2 does not yet emit a bounded unreachable certificate; the existing full certificate remains in
  G3. A G2 target with no evidence-supported step therefore wakes Duck rather than being skipped.
- Exact multi-action batches are still outside the one-action controller turn contract. This does
  not affect the G1 probes or ordinary G2 pursuit tested here.
- The executed checkpoint contains the frozen source at commit `0b1a5e4`; later active-source
  changes are outside that evidence boundary.

## Live checkpoint result

The bounded ls20 run completed on 2026-10-03 and graded **5 PASS, 2 PARTIAL, 1 FAIL** against its
eight preregistered criteria. The controller closed G0, performed seven of eight Delphi actions,
executed the supported G1 demonstration, entered G2, and formed the complete recurrent counter
candidate after two G2 pursuit actions. Duck's accepted G1 explanation correctly described the ego
and all four movement laws.

The remaining defects are ownership boundaries. A generic low-budget wake overrode one exact G1
action, and NAV G2 woke Duck for an explanation after the controller already held the footprint,
rewrite, recurrence, and trigger evidence needed for the narrow counter gate. Full evidence and the
required repair are in `REVIEW_RING9_CONTROLLER_FIRST_LS20_V1_2026-10-03.md`.

— Sol

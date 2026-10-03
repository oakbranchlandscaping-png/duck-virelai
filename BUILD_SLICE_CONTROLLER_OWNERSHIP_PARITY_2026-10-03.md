# Build slice: controller ownership parity across CLICK and NAV

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** BUILT AND LOCALLY VERIFIED; live unconfirmed
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

## Ruling implemented

Duck is called only when the next required operation needs semantic judgment that deterministic
code and certified evidence cannot supply. A warning, small remaining budget, death, level event,
or NAV world type does not by itself transfer an exact action or certified answer to Duck.

This applies to the complete gate ladder and to both control archetypes. NAV is a different way to
reach and activate a target; it is not a reason to give mechanical control back to the model.

## Ownership contract

| Stage | Controller owns | Duck owns |
|---|---|---|
| G0 | metadata-derived world type | unresolved or unsupported metadata only |
| G1 | exact Delphi probes and prospective demonstration | embodied-ego explanation and movement law |
| G2 | deterministic pursuit, certified counter answer, bound demonstration | an OPEN/IRREGULAR trigger or evidence that does not determine a prediction |
| G3 | ranked pursuit, contact attempts, confirmations, certified dossiers and inventory | genuine ambiguity or a probe for which no evidence-bounded route/action exists |
| G4.1 | anatomy rendered from certified G3 effect channels | no routine role |
| G4 orientation | no action | one semantic orientation that names and organizes the certified world model |
| G4-A | route, terminal contact, repeated activations, stopping law, requested extra runs | explanation of each confirmed orbit and optional request for more evidence |
| G4-B/C | route and execute a frozen prediction | formulate the prediction, describe relations, and state the lever law |

The explanations remain required because this project's success standard includes human-readable
mechanistic understanding. Duck does not choose an action when the controller already knows one.

## Defects found by the audit

1. A fixed budget wake could hand the next exact controller action to Duck. The ls20 checkpoint
   exposed this during G1; the existing CLICK G4 test deliberately expected the same transfer.
2. NAV G2 always woke Duck when an answer was due, even when the counter trigger and prediction
   were fully certified.
3. NAV G3 did not reuse controller-rendered dossiers and inventory.
4. NAV G4.1 did not reuse controller-rendered effect anatomy.
5. The one G4 orientation turn was enforced in CLICK after G4.1 but bypassed by the NAV dispatcher.
6. A Duck-requested extra G4-A run had a CLICK execution path but no NAV routing path.
7. A death or other boundary warning could cause Duck to take the next mechanical G4 action even
   when the continuing procedure remained exact.

## Implementation

### Ownership after a wake

The controller now computes the next owner before acting on a pending wake. If the next operation
is still a certified answer or exact action, the controller logs the warning and retains ownership.
If the next operation independently belongs to Duck, the warning is included in the handoff.

This makes budget and boundary signals context rather than ownership transfers. Contradiction,
ambiguity, and missing-route states reach Duck when the resulting gate state has no certified
recovery step. If deterministic recovery exists, the controller performs it.

### Certified answers in NAV

CLICK and NAV now share one certified-answer helper. It preserves the refusal guard and renders:

- the G2 counter answer when the observed trigger class is controller-owned;
- G3 dossiers and the inventory when attribution is unambiguous;
- G4.1 effect anatomy from certified channels.

An OPEN or IRREGULAR G2 record still belongs to Duck because the next discriminating experiment is
a choice rather than a deduction.

### G4 NAV parity

- NAV receives the same single semantic orientation boundary as CLICK.
- G4-A routing and terminal contact remain controller actions.
- A requested extra run is routed back to the named NAV lever before its explanation continues.
- NAV approach moves do not consume the requested press count; only terminal contact does.
- Confirmed-orbit explanation remains Duck's required semantic product.
- G4-B and G4-C keep Duck's frozen predictions and descriptions while the controller routes and
  executes each test.

## Files

- `inference/framework/controller_executor.py`
- `inference/agent/controller_turn.py`
- `tests/test_memory_m2.py`
- `tests/test_memory_m4.py`
- `tests/test_nav_branch_foundations.py`

## Focused validation

The production controller, G4 economy/lives, and NAV foundation suites pass **47 tests** after the
old expectations that Duck performs a post-wake action were replaced. These include direct
regressions for exact-action retention, certified NAV answers, NAV orientation, NAV extra-run
routing, and controller continuation across budget and death signals.

Complete source suite:

```text
549 passed, 14 third-party deprecation warnings, 0 failures
```

The clean run completed in 549.14 seconds.

## Evidence boundary and next checkpoint

This slice changes active source only. It does not change the frozen ls20 v1 package or its review.
The full local suite must pass before packaging. A new bounded ls20 run should then require:

1. all eight Delphi actions and the demonstration are controller-owned;
2. Duck supplies the accepted G1 explanation;
3. the controller certifies G2 from the recurrent bar evidence, executes its bound demonstration,
   installs the mask, and enters G3;
4. no budget or boundary warning causes Duck to select a mechanical action;
5. any Duck call names the semantic uncertainty that deterministic code could not resolve.

The next broader G4 NAV checkpoint should grade model-call economy as an explicit output: one
orientation, one explanation per confirmed orbit, and one semantic prediction/description turn
only where the gate contract requires it. Every route, contact, repeat, and bound test must be
controller-owned.

— Sol

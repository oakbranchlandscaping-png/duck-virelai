# Checkpoint: controller ownership ls20 v2

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** PREREGISTERED; package not yet built
**Frozen source:** `4e1be00f59c1c430391603c572bfd1dcaa4f87cb`

## Question

Does the ownership-parity source carry ls20 from metadata through a certified counter mask and
into G3 without asking Duck to select any environment action?

This is the direct successor to the v1 checkpoint. V1 established the ego model and found the
counter candidate, but a budget wake transferred one exact G1 action to Duck and the NAV G2 branch
spent the remaining runtime asking Duck to explain a mechanically complete counter record.

## Frozen configuration

- World: `ls20-9607627b`
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Passes and concurrency: 1 and 1
- Environment-action cap: 16
- Behavior-time cap: 1200 seconds
- Model output cap: 4096 tokens per request
- Thinking: enabled
- Temperature: 0.6
- Runtime image: the previously successful pinned Python 3.12 image

The action and time limits match v1 so the ownership result can be compared directly. They are
checkpoint limits, not estimates of what the complete solver should need.

## Preregistered criteria

1. G0 closes through the controller with no model request.
2. All eight Delphi actions run through the controller in strict order.
3. Duck supplies an accepted human-readable embodied-ego explanation and movement law.
4. The controller executes a supported prospective demonstration and closes G1.
5. Deterministic G2 pursuit forms the recurrent counter candidate without a Duck action.
6. The controller submits the certified G2 answer and executes its bound demonstration.
7. G2 installs the complete counter mask and the gate machine enters G3.
8. Every environment action is controller-owned. Every Duck call corresponds to a semantic
   boundary for which certified state did not already determine the operation.
9. The run stops at its explicit cap or another controlled boundary without crashing.

The checkpoint does not require competition score, level completion, G3 closure, lever discovery,
G4 entry, or a win.

## Required evidence

- execution receipt matching the frozen source and package manifests;
- turn ledger separating controller and Duck turns;
- probe envelopes identifying every action executor;
- G0, G1, and G2 answer records;
- supported G1 and G2 demonstration comparisons;
- a G2 product containing the locked mask;
- a G3 gate event, view, or turn-ledger row proving entry;
- request log showing what each model call was asked to do.

## Decision rule

Do not infer success from source tests, packaging, notebook completion, score, or a final summary.
Grade only the downloaded executed artifacts. A Duck-selected environment action fails criterion 8
even if it chooses the same action the controller would have chosen.

— Sol

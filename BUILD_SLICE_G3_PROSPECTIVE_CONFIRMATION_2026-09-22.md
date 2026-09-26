# Build slice: G3 prospective witness confirmation and G4 handoff

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Purpose

This slice prevents one transition from serving as both discovery and proof. A positive G3
attribution freezes a target-local prediction, pauses enumeration, and requires a later independent
transition before the entity can enter G4.

## Implemented behavior

- Positive local, remote, or combined attribution creates a pending confirmation containing the
  witness evidence reference, frozen pre-action target footprint and pointer owner, target identity,
  phase, predicted residue partition, and declaration transition.
- The scheduler emits `CONFIRM_LEVER_WITNESS` before any next ranked target.
- Confirmation uses the same pointer intervention for CLICK or a separately admitted movement /
  contact action for NAV.
- A later positive residue overlapping the frozen local or remote prediction produces an immutable
  witness, then transitions the entity through `WITNESSED → G3-CLOSED → G4-READY`.
- A contradicted confirmation becomes `AMBIGUOUS`; a boundary confirmation becomes `FILED_TO_G5`.
- The confirmation evidence is retained in the attribution accumulator and scheduler snapshot.
- A dossier answer still cannot close the lifecycle by itself.

## Exit criteria

- Discovery and confirmation have different transition ids and evidence references.
- Enumeration cannot advance past a positive target before confirmation.
- Confirmed entities have a lifecycle path to `G4-READY`.
- Contradicted and boundary cases remain explicitly deferred.
- Local tests cover a positive witness, its confirmation probe, and the resulting target advance.

## What remains unproven

The served Duck has not yet completed a G3 sweep with confirmation and a G4 handoff certificate.
Live confirmation still requires a controlled run with the production adapter and behavioral
trace. The next implementation work is the live runbook / certificate evaluator, not a broader
mechanics claim.

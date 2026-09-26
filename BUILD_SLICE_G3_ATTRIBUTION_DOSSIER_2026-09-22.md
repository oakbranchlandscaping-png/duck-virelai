# Build slice: G3 attribution and Duck dossier contract

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Purpose

This slice connects the scheduler to the existing scoped attribution kernel and gives Duck one
answer contract for each target. It tests whether a target response can be explained from immutable
evidence; it does not let prose itself close a gate or infer a full mechanism.

## Implemented behavior

- Every scheduled outcome is converted into a production-shaped `ObservationScope` before
  attribution.
- CLICK actions are attributed through the pre-action pointer owner. NAV contact attempts use the
  body channel and require contact or an explicit refused-contact report.
- Counter-mask cells, authorized ego motion, ego-confounded residue, and ground exchange are
  retained as separate partitions.
- The existing `LeverEvidenceAccumulator` receives the attribution and exposes local, remote,
  combined, scoped-null, boundary-deferred, and unresolved dispositions.
- A target-cell change is only a provisional response until the attribution disposition supports
  it; boundary and ambiguity remain distinct.
- `submit_answer` now requires `target_member_id`, immutable `evidence_refs`, an explanation,
  competing model(s), and a falsifier. The answer is stored in the target dossier and lifecycle
  journal; it cannot close the lifecycle by itself.
- G3 snapshots include the evidence records and submitted dossier answers.

## Exit criteria

- A G3 event names the persistent target, attribution disposition, residue partitions, and exact
  evidence reference.
- Positive witnesses are produced only by the attribution kernel.
- A null observation never grants inertness.
- A dossier answer cannot cite unknown evidence or omit a competing model and falsifier.
- Local tests cover a positive pointer witness and a valid dossier answer.

## What remains unproven

The served Duck has not yet supplied dossier answers during a complete G3 sweep. Prospective
confirmation of positive witnesses, complete lifecycle closure, and G4 handoff remain the next
slice. A live run is required before this becomes LIVE CONFIRMED.

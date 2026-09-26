# Build slice: G3 world-type scheduler shell

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Purpose

This slice gives G3 one controlled probe path. It turns the ranked entity roster inherited from
G2 into a strict, resumable schedule while preserving the distinction between CLICK, NAV, and
HYBRID worlds. It does not claim a lever, inertness, or a win merely because a target was tried.

## Scheduler contract

- CLICK worlds issue one exact `ACTION6` probe per ranked entity, in visual-rank order.
- NAV worlds issue one movement probe at a time, admitting only metadata actions 1–5 and requiring
  `APPROACH` or `CONTACT_ATTEMPT` intent.
- HYBRID worlds complete the click activation arm before entering the NAV arm.
- Probe identifiers are derived from phase, target index, and navigation step, so capability
  tokens remain stable while a decision is being supplied.
- Every attempted target gets a lifecycle evidence reference. A target-local change is recorded as
  a provisional response signal; final local/remote attribution remains the next slice.
- Every transition is sent to the locked-counter monitor before the G3 event is returned. Counter
  evidence therefore cannot disappear inside the lever sweep.
- A target-cell comparison uses normalized `(row, col)` pairs, preserving the lossless cell
  representation delivered by the production adapter.

## Implemented artifacts

`inference/framework/virelai_gates.py` now contains the G3 phase, target index, navigation budget,
probe construction, validation, outcome recording, scheduler snapshot, and counter-monitor hook.
`tests/test_g3_scheduler.py` covers click token stability, ranked target binding, and NAV intent /
action admission.

## Exit criteria

- No direct G3 probe can bypass the active scheduler.
- The next operation is explicit in the G3 snapshot (`QUERY_NEXT_G3_TARGET` or
  `G3_ENUMERATION_COMPLETE`).
- CLICK, NAV, and HYBRID have distinct admissibility rules.
- Target attempts and counter-monitor events are retained in the returned trace.
- Local tests pass without claiming a served-model result.

## What remains unproven

This is a controller shell, not a live Duck result. A served run must still demonstrate strict
ranking, correct world-arm selection, persistent entity dossiers, honest handling of no-response
and budget stops, and a Duck explanation for each accepted witness. Attribution integration and the
G3 dossier contract are the next build slice.

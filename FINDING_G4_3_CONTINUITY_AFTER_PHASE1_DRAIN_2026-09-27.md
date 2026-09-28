# Finding: G4.3 loses state continuity after the Phase-1 drain

**Date:** 2026-09-27 (written while `taaf-virelai-ring9-g4-ft09-phase1-v1` v1 was running, before
any of its output had been seen)
**Author:** Claude (Alpha build seat), signed
**Source examined:** `8cfb782` (`variants/ring9-cybernetic-gates/ARC3-Inference/`)
**Status:** OPEN. Defect confirmed offline; no fix applied yet.

## Defect

Each `LeverLimitStudy` (`inference/framework/g4_limits.py`) starts from its own lever's G4.2 orbit
endpoint (`self._current_address = states[-1]`). `record()` rejects any observation whose masked
before-state differs from that address ("the G4.3 chain is discontinuous").

That premise held when G4.3 ran on a lever immediately after its own orbit, before S1. With S1,
every lever's orbit runs first (Phase 1) and G4.3 opens only afterwards. Two things now move the
world away from a study's expected start:

1. later orbits, whenever an earlier lever's orbit did not return the world to where it started;
2. earlier G4.3 studies, whose persistence and inverse probes press other levers.

When that happens, the G4.3 probe executes in the environment, `record_outcome` raises
`GateContractError`, the evidence is not recorded, and every retry fails the same way.

## Reproduction (offline, scratch harness driving the real gate machine)

The simulation used two synthetic CLICK levers.

| Lever mix | Result |
|---|---|
| Both toggles (each orbit returns to its start state) | Clean: G4.2 drains, G4.3 `EXACT_RECURRENCE_RECONFIRMED` for both, G4.3 `SATISFIED` |
| A absorbing, then B toggle | A's G4.3 completes (its inverse test presses B and moves the world); B's first `RECONFIRM_RECURRENCE` is **rejected as discontinuous** |
| A toggle, then B absorbing | A's first `RECONFIRM_RECURRENCE` is **rejected as discontinuous** (world is at B's endpoint) |

The committed suite misses this. `test_gate_routes_through_endpoint_inverse_and_reapplication`
stops after asserting that the second lever is current and never executes its probe. No committed
test asserts `EXACT_RECURRENCE_RECONFIRMED` or `RECURRENCE_DIVERGED` through the gate.

## Prediction for the running ft09 checkpoint (made before seeing output)

- If every ft09 lever that completes G4.2 is an exact toggle or cycle that returns to its own start
  state, and the ticker is masked, G4.3 should run cleanly. C5 is gradable.
- If any completed lever ends in a masked null (ABSORBING), or recurs to a state other than its
  start, G4.3 will hit repeated "discontinuous" rejections. C5 fails, and C7 fails as a stall.
  This is a known defect, not new evidence against the recurrence logic.
- C1–C4 (the drain itself) are unaffected.

## Resolution direction

The locked doctrine already places this line. `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md`
says G4.3's endpoint confirmation is single-lever (Phase 1), while persistence and reversal are
multi-lever (Phase 2). Recurrence re-confirmation is also single-lever. Proposed build:

1. Move endpoint confirmation and recurrence re-confirmation into each lever's Phase-1 study,
   executed right after its G4.2 orbit while the world is still at that endpoint.
2. Phase-2 probes (persistence, inverse) anchor to the current observed masked state, not to a
   stored endpoint. They state which lever's state they test from what the frames show.
3. Write a regression test first, showing the two failing mixes above on `8cfb782`.

Point 2 changes what a Phase-2 claim is anchored to. The Director should confirm it before the build.

— Claude, Alpha build seat, 2026-09-27

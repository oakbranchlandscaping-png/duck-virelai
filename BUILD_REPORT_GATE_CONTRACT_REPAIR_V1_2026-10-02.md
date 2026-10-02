# Build report: bounded gate contract repair v1

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Source:** `variants/ring9-cybernetic-gates/ARC3-Inference`

## Purpose

V6 produced a substantively useful G1 explanation, but one copied evidence hash was wrong. The gate
correctly rejected it. The runtime incorrectly classified that rejection as passive inspection and
stopped before Duck could repair the field. This slice repairs that interface without weakening the
gate's evidence standard.

## Implemented behavior

The tool bridge now classifies every completed call as one of four relevant outcomes:

1. `OBSERVATION` — a read-only inspection;
2. `ENVIRONMENT_STEP` — represented by the existing executed-step flag;
3. `GATE_TRANSITION` — an accepted answer that advances the active gate;
4. `CONTRACT_REPAIR` — a rejected gate answer that must be corrected.

A first contract failure supersedes an earlier no-progress warning and produces one binding repair
instruction. The next operation must resubmit the answer. Inspection or environment action while
repair is pending ends cleanly with `contract_repair_loop`. Repeating a previously seen validation
failure also ends cleanly. A newly corrected field may produce a different validation failure and
receive another bounded repair turn; an accepted answer resets the guard.

An action later in the same Python call as a rejected answer is blocked before it reaches the game.

G1 `evidence_refs` now uses the established certified-field path already used by later gates. The
card displays `CERTIFIED`, and the controller fills the exact live evidence IDs if Duck omits the
field or leaves the marker. If Duck supplies an explicit value, it is preserved and validated as
written. No incorrect claim is silently repaired.

The G1 card also states that PATTERN_TRANSLATION footprints contain every cell of the moved
multi-integer ego. This keeps the prediction geometric and exact while removing ambiguity about
anchor cells.

The checkpoint evaluator now recognizes the v5-v7 G3 NAV receipt schemas. V6's receipt and world
alignment pass after the update; its behavioral grade remains failed because G1 did not close.

## Validation

- focused interaction, card, gate and evaluator suite: 58 passed;
- bridge plus guard integration suite: 35 passed;
- full source suite: 542 passed in 9m 17s;
- diff whitespace validation: clean;
- v6 artifact re-evaluation: receipt PASS, G1 behavioral FAIL for missing accepted answer and
  demonstration.

## V7 checkpoint exit

On ls20, v7 must:

1. preserve the exact eight-action G1 Delphi sequence;
2. produce a controller-bound G1 evidence list;
3. accept a substantive ego explanation without an opaque-ID transcription failure;
4. execute and join the prospective ego demonstration;
5. open G2 without `no_progress_tool_loop` or `contract_repair_loop`.

G2 or G3 success is useful evidence but is not required to pass this interaction slice.

— **Sol**

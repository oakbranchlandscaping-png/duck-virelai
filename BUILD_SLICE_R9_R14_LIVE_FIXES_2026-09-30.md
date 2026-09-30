# Build slice R9-R14: the two defects the live G4-B run found

**Revision label:** `R9-R14`
**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed
**Base:** `c448e27` (R9-R13).
**Source of the findings:** `REVIEW_RING9_G4B_FT09_KAGGLE_V1_2026-09-30.md`, F1 and F2.

## F1: a refusal must reach Duck

**What happened live.**
- Duck's first orientation was refused, because one note's subject was the current gate
  (`G4.2-LEVER-ORBITS`), which was not yet certified.
- The reply carried the whole card *before* the error. The tool-output limit cut it, so Duck never
  saw the reason.
- It took 5 turns and 6 minutes to stumble onto a note set that passed.

**The fix.**
- Every memory and orientation reply now puts `error` before `data`.
- A refusal carries only a compact state (gate, status, next operation, and `virelai('gate')` for
  the card), not the full card.
- The subject refusal now names what is allowed: WORLD, an entity id, or the gate ids listed.
- The current gate is accepted as a note subject. It is the natural subject of a note about the
  study in progress.

## F2: the machine's observed step follows every transition

**What happened live.** `CyberneticGateMachine.observed_through_step` was the larger of the G1 and G2
counters, and nothing after G2 advanced it. It stayed at 57 while the game reached 117. Every later
freeze stamp (G3, G4-A, G4-B, G4-C) and every note's timestamp was therefore stale.

**The fix.**
- The machine keeps a high-water mark, advanced by every recorded outcome and every harness reset.
- `observed_through_step` is the largest of the three values.
- A prediction frozen now is stamped now.

## Changed

| File | Change |
|---|---|
| `inference/agent/memory_queries.py` | `_reply` puts the error first; `_refused_state` replaces the full card on a refusal |
| `inference/framework/annotation_lane.py` | The current gate is a known subject; the refusal lists what is allowed |
| `inference/framework/virelai_gates.py` | `_high_step`, advanced in `record_outcome` and `observe_system_reset` |
| `tests/test_r9_r14_live_fixes.py` (new) | 3 tests, each failing before the fix: the live refusal reproduced (reason first, under the tool-output limit); the current gate as a subject; the observed step on the live v1 record (57 before, 109 after) and a G4-B freeze stamped at the current transition |

**Suite:** cloud **486 passed, 1 skipped** (487 tests). Ruff is clean. **Mac expected: 487 passed.**

**Ratchet:** `virelai_gates.py` goes from 5,428 to **5,425**. Two multi-line statements were folded
to offset the four added lines.

— Claude, Alpha build seat, 2026-09-30

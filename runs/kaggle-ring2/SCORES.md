# Ring 2 (the counter) — single-run feedback read, 2026-08-26
Per the one-run cadence: shapes and fixtures, not verdicts. Tufa's scorer throughout.

## Four-arm table

| arm | all-25 | ex-ft09 | actions | 2-level games |
|---|---|---|---|---|
| baseline | 1.2225 | 1.2734 | 3,673 | 2 |
| ring1 | 1.4833 | 0.9499 | 6,220 | 1 |
| ring11 | 1.0140 | 1.0563 | 5,189 | 2 |
| **ring2** | **1.3632** | **1.1824** | **4,830** | **4** |

Paired vs base p=0.77 (tie — no promotion; slot stays r0). Budget: ring2 second-best
at every point ≥20k (0.661@20k vs base 0.200); ring1 still budget-best (its terminal
was ft09-carried).

## What the ring demonstrably did

- **Over-pressing falls monotonically as doctrine deepens: 6220 → 5189 → 4830**
  (+69% → +41% → +31% vs base). The restraint stack is working, ring by ring.
- **Most 2-level completions of any arm** (ft09, sb26, tu93, vc33) and TWO first-evers:
  vc33 4.86 in 48 actions (never above 0.14 in any arm) and sk48 2.78 (never scored
  in any arm). tu93 recovered (0 in both prior rings → 2.39); r11l recovered (4.76).
- **The counter subsystem ran live end-to-end**: 4 games sealed counters (ar25, bp35,
  lf52, sp80), 7 unseals (incl. transient false seals killed by their own evidence —
  the pre-registered self-correction), world-grain map + world_changed live, no crashes.

## Pre-registered fixture results — one pass, one honest failure

- Still-board worlds: no persistent false masks observed (transients self-killed). PASS.
- **ls20 and tn36 did NOT seal — fixture FAILED as written, and the failure is a
  finding:** their drains are evidently NOT which-action-invariant (a fuel bar that
  ticks only when the ego MOVES fails conjunct 1 on any blocked/click press — it is a
  motion-COUPLED drain, a rung-5 coupling, not a schedule-autonomous COUNTER).
  ls20 still scored 1.69. The archetype correction routes those worlds to the
  ego/coupling rungs (Ring 2.5+), exactly where the lawful order says couplings live.
  Transcript verification owed.

## Observed defect-class to carry into the next build

Seals at the 2-press evidence floor are noisy (bp35 sealed two mid-board 23-cell
regions at 2 presses; later unsealed). The floor is structurally minimal, not wrong —
but announcement at first seal spends model attention on transients. Candidate
refinement for the next ring (threshold-free): announce a seal only once it has
survived one additional press beyond its sealing evidence.

## Disposition

Feedback absorbed; no promotion; next build = Ring 2.5 (ego read: light threader +
edge.py verb transcription) with the seal-announcement refinement folded in, on the
Director's go.

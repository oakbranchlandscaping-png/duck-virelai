# Targeting log: G2's object frontier ranks the counter bar's remainder first (k008)

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat)
**Status:** logged under Sol's ruling 1 on G3 reset continuity. **Not a defect of that slice, and not changed.**

## Observation

On k008, G2 now starts from the true post-reset board.
- Row 0 is the counter bar refilled by RESET 31: 62 cells of integer 14, plus a 2-cell remainder of integer 0 at `(0, 62)`–`(0, 63)`.
- G2's ranked object frontier puts that 2-cell remainder, `M0002`, first, so G2's first `PILOT_TO_CONTACT` targets it.
- On the stale pre-reset board, row 0 was one 64-cell object of integer 0 and ranked third. `M0003` (12 cells at `(1, 36)`) was first.

## Why it may matter

- The remainder is part of the counter display.
- G2 does not yet know the counter (G2 is the gate that finds it), so its existing rule ranks the fragment like any small object.
- A body-contact pilot toward a display fragment on row 0 is probably not a productive first G2 target.

## Not done

No ranking change. A question for the targeting work: should G2's frontier deprioritise components that are both small and edge-adjacent on the top or bottom row, before the counter is known? That would be an invention, so it needs prior-art mining first.

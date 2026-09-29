# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-29 (PM)
**Author:** Claude (Alpha build seat), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29.md`, which is kept in place.

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
3. `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
4. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_PM.md`: current state, test commands, notes
5. `BUILD_PLAN_G4_CLICK_COMPLETION_v8_2026-09-29.md`: the revision ledger
6. `BUILD_SLICE_MEMORY_M2_CONTROLLER_EXECUTOR_2026-09-29.md`, then the M1 and M0 slices

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes, and never reset or
clean the tree.

Current position:

- **Mode.** The controller executes every move it can compute (R9-R08 built): G0–G3 run without
  Duck on CLICK worlds. Duck's first turn is at G4.0. NAV is shelved.
- **Committed.** R9-R06 (`1a4b6bd`); R9-R07 (`ee826ab`).
- **Pending commit.** R9-R08. Mac pytest expected: 450 passed (the full suite).
- **Next live test.** Not before M-3 and M-4 pass offline. It ships as the M-5 package.
- **Security.** Rotate the OpenRouter and ARC keys. Never `git add kaggle/` or `git add -A`; stage
  explicit paths only.

— Claude, Alpha build seat, 2026-09-29

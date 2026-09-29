# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-29 (night)
**Author:** Claude (Alpha build seat), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29_EVENING.md`, which is kept in place.

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
3. `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
4. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_NIGHT.md`, then the `_EVENING` and `_PM`
   files it extends
5. `BUILD_PLAN_G4_CLICK_COMPLETION_v10_2026-09-29.md`
6. The memory slices, newest first:
   - `BUILD_SLICE_MEMORY_M4_G4_ECONOMY_AND_LIVES_2026-09-29.md`
   - M3
   - M2
   - M1
   - M0

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes, and never reset or
clean the tree.

Current position:

- **Committed.** R9-R06 through R9-R09 (`e2c2b06`).
- **Pending commit.** R9-R10, memory M-4. Mac pytest expected: 470 passed.
- **Mode.**
  - The controller runs ft09 from G0 to a satisfied G4-A, offline, in 92 actions.
  - Duck takes 7 turns: orientation, 5 orbit explanations, and 1 budget wake.
  - A same-level death re-studies the lever (D4).
- **Next.** The M-5 package and the D7 throughput run: the first live test since R9-R05.
- **Security.**
  - Rotate the OpenRouter and ARC keys.
  - Never `git add kaggle/` or `git add -A`.
  - Upload datasets with `-r skip`.

Kaggle procedure:

1. Run `tools/verify_kaggle_package.py`.
2. `kaggle datasets create -p <pkg>/source-dataset -r skip`, then wait until
   `kaggle datasets status` reports `ready`.
3. `kaggle kernels push -p <pkg>/kernel --accelerator NvidiaRtxPro6000`.
4. Before grading, check that the downloaded `execution_receipt.json` is byte-identical to the
   package receipt.

— Claude, Alpha build seat, 2026-09-29

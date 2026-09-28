# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-27 (evening)
**Author:** Claude (Alpha build seat), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-24.md` and this file's morning version, which
is kept in git history.

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its 2026-09-27 amendment banner first)
2. `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md`: the Director's rulings as axioms A1–A5
3. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md`: current state and read order
4. `BUILD_PLAN_G4_CLICK_COMPLETION_v3_2026-09-27.md`: the current plan

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes, and never reset or
clean the tree. Keep editable source, frozen packages (`kaggle/<package>/`) and executed artifacts
(`runs/`) separate.

Current position:

- **Mode.** The controller states targets and Duck executes them.
  - G2 (CLICK worlds) and G4 are **stated targets**: a `GUIDED_ACTION` capability admits any action,
    and the controller audits the record.
  - G0, G1 and G3 are scripted. NAV is shelved.
- **Committed.**
  - G4-A guided lever study: `fcc7f11`.
  - The G2 counter axiom and no-legal-move guard are written to the Mac, pending Mac pytest (expect
    385) and commit.
- **Live evidence.**
  - vc33: G0 through G4.2 on Kaggle; G4 interrupted by a level change.
  - ft09: stalled in G2 on the old counter-only rule, which is fixed now.
  - No guided gate has run live yet.
- **Next live test.** `ring9-g4-ft09-guided-v1` on Kaggle: guided G2 → scripted G3 → guided G4-A on
  ft09.
- **Security.** Rotate the OpenRouter and ARC keys. Never `git add kaggle/` or `git add -A`.

Kaggle procedure:

1. Run `tools/verify_kaggle_package.py`.
2. Create the dataset with `kaggle datasets create -p <pkg>/source-dataset -r skip`.
3. Wait until `kaggle datasets status` reports `ready`.
4. Push with `kaggle kernels push -p <pkg>/kernel --accelerator NvidiaRtxPro6000`.
5. After the run, check that the downloaded `execution_receipt.json` is byte-identical to the
   package receipt before grading.

— Claude, Alpha build seat, 2026-09-27

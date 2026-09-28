# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-28 (afternoon; the morning version is kept in git history)
**Author:** Claude (Alpha build seat), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-27.md`, which is kept in place.

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md`: the Director's rulings as axioms A1–A6
3. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_PM.md`: current state and read order
4. `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md`: the current plan and the revision ledger

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes, and never reset or
clean the tree. Keep editable source, frozen packages (`kaggle/<package>/`) and executed artifacts
(`runs/`) separate.

Current position:

- **Mode.** The controller states targets and Duck executes them. G2 (CLICK worlds) and G4-A are
  stated targets; G0, G1 and G3 are scripted. The ranked list on the card stays, by ruling. NAV is
  shelved.
- **Revisions.** Every build revision carries a label (`R9-Rnn`; harness work `R9-Inn`) in its
  slice document, commit message and Kaggle package. Ledger: plan v5 §1.
- **Committed.** R9-R03 (`3c89c21`); package `ring9-g4-ft09-guided-v1` (`b68228a`); R9-R04
  (`8319853`): G3 bounded card (A6) and counter trigger label (A1 v2).
- **Pending commit.** R9-R05: G3 entity identity survives recolour; the ft09 ladder passes offline.
  Mac pytest expected 400.
- **Live evidence.** ft09 guided v1: G2 closed live under A1; the run crashed at G3 entry on the
  card-size guard (fixed by R9-R04). Offline, the whole ft09 ladder now reaches G4-A satisfied. vc33: G0 through G4.2 on Kaggle.
- **Next live test.** `ring9-g4-ft09-guided-v2` on Kaggle, carrying R9-R04 and R9-R05.
- **Security.** Rotate the OpenRouter and ARC keys. Never `git add kaggle/` or `git add -A`; stage
  explicit paths only.

Kaggle procedure:

1. Run `tools/verify_kaggle_package.py`.
2. Create the dataset with `kaggle datasets create -p <pkg>/source-dataset -r skip`.
3. Wait until `kaggle datasets status` reports `ready`.
4. Push with `kaggle kernels push -p <pkg>/kernel --accelerator NvidiaRtxPro6000`.
5. After the run, check that the downloaded `execution_receipt.json` is byte-identical to the
   package receipt before grading.

— Claude, Alpha build seat, 2026-09-28

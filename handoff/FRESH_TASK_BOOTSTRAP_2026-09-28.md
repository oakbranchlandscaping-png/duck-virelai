# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-28 (evening; earlier versions are kept in git history)
**Author:** Claude (Alpha build seat), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-27.md`, which is kept in place.

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`: the axioms A1–A6 and the memory laws M1–M10
3. `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md`: RATIFIED; the governing design and its staged build
4. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_EVENING.md`: current state and read order
5. `BUILD_PLAN_G4_CLICK_COMPLETION_v6_2026-09-28.md`: the revision ledger

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes, and never reset or
clean the tree. Keep editable source, frozen packages (`kaggle/<package>/`) and executed artifacts
(`runs/`) separate.

Current position:

- **Mode (ruled 2026-09-28, evening).** The controller executes every move it can compute; Duck is
  woken where judgment is needed. G0–G3 are to run without Duck (stage M-2, not built yet). NAV is
  shelved.
- **Revisions.** Every build revision carries a label (`R9-Rnn`; harness work `R9-Inn`) in its
  slice document, commit message and Kaggle package. Ledger: plan v6 §1.
- **Committed.** R9-R04 (`8319853`); R9-R05 (`4329185`); package `ring9-g4-ft09-guided-v2`.
- **Pending commit.** R9-R06, memory M-0 (instruments: replay harness, record index, memory store,
  turn ledger). Mac pytest expected 409.
- **Live evidence.** ft09 guided v2: G2 closed; G3 confirmed five levers; the card overflowed at
  the fifth dossier (25,502). vc33: G0 through G4.2 on Kaggle.
- **Next live test.** Not before memory stages M-0 through M-4 pass offline on both real ft09
  records (DESIGN §10, §12).
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

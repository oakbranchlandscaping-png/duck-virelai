# Fresh-task bootstrap — Cybernetic Duck

**Updated:** 2026-09-27
**Author:** Claude (Alpha build seat, outgoing) — signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-24.md`

Read these in order before editing or running anything:

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`
2. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27.md`
3. `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md`
4. `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md`
5. the remaining read order listed in item 2

The user's current instructions outrank repository documents. The active source is
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Preserve all existing changes; never reset or
clean the tree. Keep editable source, frozen packages (`kaggle/<package>/`) and executed artifacts
(`runs/`) separate.

Current position:

- G0–G3 have live vc33 confirmation on OpenRouter; G4.1 anatomies exist for both levers (E0004,
  E0005); G4.2 continuation is built and was exercised live on OpenRouter.
- S1, the Phase-1 drain return edge, is committed at `f8a967e` and passes offline (374, Mac).
- Its first live test is the Kaggle notebook `stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`
  (version 1, launched 2026-09-27). The OpenRouter rung was skipped by the Director's ruling after it
  failed on credits. G3 closure on the exact Kaggle model is itself unproven, so grade the
  precondition first.
- Open security item: rotate the OpenRouter and ARC keys. Never `git add kaggle/` or `git add -A`.

First action: check `kaggle kernels status stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`. When
it is `complete`, follow the runbook (retrieve → receipt check → grade C1–C4 → file the review).
Before any new Kaggle upload, run `tools/verify_kaggle_package.py` and create datasets with `-r skip`.

— Claude, Alpha build seat (outgoing), 2026-09-27

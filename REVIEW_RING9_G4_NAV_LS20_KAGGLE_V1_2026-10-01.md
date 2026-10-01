# Review: R9-R19 G4 NAV ls20 Kaggle checkpoint v1

**Reviewer:** Sol (Alpha build seat), signed  
**Notebook:** `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v1`, version 1  
**Status:** infrastructure failure before model startup; no behavioral grade

## Direct observations

- Kaggle mounted the private Virelai source dataset.
- The notebook verified all 220 source-manifest entries.
- Kaggle allocated one NVIDIA RTX PRO 6000 Blackwell Server Edition as requested.
- Kaggle did not attach either third-party runtime dataset. The kernel push had already warned that
  both references were invalid, and both paths were absent in the run.
- Setup stopped with `FileNotFoundError` for the vLLM wheelhouse and Qwen3.6 model paths.
- No model request, ARC game action, gate transition, or behavioral artifact occurred.

## Supported conclusion

The R9-R19 source transport and initial Kaggle GPU environment worked. Version 1 says nothing about
G0 through G4 NAV behavior. Its failure is entirely upstream of Duck and the game.

## Repair

Version 2 keeps source commit `72adbe3`, ls20, all budgets, and the preregistered grading order. It
uses an accessible wheelhouse mirror whose 174 wheel filenames and SHA-256 hashes exactly match the
pinned reconstruction, plus an unmodified Kaggle model source for Qwen3.8-27B-FP8 pinned at
`017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`. The model change is explicit and receipt-bound.

— **Sol**

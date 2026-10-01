# Review: R9-R19 G4 NAV ls20 Kaggle checkpoint v2

**Reviewer:** Sol (Alpha build seat), signed  
**Notebook:** `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v2`, version 1  
**Status:** infrastructure failure before model startup; no behavioral grade

## Direct observations

- The v2 private source mounted and all 220 manifest entries verified.
- The checksum-identical vLLM wheelhouse mirror mounted at its Kaggle dataset path.
- Kaggle accepted the pinned Qwen3.8 model source in the server-side kernel metadata.
- The requested RTX PRO 6000 was allocated.
- The notebook constructed a case-preserving `PyTorch` model path. That path did not exist in the
  normalized Kaggle model mount, so setup stopped before vLLM installation or model startup.
- No model request, ARC action, gate transition, or behavioral artifact occurred.

## Supported conclusion

The runtime asset choice is viable at the metadata layer and the exact wheelhouse is present. V2
does not test Qwen3.8 compatibility or NAV behavior because model-path discovery failed first.

## Repair

V3 keeps the entire v2 payload and resolves the model framework directory case-insensitively. If
the documented candidate paths differ again, it accepts only a unique descendant containing the
model's `config.json`; ambiguity is an error. This changes mount discovery only.

— **Sol**

# Review: Ring 9 G3 NAV reachability v7, Kaggle version 1 failure

**Author:** Sol (Alpha build seat), signed  
**Date:** 2026-10-02  
**Status:** infrastructure failure before benchmark

## Direct observations

- Kaggle status: `KernelWorkerStatus.ERROR`.
- Dataset and model mounts resolved successfully.
- GPU validation passed on one NVIDIA RTX PRO 6000 Blackwell Server Edition.
- Kaggle selected Docker image digest
  `2757e0c7d1e0a9cb43da657b97e223c321a98f5014bdf64f44f2f6b083ad2b2f`.
- That image ran `/usr/bin/python3` as Python 3.13.
- The attached offline wheelhouse contains CPython 3.12 wheels. Pip stopped first at
  `aiohttp==3.13.5`, reporting no compatible distribution.
- Setup exited before vLLM startup, model smoke testing, benchmark construction, Duck execution or
  any environment action.
- Downloaded log SHA-256:
  `98ebff6d345c5113176768beae9b5d7249d838472b039a23ae0137b6eef61ff4`.

## Comparison with the successful v6 runtime

Kaggle's recorded metadata for v6 names Docker image digest
`37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`.
The v6 log shows Python 3.12, successful installation of the same `aiohttp` wheel and successful
vLLM startup. V7 version 1 and v6 otherwise used the same GPU shape, model and wheelhouse dataset.

## Supported conclusion

This is Kaggle base-image drift, not evidence about the v7 contract-repair architecture or model
behavior. No gate may be graded from this run.

## Repair

Keep the frozen v7 source dataset and notebook byte-identical. Push notebook version 2 with a
runtime-only metadata overlay that pins the exact successful v6 Docker image digest. The overlay
must verify the notebook SHA-256 before launch.

— **Sol**

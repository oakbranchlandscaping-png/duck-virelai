# Build slice: G3 live runbook and certificate evaluator

**Date:** 2026-09-22  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

`inference/framework/g3_checkpoint.py` evaluates a served trace against the G3 checkpoint without
using score or a guessed win. It checks world-arm selection, strict target ranking, counter mask and
monitor exposure, persistent entity dossiers, evidence-bound explanations, separate confirmation,
honest unresolved handling, no-win guessing, and terminal lifecycle states.

`G3_LIVE_CHECKPOINT_RUNBOOK_2026-09-22.md` defines the launch, trace-retention, stop, and review
procedure. The evaluator returns a versioned certificate with per-check evidence references and
explicit limitations.

The evaluator has a synthetic complete CLICK trace test. That proves the certificate logic only;
it is not a served Duck result. A live pass requires the actual package, model trace, and final
snapshot from a controlled run.

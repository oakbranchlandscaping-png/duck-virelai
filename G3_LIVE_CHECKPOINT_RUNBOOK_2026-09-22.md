# G3 live checkpoint runbook

**Evidence state:** exact-Qwen Kaggle notebook v2 completed; vc33 G3 exit failed  
**Source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`

This checkpoint grades the G3 products only. It does not grade game score, level completion, or a
guessed win. Keep the source package, notebook output, raw event trace, gate snapshot, and
certificate in separate run directories.

## Before launch

1. Freeze the exact package identity and record its source and manifest hashes.
2. Bind the actual metadata action surface and record the selected world type:
   `CLICK_GOD_MODE`, `NAVIGATION`, or `HYBRID`.
3. Confirm that the G2 product contains the ranked frontier and counter mask. If either is absent,
   stop before G3.
4. Allocate the runtime from the measured benchmark start, leaving the teardown reserve. Do not
   silently shorten the behavioral window.
5. Configure one controlled world first. Add more worlds only after the single-world trace is
   reviewable.

For the current three-world exact-model compatibility checkpoint, that single-world prerequisite
was supplied by the earlier local vc33 and ls20 diagnostics. The frozen run keeps vc33, ft09, and
ls20 sequential and grades every world independently. Its infrastructure and recovery record is
`INFRASTRUCTURE_G3_QWEN36_KAGGLE_CHECKPOINT_2026-09-23.md`.

## During the run

The trace must retain every `next_probe`, admitted action, lossless outcome, gate event, and final
G3 snapshot. The reviewer should see:

- the correct world arm and strict visual ranking;
- a counter mask and a counter-monitor field on every attributed transition;
- persistent entity ids across transitions;
- a dossier answer tied to immutable evidence for every positive witness;
- a separate `CONFIRM_LEVER_WITNESS` transition before any positive target is advanced;
- explicit null, ambiguous, and boundary dispositions;
- no `WIN_GUESSED` or equivalent claim;
- an immediate stop once the G3 enumeration and confirmation obligations are complete.

Do not keep querying a closed G3 gate until the notebook deadline. The run should emit the final
snapshot and stop.

## After the run

Call `evaluate_g3_checkpoint(trace, world_type=..., final_snapshot=...)` and save its returned
`virelai-g3-checkpoint-certificate-v1` JSON beside the raw trace. Grade only from the certificate
and supporting evidence:

- `PASS`: all checks pass and the trace is a served-model run;
- `FAIL`: any contract check fails;
- `BUILT, LIVE UNCONFIRMED`: local replay or synthetic traces pass, but no served run exists.

The certificate does not promote a builder report or replay to live evidence. A passed G3
certificate opens G4 only for the documented entities and deferred boundary observations.

## Kaggle packaging preflight learned from the current run

Exclude `runs/`, `.DS_Store`, caches, tests, and virtual environments before constructing the
source manifest. When `src.zip` is an explicit verified artifact, upload with directory handling
disabled so the CLI does not create a second archive with the same name. Confirm the private
dataset reports `ready` before pushing the notebook. A manifest failure before model startup is an
infrastructure failure and carries no gate result.

The current run also proves that a per-world receipt is insufficient when a shorter notebook-wide
soft deadline governs all worlds after model startup. Future packages must bind and validate both
budgets. A certificate must fail when the gate remains active, no accepted inventory exists, or an
entity reaches `G4-READY` without a supported positive confirmation. See the completed review at
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/REVIEW_V2.md`.

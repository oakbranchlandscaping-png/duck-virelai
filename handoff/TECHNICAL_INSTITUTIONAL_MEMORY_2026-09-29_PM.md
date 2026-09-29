# Technical institutional memory — Cybernetic Duck (2026-09-29, PM)

**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29.md`, which is
kept in place. The 2026-09-28 evening file remains the reference for the v2 run, the survey, the
constraints and D1–D7.
**Governing now:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `BUILD_PLAN_G4_CLICK_COMPLETION_v8_2026-09-29.md`

## Where things stand

| Stage | Label | State |
|---|---|---|
| M-0 instruments | R9-R06 | Committed `1a4b6bd` |
| M-1 slot-built card | R9-R07 | Committed `ee826ab`; Mac 431 passed |
| M-2 controller executor | R9-R08 | **Built; cloud 449 passed, 1 skipped; awaiting Mac pytest (expect 450) and commit** |
| M-3 recall and orientation | R9-R09 | next |
| M-4 G4 economy and lives | R9-R10 | planned |
| M-5 Kaggle package and throughput run | — | after M-4 |

## The Mac test command

The environment does not put the bundled framework (`taaf`) on the path by itself. Always run:

```
cd ~/Desktop/virelai-review/duck-virelai/variants/ring9-cybernetic-gates/ARC3-Inference && PYTHONPATH=../tufa-arc-agi-framework/src .venv/bin/python -m pytest -q tests 2>&1 | tail -3
```

Quote expectations as full-suite counts, never as deltas on an earlier figure. (The "409" once
reported for R9-R06 was a run that did not collect the whole suite.)

## Builder notes

- **Cloud test command.** `PYTHONPATH=.:tests:../tufa-arc-agi-framework/src
  /home/claude/g4build/.venv/bin/python -m pytest -q -p no:cacheprovider tests`
- **Read-only checks on the Mac repo.** Use `git --no-optional-locks status`. A plain `git status`
  from the session left an `index.lock` that the session cannot delete.
- **Who owns a step** is decided in one pure function, `controller_executor.next_owned_step`. It
  calls `next_probe_capability()` *before* `gate_view()`, because the capability call can advance
  a gate (G3 completes its roster there). Any code reading gate state must keep that order.
- **The recording protocol** (`machine.protocol`) is stamped on every probe envelope. A replay
  honours the protocol a record was made under. Records without it predate D5.
- **The escape hatch.** `VIRELAI_CONTROLLER_EXECUTOR=0` turns the executor off in gated mode.
- **`tests/ft09_world.py`** is the offline ft09 continuation. **`tests/card_duck.py`** is the
  card-only Duck. Both are acceptance instruments for every later stage.

## Immediate handoff actions

1. Mac pytest (expect 450 passed), then commit R9-R08 with explicit paths.
2. The Director rules on the five R9-R08 deviations (slice, "Deviations").
3. Build M-3 (R9-R09):
   - the orientation turn at G3 close;
   - the UNCERTIFIED lane for Duck's annotations (D6);
   - injected recall;
   - `virelai('memory', …)`.
4. Director-owned and still open:
   - the A7 ruling;
   - confirming the Kaggle runtime and game count;
   - key rotation and G3-era dataset cleanup.

— Claude, Alpha build seat, 2026-09-29

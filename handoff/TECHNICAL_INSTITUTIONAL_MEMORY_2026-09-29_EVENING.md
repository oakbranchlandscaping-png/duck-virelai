# Technical institutional memory — Cybernetic Duck (2026-09-29, evening)

**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_PM.md` (kept in
place; its test commands and builder notes still apply).
**Governing now:**
- `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` (RATIFIED)
- `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`
- `BUILD_PLAN_G4_CLICK_COMPLETION_v9_2026-09-29.md`

## Where things stand

| Stage | Label | State |
|---|---|---|
| M-0 instruments | R9-R06 | Committed `1a4b6bd` |
| M-1 slot-built card | R9-R07 | Committed `ee826ab` |
| M-2 controller executor | R9-R08 | Committed `2941f53`; Mac 450 passed |
| M-3 recall and orientation | R9-R09 | **Built; cloud 460 passed, 1 skipped; awaiting Mac pytest (expect 461) and commit** |
| M-4 G4 economy and lives | R9-R10 | next |
| M-5 Kaggle package and throughput run | — | after M-4 |

## Test commands

**Mac:**

```
cd ~/Desktop/virelai-review/duck-virelai/variants/ring9-cybernetic-gates/ARC3-Inference && PYTHONPATH=../tufa-arc-agi-framework/src .venv/bin/python -m pytest -q tests 2>&1 | tail -3
```

**Cloud:**

```
PYTHONPATH=.:tests:../tufa-arc-agi-framework/src /home/claude/g4build/.venv/bin/python -m pytest -q -p no:cacheprovider tests
```

## Builder notes (additions)

- **Every pull must fit `PULL_CHARS`.** The sandbox prints each `virelai()` result as indented
  JSON, and the tool result is capped near 4,096 characters, so a result over about 1,800 compact
  characters would reach Duck truncated. `MemoryStore.query` fits every result. A new pull kind
  must go through it.
- **Orientation is enforced in the tool layer**, not in gate logic. `orientation_due(machine)` is
  the single test of it.
- **Notes live on `machine.annotations`.** No gate reads them. Anything that makes a note matter
  must go through a gate (D6).
- **Do not `git stash` in the cloud tree.** It tracks `__pycache__`, and running Python while
  stashed blocks the pop. Compare against a commit with `git show` instead.

## Immediate handoff actions

1. Mac pytest (expect 461), then commit R9-R09 with explicit paths.
2. The Director rules on the five R9-R08 deviations.
3. Build M-4 (R9-R10), per DESIGN v2 §5.5 and §6 and rulings D3 and D4:
   - the G4.1 split: the controller certifies the anatomy, and Duck explains;
   - the G4-A split: the controller runs each lever to its endpoint, and Duck explains each
     confirmed orbit;
   - the lives rule: a game over on the same level is a life boundary, and the world model
     persists;
   - the time and action wake conditions.

— Claude, Alpha build seat, 2026-09-29

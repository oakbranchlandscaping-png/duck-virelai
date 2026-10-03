# Upload status: ring9-carry-vc33-v6 (R9-R22 lever typing, pinned image)

**Date:** 2026-10-03
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v6.py`
**Slice:** `BUILD_SLICE_R9_R22_LEVER_TYPING_2026-10-03.md` (branch `r9-r20-level-entry`, commit `8656839`)
**Directive:** `DIRECTIVE_COMPETITION_ENDGAME_v1_2026-10-03.md` (3-hour window kept; expected GPU time stated below, per D-5)

## Identity

| Field | Value |
|---|---|
| Package | `kaggle/ring9-carry-vc33-v6` (225 files; source 218) |
| Package manifest sha256 | `7ab2027ae36918485dd077f6a3ad6390824e3f1621e48e74b5deb99a27a87132` |
| Source manifest sha256 | `b8df20cf1612e962489341338a1a4089aab571a3e24116b3cb055bdb35485dc0` |
| Source commit | `865683950e657d8ca080914dc4b9a67f7518892e` (`623ad58` + R9-R22), from the Director's `git archive` export |
| Image | pinned as in v4 and v5: `gcr.io/kaggle-private-byod/python@sha256:37c64f7d…` (Python 3.12), `docker_image_pinning_type: original` |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v6` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v6` |
| Expected GPU time | **At most about 3.3 GPU-hours:** setup plus model load (about 15 minutes in v5) and a 3-hour behaviour window. Less if the run ends early, since R9-R22's A2 rule ends stalls. Whether the notebook stops with the run is reported under I11. |

## What changed from v5

Only the source changed.
- **Source files:** exactly 5 shipped source files differ (`virelai_gates.py`, `g4_guided.py`, `controller_executor.py`, `life_record.py`, `lever_dossier.py`), plus one new file, `lever_repeat.py`.
- **Notebook:** differs only in two identity lines, its dataset name and its run label.
- **Benchmark pickle:** differs only in its two labels.
- **Unchanged from v5:** the setup command, the deploy target, the image pin, the datasets, the world (vc33), and the budgets (200 actions, 10,800 seconds).

**Preregistered criteria, new or amended:**
- **I9, amended (R9-R22 supersedes R9-R21 D4):**
  - A repeat press that differs from its witness keeps its grade and gains its repeat disposition.
  - It certifies the lever and wakes no Duck turn.
  - The controller's dossier states the repeat as observed.
  - G3 closes with the controller's inventory and the ladder moves to G4.
- **I10, new (G4-A typing):**
  - G4-A queues every lever in G3's level-2 inventory.
  - Each lever's card row carries its G3 repeat.
  - Every completed run reports mechanism and condition beside its `lever_class`.
- **I11, new (A2 as the general rule):** a state with no probe, no acceptable answer and no declared end is ended within three watchdog checks. Also reported: whether the notebook's end followed the run's end.

**Marker guards:**
- The packager refuses a source that lacks the R9-R22 markers, or that still carries R9-R21 D4's `_bound_contradicted`.
- R9-R20 D2's operation list is no longer required, because D11 replaced it.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (`8656839`) | **8/8** |
| Export against the cloud R9-R22 tree | Identical, apart from a lint cache |
| Mount simulation, three layouts, with the two dependency datasets mounted | **All pass** (nested, zip, direct) |
| G4-entry pre-flight (`tools/check_level_two_g4_entry_from_record.py`), on the **packaged** source with the v4 live record | Rests at **G4.2-LEVER-ORBITS**, legal (PROBE), Duck's turn. G3's inventory lists E0004–E0007, with nothing ambiguous. G4-A queues all four: E0004 held after its repeat; E0005, E0006 and E0007 each reached a third state. Exit 0 |
| Tamper: one byte appended to `controller_executor.py` | Refused (4 FAIL) |
| Suite at `8656839` | Cloud 523 passed, 1 skipped; Mac (worktree) 523 passed, 1 skipped |

## What the run should show

- **Setup and level 1:** as in v5. The first 26 gate events should be byte-identical (I6).
- **Level 2 through t47:** the same clicks as v5, and the carry graded 4/4 RECONFIRMED.
- **New from there:**
  - no Duck turn at E0004's or E0005's repeat press;
  - the controller's dossiers for all four levers and its inventory;
  - then G4-A, starting with Duck's orientation turn, studying all four levers.

**Hypotheses, not findings:**
- From the board G4-A starts on, E0004 may type `UNKNOWN` with the condition SATURATED at that state, while its G3 pair says it moved once, then held.
- E0005 may keep revealing new states until it holds.
- The likely limit is the action budget: 47 of 200 actions were used through G3.

## Director's steps

1. I'll put the package, packager and this record in place. You run `verify_kaggle_package.py` on the Mac.
2. Commit on `main`, staging explicit paths.
3. `kaggle datasets create -p kaggle/ring9-carry-vc33-v6/source-dataset -r skip`, then `status` until it says `ready`.
4. `kaggle kernels push -p kaggle/ring9-carry-vc33-v6/kernel`

— Claude, Alpha build seat, 2026-10-03

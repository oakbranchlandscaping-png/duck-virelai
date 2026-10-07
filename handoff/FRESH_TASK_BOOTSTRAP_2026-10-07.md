# Fresh-task bootstrap: Cybernetic Duck, Ring 9 single tree

**Updated:** 2026-10-07
**Author:** Claude (Alpha build seat, click line), signed
**Supersedes:** `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29_NIGHT.md`. That file is kept in place and is historical: it predates the NAV merge, controller-first G4 and submission mode.
**For:** a new collaborator, or a fresh session of either Alpha seat. Read this, then the documents in §3, before editing or running anything.

## 1 · Who does what

| Seat | Role |
|---|---|
| **Director** (Stephen) | The only human. Runs every Mac terminal command, every `git commit` and push, every Kaggle action and the Mac test floor. Rules on plan- and architecture-level questions. |
| **Claude**, Alpha build seat, click line | CLICK gates, memory, submission mode and packaging, learn to win (the W-series). Builds and tests in a cloud sandbox and delivers files to the Mac; the Director commits them. |
| **Sol**, Alpha build seat, NAV line | NAV gates (ego bearings, routing, contact, reachability) and NAV G4. |

The seats correspond by signed documents (`REVIEW_…`, `REPORT_…`, `RECORD_…`) committed to the repo. A friction is routed by altitude first: code, architecture (to the Director) or plan.

## 2 · The tree and the branch rule

- **Repository:** `duck-virelai` (private remote `oakbranchlandscaping-png/duck-virelai`).
- **The only editable runtime source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`, with the vendored framework beside it in `variants/ring9-cybernetic-gates/tufa-arc-agi-framework/`. Everything else under `variants/` is a donor or history.
- **Branches.** Since 2026-10-05 there is one tree.
  - All work commits to **`ring9-unified`**.
  - **`main` only fast-forwards after a Mac floor passes.**
  - **Kaggle packages are built from `main`.**
  - The old lines are frozen provenance: `r9-r20-level-entry` (click, `c9b246b`) and NAV's `main` before the merge (`aa799b5`).
- **Checkouts on the Mac:**
  - the main checkout: `~/Desktop/virelai-review/duck-virelai`, on `main`;
  - the worktree: `~/Desktop/virelai-review/duck-virelai-r9r20`, on `ring9-unified`.

  Never run `git worktree prune`.
- **The floor.** Run from the worktree's `ARC3-Inference/`, using the main checkout's virtual environment:

  ```
  PYTHONPATH=.:tests:../tufa-arc-agi-framework/src ~/Desktop/virelai-review/duck-virelai/variants/ring9-cybernetic-gates/ARC3-Inference/.venv/bin/python -m pytest -q
  ```

  Current floor: 619 passed, 1 skipped (`RECORD_RING9_TEST_FLOOR_v1_2026-10-07`).
- **Pushes** need `git -c http.version=HTTP/1.1 -c http.postBuffer=157286400 push origin <branch>`.

## 3 · Read in this order

1. `STATE_OF_THE_DUCK_BUILD_v2_2026-10-07.md`: where everything stands, what is open, the honest ledger.
2. `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04.md`: the calendar, the model rule and the GPU quota.
3. `RECORD_RING9_SINGLE_TREE_AGREEMENT_v1_2026-10-05.md` and `UNIFICATION_RING9_SINGLE_TREE_v1_2026-10-05.md`: the merge, the shared first-witness law (G3 discovers, G4 types) and the split of work.
4. `REPORT_SOL_SINGLE_TREE_NAV_AND_NEXT_WORK_v1_2026-10-06.md` and `REVIEW_SOL_SINGLE_TREE_REPORT_v1_2026-10-06.md`: the whole tree as read at source (G0 to play, ownership, CLICK, NAV, HYBRID), and where the seats agree and differ.
5. `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md`: axioms A1 to A6. Every friction is routed here first.
6. `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`: the record, the certified world model and the card.
7. **The rulings in force:**
   - `RULING_G4_CONTROLLER_FIRST_v2_2026-10-04.md`;
   - `RULING_MU_BUCKET_v1_2026-10-03.md`;
   - `RULINGS_PORT_AND_PILLARS_v1_2026-10-04.md` (R-1 to R-8).
8. **The current plans:**
   - `BUILD_SLICE_SUB_1_SUBMISSION_MODE_2026-10-06.md` (submission);
   - `BUILD_PLAN_RING9_CELL_SITE_TARGETING_v1_2026-10-06.md` (NAV G1→G3);
   - `BUILD_PLAN_G4_NAV_COMPLETION_v1_2026-10-01.md`;
   - `BUILD_PLAN_PORTS_AND_PILLARS_v1_2026-10-04.md` and `BUILD_SLICE_LW_1_RELATIONS_REFEREE_LEDGER_v1_2026-10-06.md` (learn to win).
9. **The latest live reviews:**
   - `REVIEW_RING9_CARRY_VC33_V8_KAGGLE_2026-10-06.md` (CLICK, G4 controller-first);
   - `REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md` (NAV, the G1→G3 boundary).
10. `PREREG_SMALL_MODEL_GLASS_ENGINE_v2_2026-10-01.md`: the paper's preregistration and its held-out worlds, which the build seats never read.

`DOCUMENTATION_INDEX_2026-09-20.md` maps every older document. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` still states the engineering rhythm, but its branch and status sections predate the single tree.

## 4 · How a change reaches Kaggle

1. Build and test in new files where possible. A shared file gets only a thin hook, announced in a signed document.
2. The Director commits on `ring9-unified` (explicit paths only), runs the Mac floor, then fast-forwards `main`.
3. The Director exports the commit (`git archive <commit> -- variants/ring9-cybernetic-gates/ARC3-Inference variants/ring9-cybernetic-gates/tufa-arc-agi-framework`). The packager runs against that export, never against the working tree.
4. Packagers live in `tools/`:
   - `package_ring9_unified_canary_v1.py` (canaries, including Sol's ls20 profiles);
   - `package_ring9_submission_v1.py` (`VIRELAI_SUBMISSION_MODE=dryrun|submit`).
5. Verify with `tools/verify_kaggle_package.py --source-export <export> <package>`; expect 9/9. Where Linux is available, also run the mount simulation (`tools/simulate_kaggle_submission_mounts.py`).
6. Upload:
   1. `kaggle datasets create -p kaggle/<package>/source-dataset -r skip`;
   2. wait for `kaggle datasets status` to report `ready`;
   3. `kaggle kernels push -p kaggle/<package>/kernel`.
7. Every package has an `UPLOAD_STATUS_…` record with:
   - its hashes;
   - its preregistered criteria;
   - its expected GPU-hours (about 30 GPU-hours a week are shared by all seats).
8. After the run:
   - `kaggle kernels output <kernel> -p runs/<run>/output`;
   - check that the downloaded `execution_receipt.json` is byte-identical to the package's;
   - grade from artifact state (turn ledger, gate events, gate answers, probe envelopes), never from prose.

## 5 · Rules that are never bent

- **Staging.** Never `git add kaggle/`, `git add -A` or `git add .`. Stage explicit paths. `runs/` and `kaggle/` stay local.
- **The working tree.** Never reset or clean it. Never edit another seat's files without a correspondence.
- **Secrets.** Never print one. The G3-era bundles carried API keys (`INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27`, still OPEN).
- **The firewall.** No world's name, colour, position or mechanic enters the solver, a test's logic or a probe heuristic. Game environment files are used only as an arcade directory and are never opened. Exposure to any world's mechanics is declared in a signed document.
- **Documents.**
  - Named `TYPE_NAME_vN_YYYY-MM-DD`; the highest version is current.
  - Revised by a new version, never edited in place. The README and the documentation index are maps and are kept current.
  - Signed by their author.
  - Every claim tagged as observed (at file:line or a commit) or inferred.
- **Evidence.** A frozen package and its run are immutable evidence about the bytes that ran. A source change is evidence only after a new package runs.

— Claude, Alpha build seat (click line), 2026-10-07

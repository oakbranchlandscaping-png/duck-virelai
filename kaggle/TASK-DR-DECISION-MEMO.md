# TASK D-R DECISION MEMO — environment files
**Date:** 2026-08-23 · **Chamber:** Cowork · **Per:** WO-1 Addendum Task D-R
**Decision recommended: NONE OF THE THREE. No harvest, no env files in the bundle — rebuild
the kernel with Tufa's share variant, which uses the competition's own env files in-session.**

## R2 — Why Phase A failed (mechanism proven from artifacts)

The pickled benchmark in bundle v1 carries, in every game:
`ArcadeSpec(operation_mode=OFFLINE, environments_dir='__auto__')`.
The frozen build **rejects `__auto__` at play time** — `taaf/game_api.py::_resolve_environments_dir`:
*"Offline env files (the '__auto__' mode) are not bundled in this build. Pass an explicit
environments_dir."* Tufa stripped their private env-file repos from the public share
(`_SHARE_EXCLUDE_REPOS` in `deploy_kaggle.py`) and made auto mode a loud error.

Bundle v1 used TAAF's **generic** kernel template (`taaf_kaggle_run.ipynb`), which plays the
pickled games directly in a non-submission run → deterministic failure at the first game.
Claim: **MATCH** (both artifacts read from the frozen tree and the v1 bundle). The observed
Kaggle log is NOT_MEASURED in this chamber — Director's log tail would confirm the error
string, but the mechanism does not depend on it.

## R2 (cont.) — How Tufa's real entry solved it

`--kaggle-make-share-version` selects the **share** kernel template (the notebook at the
repo root — the one that survived their submission). It **ignores the pickled game specs**
and rebuilds `bm.games` at runtime:
- **Phase A (interactive):** offline games from the **competition dataset mount** —
  `/kaggle/input/competitions/arc-prize-2026-arc-agi-3/environment_files` ("the
  competition's environment files ship alongside the wheelhouse in the competition
  dataset" — their comment, their precedent).
- **Phase B (rerun):** the live gateway (`http://gateway:8001/`), no env files at all.

So the v2 fix is **one flag on the same build command**: `KAGGLE_MAKE_SHARE_VERSION=true`.
No env files ride in our dataset in either phase.

## R3 — Publication precedent

Tufa's public source dataset shipped **no environment files**; their share flow excludes
the private env repos and leans on the competition mount. Read from the frozen deployer
(**MATCH**); their live dataset file listing on kaggle.com not re-checked (NOT_MEASURED —
optional, the code precedent is sufficient). Milestone-day implication: we ship none
either; the games' content never enters our published artifact.

## R1 — Local cache inventory (for the record; not needed for the Kaggle path)

| location (under ARC_3_BETA) | games | downloaded | currency vs frozen harness's official-25 list |
|---|---|---|---|
| `arc-prize-2026-arc-agi-3/environment_files/` | **all 25** | 2026-03-23 | **10/25 version-match; 15/25 STALE** (e.g. cache `vc33-9851e02b` vs official `vc33-5430563c`; `tn36-ab4f63cc` vs `tn36-ef4dde99`) |
| `environment_files/` (root), `Universal_Solver_v1/`, `Universal_Solver_v3_5/`, `virelai_kaggle_submission/…` | 3 (ft09, ls20, vc33) | Jan–Feb 2026 | older still |

Matched 10: bp35, cd82, ft09, g50t, lf52, lp85, ls20, sb26, tr87, wa30. The stale 15
confirm the version-drift concern — the March cache must NOT seed a baseline. It remains
useful later only for the local competition-arcade simulator, and only after a fresh
harvest (the Director's 5-minute capsule) — deferred until local simulation is actually
wanted.

## R4 — Decision requested

**Rebuild bundle v2 with `make kaggle-duck KAGGLE_DRY_RUN=true KAGGLE_MAKE_SHARE_VERSION=true`**
(same refs, same frozen config; kernel slug gains Tufa's `-share` semantics or keeps ours
explicitly), Director re-pushes the kernel only (dataset unchanged), Phase A re-runs on the
competition-mounted env files. Cost: minutes of chamber time, one kernel push, no quota
beyond the re-run. No harvest. No env files published. The v1 failure cost zero submissions
(Phase B was never clicked) — the dry-run did exactly its job.

**How this could be wrong:** if the competition dataset no longer mounts
`environment_files/` in interactive sessions (it did at Milestone 1, per Tufa's template),
Phase A v2 fails with a path error — that halt names the fallback (starter kit carrier, or
shipping current env files after an ARC Prize licensing check, which R3 flags as the only
option that publishes their content).

**Not done, per the addendum:** no fresh harvest, no bundle build, no push, no baseline edits.

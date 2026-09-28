# Technical institutional memory — Cybernetic Duck

> **Superseded for current state (Claude, 2026-09-27 evening):** read `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md`. This file remains the reference for the S1 build, the dotenv key incident, and the ranked risks below.

**Date:** 2026-09-27
**Author:** Claude (Alpha build seat, outgoing) — signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-26.md` (still the
reference for the counter doctrine, G0–G4.2 direct evidence and the gate spine; not repeated here)
**Builder method:** `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/` at `f8a967e`

## Where things stand

- **S1 (Phase-1 drain return edge) is built and offline-green.** G4.2 now holds until every
  confirmed lever is orbited and classified; G4.3 is guarded behind that. See
  `BUILD_SLICE_G4_PHASE1_DRAIN_RETURN_EDGE_2026-09-27.md`.
- **Its first live test is running on Kaggle:** notebook
  `stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`, version 1, launched 2026-09-27, vc33,
  `Qwen3.6-27B-FP8`, 160 actions / 7,200 s. Ungraded. See
  `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md` and grade with
  `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md`.
- **The OpenRouter rung was skipped by the Director's ruling.** It could not run: OpenRouter
  returned 402 `weight_exceeds_budget` because each request's pre-authorized maximum cost exceeded
  the account balance. The Director ruled Kaggle the test venue for the Duck. This is a recorded
  deviation from protocol §8 and `BUILD_RHYTHM.md`; see the infrastructure record for its grading
  consequence.
- **Security incident open:** API keys shipped inside the G3-era Kaggle bundles. Keys must be
  rotated. See `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md`.

## Commit ledger since the 2026-09-26 memory (verified from `.git/logs/HEAD`)

All authored by Claude (Alpha build seat) and committed by the Director on the Mac.

| Commit | Date | What |
|---|---|---|
| `9683181` | 2026-09-26 | Ring 9 anchor: first commit of the Cybernetic Duck gate build (the tree had been uncommitted since `0efc7ca`, 2026-08-30). Surgical staging; `runs/` and `*.egg-info/` added to `.gitignore`. |
| `1bf09e0` | 2026-09-26 | G4.3 seed crash fix on recurrence orbits; production-faithful G4.3 fixture. |
| `73d7475` | 2026-09-26 | Two-phase lever-study doctrine (LOCKED) and the Phase-1 drain build plan. |
| `c3e47ff` | 2026-09-26 | Two-phase upgrade banners propagated to the protocol, index, memory and bootstrap. |
| `495ded5` | 2026-09-26 | S1 part: Phase-1 lever classification on the G4.2 orbit product. |
| `f8a967e` | 2026-09-26 | S1: pending-lever return edge and G4.3 guard. |
| `777dc39` | 2026-09-27 | G4 S1 Kaggle checkpoint: `kaggle/ring9-g4-phase1-drain-v1/` and `tools/package_g4_phase1_drain.py`. |

The documentation and verification tools added with this memory are committed separately after it.

## Direct evidence added since 2026-09-26

- Offline suite at `f8a967e`: 374 passed (Director, Mac); 373 passed + 1 artifact-gated skip on an
  independent `git archive` of the same commit.
- The G4 package passed static verification, executed-notebook startup in three mount layouts,
  and two negative controls before upload (infrastructure record).
- Kaggle runtime evidence for budgeting: gated G3 on `Qwen3.6-27B-FP8` ran about 66 s per action
  (G3-v3: 41 actions in 45 minutes).
- Qwen tool-call reliability on Kaggle: 1 of 212 responses lacked a tool call; never two in a row.

## Corrections to things said during the 2026-09-26/27 session

- The G3-v3 Kaggle output **was** downloaded and reviewed on 2026-09-24
  (`runs/kaggle-ring9-g3-vc33-closure-v3/REVIEW_2026-09-24.md`). An in-session claim that it was
  missing came from a truncated directory listing.
- The G3-v3 notebook machinery (receipt binding, benchmark-start deadline, nested `src.zip` mount)
  is **proven on Kaggle**; the G4 package inherits it. What remains unproven on Kaggle is G3
  *closure* on the exact model: G3-v3 confirmed both levers and then looped 31 actions on the
  counter object. The later repairs passed live on OpenRouter v8, not yet on Kaggle.
- The G4.2 orbits v3-live OpenRouter run (`...20260926_070833..._v3-live`) completed (25 actions,
  one level) but has **no filed review** in its run folder. Its seven criteria in the 2026-09-26
  memory remain ungraded on the record.

## Known gaps and risks (ranked)

1. **Keys not yet rotated** (incident report). Until the four G3-era package directories are
   scrubbed, never stage `kaggle/` wholesale.
2. **Target journal not persisted to run artifacts.** Product-level criteria (for example the final
   `LeverOrbitSet`) must be reconstructed from gate answers and events. Protocol §9 step 7
   ("verify active products and router state") cannot be done directly. Small slice: write
   `TargetJournal.snapshot()` to a per-game artifact on every product put.
3. **Newborn append not implemented.** The G4.2 lever queue is frozen at G4.1; new objects seen
   mid-orbit are recorded but not queued (slice S4).
4. **Reset-during-orbit guard.** `g4_orbits.py` treats only `done` / `level_completed` /
   `game_over` / `run_complete` as boundaries; a reset without those flags mid-orbit is unguarded.
   Close before NAV work.
5. **OpenRouter harness retries without backoff.** A 402 produced hundreds of immediate retries
   over the whole window. Honor `Retry-After` and cap attempts. This does not fix
   `weight_exceeds_budget`; that needs credits or a smaller `max_tokens` / context.
6. **Untracked infrastructure.** `tools/` (all earlier packagers) and every `kaggle/` package except
   G4 are untracked. The G4 packager's `BASE` (`kaggle/ring9-g3-vc33-closure-v3/`) is untracked
   and still contains the old key, so the G4 packager is not re-runnable from a clean checkout until
   that base is scrubbed and committed, or replaced.
7. **Stale deploy target.** `deploy_target.pkl` in every ring9 package still carries G0 labels. It
   is inert at runtime (infrastructure record) but misleading to readers.
8. **Local shell VM failure (session environment, not repo).** On 2026-09-27 the Cowork shell VM on
   the Mac stopped starting sessions ("failed to create bridge sockets") and a full app restart did
   not recover it; the file channel stayed healthy. Suspected cause: that VM's disk filled earlier in
   the session. Relevant only if a future builder sees the same error.

## Immediate handoff action

1. When the Kaggle notebook reports `complete`, retrieve, check the receipt, and grade with the
   runbook. Grade the precondition first.
2. File the run review; update the upload status.
3. If S1 passes, plan S2 (Phase-2 ABA/ABC sequences) per the build plan; consider the
   target-journal artifact slice first, since S2 grading will need it even more.
4. If S1 is ungraded because G3 stalled on Kaggle, compare against the G3-v3 review and repair G3
   on the exact model at one-world scale.
5. Keep the Director's open items visible: key rotation, dataset cleanup.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md`
2. this file
3. `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-26.md` (doctrine and earlier evidence)
4. `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md`
5. `BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1_2026-09-26.md`
6. `BUILD_SLICE_G4_PHASE1_DRAIN_RETURN_EDGE_2026-09-27.md`
7. `INFRASTRUCTURE_G4_PHASE1_DRAIN_KAGGLE_CHECKPOINT_2026-09-27.md`
8. `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md`
9. `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md`
10. `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md`
11. `runs/kaggle-ring9-g3-vc33-closure-v3/REVIEW_2026-09-24.md`
12. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat (outgoing), 2026-09-27

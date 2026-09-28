# Technical institutional memory — Cybernetic Duck (afternoon, 2026-09-28)

**Date:** 2026-09-28, afternoon
**Author:** Claude (Alpha build seat), signed
**Supersedes for current state:** `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28.md`
(morning). That file remains the reference for the day's rulings, the guided-v1 evidence, and the
A6 and A1 v2 notes for builders. This file does not repeat them.
**Current plan:** `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md` (revision ledger in §1)

## What changed since the morning memory

| Item | State | Record |
|---|---|---|
| R9-R04: G3 bounded card, counter trigger label | **Committed `8319853`**; Mac 393 passed | `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md` |
| **R9-R05: G3 entity identity survives recolour; ambiguity abstains** | **Built, offline-green (cloud 411 passed, 1 skipped); written to the Mac; awaiting Mac pytest (expect 400) and commit** | `BUILD_SLICE_G3_RECOLOR_IDENTITY_AND_FT09_LADDER_2026-09-28.md` |
| Planned labels | Moved up by one: G4-B is now R9-R06 and G4-C is R9-R07 | plan v5 §1 |
| Next live test | `ring9-g4-ft09-guided-v2`, packaged from the R9-R05 commit (not from R9-R04) | — |

## The finding, in one paragraph

- While measuring card sizes past G2 on the real ft09 record, I found that G3 would have filed
  both ft09 controls as `UNRESOLVED_ATTRIBUTION` and closed with zero levers.
- The cause: when a 6×6 control recoloured, the entity ledger counted unchanged same-colour
  6×6 tiles elsewhere as possible move sources. The control lost its identity, and in the
  one-other-tile case identities were silently swapped.
- R9-R05 enforces the contract's own rules: what persists is STILL; one exact source matches;
  several abstain.
- With it, the whole ft09 ladder runs offline, from the real G2 record through G4-A satisfied,
  in 131 of 200 actions. Every card fits, and the largest is 15,792 characters. The run
  continues the one observed control law by hypothesis.

## What a new builder must understand (additions)

- **Walk the whole ladder offline before a live run.** Continue the recorded world by its observed
  law and use the simplest card-following policy (`tests/test_ft09_ladder_offline.py` shows how).
  This pass found a defect that would otherwise have cost a two-hour Kaggle run.
- **Entity identity is structural and exact.**
  - Never let a persisting object be a source elsewhere.
  - Never resolve a tie by picking one candidate.
  - Continuity changes affect every world. Run the full suite, including the NAV ego and
    continuity-shadow tests.
- **The ft09 counter bar has finite capacity:** 64 cells at 2 per effective click, so about 32
  effective clicks. The offline ladder uses 15.

## Packaging note (from this session)

- Export the source for a package with both source paths. `tools/package_g4_ft09_guided.py`
  requires `ARC3-Inference` **and** `tufa-arc-agi-framework`:

  `git archive --format=tar.gz -o ../src_<commit>.tar.gz <commit> variants/ring9-cybernetic-gates/ARC3-Inference variants/ring9-cybernetic-gates/tufa-arc-agi-framework`

- The first R9-R04 export named only `ARC3-Inference`. It is superseded by the R9-R05 export and
  is not used.

## Immediate handoff actions

1. Mac pytest (expect 400), then commit R9-R05 with explicit paths, labelled.
2. Export the R9-R05 commit with both source paths. Package `ring9-g4-ft09-guided-v2` from the
   committed guided-v1 package. Preregister the v1 criteria plus G2-3, A6-1 and G3-1.
3. Run it on Kaggle and grade it.
4. Director decisions: ratify A7 or not; the G4 CLICK exit definition; newborn objects; key
   rotation and the cleanup of the G3-era datasets.

## Read order for a replacement builder

1. `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` (read its amendment banners first)
2. `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md`
3. this file, then `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28.md`
4. `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md`
5. `BUILD_SLICE_G3_RECOLOR_IDENTITY_AND_FT09_LADDER_2026-09-28.md`, then
   `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md`
6. `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`
7. `DOCUMENTATION_INDEX_2026-09-20.md` for everything else

— Claude, Alpha build seat, 2026-09-28

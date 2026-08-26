# Variant: ring25 — world type, the weave, and the ego

**Created:** 2026-08-26 · **From:** `variants/ring2` (89 files verified at copy) ·
**Design:** `DESIGN.md` (harvest table, seal shapes, fixtures) · **Ruling basis:**
Director's world-type ruling 2026-08-26 ("the available actions dictate the type of
world — NAV, click, hybrid; that lets the model know if it should look for an embodied
ego, or know it is in god mode") · R-H1 (the edge.py transcription — the one ruled
unit, now taken) · R-A (per-action covariance) · R3 (multi-ego set; worldline-level) ·
the navigation campaign's ∀→∃ ego-seal ruling · ring2 feedback (announce-delay).

## The one variable (vs ring2)

The ego stack: world-type derivation from the action roster + the light weave
(components → transcribed matcher → worldlines) + the existential ego seal + the
[WORLD]/[EGO] sealed reads — plus the counter announce-delay refinement.

## Diff surface

| file | change |
|---|---|
| `virelai_weave.py` | **new** — world_type derivation (replaces v4's classify_world_type + confidence ratchet, `library_sync.py:564`; ratchet = banned epistemology, concept harvested); minimal Region + 4-connected components (sealed-counter cells excluded per attribution-quarantine); **TRANSCRIBED `weave/edge.py` matcher** (three-pass SITE→CLASS→residual cascade, verb alphabet, cited per R-C); worldline threading (site-anchored across RESET back-edges — legal per canon 1 §2 byte-identical s₀); the EGO seal: MOVEd under ≥2 distinct directional labels with ≥2 distinct bearings — which-action covariance, ∃-shaped, PERMANENT (a later STILL is BLOCKED, never doubt); multi-ego as a set |
| `virelai_ledger.py` | v4: weave wired into record() (threading errors loud, never fatal); [WORLD] announced on roster-union change; [EGO] seal notes + per-turn position line; snapshot gains world_type/roster/ego/worldlines; counter seals now ANNOUNCED only after surviving one press beyond sealing evidence (mask still applies immediately — announcement gates attention, not mechanism) |
| `prompts.py` | contract: sealed reads now [WORLD]/[COUNTER]/[EGO] with [WORLD] as a GIVEN (roster derivation); strategy beat 2: confirm-don't-discover on NAV, skip-the-hunt on CLICK; `virelai` docs gain world_type/roster/ego/worldlines; **lockstep deletion:** the "do not assume a player exists" caution (replaced by the [WORLD] capability) |

Prompt: 2464 → 2513 words (+49 net). **Health-metric finding, flagged honestly:** growth
is the new sealed-read contract vocabulary ([WORLD]/[EGO]) minus this ring's deletion —
teaching for new machinery, not coaching creep. Watch next ring.

## Verification at creation (cloud, 2026-08-26)

py_compile ×3; solver imports in venv. Unit battery PASS: matcher MOVE/RECOLOR verbs
correct with deltas; world-type derivation (NAV/CLICK/HYBRID); NAV ego seals on 2
labels/2 bearings with correct bearing map; seal survives a blocked press (permanent)
and RESET (site-anchored back-edge); CLICK world announces GOD_MODE and runs no ego
search; counter announce-delay: mask immediate, announcement only after surviving one
press. Perf ~0.01ms/turn cached. **Live behavior NOT_MEASURED until the single
validation run** (Director's go required).

## Pre-registered fixtures (DESIGN.md)

NAV worlds: [WORLD] NAV + ego sealed in the opening + correct bearings in transcripts.
CLICK worlds: GOD_MODE + zero ego seals. Failure shape filed: driven objects moving
under 2 labels/2 bearings can false-seal into the multi-ego set (lever rung
disambiguates later).

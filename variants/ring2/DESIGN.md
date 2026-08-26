# RING 2 DESIGN — THE COUNTER: SEAL, MASK, TEACH
**v1 · 2026-08-26 · Cowork chamber · per the Director's build order ("build now with
high quality; use our documentation")**

## What this ring does

Three capabilities, one variable: (1) a behavioral COUNTER seal over churn regions;
(2) counter-masked node identity (the world grain) so the map converges on counter
worlds — G9's requirement, not an optimization; (3) the first sealed role taught to
the model, plus the Ring-2 lockstep prose deletions.

## Step-zero harvest (v4 as port source — Director's posture 2026-08-25)

| v4 source | lesson carried | disposition |
|---|---|---|
| `cycle_probe._hud_masked_state_hash` + WO-CP1-FIX-B | mask-then-sha256 IS the design; the scar: "the live counter tick changed every press hash and saturation never fired" (the K-cap burn) | transcribed in shape |
| `library_sync._build_hud_mask` | mask permanence across lives | superseded: our mask is recomputed from the record every turn (buckets drain); permanence emerges from stable evidence, is never stored |
| `contact_reactivity.extend_hud_mask_rows` | class-derived masks under-cover: a second counter (different class) shares the strip | root cause dissolved: our seal is behavioral, so each ticking region seals on its own evidence; no geometric row-prior imported. Fallback recorded if under-coverage observed |
| `contact_reactivity` 25%-delta LIFE_RESET filter | massive deltas are boundary events, not physics | threshold-free version: RESET edges and level-crossing edges never enter seal evaluation |
| `role_classifier` COUNTER rules | the catalog of counter shapes (strips, digit displays) | informs tests, never detection |

## The seal (counts and quantifiers only — no threshold anywhere)

Evidence base: the ledger stores, per edge, the changed-cell set (derived from stored
node grids), the action label, and level; RESET and level-crossing edges are excluded.
Candidate regions: 4-connected components of cells-that-ever-changed (current level).

**Region R seals COUNTER iff, over all eligible edges E:**
1. ∀ e ∈ E: R ∩ changed(e) ≠ ∅ — it ticked on EVERY press;
2. |{labels(E)}| ≥ 2 — which-action-invariance is unwitnessable with one label
   (R-A: counter keys on THAT any action occurred, not WHICH);
3. ∀ e ∈ E: |R ∩ changed(e)| is one constant — stable per-press magnitude;
4. when MOUSE edges exist: ∃ e with click coordinates outside R and R ticking —
   the not-acted-member witness (the `_marginal_counter_seal` evidence shape,
   R-H1a(iii)).

**One counter-witness kills:** any eligible edge on which R held unseals it, and the
seal is recomputed from the full record every turn — never remembered (bucket law).

**Pre-registered limitation (filed, not hidden):** an ego that moves on every single
press, under ≥2 labels, with constant changed-cell magnitude, and is never blocked,
can falsely seal. One blocked press (a STILL edge) kills it. Falsely masking an ego
merges states that differ only in ego position — visible as map pathology, reported
loudly by the mismatched-RESET/boundary machinery.

## The world grain (transcribed from `weave/world_grain.py`, R-H1a(v) shape)

Two grains, the raw one untouched: raw node keys and grids remain the append-only
record. The WORLD key is a view — sha256 over (level, grid with sealed-counter cells
replaced by a sentinel) — stamped by the mask that produced it. The world MAP is a
fold of the recorded edges under the current mask: recomputed when the mask changes,
appended-to otherwise (induced-map idempotent-fold shape). Digest, menu, Tier-A
subtraction, RESET root, and the `virelai` snapshot all read the WORLD map. When the
mask seals mid-game, previously-distinct raw nodes merge and revisits become
recognizable — the map converges exactly where G9 says it must.

**`world_changed`** rides every action payload: did anything OUTSIDE the mask change.
Tier-A seals on world_changed (a press that only ticked the counter is a proven no-op
— the fix that makes menu subtraction work on counter worlds). `board_changed` stays,
honest, beside it. The batch account reports the last WORLD change.

## Teaching (the sealed read + prompt surgery)

On seal, the digest carries: `[COUNTER] rows r0-r1 x cols c0-c1 (N cells) sealed:
ticked on all E presses under every action (m cells/press). Excluded from state
identity. Watch it -- likely your budget.` On unseal: a loud retraction line. Axiom 5
gains the Director's grounding note ("every state on the map is PROVEN not the win;
the win lives in what the map marks untried"). Ring-2 lockstep deletions fire:
the timer-bar paragraph, the "DON'T DO THIS!" paragraph, the after-every-action
HUD-verification ritual, and the background-hypothesis coaching — each replaced by
the machinery and axioms that now do the job. The `virelai` variable doc gains the
counter block and `world_changed`.

## Verification plan

Unit: synthetic counter world (bar ticking 1 cell/press under 3 labels) seals by
edge 3-of-2-labels and masks; blocked-ego world never seals; counter-witness unseals;
world-map merge recognizes revisits raw hashing missed; RESET root on world keys;
world_changed drives Tier-A. Prompt: implants present, Ring-2 deletions absent,
Ring-1 deletions still absent. Live: ONE validation run on the Director's go
(single-run feedback cadence, 2026-08-26); fixtures ls20/tn36 (counter worlds should
show revisit recognition + falling waste), still-board worlds (mask must never seal).

# RING 2.5 DESIGN — WORLD TYPE, THE WEAVE, AND THE EGO
**v1 · 2026-08-26 · per the Director's build order + world-type ruling ("the available
actions given by the arc grid world dictate the type of world we are in — NAV, click,
hybrid; that lets the model know if it should look for an embodied ego, or know it is
in god mode")**

## Three capabilities, one variable vs ring2

1. **World type from the action roster** (Director's ruling, 2026-08-26). The roster is
   interface metadata (G2) — so world type is a DERIVATION, not a classification:
   directional labels present & no MOUSE → NAV; MOUSE only → CLICK (GOD_MODE);
   both → HYBRID. Computed over the union of observed rosters, re-announced loudly if
   the union changes. Replaces v4's `classify_world_type` + confidence ratchet
   (`library_sync.py:564` — harvested concept, banned epistemology discarded).
2. **The light weave**: per-frame 4-connected components (sealed-counter cells
   excluded), threaded across edges by the TRANSCRIBED `weave/edge.py` matcher —
   R-H1's one ruled transcription: the three-pass cascade (SITE footprint → CLASS-held
   single licensed transform → residual), verbs STILL/RECOLOR/MOVE/GROW/SHRINK/BIRTH/
   DEATH/DEFORM/AMBIGUOUS. Worldlines thread across ordinary edges; across a RESET
   back-edge they thread by SITE+class only — legal because RESET returns s0
   byte-identically (canon 1 §2), so identity survives death at identical footprints.
3. **The ego seal** (∃-shaped, permanent — the navigation campaign's ∀→∃ ruling):
   a worldline seals EGO when it has MOVEd under ≥2 DISTINCT directional labels with
   ≥2 DISTINCT observed bearings — which-action covariance per R-A, counts only.
   Multi-ego is a set (R3). A later STILL press means BLOCKED, never doubt; the seal
   is permanent for the game. NAV/HYBRID worlds only — on CLICK worlds GOD_MODE is
   known from the roster and no ego search runs (null-locus, canon 2 §6.3).

Plus the ring2 feedback refinement: a counter seal is ANNOUNCED only after surviving
one additional evaluation beyond its sealing evidence (transient false seals stay
silent; the mask itself still applies immediately — announcement != application).

## Teaching

[WORLD] line once per game (and on roster-union change): "NAV world (roster: UP, DOWN,
LEFT, RIGHT): expect an embodied ego — find what moves with your presses" / "CLICK
world (roster: MOUSE): GOD_MODE — no avatar; your clicks are the hand" / hybrid.
[EGO] on seal: "the N-cell class-c shape is YOU. Observed: UP→(-1,0) ... A press that
does not move you means BLOCKED, not doubt." Position line on ego MOVE edges.
Contract's sealed reads: [COUNTER], [WORLD], [EGO]. Snapshot gains world_type, ego
(bbox/class/bearings), worldline count.

## Pre-registered fixtures for the single validation run

NAV worlds (ls20-class): [WORLD] NAV announced; ego seals within the opening; bearing
map correct in transcripts. CLICK worlds: GOD_MODE announced; zero ego seals. The
motion-coupled-drain finding (ring2): with the ego sealed, ls20's bar churn should now
be attributable as ego-coupled (groundwork for the coupling read — noted, not built).
Failure shape pre-registered: driven objects that move under 2 labels with 2 bearings
(e.g., an object pushed by the ego) can false-seal EGO — multi-ego set semantics keep
this survivable; the lever rung disambiguates later (drivers vs selves).

## Harvest table

| v4 source | lesson | disposition |
|---|---|---|
| `weave/edge.py` | the matcher cascade + verb alphabet | **TRANSCRIBED** (R-H1 ruled) with citation, RegionClay reduced to the minimal stand-in |
| `library_sync.classify_world_type` + ratchet | world type gates probing | concept kept; ratchet REPLACED by roster derivation (Director's ruling) |
| navigation campaign (STATE_OF_THE_CAMPAIGN_NAVIGATION) | the ∀→∃ ego seal fix; "blocked, not not-the-avatar" | seal shape carried |
| `collide_drive` doc ("observed, not bearings") | bearing maps record what was SEEN per label | EgoMap.observed shape carried |

# BUILD PLAN — POTENTIAL UPGRADES (HELD PENDING RING 7)
**Type:** BUILD_PLAN_POTENTIAL_UPGRADES · **Version:** v1 · **Date:** 2026-08-30
**Status:** PROPOSED. Nothing herein is chartered. **No construction begins
until the Ring 7 run returns and is graded.** This document exists so that
the moment the ring 7 read is in, the next ring is a selection, not a design
session.
**Sources:** the Ring 7 revelation (`REVELATION_RING7_v1`), the v3.5 spark
plug sweep (`SWEEP_V35_SPARKPLUG_v1`), the Director's post-6.3 ladder
(`BUILD_LADDER_POST_RING63_v1`), the outsider research bootstrap
(`BOOTSTRAP_OUTSIDER_REPORT_USE_v1`, results pending).
**Standing constraints on every item:** one variable per ring; the bar is
r0's 30.5, permanently; no game-specific knowledge anywhere; card authority
is never inflated beyond its evidence (the compliance hazard); the 6.3
transport gate is regression-tested in every ring that touches delivery.

---

## PART A — INSTRUMENTS (no run variables; buildable first, offline)

### U1 · Delta-novelty grader
**What:** an offline audit tool scoring every Duck action by measured
information gain — novel post-action state-delta hash vs repeat — ported
conceptually from v3.5's EntropySidecar (delta_hash / novel / entropy ratio).
**Why:** gives Layer B a mechanical, echo-proof metric: "the action produced
novel evidence" is measured from the world, never from the model's prose.
**Inputs:** existing run artifacts only (transcripts, events.jsonl,
benchmark). Runs retroactively over ring 6.3 and ring 7 outputs.
**Exit:** per-game novelty curves for both runs; a calibration note
comparing high-novelty vs low-novelty games against score.
**Risk:** none to any run — pure evaluation.

### U2 · Declaration validator
**What:** an offline check that anything Duck claims to act on — a target, a
gap, a briefed fact — exists in the delivered card and/or the frame at the
time of the claim. Logs agreements and fabrications; vetoes nothing.
**Why:** makes Ring 6.6's markers verifiable by content (the ladder's own
requirement) and detects report-fabrication, the failure the (0,0)
catastrophe teaches us to expect from defaulting parsers and confident
models.
**Exit:** per-game fabrication/agreement counts over ring 6.3 and ring 7.
**Risk:** none — offline.

Instruments U1+U2 are the recommended FIRST build after the ring 7 grade,
possibly graded WITH ring 7 as their calibration data. They implement the
measurement layer every later upgrade is judged by.

## PART B — RING UPGRADES (each requires a charter; evidence gates named)

### U3 · Ring 6.6 as the vocabulary contract (+ ordinal handles)
**What:** the Director's 6.6 use-contract, sharpened by QSPI's structural
rule: Duck's first-turn Goal must name a GAPS entry and its Prediction must
cite a briefed claim — the card's contents are the only legal fill for the
contract's fields ("never invent class IDs not present in the field card").
Paired renderer change: stable ordinal handles on every object/lever/gap
(Object 3, Lever B, Gap 2) so citation is exact and grading mechanical.
**Evidence gate:** ring 7 transport passes AND Layer B shows use is present
but unmethodical (the 6.3 pattern). If ring 7 shows strong spontaneous
method, U3's priority drops.
**Ruling required:** the handles are a card-wording change, frozen under the
current ladder — Director must fold them into 6.6's charter explicitly.
**Grading:** U1+U2 metrics, plus the ladder's six yes/no questions.
**Risk:** ritual compliance (boilerplate sections over real method) —
detected by U1: a "prediction" whose test action yields no discriminating
delta is ritual.

### U4 · Bounded refreshed projection (durability) — TRIPWIRE-GATED
**What:** v3.5's durability answer inverted into Duck's loop: a small,
verified-facts-only, OVERWRITTEN re-projection of the card's stable facts
(bearing map, sealed roles, open gaps) available each turn — tool-served or
single-line. Bounded ceiling; no invention; no accumulation.
**Evidence gate (the tripwire):** ring 7 transcripts show card-use decaying
as the card ages out of retained history (~30 turns). If use does NOT decay,
U4 is not built.
**Risk — named plainly:** this is structurally what rings 1–5 attempted and
botched. The differences that made v3.5's version work are load-bearing:
verified content only, hard ceiling, overwrite-never-append. Any drift
toward inventive or accumulating projection recreates the deleted layer.
One variable vs ring 7; killed at the first sign of score regression.

### U5 · Library B analog — the curated mechanism card (the ontology arm, reborn)
**What:** a stable, game-agnostic second card beside the empirical one,
modeled on v3.5's Library B: mechanism primitives (NAV, TOGGLE, COLLECT,
TARGET, PUSH, TRANSFORM, COUNTER, UNLOCK), diagnostic signatures, strategy
heuristics. Concrete, mechanism-level "above the model" structure — a
sharper form of the ontology the minimal hybrid deliberately excluded.
**Evidence gate:** ring 7's own number is in; U3 (or ring 7 itself) shows
the model uses what it is handed. This is the parked ontology A/B slot: one
variable on the ring 7 base.
**Risk:** prompt-mass regression on the pristine host — exactly what the
revelation warns about. Charter includes a hard size ceiling and a paired
no-Library-B control read.

### U6 · Win-packet vocabulary constraint (rider on Ring 6.5)
**What:** when Ring 6.5's win packet is built, its "candidate explanation"
and "competing explanations" sections are constrained QSPI-style: every
explanation must reference recorded transition facts by handle; free-floating
explanation text is nonconforming. Not a new ring — a design constraint
written into 6.5's charter now, costing nothing.
**Evidence gate:** none needed; it is a specification rider, adopted at 6.5
charter time.

## PART C — DECISION TREE ON RING 7'S RETURN

1. **Transport fails** → fix transport on the ring 7 base first; nothing in
   Part B proceeds. (Not expected: machinery is 6.3-proven.)
2. **Score > 30.5** → thesis proven at the true bar. Build order:
   U1+U2 (grade the win properly) → Director's ladder 6.4 (throughput) and
   6.5 (learn-to-win, with U6 rider) rebased on ring 7 → U3 → U5 A/B.
3. **Score 14–30.5** → card helps, doesn't cover its cost on the good host.
   Build order: U1+U2 → U3 (method is the cheapest lever) → 6.4 (richer
   cards) → U4 only if the tripwire fired → 6.5 → U5.
4. **Score ≤ 14** → host degradation was not the main story; card CONTENT is
   the bottleneck. Build order: U1+U2 → 6.4 (throughput: thin cards are the
   first suspect) → card-content review against the Layer B read → U3 →
   revisit.
5. **In every branch:** the outsider chamber's memo (bootstrap pending) is
   read before U3/U4 charters are finalized, and may reorder them.

## PART D — WHAT IS EXPLICITLY NOT PROPOSED

No model change, no decoding change, no fine-tuning. No authority for any
model output over deterministic machinery (Campaign CORRECTION law, adopted
here as precedent-by-scar, not by citation). No card-authority inflation
("the report is always right" is disqualified in every variant). No
resurrection of ring 1–5 machinery except through U4's narrow, tripwire-
gated, ceiling-bounded door.

*Nothing in this document is chartered. The ring 7 grade selects; the
Director rules; then we build.*

# G3 Mine Report — levers: the sweep, the split, the witness, the typing

**Type:** `MINE_REPORT_G3_LEVERS` · **v1** · **2026-09-20**
**Author:** collaborator seat (Cowork), read-only mine of both roots and the project KB, against
the ruled G3 contract below. Every claim is a builder report about the archive until re-read
first-hand at the current anchor; citations are perishable — re-verify before binding.

## 0 · The ruled contract this mine serves

Director rulings, 2026-09-20: the target list derives from the visual-object definition, ranked
smallest footprint → lowest class-integer (→ nearest (0,0) as deterministic tiebreak); the
roster is **re-derived from the record each turn**, never a stored id-keyed queue (frozen-roster
and re-mint failures on file); new objects join as they appear. **Duck goes through the list in
order** — interpreter during the sweep, no reordering. After the broad sweep, the split cascade:
**responded / no-response-yet** (never "inert" — ∀ law), then **local / remote** on the
attributed residue, then the **full lever typing protocol** for remote-bearing candidates;
local-only responses are filed as target-response evidence for G4. The sweep ledger is the
**shared intervention spine** G4 and G6 later read. Hybrid worlds: click arm to exhaustion
first, collide only for unreachable-or-null targets (Director nod pending, recorded as lean).

## 1 · The verdict

**G3 is substantially a port.** Every layer of the ruled contract has proven machinery in the
archive — most of it built twice (v4 and golden), some of it wired and canary-proven, one piece
(collide attribution) solved in golden after being found structurally absent in v4. The
genuinely new work is thin: the gate state machine itself, the abstention route to G5, and the
presumption-and-reopen walk policy that no prior tree ever wired end to end.

## 2 · Port ledger, by layer

### 2a · Sweep and coverage (the spine)

- `virelai-golden/golden/captain/sweep_click.py` — click arm: every present worldline once, at a
  NW-most **member** cell; attempted-set re-derived from the whole record each press; terminal is
  ENUMERATION_COMPLETE only. Proved `NEVER ATTEMPTED 0` on the click canary (2026-09-05).
- `golden/captain/nav_sweep.py` + `nav_lattice.py` — collide arm: walk is cost never gate;
  press-from-here before walk before revisit; unreachability earned by attempting; refused edges
  removed from the lattice by the world's own refusals. Proved `ARRIVED` on the embodied canary.
- `virelai_v4/strategy/investigation_priority.py` — size/rarity/isolation ranking plus
  `investigation_coverage_complete()` (every eligible object probed ≥1 before deepening). Port
  the *shape*; the ruled ordering (footprint → class-integer → (0,0)) replaces its weights.
- Ring 9 `adaptive_ego_coverage.py` (H4) — representative-first class collapse with explicit
  unknowns; ft09 65→8. The affordability layer over the everything-eventually guarantee.
- **Standing warning:** v4's `strategy/click_sweep.py` was built, tested, and never wired into
  live dispatch (code atlas: "live-code/dead-integration split"). The Ring 9 sweep must be the
  gate router's only probe source from slice one.

### 2b · Attribution (who was acted on)

- POINTER channel: the wiring law — a targeted press resolves against the owner map at **t−1**,
  the frame the actor saw; unowned cell reads EMPTY, never snapped
  (`virelai_v4/weave/action_roster.py::acted_on`; carried into golden).
- BODY channel: the **contact line** — the worldline that gave cells to a sealed ego across the
  press is what the ego touched (`virelai_v4/weave/contact_line.py` → `golden/roles/lever.py`,
  `golden/roles/effects.py`). INTENTIONAL (the pursued target gave) vs INCIDENTAL (something
  else gave en route) is already distinguished — exactly what the approach-path confound needs.
- The two channels are **never merged**, and their exclusion sets differ: ego|counters never
  ACT; ego|ground|counters never PARTNER — but GROUND may act (`GROUND+LEVER` is legal).
- `RULING_COLLISION_ATTRIBUTION_v2` (project KB) — the three-rung decomposition (coverage
  policy / drive / attribution) and the finding that v4's directional presses entered the record
  with `target_cell=None`, making collide attribution structurally empty. Golden's contact line
  is the repair. **Ring 9 echo, found this mine:** `probe_evidence.py` already declares the same
  limitation on itself — "non-coordinate action has no acted-site scope; local/remote split
  unavailable." The collide arm's first slice is closing that exact gap with the contact line.
- Multi-ego ruling (`RULING_EGO_WORLDLINE_v1`, via contact_line): every downstream consumer
  takes a **set** of ego worldlines; any single-ego contract is stale.

### 2c · Outcome classification (the ruled split cascade, already built)

`virelai_v4/library/probe_outcome_classifier.py` (read whole, 175 lines) is the cascade verbatim:
`NO_EFFECT / LEVER_LOCAL_SELF / LEVER_REMOTE_ONLY / LEVER_LOCAL_REMOTE`, plus two refinements
the ruled contract should adopt:

- **AMBIGUOUS** — a delta entirely masked by ego occupancy is neither active nor null: "re-probe
  after ego moves." Keeps a confound out of both branches.
- **Disregard, never erase** — counter ticks are labeled and routed to `disregarded_region_ids`,
  recorded on the outcome rather than silently masked. And ego is deliberately NOT disregarded:
  *a lever can legitimately drive the ego* (a teleporter) — a separate flagged decision.

Upstream of it, the subtraction chain (`library_sync` mask → `world_delta_computer` cell-grain
ego/HUD/world partition → classify) is the three-stage chain `WO_LEVER_MINE_00` verified: "one
probe, one classified outcome, no rate, no threshold, no quiet population." Ring 9's
`probe_evidence.py` + `masked_world_state.py` already reproduce the partition; the classifier is
a thin port over structures that exist.

### 2d · The witness law (candidate → lever)

`golden/roles/lever.py` (with `virelai_v4/weave/lever_witness.py` as oracle): LEVER is ∃ — one
witnessed press, permanent; nulls are recorded (`nulls`), never subtracted; `self_only` presses
are recorded as reactive-not-lever (the ruled local-only branch); `unattributed_residue` is the
schedule-or-mechanism file — **the G5 abstention route already has a field name**. The residue:
changed cells minus ego members' cells at both ends, minus ground exchange, minus masked counter
tick; `counter_event` marks refill presses so a reset never reads as an effect. Do-not-carry
(recorded in the source itself): `repeated_contact.py`'s threshold of 2 — a ∀-shaped bar on an
∃-claim.

### 2e · Typing (the "zoom in" — child targets)

- Form verbs: Ring 9 H3b already verifies `STILL / RECOLOR / PURE_TRANSLATION / GROW / SHRINK /
  DEFORM` over declared footprints; `REVIEW_H3_TRANSFORMATION_LEXICON` fixes the ladder — site
  arithmetic → footprint arithmetic → correspondence-qualified form verb → repeated mechanic —
  and forbids promoting a raw rewrite straight to an object verb.
- Repeated-transition mechanics: `virelai_v4/library/cycle_probe.py` (1,001 lines, WO-hardened;
  v3.5 classifier ported verbatim) types **TOGGLE** (recurrence at cycle length 2), **CYCLE**
  (>2), **DIRECTIONAL** (drift pixels only, no reversal), **SATURATED** (predecessor equality),
  with UNKNOWN and a write-time UNDETERMINED at the 20-press cap. Drift/toggle pixel separation
  structurally excludes HUD residue before the cycle test runs.
- Mechanism vocabulary (`SOLVER_BLUEPRINT_v1` §3.3–3.5): toggle · cycle · directional · global ·
  one-shot · **gated** — a gate is a lever mechanism, not a category; effect representation as
  measured transforms with `NOT_OBSERVED / OBSERVED_RIGID / OBSERVED_NON_RIGID`, vocabulary
  extensible by licensing, never forced rigid.
- Downstream consumption: `virelai_v4/library/lever_dispatch.py::route_lever` (TOGGLE/CYCLE →
  Gray-code bundle, DIRECTIONAL → depth sequence, SATURATED → skip, untyped →
  NEEDS_CYCLE_PROBE) and `physics_accumulator.py` (vector-consistency agreement replacing the
  marching-set 0%). These are G3-child and G7-facing — mine again at their charter.
- The subtree map: `AUDIT_LEVER_SUBTREE_CAMPAIGN_v1` names **seven** lever questions — mechanism,
  effect subjects, effect quality/bearing/magnitude, locality, coupling membership, repetition
  law, saturation-as-property. Only mechanism was ever answered. The child-target tree should be
  cut along those seven, opened on evidence only.

### 2f · Ring 8 evidence for the model-facing layer

`ring8-effects-tool` runtime (`virelai_runtime.py::_effects`): accumulated per-action effect
entries served compactly (caps 12 entries / 3 ranked). Run evidence: voluntary use in 16/25
games, explicit subsequent uptake after ≥13 calls — the strongest prior that *accumulated effect
structure is something Duck actually consumes*. Port the serving shape for the G3 gate view.

## 3 · Do-not-port list (each entry a paid-for lesson)

Confidence ladders and thresholds (`lever_evidence.py`'s 0.60+0.10→0.95; cycle caps as verdicts;
`≥0.80` ratios) — no threshold constant rides in. The frozen spawn roster and any id-keyed
stored queue. Single-ego contracts. First-lever and k-consecutive-inert early stops. Class-keyed
passability/inertness oracles and permanent dead-zone filters. Legacy's middle-band reading of
the sometimes-mover as lever-or-target — golden ruled selective change is not evidence; that
object is G5's. The write-time UNDETERMINED relabel — decide it fresh, don't inherit it.

## 4 · Open flanks (surfaced, not patched)

1. **Non-coordinate acted-site gap in Ring 9's own evidence layer** (§2b) — the collide arm's
   blocking dependency, with a named repair (contact line) and a named consumer.
2. **Locked-counter monitor not yet installed as cross-gate observer** (known limitation in the
   handoff): G3's first integration slice must feed every sweep action through it and the masked
   world delta.
3. **The partial autonomous mover** — no archetype anywhere; `unattributed_residue` +
   AMBIGUOUS give G3 its abstention shapes; the archetype itself is G5's charter question.
4. **Six of seven subtree questions unanswered** (§2e) — the child-target tree is mostly
   unmined territory; do not let mechanism-typing's maturity imply the rest is settled.
5. **Hybrid arm ordering** has no prior art (golden chose one arm by ego kind, never both) —
   click-first-to-exhaustion is a lean awaiting the Director's nod, not a port.

## 5 · Deep-reads owed when the G3 work order is authored

`golden/roles/lever.py` below line 110 (the read itself) and `roles/effects.py` whole;
`golden/captain/sweep_click.py` / `nav_sweep.py` bodies at the current golden anchor;
`virelai_v4/library/world_delta_computer.py:205-358` (the unread transition-view tail);
`cycle_probe.py`'s incremental per-press detector (lines ~468–533) before any child mechanic
slice; `ring8-effects-tool` `_effects` serving code before the gate-view slice; and the three
committed lever-fixture files named in `WO_LEVER_LABEL_01` (they caught the looseness once).

*Read-only mine; no code changed. This report seeds the G3 work order; it does not replace the
amendment-landing-status pre-check at that WO's own anchor.*

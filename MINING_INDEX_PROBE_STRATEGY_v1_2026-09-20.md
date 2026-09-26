# Mining index: probe strategy — click everything, collide everything, type the levers

**Type:** `MINING_INDEX_PROBE_STRATEGY` · **v1** · **2026-09-20**
**Author:** collaborator seat (Cowork). Read-only sweep of both connected roots and the project
knowledge base. Nothing here is a design; it is the located prior art for the sweep-then-type
probe strategy, gate by gate, with what each source proved and what its own record says not to
carry. File paths are as of this sweep; per the citation-perishability lesson
(`RULING_COLLISION_ATTRIBUTION_v2`), re-verify at the anchor before any WO cites them.

---

## 0 · The strategy already has a canonical statement

`SOLVER_BLUEPRINT_v3_2026-07-13.md` §3.2–3.4 (project KB) is the Director's proposal in ratified
form, three moves deep:

1. **The void opening is generative, not strategic** — "click everything" on a coordinate world,
   "collide with everything" on an embodied one; the platform's available-actions set selects
   which arm. Ordering is a cheap visual prior (smallest footprint → lowest class-integer →
   nearest (0,0)) and explicitly an *ordering, never a classification*.
2. **Noise-floor tiers first** — ego (covaries with control) and counter (ticks regardless of
   target) are the two false responders; both must be masked before "produced a delta" means
   anything. This is exactly why the Ring 9 gate order is G1 ego → G2 counter → G3 levers.
3. **Deepen by realized yield, not type-prior** — broad sweep populates; the objects that
   answered get the zoom-in; asymmetry emerges instead of being assumed. "The worklist grows as
   probing reveals objects — and that growth is success, not scope-creep."

So the proposal is not new invention; it is the port of a ratified opening doctrine into the
gate architecture. PORT-default is satisfied at the strategy level. Everything below is the
component-level prior art per gate.

## 1 · The sweep spine (G3's coverage layer, shared downstream)

**Golden click arm** — `virelai-golden/golden/captain/sweep_click.py`. Press every present
worldline once at its NW-most *member* cell (never the bbox corner — "a click on a non-member
cell is a click on someone else"); enumeration re-derived from the whole record every press, no
stored queue; the only terminal is ENUMERATION_COMPLETE — never first-lever, never a run of
inerts, because LEVER is ∃ and INERT is ∀. Proved: `NEVER ATTEMPTED 0` on the click canary,
2026-09-05. Own origin: `virelai_v4/weave/coverage_sweep.py:676-731`, which itself retired the
"8 consecutive inerts" early stop.

**Golden collide arm** — `golden/captain/nav_sweep.py` + `nav_lattice.py`. Collide with every
object on the list; walk is COST, not a GATE (SUBTREE_CHARTER S-3); press-from-here before walk
before revisit; unreachability is *earned by attempting*, never inferred; a typed WALL is not a
walk-to target — the refusal that typed it is the contact. Explicitly NOT carried from v3.5's
`nav_atlas.py`: permanent dead-zone filtering and class-keyed passability ("class-wide judgment
is poison"). Proved: `ARRIVED` on the embodied canary, 2026-09-05.

**Golden opening** — `golden/captain/opening.py`. Every non-targeted action pressed twice in
consecutive pairs (the second press is the first at which the ∀ means anything; a pair
straddling other presses is not a reproduction); one click per frame-0 region anchor on pointer
worlds. Origin `coverage_sweep.py:249-306`; proved on the embodied canary 2026-08-28.

**v4 target ranking** — `virelai_v4/strategy/investigation_priority.py` (PRODUCTION_LIVE in the
code atlas): size/rarity/isolation/reactivity-boost ranking plus
`investigation_coverage_complete()`, the gate that required every eligible object probed ≥1
before deeper probing could fire. The ranking is a Duck-free deterministic target-class
generator — directly portable to the Ring 9 sweep scheduler alongside H4's representative-first
collapse (`adaptive_ego_coverage.py`, ft09 65→8).

**Standing warning from the same sweep** — v4's `strategy/click_sweep.py` was fully built,
well-tested, and **never wired into live dispatch** (`CODE_ATLAS_DATA`: "live-code /
dead-integration split"; tier4_click bypassed it entirely). The Ring 9 version must route
through the gate router from the first slice — a sweep that exists but is not the only source
of probes has not shipped.

## 2 · Collide attribution (the part "collide everything" is missing)

`RULING_COLLISION_ATTRIBUTION_v2_2026-08-10` (project KB) decomposed collide-with-everything
into three rungs and found the cliff: **coverage policy** (v4 `strategy/collide_sweep.py:37-85`,
BUILT), **the drive** (`:104-196`, BUILT, env-gated), **attribution** (ABSENT — and on an
embodied world the channel was *structurally empty by construction*: `target_cell is None` for
every directional press, so `NON_TARGETED` short-circuits before the owner map is consulted).
Golden closed that gap with the contact line: attribution for a body press is the worldline that
*traded cells with an ego member across the press* (`virelai_v4/weave/contact_line.py` origin,
carried into `golden/roles/lever.py` and `golden/roles/effects.py`'s BODY channel — "an object
that gave cells to a sealed ego on the press is what the ego touched"). This is the single most
important port for the Ring 9 collide arm: without the contact line, the collide sweep learns
nothing, which the ruling states as "rung 2 has not shipped."

## 3 · Lever typing (G3's zoom-in)

**The witness law** — `virelai_v4/weave/lever_witness.py` and its golden transcription
`golden/roles/lever.py`: LEVER is ∃ — one witnessed press proves it, permanent, and "later
silence cannot retract it" (a null press is not a witness and cannot subtract from an
existential — no decay arithmetic exists). The residue construction: a press's changed cells
minus ego cells minus ground exchange minus masked counter tick; a witness is an attributed
press whose residue has a non-excluded owner. Corrected from the oracle: a mover is any owner of
a residue *cell*, not a scalar magnitude (v4's scalar channel read recolor movers as 0).
NOT carried, by the file's own header: `repeated_contact.py`'s threshold of 2 (a ∀-shaped bar on
an ∃-claim) and `pair_classify.py`/`mechanism_classify.py` (what a lever *does* — that is the
child target, not the witness).

**Two attribution channels, never merged** — `golden/roles/effects.py`: POINTER (owner at t−1 of
the targeted cell — the parallax law: the key is who owned the site *before* the press) and BODY
(the contact line). Exclusion sets differ and must not collapse: ego|counters are never actors;
ego|ground|counters are never partners — but GROUND may act (`GROUND+LEVER` is legal).

**Routing after typing** — `virelai_v4/library/lever_dispatch.py` (mechanism verdict → probe
bundle; v3.5 origin `crucible/machine_search.py:200-224`), `library/physics_accumulator.py`
(per-lever vector-consistency agreement — the repaired answer to the marching changed-cell set
that made agreement structurally 0%), `library/probe_outcome_classifier.py` (probe result →
contract, with its import-sovereignty lesson). These are the "zoom in and type" mechanics.

**Open flank recorded three times** — the *partial autonomous mover* (moves sometimes, not on
every press, not a counter, not inert) has no archetype; `WO_REMOTE_WITNESS_01` proved it
load-bearing: "the lever stage cannot close without it." In Ring 9 terms it lands in G5
(environmental forces), and G3 must abstain rather than type it — plan for that abstention
explicitly or G3 inherits the same halt.

## 4 · Reactions and terrain (G4)

`golden/roles/ground.py`, `wall.py`, `nav_lattice.py`'s refusal record, and the crossing/medium
work (`virelai_v4/weave/crossing.py`, `medium.py`; project KB `WO_CROSSING_KEEP_01`,
`WO_MEDIUM_01`). The law worth carrying verbatim: a GROUND worldline's deltas are the ego's and
never lever evidence; the refusal that types a WALL *is* the contact — negative responses are
evidence, not noise. Boundary presses (death, level-up, respawn) are EVENTS, not moves
(`golden/push/machine.py` measured the cost of getting this wrong: 3 phantom contradictions on
ls20 until boundary presses were excluded from edges).

## 5 · Scoped inertness (G6)

`WO_INERT_CERTIFICATE_01` (project KB): INERT is PROVISIONAL, always — the certificate records
what was aimed, what the world offered, what fired, and what was never tried; on ls20 no action
can be aimed at any worldline at all, so INERT is *unassertable by the platform's own offer*,
and the certificate states that instead of leaving silence. "Repetition is a count, not an
exhaustion." H4's `inertness_claim_permitted: false` is the same law already in Ring 9; G6
should port the certificate shape whole.

## 6 · Novelty and the push (G7)

`golden/push/machine.py` + `search.py`: the state machine over masked addresses — (state, key) →
state, click keys resolved at t−1, boundary presses excluded, UNTRIED enumerated per state, and
SEARCH = "press the first untried key from here, else walk to a state that has one, else
SATURATED → EXHAUSTED_NO_WIN." A WIN is observed by the play loop, never sought. NOT carried by
its own header: the nav approach loop that spent 150 of 175 presses approaching two untouchable
panels (F-0013). Ring 9's masked state archive (G2) is already the address substrate this needs.

## 7 · Win explanation and carry (G8–G9)

`golden/explain/` is package-only (placeholder) — golden has no built prior art here. The hybrid
side does: `virelai_lessons.py`, `virelai_win_capsule.py`, `tools/freeze_win_corpus.py`,
`tools/compile_level_carry.py`, `compile_post_win_grammars.py` across Ring 8 variants — win
boundary preserved with preceding state, action, and active laws; carried as a falsifiable
hypothesis, not truth. Mine these at G8 charter time; they were not deep-read in this sweep.

## 8 · What the sweep changes about the G3 design conversation

The prior art votes, consistently: sweep to enumeration-complete, never stop on first lever or
inert runs (∃/∀); representatives and ranking make "everything" affordable (H4 +
investigation_priority) without deleting the everything-eventually guarantee; the collide arm is
worthless without the contact line (the one ABSENT rung, already solved once in golden);
zoom-in/typing is a child target with its own witness law, prediction, and demonstration, and
the mechanism question (what the lever does) is a *further* child, not part of the witness. One
genuinely open design item survives the sweep with no prior answer: the partial autonomous
mover's archetype (§3), which is a G5 question G3 must be built to abstain toward.

*Read-only sweep; no code changed. Deep-reads deferred: Ring 8 effects-channel internals,
`joint_transform`, `pointer_depth` adapters, and the G8 carry modules — each gets its own WO-00
at its gate's charter.*

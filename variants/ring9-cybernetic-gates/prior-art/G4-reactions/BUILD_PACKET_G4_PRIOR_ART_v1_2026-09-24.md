# G4 build packet — code-verified prior art, verdicts, and wiring plan

**Type:** `BUILD_PACKET_G4_PRIOR_ART` · **v1** · **2026-09-24**
**Author:** collaborator seat (Cowork). Code-level sweep: every module below was read
first-hand at this anchor — APIs, bodies, and consumers — not summarized from documents.
Supersedes nothing; deepens `MINE_REPORT_G4_CAUSAL_EXPANSION_v1` from doc-grade to code-grade.
Re-verify at the implementing WO's own anchor; citations are perishable.

## 0 · The headline, sharpened by the code

The G4 evidence layer in `virelai_semantic/` is better than the doc-grade mine suggested — and
one piece of it must NOT be wired as-is. `typing.py` already implements the condition-humility
doctrine in miniature. `mechanics.py` contains its own target-identity rejoin, which under Ring
9 would create a second identity authority beside the entity ledger — the port must remove it,
not carry it. Consumer map: `compiler.py` is already consumed (runtime, lessons, two tools);
`typing / joint_transform / mechanics / depth_probe` are consumed by nothing on the gate path.

## 1 · In-tree modules (`inference/framework/virelai_semantic/`) — verdicts per module

**`typing.py` (119 lines) — RE-POINT AS-IS; it is the best epistemics in the tree.**
`classify_effect_channel(transitions)` licenses recurrence only inside *uninterrupted
activation runs* (separated discovery observations stay evidence but never license a period);
the confirmation floor is **two complete periods** — one return is only a candidate; verdicts:
`TOGGLE` (period 2) / `CYCLE` / `UNIFORM_TRANSFORM` / `DETERMINISTIC_STATE_TRANSITION` (unique
successors, explicitly scoped `ONLY_FOR_OBSERVED_INPUT_STATES`) / `DIRECTIONAL_CHANGE` /
honest `UNKNOWN`; every verdict carries a `condition` field, today `UNMEASURED` or
`OPEN_OR_UNMEASURED`. That deterministic-table verdict IS the outcome-set-then-promote pattern.
The condition ledger (§3, slice 2) is a thin extension of exactly this function.

**`joint_transform.py` (220) — RE-POINT AS-IS.** `compile_joint_transformation(record, presses,
actor)` runs on post-residue cells only, needs ≥2 attributed presses with nonempty residue, and
emits `virelai-joint-transformation-v1`: per-press exact rewrite arithmetic, class-multiset
conservation per press, kinds `COORDINATED_CLASS_PERMUTATION / _FIXED_CLASS_SUBSTITUTION /
_REPEATED_CLASS_REWRITE / _CLASS_REWRITE`, functional-substitution test, connected-component
decomposition, fingerprint `period` detection, and a limitations sentence refusing purpose
claims. This is the effect-quality/magnitude reader, done.

**`mechanics.py` (438) — PORT WITH SURGERY.** Two defects verified in the body:
(a) `MIN_ACTION_INDEPENDENT_PRESSES = 8` — a threshold constant; replace with the structural
counter/mask verdicts Ring 9 already has (the mask law says what is bookkeeping; no press-count
proxy). (b) `_effect_channels` performs its own re-minted-target rejoin by exact
(pre-class, bbox) footprint — a second identity authority. Under the entity contract, identity
belongs to the entity ledger alone: the port keys channels by **entity id** and deletes the
union-find rejoin. Keep: the per-edge best-evidence dedup, the channel grouping shape,
`_shared_control_bundles` / `_co_attributed_actor_groups` (coupling seeds).

**`depth_probe.py` (210) — RE-POINT BEHIND THE ROUTER.** `LeverDepthPlanner` is the G4
paid-half skeleton, verified: dynamic queue, `refresh()` *appends newly discovered levers
without resetting earlier evidence* (the event-driven reopen's exact shape), one-lever-at-a-
time, `request()` returns an empirical operation with `arc_action: None` — it never fabricates
an action, so it slots behind the gate router's token discipline cleanly; evidence-terminated
with `SATURATED`. One flag: `engineering_cap = 64` — acceptable as an engineering bound only if
hitting it emits a typed `BUDGET_STOPPED`-style certificate line, never silence.

**`depth_adapter.py` (118) / `compiler.py` (672) / `view.py` (95).** The adapter is the
pointer-arm activation shim (port pattern for the CLICK branch). The compiler is the semantic
dossier assembler (`EntityDossier`, `RoleClaim` with evidence refs, `ControlModel`,
`JointDelta`) — already consumed by `virelai_runtime` and `virelai_lessons`; treat as the
serving-layer projection, and reconcile its `EntityDossier` with the G3 entity ledger so there
is one dossier schema, not two (an alignment task, not a rewrite).

## 2 · v4 ports (read at the body, not the docstring)

**`library/conserved_transfer_author.py` — PORT WHOLE, INCLUDING ITS HALT.** Verified:
integer-exact licensing, no epsilon; Shape A (functional endpoints net to zero exactly) and
Shape B (single endpoint nets exactly against a measured boundary complement, typed by
behavior, never by class); forward out-of-sample exact prediction required or no license; and
`DescentRequired` — when the global total conserves but recorded endpoints don't close, it
*escalates* ("a Slot must be re-read to expose the missing endpoint") instead of silently
coupling. That is halts-are-information as code; carry the exception and give it a G4
disposition (`REPRESENTATION_GAP` on the coupling claim).

**`weave/coupling.py` — PORT THE PANEL, NOT THE CONSTANTS.** The press-indexed signed-delta
matrix, the multi-criterion panel (`PanelRow` with independence/dependence read off
fired∧live∧(un)targeted denominators), and derived-complement discipline port. Verified
do-not-port: `CAND_CORR = 0.6`, `COUPLE_CORR = 0.85` — correlation thresholds. The structural
replacement is already in hand: couplings *license* the conserved-transfer way (exact
prediction) or remain reported panel evidence; correlation never seals.

**`weave/mechanism_classify.py`** — concept already absorbed into `typing.py` (classify the
reactive partner, not the lever); no second port needed. **`cycle_probe.py`** — superseded for
typing by `typing.py`'s stricter run-scoped rules; mine again only if the incremental
masked-hash detector is wanted for early termination.

## 3 · Wiring plan (five slices, in order)

**S1 — Wire the dark machinery.** G4 gate machine consumes G3's outputs: per confirmed lever,
feed its attributed transitions (entity-id-keyed) to `classify_effect_channel` and
`compile_joint_transformation`; publish verdicts into the entity dossier; `mechanics.py`
surgery (threshold out, rejoin out, entity ids in). No new epistemics — a consumer commit for
machinery that has never had one.

**S2 — The condition ledger.** Extend `typing.py`'s deterministic-table verdict with the world
dimension: successors keyed by `(channel state, masked world address, known_phase)`. A split
under the same key is a condition *candidate*; promotion to a conditional law (the `gated`
mechanism) only by a frozen discriminating demonstration — G2's freeze-then-press machinery
reused. The retained confirmation records from the pre-run corrections slice (frozen footprint,
predicted cells, declaration and grading transitions) are this ledger's seed data.

**S3 — Couplings with a live consumer.** `conserved_transfer_author` + the coupling panel land
in the same commit as their consumer (dossier edges + G7's planner reads them) — the
blueprint's recorded defect was couplings terminating in a renderer; do not repeat it.

**S4 — The depth planner behind the router.** `LeverDepthPlanner` as the G4 SELECT source,
router-token discipline unchanged, `SATURATED`/cap exits typed into the certificate.

**S5 — Boundary and counter-expiry conditional reactions.** New construction (no ancestor):
consume the `BOUNDARY_EVENT_DEFERRED` pool and reset/expiry records; laws of the form
"at counter extremum, X" earn themselves through the same candidate → explain → freeze →
demonstrate rhythm. Transition-43-style composite events (bar reset + ego respawn + third-party
depletion) are the target shape.

## 4 · Constants inventory (each dies or is justified at port time)

`MIN_ACTION_INDEPENDENT_PRESSES = 8` (mechanics — dies, structural replacement named);
`CAND_CORR/COUPLE_CORR` (coupling — die; licensing replaces); `engineering_cap = 64`
(depth planner — survives only as a typed budget stop); `typing.py`'s two-complete-periods
floor (survives: it is a cardinality with a stated reason, the ∀ needs two periods to mean
anything — same class as the paired-press rule).

## 5 · Tests owed with the slices

Production-shaped, per the house pattern: S1 — a lever's transitions through the real gate
machine reach a dossier verdict with evidence refs intact; entity-id keying survives a re-mint
(no footprint rejoin anywhere). S2 — same press, two masked addresses, split recorded as
candidate, not law; promotion only after a frozen discriminating demonstration; planted defect:
a split promoted without demonstration must fail. S3 — a conserved transfer licenses on exact
arithmetic and refuses on ±1; `DescentRequired` surfaces as a typed gap. S4 — cap hit emits the
typed stop; `refresh()` appends mid-run discoveries without resetting records (the reopen
doctrine's test). S5 — a composite boundary event yields candidates in each family and no
lever witness.

*Read-only sweep; no code changed. This packet plus `MINE_REPORT_G4_CAUSAL_EXPANSION_v1` and
`MINE_ADDENDUM_G3G4_EVENT_DRIVEN_REOPEN_v1` constitute the G4 shelf. The G4 contract document
(condition-ledger spec + coupling stratum schema, paying the mechanic-layer doc debt) is the
next governance artifact, written against this packet.*

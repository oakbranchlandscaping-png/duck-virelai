# NAV build packet — collide-with-everything: code-verified prior art and port plan

**Type:** `BUILD_PACKET_NAV_COLLIDE_PRIOR_ART` · **v1** · **2026-09-25**
**Author:** collaborator seat (Cowork). Code-level sweep: golden's nav stack read at the bodies,
v4 donors at their key sections, Ring 9's current NAV path located in the gate machine. This
packet is cross-cutting — it serves G1 consumption (the ego's bearings), G3's collide arm, and
G4's terrain harvest — and lives in its own folder for that reason. Re-verify every citation at
the implementing WO's anchor.

## 0 · The headline

The embodied pilot problem is **solved, canary-proven, and carries its own hard-won corrections
in the source**. Golden's `captain/nav_lattice.py` + `nav_sweep.py` is a complete deterministic
pilot: lattice, BFS routing, the charter's target order, honest unreachability certificates, and
a typed enumeration-complete exit — proven `ARRIVED` live, with the one measured failure of its
own first design documented and fixed *in the docstring where the fix lives*. Ring 9 currently
implements Duck-piloted approach instead (`pilot_intent APPROACH|CONTACT_ATTEMPT` validated in
`virelai_gates.py:~1147`, step accounting in `_record_navigation_step`). The pending Director
ruling (pilot: deterministic service vs Duck-steered) decides which is primary; this packet
supports either, but the port ledger below is written for the deterministic service with Duck
fallback, per the collaborator lean.

## 1 · The golden pilot stack (port as the route service)

**`golden/captain/nav_lattice.py` — PORT WHOLE.** `Lattice(anchor, shape, bearings, walk,
stands, refused, bounds)`; `routes()` = BFS over *stands* with refused `(anchor, action)` pairs
excluded as edges; `probes()` = every unrefused press from reachable stands *including landings
beyond known ground*; `contacts()`, `first_step()`, `route_actions()`, `approach()`. Three laws
are written into the bodies and are binding on the port:

- **Traversal only over anchors actually stood on** (`fits()`): the measured 2026-09-09 defect —
  footprint-vs-trail testing starved the graph to one position at node 54 and declared ten
  worldlines unreachable from starvation, not from the world. "An anchor the body has stood on
  is a fact about where it can be; the cell trail under its feet is not. The graph can only
  grow." This is the packet's premier planted-defect test.
- **One press beyond the frontier is an experiment; a route beyond it is a story** (`probes()`):
  extension happens one attempt at a time, toward the nearest target; whole routes are planned
  only over known ground.
- **A refused edge is not an edge**, and the refusal is evidence (types a WALL candidate — the
  refusal IS the contact, R-I).

**`golden/captain/nav_sweep.py` — PORT THE PLAN AND ITS CERTIFICATES.** `plan()` implements the
ratified charter order (S-4): (1) a contact available from known ground — take it; (2) else one
press beyond the frontier, chosen by nearest-target L1 with deterministic ties; (3) else every
press from every reachable stand is spent and each remaining target earns a
`PRESUMED UNREACHABLE` certificate that records *what was tried* — closest stand, gap, position
count, refused-edge count, node — and its reopen conditions verbatim ("new walkable ground, a
refusal that later yields, or a world-state change"). `Nav.next()` shows the exit discipline:
`ENUMERATION_COMPLETE (body)` with full counts, and the typed halt when the platform stops
offering a route's action. **Ordering note for the Director's ruling:** the charter order is
route-cost-aware within the coverage guarantee (press-from-here before walk; nearest first) —
it amends the CLICK-context roster order and needs explicit ratification for NAV.

## 2 · v4 donors (targeted sections read)

- `weave/reachable.py` — footprint-arithmetic reachability (`overlaps`/`within`/`reach` over
  bearing expansions): the geometric core under the lattice; superseded in shape by golden but
  the collision-landing math is the reference.
- `weave/collide_plan.py` — predicted-landing contact test and the whole-footprint plural
  check-off at every position.
- `weave/collide_drive.py` (1,783 lines; key sections read) — the pursuit-semantics lessons,
  each paid for live: **arrival is cell transfer, never adjacency** (a displace with no transfer
  "never registers as reached"); **budget fires before STUCK and that is correct** — "STUCK
  means this place defeated me, which should be rare; the budget means I have spent enough
  here, which should be common"; **stillness is presence, not position** (WO-BUDGET-OUT-01);
  budget expiry maps to its own record, never a third disposition invented at write time.
- `weave/nav_target.py` — target election by measured gains (who gave cells to the ego), with
  explicit abstention (`_abstain`) when the record cannot say.
- `weave/contact_line.py` — INTENTIONAL vs INCIDENTAL givers (already binding via the G3
  packet); the en-route confound reader.
- V3.5 `memory/nav_atlas.py` — unreachability *earned by attempting*, live across lives.
  **Do-not-port stands as recorded:** its permanent dead-zone filter and class-keyed
  passability oracle ("class-wide judgment is poison").

## 3 · Ring 9 as it stands (the delta the slice closes)

`virelai_gates.py`: NAV/HYBRID world-typing at ~241; embodied pilot admission requiring
`pilot_intent ∈ {APPROACH, CONTACT_ATTEMPT}`; `_record_navigation_step` with navigation-limit
accounting; contact attribution through the BODY channel of `lever_attribution.py`; the
observation adapter deriving ego self-motion and ground exchange. What does not exist: a
lattice, routing, the charter order, unreachability certificates, or counter-aware feasibility.
Duck currently chooses the approach presses. The delta is precisely the golden stack as a
**route service**: each turn it computes the exact next press and the router issues it as the
scheduled token — Duck rides and interprets; Duck-steering survives only as the typed fallback
where the lattice has no route, and the fallback is recorded as such.

## 4 · New construction (no ancestor): counter-aware feasibility

G2's locked `CounterModel` rate turns the bar's standing into an actions-remaining estimate —
machinery consuming earned law. The route service checks feasibility (route length + one
contact press against remaining budget) and defers infeasible targets with a typed reason
(`DEFERRED_INSUFFICIENT_LIFE`), re-admitting them after respawn. Certificates report deferrals
distinctly from unreachability. Small, unprecedented, and on a 42-action life the difference
between a sweep that finishes and one that drowns mid-route.

## 5 · The free G4 harvest (journaled from slice one)

Every refusal → WALL candidate with its (anchor, action) evidence; every ground exchange →
medium evidence; every en-route third-party change → passive-kernel causal candidate; every
gains-election → contact-subject evidence. None of it typed in G3's slices — all of it
journaled, entity-keyed, waiting for G4's terrain stages.

## 6 · Do-not-port list

Footprint-in-trail traversal testing (the starved-graph defect — the fix is the law now);
whole-route planning beyond known ground; adjacency-as-arrival; permanent unreachable filters
and class passability oracles (V3.5); the 12-frame per-target budget as a *verdict* — budgets
survive only as typed stops (`COLLIDE_MAX_FRAMES_PER_TARGET`-style constants become recorded
engineering bounds, never dispositions); any invented third disposition at budget expiry.

## 7 · Tests owed (production-shaped, per house pattern)

The starved-graph regression: a corridor walk where footprint-in-trail testing would collapse
the graph — stands-based traversal keeps planning (the node-54 story as a planted defect).
Refused-edge exclusion from routing plus WALL-candidate journaling of the same refusal.
Presumed-unreachable certificate content and its reopen on newly stood ground. Budget-before-
STUCK ordering with each mapping to its own record. Contact = cell transfer, not adjacency (a
flush approach with no exchange is not a contact). Counter-aware deferral: an infeasible route
defers typed and re-admits after respawn. Enumeration-complete only when contacts, frontier
presses, and feasibility are all spent.

## 8 · Slice ladder

**N1** — port `Lattice` + `plan()` as the route service behind the gate router (token
discipline unchanged; Duck fallback typed). **N2** — harvest journaling (refusals, exchanges,
gains) entity-keyed into the shared spine. **N3** — counter-aware feasibility and deferral.
**N4** — the ls20 G3-NAV live checkpoint: runbook, certificate additions (NAV enumeration
reasons, deferral and unreachability reporting), graded against the standing prereg's P2 (the
navigation-cost prediction, still unfalsified).

*Read-only sweep; no code changed. Folder `prior-art/NAV-collide/` is cross-gate by design; the
G3-levers and G4-reactions packets remain the per-gate authorities and this packet defers to
them wherever they overlap.*

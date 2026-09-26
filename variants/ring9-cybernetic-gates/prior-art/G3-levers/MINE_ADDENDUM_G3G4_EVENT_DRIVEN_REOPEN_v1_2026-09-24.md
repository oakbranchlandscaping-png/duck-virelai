# Mine addendum: the G3/G4 boundary and the event-driven reopen — doctrine, lineage, guards

**Type:** `MINE_ADDENDUM_G3G4_EVENT_DRIVEN_REOPEN` · **v1** · **2026-09-24**
**Companion to:** `MINE_REPORT_G3_LEVERS_v1`, `MINE_REPORT_G4_CAUSAL_EXPANSION_v1`,
`CONTRACT_G3_ENTITY_LIFECYCLE_v1`. Records the Director's doctrine of 2026-09-24 and the repo
lineage behind its one new element.

## The doctrine (Director's words, binding)

> G3 exhaustively locates and confirms the world's levers. Each confirmed lever opens an
> entity-specific G4 subtree for detailed reaction study. Any newly appearing visual object must
> pass through G3 before the system assigns it a causal role.

G3 asks *which objects are levers*; G4 asks *how each confirmed lever works* (what transforms;
local or remote; reversible; conditioned on state, sequence, location, or another object; what
its law predicts; what would falsify it). G3 is therefore not a phase that finishes at the
opening sweep: it is an **event-driven classification gate**. The original roster can close
while later discoveries — above all, objects born from G4 interactions — create new G3
obligations without erasing earlier results. The reverse edge is law: G4 interaction → new
visual object → persistent identity registered → its own G3 → if confirmed, its own G4 subtree.

## The mined lineage (each element has prior art; none is invention)

- **The failure this doctrine kills is the oldest on file.** `WO_LAYER1_00_GROUNDING` proved
  v4's captain spawn-blind within a level: the roster minted only at spawn, the per-frame path
  could not birth a slot, and a mid-level-born object was structurally invisible until the next
  level. Its two load-bearing findings carry forward: the *decision logic inherits a grown
  roster for free* (no probe machinery needs rebuilding when births join), and the born-object
  keyspace must be non-colliding with per-turn-recomputed derived fields (satisfied in Ring 9:
  entity ids are minted stably, the roster and ranks re-derive from the record each turn).
- **Birth is already first-class in the active tree.** `entity_observation.py` mints generic
  `BIRTH` and `AMBIGUOUS_BIRTH` relations (not only `RESET_BIRTH`), so a G4-spawned object
  already becomes a persistent entity with a sighting record. The doctrine adds only the
  *obligation*: a BIRTH entity enters the lifecycle at `UNTOUCHED` and the scheduler admits it
  by roster order — which the re-derived roster does without new machinery.
- **APPEAR is a correspondence event, never a pixel predicate** (H3 lexicon review): the
  substrate records only integer rewrites; "a new object appeared" is a reading licensed by the
  correspondence layer. The doctrine's registration step is exactly that licensing.
- **Reversibility** (G4's question list): prior art is the TOGGLE mechanism (recurrence at
  cycle length 2) from the V3.5/V4 typing lineage, plus the Undo protocol where G0's metadata
  reports the action.

## Two design guards the mine surfaces (new, binding on the implementing slice)

**G-1 · Dual booking.** An object born from an attributed intervention is booked **twice, and
neither booking substitutes for the other**: (a) as *effect evidence in the causing lever's G4
law* — spawning is a transformation, recorded with a provenance lineage edge (`SPAWNED_BY`,
distinct from `RESET_BIRTH`) from the causing intervention to the born entity; and (b) as a *new
G3 obligation* for the born entity, whose causal role is unknown until it passes its own G3.
The lever that spawns a thing is not thereby the parent of the thing's behavior.

**G-2 · Birth-storm collapse.** Golden's rejoin lesson: a region the correspondence cascade
cannot license gets re-BIRTHed *every node* — un-threaded, one real object becomes an unbounded
stream of new worldlines. Under this doctrine that failure becomes an unbounded stream of G3
obligations, which is a budget attack the world performs on us. Guard: a birth recurring at the
same footprint/class signature across adjacent transitions is collapsed into one entity
(threaded, or held `AMBIGUOUS` with candidate links) rather than re-registered; the abstention
fence already blocks forced matches — this is its symmetric twin, blocking forced *non*-matches
from minting rows. One planted-defect test: an oscillating unthreadable region yields exactly
one entity and one G3 obligation, not N.

## Certificate and lifecycle implications

`G3-CLOSED` becomes roster-scoped-at-close: the certificate's enumeration claim binds to the
roster as it stood, and post-close births appear as new `UNTOUCHED` rows with open obligations —
reported by the gate view and the certificate, never silently absorbed and never a retroactive
failure of the earlier close. The G4 handoff check ("every discovered entity at a documented
terminal state") gains one clause: entities born after roster close are exempt from the closed
sweep's terminal requirement and listed as open obligations instead.

*Read-only mine plus doctrine record; no code changed. The implementing slice cites G-1 and G-2
as binding and lands the planted-defect test with them.*

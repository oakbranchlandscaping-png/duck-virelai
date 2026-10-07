# Ring 9 cell-site targeting: diagnosis, contract, and validation ladder

**Type:** `BUILD_PLAN` · **v1** · **2026-10-06**

**Author:** Sol (Alpha build seat), signed

**Branch at diagnosis:** `ring9-unified` @ `98480b0`

**Scope:** the gated G1-to-G3 NAV function: construct the ranked roster, steer the ego to each roster member, observe the masked delta, record a disposition, and continue.

## 1. Ruling

A visual object is not an anchor coordinate. It is the observed set of cell sites that currently compose one entity hypothesis.

The durable targeting unit is:

`stable entity identity -> current cell sites -> possible contact landings -> attempted route edges -> terminal disposition -> attributed delta`

The original G2 anchor and bounding box are historical geometry. They may rank and audit a target. They cannot remain the live address after the entity moves, recolours, grows, shrinks, disappears, or returns.

## 2. What the evidence showed

### Direct observation: unified ls20 canary

The canary's paired G1 probes visibly translated a composite ego on every movement action:

| Opaque action | Repeated observed cell-site translation |
|---|---:|
| `ACTION1` | `(-5, 0)` |
| `ACTION2` | `(5, 0)` |
| `ACTION3` | `(0, -5)` |
| `ACTION4` | `(0, 5)` |

The moving family contained 25 sites across integers 9 and 12. Duck described these laws correctly in prose, but wrote `action_law_specs={}` and put only two representative sites in its prospective prediction. The former `nav_control` compiler consequently produced no bearing map. G3 had a roster but could not issue its first route action.

This proves a G1-to-G3 representation failure. It does not show that ls20's roster, contact attribution, or later reachability logic is intrinsically unable to work.

### Prior art: Virelai 3.5

Virelai 3.5 had a compact deterministic execution loop:

1. refresh targets from the current frame;
2. rank untried targets before repeated targets;
3. route one action toward the selected target;
4. reread the ego and board;
5. retain refused edges;
6. rotate immediately when the target receives a terminal result.

Its useful property was the completeness of that loop. Its limitations were coordinate-level target identity, heuristic target selection, and permanent unreachable exclusions. Ring 9 should port the loop invariants while retaining its stronger entity ledger, counter mask, attribution, and reopenable reachability evidence.

## 3. Implemented slice

### Deterministic G1 cell-site flow

`nav_control.py` now reconstructs before and after frames from lossless probe evidence, extracts exact same-integer component translations, and uses Duck's supported demonstration only to identify the relevant moving family. The controller then retains every site in that family.

An ordinary action bearing is accepted only when the paired observations agree. A prospectively supported structured law remains accepted as a second direct evidence channel. Prose direction names are never parsed.

The resulting control product contains:

- the opaque action-to-displacement map;
- evidence references for each bearing;
- unresolved actions;
- the normalized full ego shape;
- the full demonstrated ego cell-site set;
- the binding source.

The result is cached by G1 revision and comparison identity so G3 does not repeat the frame analysis on every controller decision.

### Current-site roster resolution

G3 continues to inherit G2's frozen ranked identities. Before every click or NAV attempt it now resolves the active identity through `EntityLedger` and emits the entity's current complete site set, current anchor, current bounding box, current integer, and entity version.

CLICK uses the current anchor. NAV computes contact against the current full site set. A later world delta can therefore move a target without leaving its roster entry aimed at an obsolete coordinate.

## 4. End-to-end execution contract

For every eligible ranked G2 member:

1. **Bind identity.** Bind the frozen member to an entity hypothesis using the complete counter-masked site set.
2. **Resolve current geometry.** Read the entity's latest complete sighting immediately before planning.
3. **Generate contact surfaces.** Treat any landing whose full ego footprint intersects any current target site as contact. The target anchor is not a substitute for this calculation.
4. **Plan one action.** Route over demonstrated stands; allow only one experimental frontier edge at the route boundary.
5. **Observe again.** After every action, ingest the new frame before selecting another action.
6. **Attribute the delta.** Remove the counter and expected ego/ground exchange. Assign the remaining local and remote residue to the target-bound intervention.
7. **Settle the roster row.** Advance after a first positive witness, a scoped null contact, a boundary/budget disposition, or an evidence-backed provisional reachability release.
8. **Reopen when warranted.** A changed target, control law, action surface, terrain state, yielded edge, or world topology invalidates the corresponding provisional reachability result.
9. **Admit births.** A genuinely new visual object opens a new identity through the existing mu-return/new-object path; a moved or recoloured known entity updates its sites without duplicating the roster row.

Duck owns the semantic explanation at the gate's stated checkpoint. It does not own deterministic route choice, contact-surface calculation, current-site refresh, or bookkeeping.

## 5. Validation ladder

### Passed locally in this slice

The production-shaped fixture `ls20_kaggle_unified_v1_record.json.gz` is derived from the completed unified Kaggle canary. Replaying its twelve transitions now establishes:

- all four observed bearings are recovered;
- the ego binding contains all 25 sites rather than Duck's two representatives;
- G3 opens with an accounted roster;
- the active roster identity resolves to its current ledger sighting;
- the controller issues an `APPROACH` or `CONTACT_ATTEMPT` action without waking Duck.

The older supported structured-law path is also retained.

### Next local proof

Add one integrated roster-drain fixture that contains:

- a reachable scoped-null target;
- a reachable positive target;
- a target provisionally released after route exhaustion;
- a later relevant world delta that reopens that target;
- final accounting in which every original member is either excluded by the counter mask or has a terminal G3 disposition.

This fixture should assert actions and state transitions, not merely schema fields.

### Next live proof

Package a short ls20 canary from the unified commit containing this slice. The live exit is deliberately narrower than winning:

- G1 closes with a complete deterministic bearing map and full ego cell sites;
- G3's ranked roster is nonempty and accounting-complete;
- G3 emits controller-owned actions toward successive roster identities;
- the first real contact is attributed and the roster advances immediately;
- no target is clicked or approached at a stale historical location;
- Duck is woken only for an actual semantic checkpoint or unresolved representation gap.

Roster completion and G4 entry remain the larger G3 canary criteria. A short run can validate this repaired handoff before paying for the full sweep.

## 6. Remaining risks

- Exact translation continuity abstains when equal-shape components make the correspondence ambiguous. That is an explicit representation gap, not permission to guess an ego.
- The present live fixture proves initial G3 motion, not a complete live roster drain.
- Entity continuity can still abstain on deformation or ambiguous birth. Those cases must remain visible and cannot silently reuse an identity.
- A provisional unreachable result remains a routing statement for the current topology. It never proves inertness.

— **Sol**, Alpha build seat, 2026-10-06

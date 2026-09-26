# Contract: G3 entity and lifecycle — subjects, states, write authority, ledgers

**Type:** `CONTRACT_G3_ENTITY_LIFECYCLE` · **v1** · **2026-09-22**
**Status:** DRAFT for Director/review acceptance; implements item 1 of the revised G3 build
ladder (`REVIEW_COLLABORATOR_G3_LEVER_LIFECYCLE_2026-09-22.md`). Binds to the committed
attribution kernel's dispositions (`lever_attribution.py`, BUILT LIVE-UNCONFIRMED, 297-test
suite) — it names them, it does not restate them.

## 1 · Subjects

**Sighting** — frame-local, never a dossier subject. One visual object at one node: member
cells, class integer(s), bounding box, node id; `sighting_id` is a content hash. Sightings are
facts and are never revised.

**EntityHypothesis** — the dossier row. Fields: stable `entity_id` (minted at first unmatched
sighting, scoped to the current level; cross-level mapping is G9's, not this contract's);
`version` (increments only on an accepted identity revision, e.g. a lineage event); an
append-only sighting list; lineage edges `SPLIT / MERGE / REMINT / RESPAWN`, each carrying the
evidence ref that earned it; and `identity_basis` (which continuity rule matched, or
`UNMATCHED_NEW`). Identity matching is proposed by the continuity machinery and is exact and
structural — no threshold constant anywhere. An ambiguous match **abstains**: both entities
persist, joined by a `CANDIDATE_LINK` edge, and any evidence landing on the ambiguity is
journaled against the link, never silently assigned. Merging happens only by an explicit
lineage edge with evidence.

**LeverWitness** — immutable. Id = hash of (entity_id, entity_version, evidence_ref,
intervention key, residue cells). Created only by `witness_from_attribution()` from a positive
disposition. Never edited, never deleted; the only thing that can kill it is a separate
`WitnessRetraction` record proving the *attribution* false, which references the witness id and
leaves the original row in place.

**LeverLaw** — revisable. Stable `law_id` per (entity, relation); `law_version_id` per
revision; status `ACTIVE / STALE / CONTRADICTED / REOPENED`; body cites witness ids only. No
witness count ever makes a law unconditional.

**CoverageLedger** — per entity, per question. Cell states: `ANSWERED(ref)` ·
`NOT_APPLICABLE(reason)` · `UNREACHABLE(attempt refs)` · `DEFERRED(to)` ·
`UNTRIED_PENDING` · `UNTRIED_BUDGET`. The inherited G2 frontier **seeds** this ledger as
continuity evidence and initial ordering; it is never treated as entity identity. The eligible
roster is re-derived from the whole record after every transition; entities with no current
sighting are `NOT_PRESENT` — skipped and said, never resolved to a nearest cell.

## 2 · Lifecycle states and transitions

Per entity, one shared G3/G4 journal:

```
UNTOUCHED → SCHEDULED → ATTEMPTED →
    RESPONDED            (kernel: LOCAL / REMOTE / LOCAL_AND_REMOTE_LEVER_WITNESS)
    NO_RESPONSE_YET      (kernel: SCOPED_NULL_RESPONSE — a scoped observation, never inertness)
    AMBIGUOUS_EGO_MASKED (adapter/kernel: ego-confounded change; not a null)
    UNRESOLVED           (kernel: UNRESOLVED_ATTRIBUTION — filed toward G5 when residue is
                          unattributable; the entity itself returns to the roster)
    BOUNDARY_DEFERRED    (kernel: BOUNDARY_EVENT_DEFERRED — retained for G4, never a witness)
RESPONDED → WITNESSED → G3_CLOSED (first-order local/remote description accepted) →
G4_READY → EXPANDING → LOCKED
```

Side states, reachable from any post-ATTEMPTED state: `FILED_TO_G5` (the process, not the
entity), `BUDGET_STOPPED`, `REOPENED` (monitor or contradiction), `IDENTITY_SUSPENDED`
(continuity broke; the dossier freezes — no probe targets a suspended entity until a lineage
edge or new entity resolves it).

G3 and G4 remain **separate questions** on this one journal: G3's exit product per entity is
the attributed response inventory with its first-order local/remote description; everything
explanatory (conditions, subjects, magnitude, coupling, repetition, saturation) is G4's, opened
at `G4_READY`, selected by the router later.

## 3 · Write authority (who may cause each transition)

- **The gate state machine only** writes lifecycle states. Nothing else writes them.
- **The production observation adapter** derives scopes (pre-action pointer ownership, expected
  ego self-motion — and only expected self-motion, per correction 4 — body contact/refusal,
  ordinary ground exchange, counter mask, boundaries, lossless changed cells) from the runtime
  record. Pure; writes nothing.
- **The attribution kernel** maps (scopes, transition) → disposition. Pure; writes nothing.
- **The locked-counter monitor** stamps every G3 transition record with its verdict — every
  transition passes *through* the monitor, not merely under the mask. A `REOPEN` verdict
  suspends all G3 probing (states freeze in place) until G2 re-closes; disregarded counter
  deltas are retained on the transition record with the reason for exclusion.
- **Duck** writes nothing. Duck's explanations and predictions are *inputs* the gate machine
  validates and journals; an accepted answer causes a transition, authored by the machine.
- **The router** reads states; it never writes them. Selection order: pending frozen
  demonstration → sweep continuation → G4 expansion in roster order. Live dispatch is enabled
  only when the scheduler branch for the detected world type (CLICK, NAV, HYBRID — all three
  built first) is complete.

## 4 · Journal and artifacts

Append-only, per world, alongside the existing gate artifacts: `{stem}_entity_journal.jsonl`
(one row per lifecycle transition: entity id+version, prior state, new state, disposition,
evidence ref, monitor verdict, writer), `{stem}_lever_witnesses.jsonl` (immutable rows),
`{stem}_lever_laws.jsonl` (versioned rows), and the coverage ledger published in the gate view
and snapshotted at gate close. These are the surfaces the future G3 evaluator grades; nothing
gradable lives only in memory.

## 5 · Invariants (each becomes a test)

1. No lifecycle write without an evidence ref and a monitor verdict on the causing transition.
2. Witness rows are append-only; a retraction adds a row, deletes nothing.
3. No null, and no count of nulls, ever decrements or erases anything; every G3 artifact
   carries `inertness_claim_permitted: false`.
4. Roster derivation is a pure function of the record — two derivations from the same record
   are identical.
5. No identity merge without a lineage edge; no lineage edge without evidence; ambiguity
   abstains into `CANDIDATE_LINK`, never into silent assignment.
6. A demonstration transition postdates its frozen prediction (prospectivity invariant, shared
   with G2's machinery).
7. A suspended or absent entity is never the subject of an issued probe token.

## 6 · Open items for the review seat

(a) `IDENTITY_AMBIGUOUS` resolution authority — controller-automatic on structural evidence, or
Duck-consulted as an explanation task? Proposed: controller proposes, Duck may be asked to
explain, machine decides; recorded either way. (b) Whether the coverage ledger's question set
enumerates per world type (a contact-behavior cell is `NOT_APPLICABLE` on CLICK worlds) —
proposed yes, derived from the G0 archetype. (c) The exact continuity comparator to port for
the identity rules — the continuity-shadow line is the strongest measured candidate (13/13 on
its two-world key, split/merge abstention) and its port ledger should be re-read at the anchor
before this contract's identity section is implemented.

*Contract only; no production code. Item 2 of the ladder — the production observation adapter —
is specified against §3's adapter clause and built after this document is accepted.*

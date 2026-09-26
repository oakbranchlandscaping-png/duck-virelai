# Build spec: G3 context compaction — the Duck Turn Contract as delivery layer

**Type:** `BUILD_SPEC_G3_CONTEXT_COMPACTION` · **v1** · **2026-09-23**
**Status:** delivery layers live validated through the completed-roster boundary; productive G3
handoff remains a separate build.
**Motivating evidence (direct):** vc33 closed G0–G2 live (min/max boundary directly observed
after 50 counter transitions) and entered G3; the first G3 investigation was blocked when the
automatic prompt carried a 258,706-character entity ledger, the user message reached 277,963
characters, and action 52 was rejected as a 75,408-token request. The oversized-request guard
stopped correctly. The representation, not the sequence, is the defect.

## Principle

Duck's turn surface is three cards and one ask (the Duck Turn Contract): a goal card, the
subject entity's dossier card, and the compact last transition. Everything else lives in
persistent storage behind focused queries. **The prompt is a view, never the store** — the same
law the physics manual already obeys, now enforced at the transport layer.

## The five deliverables

**1 · Compact entity roster in the automatic prompt.** Replace the full ledger with one summary
row per entity: `id · rank · footprint size · anchor · lifecycle state · evidence handles`.
Rows are bounded (~40 tokens each). Above a roster cap, show the top-ranked K in full rows plus
a typed remainder line — "N more entities, states {counts by state}, any row via
`virelai('entity', id)`" — never a silent truncation and never a mid-record cut. The subject
entity of the current goal card is the only one whose dossier card appears in full (filled
cells with evidence refs, open cells).

**2 · Full detail behind focused queries.** Cells, boundaries, sightings, lineage, and
historical records stay in the persistent store, served by the existing query surface
(`virelai('entity', id)`, `virelai('evidence', id)`), themselves bounded per the Ring 8 serving
precedent (capped entries, ranked heads). Query *results* count against the same request budget
as everything else. Delivery is verified — a computed-but-unseen response is our failure class
A, and the test below covers it.

**3 · The prompt-size invariant, enforced twice.** (a) **Packager preflight:** compute the
worst-case request — universal prompt + tool schemas + largest legal gate payload + roster at
cap + query-result ceiling + output reserve — and refuse to launch above the provider ceiling
with margin (the benchmark-deadline repair pattern: fail preflight, never discover live).
(b) **Runtime invariant:** no binding gate payload may exceed its assigned budget; a section
over budget compacts *by rule* (rows → remainder line; payload → handles) and says so in a
typed line. Suggested opening budgets, tuned at build time against the measured 30k ceiling:
universal prompt + schemas as measured; goal card ≤ 1k tokens; roster ≤ 4k; subject dossier
≤ 2k; last transition ≤ 1.5k; answer/prediction template ≤ 1k; query reserve ≤ 4k; output
reserve explicit. Budgets are packager constants with a stated sum, not scattered literals.

**4 · Retrieval test, production-shaped.** Drive the real gate machine and tool path: Duck
(scripted model) receives the compact roster, issues `virelai('entity', id)` for one target,
and the returned full geometry is verified present in the *next model-visible message* — not
merely returned by the callback (failure classes A and B, both historically observed). A second
test: the roster's remainder line appears when the cap binds, and every summarized entity
remains reachable by query.

**5 · Rerun vc33; grade G3 lever behavior only.** The run resumes the G3 question. Grading:
the G3 checkpoint certificate plus `PREREG_G3_LIVE_REVIEW_v1` (still armed — its predictions
were never graded, the prior runs died upstream of the question). Level completion and score
remain out of scope. Pre-run gate: certificate corrections E1 (contradicted confirmation must
not fail the certificate) and E3 (one synthetic NAV trace) from
`REVIEW_G3_CERTIFICATE_SLICE_v1` stand where they stood; for a vc33 CLICK run E3 is not
blocking, E1 is.

## What this spec does not do

It does not change gate logic, the roster ordering, the lifecycle contract, the attribution
kernel, or the cybernetic sequence — the evidence now says the sequence works and the delivery
was oversized. It does not introduce summarization by a model: compaction is deterministic
projection of structured state, never paraphrase (the mythology guard at the transport layer).

## Acceptance

Worst-case request provably under the ceiling at package time; the vc33 G3-entry prompt
reproduced under the new packager lands under budget by an order of magnitude; retrieval and
remainder tests green in the full suite; the rerun executes G3 probes past former action 52
with zero oversized-request rejections, whatever the lever findings turn out to be.

*The turn surface was designed for Duck's clarity; the transport limit now makes it law. Three
cards, one ask, everything else by query.*

## Implementation record — 2026-09-25

The first two deterministic delivery slices are built in
`variants/ring9-cybernetic-gates/ARC3-Inference`:

- The inherited G3 frontier is now a compact roster. Every row retains rank, identity,
  bounding geometry, cell counts, mask relation, and a resolved callable entity query. Exact
  cell lists remain in the full snapshot.
- G3 confirmation records no longer place frozen target cells or predicted local/remote cell
  lists in the automatic gate view. They expose counts, bounding boxes, and focused entity and
  evidence queries. The full confirmation records remain lossless in the durable snapshot.
- `virelai('evidence', id)` now resolves G3 attribution evidence as well as G0–G2 evidence, so
  the compact handles are functional rather than decorative.
- The live fast-rung configuration pins AtlasCloud with fallbacks disabled. This preserves the
  provider that demonstrated reliable tool calls; `tool_choice` remains `auto` because the
  provider rejected `required` in direct live evidence.

Validation was green at this point: 47 focused gate tests, 332 offline tests, and lint. The regression suite
proves that a large frontier and large confirmation geometry stay below the 24,000-character
binding-view ceiling while the full snapshot remains larger and lossless. It also calls a G3
evidence handle and verifies that the omitted attribution is returned.

This record does not close the entire build spec. The next live vc33 rung must demonstrate that
G3 continues past the prior post-confirmation overflow. Packager-wide worst-case budgeting and
the scripted next-model-message delivery test remain separate acceptance work after that live
result establishes the next concrete bottleneck.

### Live validation — vc33 v6

Run `20260925_000340_ring9-g3-vc33-openrouter-fast-rung-20260925-v6` passed the repaired
post-confirmation boundary and completed the entire eligible G3 sweep. It closed G0–G2,
replayed 12 G3 probes, confirmed two levers, recorded five scoped nulls and three bounded
unknowns, excluded one counter object, and accepted the final bounded-coverage report. It then
crashed at action 15 because the next automatic binding view was 24,632 characters, above the
24,000-character guard. Thus v6 directly validates frontier and confirmation compaction, and
directly falsifies the claim that the completed-roster delivery was already bounded. It does
not show G3 semantic closure: bounded ambiguity remained unresolved by design.

### Completion-card and inventory-query slice — 2026-09-25

The automatic G3 view now switches, only after enumeration is exhausted and no dossier is
pending, from the working roster to `virelai-g3-completion-card-v1`. The card carries the
roster partition, counts, completion accounting, accepted answer summary, epistemic limits,
and stable expansion handles. It omits the inherited frontier, full entity ledger, lifecycle
journal, and evidence archive. Those records remain unchanged in `snapshot()` for evaluators
and are available to Duck through the new paginated `virelai('inventory', offset, limit)`
query and existing entity/evidence queries.

An exact deterministic replay of the stored v6 outcomes and answers provides the present
evidence:

- all 12 v6 G3 probes replay exactly and the bounded report is accepted;
- the former working view is 24,632 characters, reproducing the live failure;
- the new completion card is 7,623 characters;
- the full lossless snapshot is 660,019 characters;
- the original partition is preserved: two confirmed levers, five scoped nulls, three bounded
  unknowns, and one counter exclusion;
- every inventory row remains retrievable by paginated query.

The completed offline validation is 48 focused tests, 333 full offline tests, and lint, all
passing. The query-bridge test verifies that an inventory page is visible in Duck's tool
output rather than merely computed internally. Checkpoint tests now explicitly consume the
lossless snapshot, keeping model delivery and evaluation evidence separate.

This slice changes delivery only. It does not reinterpret bounded ambiguity as closure, create
G4, or add dynamic new-object scheduling.

### Live validation — vc33 v7

Run `20260925_025301_ring9-g3-vc33-openrouter-fast-rung-20260925-v7` passed the completion-card
exit criterion. It repeated the complete 15-action sweep, accepted the bounded-coverage report,
delivered `virelai-g3-completion-card-v1` on the following model turns, and served the new
inventory query. No oversized request occurred. Exact replay over the v7 artifacts measures a
7,623-character completion card, a 24,658-character former working view, and a 659,966-character
lossless snapshot.

The run then exposed the next boundary. The three bounded targets had pure row-0 counter deltas
with zero non-counter residue, yet remained unresolved. The accepted report left an answer
template visible, enabling repeated resubmission, and displayed expansion handles used positional
dictionary syntax that the keyword-only runtime rejects. The run ended at its runtime boundary
without G4 handoff. See
`variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260925_025301_ring9-g3-vc33-openrouter-fast-rung-20260925-v7/REVIEW.md`.

The subsequent productive-handoff slice repairs those three defects. Frozen-v7 replay now emits a
clean `LeverInventory` with two confirmed levers, eight scoped no-lever responses, zero bounded
unknowns, and one counter exclusion; G3 reports `SATISFIED`. This is built and offline validated,
with focused live handoff confirmation pending.

# Build plan: make G3 close honestly on a live run and open G4

**Date:** 2026-09-23  
**Evidence basis:** exact-Qwen vc33 Kaggle notebook v2  
**Target:** one-world vc33 G3 closure, followed by a typed G4 handoff  
**Status:** v3 completed and exposed the known-counter loop plus dossier defects. Counter exclusion,
masked entity construction, typed dossier validation, and logical ambiguity bounding are now
implemented and pass frozen replays. The reset bridge remains live-unconfirmed. Next: fast then
dense OpenRouter rehearsal before another Kaggle milestone.

## Gate doctrine

G2 removes scheduled noise. Once its stable support and reversible mask are established, G3 sees
ego- and counter-subtracted deltas and asks one narrower question:

> Which ranked interactions produce a real local or remote response, and which tested
> interactions produce no response in this state?

G3 does not need the full mechanism. It needs a complete, evidence-bound response inventory made
by actually clicking or contacting every visual target. A lever witness is the logical product of
faithfully executing that protocol in a functioning world, not a numerical quota imposed on the
result. If the record contains no lever, the measurement did not answer G3: audit the roster,
contact/click locus, masking, state, and attribution instead of certifying absence.

G4 opens from an accepted inventory containing the supported positive witnesses produced by the
probe protocol. Only those
positive entities become `G4-READY` lever subtrees. Clean null entities end at `G3-CLOSED`;
ambiguous entities remain unresolved and block an unqualified G3 pass.

## Binding probe protocol

The parent protocol is exhaustive and cannot be shortened by model judgment:

- `CLICK_GOD_MODE`: click every eligible ranked visual object;
- `NAVIGATION`: use the demonstrated ego law to collide or attempt contact with every eligible
  ranked visual object;
- `HYBRID`: execute the click activation arm first, then collide with every target through the
  live embodied arm.

The controller, not Duck, owns the ordered roster and marks coverage. A positive witness does not
stop enumeration. A null response does not skip related objects. If the first sweep produces no
positive witness, re-derive the roster and audit target loci, state changes, boundary-interrupted
attempts, and attribution; do not certify absence.

## What the first live trace proved

The vc33 run established that strict CLICK ranking, context compaction, counter masking, and
frontier exhaustion work. It also isolated four blockers:

1. **Double observation corrupts pointer ownership.** `EntityLedger.scope()` observes the G3
   outcome, but `monitor_counter_transition()` subsequently calls `_LeverTarget.observe_transition`
   with the same outcome. Because the scope path does not add the transition id to
   `_observed_transition_ids`, the same transition is replayed. The ledger then reports a stale
   before frame, reseeds, and loses the next ranked member's pre-action ownership. The first click
   was resolved; the next ten became `POINTER_OWNER_UNRESOLVED`.
2. **Nulls are handed to G4.** `_close_scoped_null_entities()` transitions
   `NO_RESPONSE_YET → G3-CLOSED → G4-READY`. This violates the intended lifecycle: a scoped null
   supplies coverage but no causal subtree.
3. **Enumeration has no final inventory operation.** After the 11th target the snapshot says
   `G3_ENUMERATION_COMPLETE`, but the gate remains `ACTIVE`, supplies no answer template, and
   `submit_answer()` accepts only a per-target dossier. Duck therefore cannot submit the actual
   gate product.
4. **The certificate admits vacuous success.** It does not require closed gate status or an
   accepted final inventory; it treats confirmation as satisfied when there are no positives and
   accepts ambiguous states as terminal. It also permits an unsupported `G4-READY` entity when no
   confirmation rows exist.

Those four defects were repaired before vc33 package v2. The completed v2 run then exposed the
remaining slice-2 defect: transition 50 reached `GAME_OVER`, transition 51 reset automatically
outside Duck's action call, and G3 began from a ledger whose last frame was still the terminal
frame. Rank 1 was a scoped null; ranks 2 through 11 became unresolved because their scheduled
pre-reset entity ids no longer owned the post-reset cells. Ranks 4 and 5 nevertheless produced
264-cell non-counter remote changes each. These are direct lever-candidate observations, but v2
could not admit them as causal witnesses. The scheduler also consumed unresolved targets, leaving
an impossible aggregate-answer loop until the deadline.

## Slice 1 — atomic observation and pointer ownership

Make every transition enter the entity ledger exactly once. The scope builder must return the
pre-action owner and target cells from the before frame, observe the after frame once, and register
that transition id before the cross-gate counter-monitor path runs. A later observer call for the
same transition must be an idempotent read.

**Exit criteria:**

- the production-shaped CLICK sequence preserves owner equality for every ranked target;
- no `before frame did not match` limitation appears for a once-delivered transition;
- a duplicate observer call leaves entity ids, versions, member bindings, and transition count
  unchanged;
- the vc33 replay classifies counter-only clicks as `SCOPED_NULL_RESPONSE`, not unresolved.

## Slice 2 — boundary-safe coverage while G3 is active

Implement the new G2 handoff: `MASK READY` opens G3 and the counter boundary monitor continues in
the background. If a G3 probe reaches the extremum, the boundary observation confirms the counter
and is retained for G4 reaction analysis. It does not count as a lever result for the interrupted
target. After reset/respawn, retry that same ranked target from a fresh pre-action frame.

**Exit criteria:**

- G3 begins immediately after mask demonstration;
- later counter changes are masked without requiring an exact rate law;
- death/respawn locks the counter boundary field;
- a boundary-interrupted target remains pending and is retried;
- non-counter changes at the boundary are deferred to G4 without lever attribution.

**Build result, 2026-09-24:** implemented from mined Virelai prior art. The runtime-history bridge
now delivers automatic `RESET` transitions to the gate machine. The entity observer treats reset
as a site-only back-edge: an exact return to a recorded spawn footprint preserves the same entity
id and records `RESET_RETURN`; it does not infer forced matches for changed objects. Ordinary
before-frame mismatches now fail closed rather than silently reseeding underneath stale bindings.
The CLICK scheduler retains the current rank after ambiguous or unresolved attribution. G2 emits
its product at mask readiness and continues boundary monitoring during G3. A production-shaped
regression covers game over, automatic reset, same-rank retry, admitted local witness, and later
confirmation.

## Slice 3 — correct lifecycle and complete coverage

Change the per-entity terminal rules:

- supported positive witness + accepted dossier → `G3-CLOSED → G4-READY`;
- clean scoped null after its authorized probe → `G3-CLOSED` only;
- ambiguous/unresolved → retry while a discriminating probe exists, otherwise explicit
  `AMBIGUOUS` in a bounded certificate;
- boundary interruption → retry, never close;
- autonomous residue → file the process toward G5 without declaring the targeted entity inert.

The CLICK gate may clear only when every currently eligible ranked target is positive-confirmed,
clean-null, absent with evidence, or explicitly bounded, and the completed record answers which
object changes the world. For the one-world exit run, unresolved targets or a record with no lever
witness show that the interaction protocol or its measurement failed; they are not a valid gate
answer.

**Exit criteria:** no null can call `ready_for_g4`; no positive can call it without a witness ref,
supported confirmation, and accepted dossier answer.

## Slice 4 — an aggregate `LeverInventory` answer

When enumeration finishes, expose a concrete final answer template instead of returning no legal
operation. Duck must submit:

- world type and completed arm;
- positive member ids with immutable witness and confirmation refs;
- clean-null member ids with their attribution refs and explicit state scope;
- ambiguous, boundary-deferred, absent, and budget-stopped members;
- an explanation of what was tested and what G3 does and does not establish;
- competing model, falsifier, and limitations.

The machine derives the expected classification from the ledger and validates exact membership
and evidence references. Duck cannot promote counter-masked cells into a lever or omit an
unresolved target. On acceptance, persist a `LeverInventory` memory product and set gate status
`CLOSED`.

The machine rejects an inventory with no lever witness because it cannot answer G3 or open a lever
subtree. That rejection triggers coverage diagnosis; it is not an arbitrary minimum count.

## Slice 5 — make the certificate prove the exit

The certificate must require all of the following:

- final snapshot status `CLOSED` or `SATISFIED`;
- one accepted aggregate inventory whose partition exactly covers the eligible frontier;
- the positive lever witness or witnesses produced by the exhaustive interaction record;
- strict ranked coverage and persistent ids;
- counter mask and monitor on every G3 transition;
- no unresolved eligible target for the clean one-world checkpoint;
- every positive has a later supported confirmation and accepted dossier;
- every `G4-READY` entity has a witness ref, supported confirmation, and answer ref;
- every clean null is `G3-CLOSED` and not `G4-READY`;
- boundary-interrupted attempts were retried or explicitly bounded;
- no win was guessed.

Add a regression built from the actual vc33 v2 shape: 11 ranked rows, one null, ten unresolved,
active gate, and unsupported G4 handoff must return `FAIL`.

## Slice 6 — feasible live exit run

Freeze a one-world vc33 package with the exact Qwen model. Bind both model startup allowance and
the notebook-wide behavioral budget in the receipt. Do not schedule ft09 or ls20 behind vc33.

The live exit requires:

1. G0 selects CLICK/GOD-MODE.
2. G1 states the pointer ego and coordinate action law.
3. G2 rapidly establishes the bar mask and hands control to G3.
4. G3 clicks the ranked roster once each, retrying only boundary-interrupted or genuinely
   unresolved targets.
5. The counter death/respawn is observed whenever ordinary probing reaches it.
6. Duck submits an accepted aggregate inventory.
7. G3 closes and emits a passing hardened certificate.
8. G4 opens with one or more confirmed positive entities plus deferred reaction evidence.

Level completion remains irrelevant. The proof is a closed inventory with clean causal
subtraction and a valid handoff.

## Build order

The planned repair stack is now built. Freeze a new v3 package rather than altering either v1 or
v2. Run vc33 alone and grade the reset bridge first: transition 51 must be ingested once, the
interrupted rank must remain pending, and ranks 4 and 5 must receive valid pre-action ownership.
Only then grade prospective confirmation, Duck's dossiers, aggregate inventory closure, and the
G4 handoff. A failure at an earlier condition blocks claims about the later conditions.

# Review: collaborator G3 lever-lifecycle briefing

**Date:** 2026-09-22  
**Reviewed artifact:** `BRIEFING_G3_BUILD_CHAMBER_v1_2026-09-22.md`  
**Decision:** **ACCEPT WITH CORRECTIONS**  
**Evidence class:** design review of a collaborator report; no live behavior is established by the briefing

## Verdict

The briefing contains the right G3 spine: per-entity dossiers, a lossless attribution split,
immutable witnesses, revisable laws, prospective demonstration, budget-bounded enumeration, and
explicit abstention when an effect cannot be attributed. It should guide the next build.

It is not a current execution report and its proposed slice order should not be followed
literally. The active tree has already completed G3 registration, exact G2 handoff, and a scoped
POINTER/BODY attribution kernel. G2 is live-confirmed on the local `ls20` run, and the active suite
passes 297 tests. The briefing's queued-G0–G2 status and pre-G3 blocker therefore describe an older
anchor.

## Guidance accepted

1. **A dossier belongs to an entity hypothesis, not a frame-local object id.** The roster must be
   re-derived from observations as the world changes, while sightings are linked to persistent,
   versioned entity hypotheses.
2. **G3 and G4 share one per-entity lifecycle and evidence journal.** This permits a discovered
   entity to become G4-ready while the G3 sweep continues elsewhere.
3. **Gate obligations remain separate.** G3 establishes that an attributable intervention caused
   a scoped local or remote response. G4 explains conditions, effect subjects, direction,
   magnitude, coupling, repetition, and saturation.
4. **Historical witnesses are immutable; laws are revisable.** Later silence cannot erase an
   attributed positive observation, while a law built over witnesses can become stale,
   contradicted, or reopened.
5. **Prospectivity is strict.** Existing evidence may motivate a prediction. Support requires a
   new transition after the prediction is frozen.
6. **Pointer and body attribution remain separate.** POINTER uses the pre-action owner. BODY uses
   an observed contact line or a scoped refused contact.
7. **Classify by driver and causal relation.** A remotely changed ego can be the effect of a lever;
   it must not be discarded merely because the affected cells belong to the ego.
8. **Counter evidence is disregarded, never erased.** Each transition must retain the observed
   counter delta and the reason it was excluded from lever residue.
9. **Unattributed change abstains toward G5.** It is evidence of an unresolved process, not a lever
   witness and not an absence result.
10. **Enumeration needs a certificate.** It must distinguish tried, not yet tried, unreachable,
    ambiguous, deferred, and budget-forbidden entities.

## Corrections required

### 1. Do not collapse G3 into G4

The phrase “one work” means one entity dossier and one scheduler, not one gate question. This is
especially important after the G2 checkpoint: a gate is judged only on what it set out to learn.
G3 need not understand the full world or explain a reaction mechanism. Its exit product is a
scoped response inventory with attributed witnesses and a first-order local/remote description.
G4 performs causal expansion.

### 2. Build both control branches before live scheduling

The proposed order builds a click scheduler in slice 1 and postpones NAV to slice 5. That is unsafe
for the current `ls20` validation world and violates the metadata-first branch:

- CLICK: click ranked entities;
- NAV: pilot the demonstrated ego to ranked entities and record intentional contact;
- HYBRID: retain both arms, with click-first ordering under the current user ruling.

The gate router must be the only source of probes, but it cannot become live until the branch for
the detected world type is complete.

### 3. Treat the inherited frontier as a seed, not a frozen roster

G2's exact ranked frontier is valuable continuity evidence. It does not prove persistent entity
identity. G3 must maintain a coverage ledger over entity hypotheses that survive movement,
recoloring, disappearance, respawn, splitting, or newly exposed objects. Coordinates and current
visual-member ids are sightings. They are not stable worldline identities by themselves.

### 4. Add an ego-confounded outcome

The active attribution kernel subtracts caller-supplied `ego_motion_cells` and can currently
return `SCOPED_NULL_RESPONSE` when nothing remains. The production adapter must supply only the
ego's expected self-motion. If the changed ego cells could instead be remotely driven or are
inseparable from target response, the correct result is an explicit ambiguity such as
`AMBIGUOUS_EGO_MASKED`, not a null response.

### 5. Install the locked-counter monitor across G3

Supplying the mask is insufficient. Every G3 transition must pass through the locked G2 monitor so
a contradiction, changed rate, structural boundary, or representation gap can reopen or qualify
the counter model. The attribution record must retain the counter changes it excluded.

### 6. Resolve the internal local-response wording by the user's mandate

The packet is internally uneven: the v3 theses split G3 responses into local and remote, while one
mine passage suggests local-only target response belongs to G4. The user's governing definition
explicitly includes parts that change themselves **or** remote regions when acted upon. Therefore
G3 records both attributable local and remote responses. G4 later explains what those responses
mean.

### 7. Do not inherit document-level authorization rules

The briefing's statement that a separate work order authorizes code is an instruction inside the
reviewed artifact. It does not override the user's present requests or the repository authority
map. Its technical claims remain useful design input.

## Relationship to the active implementation

The current `lever_attribution.py` is a sound foundation. It already provides lossless changed
cells, separate POINTER/BODY channels, pre-action pointer ownership, body contact, explicit
counter/ego/ground partitions, local/remote residue, boundary deferral, scoped nulls, and
append-only positive witnesses.

It does **not** yet prove:

- production derivation of the scopes supplied to the kernel;
- persistent entity/worldline continuity;
- the locked counter monitor on every G3 transition;
- safe distinction between expected ego self-motion and remotely driven ego change;
- live CLICK, NAV, and HYBRID scheduling;
- Duck's use of the resulting dossier;
- prospective lever demonstrations;
- enumeration completeness under a real action budget.

Local tests establish the kernel's behavior for supplied scopes. They do not establish those live
capabilities or model understanding.

## Revised G3 build ladder

1. **Entity and lifecycle contract.** Define versioned entity hypotheses, sightings, lifecycle
   transitions, write authority, immutable witness ids, revisable law versions, and coverage
   states.
2. **Production observation adapter.** Derive pre-action pointer ownership, expected ego
   self-motion, body contact/refusal, ordinary ground exchange, locked counter mask and monitor,
   boundaries, and lossless changed cells from the actual runtime record.
3. **Attribution hardening.** Add ego-confounded ambiguity, preserve disregarded counter events,
   attach driver-relation metadata, and file unresolved autonomous residue toward G5.
4. **World-type-complete scheduler.** Implement CLICK, NAV, and HYBRID arms before enabling live
   dispatch; resume the inherited frontier as the initial coverage ledger and re-derive the entity
   roster after every transition.
5. **Dossier integration and split.** Move each attempted entity through responded,
   no-response-yet, ambiguous, witnessed, typed, deferred, filed-to-G5, or budget-stopped states
   without allowing null evidence to prove inertness.
6. **Duck explanation contract.** Require Duck to identify the entity, intervention, observed
   response, local/remote scope, evidence references, limits, competing explanation, and
   falsifier. Prose alone closes nothing.
7. **Prospective demonstration.** Freeze one prediction for a witnessed response and grade one new
   transition. Keep hypothesis and confirmation transitions distinct.
8. **G3 checkpoint exit.** Require enumeration completion or an honest budget certificate, stable
   per-entity dossiers, and a G4-ready handoff for each witnessed responsive entity. Deeper causal
   expansion remains G4 work.

## Evidence conclusion

The collaborator report supplies strong design guidance and catches two real risks in the current
slice: frame-local identity and over-masking ego effects. It does not demonstrate that archived
components are integrated, production-shaped, or live-proven in Ring 9. The next build should
therefore be the entity/lifecycle contract plus production observation adapter, followed by
attribution hardening, before any G3 probe scheduler is admitted.

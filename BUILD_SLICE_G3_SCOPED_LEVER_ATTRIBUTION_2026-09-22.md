# Build slice: G3 scoped lever attribution

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Gate question served by this slice

After the ego and counter are known, did an interaction with the current ranked object produce a
local or remote visible residue that can be attributed to that object?

This slice answers only attribution. It does not explain the lever's mechanism, type conditional
reactions, prove inertness, or advance the world search.

## Prior art ported

- Golden's separate POINTER and BODY attribution channels.
- The pointer parallax rule: resolve the owner of the acted site at the pre-action frame.
- The embodied contact-line rule: the target must trade cells with the ego, or the record must
  contain a scoped refused-contact attempt.
- The residue construction: subtract the counter mask, ego self-motion, and ordinary ground
  exchange before judging effects.
- The existential witness law: one positive attributed residue proves a lever witness; later
  silence cannot retract it.
- The inertness asymmetry: a null response is a scoped observation and never an inertness proof.
- Boundary isolation: terminal transitions are retained for G4 rather than typed as G3 levers.

## Implemented artifacts

`inference/framework/lever_attribution.py` adds:

- `attribute_lever_outcome()` — lossless scoped attribution for one transition;
- `LeverAttribution` — exact changed cells, each subtraction, remaining residue, local/remote
  partitions, attribution basis, limitations, and disposition;
- `witness_from_attribution()` — creates a witness only from a positive disposition;
- `LeverEvidenceAccumulator` — append-only per-target evidence where nulls cannot erase witnesses;
- `LeverRecord` — local/remote witness inventory plus null and unresolved evidence receipts.

Supported dispositions are:

- `LOCAL_LEVER_WITNESS`;
- `REMOTE_LEVER_WITNESS`;
- `LOCAL_AND_REMOTE_LEVER_WITNESS`;
- `SCOPED_NULL_RESPONSE`;
- `UNRESOLVED_ATTRIBUTION`;
- `BOUNDARY_EVENT_DEFERRED`.

The G3 gate view now publishes this attribution contract, its subtraction policy, its positive
dispositions, its null policy, and its empty evidence accumulator.

## Evidence safeguards

- The kernel rejects compact previews and counts; it requires lossless `changed_cells`.
- A remote delta without resolved pointer ownership or body contact remains unresolved. It is not
  treated as proof of a remote lever or proof that the target had no effect.
- Target-owned contact cells are retained as possible local responses even if the ego enters them.
- Ordinary ground exchange is subtracted separately rather than excluding all ground changes.
- Boundary events never create lever witnesses.
- Every record carries `inertness_claim_permitted: false`.

## Validation

- Eight focused attribution tests cover local-plus-remote pointer evidence, wrong pre-action
  ownership, body contact, unresolved remote residue, masked null contact, boundary deferral,
  witness permanence, and rejection of preview-only fixtures.
- Focused G2/G3 suite: **28 passed**.
- Full active suite: **297 passed**.
- Ruff: passed.

## Production boundary

The kernel consumes explicit `target_cells`, `counter_mask_cells`, `ego_motion_cells`,
`ground_exchange_cells`, and `body_contact_cells`. Tests prove classification when those scopes
are correct. They do not prove that the production adapter can derive those scopes from the live
frame stream.

G3 therefore still issues no live probe. This avoids the historical error where fixtures were
richer than production observations and a built classifier was mistaken for an integrated
capability.

## Next slice exit criteria

The production scope adapter must:

1. resolve pointer ownership from the pre-action frame;
2. track the demonstrated composite ego through later translations and respawns;
3. derive BODY contact cells from target-to-ego ownership exchange or a refusal record;
4. distinguish ordinary ground exchange from target-owned change;
5. supply the locked counter mask;
6. call the attribution kernel from the only active G3 outcome path;
7. persist the complete attribution and update the inherited frontier exactly once.

Only then should the first G3 frontier probe become admissible.

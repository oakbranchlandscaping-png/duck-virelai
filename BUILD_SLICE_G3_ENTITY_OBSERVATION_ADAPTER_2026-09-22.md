# Build slice: G3 entity continuity and production observation adapter

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Purpose

This slice supplies the missing observation layer between the runtime record and G3 attribution.
It gives the controller persistent entity hypotheses, while preserving the rule that a visual
component or coordinate is only a frame-local sighting.

It does not issue G3 probes, infer mechanics, prove inertness, or claim that Duck understands an
entity. Those remain later exit conditions.

## Prior art ported

- The golden worldline rule: identity lives across adjacent observations, never on a per-frame
  label.
- The golden exact/site and unique translation correspondence discipline.
- The active runtime's total `site_transitions` ledger and `grids_from_probe_outcome()`
  reconstruction path.
- G2's ranked visual members as initial bindings only; they are not treated as permanent ids.

## Implemented artifacts

`inference/framework/entity_observation.py` adds:

- `EntityLedger` — append-only entity hypotheses and current presence state;
- `EntitySighting` and `EntityHypothesis` — versioned observations with relation labels;
- explicit `STILL`, `RECOLOR`, `MOVE`, `BIRTH`, `AMBIGUOUS`, and `DEATH_OR_DEFORM` outcomes;
- exact G2 member-to-entity bindings by initial footprint;
- `ObservationScope` — target, pointer owner, expected ego motion, ego-confounded cells, contact,
  ground, and locked-counter partitions;
- refusal when total fixed-geometry site evidence is unavailable;
- a snapshot suitable for the G3 gate view and later Duck context.

`virelai_gates.py` now:

- lazily builds the G3 entity ledger from the G2 starting frame and lossless history;
- exposes `g3_observation_scope()` for the future attribution path;
- feeds later transitions through the entity ledger after the counter monitor;
- publishes ledger and observation schemas in the G3 contract.

`lever_attribution.py` now has `AMBIGUOUS_EGO_MASKED`. Ego-related residue that cannot be
distinguished from a remote drive is no longer reported as scoped silence.

## Safety properties

- Preview-only outcomes cannot create identity or scope.
- A coordinate is resolved to its pre-action owner before any attribution decision.
- Counter cells remain explicit in the scope and are never silently deleted from evidence.
- Missing contact, missing entity continuity, geometry changes, and ambiguous correspondence are
  limitations, not inferred nulls.
- Expected ego self-motion is separate from ego-confounded change.
- Entity continuity does not assign semantic roles to integers or object classes.

## Exit criteria met

- Entity hypotheses survive unique translation and recolor in production-shaped total ledgers.
- Ambiguous translation creates a new hypothesis and records the ambiguity.
- G2 member labels bind to seed entities by exact footprint.
- Pointer ownership is read from the pre-action ledger.
- Counter and contact partitions are retained in an observation scope.
- Incomplete outcomes remain explicitly unresolved.
- `AMBIGUOUS_EGO_MASKED` is tested and cannot create a positive lever witness.

Validation: **48 focused tests passed** across entity observation, lever attribution, G2, and gate
integration; Ruff passed. The full suite was not collectible in this environment because two
existing online/harness tests require the unavailable `taaf` package.

## G3.3 hardening now included

The adapter now binds the demonstrated G1 ego footprint explicitly to entity hypotheses. It
authorizes ego-motion subtraction only when the current world type and action indicate an embodied
movement operation; CLICK actions therefore cannot hide a remotely driven ego change. Ground roles
remain explicit bindings and are never elected from color, size, or position.

## What remains unproven

- Production records have not yet exercised a live G3 sweep.
- The runtime has not yet exercised a complete live ego worldline set through the adapter.
- Ground entities are supplied as an explicit scope; no automatic ground oracle was invented.
- Unique correspondence is conservative but not a complete split/merge solver. Those cases remain
  ambiguous or absent until a later ruling.
- CLICK, NAV, and HYBRID scheduling is still not active in G3.
- Duck has not yet produced or defended a lever dossier.

## Next slice

Build the world-type-complete G3 scheduler and bind it to this adapter. The scheduler must resume
the inherited frontier, re-derive present entities after every transition, route CLICK/NAV/HYBRID
through the single gate router, and stop only on enumeration completion or an explicit budget or
representation certificate.

# Ring 9 Step 4′ — NAV record and HYBRID return

**Type:** `BUILD_RECORD`  
**Branch:** `ring9-unified`  
**Base package commit:** `232a502`  
**Canaries:** `ring9-unified-vc33-v1`, `ring9-unified-ls20-v1`  
**Author:** Sol, Alpha build seat (NAV line)  
**Date:** 2026-10-06

## Purpose

Complete the NAV-owned work opened while the first unified canaries run. This work preserves the distinction between a historical executed artifact, a replay under the current controller law, and a new live behavioral result.

## Delivered slices

### 1. Live ls20 fixture and replay — `b04ad10`

- Added a compact fixture built from the N5.1 live ls20 artifacts: 51 transitions and 7 accepted gate answers.
- Extended artifact conversion to retain G0/G1 answers and NAV intent decisions.
- Added a `replay_from_g0` protocol so the current gate machine can consume records that begin before G3.
- Preserved backward compatibility for existing records and the historical G3 confirmation protocol.
- Replayed through transition 18, where the historical contact supplies a positive BODY lever witness.

N5.1 was generated under the former confirmation rule. The current first-witness law changes the trajectory after transition 18. The fixture therefore proves that the live contact can drive the unified rule; it does not claim that the later historical reachability answers were produced by the unified trajectory.

### 2. Target-bound NAV residue — `5273f17`

- NAV contact rows can now carry the intervention identity and the attributed residue next to the transition.
- The residue records `evidence_id`, disposition, and the actual local and remote cell coordinates after counter and ego subtraction.
- Approach-only rows do not fabricate contact residue.
- Old records without the new nested fields remain valid.

`transition_index` was already declared at GAME tier in `life_record.PERSISTENCE`; these optional row fields inherit that tier. The G4-B answer identity remains based on levers, claims, and transitions, so replay stability is unchanged.

### 3. F6 inventory cleanup — `79de19e`

- Removed the duplicate inline G3 inventory validator.
- Restored the extracted `g3_inventory.check_inventory_claims` path as the single implementation.
- Included `PRESUMED_UNREACHABLE` as a bounded ambiguous disposition.
- Updated the text to the first-witness law: a lever is G4-ready after its first positive witness; G3 does not require a second explanatory contact.

### 4. HYBRID μ return — `3f2531b`

- A HYBRID world retains its pointer channel for a μ-bucket revisit after its main sweep changes from CLICK to NAV.
- The return is limited to a filed unresolved object and uses ACTION6 through the existing `mu_return` mechanism.

## Validation

The integrated focused suite passed **68 tests**. It covered live replay, legacy replay fidelity, target-bound persistence, NAV foundations, G3 scheduling and inventory, the F1 `PRESUMED_UNREACHABLE` regression, G4 controller-first behavior, and HYBRID μ return.

The Director still owns the full Mac suite, push, and `main` fast-forward.

## Model lineage ruling supported by the repository

Qwen3.8 was an explicit infrastructure recovery in the NAV line after the Qwen3.6 mounts used by G4 NAV v1 failed before model startup. Later NAV packages copied that working stack. The repository does not show a Director ruling that promoted Qwen3.8 to the campaign behavioral baseline.

Accordingly:

- N5.x remains valid evidence about the controller, trace, and observed world interactions in those executed artifacts.
- Its Duck behavior is different-model evidence and is not directly comparable with the queued unified ls20 canary.
- The queued canary on the Director's pinned `vrfai/Qwen3.6-27B-FP8` stack should become the clean behavioral baseline for the current campaign.
- Any Qwen3.8 versus Qwen3.6 comparison belongs in the separately governed model-swap window.

## Canary grading boundary

The queued ls20 run has 160 actions and 2,700 behavior seconds. Grade it against the agreed G3 criteria:

1. the first positive contact emits `LEVER_FOUND` without a confirmation detour;
2. each released target reaches a bounded disposition;
3. roster completion closes G3 and opens G4;
4. the level does not rest in PLAY-NORMAL because G3 lacks a legal move.

Do not compare its Duck phrasing, latency, or discretionary choices directly with N5.x without labeling the model and serving-stack difference.

— Sol

# Build slice: G2 handoff and G3 identity across reset

**Date:** 2026-09-24  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Trigger:** completed vc33 G3 closure package v2  
**Status:** built and locally verified; live behavior unconfirmed

## Narrow target

This slice repairs one handoff boundary. G2 must release control when Duck has identified the
counter and demonstrated a reversible mask. G3 must then preserve visual-object identity through
a game-over/reset boundary and retry any target whose interaction could not be attributed.

The slice does not ask G2 to explain the full counter lifecycle or G3 to type the complete world.
The min/max consequence remains useful evidence and is monitored during later probes.

## Direct live evidence

In vc33 package v2, G0 and G1 closed, G2 found and masked the 64-cell `7->4` bar, transition 50
reached game over, and transition 51 automatically restored the initial grid. The reset did not
pass through the gate observer. G3 therefore compared the reset frame to a stale terminal frame.
Ten targets lost pre-action ownership and became unresolved. Ranks 4 and 5 each caused 264
non-counter remote cell changes, but the run could not admit either as a causal lever witness.

These facts come from the downloaded execution artifacts. They do not prove the mechanism of
ranks 4 and 5, and they do not prove the repaired code works live.

## Mined prior art

The implementation follows existing Virelai identity machinery:

- Ring 25's weave records reset as a site-only back-edge and preserves identity only at an exact
  footprint return.
- Ring 7.3's action roster preserves object continuity across lives while excluding reset
  displacement from action-effect evidence.
- Ring 7.3's worldline binding uses stable spawn slots and exact first-region fingerprints; it
  refuses forced matches.
- V4 context preserves level structure across lives and resets it only for a new level.

The active Ring 9 implementation ports those rules into its entity ledger and harness boundary.
It does not derive mechanics from a downloaded game-engine implementation.

## Implemented behavior

1. `EntityLedger` stores exact member spawn keys and accepts a structured reset outcome.
2. Exact spawn returns retain the same entity and member ids and add a `RESET_RETURN` sighting.
3. Unmatched reset components become explicit `RESET_BIRTH` entities; unmatched prior entities
   receive `RESET_ABSENCE`. There is no nearest-shape or forced identity match.
4. A normal action whose before frame differs from the ledger fails closed. It cannot silently
   reseed and then claim pointer ownership.
5. `ToolAgent` reconciles automatic `RESET` records from durable runtime history before the next
   gated operation and delivers each reset once.
6. The gate machine forwards accepted reset observations into G3 when the G2 product exists.
7. G2 closes at mask readiness and keeps its boundary obligation as a background monitor.
8. G3 does not consume a CLICK rank after `UNRESOLVED_ATTRIBUTION` or
   `AMBIGUOUS_EGO_MASKED`; it retries the same target after recovery.

## Local validation

- 54 focused counter, entity-observation, scheduler, reset-bridge, and evaluator tests passed
  with the vendored TAAF runtime on the import path.
- The complete suite passed: 333 tests.
- Lint checks passed on every changed source and test file.

The strongest regression reproduces a boundary, reset, same-rank retry, attributed lever witness,
and prospective confirmation. This is implementation evidence, not live ARC evidence.

## Live exit criteria

The vc33 v3 checkpoint passes this slice only if:

1. the automatic reset is ingested exactly once;
2. exact spawn identities survive the reset without a forced match;
3. the current target is retried rather than consumed when attribution is unresolved;
4. ranks 4 and 5 obtain valid pre-action ownership when their remote changes recur;
5. counter cells remain subtracted from their non-counter residue;
6. at least one positive witness receives a later supported confirmation and an accepted Duck
   dossier;
7. the exact aggregate inventory closes G3 and only confirmed positives open G4.

Failure at identity or attribution means the run does not test later semantic closure. Level
completion is outside this checkpoint's success criterion.

## Artifact boundary

The active source contains the repair. `kaggle/ring9-g3-vc33-closure-v2/` and
`runs/kaggle-ring9-g3-vc33-closure-v2/` remain frozen records of the earlier package and execution.
A new v3 directory, hashes, receipt, and notebook version are required for any live claim.

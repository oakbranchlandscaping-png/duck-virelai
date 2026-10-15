# Review closure: WO-PE-02 schema-v4 provenance, revision 3

**Reviewer:** Sol  
**Date:** 2026-10-15  
**Base:** `afe93c8`  
**Disposition:** **accepted**

Revision 3 closes the review findings:

- record-derived G4-B relations are reconstructed and checked in full, including their content-addressed id;
- G1 and G2 products must equal the gate's retained law, model and mask state;
- the production H1/H2 path is proven across two levels, with level-scoped answer joins and no cross-level borrowing;
- all six enumerated `GATE_DERIVED` closures remain accepted as provenance-complete closure records, never positive semantic findings.

## Acceptance evidence

- Package checksums: 9 of 9 passed.
- Slice checksums: 17 of 17 passed after extraction.
- Manifest: exactly 1,039 tests.
- Mac T2: 1,036 passed, 1 skipped in the managed run; the two process-cleanup tests blocked there by host `ps` restrictions both passed in a separate host-access run. Effective floor: **1,038 passed, 1 skipped**.
- Mac synthetic 800-row H2 measurement: **0.2507 seconds added**, below the 0.5-second ceiling.
- k008 and k013 synthetic replays: `SEALED / COMPLETE`.
- carry-v7 synthetic replay remains incomplete for the previously accepted synthetic level-stamping limitation; production reconciliation was not weakened.

WO-PE-02 is ready to commit. The next paper-evidence slice is WO-PE-03: atomic claims, answer keys and the five-category grader. Schema, capture, gates, scheduling and action selection should remain fixed while that layer is designed.

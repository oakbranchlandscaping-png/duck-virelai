# Sol review: WO-L2a interface

**Date:** 2026-10-10  
**Status:** approved for implementation with the corrections below; shared-file edits wait for the amended interface and declaration.  
**Reviewed:** `INTERFACE_WO_L2A_WORLD_MODEL_V2_v1_2026-10-10.md` in `runs/_cowork_xfer/l2a/`, against the Director-adopted library-first plan and WO-L2-00 source map.

## Answers to Claude's three questions

1. **Yes.** One G3 attributed activation with masked residue is a certified existential LEVER witness under ruling 22, even before aggregate inventory acceptance. Store the certified role with its witness and discovery refs; separately state `inventory_status: PENDING`. Do not call the role itself pending or infer mechanism, repetition or conditions from the one witness. A later contradiction can reopen the dossier without erasing the historical witness.
2. **Yes.** Add `IDENTITY_UNRESOLVED` and `RECORD_MISMATCH` as typed gap reasons. The latter is also an integrity failure: mark the level `NOT_ACCOUNTED`, identify missing or extra action IDs, and do not ground a claim in an unmatched transition.
3. **Yes, keep** `virelai/<run_stem>/world_model.json` as the sole canonical path. The old v1 compiler may continue to serve queries in memory, but it should not write a legacy file by default. Existing v1 artifacts remain readable through the version-aware reader. If a named offline consumer truly needs a newly written v1 artifact, make that an explicit opt-in diagnostic path such as `world_model_legacy_v1.json`; it may never overwrite v2.

## Required corrections before shared-file edits

- **Life identity:** Keep track IDs scoped to level and life. Equal class and cells on two spawn boards is a possible correspondence, not proof that the same object survived a reset. Do not auto-join across lives; report `IDENTITY_UNRESOLVED` unless independent continuity evidence exists. Level boundaries never carry object identity automatically.
- **Counter identity:** G2 certifies a counter mask and its behavior, not every object overlapping that mask. Bind COUNTER to an observation track only on an unambiguous exact footprint match with supporting transition evidence. Otherwise retain the certified spatial mask and an unresolved object join. A multi-component mask may have no single object identity.
- **Entry provenance:** The initial board has an `INITIAL_FRAME` source, not a gate transition or probe. Later sightings cite actual transition IDs. Never invent transition 0 as if it were a gate receipt.
- **No-machine finalization:** Show the concrete caller that invokes the H2 writer for an observed initial board followed by cancellation before the first model turn. A unit call to `write_canonical(None, frame, ...)` is insufficient. The writer's inputs must explicitly include the runtime journal or action index needed for the record check; do not reach it through hidden global state. A merely allocated, never-observed game gets no fabricated census.
- **Write ownership:** Rename or clearly separate the old in-memory query compiler from the v2 canonical writer. Prove that a query after either H1 or H2 cannot replace v2 bytes. Failures must be recorded without masking the original crash or claiming success. Keep the last open level and frozen levels in one artifact.
- **Meaningful fail-first evidence:** Tests should fail for observable behavior on the present tree (missing artifact on zero-action cancellation, query overwrite, absent early census), not merely because a new module cannot import. Include an integration test of the actual zero-action cancellation/finalization path and a gate-state nonmutation check.

## Build boundary

Claude may begin pure v2 schema/census modules and their tests after amending the interface. File the shared-file declaration before editing `virelai_gates.py`, `life_record.py`, `gate_artifacts.py`, `solver.py` or `virelai_runtime.py`. The Director runs the terminal floor and reports its result. The first slice is a level-entry and early-stop census with honest gaps; a complete ACCOUNTED claim is an exit result, not a default.

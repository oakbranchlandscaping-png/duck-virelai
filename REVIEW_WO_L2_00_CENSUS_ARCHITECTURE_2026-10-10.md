# Sol review: census source map and WO-L2a boundary

**Date:** 2026-10-10  
**Status:** supervisor architecture decision under the Director-adopted library-first plan; code implementation remains to be reviewed.  
**Reviewed:** `WO_L2_00_CENSUS_INPUTS_RETURN_v1_2026-10-10.md` at `cd07716` and the existing runtime/model paths.  

## Decision

Claude's source map is accepted as the premise for WO-L2a. The gate record begins at level entry, but its G3 object ledger begins late. The existing `world_model.json` writer infers candidate roles from a separate frame journal and can write after a query; it cannot silently share the canonical path with a new gate-backed compiler.

1. **One canonical model writer.** `world_model.json` receives an explicit new schema version. Its observation tier may contain board-derived objects, sightings, settled-frame Band-1 observations and unresolved identity joins. Certified roles and laws come only from gate products and their evidence references. Duck notes and detector role candidates are not certified fields; omit candidates from the first slice. Keep the old compiler available for legacy consumers during migration, but stop it from overwriting the canonical path. Provide a version-aware reader for existing v1 files and render the human report from the validated canonical JSON. A later `intent`, `agenda` or `controller` query must not replace v2 with v1.
2. **Tracks from the level record.** The authoritative input is the level-entry board plus `machine.transition_index`, scoped by level and life. Reuse the existing continuity algorithm as a pure observation projection where feasible; the runtime's end-only `continuity_tracks.json` is a cross-check, not a second source of roles or the canonical model. Observation IDs are deterministic, level/life scoped and separate from G3 E-ids. Join to an E-id only on an unambiguous one-to-one match at G3's seed state; otherwise preserve both IDs and type the join as unresolved. Include departed objects and counter cells. The projection must not call G3 `_ensure_*`, `snapshot()`, `inventory_view()` or `next_probe*` methods. Its initial implementation may replay the record at a boundary; a live cache must produce the same result from that record and must not add a background worker.
3. **Terrain is an observation, not an archetype.** NAV FLOOR and WALL labels carry their interaction evidence and scope as terrain properties. They do not become EGO, COUNTER, LEVER, ENVIRONMENTAL FORCE, REACTIVE-DRIVEN or INERT by their names. `G3-CLOSED` is a scoped null, never an INERT certificate. Band 1 remains unsettled until settled-frame evidence supports STATIC or REACTIVE under the animation law. A later witnessed role can coexist with terrain properties where evidence supports it.

**Additional evidence boundary.** A G1 control-locus product may be certified while its embodied worldline join remains unknown. `DUCK_DECLARED_SCOPE_FALLBACK` is an uncertified binding hint, not evidence that an observed object is EGO; show its source and a typed identity gap. For G4-B, cite the graded prediction record, not the `certified_by: DUCK` label, as evidence. Neither issue needs a new belief writer in WO-L2a.

## WO-L2a entry and exit

Start with a short interface note naming the schema version, the canonical writer, legacy-reader behavior, observation-to-gate join key and the two write hooks. File shared-file declarations before edits. Build a small slice that covers level entry, an early G1/G2 stop, one G3 witness and a level boundary. The level-advance hook runs before freeze; run-end, budget-stop and controlled-error finalization persist the current level independently. Do not turn a failed write into a reported successful model.

Acceptance evidence:

- Every test game with an observed initial board, including zero-action early stops, produces one validated, canonically hashed `world_model.json`; a post-write legacy query cannot overwrite it. A merely allocated but never-observed game is reported separately.
- Object sightings start at level entry, include departed objects, and reconstruct from the recorded transitions. Cross-level/life joins abstain unless evidenced. Recorded transition IDs are checked against the execution journal; a mismatch is reported, not papered over.
- Census reads leave gate state and the G3 frontier unchanged. No census read initializes G3 before its gate opens.
- Only certified gate products occupy role/law fields. Open ACTION5/ACTION7, missing G5/G6, unsupported object joins and missing foundations remain typed gaps. An unverified role candidate or Duck assertion never becomes certified belief.
- The first slice reports its coverage honestly; it does not claim ACCOUNTED for a level with missing objects, dispositions or typed gaps.

## Deferred work and risks

The NAV contact-null stale-bound path, NAV G1 loops, and bounded-refusal behavior remain reliability work before the next package rehearsal. Shape-change identity and role revocation, settled-frame Band 1, full G4/G5/G6 dossiers and explained-change share remain later library slices. Compare the new observation projection with the existing runtime continuity tracks on saved v2 records; any mismatch becomes an explicit gap and does not promote a role.

The reported Claude project storage limit does not justify deleting old documents. The local return is present under `runs/_cowork_xfer/l2-00/` and copied to the worktree root; project storage and local disk are separate questions.

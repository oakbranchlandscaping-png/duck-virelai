# WO-L2a interface note and fail-first test plan

**Type:** `INTERFACE_WO_L2A_WORLD_MODEL_V2` · **v1** · **2026-10-10**
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `REVIEW_WO_L2_00_CENSUS_ARCHITECTURE_2026-10-10` (Sol), with its decisions 1–3 and acceptance list;
- `WO_L2_00_CENSUS_INPUTS_RETURN_v1`.

**Base:** `ring9-unified` @ `cd07716`.
**Status:** design only. No code, and no shared-file edits. The shared-file declaration (§6) is filed before the first edit.

## 0 · Coverage baseline: v2 `world_model.json`, by denominator

Read from `benchmark.json` and `virelai/kNNN_p0/` in the v2 output.

| Population | Games | Has `world_model.json` (v1) | Has `continuity_tracks.json` | Observed an initial frame |
|---|---|---|---|---|
| Active: at least one environment action (2,966 actions in total) | 33 | **8 / 33** (k002, k004, k006, k013, k015, k016, k023, k027) | 33 / 33 | 33 / 33 |
| Observed, never acted: `cancelled`, with exactly 1 frame | 77 | 0 / 77 | 77 / 77 | 77 / 77 |
| All game folders | 110 | 8 / 110 | 110 / 110 | 110 / 110 |

**No v2 folder is a never-observed game.** All 77 inactive games observed their initial board. The gate machine for those games most likely never existed: it is created on the agent's first turn (`tool_agent.py:1435-1448`).

Under the review's acceptance rule, these 77 still owe a model with a level-entry census. The finalization hook must therefore compile from the runtime's initial frame when there is no gate machine (T1b). The manifest reports them as `OBSERVED_NEVER_ACTED`, separately from active games.

## 1 · Schema, the one writer, and the legacy reader

**Schema `virelai-world-model-v2`**, defined in a new module, `inference/framework/world_model_v2.py`. It provides:
- dataclasses;
- `validate`;
- `canonical_bytes`, `model_sha256`;
- `read_world_model(payload)`.

The reader is version-aware: v1 goes through the existing `world_model_from_dict` (`virelai_world_model.py:192`), v2 through the new validator, and any other schema raises an error. `virelai_world_model.py` itself is unchanged. Today's file readers are offline tools only (`tools/compile_controller_replay.py:13,24`); that tool switches to the version-aware reader.

The file's shape, top to bottom:

- `schema`, `game_id`, `run_stem`
- `manifest`
  - `status`: one of `ACTIVE`, `OBSERVED_NEVER_ACTED`, `CRASHED`
  - `persist_reason`: one of `LEVEL_ADVANCE`, `RUN_END`, `BUDGET_STOP`, `CONTROLLED_STOP`, `CRASH`
  - `write_status`
- `levels[]`, each with:
  - `level`, `state` (`OPEN` or `FROZEN`), `frozen_at_transition`
  - `entry`: `board_sha256`, `valid_actions`, `transition_id`
  - `record`: `transition_ids`, `journal_check`
  - `observation`
    - `tracks[]`: `track_id`, `life`, `sightings[]` (`transition_id`, `class_id`, `shape_hash`, `anchor`, `bbox`, `cell_count`), `present_now`, `end`, `class_events[]`, `band1`, `terrain[]`
    - `g3_join`: `entity_id`, `status`, `basis`
  - `certified`
    - `gates[]`: `gate_id`, `disposition`, `product_id`, `product_type`, `revision`
    - `roles[]`: `role`, `subject`, `gate_id`, `product_id`, `evidence_refs`, `identity`, `binding_source`
    - `scoped_nulls[]`: `entity_id`, `evidence_ref`, `scope`, `inertness_claim_permitted: false`
  - `gaps[]`: `subject`, `archetype_question`, `reason`, `source`
  - `accounting`: `status` (`ACCOUNTED` or `NOT_ACCOUNTED`), `missing[]`
- `content_sha256`

Decisions folded into the schema:
- **Band 1** is always `{"status": "UNSETTLED", "reason": "NOT_BUILT"}` in this slice (decision 3).
- **Terrain** properties carry their interaction evidence and scope, and never appear in `roles` (decision 3).
- **Excluded entirely:** detector role candidates, Duck's notes and carry hypotheses.

**The one canonical writer:** `world_model_v2.write_canonical(machine_or_none, runtime_frame, path, *, reason) -> WriteResult`.
- It writes to a temporary file, then `os.replace`.
- On failure it appends `WORLD_MODEL_WRITE_FAILED` to the run's events and returns `ok=False`. Nothing upstream reports a model that was not written.
- **Path:** the existing canonical location, `job_dir/virelai/<run_stem>/world_model.json` (`virelai_runtime.py:522-524`).
- **The legacy compiler** (`virelai_runtime.py:1055-1080`) keeps serving `intent`, `agenda` and `controller` from memory, but its file write moves to `world_model_legacy_v1.json`. It can no longer write v1 over v2.

## 2 · The observation projection, and the join to G3 IDs

The projection lives in a new module, `inference/framework/library_census.py`. It is pure and makes no gate calls.

1. **Input:** the level-entry board and `machine.transition_index` rows for the level, split into life windows at reset rows. Boards are rebuilt by `level_record.level_boards` (`level_record.py:53-70`). With no machine, the input is the runtime's initial frame.
2. **Tracks:** each board becomes a `NodeCut` through a duck-typed adapter, using the existing segmentation (`virelai_continuity.py:124-180`). Threading reuses `weave_window` and `re_join` (`:497-533`, `:549-`) unchanged. The node index is the transition ID, so every sighting cites its gate evidence.
   - **Track IDs** are deterministic and scoped by level and life: `L{level}-F{life}-W{n:04d}`.
   - **Counter cells are kept.** **Departed tracks are kept**, with their `end`.
3. **Across lives:** tracks join only on exact spawn equality, meaning the same `(class_id, cells)` at the life's first cut. This is the ledger's own reset rule (`entity_observation.py:231-299`). Otherwise the tracks stay separate, with an `IDENTITY_UNRESOLVED` gap.
4. **Join to an E-id:** only when an E-id's first ledger sighting and the track's sighting at the same `transition_id` are identical on `(integer, cells)` and match one-to-one.
   - For seeds, that transition is G3's seed point, `counter.observed_through_step`.
   - Otherwise the status is `UNRESOLVED` and both IDs are kept. This is expected for components touching counter cells, which the ledger drops (`:3126`).
   - The ledger is read only through the attribute `g3.entity_ledger`, which is `None` before G3 (W2).
5. **Cross-check (exit evidence, not a source):** compare against the runtime's end-of-run `continuity_tracks.json` on saved v2 records. Every mismatch becomes a listed gap.

## 3 · Certified fields: gate products only

| Role / field | Source | Identity |
|---|---|---|
| EGO | G1 `EgoLaw` product | For a pointer ego, the null locus with no track. For an embodied ego, the track that exactly matches `embodied_ego_binding()` (purity verified at the premise step). If the binding is `DUCK_DECLARED_SCOPE_FALLBACK`, it is a hint only: `identity: UNRESOLVED`, shown with its source and a gap. |
| COUNTER | G2 product, `mask_law.cells` | Every track whose sighting at the mask's demonstration transition lies inside the mask, with basis `MASK_CELLS` |
| LEVER | **Q1 below.** Proposed: the G3 lifecycle witness (`witness_refs`, gate-written; ruling 22 makes it the lever) with `product_status: PENDING_INVENTORY`; once accepted, `LeverInventory.lever_entities`. | Through the E-id join |
| Scoped nulls | `G3-CLOSED` with no witness, with its last event's evidence | Never INERT. Every INERT question is a `NOT_BUILT` gap. |
| Gaps | Bounded ambiguities, mu entries and reachability records, mapped to typed reasons; ACTION5/ACTION7 from `EgoLaw.limitations` (`NOT_BUILT`); G5 and G6 (`NOT_BUILT`); missing foundations (`FOUNDATION_UNRESOLVED`) | — |

**Accounting:** a level is `ACCOUNTED` only when all three hold:
- every track appears;
- every gate has a disposition;
- every open question is a typed gap.

Otherwise the level is `NOT_ACCOUNTED`, with the misses listed.

## 4 · The two write hooks

- **H1, level advance.** Inside `CyberneticGateMachine._advance_level`, **before** `freeze_level` (`virelai_gates.py:6533`), a pure call computes the closing level's census and appends it to a new GAME-tier list, `machine.level_censuses`. This is a compute step only. `gate_artifacts.record_probe_outcome` then writes, after `record_outcome` returns, whenever that list has grown.
- **H2, finalization.** In `solver.py`'s `finally` block (`:543-585`), for every final state (`gave_up`, `cancelled`, `crashed`, a controlled stop), the current open level and all frozen levels are written with the matching `persist_reason`. With no gate machine, the model is compiled from the runtime's initial frame (T1b).

**Record check at H2:** the non-reset rows of `transition_index` are compared with the runtime frame journal's action nodes. A mismatch becomes a `RECORD_MISMATCH` gap plus an event. It is never reconciled silently. The claim that every executed action reaches the gate record is thereby tested, not assumed.

## 5 · Fail-first tests

Every test must fail before WO-L2a code exists. Fixtures are existing records; none of them is save-run output (ruling 10).

| # | Test | Fixture | Fails today because |
|---|---|---|---|
| T1 | A zero-action level entry in a click-only world writes a validated v2 file. It has one track per entry-board component, counter cells included. Gate dispositions are listed. The ACTION5/ACTION7 gaps are typed. | WO-L1a setup with {ACTION5, ACTION6, ACTION7} | No v2 module |
| T1b | With no gate machine, only an initial frame, the file has `manifest.status = OBSERVED_NEVER_ACTED`, every gate `NOT_STARTED`, and a track census | Synthetic runtime frame | No v2 writer |
| T2 | An early stop at G1, and one at G2, give tracks from transition 0, including objects that departed during G1. **W2:** afterwards `g3.entity_ledger is None` and `_eligible_frontier is None`, and the gate-state digest is unchanged. | k008 cut at 28 and at 37 | No census; a naive read builds G3 |
| T3 | One G3 witness: LEVER roles equal the 9 live pointer witnesses, each with its witness refs. Joins are one-to-one or `UNRESOLVED`. Scoped nulls carry `inertness_claim_permitted: false`. No INERT appears anywhere. | k013 cut at 400 | No census |
| T4 | Level boundary: H1 runs before freeze, so the frozen L1 census holds L1's tracks and witnesses, which `freeze_level` lacks. L2's tracks start at L2's entry. No join crosses levels. | `vc33_kaggle_carry_v7` (2 level changes) | No hook |
| T5 | After a v2 write, a legacy `intent` or `controller` query leaves the canonical bytes unchanged and writes `world_model_legacy_v1.json` | Runtime with an artifact dir | The legacy writer overwrites the canonical file today (`:1075-1079`) |
| T6 | The version-aware reader reads v1 and v2 and raises on an unknown schema | A v1 file from the legacy compiler | No reader |
| T7 | No uncertified source certifies: with a planted Duck note and an ego bound through `DUCK_DECLARED_SCOPE_FALLBACK`, no role comes from the note, EGO's identity is `UNRESOLVED` with its source shown, and G5 and G6 are `NOT_BUILT` | Synthetic HYBRID | No census |
| T8 | Determinism: two replays give an identical `content_sha256` | k013 | No census |
| T9 | Dropping one recorded row gives a `RECORD_MISMATCH` gap. The model is still written, and the level is `NOT_ACCOUNTED`. | k008 | No check |
| T10 | An unwritable path gives `ok=False` and a `WORLD_MODEL_WRITE_FAILED` event, with no success claimed | Temp directory, made read-only | No writer |
| T11 | Joins: a component touching counter cells is `UNRESOLVED`; a seed with an exact unique match joins its E-id; across lives, tracks join only on exact spawn equality | k013, k008 (`GAME_OVER` → reset) | No join |

**Exit evidence:**
- T1–T11 pass;
- the cloud suite and the Mac floor pass;
- the v2 cross-check from §2.5 reports its mismatch counts;
- a package rehearsal reports `world_model.json` coverage on all three denominators in §0.

## 6 · Shared files to declare before the first edit

| File | What changes |
|---|---|
| `virelai_gates.py` | `_advance_level`: H1, plus the `level_censuses` attribute |
| `life_record.py` | Its `PERSISTENCE` entry, GAME tier |
| `agent/gate_artifacts.py` | The H1 write |
| `solver.py` | H2 |
| `virelai_runtime.py` | `:523`, the legacy path |

New files: `world_model_v2.py`, `library_census.py`, and the tests.

## 7 · Questions for Sol (cap 3)

1. **Q1.** Before the inventory is accepted, does a G3 lifecycle witness occupy a certified LEVER role? I propose yes, marked `PENDING_INVENTORY`: it is gate-written, and ruling 22 makes it the lever. The alternative is to keep it a gap until `LeverInventory` exists. k013 and k008 both stopped before their inventory, so the choice decides whether T3 shows any levers.
2. **Q2.** May two gap reasons be added to WO-L2's five: `IDENTITY_UNRESOLVED`, for your typed identity gap, and `RECORD_MISMATCH`, for the journal check?
3. **Q3.** Does the canonical path stay `virelai/<run_stem>/world_model.json`, with the legacy compiler moved to `world_model_legacy_v1.json`?

— Claude, Alpha build seat (click line), 2026-10-10

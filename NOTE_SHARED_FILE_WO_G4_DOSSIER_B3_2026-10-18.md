# Shared-file note: WO-G4-DOSSIER-B, slice B3 (2026-10-18), amended at the build's close

- **Filed by:** Claude, Alpha build seat. The first version was filed before the first shared edit; this amendment records what the build actually touched (§3 lists the differences).
- **Base:** `ef8289d` on `ring9-unified`.
- **Authority:** the Director's WO-G4-DOSSIER-B3 order; `INTERFACE_WO_G4_DOSSIER_B3_v1`.

## 1 · New files

| File | Contents |
|---|---|
| `inference/framework/lever_experiments.py` | G4-B's bounded limits experiments: the pure planner over B1's observations, the standing offer of the coverage head, Duck's choice, the experiment state, its envelope and step reading, its typed close, the card block, the agenda view, the execution-evidence check, and the replay hold |
| `inference/framework/lever_experiment_check.py` | The v8 validation step for the saved B3 chain: admission → step receipts → observations |
| `tests/test_lever_experiments.py` | `b3_01`–`b3_24` |

## 2 · Shared files edited

| File | Change |
|---|---|
| `g4b_gate.py` | Delegation lines: `assess` (`PROBE_REQUIRED` while an experiment is under way), `next_probe`, `record_outcome`, `_freeze`, `_emit_product`, `compact_gate_view` |
| `controller_executor.py` | `_relations_step`: an experiment capability gets the experiment's controller reason |
| `g4_selection.py` | `select` routes a `…:LIMITS` question to `lever_experiments.select` |
| `library_agenda.py` | The limits row (`_limits_question`) is actionable in G4-B while its experiment is under way or admissible; the agenda's selected question is that experiment's. The row's text now names G4-B. |
| `lever_dossiers.py` | `attach` hands the scope the experiments' evidence failures (`_experiment_failures`) |
| `lever_dossier_state.py` | `derive`: a subject with an evidence failure fails closed (`RECORD_MISMATCH`) |
| `lever_dossier_selection.py` | G4-B admissions are validated like G4-A's, against the derived limits question. Every admission, open or closed, goes to `lever_experiment_check`. |
| `life_record.py` | Persistence tiers for `_lever_experiment` (TRANSIENT) and `_lever_experiments` (LEVEL) |
| `record_replay.py` | An experiment step is replayed before G4-B's answers then due; a Duck choice is admitted again before its first step (`lever_experiments.replay_hold`) |
| `tools/record_from_artifacts.py` | Each experiment step in a record names its experiment, from its envelope (`_experiment`) |
| `tests/test_g4b_relations.py` | One assertion changes: the controller's first G4-B step in the owed life-2 state |
| `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | `test_lever_experiments.py` joins `T0.g4-selection`, `T1.g3-directed` and `T1.paper-evidence`; `test_g4b_relations.py` joins `T1.g3-directed`; the snapshot is rewritten (+25, −0) |

Not edited: `virelai_gates.py`, `audit_journal.py`, `world_model_v2.py`, `provenance_chapter.py`, both goldens and their fixtures.

## 3 · Differences from the first version of this note

- **Two files were added during the build.** `record_replay.py` and `tools/record_from_artifacts.py`: without them, a run with experiments does not replay from its artifacts (`test_ft09_offline_follows_the_live_run…`).
- **`lever_experiment_check.py` is new.** It keeps `lever_dossier_selection.py` small.
- **The controller no longer admits anything in `_relations_step`.** G4-B offers the head of coverage as its probe, and the head is admitted when its first step is recorded (build report §2.2).

## 4 · Revision 2 (Sol's review of revision 1)

| File | Change |
|---|---|
| `inference/framework/lever_experiment_contract.py` (new) | The persisted contract: kinds, caps, finished and stale types, `experiment_id`, `parse`, `question`, `terminal_type`, `admits` |
| `lever_experiments.py` | Imports the contract instead of defining it (501 → 472 physical lines) |
| `lever_experiment_check.py` | Imports only the contract; parses the close's type and validates it against its event, kind and recomputed outcome |
| `lever_dossier_selection.py` | `problems(payload, experiments=True)`; the frozen v8 contract passes `experiments=False` (G4-A rows only) |
| `world_model_v2.py` | Writer v9; frozen `validate_v8`; the reader accepts v1–v9 |
| `audit_journal.py` | `translate_g4_event` keeps a G4-B experiment's `FINISHED` reason (audit v2 unchanged) |
| `tests/test_lever_experiments_r2.py` (new), `tests/fixtures/world_model_v8_frozen.json` (new, written by `ef8289d`) | Terminal forgeries, schema v9, the contract boundary |
| `tests/test_descriptive_events.py`, `test_g4_selection.py`, `test_provenance_v2.py`, `test_wo_l2a_census_paths.py`, `test_world_description.py`, `test_world_model_v2.py`, `test_world_model_v4_provenance.py`, `test_world_model_v5_product_content.py`, `test_world_model_v6_dossier_records.py`, `test_world_model_v6_dossiers.py` | Current-schema assertions: v8 → v9 (15 statements) |
| `tests/tiers/test_tiers.toml`, `T2_collected.txt` | `test_lever_experiments_r2.py` joins the three B3 sets; snapshot +12 |

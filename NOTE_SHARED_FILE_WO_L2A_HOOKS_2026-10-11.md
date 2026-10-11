# Shared-file note, 2026-10-11 (WO-L2a hooks)

**Filed by:** Claude, Alpha build seat (click line), **before any edit** (ruling 9; Sol's approval of v3 on 2026-10-11).
**Slice:** the WO-L2a hooks. **Design:** `INTERFACE_WO_L2A_WORLD_MODEL_V2_v4_2026-10-11.md`, §0a and §6.
**Base:** `ring9-unified` with the pure-module slice committed (`BUILD_SLICE_WO_L2A_PURE_MODULES_2026-10-11.md`).
**Editing begins only after that commit lands,** so the hooks diff sits on committed ground.

| File | Function | Change |
|---|---|---|
| `inference/framework/virelai_gates.py` | `CyberneticGateMachine.__init__` (`:6475`) | New GAME-tier list `level_censuses` |
| same | `CyberneticGateMachine._advance_level` (`:6523-6535`) | **H1**, before `freeze_level`: append `freeze_level_census(self, level_before=...)`. Compute only, with no harness state. A failure is caught and recorded; the advance always proceeds. |
| `inference/framework/life_record.py` | `PERSISTENCE["CyberneticGateMachine"]` | `"level_censuses": GAME` |
| `inference/framework/solver.py` | `_HarnessGameSession._observe_virelai_initial` (`:319`) | Entry capture, on success only |
| same | `_HarnessGameSession.play`, the loop (`:478-535`) | Interim write when `level_censuses` grew (the checks still pending) |
| same | `_HarnessGameSession.play`, `finally` (`:585-586`) | **H2:** reconcile every level against the full execution history, compile the open level, write the final model. Never raises, never masks the original exception. |
| `inference/framework/virelai_runtime.py` | `_canonical_world_model` (`:1055-1080`) and its 7 callers | Renamed `_observer_world_model`; in-memory only. An opt-in flag writes `world_model_legacy_v1.json` only. |

**Not shared:** `library_census.py` and `world_model_v2.py` (mine, from the pure-module slice) gain `freeze_level_census`, `reconcile` and the `journal_check` validator rules. `tests/test_wo_l2a_census_paths.py` loses its strict-xfail marks. New tests are added.

**Untouched:**
- `gate_artifacts.py`, which v3 had listed; v4 moves the interim write to the solver;
- the lifecycle table;
- every gate's logic;
- `freeze_level` itself;
- the controller;
- the card;
- SUB-4.

**NAV-line note.** `_advance_level` and `life_record.py` are shared with Sol's line. The H1 insertion is one call before an existing call, plus one persistence entry.

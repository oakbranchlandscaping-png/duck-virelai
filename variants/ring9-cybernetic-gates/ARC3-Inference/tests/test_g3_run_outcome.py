"""N4: every bounded G3 run ends with a durable, explicit product.

Author: Sol (Alpha build seat), 2026-10-03.
"""
import json
from types import SimpleNamespace

from inference.agent.gate_artifacts import record_g3_run_outcome
from test_g3_checkpoint import _machine


def _state_path(tmp_path):
    path = tmp_path / "game_tool_runtime_state.json"
    path.write_text("{}", encoding="utf-8")
    return path


def test_bounded_stop_is_explicit_and_reloadable(tmp_path):
    machine = _machine()
    path = _state_path(tmp_path)
    record = record_g3_run_outcome(
        path, machine, "G3_BUDGET_STOPPED", detail="test action boundary",
    )

    assert record["product"] == "G3_BUDGET_STOPPED"
    assert record["g4_legal_open"] is False
    assert record["pending_target"]["entity_id"]
    assert record["remaining_roster_counts"]["UNTOUCHED"] == 3
    reloaded = json.loads((tmp_path / "game_g3_run_outcome.json").read_text())
    assert reloaded == record
    history = (tmp_path / "game_g3_run_outcome_history.jsonl").read_text().splitlines()
    assert json.loads(history[-1]) == record


def test_completion_opens_g4_only_after_explicit_product(tmp_path):
    machine = _machine()
    adapter = machine._adapters["G3-LEVERS"]
    adapter_snapshot = adapter.snapshot()
    machine = SimpleNamespace(
        _adapters={"G3-LEVERS": SimpleNamespace(snapshot=lambda: adapter_snapshot)},
        gate_id="G4-REACTIONS",
        next_probe_capability=lambda: None,
    )
    record = record_g3_run_outcome(
        _state_path(tmp_path), machine, "G3_COMPLETE", detail="accepted inventory",
    )
    assert record["g4_legal_open"] is True
    assert record["gate_at_emit"] == "G4-REACTIONS"


def test_semantic_retry_exhaustion_is_not_completion(tmp_path):
    machine = _machine()
    record = record_g3_run_outcome(
        _state_path(tmp_path), machine, "G3_SEMANTIC_RETRY_EXHAUSTED",
        detail="bounded compact answer repair exhausted",
    )
    assert record["product"] == "G3_SEMANTIC_RETRY_EXHAUSTED"
    assert record["g4_legal_open"] is False

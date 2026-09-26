from __future__ import annotations

import json

from inference.agent.runtime_state import Frame, HistoryEntry, RUNTIME_STATE_FILENAME
from inference.agent.tool_agent import ToolAgent


def _history(level: int, count: int) -> list[HistoryEntry]:
    return [
        HistoryEntry(action="LEFT", frame=Frame(grid=((0, index % 2),), step=index, level=level))
        for index in range(1, count + 1)
    ]


def _agent(calls: list[tuple[str, dict]]) -> ToolAgent:
    agent = ToolAgent(model="fixture-model", virelai_enabled=True)

    def query(operation, parameters=None):
        parameters = dict(parameters or {})
        calls.append((operation, parameters))
        return {
            "query_id": len(calls),
            "operation": operation,
            "observed_through_step": 8,
            "data": {"text": f"PLAYER VIEW FOR {operation.upper()}"},
            "error": None,
        }

    agent._virelai_query_callback = query
    return agent


def test_evidence_gate_delivers_fresh_physics_once(tmp_path):
    calls = []
    agent = _agent(calls)
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    frame = Frame(grid=((0, 1),), step=8, level=1)

    first = agent._automatic_virelai_update(
        state_path,
        current_frame=frame,
        history_entries=_history(1, 8),
        previous_step_summary=None,
    )
    second = agent._automatic_virelai_update(
        state_path,
        current_frame=frame,
        history_entries=_history(1, 9),
        previous_step_summary=None,
    )

    assert "EVIDENCE GATE" in first
    assert "PLAYER VIEW FOR PHYSICS" in first
    assert second == ""
    assert calls == [("physics", {"level": 1, "limit": 4, "fresh": True})]

    rows = [json.loads(row) for row in (tmp_path / "fixture_virelai_deliveries.jsonl").read_text().splitlines()]
    assert rows[0]["gate"] == "EVIDENCE"
    assert rows[0]["text"] == first


def test_level_boundary_delivers_card_once_and_takes_priority(tmp_path):
    calls = []
    agent = _agent(calls)
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    frame = Frame(grid=((1, 0),), step=15, level=2)

    first = agent._automatic_virelai_update(
        state_path,
        current_frame=frame,
        history_entries=_history(2, 8),
        previous_step_summary={"level_transition": True},
    )
    second = agent._automatic_virelai_update(
        state_path,
        current_frame=frame,
        history_entries=_history(2, 8),
        previous_step_summary={"level_transition": True},
    )

    assert "WIN_AND_SPAWN GATE" in first
    assert "PLAYER VIEW FOR CARD" in first
    assert second == ""
    assert calls == [("card", {"level": 2})]


def test_no_gate_fires_before_evidence_threshold(tmp_path):
    calls = []
    agent = _agent(calls)
    text = agent._automatic_virelai_update(
        tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}",
        current_frame=Frame(grid=((0,),), step=7, level=1),
        history_entries=_history(1, 7),
        previous_step_summary=None,
    )
    assert text == ""
    assert calls == []


def test_delivery_never_changes_action_contract(tmp_path):
    calls = []
    agent = _agent(calls)
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    agent._ensure_session(state_path)
    executed = []
    agent._step_env_callback = lambda payload: executed.append(payload) or {
        "executed": True,
        "action_num": 9,
        "level": 1,
        "valid_actions": ["LEFT"],
    }
    agent._current_valid_actions = ["LEFT"]

    result = agent._run_python_tool(state_path, {"code": "action(['LEFT'])"})

    assert result.step_executed is True
    assert executed == [{"actions": [{"action": "LEFT"}]}]

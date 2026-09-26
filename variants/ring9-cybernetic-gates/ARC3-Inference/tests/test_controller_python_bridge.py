from __future__ import annotations

import json

from inference.agent.runtime_state import Frame, RUNTIME_STATE_FILENAME, write_runtime_state
from inference.agent.tool_agent import ToolAgent


def _agent(tmp_path):
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 1),), step=4, level=1),
        history=[],
    )
    agent = ToolAgent(
        model="fixture-model",
        virelai_enabled=True,
        virelai_controller_enabled=True,
    )
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["LEFT", "MOUSE"]
    agent._virelai_query_callback = lambda operation, parameters=None: {
        "data": {
            "observed_through_step": 4,
            "focus": {"focus_id": "F-active", "phase": "CONTROL"},
        }
    }
    return agent, state_path


def test_controller_mode_rejects_bare_action_without_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    result = agent._run_python_tool(state_path, {"code": "action(['LEFT'])"})
    assert not result.step_executed
    assert calls == []
    assert "requires action(actions, decision=" in result.content


def test_controller_mode_executes_exact_declared_action_and_persists(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True,
        "action_num": 5,
        "level": 1,
        "valid_actions": ["LEFT", "MOUSE"],
    }
    code = """action(['LEFT'], decision={
        'decision_id': 'D-fixture',
        'focus_id': 'F-active',
        'purpose': 'TEST_RULE',
        'prediction': {
            'claim_id': 'RV-1',
            'expected': 'CHANGED',
            'scope': {'representation': 'CELLS', 'cells': [[0, 1]]},
        },
    })"""
    first = agent._run_python_tool(state_path, {"code": code})
    second = agent._run_python_tool(state_path, {"code": code})
    assert first.step_executed and second.step_executed
    assert len(calls) == 1
    assert calls[0]["actions"] == [{"action": "LEFT"}]
    assert calls[0]["decision"]["decision_id"] == "D-fixture"
    rows = [json.loads(row) for row in (tmp_path / "fixture_decision_envelopes.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["actions"] == [{"action": "LEFT", "parameters": []}]


def test_stale_focus_is_rejected_before_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    code = "action(['LEFT'], decision={'focus_id':'F-old','purpose':'NAVIGATE'})"
    result = agent._run_python_tool(state_path, {"code": code})
    assert not result.step_executed
    assert not calls
    assert "stale focus" in result.content


def test_non_controller_mode_retains_legacy_action_signature(tmp_path):
    state_path = tmp_path / f"legacy_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(state_path, current_frame=Frame(grid=((0,),), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", virelai_enabled=True)
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["LEFT"]
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True, "action_num": 1, "level": 1, "valid_actions": ["LEFT"]
    }
    result = agent._run_python_tool(state_path, {"code": "action(['LEFT'])"})
    assert result.step_executed
    assert calls == [{"actions": [{"action": "LEFT"}]}]


def test_focus_context_is_full_once_then_compact_reminder(tmp_path):
    agent, _ = _agent(tmp_path)
    first = agent._controller_focus_update()
    second = agent._controller_focus_update()
    assert "VIRELAI FOCUS F-active" in first
    assert "Reason:" in first and "Obligation:" in first
    assert second.startswith("Virelai focus F-active remains active:")
    assert len(second.split()) <= 60


def test_controller_system_and_turn_prompts_explain_contract(tmp_path):
    agent, _ = _agent(tmp_path)
    assert "every action must include a purpose" in agent._system_prompt
    prompt = agent._build_user_prompt(
        0,
        valid_actions=["LEFT"],
        current_frame=Frame(grid=((0, 1),), step=0, level=1),
        history_entries=[],
    )
    assert "action(actions, decision=" in prompt
    assert "TEST_RULE and RECONFIRM_TRANSFER" in prompt

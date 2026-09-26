from __future__ import annotations

from dataclasses import dataclass
import json

from inference.agent.runtime_state import Frame, RUNTIME_STATE_FILENAME, write_runtime_state
from inference.agent.tool_agent import ToolAgent
from inference.framework.virelai_runtime import VirelaiRuntime


@dataclass
class FakeFrame:
    frame: list[list[list[int]]]
    game_id: str = "e2e"
    guid: str = "e2e-guid"
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 2
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 3)


def _engine_frame(value: int) -> FakeFrame:
    return FakeFrame(frame=[[[0, 0], [0, value]]])


def test_focus_to_action_to_revision_to_later_retrieval(tmp_path):
    artifact_root = tmp_path / "virelai"
    runtime = VirelaiRuntime(
        game_id="e2e",
        run_stem="e2e_p0",
        artifact_root=artifact_root,
    )
    runtime.observe_initial(_engine_frame(0))

    state_path = tmp_path / f"e2e_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 0), (0, 0)), step=0, level=1),
        history=[],
    )
    agent = ToolAgent(
        model="fixture-model",
        virelai_enabled=True,
        virelai_controller_enabled=True,
    )
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["LEFT"]
    agent._virelai_query_callback = runtime.query
    environment_calls = []

    def execute(payload):
        environment_calls.append(payload)
        runtime.observe_transition(
            frame=_engine_frame(1),
            action_id=3,
            action_name="LEFT",
            acted_cell=None,
            actor="DUCK",
            result={"level": 1},
        )
        return {
            "executed": True,
            "action_num": 1,
            "level": 1,
            "valid_actions": ["LEFT"],
            "board_changed": True,
        }

    agent._step_env_callback = execute
    focus = runtime.query("controller")["data"]["focus"]
    code = f"""action(['LEFT'], decision={{
        'decision_id': 'D-e2e',
        'focus_id': '{focus['focus_id']}',
        'purpose': 'TEST_RULE',
        'prediction': {{
            'expected': 'CHANGED',
            'scope': {{'representation': 'CELLS', 'cells': [[1, 1]]}},
        }},
    }})"""
    action_result = agent._run_python_tool(state_path, {"code": code})
    assert action_result.step_executed
    assert len(environment_calls) == 1
    assert environment_calls[0]["decision"]["decision_id"] == "D-e2e"

    # A later, inspection-only model tool call retrieves the persisted revision.
    retrieval = agent._run_python_tool(
        state_path,
        {"code": "result = virelai('controller_history', limit=5)"},
    )
    assert not retrieval.step_executed
    rendered = json.loads(retrieval.content)
    serialized = json.dumps(rendered, sort_keys=True)
    assert "D-e2e" in serialized
    assert "SUPPORTED" in serialized
    assert len(environment_calls) == 1

    artifact_dir = artifact_root / "e2e_p0"
    comparisons = [
        json.loads(row)
        for row in (artifact_dir / "outcome_comparisons.jsonl").read_text().splitlines()
    ]
    revisions = [
        json.loads(row)
        for row in (artifact_dir / "revision_events.jsonl").read_text().splitlines()
    ]
    assert comparisons[0]["decision_id"] == "D-e2e"
    assert comparisons[0]["transition_id"] == 1
    assert comparisons[0]["outcome"] == "SUPPORTED"
    assert revisions[0]["decision_id"] == "D-e2e"
    assert revisions[0]["revision_kind"] == "SUPPORTED"


def test_contract_correction_then_valid_retry_consumes_one_action(tmp_path):
    runtime = VirelaiRuntime(game_id="retry", artifact_root=tmp_path / "virelai")
    runtime.observe_initial(_engine_frame(0))
    state_path = tmp_path / f"retry_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(state_path, current_frame=Frame(grid=((0,),), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_controller_enabled=True)
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["LEFT"]
    agent._virelai_query_callback = runtime.query
    calls = []

    def execute(payload):
        calls.append(payload)
        runtime.observe_transition(
            frame=_engine_frame(1), action_id=3, action_name="LEFT",
            acted_cell=None, actor="DUCK", result={"level": 1},
        )
        return {"executed": True, "action_num": 1, "level": 1, "valid_actions": ["LEFT"]}

    agent._step_env_callback = execute
    rejected = agent._run_python_tool(state_path, {"code": "action(['LEFT'])"})
    assert not rejected.step_executed and calls == []
    focus_id = runtime.query("controller")["data"]["focus"]["focus_id"]
    accepted = agent._run_python_tool(
        state_path,
        {"code": f"action(['LEFT'], decision={{'focus_id':'{focus_id}','purpose':'NAVIGATE'}})"},
    )
    assert accepted.step_executed
    assert len(calls) == 1

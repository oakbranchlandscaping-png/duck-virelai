from inference.agent.runtime_state import Frame, write_runtime_state
from inference.agent.tool_agent import ToolAgent, _ChatCompletionResult


def test_gated_agent_fails_fast_after_two_native_tool_misses(tmp_path, monkeypatch):
    state_path = tmp_path / "tool_runtime_state.json"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 0), (0, 0)), step=0, level=1),
        history=[],
    )
    monkeypatch.setattr(
        "inference.agent.tool_agent._LOCAL_ANALYZER_MAX_NO_TOOL_RESPONSES", 2
    )
    agent = ToolAgent(
        model="fixture-model",
        provider="openai",
        base_url="https://fixture.invalid/v1",
        api_key="fixture",
        virelai_gates_enabled=True,
    )
    tool = [{
        "type": "function",
        "function": {
            "name": "python",
            "description": "fixture",
            "parameters": {"type": "object", "properties": {}},
        },
    }]
    monkeypatch.setattr(agent, "_ensure_session", lambda _path: None)
    monkeypatch.setattr(agent, "_tools", lambda _path: tool)
    monkeypatch.setattr(agent, "_automatic_virelai_update", lambda *args, **kwargs: "")
    monkeypatch.setattr(agent, "_controller_focus_update", lambda: "")
    monkeypatch.setattr(agent, "_gate_context_update", lambda _path: "")
    monkeypatch.setattr(agent, "_build_user_prompt", lambda *args, **kwargs: "probe")
    monkeypatch.setattr(
        agent,
        "_build_user_message",
        lambda prompt, _frame: {"role": "user", "content": prompt},
    )
    requests = []

    def prose_only(messages, **_kwargs):
        requests.append(messages)
        return _ChatCompletionResult(
            message={"role": "assistant", "content": "```python\nresult = 2 + 2\n```"},
            finish_reason="stop",
            model_id="fixture-model",
            routed_provider="incompatible-provider",
        )

    monkeypatch.setattr(agent, "_chat_completion", prose_only)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION6"])

    assert result is not None
    assert result.step_executed is False
    assert result.fatal_failure.startswith("provider_tool_call_incompatible:")
    assert len(requests) == 2
    assert "provider_tool_call_incompatible" in (
        tmp_path / "tool_runtime_state_analyzer.txt"
    ).read_text(encoding="utf-8")

from inference.agent.runtime_state import Frame, write_runtime_state
import json
from types import SimpleNamespace

from inference.agent.tool_agent import (
    AnalyzerTurnResult,
    ToolAgent,
    _ChatCompletionResult,
    _ToolDispatchResult,
)
from inference.framework.solver import _turn_ends_game


class _Ledger:
    def request(self, _usage):
        return None

    def query(self, _operation):
        return None


def _tool_call(code: str, index: int) -> _ChatCompletionResult:
    return _ChatCompletionResult(
        message={
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": f"call-{index}",
                "type": "function",
                "function": {
                    "name": "python",
                    "arguments": json.dumps({"code": code}),
                },
            }],
        },
        finish_reason="tool_calls",
        model_id="fixture-model",
    )


def _guard_agent(tmp_path, monkeypatch, codes):
    state_path = tmp_path / "tool_runtime_state.json"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 0), (0, 0)), step=0, level=1),
        history=[],
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
    monkeypatch.setattr(agent, "_controller_no_legal_move", lambda _path: "")
    monkeypatch.setattr(agent, "_begin_turn_ledger", lambda *args, **kwargs: _Ledger())
    monkeypatch.setattr(
        agent,
        "_finish_turn_ledger",
        lambda *args, **kwargs: setattr(agent, "_turn_ledger", None),
    )
    requests = []

    def scripted(messages, **_kwargs):
        requests.append(messages)
        index = len(requests) - 1
        return _tool_call(codes[min(index, len(codes) - 1)], index)

    monkeypatch.setattr(agent, "_chat_completion", scripted)
    return agent, state_path, requests


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


def test_identical_read_only_calls_get_one_correction_then_controlled_stop(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    agent, state_path, requests = _guard_agent(tmp_path, monkeypatch, [inspect])
    monkeypatch.setattr(
        agent,
        "_dispatch_tool",
        lambda *_args, **_kwargs: _ToolDispatchResult('{"returncode": 0}'),
    )

    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and not result.step_executed
    assert result.controlled_stop.startswith("no_progress_tool_loop:")
    assert len(requests) == 3
    correction_messages = [
        message["content"]
        for message in requests[-1]
        if message.get("role") == "user" and "NO-PROGRESS TOOL GUARD" in message.get("content", "")
    ]
    assert correction_messages


def test_real_action_after_duplicate_correction_resets_guard(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    act = "action([{'action': 'ACTION1'}])"
    agent, state_path, requests = _guard_agent(tmp_path, monkeypatch, [inspect, inspect, act])

    def dispatch(_path, _name, arguments):
        return _ToolDispatchResult(
            '{"returncode": 0}',
            step_executed="action(" in arguments.get("code", ""),
        )

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and result.step_executed
    assert result.controlled_stop == ""
    assert len(requests) == 3
    assert agent._read_only_calls_without_progress == 0
    assert agent._no_progress_correction_issued is False


def test_later_action_in_same_multi_tool_response_is_not_skipped(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    act = "action([{'action': 'ACTION1'}])"
    agent, state_path, requests = _guard_agent(tmp_path, monkeypatch, [inspect])

    def scripted(messages, **_kwargs):
        requests.append(messages)
        if len(requests) == 1:
            return _tool_call(inspect, 0)
        return _ChatCompletionResult(
            message={
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "python",
                            "arguments": json.dumps({"code": inspect}),
                        },
                    },
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {
                            "name": "python",
                            "arguments": json.dumps({"code": act}),
                        },
                    },
                ],
            },
            finish_reason="tool_calls",
            model_id="fixture-model",
        )

    def dispatch(_path, _name, arguments):
        return _ToolDispatchResult(
            '{"returncode": 0}',
            step_executed="action(" in arguments.get("code", ""),
        )

    monkeypatch.setattr(agent, "_chat_completion", scripted)
    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and result.step_executed
    assert result.controlled_stop == ""
    assert len(requests) == 2
    assert agent._no_progress_correction_issued is False


def test_duplicate_guard_persists_across_turn_boundaries(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    agent, state_path, requests = _guard_agent(tmp_path, monkeypatch, [inspect])
    agent._tool_steps = 1
    monkeypatch.setattr(
        agent,
        "_dispatch_tool",
        lambda *_args, **_kwargs: _ToolDispatchResult('{"returncode": 0}'),
    )

    first = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    second = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    third = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert first is not None and first.controlled_stop == ""
    assert second is not None and second.controlled_stop == ""
    assert third is not None and third.controlled_stop.startswith("no_progress_tool_loop:")
    assert len(requests) == 3


def test_gate_transition_after_duplicate_correction_resets_guard(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    answer = "print(virelai('gate_answer', answer={}))"
    agent, state_path, _requests = _guard_agent(tmp_path, monkeypatch, [inspect, inspect, answer])

    def dispatch(_path, _name, arguments):
        if "gate_answer" in arguments.get("code", ""):
            agent._gate_transitioned_this_turn = True
        return _ToolDispatchResult('{"returncode": 0}')

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and result.controlled_stop == ""
    assert result.yielded_control
    assert agent._read_only_calls_without_progress == 0


def test_rejected_gate_answer_gets_binding_repair_turn_then_can_transition(tmp_path, monkeypatch):
    answer = "print(virelai('gate_answer', answer={}))"
    agent, state_path, requests = _guard_agent(tmp_path, monkeypatch, [answer, answer])
    calls = 0

    def dispatch(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _ToolDispatchResult(
                '{"error": "bad evidence"}',
                interaction_kind="CONTRACT_REPAIR",
                repair_signature="failure-a",
                repair_error="bad evidence",
            )
        agent._gate_transitioned_this_turn = True
        return _ToolDispatchResult(
            '{"error": null}', interaction_kind="GATE_TRANSITION"
        )

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and result.controlled_stop == ""
    assert result.yielded_control
    assert len(requests) == 2
    assert any(
        "GATE CONTRACT REPAIR" in message.get("content", "")
        for message in requests[-1]
        if message.get("role") == "user"
    )


def test_same_contract_failure_twice_stops_cleanly(tmp_path, monkeypatch):
    answer = "print(virelai('gate_answer', answer={}))"
    agent, state_path, _requests = _guard_agent(tmp_path, monkeypatch, [answer])
    rejected = _ToolDispatchResult(
        '{"error": "bad evidence"}',
        interaction_kind="CONTRACT_REPAIR",
        repair_signature="failure-a",
        repair_error="bad evidence",
    )
    monkeypatch.setattr(agent, "_dispatch_tool", lambda *_args, **_kwargs: rejected)

    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None
    assert result.controlled_stop.startswith("contract_repair_loop:")


def test_inspection_during_contract_repair_stops_cleanly(tmp_path, monkeypatch):
    answer = "print(virelai('gate_answer', answer={}))"
    inspect = "print(current_frame.step)"
    agent, state_path, _requests = _guard_agent(tmp_path, monkeypatch, [answer, inspect])
    calls = 0

    def dispatch(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _ToolDispatchResult(
                '{"error": "bad evidence"}',
                interaction_kind="CONTRACT_REPAIR",
                repair_signature="failure-a",
                repair_error="bad evidence",
            )
        return _ToolDispatchResult('{"returncode": 0}')

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None
    assert result.controlled_stop.startswith("contract_repair_loop:")


def test_contract_attempt_supersedes_existing_no_progress_warning(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    answer = "print(virelai('gate_answer', answer={}))"
    agent, state_path, _requests = _guard_agent(
        tmp_path, monkeypatch, [inspect, inspect, answer, answer]
    )
    calls = 0

    def dispatch(_path, _name, arguments):
        nonlocal calls
        calls += 1
        code = arguments.get("code", "")
        if "gate_answer" not in code:
            return _ToolDispatchResult('{"returncode": 0}')
        if calls == 3:
            return _ToolDispatchResult(
                '{"error": "bad evidence"}',
                interaction_kind="CONTRACT_REPAIR",
                repair_signature="failure-a",
                repair_error="bad evidence",
            )
        agent._gate_transitioned_this_turn = True
        return _ToolDispatchResult(
            '{"error": null}', interaction_kind="GATE_TRANSITION"
        )

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])

    assert result is not None and result.controlled_stop == ""
    assert result.yielded_control
    assert calls == 4


def test_world_step_change_clears_cross_turn_duplicate_state(tmp_path, monkeypatch):
    inspect = "print(current_frame.step)"
    agent, state_path, _requests = _guard_agent(tmp_path, monkeypatch, [inspect])
    agent._sync_no_progress_tool_guard(state_path)
    fingerprint = agent._tool_call_fingerprint("python", {"code": inspect})
    assert agent._record_read_only_tool_call(fingerprint) is None

    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 0), (0, 0)), step=1, level=1),
        history=[],
    )
    agent._sync_no_progress_tool_guard(state_path)

    assert agent._record_read_only_tool_call(fingerprint) is None
    assert agent._duplicate_read_only_count == 1
    assert agent._read_only_calls_without_progress == 1


def test_no_progress_guard_ends_harness_cleanly_with_diagnostic():
    run = SimpleNamespace(solver_note=None)
    result = AnalyzerTurnResult(
        step_executed=False,
        controlled_stop="no_progress_tool_loop: repeated read-only call",
    )

    assert _turn_ends_game(result, run)
    assert run.solver_note == "controlled_stop: no_progress_tool_loop: repeated read-only call"

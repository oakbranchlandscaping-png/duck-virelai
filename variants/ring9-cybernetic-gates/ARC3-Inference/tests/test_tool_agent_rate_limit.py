import json

import requests

from inference.agent.tool_agent import (
    AnalyzerRequestTooLarge,
    ToolAgent,
    _rate_limit_retry_delay,
)


def _response(status: int, payload: dict, *, retry_after: str = "") -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    if retry_after:
        response.headers["Retry-After"] = retry_after
    return response


def test_rate_limit_delay_reads_openai_message_and_adds_safety_margin():
    response = _response(
        429,
        {"error": {"message": "Please try again in 414ms."}},
    )
    assert _rate_limit_retry_delay(response) == 1.414


def test_chat_completion_retries_429_inside_same_tool_turn(monkeypatch):
    responses = iter(
        [
            _response(
                429,
                {"error": {"message": "Please try again in 19.024s."}},
            ),
            _response(
                200,
                {
                    "choices": [
                        {"message": {"role": "assistant", "content": "ready"}, "finish_reason": "stop"}
                    ],
                    "usage": {"total_tokens": 12},
                },
            ),
        ]
    )
    sleeps: list[float] = []
    monkeypatch.setattr("inference.agent.tool_agent.requests.post", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr("inference.agent.tool_agent.time.sleep", sleeps.append)

    agent = ToolAgent(
        model="gpt-4o",
        provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="fixture",
    )
    result = agent._chat_completion(
        [{"role": "user", "content": "probe"}],
        tools=None,
    )

    assert result.message["content"] == "ready"
    assert sleeps == [20.024]


def test_chat_completion_does_not_retry_individually_oversized_request(monkeypatch):
    response = _response(
        429,
        {
            "error": {
                "message": (
                    "Request too large for gpt-4o. The input or output tokens "
                    "must be reduced in order to run successfully."
                )
            }
        },
    )
    calls = []
    sleeps = []
    monkeypatch.setattr(
        "inference.agent.tool_agent.requests.post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or response,
    )
    monkeypatch.setattr("inference.agent.tool_agent.time.sleep", sleeps.append)
    agent = ToolAgent(
        model="gpt-4o",
        provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="fixture",
    )

    try:
        agent._chat_completion([{"role": "user", "content": "probe"}], tools=None)
    except AnalyzerRequestTooLarge:
        pass
    else:
        raise AssertionError("oversized request should fail immediately")

    assert len(calls) == 1
    assert sleeps == []


def test_openrouter_request_and_response_bind_serving_identity(monkeypatch):
    response = _response(
        200,
        {
            "id": "gen-fixture",
            "model": "qwen/qwen3.6-27b",
            "provider": "DeepInfra",
            "choices": [
                {"message": {"role": "assistant", "content": "ready"}, "finish_reason": "stop"}
            ],
            "usage": {"total_tokens": 12},
        },
    )
    calls = []
    monkeypatch.setattr(
        "inference.agent.tool_agent.requests.post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or response,
    )
    monkeypatch.setattr("inference.agent.tool_agent._OPENROUTER_REASONING_EFFORT", "medium")
    monkeypatch.setattr("inference.agent.tool_agent._OPENROUTER_PROVIDER_ONLY", ["deepinfra"])
    monkeypatch.setattr("inference.agent.tool_agent._OPENROUTER_QUANTIZATIONS", ["fp8"])
    monkeypatch.setattr("inference.agent.tool_agent._OPENROUTER_ALLOW_FALLBACKS", False)

    agent = ToolAgent(
        model="qwen/qwen3.6-27b",
        provider="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key="fixture",
    )
    result = agent._chat_completion(
        [{"role": "user", "content": "probe"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "python",
                "description": "fixture",
                "parameters": {"type": "object", "properties": {}},
            },
        }],
    )

    request_payload = calls[0][1]["json"]
    assert request_payload["reasoning"] == {"effort": "medium"}
    assert request_payload["include_reasoning"] is True
    assert request_payload["provider"] == {
        "allow_fallbacks": False,
        "require_parameters": True,
        "only": ["deepinfra"],
        "quantizations": ["fp8"],
    }
    assert result.model_id == "qwen/qwen3.6-27b"
    assert result.routed_provider == "DeepInfra"
    assert result.response_id == "gen-fixture"


def test_semantic_checkpoint_request_overrides_disable_thinking_and_require_tool(monkeypatch):
    response = _response(
        200,
        {
            "choices": [{
                "message": {"role": "assistant", "content": "ready"},
                "finish_reason": "stop",
            }],
            "usage": {"total_tokens": 12},
        },
    )
    calls = []
    monkeypatch.setattr(
        "inference.agent.tool_agent.requests.post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or response,
    )
    agent = ToolAgent(
        model="fixture-model", provider="vllm",
        base_url="http://127.0.0.1:8000/v1", api_key="fixture",
    )
    agent._chat_completion(
        [{"role": "user", "content": "answer the certified checkpoint"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "python", "description": "fixture",
                "parameters": {"type": "object", "properties": {}},
            },
        }],
        tool_choice_override="required",
        max_output_tokens_override=256,
        thinking_override=False,
    )

    payload = calls[0][1]["json"]
    assert payload["tool_choice"] == "required"
    assert payload["max_tokens"] == 256
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}

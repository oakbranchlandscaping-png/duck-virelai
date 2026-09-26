from inference.utils.openai_compat import build_chat_payload, normalize_provider


def test_openai_provider_omits_vllm_only_request_fields():
    payload = build_chat_payload(
        provider="openai",
        model="gpt-4o",
        messages=[{"role": "user", "content": "probe"}],
        max_tokens=128,
        temperature=0.2,
        top_p=0.9,
        top_k=20,
        thinking=True,
    )
    assert normalize_provider("openai") == "openai"
    assert "top_k" not in payload
    assert "chat_template_kwargs" not in payload


def test_openai_compatible_alias_retains_local_vllm_fields():
    payload = build_chat_payload(
        provider="openai-compatible",
        model="local-model",
        messages=[{"role": "user", "content": "probe"}],
        max_tokens=128,
        temperature=0.2,
        top_p=0.9,
        top_k=20,
        thinking=True,
    )
    assert normalize_provider("openai-compatible") == "vllm"
    assert payload["top_k"] == 20
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}


def test_openrouter_payload_binds_reasoning_sampling_and_provider_route():
    route = {
        "only": ["deepinfra"],
        "quantizations": ["fp8"],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    payload = build_chat_payload(
        provider="openrouter",
        model="qwen/qwen3.6-27b",
        messages=[{"role": "user", "content": "probe"}],
        max_tokens=2048,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        thinking=True,
        reasoning_effort="medium",
        provider_preferences=route,
        seed=7,
    )
    assert payload["reasoning"] == {"effort": "medium"}
    assert payload["include_reasoning"] is True
    assert payload["top_k"] == 20
    assert payload["seed"] == 7
    assert payload["provider"] == route


def test_openrouter_can_explicitly_disable_reasoning():
    payload = build_chat_payload(
        provider="openrouter",
        model="qwen/qwen3.6-35b-a3b",
        messages=[{"role": "user", "content": "probe"}],
        max_tokens=128,
        temperature=0.2,
        top_p=0.9,
        top_k=0,
        thinking=False,
    )
    assert payload["reasoning"] == {"enabled": False}
    assert "include_reasoning" not in payload

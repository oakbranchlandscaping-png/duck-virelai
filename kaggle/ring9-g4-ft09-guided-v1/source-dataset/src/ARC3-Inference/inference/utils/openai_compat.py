"""Helpers for provider-specific OpenAI-compatible requests."""
from __future__ import annotations

from typing import Any


def normalize_provider(value: str | None) -> str:
    provider = str(value or "").strip().lower()
    if provider in {"", "vllm", "openai-compatible", "compat"}:
        return "vllm"
    if provider == "openai":
        return "openai"
    if provider in {"openrouter", "router"}:
        return "openrouter"
    return provider


def build_headers(
    *,
    provider: str,
    api_key: str,
    referer: str = "",
    title: str = "",
) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    normalized = normalize_provider(provider)
    if normalized == "openrouter":
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
    return headers


def build_chat_payload(
    *,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int | None,
    temperature: float,
    top_p: float,
    top_k: int,
    thinking: bool,
    reasoning_effort: str = "",
    provider_preferences: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "top_p": top_p,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if tools:
        payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

    normalized = normalize_provider(provider)
    if normalized == "vllm":
        if top_k > 0:
            payload["top_k"] = top_k
        payload["chat_template_kwargs"] = {"enable_thinking": bool(thinking)}
        if seed is not None and seed >= 0:
            payload["seed"] = seed
    elif normalized == "openrouter":
        if top_k > 0:
            payload["top_k"] = top_k
        effort = str(reasoning_effort or "").strip().lower()
        if thinking:
            payload["reasoning"] = {"effort": effort} if effort else {"enabled": True}
            payload["include_reasoning"] = True
        else:
            payload["reasoning"] = {"enabled": False}
        if seed is not None and seed >= 0:
            payload["seed"] = seed
        if provider_preferences:
            payload["provider"] = dict(provider_preferences)

    return payload

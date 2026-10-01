#!/usr/bin/env python3
"""Verify native Python tool calling and tool-result visibility before a live run."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def _set(name: str, value: Any) -> None:
    if value is None or value == "":
        return
    if isinstance(value, bool):
        value = "true" if value else "false"
    os.environ[name] = str(value)


def _load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    shared = config.get("shared") or {}
    analyzer = config.get("analyzer") or {}
    router = analyzer.get("openrouter") or {}
    _set("LOCAL_ANALYZER_MODEL_ID", analyzer.get("model_id") or shared.get("model_name"))
    _set("LOCAL_ANALYZER_BASE_URL", analyzer.get("base_url") or shared.get("base_url"))
    _set("LOCAL_ANALYZER_PROVIDER", analyzer.get("provider") or shared.get("provider"))
    _set("LOCAL_ANALYZER_MAX_OUTPUT", analyzer.get("max_output", 512))
    _set("LOCAL_ANALYZER_TIMEOUT", analyzer.get("timeout", 180))
    _set("LOCAL_ANALYZER_ENABLE_THINKING", analyzer.get("thinking", True))
    _set("OPENROUTER_REASONING_EFFORT", router.get("reasoning_effort"))
    _set("OPENROUTER_PROVIDER_ORDER", router.get("provider_order"))
    _set("OPENROUTER_PROVIDER_ONLY", router.get("provider_only"))
    _set("OPENROUTER_QUANTIZATIONS", router.get("quantizations"))
    _set("OPENROUTER_PROVIDER_SORT", router.get("provider_sort"))
    _set("OPENROUTER_ALLOW_FALLBACKS", router.get("allow_fallbacks", False))
    _set("OPENROUTER_REQUIRE_PARAMETERS", router.get("require_parameters", True))
    return config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env.example")
    load_dotenv(ROOT / ".env", override=True)
    config = _load_config(args.config.resolve())

    # Import after environment setup because the production client snapshots its
    # request settings at module import time.
    from inference.agent.tool_agent import ToolAgent

    shared = config.get("shared") or {}
    analyzer = config.get("analyzer") or {}
    agent = ToolAgent(
        model=str(analyzer.get("model_id") or shared.get("model_name") or ""),
        provider=str(analyzer.get("provider") or shared.get("provider") or "openrouter"),
        base_url=str(analyzer.get("base_url") or shared.get("base_url") or "https://openrouter.ai/api/v1"),
        timeout=float(analyzer.get("timeout", 180)),
    )
    tools = [{
        "type": "function",
        "function": {
            "name": "python",
            "description": "Run a tiny compatibility canary and return its result.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    }]
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                "Compatibility canary. Call the python tool now with code that computes 2 + 2. "
                "Do not write Python in prose and do not answer before the tool call. After the "
                "tool result arrives, repeat its exact CANARY_RESULT=<value> marker in assistant text."
            ),
        }
    ]
    first = agent._chat_completion(messages, tools=tools)
    calls = first.message.get("tool_calls") or []
    if not calls:
        print(json.dumps({
            "ok": False,
            "stage": "native_tool_call",
            "finish_reason": first.finish_reason,
            "routed_provider": first.routed_provider,
            "model": first.model_id,
        }, indent=2))
        return 2
    call = calls[0]
    function = call.get("function") or {}
    if function.get("name") != "python":
        print(json.dumps({"ok": False, "stage": "wrong_tool", "tool": function.get("name")}, indent=2))
        return 3
    try:
        arguments = json.loads(function.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {}
    if not str(arguments.get("code") or "").strip():
        print(json.dumps({"ok": False, "stage": "python_arguments"}, indent=2))
        return 4

    assistant = dict(first.message)
    assistant.setdefault("role", "assistant")
    messages.extend([
        assistant,
        {
            "role": "tool",
            "tool_call_id": str(call.get("id") or "canary-call"),
            "content": "CANARY_RESULT=4",
        },
    ])
    second = agent._chat_completion(messages, tools=tools)
    content = str(second.message.get("content") or "")
    ok = "CANARY_RESULT=4" in content
    print(json.dumps({
        "ok": ok,
        "stage": "complete" if ok else "tool_result_visibility",
        "native_tool_call": True,
        "tool_result_visible": ok,
        "finish_reason": second.finish_reason,
        "routed_provider": second.routed_provider or first.routed_provider,
        "model": second.model_id or first.model_id,
        "returned_text": content[:200],
        "returned_tool_calls": len(second.message.get("tool_calls") or []),
    }, indent=2))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())

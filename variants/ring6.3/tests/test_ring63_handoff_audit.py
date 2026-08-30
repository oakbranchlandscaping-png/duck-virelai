"""Dependency-free executable contract for Ring 6.3's request boundary."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ARC_ROOT = HERE.parent / "ARC3-Inference"
HELPER = ARC_ROOT / "inference" / "framework" / "virelai_handoff_v63.py"


def _load_helper():
    spec = importlib.util.spec_from_file_location("ring63_handoff", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_tool_agent():
    # Pillow is a Kaggle runtime dependency but not installed in the local
    # review Python.  ToolAgent's transport path does not use it; provide only
    # the import surface required by vision_context.
    if "PIL" not in sys.modules:
        pillow = types.ModuleType("PIL")
        pillow.Image = object()
        sys.modules["PIL"] = pillow
    sys.path.insert(0, str(ARC_ROOT))
    import inference.agent.tool_agent as tool_agent
    return tool_agent


def test_exact_unicode_fingerprint_uses_utf8_without_normalization():
    helper = _load_helper()
    report = "=== CAPTAIN — α ===\nstate: café"
    fingerprint = helper.fingerprint_text(report)
    assert fingerprint.characters == len(report)
    assert fingerprint.utf8_bytes == len(report.encode("utf-8"))
    assert len(fingerprint.sha256) == 64
    assert helper.fingerprint_text(report) == fingerprint
    assert helper.fingerprint_text(report + "\n") != fingerprint


def test_multimodal_payload_finds_exact_user_report_and_ignores_image_data():
    helper = _load_helper()
    report = "=== CAPTAIN PROBE REPORT — TEST ===\nexact\n=== END CAPTAIN PROBE REPORT ==="
    payload = {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": [
                {"type": "text", "text": f"prefix\n{report}\nsuffix"},
                {"type": "image_url", "image_url": {"url": report}},
            ]},
        ]
    }
    locations = helper.payload_report_locations(payload, report)
    assert len(locations) == 1
    assert locations[0].role == "user"
    assert locations[0].message_index == 1
    assert locations[0].text_block_index == 0


def test_zero_and_duplicate_report_occurrences_are_distinguishable():
    helper = _load_helper()
    report = "REPORT"
    assert helper.payload_report_locations({"messages": []}, report) == []
    locations = helper.payload_report_locations(
        {"messages": [{"role": "user", "content": f"{report}\n{report}"}]},
        report,
        roles={"user"},
    )
    assert len(locations) == 2


def test_history_containment_checks_retained_user_messages_only():
    helper = _load_helper()
    report = "EXACT REPORT"
    assert not helper.history_contains_report(
        [{"role": "assistant", "content": report}], report
    )
    assert helper.history_contains_report(
        [{"role": "user", "content": [{"type": "text", "text": report}]}],
        report,
    )


def test_nonzero_global_action_prompt_appends_report_verbatim_once():
    tool_agent = _load_tool_agent()
    agent = tool_agent.ToolAgent.__new__(tool_agent.ToolAgent)
    agent._summarized_knowledge = tool_agent._empty_world_model()
    report = "=== CAPTAIN PROBE REPORT — TEST ===\nline one\nline two\n=== END CAPTAIN PROBE REPORT ==="
    prompt = agent._build_user_prompt(
        47,
        valid_actions=["ACTION1"],
        virelai_card=report,
    )
    assert prompt.count(report) == 1
    assert report in prompt


class _FakeResponse:
    status_code = 200
    text = ""

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 10},
        }


def _bare_transport_agent(tool_agent):
    agent = tool_agent.ToolAgent.__new__(tool_agent.ToolAgent)
    agent._model = tool_agent.AnalyzerModelConfig(
        provider="vllm", base_url="http://127.0.0.1:1/v1", model_id="test-model"
    )
    agent._max_output_tokens = 64
    agent._timeout = 1.0
    agent._api_key = ""
    return agent


def test_observer_sees_final_provider_payload_immediately_before_post():
    tool_agent = _load_tool_agent()
    agent = _bare_transport_agent(tool_agent)
    report = "EXACT CAPTAIN REPORT"
    messages = [{"role": "user", "content": report}]
    order = []
    observed = []
    posted = []

    def observer(event, record):
        order.append(event)
        observed.append(record)
        if event == "prepared":
            # Mutating the detached observer record must not mutate the real
            # payload passed to requests.post.
            record["provider_payload"]["messages"][0]["content"] = "MUTATED"

    def fake_post(*args, **kwargs):
        order.append("post")
        posted.append(kwargs["json"])
        return _FakeResponse()

    with patch.object(tool_agent.requests, "post", fake_post):
        result = agent._chat_completion(
            messages,
            tools=[],
            request_observer=observer,
            request_context={"request_id": "a1-i1-r1"},
        )

    assert order == ["prepared", "post", "completed"]
    assert observed[0]["provider_payload"]["messages"][0]["content"] == "MUTATED"
    assert posted[0]["messages"][0]["content"] == report
    assert result.message["content"] == "ok"


def test_observer_failure_is_fail_open_for_model_request():
    tool_agent = _load_tool_agent()
    agent = _bare_transport_agent(tool_agent)
    posted = []

    def broken_observer(event, record):
        raise RuntimeError("audit unavailable")

    def fake_post(*args, **kwargs):
        posted.append(kwargs["json"])
        return _FakeResponse()

    with patch.object(tool_agent.requests, "post", fake_post):
        result = agent._chat_completion(
            [{"role": "user", "content": "report"}],
            tools=[],
            request_observer=broken_observer,
            request_context={"request_id": "a1-i1-r1"},
        )

    assert len(posted) == 1
    assert result.message["content"] == "ok"


def _runtime_state(tool_agent, directory: str) -> Path:
    from inference.agent.runtime_state import (
        Frame,
        HistoryEntry,
        write_runtime_state,
    )

    path = Path(directory) / "artifacts" / "game_p0_tool_runtime_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(grid=((0,),), step=41, level=1)
    write_runtime_state(
        path,
        current_frame=frame,
        history=[HistoryEntry(action="", frame=frame)],
    )
    return path


def test_retained_yield_style_history_prevents_fresh_duplicate():
    tool_agent = _load_tool_agent()
    helper = _load_helper()
    agent = tool_agent.ToolAgent(
        model="test-model",
        base_url="http://127.0.0.1:1/v1",
        provider="vllm",
    )
    agent._tool_steps = 1
    report = "=== UNIQUE RING63 REPORT ===\nworld evidence\n=== END UNIQUE RING63 ==="
    prepared = []

    def observer(event, record):
        if event == "prepared":
            prepared.append(record["provider_payload"])

    with tempfile.TemporaryDirectory() as directory:
        state_path = _runtime_state(tool_agent, directory)
        with patch.object(tool_agent.requests, "post", lambda *args, **kwargs: _FakeResponse()):
            # A completed no-action invocation preserves its card-bearing user
            # message, the same history shape that matters when a turn yields.
            agent.analyze(
                state_path,
                41,
                valid_actions=["ACTION1"],
                analysis_step=1,
                virelai_card=report,
                request_observer=observer,
            )
            agent.analyze(
                state_path,
                41,
                valid_actions=["ACTION1"],
                analysis_step=1,
                virelai_card=report,
                request_observer=observer,
            )

    assert len(prepared) == 2
    assert [
        len(helper.payload_report_locations(payload, report, roles={"user"}))
        for payload in prepared
    ] == [1, 1]


def test_request_failure_restores_history_and_retry_reoffers_one_report():
    tool_agent = _load_tool_agent()
    helper = _load_helper()
    agent = tool_agent.ToolAgent(
        model="test-model",
        base_url="http://127.0.0.1:1/v1",
        provider="vllm",
    )
    agent._tool_steps = 1
    report = "=== UNIQUE RETRY REPORT ===\nretry evidence\n=== END UNIQUE RETRY ==="
    prepared = []

    def observer(event, record):
        if event == "prepared":
            prepared.append(record["provider_payload"])

    with tempfile.TemporaryDirectory() as directory:
        state_path = _runtime_state(tool_agent, directory)
        with patch.object(
            tool_agent.requests,
            "post",
            side_effect=tool_agent.requests.RequestException("temporary failure"),
        ):
            failed = agent.analyze(
                state_path,
                41,
                valid_actions=["ACTION1"],
                analysis_step=1,
                virelai_card=report,
                request_observer=observer,
            )
        with patch.object(tool_agent.requests, "post", lambda *args, **kwargs: _FakeResponse()):
            retried = agent.analyze(
                state_path,
                41,
                valid_actions=["ACTION1"],
                analysis_step=1,
                virelai_card=report,
                request_observer=observer,
            )

    assert failed is not None and failed.retryable_failure
    assert retried is not None and not retried.retryable_failure
    assert len(prepared) == 2
    assert [
        len(helper.payload_report_locations(payload, report, roles={"user"}))
        for payload in prepared
    ] == [1, 1]


def test_context_overflow_retry_reposts_new_inspected_payload():
    tool_agent = _load_tool_agent()
    helper = _load_helper()
    agent = tool_agent.ToolAgent(
        model="test-model",
        base_url="http://127.0.0.1:1/v1",
        provider="vllm",
    )
    agent._tool_steps = 2
    report = "=== RING63 OVERFLOW REPORT ===\nevidence\n=== END RING63 OVERFLOW ==="
    events = []
    prepared = []
    posted = []
    calls = {"n": 0}

    def observer(event, record):
        events.append((event, record.get("request_id")))
        if event == "prepared":
            prepared.append(record["provider_payload"])

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        # Snapshot at post time: the harness later appends the assistant
        # reply to the same live message list.
        import json as _json
        posted.append(_json.loads(_json.dumps(kwargs["json"])))
        if calls["n"] == 1:
            raise tool_agent.requests.RequestException(
                "This model's maximum context length is 8 tokens"
            )
        return _FakeResponse()

    with tempfile.TemporaryDirectory() as directory:
        state_path = _runtime_state(tool_agent, directory)
        # Match the session so the seeded pre-existing history block survives
        # _ensure_session, giving the overflow handler something to drop.
        agent._session_runtime_dir = state_path.parent
        agent._history_messages = [
            {"role": "user", "content": "OLD HISTORY BLOCK"},
            {"role": "assistant", "content": "old reply"},
        ]
        with patch.object(tool_agent.requests, "post", fake_post):
            agent.analyze(
                state_path,
                41,
                valid_actions=["ACTION1"],
                analysis_step=1,
                virelai_card=report,
                request_observer=observer,
            )

    assert calls["n"] == 2, "server rejection must produce exactly one re-post"
    names = [name for name, _ in events]
    assert names[0] == "prepared" and names[1] == "failed"
    prepared_ids = [rid for name, rid in events if name == "prepared"]
    assert len(prepared_ids) == 2
    assert prepared_ids[0] != prepared_ids[1], "each post needs its own request id"
    for payload in prepared:
        assert len(
            helper.payload_report_locations(payload, report, roles={"user"})
        ) == 1, "the current first-turn report must survive the overflow re-trim"
    assert [p["messages"] for p in prepared] == [p["messages"] for p in posted]

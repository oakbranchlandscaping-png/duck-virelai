from __future__ import annotations

from inference.agent.runtime_state import Frame
from inference.agent.tool_agent import ToolAgent


def _text(message):
    content = message["content"]
    if isinstance(content, str):
        return content
    return "\n".join(
        part.get("text", "") for part in content if part.get("type") == "text"
    )


def test_optional_physics_tool_does_not_push_agenda_or_card_into_request():
    agent = ToolAgent(model="fixture-model", virelai_enabled=True)
    agent._virelai_query_callback = lambda operation, parameters=None: {
        "data": {"text": "AGENDA_SENTINEL"}
    }
    agent._transition_briefing_level = 2
    agent._transition_briefing_text = "MEMORY_CARD_SENTINEL"
    frame = Frame(grid=((0, 0), (0, 1)), step=8, level=2)

    prompt = agent._build_user_prompt(
        8,
        valid_actions=["LEFT"],
        current_frame=frame,
        history_entries=[],
        previous_step_summary={"level_transition": True, "level": 2},
    )
    request = agent._trim_messages_for_context(
        [
            {"role": "system", "content": agent._system_prompt},
            agent._build_user_message(prompt, frame),
        ],
        tools=None,
        preserve_recent=1,
    )

    final_user_text = _text(request[-1])
    assert "AGENDA_SENTINEL" not in final_user_text
    assert "MEMORY_CARD_SENTINEL" not in final_user_text


def test_card_is_absent_from_unrelated_level():
    agent = ToolAgent(model="fixture-model", virelai_enabled=True)
    agent._virelai_query_callback = lambda operation, parameters=None: {
        "data": {"text": "AGENDA_SENTINEL"}
    }
    agent._transition_briefing_level = 2
    agent._transition_briefing_text = "MEMORY_CARD_SENTINEL"
    frame = Frame(grid=((0,),), step=9, level=3)
    prompt = agent._build_user_prompt(
        9, valid_actions=["LEFT"], current_frame=frame, history_entries=[]
    )
    assert "MEMORY_CARD_SENTINEL" not in prompt


def test_card_remains_absent_across_analysis_only_prompts():
    agent = ToolAgent(model="fixture-model", virelai_enabled=True)
    agent._virelai_query_callback = lambda operation, parameters=None: {
        "data": {"text": "AGENDA_SENTINEL"}
    }
    agent._transition_briefing_level = 2
    agent._transition_briefing_text = "MEMORY_CARD_SENTINEL"
    frame = Frame(grid=((0, 0), (0, 1)), step=8, level=2)

    first = agent._build_user_prompt(
        8, valid_actions=["LEFT"], current_frame=frame, history_entries=[]
    )
    second = agent._build_user_prompt(
        8, valid_actions=["LEFT"], current_frame=frame, history_entries=[]
    )

    assert "MEMORY_CARD_SENTINEL" not in first
    assert "MEMORY_CARD_SENTINEL" not in second

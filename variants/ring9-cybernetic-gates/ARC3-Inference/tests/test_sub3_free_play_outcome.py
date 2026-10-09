"""SUB-3: a free-play action reports its outcome to Duck (rehearsal of ring9-submission-v1, 2026-10-08).

Author: Claude (Alpha build seat), 2026-10-09. Director: "lets do B" (SUB-3 with a 1,000-action cap).

In the rehearsal every one of 685 free-play actions ran and was recorded, but Duck was told "action
failed in sandbox host." The play gate's event had no ``outcome`` (every other gate's event has one),
``_apply_step_result`` read ``gate_event["outcome"]``, and the sandbox host hid the KeyError behind
its generic message. These tests drive the real tool path, with no stub on ``_apply_step_result``.
"""
from __future__ import annotations

import json
import logging

from inference.agent import python_tool_sandbox
from inference.agent.python_tool_sandbox import run_sandboxed_python
from inference.framework.play_gate import rest_in_play
from tests.test_gated_python_bridge import _agent, _capability

PLAY = "PLAY-NORMAL"


def _step(payload: dict) -> dict:
    return {"executed": True, "action_num": 2, "transition_id": 2, "level": 1,
            "valid_actions": ["ACTION1", "ACTION2"], "board_changed": True}


def _resting_agent(tmp_path):
    agent, state_path = _agent(tmp_path)
    _capability(agent, state_path)  # answers G0, as the ladder does before any action
    machine = agent._ensure_gate_machine(state_path)
    rest_in_play(machine, "SUB-3 test: the level rests in normal play")
    assert machine.gate_id == PLAY
    return agent, state_path, machine


def _free_play_action(agent, state_path, machine):
    token = machine.next_probe_capability()["probe_token"]
    return agent._run_python_tool(
        state_path, {"code": f"r = action(['ACTION1'], decision={{'probe_token': {token!r}}})"}
    )


def _events(tmp_path) -> list[dict]:
    return [json.loads(line) for line in (tmp_path / "gated_gate_events.jsonl").read_text().splitlines()]


def test_a_free_play_action_reports_its_outcome_to_duck(tmp_path):
    agent, state_path, machine = _resting_agent(tmp_path)
    calls: list[dict] = []
    agent._step_env_callback = lambda payload: calls.append(payload) or _step(payload)
    result = _free_play_action(agent, state_path, machine)
    assert len(calls) == 1
    assert "action failed in sandbox host" not in result.content
    assert result.step_executed  # the turn ledger and the solver now see the action
    event = _events(tmp_path)[-1]
    assert event["gate_id"] == PLAY and event["receipt"] == "FREE_PLAY"
    shown = json.loads(result.content)["result"]
    assert shown["executed"] is True
    assert shown["virelai_evidence_id"] == event["evidence_id"]


def test_the_free_play_event_keeps_the_gate_event_contract(tmp_path):
    """Every gate's event carries the fields _apply_step_result reads; free play now does too."""
    agent, state_path, machine = _resting_agent(tmp_path)
    agent._step_env_callback = _step
    _free_play_action(agent, state_path, machine)
    event = _events(tmp_path)[-1]
    assert {"evidence_id", "outcome"} <= set(event)
    assert event["outcome"]["probe_id"] == event["probe_id"]
    assert "changed_cells" not in event["outcome"]  # the prompt-facing copy is compact, as at every gate
    play = machine._adapters[PLAY]
    assert all("outcome" not in item for item in play.snapshot()["events"])  # the persisted list stays lean


def test_the_sandbox_host_logs_an_error_it_hides_from_duck(caplog):
    def failing_action(actions, decision=None):
        raise KeyError("outcome")

    def failing_query(operation, parameters):
        raise ValueError("query broke")

    with caplog.at_level(logging.WARNING, logger=python_tool_sandbox.__name__):
        result = run_sandboxed_python(
            code=(
                "try:\n    action(['ACTION1'], decision={'probe_token': 'T'})\nexcept RuntimeError as exc:\n"
                "    print(exc)\ntry:\n    virelai('gate')\nexcept RuntimeError as exc:\n    print(exc)\n"
            ),
            timeout_seconds=20,
            initial_state={},
            action_handler=failing_action,
            decision_action_handler=failing_action,
            virelai_handler=failing_query,
        )
    assert "action failed in sandbox host." in result["stdout"]  # Duck's message is unchanged
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "KeyError" in logged and "'outcome'" in logged and "test_sub3_free_play_outcome.py" in logged
    assert "ValueError" in logged and "query broke" in logged

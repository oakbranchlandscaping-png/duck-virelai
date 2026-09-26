from __future__ import annotations

import json

from inference.agent.runtime_state import Frame, write_runtime_state
from inference.agent.tool_agent import ToolAgent, _compact_transition_briefing


def _responses():
    return {
        "mechanics": {
            "data": {
                "controls": [
                    {
                        "name": "Lever A",
                        "kind": "REMOTE_LEVER",
                        "location": [1, 2, 1, 2],
                        "affected_regions": [[3, 4, 5, 6]],
                        "observations": 7,
                    }
                ]
            }
        },
        "win": {
            "data": {
                "winning_action": "MOUSE(1,2)",
                "acted_cell": [1, 2],
                "status": "MINIMAL_OBSERVED_SEPARATOR",
                "earlier_same_action_failures": 2,
                "distinguishing_conditions": [
                    {"region": [3, 4, 5, 6], "winning_pre_state": {"9": 4}}
                ],
            }
        },
        "carry": {
            "data": {
                "candidate_controls": [
                    {
                        "prior_control": "Lever A",
                        "prior_location": [1, 2, 1, 2],
                        "candidate_locations": [[8, 9, 8, 9]],
                    }
                ]
            }
        },
    }


def test_transition_briefing_is_compact_and_contains_three_evidence_views():
    briefing = _compact_transition_briefing(1, _responses())

    assert "Observed winning edge" in briefing
    assert "Observed prior-level mechanics" in briefing
    assert "Untested correspondences" in briefing
    assert len(briefing.encode()) < 3000


def test_new_level_briefing_never_blocks_duck_action(tmp_path):
    state_path = tmp_path / "state.json"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 0), (0, 1)), step=4, level=2),
        history=[],
    )
    analyzer = ToolAgent(model="fixture-model", virelai_enabled=True)
    analyzer._ensure_session(state_path)
    calls = []
    analyzer._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True,
        "action_num": 5,
        "level": 2,
        "valid_actions": ["LEFT"],
    }
    analyzer._current_valid_actions = ["LEFT"]
    analyzer._transition_briefing_level = 2
    analyzer._transition_briefing_text = _compact_transition_briefing(1, _responses())

    allowed = json.loads(
        analyzer._run_python_tool(
            state_path, {"code": "action(['LEFT'])"}
        ).content
    )
    assert len(calls) == 1
    assert '"executed": true' in json.dumps(allowed).lower()
    assert analyzer._transition_briefing_level is None

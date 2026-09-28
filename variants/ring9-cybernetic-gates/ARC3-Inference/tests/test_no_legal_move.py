"""Axiom A2: every gate state admits a legal move or declares an end.

Author: Claude (Alpha build seat), 2026-09-27.

Three live runs idled to their deadline in a gate state that offered no legal move: ls20 G2
(2026-09-22), vc33 G4.2 (2026-09-27) and ft09 G2 (2026-09-27). Director ruling 2026-09-27: every
friction sharpens an axiom (DOCTRINE_FRICTION_AXIOMS_v1). These tests pin both halves of A2: the
machine reports its legal-move status, and the runtime watchdog ends gated work as a recorded
controller failure after consecutive no-legal-move checks.
"""
from __future__ import annotations

from types import SimpleNamespace

from inference.agent import tool_agent
from inference.agent.tool_agent import ToolAgent
from test_g2_counter_axiom import _act, _answer, _decode, _load, _machine
from test_g4_guided import SYNTHETIC_LEVERS, World, _grid, toggle, absorb
from test_g4_phase1_boundary import LEVEL_UP, _act as _g4_act, _explain
from test_g4_phase1_boundary import _machine as _g4_machine
from test_g4_phase1_boundary import A, B


def _assert_legal(machine):
    status = machine.legal_move_status()
    assert status["legal"], status


def test_every_state_of_the_real_ft09_g2_replay_has_a_legal_move():
    data = _load()
    grid = _decode(data["initial_grid"])
    machine = _machine(grid)
    _assert_legal(machine)
    for step in data["steps"]:
        grid, _ = _act(machine, grid, step["transition_id"], step["action"], step["changed"])
        _assert_legal(machine)
    assert machine.legal_move_status()["move"] == "ANSWER"
    _answer(machine, action={"action": "ACTION6", "row": 10, "col": 14},
            predicate="COUNTER_SILENT", amount=0)
    assert machine.legal_move_status()["move"] == "PROBE"


def test_every_state_of_a_guided_g4a_study_has_a_legal_move():
    machine = _g4_machine(_grid(1, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle)
    _assert_legal(machine)
    for action in (A, A, A, A, B, B, B, B):
        world.press(machine, action)
        _assert_legal(machine)
    _explain(machine, "E-A")
    _assert_legal(machine)
    _explain(machine, "E-B")
    _assert_legal(machine)
    assert machine.legal_move_status()["move"] == "DECLARED_STATE"


def test_level_closed_g4_state_is_a_declared_end_not_a_deadlock():
    machine = _g4_machine(_grid(1, 1), SYNTHETIC_LEVERS)
    _g4_act(machine, B, _grid(1, 1), _grid(1, 2), 1)
    _g4_act(machine, B, _grid(1, 2), _grid(1, 7), 2, LEVEL_UP)
    status = machine.legal_move_status()
    assert status["legal"] and status["move"] == "DECLARED_STATE"
    assert status["next_operation"] == "G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9"


def test_the_ft09_deadlock_signature_is_detected(monkeypatch):
    """The 8cfb782 signature: an answer demanded while the card carries no template."""
    data = _load()
    grid = _decode(data["initial_grid"])
    machine = _machine(grid)
    for step in data["steps"]:
        grid, _ = _act(machine, grid, step["transition_id"], step["action"], step["changed"])
    monkeypatch.setattr(machine.counter, "answer_template", lambda: None)
    status = machine.legal_move_status()
    assert not status["legal"]
    assert "no answer template" in status["reason"]


def _agent_with(machine):
    agent = ToolAgent.__new__(ToolAgent)
    agent._virelai_gates_enabled = True
    agent._ensure_gate_machine = lambda state_path: machine
    return agent


def test_watchdog_ends_gated_work_after_consecutive_no_legal_move_checks():
    stuck = SimpleNamespace(legal_move_status=lambda: {
        "legal": False, "gate_id": "G2-COUNTER", "status": "ANSWER_REQUIRED",
        "next_operation": "SUBMIT_GATE_ANSWER",
        "reason": "an answer is demanded but the card supplies no answer template",
    })
    agent = _agent_with(stuck)
    results = [agent._controller_no_legal_move(None) for _ in range(tool_agent._NO_LEGAL_MOVE_LIMIT)]
    assert results[:-1] == [""] * (tool_agent._NO_LEGAL_MOVE_LIMIT - 1)
    assert results[-1].startswith("controller_no_legal_move: gate=G2-COUNTER")
    assert "Axiom A2" in results[-1]


def test_watchdog_resets_when_a_legal_move_returns():
    states = iter([False, False, True, False, False])
    machine = SimpleNamespace(legal_move_status=lambda: {
        "legal": next(states), "gate_id": "G", "status": "S", "next_operation": "O", "reason": "r",
    })
    agent = _agent_with(machine)
    assert [agent._controller_no_legal_move(None) for _ in range(5)] == [""] * 5

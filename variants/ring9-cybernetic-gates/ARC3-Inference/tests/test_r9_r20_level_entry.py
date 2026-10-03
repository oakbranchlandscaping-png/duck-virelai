"""R9-R20: level 2's G1 deadlock in ring9-carry-vc33-v2 (Kaggle, 2026-10-02).

Author: Claude (Alpha build seat), 2026-10-02. REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md.

Live: the winning click at transition 26 froze level 1 and built level 2's gate machine inside the
action's recording. The same action's artifact path then refreshed the action metadata
(``agent/gate_artifacts.py``), which settled the fresh pointer ego by coverage logic: G1 went from
ANSWER_REQUIRED to UNRESOLVED with no probe and no template (D1). The axiom-A2 watchdog called that
state legal (D2), so Duck idled 131 turns, about 3 hours, with zero level-2 actions. Offline replay
never made that refresh (D3), so R9-R17 and R9-R18's tests could not see D1.

Fixture: the v2 run's own record (its transitions equal the exit run's; Duck's prose differs).
Each test failed before R9-R20.
"""
from __future__ import annotations

from pathlib import Path

from inference.framework import record_replay
from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import EgoGateMachine

VC33_CARRY_V2 = Path(__file__).resolve().parent / "fixtures" / "vc33_kaggle_carry_v2_record.json.gz"
BOARD = [[0] * 8 for _ in range(8)]


def _level_two():
    result = replay(load_record(VC33_CARRY_V2))
    assert result.machine.lives.level == 2 and result.machine.gate_id == "G0-ACTION-METADATA"
    return result.machine


def _controller_until_action(machine):
    """The controller's turn on level 2: answers until it owns an action or hands to Duck."""
    for _ in range(4):
        step = next_owned_step(machine)
        if step.owner != "CONTROLLER" or step.kind != "ANSWER":
            return step
        machine.submit_answer(step.answer)
    raise AssertionError("the controller kept answering")


def test_a_metadata_refresh_leaves_a_fresh_pointer_ego_answerable():
    """D1: a click world's G1 closes on the G0 interface axiom; a refresh adding nothing never unsettles it."""
    ego = EgoGateMachine(valid_actions=["ACTION6"], initial_grid=BOARD, observed_through_step=26)
    assert (ego.status, ego.coverage_stop_reason) == ("ANSWER_REQUIRED", "ACTION_SURFACE_POINTER_EGO")
    ego.update_action_metadata(["ACTION6"])
    assert (ego.status, ego.coverage_stop_reason) == ("ANSWER_REQUIRED", "ACTION_SURFACE_POINTER_EGO")


def test_replay_refreshes_the_action_metadata_after_every_action_as_the_live_path_does(monkeypatch):
    """D3: replay is faithful to agent/gate_artifacts.py, which refreshes metadata after each action."""
    calls = []
    original = record_replay.CyberneticGateMachine.update_action_metadata

    def spy(self, valid_actions):
        calls.append(list(valid_actions))
        return original(self, valid_actions)

    monkeypatch.setattr(record_replay.CyberneticGateMachine, "update_action_metadata", spy)
    result = replay(load_record(VC33_CARRY_V2))
    assert result.steps_replayed == 26 and calls == [["ACTION6"]] * 26


def test_the_live_level_two_entry_reaches_g2_under_the_controller():
    """The v2 run, replayed as it ran: the controller answers G0 and G1 and takes G2's first click."""
    machine = _level_two()
    machine.update_action_metadata(["ACTION6"])  # the winning action's own refresh, as live (idempotent)
    step = _controller_until_action(machine)
    assert (step.owner, step.kind, machine.gate_id) == ("CONTROLLER", "ACTION", "G2-COUNTER"), step.reason
    assert [row["gate_id"] for row in machine.completed_gate_rows()] == ["G0-ACTION-METADATA", "G1-EGO"]


def test_waiting_for_an_action_while_admitting_none_is_not_a_legal_move():
    """D2 (axiom A2): the exact live state, built directly, is a deadlock the watchdog must see."""
    machine = _level_two()
    machine.submit_answer(next_owned_step(machine).answer)  # G0, as the controller did live
    machine.ego.status, machine.ego.coverage_stop_reason = "UNRESOLVED", "REPRESENTATION_GAP_NO_VISIBLE_EFFECT"
    view = machine.gate_view()
    assert (machine.gate_id, view["next_operation"]) == ("G1-EGO", "WAIT_FOR_REPRESENTATION_OR_NEW_ACTION")
    assert machine.next_probe_capability() is None
    status = machine.legal_move_status()
    assert status["legal"] is False and "offers no probe, answer or end" in status["reason"]  # R9-R22 D11 wording

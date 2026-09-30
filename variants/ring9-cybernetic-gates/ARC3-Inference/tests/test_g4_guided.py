"""G4-A guided lever study: a stated target that Duck executes as needed.

Author: Claude (Alpha build seat), 2026-09-27.

Director ruling, 2026-09-27: G3 stays scripted; G4 becomes stated targets. The controller states
the target and the closure test and audits the record; Duck chooses every action. These tests pin
the audit rules (what counts as a run, what confirms it, what ends it) and the regression from
FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27.md: mixed absorbing/toggle levers now
complete, because each lever's confirmation happens inside its own run.
"""
from __future__ import annotations

import pytest

from inference.framework.virelai_gates import GateContractError
from test_g4_phase1_boundary import A, B, ORBITS, SYNTHETIC_LEVERS, _act, _explain, _machine

OTHER = {"action": "ACTION6", "row": 0, "col": 0}


def _grid(a, b):
    return ((a, b), (0, 0))


class World:
    """Tiny deterministic world: lever A drives cell (0,0), lever B drives cell (0,1)."""

    def __init__(self, a_law, b_law, a=1, b=1):
        self.a, self.b = a, b
        self.laws = {"A": a_law, "B": b_law}
        self.tid = 0

    def press(self, machine, action):
        before = _grid(self.a, self.b)
        if action == A:
            self.a = self.laws["A"](self.a)
        elif action == B:
            self.b = self.laws["B"](self.b)
        self.tid += 1
        return _act(machine, action, before, _grid(self.a, self.b), self.tid)


def toggle(value):
    return 3 - value


def absorb(value):
    return min(value + 1, 3)


def _payload(machine):
    return machine.target_journal.active_product(ORBITS).payload


def test_card_states_target_and_duck_chooses_the_action():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    view = machine.gate_view()
    assert view["schema"] == "virelai-g4a-target-card-v1"
    assert "press" in view["target"].lower() and "confirm" in view["target"].lower()
    assert view["done_when"]
    assert [item["click"] for item in view["levers"]] == [A, B]
    capability = machine.next_probe_capability()
    assert capability["purpose"] == "GUIDED_ACTION"
    assert capability["actions"] == []
    assert capability["admissible_actions"] == ["ACTION6"]
    # Duck may start with either lever; the controller does not impose an order.
    world = World(toggle, toggle)
    event = world.press(machine, B)
    assert event["lever_entity_id"] == "E-B"
    assert event["run"]["run_id"] == "E-B-R1"


def test_mixed_absorbing_and_toggle_levers_both_complete_in_either_order():
    """Regression for the G4.3 continuity finding: no stale endpoint, no rejected press."""
    for order in (("A", "B"), ("B", "A")):
        machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
        world = World(absorb, toggle)
        for name in order:
            action = A if name == "A" else B
            while f"E-{name}" not in {
                item["entity_id"] for item in machine.gate_view().get("answer_templates") or ()
            }:
                world.press(machine, action)
            _explain(machine, f"E-{name}")
        payload = _payload(machine)
        assert payload["phase1_status"] == "COMPLETE", order
        assert payload["lever_classes"] == {"E-A": "ABSORBING", "E-B": "TOGGLE"}, order
        assert machine._adapters["G4.2-LEVER-ORBITS"].assess().disposition == "SATISFIED"  # the ladder then opens G4-B


def test_toggle_needs_one_full_extra_period_to_confirm():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    world = World(toggle, toggle)
    assert world.press(machine, A)["run"]["disposition"] == "NOVEL_STATE_REVEALED"
    stop = world.press(machine, A)["run"]
    assert (stop["disposition"], stop["run_status"]) == ("OBSERVED_STATE_RECURRENCE", "CONFIRMING")
    assert world.press(machine, A)["run"]["disposition"] == "RECURRENCE_STATE_MATCHED"
    done = world.press(machine, A)["run"]
    assert (done["disposition"], done["run_status"]) == ("RECURRENCE_CONFIRMED", "CONFIRMED")


def test_confirmation_that_disagrees_is_recorded_as_divergence_not_hidden():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    values = iter([1, 3])  # null, then a change on the confirming press

    def flaky(value):
        return next(values)

    world = World(flaky, toggle)
    world.press(machine, A)
    event = world.press(machine, A)
    assert event["run"]["disposition"] == "CONFIRMATION_DIVERGED"
    assert event["run"]["run_status"] == "DIVERGED"
    _explain(machine, "E-A")
    assert _payload(machine)["lever_classes"] == {"E-A": "DIVERGENT"}


def test_other_action_ends_an_unconfirmed_run_and_evidence_is_kept():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle)
    world.press(machine, A)
    event = world.press(machine, OTHER)
    assert event["lever_entity_id"] is None
    assert event["run"]["kind"] == "OTHER_ACTION"
    assert event["run"]["ended_run"] == "E-A-R1"
    detail = machine.orbit_view("E-A")
    assert detail["status"] == "RUN_ENDED_RESTART_NEEDED"
    assert detail["runs"][0]["status"] == "BROKEN"
    assert len(detail["runs"][0]["orbit"]["steps"]) == 1
    # A fresh run starts from the current board.
    assert world.press(machine, A)["run"]["run_id"] == "E-A-R2"


def test_switching_levers_mid_run_ends_the_first_run():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle)
    world.press(machine, A)
    event = world.press(machine, B)
    assert event["run"]["ended_run"] == "E-A-R1"
    assert machine.orbit_view("E-A")["runs"][0]["status"] == "BROKEN"


def test_board_change_between_presses_starts_a_new_run_instead_of_raising():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    _act(machine, A, _grid(1, 1), _grid(2, 1), 1)
    # Something outside Duck's action changed the board (for example a system reset).
    event = _act(machine, A, _grid(1, 1), _grid(2, 1), 2)
    assert event["run"]["ended_run"] == "E-A-R1"
    assert event["run"]["run_id"] == "E-A-R2"


def test_explanation_before_confirmation_is_refused_with_the_reason():
    machine = _machine(_grid(1, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle)
    world.press(machine, A)
    with pytest.raises(GateContractError, match="no confirmed run"):
        machine.submit_answer({"entity_id": "E-A"})


def test_presses_after_confirmation_do_not_rewrite_the_confirmed_run():
    machine = _machine(_grid(3, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle, a=3)
    world.press(machine, A)
    world.press(machine, A)
    extra = world.press(machine, A)
    assert extra["run"]["kind"] == "PRESS_AFTER_CONFIRMED_RUN"
    detail = machine.orbit_view("E-A")
    assert len(detail["runs"]) == 1
    assert detail["runs"][0]["status"] == "CONFIRMED"


def test_answers_can_be_given_in_any_order_and_gate_waits_for_them():
    machine = _machine(_grid(3, 1), SYNTHETIC_LEVERS)
    world = World(absorb, toggle, a=3)
    world.press(machine, A)
    world.press(machine, A)
    world.press(machine, B)
    world.press(machine, B)
    world.press(machine, B)
    world.press(machine, B)
    view = machine.gate_view()
    assert view["status"] == "ANSWER_REQUIRED"
    assert view["next_operation"] == "SUBMIT_GATE_ANSWER"
    assert machine.next_probe_capability() is None
    _explain(machine, "E-B")
    _explain(machine, "E-A")
    assert _payload(machine)["lever_entities"] == ["E-A", "E-B"]
    assert machine._adapters["G4.2-LEVER-ORBITS"].assess().disposition == "SATISFIED"  # the ladder then opens G4-B

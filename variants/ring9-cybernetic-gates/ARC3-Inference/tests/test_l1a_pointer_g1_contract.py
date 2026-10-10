"""WO-L1a: the click-only (pointer) G1 contract (EXECUTION_PLAN_SEMANTIC_LIBRARY_v1 §3, §5).

Author: Claude (Alpha build seat), 2026-10-10. Rulings 6, 15 and 21 (RULINGS_CONSOLIDATION_v2/v3).

In the v1 and v2 rehearsals, click-only worlds that also offer non-coordinate actions stopped at G1
before any action. G1's pointer answer template wrote an ``action_laws`` entry for every available
action ("selects the supplied grid coordinate"), while ``submit_answer`` and
``ego_law_from_interface`` accept exactly ``{"ACTION6"}``. The controller submitted the template, G1
refused it, Duck copied it, and the contract loop ended the study at 0 actions.

The interface axiom explains ACTION6 only. Other actions are recorded as open obligations for later
gates, never given a coordinate meaning.
"""
from __future__ import annotations

import pytest

from inference.framework.controller_executor import ANSWER, CONTROLLER, controller_answer, next_owned_step
from inference.framework.virelai_gates import CyberneticGateMachine

GRID = (
    (7, 7, 7, 7, 0, 0),
    (0, 0, 0, 0, 0, 0),
    (0, 2, 2, 0, 3, 0),
    (0, 0, 0, 0, 0, 0),
)
CLICK_SURFACES = (
    ("ACTION6",),
    ("ACTION6", "ACTION7"),
    ("ACTION5", "ACTION6", "ACTION7"),
)


def _at_g1(actions: tuple[str, ...]) -> CyberneticGateMachine:
    machine = CyberneticGateMachine(valid_actions=list(actions), initial_grid=GRID)
    answer, _ = controller_answer(machine, machine.gate_view())
    machine.submit_answer(answer)
    assert machine.gate_id == "G1-EGO"
    return machine


@pytest.mark.parametrize("actions", CLICK_SURFACES)
def test_the_controller_closes_pointer_g1_at_zero_actions(actions):
    machine = _at_g1(actions)
    step = next_owned_step(machine)
    assert (step.owner, step.kind) == (CONTROLLER, ANSWER)  # ruling 6: no Duck turn before the first action
    machine.submit_answer(step.answer)
    assert machine.gate_id == "G2-COUNTER"


@pytest.mark.parametrize("actions", CLICK_SURFACES)
def test_the_pointer_template_explains_action6_only(actions):
    template = _at_g1(actions).gate_view()["answer_template"]
    assert set(template["action_laws"]) == {"ACTION6"}
    others = sorted(set(actions) - {"ACTION6"})
    for action in others:
        assert any(action in item and "open obligation" in item for item in template["limitations"])
    assert not any("coordinate" in law for name, law in template["action_laws"].items() if name != "ACTION6")


def test_the_g1_product_carries_the_open_non_pointer_actions():
    machine = _at_g1(("ACTION5", "ACTION6", "ACTION7"))
    step = next_owned_step(machine)
    machine.submit_answer(step.answer)
    law = machine.ego.ego_law
    assert dict(law.opaque_action_laws).keys() == {"ACTION6"}
    assert any("ACTION5" in item and "open obligation" in item for item in law.limitations)
    assert any("ACTION7" in item and "open obligation" in item for item in law.limitations)

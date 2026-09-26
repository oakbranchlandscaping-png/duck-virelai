from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from inference.framework.virelai_gates import EgoGateMachine


FIXTURE = Path(__file__).parent / "fixtures" / "cybernetic_gates" / "g0_g1_cases.json"


def _decision(probe):
    value = asdict(probe)
    value.pop("actions")
    value.pop("declared_at_transition")
    value["live_alternatives"] = list(value["live_alternatives"])
    value["outcome_partition"] = list(value["outcome_partition"])
    return value


def test_pointer_embodied_conditional_and_negative_fixtures_use_adapter_shape():
    payload = json.loads(FIXTURE.read_text())
    assert payload["schema"] == "virelai-production-shaped-gate-fixtures-v1"
    seen = set()
    for case in payload["cases"]:
        seen.add(case["name"])
        frame = case["current_frame"]
        machine = EgoGateMachine(
            valid_actions=case["valid_actions"],
            initial_grid=frame["grid"],
            observed_through_step=frame["step"],
        )
        probe = machine.next_probe()
        if case["expected_first_probe"] is None:
            assert probe is None
            assert machine.status == case["expected_status"]
        else:
            assert probe.actions[0] == case["expected_first_probe"]
        if "action_result" in case:
            accepted = machine.validate_probe(_decision(probe), list(probe.actions))
            machine.record_outcome(accepted, case["action_result"])
            machine.update_action_metadata(case["action_result"]["valid_actions"])
        if "new_action" in case:
            assert case["new_action"] in {item.action for item in machine.affordances}
    assert seen == {"pointer", "embodied", "conditional-action-surface", "negative-no-visible-effect"}

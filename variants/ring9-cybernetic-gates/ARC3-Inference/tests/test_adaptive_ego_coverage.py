from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from inference.framework.adaptive_ego_coverage import (
    AdaptiveCoordinateCoverage,
    visual_object_rank,
)
from inference.framework.virelai_gates import EgoGateMachine, GateContractError


GRID = (
    (0, 0, 0, 0, 0, 0, 0),
    (0, 1, 0, 1, 0, 1, 0),
    (0, 0, 0, 0, 0, 0, 0),
)


def _decision(machine: EgoGateMachine) -> dict:
    probe = machine.next_probe()
    assert probe is not None
    value = asdict(probe)
    value.pop("actions")
    value.pop("declared_at_transition")
    value["live_alternatives"] = list(value["live_alternatives"])
    value["outcome_partition"] = list(value["outcome_partition"])
    return value


def _execute(machine: EgoGateMachine, *, changed: bool) -> None:
    probe = machine.next_probe()
    assert probe is not None
    accepted = machine.validate_probe(_decision(machine), list(probe.actions))
    machine.record_outcome(accepted, {
        "transition_id": machine.observed_through_step + 1,
        "board_changed": changed,
    })


def test_coordinate_classes_are_deterministic_and_keep_observational_metadata():
    first = AdaptiveCoordinateCoverage(GRID)
    second = AdaptiveCoordinateCoverage(GRID)
    assert first.classes == second.classes
    assert first.initial_representatives() == second.initial_representatives()
    assert len(first.candidates) == 4
    assert len(first.classes) == 2
    point = next(item for item in first.candidates.values() if item.integer == 1)
    assert point.fingerprint_frequency == "REPEATED"
    assert point.zone in {"NW", "NC", "NE", "CW", "CC", "CE", "SW", "SC", "SE"}
    assert point.adjacent_component_count >= 1


def test_visual_object_roster_uses_captain_total_order_and_is_exhaustive():
    planner = AdaptiveCoordinateCoverage(GRID)
    ranked = planner.ranked_candidates()
    assert len(ranked) == len(planner.candidates)
    assert ranked == tuple(sorted(ranked, key=visual_object_rank))
    assert [(item.cell_count, item.integer, item.anchor) for item in ranked] == [
        (1, 1, (1, 1)),
        (1, 1, (1, 3)),
        (1, 1, (1, 5)),
        (18, 0, (0, 0)),
    ]


def test_positive_representative_requests_contrast_then_inconsistency_forces_expansion():
    planner = AdaptiveCoordinateCoverage(GRID)
    point_class = next(
        item for item in planner.classes
        if planner.candidates[item.representative_member_id].integer == 1
    )
    for target_class in planner.classes:
        planner.record(
            target_class.representative_member_id,
            {"board_changed": target_class.class_id == point_class.class_id},
        )
    contrast = planner.next_adaptive()
    assert contrast is not None and contrast[1] == "POSITIVE_CLASS_CONTRAST"
    planner.record(contrast[0].member_id, {"board_changed": False})
    expansion = planner.next_adaptive()
    assert expansion is not None and expansion[1] == "INCONSISTENT_CLASS_EXPANSION"
    assert expansion[0].class_id == point_class.class_id
    planner.record(expansion[0].member_id, {"board_changed": True})
    assert planner.next_adaptive() is None
    certificate = planner.certificate(include_unknown_members=True)
    row = next(item for item in certificate["classes"] if item["class_id"] == point_class.class_id)
    assert row["status"] == "INCONSISTENT_EXPANDED"
    assert row["members_unknown"] == 0


def test_negative_representatives_stop_as_representation_gap_without_inertness_claim():
    machine = EgoGateMachine(valid_actions=["ACTION1", "ACTION6"], initial_grid=GRID)
    initial_probe_count = len(machine.coverage)
    while machine.next_probe() is not None:
        _execute(machine, changed=False)
    assert initial_probe_count == 4
    assert machine.status == "UNRESOLVED"
    assert machine.coverage_stop_reason == "REPRESENTATION_GAP_NO_VISIBLE_EFFECT"
    certificate = machine.coverage_certificate(include_unknown_members=True)
    assert certificate["inertness_claim_permitted"] is False
    assert certificate["coordinate"]["unknown_count"] == 2
    with pytest.raises(GateContractError, match="representation gap"):
        machine.submit_answer({})


def test_simple_and_coordinate_effects_are_reported_as_mixed_without_semantic_assignment():
    machine = EgoGateMachine(valid_actions=["ACTION1", "ACTION6"], initial_grid=((0, 1),))
    while machine.next_probe() is not None:
        _execute(machine, changed=True)
    assert machine.status == "ANSWER_REQUIRED"
    certificate = machine.coverage_certificate(include_unknown_members=False)
    assert certificate["observed_channels"] == "MIXED"
    assert certificate["inertness_claim_permitted"] is False
    assert certificate["hybrid_post_click_pairs"] == [{
        "action": "ACTION1",
        "required_presses": 2,
        "observed_presses": 2,
        "effect_observed": True,
        "selection_reason": "TEST_POINTER_ACTIVATION",
    }]


def test_hybrid_retests_action5_and_movement_after_effective_click():
    machine = EgoGateMachine(
        valid_actions=["ACTION1", "ACTION5", "ACTION6"],
        initial_grid=((0, 1),),
    )
    while machine.next_probe() is not None:
        probe = machine.next_probe()
        changed = probe.actions[0]["action"] == "ACTION6"
        _execute(machine, changed=changed)
    certificate = machine.coverage_certificate(include_unknown_members=False)
    assert [row["action"] for row in certificate["hybrid_post_click_pairs"]] == [
        "ACTION1", "ACTION5"
    ]
    assert all(
        row["observed_presses"] == 2
        for row in certificate["hybrid_post_click_pairs"]
    )


def test_embodied_pointer_and_conditional_observation_branches_remain_hypotheses():
    embodied = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=GRID)
    _execute(embodied, changed=True)
    _execute(embodied, changed=True)
    embodied_certificate = embodied.coverage_certificate(include_unknown_members=False)
    assert embodied.status == "ANSWER_REQUIRED"
    assert embodied_certificate["observed_channels"] == "NON_COORDINATE_EFFECT"
    assert "embodied direct control" in embodied_certificate["live_alternatives"]

    pointer = EgoGateMachine(valid_actions=["ACTION6"], initial_grid=((0, 1),))
    pointer_certificate = pointer.coverage_certificate(include_unknown_members=False)
    assert pointer.status == "ANSWER_REQUIRED"
    assert pointer.next_probe() is None
    assert pointer_certificate["stop_reason"] == "ACTION_SURFACE_POINTER_EGO"
    assert pointer_certificate["coordinate"]["state"] == "DEFERRED_TO_LATER_TARGETS"

    conditional = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=GRID)
    _execute(conditional, changed=False)
    _execute(conditional, changed=True)
    conditional_certificate = conditional.coverage_certificate(include_unknown_members=False)
    assert conditional.status == "ANSWER_REQUIRED"
    assert conditional_certificate["conditional_evidence"] is True
    assert "conditional or refused control" in conditional_certificate["live_alternatives"]


def test_newly_offered_action_extends_pairs_before_coverage_can_finish():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=GRID)
    _execute(machine, changed=True)
    machine.update_action_metadata(["ACTION1", "ACTION5"])
    remaining = [item for item in machine.coverage if not item.observed]
    assert [item.action for item in remaining] == ["ACTION1", "ACTION5", "ACTION5"]
    while machine.next_probe() is not None:
        _execute(machine, changed=True)
    certificate = machine.coverage_certificate(include_unknown_members=False)
    action5 = next(row for row in certificate["simple_action_pairs"] if row["action"] == "ACTION5")
    assert action5["observed_presses"] == 2
    assert machine.status == "ANSWER_REQUIRED"


def test_temporarily_unavailable_coordinate_action_records_gap_and_resumes():
    machine = EgoGateMachine(valid_actions=["ACTION1", "ACTION6"], initial_grid=GRID)
    _execute(machine, changed=True)
    _execute(machine, changed=True)
    _execute(machine, changed=True)
    machine.update_action_metadata([])
    assert machine.status == "UNRESOLVED"
    assert machine.coverage_stop_reason == "COORDINATE_ACTION_UNAVAILABLE"
    assert machine.next_probe() is None
    machine.update_action_metadata(["ACTION6"])
    assert machine.status == "ACTIVE"
    assert machine.next_probe() is not None


def test_recorded_ft09_is_reduced_from_65_components_to_eight_representatives():
    repo = Path(__file__).resolve().parents[4]
    events = repo / "runs/kaggle-ring9-g0-checkpoint-v2/kaggle-output/artifacts/ft09-0d8bbf25_p0_events.jsonl"
    if not events.exists():
        pytest.skip("recorded ft09 artifact is outside this source package")
    rows = [json.loads(line) for line in events.read_text().splitlines() if line.strip()]
    grid = next(row["board"] for row in rows if isinstance(row.get("board"), list))
    planner = AdaptiveCoordinateCoverage(grid)
    assert len(planner.candidates) == 65
    assert len(planner.initial_representatives()) == 8

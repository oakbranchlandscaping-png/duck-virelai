from __future__ import annotations

import pytest

from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.g4_limits import (
    G4LimitError,
    LeverLimitStudy,
    validate_limit_answer,
)
from inference.framework.masked_world_state import raw_address
from inference.framework.virelai_gates import CyberneticGateMachine


def grid(value):
    return ((0, value), (0, 0))


def record(study, before, after, index, boundary=None):
    return study.record(
        evidence_ref=f"E-{index}",
        transition_id=index,
        before=grid(before),
        after=grid(after),
        boundary_state=boundary,
    )


def study(**overrides):
    options = {
        "entity_id": "E-A",
        "intervention": {"action": "ACTION6", "row": 2, "col": 3},
        "orbit_state_sequence": ("unused-S0", "unused-S1"),
        "orbit_stop_disposition": "NULL_AT_OBSERVED_STATE",
        "mask_law": None,
        "inverse_candidates": (
            ("E-B", {"action": "ACTION6", "row": 5, "col": 6}),
        ),
    }
    # Replace symbolic orbit addresses with the addresses computed by the implementation.
    options["orbit_state_sequence"] = (raw_address(grid(1)), raw_address(grid(2)))
    options.update(overrides)
    return LeverLimitStudy(**options)


def valid_answer(target):
    return {
        "answer_kind": "LEVER_LIMIT_OBSERVATION",
        "entity_id": target.entity_id,
        "endpoint_disposition": target.endpoint_disposition,
        "persistence_disposition": target.persistence_disposition,
        "reversal_disposition": target.reversal_disposition,
        "inverse_entity_id": target.inverse_entity_id,
        "restored_orbit_state_index": target.restored_orbit_state_index,
        "original_reenabled": target.original_reenabled,
        "mechanism_explanation": (
            "The observed endpoint repeated, the candidate restored an earlier state, "
            "and the original lever then produced another visible change."
        ),
        "evidence_refs": [item.evidence_ref for item in target.observations],
        "competing_models": ["The relation may depend on an unmeasured world condition."],
        "falsifier": "The same scoped sequence later fails to restore the prior state.",
        "limitations": ["The result is scoped to this observed state."],
    }


def test_exact_reversal_requires_endpoint_repeat_restore_and_reenablement():
    target = study()
    assert target.next_probe().operation_kind == "CONFIRM_ENDPOINT"
    assert record(target, 2, 2, 1).disposition == "ENDPOINT_CONFIRMED"
    assert target.endpoint_disposition == "SATURATED_AT_OBSERVED_STATE"

    inverse = target.next_probe()
    assert inverse.operation_kind == "TEST_INVERSE"
    assert inverse.candidate_entity_id == "E-B"
    restored = record(target, 2, 1, 2)
    assert restored.disposition == "EXACT_ORBIT_STATE_RESTORED"
    assert restored.restored_orbit_state_index == 0

    assert target.next_probe().operation_kind == "REAPPLY_ORIGINAL"
    assert record(target, 1, 2, 3).disposition == "ORIGINAL_REENABLED"
    assert target.reversal_disposition == "EXACT_REVERSAL_DEMONSTRATED"
    answer = validate_limit_answer(valid_answer(target), target)
    assert answer.inverse_entity_id == "E-B"
    assert answer.original_reenabled is True


def test_two_endpoint_nulls_are_needed_across_g4_2_and_g4_3():
    target = study(inverse_candidates=())
    assert record(target, 2, 2, 1).disposition == "ENDPOINT_CONFIRMED"
    assert target.ready_for_answer is True
    assert target.endpoint_disposition == "SATURATED_AT_OBSERVED_STATE"
    assert target.reversal_disposition == "NO_CANDIDATE_AVAILABLE"


def test_control_trial_can_show_persistence_without_becoming_a_reversal_claim():
    target = study(
        control_intervention={"action": "ACTION6", "row": 8, "col": 8},
        inverse_candidates=(),
    )
    record(target, 2, 2, 1)
    assert target.next_probe().operation_kind == "TEST_PERSISTENCE"
    observation = record(target, 2, 2, 2)
    assert observation.disposition == "PERSISTED_THROUGH_CONTROL"
    assert target.persistence_disposition == "PERSISTED_THROUGH_CONTROL"
    assert target.reversal_disposition == "NO_CANDIDATE_AVAILABLE"


def test_changed_candidate_is_only_release_without_exact_prior_state():
    target = study()
    record(target, 2, 2, 1)
    observation = record(target, 2, 7, 2)
    assert observation.disposition == "STATE_RELEASED_WITHOUT_EXACT_RESTORATION"
    assert target.reversal_disposition == "STATE_RELEASED_WITHOUT_EXACT_RESTORATION"
    record(target, 7, 8, 3)
    assert target.reversal_disposition == "STATE_RELEASED_WITHOUT_EXACT_RESTORATION"


def test_boundary_interrupts_without_creating_a_limit_answer():
    target = study()
    observation = record(target, 2, 3, 1, {"level_completed": True})
    assert observation.disposition == "BOUNDARY_INTERRUPTED"
    assert target.interrupted is True
    with pytest.raises(G4LimitError, match="premature"):
        validate_limit_answer(valid_answer(target), target)


def test_discontinuous_chain_is_rejected():
    target = study()
    with pytest.raises(G4LimitError, match="discontinuous"):
        record(target, 9, 9, 1)


def test_answer_cannot_invent_an_inverse():
    target = study()
    record(target, 2, 2, 1)
    record(target, 2, 1, 2)
    record(target, 1, 2, 3)
    raw = valid_answer(target)
    raw["inverse_entity_id"] = "E-INVENTED"
    with pytest.raises(G4LimitError, match="inverse_entity_id"):
        validate_limit_answer(raw, target)


def machine_at_g4_3():
    initial = grid(2)
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=initial)
    machine.submit_answer({
        "answer_id": "G0-test",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    products = (
        MemoryProduct(
            product_id="EGO-test", product_type="EgoLaw", target_id="G1-EGO", revision=1,
            payload={"mode": "POINTER_GOD_MODE"}, dependencies=("G0-ACTION-METADATA",),
        ),
        MemoryProduct(
            product_id="COUNTER-test", product_type="CounterGateProduct",
            target_id="G2-COUNTER", revision=1, payload={"mask_law": None},
            dependencies=("G1-EGO",),
        ),
        MemoryProduct(
            product_id="LEVERS-test", product_type="LeverInventory",
            target_id="G3-LEVERS", revision=1,
            payload={"lever_entities": ["E-A", "E-B"], "clean_null_entities": []},
            dependencies=("G2-COUNTER",),
        ),
        MemoryProduct(
            product_id="ANATOMY-test", product_type="LeverEffectAnatomySet",
            target_id="G4-REACTIONS", revision=1,
            payload={
                "anatomies": [
                    {"entity_id": "E-A", "intervention": {"action": "ACTION6", "row": 2, "col": 3}},
                    {"entity_id": "E-B", "intervention": {"action": "ACTION6", "row": 5, "col": 6}},
                ]
            },
            dependencies=("G3-LEVERS",),
        ),
        MemoryProduct(
            product_id="ORBITS-test", product_type="LeverOrbitSet",
            target_id="G4.2-LEVER-ORBITS", revision=1,
            payload={
                "lever_entities": ["E-A", "E-B"],
                "pending_lever_entities": [],
                "lever_classes": {"E-A": "ABSORBING", "E-B": "TOGGLE"},
                "orbits": [
                    {
                        "entity_id": "E-A",
                        "intervention": {"action": "ACTION6", "row": 2, "col": 3},
                        "status": "NULL_AT_OBSERVED_STATE",
                        "state_sequence": [raw_address(grid(1)), raw_address(grid(2))],
                    },
                    {
                        "entity_id": "E-B",
                        "intervention": {"action": "ACTION6", "row": 5, "col": 6},
                        "status": "OBSERVED_STATE_RECURRENCE",
                        "state_sequence": [raw_address(grid(4)), raw_address(grid(5)), raw_address(grid(4))],
                    },
                ]
            },
            dependencies=("G4-REACTIONS",),
        ),
    )
    for product in products:
        machine.target_journal.put(product)
    return machine


def machine_at_g4_2_with_two_levers():
    machine = machine_at_g4_3()
    machine.target_journal.invalidate("G4.2-LEVER-ORBITS", include_self=True)
    return machine


def outcome(before, after, transition_id):
    left, right = grid(before), grid(after)
    return {
        "transition_id": transition_id,
        "action": {"action": "ACTION6", "row": 0, "col": 0},
        "changed_cells": [
            {"row": row, "col": col, "before": value, "after": right[row][col]}
            for row, values in enumerate(left)
            for col, value in enumerate(values)
            if value != right[row][col]
        ],
        "site_transitions": [
            {"row": row, "col": col, "before": value, "after": right[row][col]}
            for row, values in enumerate(left)
            for col, value in enumerate(values)
        ],
        "shape_before": [2, 2],
        "shape_after": [2, 2],
        "boundary_event": {"state": "PLAYING"},
    }


def execute(machine, before, after, transition_id):
    capability = machine.next_probe_capability()
    probe = machine.validate_probe(
        {"probe_token": capability["probe_token"]}, capability["actions"]
    )
    return machine.record_outcome(probe, outcome(before, after, transition_id))


def test_gate_routes_through_endpoint_inverse_and_reapplication():
    machine = machine_at_g4_3()
    assert machine.gate_id == "G4.3-LEVER-LIMITS"
    assert machine.gate_view()["progress"]["current_phase"] == "CONFIRM_ENDPOINT"

    first = execute(machine, 2, 2, 11)
    assert first["limit_observation"]["disposition"] == "ENDPOINT_CONFIRMED"
    assert machine.next_probe_capability()["purpose"] == "TEST_INVERSE"

    second = execute(machine, 2, 1, 12)
    assert second["limit_observation"]["disposition"] == "EXACT_ORBIT_STATE_RESTORED"
    assert machine.next_probe_capability()["purpose"] == "REAPPLY_ORIGINAL"

    third = execute(machine, 1, 2, 13)
    assert third["limit_observation"]["disposition"] == "ORIGINAL_REENABLED"
    template = machine.gate_view()["answer_template"]
    machine.submit_answer({
        **template,
        "mechanism_explanation": (
            "The endpoint repeated, E-B restored the earlier orbit state, and E-A then "
            "became effective again under the observed conditions."
        ),
        "competing_models": ["An unmeasured condition may mediate the paired response."],
        "falsifier": "The same state-scoped sequence fails to restore and re-enable E-A.",
    })
    # All-levers-then-satisfy: E-A is fully studied (endpoint/inverse/reapply proven above),
    # but E-B remains, so the gate does not satisfy on one lever - it advances to E-B.
    assert machine.status == "PROBE_REQUIRED"
    assert machine.gate_view()["progress"]["current_entity_id"] == "E-B"
    assert machine.target_journal.active_product("G4.3-LEVER-LIMITS") is None


def test_completed_orbit_descends_entity_locally_without_discarding_pending_lever():
    machine = machine_at_g4_2_with_two_levers()
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    capability = machine.next_probe_capability()
    probe = machine.validate_probe(
        {"probe_token": capability["probe_token"]}, capability["actions"]
    )
    machine.record_outcome(probe, outcome(2, 2, 21))
    template = machine.gate_view()["answer_template"]
    machine.submit_answer({
        **template,
        "mechanism_explanation": (
            "The active lever produced no counter-masked change at this exact observed state."
        ),
        "competing_models": ["The same lever may respond from another state."],
        "falsifier": "A repeat from this exact masked state later changes the world.",
    })
    orbit_product = machine.target_journal.active_product("G4.2-LEVER-ORBITS")
    assert orbit_product.payload["lever_entities"] == ["E-A"]
    assert orbit_product.payload["pending_lever_entities"] == ["E-B"]
    assert orbit_product.payload["lever_classes"]["E-A"] == "ABSORBING"
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    view = machine.gate_view()
    assert view["progress"]["current_entity_id"] == "E-B"
    assert machine.next_probe_capability()["purpose"] == "REPEAT_CONFIRMED_LEVER"


def test_phase1_drains_both_levers_before_g4_3_opens():
    machine = machine_at_g4_2_with_two_levers()

    def orbit_current_null(tid):
        cap = machine.next_probe_capability()
        probe = machine.validate_probe(
            {"probe_token": cap["probe_token"]}, cap["actions"]
        )
        machine.record_outcome(probe, outcome(2, 2, tid))
        template = machine.gate_view()["answer_template"]
        machine.submit_answer({
            **template,
            "mechanism_explanation": (
                "Consecutive presses left the counter-masked world unchanged at this state."
            ),
            "competing_models": ["The lever may respond from another state."],
            "falsifier": "A later repeat from this exact masked state changes the world.",
        })

    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    orbit_current_null(31)  # E-A
    # Return edge: E-B still pending, so the machine stays in G4.2 rather than opening G4.3.
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    assert machine.gate_view()["progress"]["current_entity_id"] == "E-B"
    orbit_current_null(32)  # E-B
    orbit_product = machine.target_journal.active_product("G4.2-LEVER-ORBITS")
    assert set(orbit_product.payload["lever_entities"]) == {"E-A", "E-B"}
    assert orbit_product.payload["pending_lever_entities"] == []
    assert orbit_product.payload["lever_classes"] == {"E-A": "ABSORBING", "E-B": "ABSORBING"}
    # Phase-1-complete: only now does Phase 2 (G4.3) open.
    assert machine.gate_id == "G4.3-LEVER-LIMITS"

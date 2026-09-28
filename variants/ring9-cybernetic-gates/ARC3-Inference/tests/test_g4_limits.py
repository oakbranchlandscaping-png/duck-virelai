from __future__ import annotations

import pytest

from inference.framework.g4_limits import (
    G4LimitError,
    LeverLimitStudy,
    validate_limit_answer,
)
from inference.framework.masked_world_state import raw_address


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


# The gate-level G4.3 routing tests were removed on 2026-09-27 (Claude, Alpha build seat):
# G4.3-LEVER-LIMITS is retired from the ladder by the Director's ruling that G4 becomes stated
# targets. Endpoint/recurrence confirmation now lives in the guided G4-A run
# (tests/test_g4_guided.py); persistence and reversal return in G4-B as Duck-proposed,
# prediction-first tests. The study-level tests above stay: g4_limits.py is the port source.

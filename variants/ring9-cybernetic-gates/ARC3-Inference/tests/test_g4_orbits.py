import pytest

from inference.framework.counter_verification import MaskLaw
from inference.framework.g4_orbits import G4OrbitError, LeverOrbit, validate_orbit_answer


LAW = MaskLaw(
    law_id="MASK-test",
    law_version_id="MASK-test-v1",
    revision=1,
    status="LOCKED",
    cells=((0, 0),),
    rewrite="ignore bookkeeping cell",
    witness_evidence_refs=("E-counter",),
    demonstration_ref="E-counter-confirm",
)


def record(orbit, before, after, index, boundary=None):
    return orbit.record(
        evidence_ref=f"E-{index}",
        transition_id=index,
        before=before,
        after=after,
        boundary_state=boundary,
    )


def test_counter_only_change_is_masked_null():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    step = record(orbit, ((8, 0), (0, 2)), ((7, 0), (0, 2)), 1)
    assert step.disposition == "NULL_AT_OBSERVED_STATE"
    assert step.world_changed is False
    assert step.changed_cells == ()
    assert orbit.closed is True


def test_novel_states_continue_until_exact_recurrence():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    first = record(orbit, ((8, 0), (0, 2)), ((7, 0), (0, 3)), 1)
    second = record(orbit, ((7, 0), (0, 3)), ((6, 0), (0, 4)), 2)
    third = record(orbit, ((6, 0), (0, 4)), ((5, 0), (0, 2)), 3)
    assert first.disposition == second.disposition == "NOVEL_STATE_REVEALED"
    assert orbit.closed is True
    assert third.disposition == "OBSERVED_STATE_RECURRENCE"
    assert third.recurrence_to_state_index == 0
    assert third.observed_period == 3
    assert len(orbit.state_sequence) == 4


def test_no_activation_count_is_epistemic_completion():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    before = ((9, 0), (0, 0))
    for index in range(1, 21):
        after = ((9 - index, 0), (0, index))
        step = record(orbit, before, after, index)
        assert step.disposition == "NOVEL_STATE_REVEALED"
        before = after
    assert orbit.closed is False
    assert len(orbit.steps) == 20


def test_boundary_interrupts_without_claiming_orbit_completion():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    step = record(
        orbit,
        ((8, 0), (0, 2)),
        ((7, 0), (0, 3)),
        1,
        {"level_completed": True},
    )
    assert step.disposition == "BOUNDARY_INTERRUPTED"
    with pytest.raises(G4OrbitError, match="boundary-interrupted"):
        validate_orbit_answer({}, orbit)


def test_answer_must_copy_exact_observed_orbit():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    record(orbit, ((8, 0), (0, 2)), ((7, 0), (0, 2)), 1)
    raw = {
        "answer_kind": "LEVER_ORBIT_OBSERVATION",
        "entity_id": "E0001",
        "intervention": {"action": "ACTION6", "row": 1, "col": 1},
        "stop_disposition": "NULL_AT_OBSERVED_STATE",
        "state_sequence": list(orbit.state_sequence),
        "recurrence_to_state_index": 0,
        "observed_period": 0,
        "mechanism_explanation": (
            "Repeated activation produced no counter-masked world change at this observed state."
        ),
        "evidence_refs": ["E-1"],
        "competing_models": ["The lever may react from a different state."],
        "falsifier": "A repeat from this exact state changes the masked world.",
        "limitations": ["This null is scoped to the observed state."],
    }
    answer = validate_orbit_answer(raw, orbit)
    assert answer.stop_disposition == "NULL_AT_OBSERVED_STATE"
    corrupted = dict(raw, state_sequence=["invented"])
    with pytest.raises(G4OrbitError, match="state_sequence"):
        validate_orbit_answer(corrupted, orbit)


def test_discontinuous_state_chain_is_rejected():
    orbit = LeverOrbit(
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        mask_law=LAW,
    )
    record(orbit, ((8, 0), (0, 2)), ((7, 0), (0, 3)), 1)
    with pytest.raises(G4OrbitError, match="discontinuous"):
        record(orbit, ((6, 0), (0, 4)), ((5, 0), (0, 5)), 2)

from inference.framework.virelai_physics_manual import physics_manual, render_physics_manual
from inference.framework.virelai_world_model import MechanicRule, StateVariable, empty_world_model
from dataclasses import replace


def test_manual_is_compact_level_scoped_projection():
    base = empty_world_model(
        game_id="fixture", observed_through_step=12, levels_observed=[1, 2],
        current_level=2, source_schema="fixture-v1",
    )
    model = replace(base, mechanics=(
        MechanicRule(
            rule_id="M-1", trigger_action="ACTION6", trigger_object_type=None,
            affected_ids=("RESOURCE",), transformation="TOGGLE", period=2,
            levels_observed=(1,), subject_ids=("CONTROL-A",),
            witness_transition_ids=(2, 3, 4, 5), scope="L1", status="OBSERVED",
        ),
        MechanicRule(
            rule_id="M-2", trigger_action="ACTION1", trigger_object_type=None,
            affected_ids=("EGO",), transformation="MOVE", levels_observed=(2,),
            subject_ids=("EGO",), status="CANDIDATE",
        ),
    ), state_variables=(
        StateVariable("V-1", "RESOURCE", ("0", "1"), "1", cyclic=True),
    ))

    manual = physics_manual(model, level=1)
    assert manual["mechanics_total"] == 1
    assert manual["mechanics"][0]["period"] == 2
    assert manual["mechanics"][0]["state"][0]["current"] == "1"
    text = render_physics_manual(manual)
    assert "Control A" in text
    assert "M-1" in text
    assert "CONTROL-A" not in text
    assert "LEVEL 1" in text
    assert "M-2" not in text

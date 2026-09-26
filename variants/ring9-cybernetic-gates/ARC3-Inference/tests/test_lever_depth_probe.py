from __future__ import annotations

import pytest

from inference.framework.virelai_semantic.depth_probe import (
    ActivationObservation,
    LeverDepthPlanner,
)


def _segment(*levers):
    return {"lever_mechanics": {"levers": list(levers)}}


def _lever(handle, *channels, kind="VISUAL_OBJECT"):
    return {
        "lever": handle,
        "kind": kind,
        "visible": {"bbox": [1, 2, 3, 4]},
        "effect_channels": [{"channel": channel} for channel in channels],
    }


def _record(planner, lever, step, **states):
    planner.record(ActivationObservation(lever=lever, step=step, channel_states=states))


def test_planner_names_target_but_never_chooses_an_arc_action():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("L-A", "C-1"))])
    request = planner.request()["request"]
    assert request["lever"] == "L-A"
    assert request["activation_mode"] == "POINTER_TARGET_REQUIRED"
    assert request["arc_action"] is None


def test_contact_surface_requires_routing_instead_of_fabricating_motion():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("SURFACE", "C-1", kind="CONTACT_SURFACE"))])
    assert planner.request()["request"]["activation_mode"] == "BODY_CONTACT_REQUIRED"


def test_exact_toggle_needs_two_complete_periods_then_advances_queue():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("L-A", "C"), _lever("L-B", "D"))])
    for step, state in enumerate(("left", "right", "left"), start=1):
        _record(planner, "L-A", step, C=state)
        assert planner.request()["request"]["lever"] == "L-A"
    _record(planner, "L-A", 4, C="right")
    assert planner.request()["request"]["lever"] == "L-B"
    row = planner.export()["levers"][0]
    assert row["channels"]["C"]["mechanism"] == "TOGGLE"
    assert row["channels"]["C"]["period"] == 2
    assert row["completion"] == "EVIDENCE_TERMINATED"


def test_two_consecutive_no_change_seals_condition_not_mechanism():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("L", "C"))])
    for step, state in enumerate(("a", "b", "b", "b"), start=1):
        _record(planner, "L", step, C=state)
    channel = planner.export()["levers"][0]["channels"]["C"]
    assert channel["condition"] == "SATURATED_OBSERVED"
    assert channel["mechanism"] == "UNIFORM_RESPONSE"
    assert planner.request()["status"] == "SATURATED"


def test_dynamic_refresh_appends_new_lever_without_resetting_completed_one():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("L-A", "C"))])
    for step, state in enumerate((0, 1, 1, 1), start=1):
        _record(planner, "L-A", step, C=state)
    planner.refresh([_segment(_lever("L-A", "C"), _lever("L-NEW", "N"))])
    assert planner.request()["request"]["lever"] == "L-NEW"
    assert planner.export()["levers"][0]["activations"] == 4


def test_channel_mismatch_is_an_explicit_failure():
    planner = LeverDepthPlanner()
    planner.refresh([_segment(_lever("L", "C"))])
    with pytest.raises(ValueError, match="channel mismatch"):
        _record(planner, "L", 1, WRONG=7)


def test_cap_is_backstop_and_does_not_invent_a_type():
    planner = LeverDepthPlanner(engineering_cap=3)
    planner.refresh([_segment(_lever("L", "C"))])
    for step, state in enumerate((1, 2, 3), start=1):
        _record(planner, "L", step, C=state)
    row = planner.export()["levers"][0]
    assert row["completion"] == "CAP_REACHED_UNRESOLVED"
    assert row["channels"]["C"]["mechanism"] == "UNKNOWN"

from __future__ import annotations

import pytest

from inference.agent.runtime_state import Frame
from inference.framework.ego_verification import (
    compare_probe_outcome,
    ego_law_from_supported,
    prediction_from_mapping,
    revise_ego_law,
)
from inference.framework.probe_evidence import compile_probe_outcome


def _outcome(before, after, *, probe_id="G1-EGO:DEMO", transition_id=4, action=None):
    return compile_probe_outcome(
        probe_id=probe_id,
        transition_id=transition_id,
        action=action or {"action": "ACTION1"},
        before_frame=Frame(grid=before, step=transition_id - 1, level=1),
        after_frame=Frame(grid=after, step=transition_id, level=1),
        available_actions_before=["ACTION1", "ACTION6"],
        available_actions_after=["ACTION1", "ACTION6"],
        callback_payload={"board_changed": before != after, "state": "PLAYING"},
    )


def _prediction(*, predicate, scope=None, action=None, expected_parameters=None):
    return prediction_from_mapping({
        "probe_id": "G1-EGO:DEMO",
        "declared_at_transition": 3,
        "action": action or {"action": "ACTION1"},
        "scope": scope or {"representation": "VISIBLE_OBSERVATION"},
        "predicate": predicate,
        "expected_parameters": expected_parameters or {},
        "evidence_basis": ["E-opening-1", "E-opening-2"],
        "falsifier": "the declared scoped transition differs",
    })


def _form_prediction(
    predicate,
    before_footprint,
    after_footprint,
    *,
    before_integer=1,
    after_integer=1,
    recolor=False,
    displacement=None,
):
    expected = {
        "before_footprint": [list(cell) for cell in before_footprint],
        "after_footprint": [list(cell) for cell in after_footprint],
        "before_integer": before_integer,
        "after_integer": after_integer,
        "recolor": recolor,
    }
    if displacement is not None:
        expected["displacement"] = list(displacement)
    return _prediction(
        predicate=predicate,
        scope={"representation": "CELLS", "cells": expected["before_footprint"]},
        expected_parameters=expected,
    )


def test_visible_no_change_is_supported_from_frame_derived_diff():
    grid = ((0, 0), (0, 5))
    comparison = compare_probe_outcome(_prediction(predicate="NO_CHANGE"), _outcome(grid, grid))
    assert comparison.outcome == "SUPPORTED"
    assert comparison.scoped_changes == ()


def test_remote_change_cannot_support_acted_component_any_change():
    before = ((0, 0, 0), (0, 5, 0), (0, 0, 0))
    after = ((2, 0, 0), (0, 5, 0), (0, 0, 0))
    action = {"action": "ACTION6", "row": 1, "col": 1}
    prediction = _prediction(
        predicate="ANY_CHANGE",
        scope={"representation": "ACTED_COMPONENT"},
        action=action,
    )
    comparison = compare_probe_outcome(prediction, _outcome(before, after, action=action))
    assert comparison.outcome == "CONTRADICTED"
    assert comparison.scoped_changes == ()
    assert comparison.remote_changes == ((0, 0, 0, 2),)


def test_remote_change_does_not_contradict_acted_component_no_change():
    before = ((0, 0, 0), (0, 5, 0), (0, 0, 0))
    after = ((2, 0, 0), (0, 5, 0), (0, 0, 0))
    action = {"action": "ACTION6", "row": 1, "col": 1}
    prediction = _prediction(
        predicate="NO_CHANGE",
        scope={"representation": "ACTED_COMPONENT"},
        action=action,
    )
    comparison = compare_probe_outcome(prediction, _outcome(before, after, action=action))
    assert comparison.outcome == "SUPPORTED"
    assert comparison.remote_changes == ((0, 0, 0, 2),)


def test_exact_cell_delta_requires_the_declared_values_and_scope():
    before = ((0, 5), (0, 0))
    after = ((0, 6), (2, 0))
    prediction = _prediction(
        predicate="EXACT_CELL_DELTA",
        scope={"representation": "CELLS", "cells": [[0, 1]]},
        expected_parameters={
            "changes": [{"row": 0, "col": 1, "before": 5, "after": 6}]
        },
    )
    comparison = compare_probe_outcome(prediction, _outcome(before, after))
    assert comparison.outcome == "SUPPORTED"
    assert comparison.scoped_changes == ((0, 1, 5, 6),)
    assert comparison.remote_changes == ((1, 0, 0, 2),)


def test_retrospective_or_wrong_action_prediction_is_unmatched():
    grid = ((0,),)
    retrospective = prediction_from_mapping({
        "probe_id": "G1-EGO:DEMO",
        "declared_at_transition": 4,
        "action": {"action": "ACTION1"},
        "scope": {"representation": "VISIBLE_OBSERVATION"},
        "predicate": "NO_CHANGE",
        "expected_parameters": {},
        "evidence_basis": ["E-opening"],
        "falsifier": "the board changes",
    })
    assert compare_probe_outcome(retrospective, _outcome(grid, grid)).outcome == "UNMATCHED"
    wrong_action = _prediction(predicate="NO_CHANGE", action={"action": "ACTION2"})
    assert compare_probe_outcome(wrong_action, _outcome(grid, grid)).outcome == "UNMATCHED"


def test_worldline_without_pre_action_resolution_is_indeterminate():
    grid = ((0, 5),)
    prediction = _prediction(
        predicate="ANY_CHANGE",
        scope={"representation": "WORLDLINE", "identifier": "candidate-ego"},
    )
    comparison = compare_probe_outcome(prediction, _outcome(grid, ((0, 6),)))
    assert comparison.outcome == "INDETERMINATE"
    assert "Scope was not widened." in comparison.limitations


def test_terminal_boundary_is_indeterminate():
    outcome = _outcome(((0,),), ((1,),))
    outcome["boundary_event"]["level_completed"] = True
    comparison = compare_probe_outcome(_prediction(predicate="ANY_CHANGE"), outcome)
    assert comparison.outcome == "INDETERMINATE"


def test_overlapping_pure_translation_uses_held_sites_and_separates_remote_change():
    before = ((1, 1, 1, 0, 0), (0, 0, 0, 0, 0))
    after = ((0, 1, 1, 1, 0), (0, 0, 0, 0, 2))
    prediction = _form_prediction(
        "PURE_TRANSLATION",
        [(0, 0), (0, 1), (0, 2)],
        [(0, 1), (0, 2), (0, 3)],
        displacement=(0, 1),
    )
    comparison = compare_probe_outcome(prediction, _outcome(before, after))
    assert comparison.outcome == "SUPPORTED"
    assert comparison.observed_form == "PURE_TRANSLATION"
    assert comparison.observed_translation == (0, 1)
    assert comparison.observed_recolor is False
    assert comparison.scoped_changes == ((0, 0, 1, 0), (0, 3, 0, 1))
    assert comparison.remote_changes == ((1, 4, 0, 2),)


@pytest.mark.parametrize(
    ("predicate", "before", "after", "before_cells", "after_cells", "after_integer", "recolor"),
    [
        ("STILL", ((0, 1, 0),), ((0, 1, 0),), [(0, 1)], [(0, 1)], 1, False),
        ("RECOLOR", ((0, 1, 0),), ((0, 2, 0),), [(0, 1)], [(0, 1)], 2, True),
        ("GROW", ((0, 1, 0),), ((0, 2, 2),), [(0, 1)], [(0, 1), (0, 2)], 2, True),
        ("SHRINK", ((1, 1, 0),), ((1, 0, 0),), [(0, 0), (0, 1)], [(0, 0)], 1, False),
        ("DEFORM", ((1, 1, 0), (0, 0, 0)), ((1, 0, 0), (1, 0, 0)), [(0, 0), (0, 1)], [(0, 0), (1, 0)], 1, False),
    ],
)
def test_form_predicates_verify_exact_component_endpoints(
    predicate, before, after, before_cells, after_cells, after_integer, recolor
):
    prediction = _form_prediction(
        predicate,
        before_cells,
        after_cells,
        after_integer=after_integer,
        recolor=recolor,
    )
    comparison = compare_probe_outcome(prediction, _outcome(before, after))
    assert comparison.outcome == "SUPPORTED"
    assert comparison.observed_form == predicate
    assert comparison.observed_recolor is recolor


def test_extra_after_component_cell_contradicts_exact_footprint_prediction():
    prediction = _form_prediction(
        "GROW", [(0, 0)], [(0, 0), (0, 1)]
    )
    comparison = compare_probe_outcome(
        prediction,
        _outcome(((1, 0, 0),), ((1, 1, 1),)),
    )
    assert comparison.outcome == "CONTRADICTED"
    assert comparison.after_footprint == ((0, 0), (0, 1), (0, 2))
    assert "footprint differed" in " ".join(comparison.limitations)


def test_absent_predicted_after_component_does_not_invent_form_or_recolor():
    prediction = _form_prediction(
        "RECOLOR", [(0, 0)], [(0, 0)], after_integer=2, recolor=True
    )
    comparison = compare_probe_outcome(
        prediction,
        _outcome(((1, 0),), ((0, 1),)),
    )
    assert comparison.outcome == "CONTRADICTED"
    assert comparison.observed_form is None
    assert comparison.observed_recolor is None
    assert comparison.after_footprint == ()


def test_unresolved_declared_before_component_is_indeterminate_without_scope_widening():
    prediction = _form_prediction("STILL", [(0, 0)], [(0, 0)])
    comparison = compare_probe_outcome(
        prediction,
        _outcome(((1, 1),), ((1, 1),)),
    )
    assert comparison.outcome == "INDETERMINATE"
    assert "Scope was not widened." in comparison.limitations


def test_form_prediction_rejects_inconsistent_geometry_or_recolor_contract():
    with pytest.raises(Exception, match="imply PURE_TRANSLATION"):
        _form_prediction("GROW", [(0, 0)], [(0, 1)], displacement=(0, 1))
    with pytest.raises(Exception, match="recolor"):
        _form_prediction(
            "RECOLOR", [(0, 0)], [(0, 0)], after_integer=1, recolor=True
        )


def test_ego_law_has_stable_identity_and_append_only_revision_lineage():
    supported = compare_probe_outcome(
        _prediction(predicate="ANY_CHANGE"),
        _outcome(((0,),), ((1,),)),
    )
    answer = {
        "answer_id": "A-grounded-ego",
        "answer_kind": "embodied",
        "subjects": ["the demonstrated cell at (0,0)"],
        "action_laws": {"ACTION1": "changes the demonstrated cell"},
        "conditions": ["the action remains available"],
        "constraints": ["visible scope only"],
        "evidence_refs": ["E-opening-1", "E-opening-2"],
        "competing_models": ["remote effect"],
        "falsifier": "the demonstrated cell remains unchanged",
        "limitations": ["identity across frames is not established"],
    }
    parent = ego_law_from_supported(answer, supported)
    contradicted = compare_probe_outcome(
        _prediction(predicate="ANY_CHANGE"),
        _outcome(((0,),), ((0,),), transition_id=5),
    )
    child = revise_ego_law(parent, contradicted)
    assert child is not None
    assert child.law_id == parent.law_id
    assert child.law_version_id != parent.law_version_id
    assert child.parent_law_version_id == parent.law_version_id
    assert child.status == "CONTRADICTED"
    assert child.contradiction_transition_ids == (5,)
    assert parent.status == "OBSERVED"
    assert parent.contradiction_transition_ids == ()


def test_indeterminate_evidence_does_not_create_a_law_revision():
    supported = compare_probe_outcome(
        _prediction(predicate="ANY_CHANGE"),
        _outcome(((0,),), ((1,),)),
    )
    parent = ego_law_from_supported({
        "answer_id": "A1",
        "answer_kind": "embodied",
        "subjects": ["cell"],
        "action_laws": {"ACTION1": "changes the cell"},
        "evidence_refs": ["E1"],
        "falsifier": "cell unchanged",
    }, supported)
    boundary = _outcome(((0,),), ((1,),), transition_id=5)
    boundary["boundary_event"]["level_completed"] = True
    indeterminate = compare_probe_outcome(_prediction(predicate="ANY_CHANGE"), boundary)
    assert revise_ego_law(parent, indeterminate) is None

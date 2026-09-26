from dataclasses import dataclass

from inference.framework.virelai_controller import (
    compare_outcome,
    compile_rule_versions,
    decision_envelope_from_dict,
    revise_rule,
)
from tests.test_virelai_controller import _claim, _model, _observed_rule
from dataclasses import replace


@dataclass(frozen=True)
class Delta:
    row: int
    col: int


@dataclass(frozen=True)
class Transition:
    transition_id: int
    cell_deltas: tuple[Delta, ...]
    actor: str = "DUCK"
    action_id: int = 3
    action_name: str = "LEFT"
    acted_cell: tuple[int, int] | None = None
    geometry_changed: bool = False
    level_completed: bool = False
    game_over: bool = False
    run_complete: bool = False


def _envelope(expected="CHANGED", representation="CELLS", scope=None):
    scope = scope or {"representation": representation, "cells": [[1, 1]]}
    return decision_envelope_from_dict(
        {
            "focus_id": "F-1",
            "purpose": "TEST_RULE",
            "prediction": {"claim_id": "RV-1", "expected": expected, "scope": scope},
        },
        actions=("LEFT",),
        declared_at_transition=4,
    )


def test_remote_effect_does_not_turn_scoped_unchanged_into_contradiction():
    comparison = compare_outcome(
        _envelope(expected="UNCHANGED"),
        Transition(5, (Delta(4, 4),)),
    )
    assert comparison.outcome == "SUPPORTED"
    assert comparison.scoped_observation[0] == ("observed", "UNCHANGED")
    assert comparison.remote_observation == (("changed_cells", ((4, 4),)),)


def test_changed_scope_and_autonomous_change_are_separate():
    comparison = compare_outcome(
        _envelope(),
        Transition(5, (Delta(1, 1), Delta(4, 4))),
        autonomous_cells=((4, 4),),
    )
    assert comparison.outcome == "SUPPORTED"
    assert comparison.remote_observation == (("changed_cells", ((4, 4),)),)
    assert comparison.autonomous_observation == (("changed_cells", ((4, 4),)),)


def test_missing_worldline_resolution_is_indeterminate_not_whole_grid():
    comparison = compare_outcome(
        _envelope(scope={"representation": "WORLDLINE", "identifier": "O-1"}),
        Transition(5, (Delta(1, 1),)),
    )
    assert comparison.outcome == "INDETERMINATE"
    assert "not widened" in comparison.limitations[0]


def test_geometry_boundary_is_indeterminate():
    comparison = compare_outcome(_envelope(), Transition(5, (), geometry_changed=True))
    assert comparison.outcome == "INDETERMINATE"


def test_revision_is_append_only_and_retains_parent_lineage():
    model = replace(_model(), mechanics=(_observed_rule(),), claims=(_claim(),))
    parent = compile_rule_versions(model)[0]
    comparison = compare_outcome(_envelope(), Transition(5, (Delta(1, 1),)))
    child, event = revise_rule(parent, _envelope(), comparison)
    assert child is not parent
    assert child.version == parent.version + 1
    assert child.parent_rule_version_id == parent.rule_version_id
    assert child.witness_transition_ids == (3, 5, 7)
    assert parent.witness_transition_ids == (3, 7)
    assert event.resulting_rule_version_id == child.rule_version_id


def test_mismatched_executed_action_is_unmatched():
    comparison = compare_outcome(
        _envelope(),
        Transition(5, (Delta(1, 1),), action_id=4, action_name="RIGHT"),
    )
    assert comparison.outcome == "UNMATCHED"

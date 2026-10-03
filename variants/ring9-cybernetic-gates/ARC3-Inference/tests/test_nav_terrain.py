"""NAV integer terrain and target-conditioned reachability contracts.

Author: Sol (Alpha build seat), 2026-10-03.
"""
from types import SimpleNamespace

from inference.framework.nav_terrain import (
    TerrainPalette,
    analyze_terrain_reachability,
    infer_terrain_palette,
    plan_hypothesis_test,
)


def _outcome(before, after, action="ACTION1", probe_id="P1"):
    return {
        "probe_id": probe_id,
        "action": {"action": action},
        "shape_before": [len(before), len(before[0])],
        "site_transitions": [
            {
                "row": row,
                "col": col,
                "before": before[row][col],
                "after": after[row][col],
            }
            for row in range(len(before))
            for col in range(len(before[0]))
        ],
        "changed_cells": [
            {"row": row, "col": col, "before": before[row][col], "after": after[row][col]}
            for row in range(len(before))
            for col in range(len(before[0]))
            if before[row][col] != after[row][col]
        ],
    }


def _palette(floor=(1,), wall=(4,)):
    return TerrainPalette(
        schema="virelai-nav-terrain-palette-v1",
        palette_id="TP-test",
        floor_integers=tuple(floor),
        wall_integers=tuple(wall),
        floor_cells=(),
        wall_cells=(),
        floor_evidence=tuple((value, ("E-FLOOR",)) for value in floor),
        wall_evidence=tuple((value, ("E-WALL",)) for value in wall),
        action_coverage=("ACTION1",),
        limitations=(),
    )


def test_palette_learns_floor_from_exchange_and_wall_from_uniform_refusal():
    before = ((1, 1, 1, 1), (1, 9, 1, 4), (1, 1, 1, 1))
    after = ((1, 1, 1, 1), (1, 1, 9, 4), (1, 1, 1, 1))
    ego = SimpleNamespace(
        _lossless_outcomes=[_outcome(before, after)],
        evidence=[{"probe_id": "P1", "evidence_id": "E-MOVE"}],
    )
    palette = infer_terrain_palette(
        ego,
        current_grid=after,
        current_ego_cells=((1, 2),),
        bearings={"ACTION1": (0, 1)},
        refused={((1, 2), "ACTION1")},
        refused_evidence={((1, 2), "ACTION1"): "E-REFUSED"},
    )

    assert palette.floor_integers == (1,)
    assert palette.wall_integers == (4,)
    assert palette.floor_refs(1) == ("E-MOVE",)
    assert palette.wall_refs(4) == ("E-REFUSED",)


def test_configuration_map_requires_the_full_ego_footprint_to_fit_floor():
    # A one-cell corridor exists in column 2, but the 2-wide ego cannot occupy it.
    grid = (
        (4, 4, 4, 4, 4),
        (1, 1, 1, 4, 4),
        (4, 4, 1, 4, 4),
        (4, 4, 1, 4, 2),
        (4, 4, 4, 4, 4),
    )
    hypothesis = analyze_terrain_reachability(
        grid=grid,
        anchor=(1, 0),
        shape=frozenset({(0, 0), (0, 1)}),
        bearings={"RIGHT": (0, 1), "DOWN": (1, 0)},
        palette=_palette(),
        demonstrated_stands={(1, 0)},
        refused=(),
        target_entity_id="TARGET",
        target_cells={(3, 4)},
    )

    assert hypothesis.status == "PREDICTED_UNREACHABLE"
    assert (2, 2) not in hypothesis.valid_stands
    assert hypothesis.reachable_stands == ((1, 0), (1, 1))


def test_predicted_limit_produces_a_falsifier_action_not_a_verdict():
    grid = (
        (4, 4, 4, 4, 4),
        (1, 1, 4, 4, 2),
        (4, 4, 4, 4, 4),
    )
    bearings = {"LEFT": (0, -1), "RIGHT": (0, 1)}
    hypothesis = analyze_terrain_reachability(
        grid=grid,
        anchor=(1, 0),
        shape=frozenset({(0, 0)}),
        bearings=bearings,
        palette=_palette(),
        demonstrated_stands={(1, 0)},
        refused=(),
        target_entity_id="TARGET",
        target_cells={(1, 4)},
    )
    plan = plan_hypothesis_test(hypothesis, bearings=bearings, refused=())

    assert hypothesis.status == "PREDICTED_UNREACHABLE"
    assert plan is not None
    assert plan.experiment_kind == "ROUTE"
    assert plan.intent == "APPROACH"
    # Once at the closest floor stand the next plan presses the predicted wall.
    at_bridge = analyze_terrain_reachability(
        grid=grid,
        anchor=(1, 1),
        shape=frozenset({(0, 0)}),
        bearings=bearings,
        palette=_palette(),
        demonstrated_stands={(1, 0), (1, 1)},
        refused=(),
        target_entity_id="TARGET",
        target_cells={(1, 4)},
    )
    falsifier = plan_hypothesis_test(at_bridge, bearings=bearings, refused=())
    assert falsifier is not None
    assert falsifier.experiment_kind == "FALSIFIER"
    assert falsifier.landing == (1, 2)


def test_local_refusal_overrides_floor_class_without_poisoning_other_routes():
    grid = (
        (1, 1, 1),
        (1, 1, 2),
        (1, 1, 1),
    )
    bearings = {
        "UP": (-1, 0), "RIGHT": (0, 1), "DOWN": (1, 0), "LEFT": (0, -1),
    }
    hypothesis = analyze_terrain_reachability(
        grid=grid,
        anchor=(1, 0),
        shape=frozenset({(0, 0)}),
        bearings=bearings,
        palette=_palette(wall=()),
        demonstrated_stands={(1, 0)},
        refused={((1, 0), "RIGHT")},
        target_entity_id="TARGET",
        target_cells={(1, 2)},
    )

    assert hypothesis.status == "PREDICTED_REACHABLE"
    plan = plan_hypothesis_test(
        hypothesis, bearings=bearings, refused={((1, 0), "RIGHT")},
    )
    assert plan is not None
    assert plan.action in {"UP", "DOWN"}
    assert plan.experiment_kind == "ROUTE"

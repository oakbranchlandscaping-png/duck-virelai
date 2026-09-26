from __future__ import annotations

import json
from dataclasses import dataclass

from inference.framework.virelai_runtime import VirelaiRuntime
from virelai_golden.substrate.grid import as_grid
from virelai_golden.substrate.scan import scan_grid
from virelai_golden.roles.counter import Marginal, Press, counter_seal, target_controls_direction
from virelai_golden.substrate.scan import Region
from virelai_golden.weave.worldline import Worldline
from inference.framework.virelai_semantic.mechanics import (
    _action_independent_partner_ids,
    _effect_channels,
    _shared_control_bundles,
)
from virelai_golden.roles.lever import LeverPress, LeverRead
from virelai_golden.roles.infer import RoleRead
from inference.framework.virelai_semantic.view import SemanticLibraryView
from inference.framework.virelai_semantic.typing import classify_effect_channel


@dataclass
class FakeFrame:
    frame: list[list[list[int]]]
    game_id: str = "semantic-fixture"
    guid: str = "semantic-guid"
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 2
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 2, 6)


def _frame(layer: list[list[int]]) -> FakeFrame:
    return FakeFrame(frame=[layer])


def test_vendored_scan_keeps_exact_four_connected_partition_without_scipy():
    grid = as_grid([[1, 0, 0], [0, 1, 0], [2, 2, 0]])
    first = scan_grid(grid)
    second = scan_grid(grid)
    ones = [region for region in first if region.value == 1]
    assert len(ones) == 2
    assert sum(region.area for region in first) == 9
    assert first == second


def test_counter_seal_has_the_frozen_eight_press_floor():
    seven = Marginal(1, 7, 7, 7, 7, 0, 0, (-1,) * 7)
    eight = Marginal(1, 8, 8, 8, 8, 0, 0, (-1,) * 8)
    assert counter_seal(seven, frozenset()) is False
    assert counter_seal(eight, frozenset()) is True


def test_target_selected_opposite_directions_are_not_an_autonomous_counter():
    regions = [
        Region(index + 1, 7, frozenset((0, col) for col in range(area)))
        for index, area in enumerate((1, 2, 3, 2, 1))
    ]
    worldline = Worldline(9, tuple(enumerate(regions)), ())
    presses = [
        Press(0, 1, 6, 1, False),
        Press(1, 2, 6, 1, False),
        Press(2, 3, 6, 2, False),
        Press(3, 4, 6, 2, False),
    ]
    assert target_controls_direction(worldline, presses) is True


def test_opposed_effects_are_one_pair_bundle_without_claiming_hidden_variable():
    bundles = _shared_control_bundles(
        [1, 2],
        {
            (1, "PANEL-A"): [(1, 3), (2, 3)],
            (2, "PANEL-A"): [(3, -3), (4, -3)],
            (1, "PANEL-B"): [(1, -4), (2, -4)],
            (2, "PANEL-B"): [(3, 4), (4, 4)],
        },
        {1: "LEVER-A", 2: "LEVER-B"},
    )
    assert len(bundles) == 1
    assert bundles[0]["lever_a"] == "LEVER-A"
    assert len(bundles[0]["affected_targets"]) == 2
    assert bundles[0]["affected_targets"][0]["lever_a_witness_steps"] == [1, 2]
    assert "hidden variable" in bundles[0]["interpretation_limit"]


def test_action_independent_partner_requires_eight_presses_and_two_targets():
    presses = tuple(
        LeverPress(i, i + 1, 6, (1 if i % 2 else 2,), frozenset({(9, i)}), {99: 1})
        for i in range(8)
    )
    read = RoleRead({}, [], None, "fixture", {}, None, None,
                    LeverRead({}, presses, "fixture", 8, (), {}, {}))
    assert _action_independent_partner_ids(read) == {99}


def test_target_dependent_partner_is_not_action_independent():
    presses = tuple(
        LeverPress(i, i + 1, 6, (1 if i < 4 else 2,), frozenset({(9, i)}),
                   {99: 1} if i < 4 else {})
        for i in range(8)
    )
    read = RoleRead({}, [], None, "fixture", {}, None, None,
                    LeverRead({}, presses, "fixture", 8, (), {}, {}))
    assert _action_independent_partner_ids(read) == set()


def test_effect_channel_rejoins_reminted_targets_only_on_exact_footprint():
    common = {
        "action_id": 1, "integer_class_before": 9, "integer_class_after": 9,
        "cells_before": 20, "cells_after": 4, "cell_count_delta": -16,
        "anchor_before": [5, 3], "anchor_after": [9, 3],
        "affected_bbox": [5, 3, 10, 8],
    }
    rows = [
        {**common, "left_node": 10, "right_node": 11, "target": "W-A"},
        {**common, "left_node": 20, "right_node": 21, "target": "W-B"},
    ]
    channels = _effect_channels(rows)
    assert len(channels) == 1
    assert channels[0]["observations"] == 2
    assert channels[0]["target_worldlines"] == ["W-A", "W-B"]
    assert channels[0]["direction"] == "DECREASES_CELL_COUNT"


def test_typing_separates_uniform_transform_from_saturation_condition():
    rows = [
        {"left_node": 1, "right_node": 2, "before": [9, 20, [5, 3]], "after": [9, 4, [9, 3]]},
        {"left_node": 5, "right_node": 6, "before": [9, 20, [5, 3]], "after": [9, 4, [9, 3]]},
    ]
    reading = classify_effect_channel(rows)
    assert reading["mechanism"] == "UNIFORM_TRANSFORM"
    assert reading["condition"] == "UNMEASURED"


def test_typing_requires_two_complete_uninterrupted_periods_for_toggle():
    rows = [
        {"left_node": i, "right_node": i + 1, "before": [5, 1, [0, i % 2]],
         "after": [5, 1, [0, (i + 1) % 2]]}
        for i in range(4)
    ]
    reading = classify_effect_channel(rows)
    assert reading["mechanism"] == "TOGGLE"
    assert reading["period"] == 2


def test_typing_uses_controlled_uninterrupted_run_after_separated_discovery_click():
    rows = [
        {"left_node": 2, "right_node": 3, "before": [9, 36, [4, 4]],
         "after": [8, 36, [4, 4]]},
        {"left_node": 20, "right_node": 21, "before": [8, 36, [4, 4]],
         "after": [9, 36, [4, 4]]},
        {"left_node": 21, "right_node": 22, "before": [9, 36, [4, 4]],
         "after": [8, 36, [4, 4]]},
        {"left_node": 22, "right_node": 23, "before": [8, 36, [4, 4]],
         "after": [9, 36, [4, 4]]},
        {"left_node": 23, "right_node": 24, "before": [9, 36, [4, 4]],
         "after": [8, 36, [4, 4]]},
    ]
    reading = classify_effect_channel(rows)
    assert reading["mechanism"] == "TOGGLE"
    assert reading["period"] == 2
    assert reading["witness_count"] == 4
    assert reading["total_observations"] == 5


def test_typing_preserves_deterministic_state_table_without_inventing_a_period():
    rows = [
        {"left_node": 2, "right_node": 3, "before": [8, 36, [4, 4]],
         "after": [9, 36, [4, 4]]},
        {"left_node": 10, "right_node": 11, "before": [9, 36, [4, 4]],
         "after": [8, 36, [4, 4]]},
        {"left_node": 20, "right_node": 21, "before": [8, 36, [4, 4]],
         "after": [9, 36, [4, 4]]},
    ]
    reading = classify_effect_channel(rows)
    assert reading["mechanism"] == "DETERMINISTIC_STATE_TRANSITION"
    assert reading["condition"] == "ONLY_FOR_OBSERVED_INPUT_STATES"
    assert reading.get("period") is None
    assert len(reading["state_transitions"]) == 2


def test_shadow_compiler_unifies_record_entities_roles_and_joint_deltas(tmp_path, monkeypatch):
    monkeypatch.setenv("VIRELAI_SEMANTIC_SHADOW", "1")
    runtime = VirelaiRuntime(game_id="semantic-fixture", artifact_root=tmp_path)
    runtime.observe_initial(_frame([[1, 1, 0], [0, 2, 0]]))
    runtime.observe_transition(
        frame=_frame([[0, 1, 1], [0, 2, 0]]),
        action_id=2,
        action_name="RIGHT",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=_frame([[0, 1, 1], [0, 3, 0]]),
        action_id=6,
        action_name="MOUSE(row=1,col=1)",
        acted_cell=(1, 1),
        actor="DUCK",
        result={"level": 1},
    )
    runtime.flush()

    root = tmp_path / "semantic-fixture"
    library = json.loads((root / "semantic_library.json").read_text())
    assert library["schema"] == "virelai-semantic-library-shadow-v1"
    assert library["record_pristine"] is True
    assert library["observed_nodes"] == 3
    assert library["summary"]["model_exposed"] is False
    assert library["summary"]["mechanics_compiled"] is True
    assert library["summary"]["mechanics_validation"] == "NOT_RUN"
    assert library["summary"]["role_claim_validation"] == "NOT_RUN"
    assert len(library["segments"]) == 1

    segment = library["segments"][0]
    assert segment["first_node"] == 0 and segment["last_node"] == 2
    assert segment["control"]["kind"] in {"BODY", "POINTER"}
    assert len(segment["entities"]) > 0
    assert len(segment["joint_deltas"]) == 2
    first = segment["joint_deltas"][0]
    assert first["action_id"] == 2
    assert first["visible_cells_rewritten"] == 2
    moved = next(item for item in first["objects"] if item["integer_class_before"] == 1)
    assert moved["verb"] == "MOVE"
    assert moved["departed_sites"] == [[0, 0, 1, 0]]
    assert moved["entered_sites"] == [[0, 2, 0, 1]]
    assert "vacated" not in json.dumps(library).lower()
    mechanics = SemanticLibraryView(library).query("mechanics")
    assert mechanics["items"][0]["segment"] == segment["segment"]

    entity_rows = [json.loads(line) for line in (root / "semantic_entities.jsonl").read_text().splitlines()]
    worldline_rows = [json.loads(line) for line in (root / "worldline_dossiers.jsonl").read_text().splitlines()]
    delta_rows = [json.loads(line) for line in (root / "semantic_joint_deltas.jsonl").read_text().splitlines()]
    assert len(entity_rows) == library["summary"]["semantic_entities"]
    assert len(worldline_rows) == library["summary"]["entities"]
    assert len(delta_rows) == library["summary"]["joint_delta_rows"]


def test_shadow_is_off_by_default_and_never_changes_duck_surface(tmp_path, monkeypatch):
    monkeypatch.delenv("VIRELAI_SEMANTIC_SHADOW", raising=False)
    runtime = VirelaiRuntime(game_id="semantic-fixture", artifact_root=tmp_path)
    runtime.observe_initial(_frame([[0]]))
    before = runtime.query("help")
    runtime.flush()
    summary = json.loads((tmp_path / "semantic-fixture" / "summary.json").read_text())
    assert before["error"] is None
    assert summary["semantic_library_shadow"]["enabled"] is False
    assert not (tmp_path / "semantic-fixture" / "semantic_library.json").exists()

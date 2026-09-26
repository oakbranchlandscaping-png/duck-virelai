from __future__ import annotations

import json
from dataclasses import dataclass

from inference.framework.virelai_runtime import VirelaiRuntime, verify_frame_archive


@dataclass
class FakeFrame:
    frame: list[list[list[int]]]
    game_id: str = "fixture"
    guid: str = "fixture-guid"
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 2
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 2, 3, 4)


def _frame(value: int, *, completed: int = 0) -> FakeFrame:
    return FakeFrame(
        frame=[[[0, 0], [0, value]]],
        levels_completed=completed,
    )


def test_passive_runtime_records_exact_boundary_and_state_map(tmp_path):
    runtime = VirelaiRuntime(game_id="fixture", artifact_root=tmp_path)
    runtime.observe_initial(_frame(0))
    runtime.observe_transition(
        frame=_frame(1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=_frame(0),
        action_id=2,
        action_name="DOWN",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )

    overview = runtime.query("overview")
    assert overview["observed_through_step"] == 2
    assert overview["data"]["frames"] == 3
    assert overview["data"]["transitions"] == 2
    assert overview["data"]["visited_visible_states"] == 2
    assert "hidden or semantic world state" in overview["data"]["visible_state_limit"]

    states = runtime.query("states", {"limit": 10})
    assert len(states["data"]) == 2
    assert any(state["actions"] for state in states["data"])
    assert all(state["key_kind"] == "visible_observation_hash" for state in states["data"])
    assert runtime.transitions[0].target_first_seen is True
    assert runtime.transitions[1].target_seen_before is True

    before_counts = (len(runtime.capture), len(runtime.transitions))
    runtime.query("recent", {"limit": 1})
    assert (len(runtime.capture), len(runtime.transitions)) == before_counts
    assert runtime.journal.record_at(0).reconstruct_frame() == _frame(0).frame
    assert overview["data"]["capture_performance"]["p95_ms"] <= 25.0


def test_controller_outcome_is_joined_persisted_and_retrievable(tmp_path):
    runtime = VirelaiRuntime(game_id="controller", artifact_root=tmp_path)
    runtime.observe_initial(_frame(0))
    focus = runtime.query("controller")["data"]["focus"]
    runtime.observe_transition(
        frame=_frame(1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    response = runtime.query(
        "controller_outcome",
        {
            "decision_id": "D-live",
            "actions": [{"action": "UP"}],
            "decision": {
                "focus_id": focus["focus_id"],
                "purpose": "TEST_RULE",
                "prediction": {
                    "expected": "CHANGED",
                    "scope": {
                        "representation": "CELLS",
                        "cells": [[1, 1]],
                    },
                },
            },
        },
    )
    assert response["error"] is None
    assert response["data"]["comparison"]["decision_id"] == "D-live"
    assert response["data"]["comparison"]["transition_id"] == 1
    assert response["data"]["comparison"]["outcome"] == "SUPPORTED"

    history = runtime.query("controller_history")
    assert history["data"]["outcomes_total"] == 1
    assert history["data"]["revisions_total"] == 1
    artifact = tmp_path / "controller"
    assert len((artifact / "outcome_comparisons.jsonl").read_text().splitlines()) == 1
    assert len((artifact / "revision_events.jsonl").read_text().splitlines()) == 1


def test_physics_query_is_bounded_read_only_player_view(tmp_path):
    runtime = VirelaiRuntime(game_id="fixture", artifact_root=tmp_path)
    runtime.observe_initial(_frame(0))
    before_counts = (len(runtime.capture), len(runtime.transitions))

    response = runtime.query("physics", {"level": 1, "limit": 2})

    assert response["error"] is None
    assert response["data"]["schema"] == "virelai-physics-manual-v1"
    assert "VIRELAI PHYSICS GRAMMAR" in response["data"]["text"]
    assert response["data"]["mechanics_returned"] <= 2
    assert (len(runtime.capture), len(runtime.transitions)) == before_counts
    assert "physics" in runtime.query("help")["data"]["operations"]

    runtime.observe_transition(
        frame=_frame(1), action_id=1, action_name="UP", acted_cell=None,
        actor="DUCK", result={"level": 1},
    )
    cached = runtime.query("physics", {"level": 1})
    assert cached["freshness"] == "model-prefix"
    assert cached["compiled_through_step"] == 0
    assert cached["data"]["pending_transitions"] == 1

    refreshed = runtime.query("physics", {"level": 1, "fresh": True})
    assert refreshed["freshness"] == "model-current"
    assert refreshed["compiled_through_step"] == 1
    assert refreshed["data"]["pending_transitions"] == 0

    runtime.observe_transition(
        frame=_frame(2, completed=1), action_id=6, action_name="MOUSE(row=1, col=1)",
        acted_cell=(1, 1), actor="DUCK", result={"level": 2, "level_completed": True},
    )
    boundary = runtime.query("physics", {"level": 1})
    assert boundary["freshness"] == "model-current"
    assert boundary["compiled_through_step"] == 2


def test_win_transition_and_artifacts_are_preserved(tmp_path):
    runtime = VirelaiRuntime(game_id="fixture", artifact_root=tmp_path)
    runtime.observe_initial(_frame(0))
    runtime.observe_transition(
        frame=_frame(2, completed=1),
        action_id=6,
        action_name="MOUSE(row=1, col=1)",
        acted_cell=(1, 1),
        actor="DUCK",
        result={"level": 2, "level_completed": True},
    )
    wins = runtime.query("wins")
    assert len(wins["data"]) == 1
    assert wins["data"][0]["acted_cell"] == (1, 1)
    assert wins["data"][0]["cell_delta_count"] == 1
    assert wins["data"][0]["cell_deltas"] == [
        {"row": 1, "col": 1, "before_class": 0, "after_class": 2}
    ]

    runtime.flush()
    artifact_dir = tmp_path / "fixture"
    assert json.loads((artifact_dir / "summary.json").read_text())["level_wins"] == 1
    assert len((artifact_dir / "events.jsonl").read_text().splitlines()) == 2
    assert len((artifact_dir / "queries.jsonl").read_text().splitlines()) == 1
    frame_index = [
        json.loads(line) for line in (artifact_dir / "frames.jsonl").read_text().splitlines()
    ]
    assert [item["node_index"] for item in frame_index] == [0, 1]
    assert [item["archive_offset"] for item in frame_index] == [0, 4]
    assert (artifact_dir / "frames.bin").read_bytes() == bytes([0, 0, 0, 0, 0, 0, 0, 2])
    assert not (artifact_dir / "capture.pkl.gz").exists()
    summary = json.loads((artifact_dir / "summary.json").read_text())
    assert summary["archive"]["encoding"] == "uint8"
    assert summary["archive"]["bytes"] == 8
    assert verify_frame_archive(artifact_dir)["passed"] is True


def test_run_stem_separates_pass_archives(tmp_path):
    first = VirelaiRuntime(
        game_id="fixture",
        run_stem="fixture_p0",
        artifact_root=tmp_path,
    )
    second = VirelaiRuntime(
        game_id="fixture",
        run_stem="fixture_p1",
        artifact_root=tmp_path,
    )
    first.observe_initial(_frame(0))
    second.observe_initial(_frame(1))
    first.flush()
    second.flush()

    first_summary = json.loads((tmp_path / "fixture_p0" / "summary.json").read_text())
    second_summary = json.loads((tmp_path / "fixture_p1" / "summary.json").read_text())
    assert first_summary["game_id"] == second_summary["game_id"] == "fixture"
    assert first_summary["run_stem"] == "fixture_p0"
    assert second_summary["run_stem"] == "fixture_p1"
    assert (tmp_path / "fixture_p0" / "frames.bin").read_bytes() != (
        tmp_path / "fixture_p1" / "frames.bin"
    ).read_bytes()


def test_multilayer_revisit_self_loop_and_geometry_are_literal(tmp_path):
    runtime = VirelaiRuntime(game_id="geometry", artifact_root=tmp_path)
    initial = FakeFrame(frame=[[[9]], [[0, 0], [0, 0]]])
    changed = FakeFrame(frame=[[[8]], [[0, 1], [0, 0]]])
    resized = FakeFrame(frame=[[[7]], [[0, 1, 0], [0, 0, 0]]])
    runtime.observe_initial(initial)
    runtime.observe_transition(
        frame=changed,
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=changed,
        action_id=0,
        action_name="TICK",
        acted_cell=None,
        actor="SYSTEM",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=initial,
        action_id=2,
        action_name="DOWN",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=resized,
        action_id=6,
        action_name="MOUSE(row=0, col=1)",
        acted_cell=(0, 1),
        actor="DUCK",
        result={"level": 1},
    )

    first, tick, revisit, geometry = runtime.transitions
    assert first.cell_deltas[0].before_class == 0
    assert first.cell_deltas[0].after_class == 1
    assert tick.visible_self_loop is True
    assert tick.target_seen_before is True
    assert revisit.target_seen_before is True
    assert geometry.geometry_changed is True
    assert geometry.before_shape == (2, 2)
    assert geometry.after_shape == (2, 3)
    assert geometry.cell_delta_count == 0
    assert geometry.cell_deltas == ()
    assert runtime.journal.record_at(1).reconstruct_frame() == changed.frame

    runtime.flush()
    events = [
        json.loads(line)
        for line in (tmp_path / "geometry" / "events.jsonl").read_text().splitlines()
    ]
    persisted_geometry = events[-1]
    assert persisted_geometry["geometry_changed"] is True
    assert persisted_geometry["cell_deltas"] == []
    assert verify_frame_archive(tmp_path / "geometry")["passed"] is True


def test_canonical_delta_is_complete_while_query_view_is_bounded(tmp_path):
    runtime = VirelaiRuntime(game_id="bounded", artifact_root=tmp_path)
    zeros = [[0] * 10 for _ in range(10)]
    ones = [[1] * 10 for _ in range(10)]
    runtime.observe_initial(FakeFrame(frame=[zeros]))
    runtime.observe_transition(
        frame=FakeFrame(frame=[ones]),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )

    response = runtime.query("transition", {"step": "last"})
    assert response["truncated"] is True
    assert response["data"]["cell_delta_count"] == 100
    assert len(response["data"]["cell_deltas"]) == 64
    persisted = [
        json.loads(line)
        for line in (tmp_path / "bounded" / "events.jsonl").read_text().splitlines()
    ][-1]
    assert persisted["cell_delta_count"] == 100
    assert len(persisted["cell_deltas"]) == 100

    recent = runtime.query("recent")
    assert recent["schema"] == "virelai-recent-v1"
    assert recent["truncated"] is True
    assert recent["data"]["cell_delta_count"] == 100
    assert recent["data"]["cell_deltas_returned"] == 32
    assert len(recent["data"]["cell_deltas"]) == 32
    assert recent["data"]["cell_deltas"][0] == [0, 0, 0, 1]


def test_effects_ledger_reports_frequency_magnitude_and_context_dependence(tmp_path):
    runtime = VirelaiRuntime(game_id="effects", artifact_root=tmp_path)
    zero = FakeFrame(frame=[[[0, 0], [0, 0]]])
    one = FakeFrame(frame=[[[0, 0], [0, 1]]])
    full = FakeFrame(frame=[[[2, 2], [2, 2]]])
    runtime.observe_initial(zero)

    # The same visible pre-state and action first self-loop, then diverge.
    runtime.observe_transition(
        frame=zero,
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=one,
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=full,
        action_id=6,
        action_name="MOUSE(row=0, col=0)",
        acted_cell=(0, 0),
        actor="DUCK",
        result={"level": 1},
    )

    response = runtime.query("effects")
    assert response["schema"] == "virelai-effects-v1"
    assert response["data"]["rankings"]["largest_effects"][0] == "MOUSE(row=0, col=0)"
    entries = {item["action"]: item for item in response["data"]["entries"]}
    up = entries["UP"]
    assert up["presses"] == 2
    assert up["changed"] == 1
    assert up["unchanged"] == 1
    assert up["cells_changed"] == {"min": 0, "median": 0.5, "max": 1}
    assert up["mixed_outcomes"] is True
    assert up["same_visible_state_divergences"] == 1
    assert response["data"]["note"].startswith("Counts of observed visible outcomes")


def test_effects_excludes_system_transitions_and_is_current_level_scoped(tmp_path):
    runtime = VirelaiRuntime(game_id="scope", artifact_root=tmp_path)
    runtime.observe_initial(_frame(0))
    runtime.observe_transition(
        frame=_frame(1),
        action_id=0,
        action_name="TICK",
        acted_cell=None,
        actor="SYSTEM",
        result={"level": 1},
    )
    runtime.observe_transition(
        frame=_frame(2, completed=1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 2, "level_completed": True},
    )

    response = runtime.query("effects")
    assert response["data"]["level"] == 2
    assert response["data"]["entries"] == []
    assert response["data"]["total_action_keys"] == 0

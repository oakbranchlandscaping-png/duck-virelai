from __future__ import annotations

import json
from dataclasses import dataclass

from inference.framework.virelai_runtime import VirelaiRuntime


@dataclass
class Frame:
    frame: list[list[list[int]]]
    game_id: str = "win-fixture"
    guid: str = "guid"
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 2
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 2, 3, 4, 6)


def layer(value: int) -> list[list[int]]:
    return [[0, 0], [0, value]]


def test_nonterminal_win_preserves_outgoing_render_and_successor_spawn(tmp_path):
    runtime = VirelaiRuntime(game_id="win-fixture", artifact_root=tmp_path)
    runtime.observe_initial(Frame([layer(0)]))
    runtime.observe_transition(
        frame=Frame([layer(7), layer(2)], levels_completed=1),
        action_id=6,
        action_name="MOUSE(row=1, col=1)",
        acted_cell=(1, 1),
        actor="CAPTAIN",
        result={"level": 2, "level_completed": True},
    )
    capsule = runtime.win_capsules[0]
    assert capsule.actor == "CAPTAIN"
    assert capsule.completed_level == 1
    assert capsule.pre_win_ref.node_index == 0
    assert capsule.winning_render_ref.layer_index == 0
    assert capsule.successor_spawn_ref.layer_index == 1
    assert capsule.level_root_ref == capsule.attempt_root_ref
    assert capsule.evidence_friction == ()
    lesson = runtime.query("lesson", {"level": 1})
    assert lesson["error"] is None
    assert lesson["data"]["completed_level"] == 1
    assert lesson["data"]["winning_action_kind"] == "MOUSE"
    assert [item["query"] for item in lesson["data"]["available"]] == [
        "virelai('mechanics', level=1)",
        "virelai('win', level=1)",
        "virelai('carry', level=1)",
    ]
    full = runtime.query("lesson", {"level": 1, "detail": "full"})
    assert full["data"]["what_final_action_changed"]["literal_rewrites"] == [
        {"before_class": 0, "after_class": 7, "cell_count": 1}
    ]
    assert runtime.query("carry", {"level": 1})["data"]["new_level"] == 2
    focused_win = runtime.query("win", {"level": 1})
    mechanics = runtime.query("mechanics", {"level": 1})
    assert mechanics["data"]["status"] == "OBSERVED_MECHANICS"
    assert focused_win["data"]["winning_action"] == "MOUSE(row=1, col=1)"
    assert len(json.dumps(lesson["data"])) < len(json.dumps(full["data"]))
    evidence_id = focused_win["data"]["evidence_transition_ids"][-1]
    assert runtime.query("evidence", {"transition_id": evidence_id})["data"]["level_completed"] is True

    runtime.flush()
    rows = (tmp_path / "win-fixture" / "win_capsules.jsonl").read_text().splitlines()
    assert len(rows) == 1
    saved = json.loads(rows[0])
    assert saved["winning_render_ref"]["sha256"] == capsule.winning_render_ref.sha256
    summary = json.loads((tmp_path / "win-fixture" / "summary.json").read_text())
    assert summary["win_capsule_archive"]["records"] == 1
    assert summary["win_capsule_archive"]["model_exposed"] is False


def test_single_layer_ascent_records_missing_evidence_instead_of_inventing_it(tmp_path):
    runtime = VirelaiRuntime(game_id="single", artifact_root=tmp_path)
    runtime.observe_initial(Frame([layer(0)], game_id="single"))
    runtime.observe_transition(
        frame=Frame([layer(2)], game_id="single", levels_completed=1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 2, "level_completed": True},
    )
    capsule = runtime.win_capsules[0]
    assert capsule.winning_render_ref is None
    assert capsule.successor_spawn_ref is not None
    assert "MISSING_OUTGOING_WIN_RENDER" in capsule.evidence_friction
    assert "MISSING_RENDER" in runtime.level_lessons[0].limitations


def test_reset_replaces_attempt_root_but_not_level_root(tmp_path):
    runtime = VirelaiRuntime(game_id="reset", artifact_root=tmp_path)
    runtime.observe_initial(Frame([layer(0)], game_id="reset"))
    runtime.observe_transition(
        frame=Frame([layer(3)], game_id="reset", full_reset=True),
        action_id=0,
        action_name="RESET",
        acted_cell=None,
        actor="SYSTEM_RESET",
        result={"level": 1, "game_over": True},
    )
    runtime.observe_transition(
        frame=Frame([layer(8), layer(1)], game_id="reset", levels_completed=1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 2, "level_completed": True},
    )
    capsule = runtime.win_capsules[0]
    assert capsule.level_root_ref.node_index == 0
    assert capsule.attempt_root_ref.node_index == 1


def test_terminal_win_has_no_successor_and_game_over_is_not_a_win(tmp_path):
    runtime = VirelaiRuntime(game_id="terminal", artifact_root=tmp_path)
    runtime.observe_initial(Frame([layer(0)], game_id="terminal", win_levels=1))
    runtime.observe_transition(
        frame=Frame([layer(4)], game_id="terminal", win_levels=1),
        action_id=2,
        action_name="DOWN",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1, "game_over": True},
    )
    assert runtime.win_capsules == []
    runtime.observe_transition(
        frame=Frame([layer(9)], game_id="terminal", levels_completed=1, win_levels=1),
        action_id=1,
        action_name="UP",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1, "run_complete": True},
    )
    capsule = runtime.win_capsules[0]
    assert capsule.terminal is True
    assert capsule.winning_render_ref.layer_index == 0
    assert capsule.successor_spawn_ref is None


def test_lesson_is_unavailable_before_first_observed_win(tmp_path):
    runtime = VirelaiRuntime(game_id="prewin", artifact_root=tmp_path)
    runtime.observe_initial(Frame([layer(0)], game_id="prewin"))
    response = runtime.query("lesson", {"level": 1})
    assert response["data"] is None
    assert "only after an observed win" in response["error"]
    assert runtime.query("lessons")["data"] == []

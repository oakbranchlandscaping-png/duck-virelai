from tools.compile_post_win_grammars import (
    _minimal_separator, compile_post_win, render_post_win, write_post_win,
)


def test_post_win_grammar_is_level_bounded_and_actor_independent():
    library = {
        "game_id": "fixture",
        "segments": [
            {"level": 1, "control": {"kind": "POINTER"}, "lever_mechanics": {
                "levers": [], "reactive_controls": [], "shared_controls": [],
                "masked_action_independent_worldlines": [],
            }},
            {"level": 2, "control": {"kind": "BODY"}, "lever_mechanics": {
                "levers": [], "reactive_controls": [], "shared_controls": [],
                "masked_action_independent_worldlines": [],
            }},
        ],
    }
    capsules = [{
        "completed_level": 1, "actor": "DUCK", "action_name": "ACTION6",
        "acted_cell": [3, 4], "transition_id": 9,
    }]
    outputs = compile_post_win(library, capsules)
    assert len(outputs) == 1
    assert [item["level"] for item in outputs[0]["levels"]] == [1]
    assert outputs[0]["levels"][0]["observed_win"]["actor"] == "DUCK"
    text = render_post_win(outputs[0])
    assert "Winning action: ACTION6" in text
    assert "World type: CLICK" in text


def test_unwon_game_writes_empty_index_without_requiring_capsule_file(tmp_path):
    (tmp_path / "semantic_library.json").write_text(
        '{"game_id":"unwon","segments":[]}', encoding="utf-8"
    )
    output = tmp_path / "post_win"
    assert write_post_win(tmp_path, output) == []
    assert (output / "index.json").read_text(encoding="utf-8") == "[]"


def test_separator_abstains_when_explanation_needs_more_than_three_regions():
    win = [1, 1, 1, 1]
    failed = [
        [0, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 0],
    ]
    assert _minimal_separator(win, failed) is None

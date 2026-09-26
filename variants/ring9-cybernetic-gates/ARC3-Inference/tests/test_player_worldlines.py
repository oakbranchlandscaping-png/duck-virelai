import json

from tools.render_player_worldlines import compile_view, render_markdown


def test_player_view_prioritizes_targeted_and_preserves_observational_limits(tmp_path):
    tracks = [
        {
            "track_id": 1, "display_id": "W001-###001", "level": 1,
            "born_node": 0, "last_seen_node": 2, "end_reason": "RUN_CLOSED",
            "observations": [
                {"class_id": 4, "cell_count": 2, "bbox": [0, 0, 0, 1]},
                {"class_id": 4, "cell_count": 2, "bbox": [0, 1, 0, 2]},
                {"class_id": 4, "cell_count": 2, "bbox": [0, 2, 0, 3]},
            ],
            "stitches": [
                {"from_node": 0, "to_node": 1, "verb": "MOVE"},
                {"from_node": 1, "to_node": 2, "verb": "MOVE"},
            ],
        },
        {
            "track_id": 2, "display_id": "W001-###002", "level": 1,
            "born_node": 0, "last_seen_node": 2, "end_reason": "RUN_CLOSED",
            "observations": [
                {"class_id": 3, "cell_count": 9, "bbox": [0, 0, 2, 2]},
                {"class_id": 3, "cell_count": 9, "bbox": [0, 0, 2, 2]},
                {"class_id": 3, "cell_count": 9, "bbox": [0, 0, 2, 2]},
            ],
            "stitches": [
                {"from_node": 0, "to_node": 1, "verb": "STILL"},
                {"from_node": 1, "to_node": 2, "verb": "STILL"},
            ],
        },
    ]
    (tmp_path / "continuity_tracks.json").write_text(json.dumps(tracks))
    (tmp_path / "acted_on.jsonl").write_text(json.dumps({
        "worldline_id": 1, "status": "RESOLVED", "issued_from_node": 0,
        "result_node": 1,
    }) + "\n")

    view = compile_view(tmp_path, level=1, limit=2)
    assert view["worldlines"][0]["handle"] == "W001-###001"
    assert view["worldlines"][0]["targeted"]["observed_self_responses"] == {"MOVE": 1}
    assert view["worldlines"][0]["targeted"]["coincident_worldline_changes"] == [
        {
            "handle": "W001-###001",
            "observed_forms_after_targeting": {"MOVE": 1},
            "observations": 1,
        }
    ]
    assert view["roles_inferred"] is False
    text = render_markdown(view)
    assert "No ego, lever, counter, cause, or objective labels are inferred." in text

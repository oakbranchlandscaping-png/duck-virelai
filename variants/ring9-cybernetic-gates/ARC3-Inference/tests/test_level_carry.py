from tools.compile_level_carry import _components, _normalized_shape, render_level_carry


def test_shape_is_position_and_scale_invariant():
    assert _normalized_shape({(0, 0), (0, 1), (1, 0), (1, 1)}) == _normalized_shape(
        {(5 + r, 7 + c) for r in range(4) for c in range(4)}
    )


def test_components_are_exact_integer_class_regions():
    rows = [[0, 2, 2], [0, 0, 2], [2, 0, 0]]
    found = _components(rows, {2})
    assert sorted(item["cell_count"] for item in found) == [1, 3]
    assert all(item["integer_class"] == 2 for item in found)


def test_player_render_marks_correspondence_as_untested():
    item = {"new_level": 2, "completed_level": 1,
            "completed_level_grammar": {"game": "x", "basis": "observed", "levels": [{
                "level": 1, "world_mode": "POINTER", "independent_process_observed": False,
                "remote_levers": [], "self_reactive_controls": [], "shared_control_relations": [],
                "still_unknown": [], "observed_win": {"actor": "DUCK", "action": "A6",
                    "acted_cell": [1, 2], "transition_id": 3, "causal_limit": "unknown"},
                "win_explanation": {"status": "NO_EARLIER_EXACT_ACTION_CONTRAST",
                    "distinguishing_conditions": [], "causal_limit": "not proved"},
            }]}, "candidate_type_correspondences": [], "carry_rule": "Prior, not guarantee.",
            "must_relearn": ["mechanics"]}
    text = render_level_carry(item)
    assert "Do not force one" in text
    assert "Prior, not guarantee" in text

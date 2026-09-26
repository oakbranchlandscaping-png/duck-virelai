from __future__ import annotations

from inference.framework.virelai_memory_card import CARD_SCHEMA, build_memory_card


def test_memory_card_is_bounded_player_index_with_expansion_handles():
    card = build_memory_card(
        entered_level=2,
        completed_level=1,
        world_mode="CLICK",
        win={
            "winning_action": "MOUSE(row=32, col=5)",
            "acted_cell": [32, 5],
            "status": "MINIMAL_OBSERVED_SEPARATOR",
            "earlier_same_action_failures": 5,
            "distinguishing_conditions": [{"region": [10, 10, 20, 20]}],
        },
        mechanics={
            "controls": [{
                "name": "Lever A",
                "kind": "REMOTE_LEVER",
                "location": [29, 2, 36, 7],
                "mechanism": "cycles a shared tile system forward",
                "affected_regions": [[19, 12, 46, 51]],
                "observations": 6,
            }],
            "shared_mechanics": [{
                "kind": "OPPOSING_EFFECTS",
                "controls": ["Lever A", "Lever B"],
                "relationship": "opposing controls reverse common visible effects",
                "affected_regions": [[19, 12, 46, 51]],
            }],
        },
        carry={
            "candidate_controls": [{
                "prior_control": "Lever A",
                "prior_location": [29, 2, 36, 7],
                "candidate_locations": [[30, 2, 37, 7]],
            }]
        },
    )

    assert card["schema"] == CARD_SCHEMA
    assert "VIRELAI WORLD MEMORY — LEVEL 2" in card["text"]
    assert "MOUSE(row=32, col=5)" in card["text"]
    assert "virelai('win', level=1)" in card["text"]
    assert "virelai('mechanics', level=1)" in card["text"]
    assert "virelai('carry', level=1)" in card["text"]
    assert "opposing controls reverse" in card["text"]
    assert "T-" not in card["text"]
    assert "required plan" in card["text"]
    assert len(card["text"].encode()) < 3000


def test_display_limit_is_not_reported_as_missing_knowledge():
    card = build_memory_card(
        entered_level=2,
        completed_level=1,
        world_mode="CLICK",
        win={"winning_action": "MOUSE(row=1, col=2)"},
        mechanics={
            "controls": [{"name": f"C{i}"} for i in range(4)],
            "controls_total": 9,
            "shared_mechanics": [],
        },
        carry={},
    )
    assert card["display"]["controls_omitted"] == 5
    assert "5 additional established mechanic record(s) omitted" in card["text"]


def test_unlocalized_raw_control_is_retained_only_behind_expansion():
    card = build_memory_card(
        entered_level=2,
        completed_level=1,
        world_mode="NAV",
        win={"winning_action": "LEFT"},
        mechanics={
            "controls": [{
                "name": "Malformed raw label",
                "location": None,
                "mechanism": "remote effect",
                "presentation_ready": False,
            }],
            "controls_total": 1,
        },
        carry={},
    )
    assert not card["known_mechanics"]
    assert "Malformed raw label" not in card["text"]
    assert "1 additional raw control record(s)" in card["text"]
    assert "virelai('mechanics', level=1)" in card["text"]


def test_memory_card_bounds_every_expandable_summary_section():
    controls = [{
        "name": f"Lever {index}",
        "kind": "REMOTE_LEVER",
        "location": [index, 0, index, 0],
        "mechanism": "changes region",
        "affected_regions": [[0, 0, 1, 1]] * 5,
        "observations": 1,
    } for index in range(20)]
    candidates = [{
        "prior_control": f"Lever {index}",
        "prior_location": [index, 0, index, 0],
        "candidate_locations": [[index, col, index, col] for col in range(8)],
    } for index in range(20)]
    card = build_memory_card(
        entered_level=2,
        completed_level=1,
        world_mode="UNKNOWN",
        win={"winning_action": "RIGHT", "distinguishing_conditions": [{}] * 10},
        mechanics={"controls": controls},
        carry={"candidate_controls": candidates},
    )
    assert len(card["known_mechanics"]) == 4
    assert len(card["level_comparison"]) == 4
    assert all(len(row["affected_regions"]) <= 2 for row in card["known_mechanics"])
    assert all(len(row["candidate_locations"]) <= 3 for row in card["level_comparison"])

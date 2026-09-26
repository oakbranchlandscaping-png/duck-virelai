from tools.render_physics_grammar import compile_grammar, render_markdown


def test_player_grammar_reports_self_toggle_without_worldline_details():
    library = {
        "game_id": "fixture",
        "segments": [{
            "level": 1,
            "control": {"kind": "POINTER"},
            "lever_mechanics": {
                "levers": [],
                "masked_action_independent_worldlines": [9, 10],
                "shared_controls": [],
                "reactive_controls": [{
                    "control": "internal-handle",
                    "visible": {"bbox": [2, 3, 7, 8], "cells": 36, "integer_classes": [8]},
                    "self_effect_channels": [{
                        "observations": 8,
                        "typing": {
                            "mechanism": "TOGGLE", "period": 2,
                            "status": "EXACT_RECURRENCE_CONFIRMED",
                        },
                        "transitions": [
                            {"before": [8, 36, [2, 3]], "after": [9, 36, [2, 3]]},
                            {"before": [9, 36, [2, 3]], "after": [8, 36, [2, 3]]},
                        ],
                    }],
                }],
            },
        }],
    }
    grammar = compile_grammar(library)
    control = grammar["levels"][0]["self_reactive_controls"][0]
    assert control["observed_rule"]["mechanism"] == "TOGGLE"
    assert control["observed_rule"]["class_rewrites"] == [[8, 9], [9, 8]]
    text = render_markdown(grammar)
    assert "Control A" in text
    assert "TOGGLE with period 2" in text
    assert "internal-handle" not in text

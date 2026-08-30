"""WO-RING6-01 SS4 -- RED THEN GREEN guards for the opening probe and the card.

Each guard here was broken, observed failing, and restored before this file was
committed (session record: the mutation, the failing assertion text, and the
restore, for all five SS4 rows except the B.3 hazard, which has its own file --
test_ring6_action_data_hazard.py). This file is the permanent GREEN form."""
import ast
import os
import sys

_HERE = os.path.dirname(__file__)
_SOLVER = os.path.join(_HERE, "..", "ARC3-Inference", "inference", "framework", "solver.py")
_CARD_MODULE_DIR = os.path.join(_HERE, "..", "ARC3-Inference", "inference", "framework")

sys.path.insert(0, _CARD_MODULE_DIR)
from virelai_field_card_v6 import render_field_card  # noqa: E402

_SEVEN_HEADERS = [
    "§1 — What Am I?", "§2 — What Do I See?", "§3 — What Can I Do?",
    "§4 — What Changes When I Act?", "§5 — What Don't I Know?",
    "§6 — How Much Time Do I Have?", "§7 — What Have I Tried?",
]


def _function_source(src: str, name: str) -> str:
    tree = ast.parse(src, filename=_SOLVER)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            seg = ast.get_source_segment(src, node)
            assert seg is not None
            return seg
    raise AssertionError(f"function {name!r} not found")


def test_opening_ran():
    """SS4 row 1 -- play() must call _virelai_opening(). Broken by removing the
    call site and confirming _function_source(play).find fails; restored."""
    with open(_SOLVER, "r", encoding="utf-8") as f:
        src = f.read()
    play_body = _function_source(src, "play")
    assert "self._virelai_opening()" in play_body, (
        "play() no longer calls _virelai_opening() -- the captain's opening "
        "probe would never run."
    )


def test_empty_captain_weave_renders_all_seven_sections_none_blank():
    """SS4 row 2 -- an empty dict (captain found/sealed nothing) must still
    render all seven sections with v3.5's fallback sentences. Broken by
    returning a whitespace-only string from a section renderer (passes the
    module's own `fn(d) or _FALLBACK[key]` truthy-OR net but strips blank);
    caught by checking .strip(), not truthiness."""
    card = render_field_card({}, game_id="TEST")
    text = str(card)
    lines = text.split("\n")
    for header in _SEVEN_HEADERS:
        assert header in text, f"missing header: {header}"
        idx = lines.index(header)
        body = lines[idx + 1]
        assert body.strip(), f"blank body after {header!r}: {body!r}"


def test_click_world_nothing_sealed_states_god_mode_never_invents_a_body():
    """SS4 row 3 -- a CLICK world (ego_mode=GOD_MODE) with an empty ego dict
    (nothing sealed) must state God Mode honestly and never fall into the
    EMBODIED branch's invented-body sentence. Broken by appending the
    EMBODIED body sentence onto the GOD_MODE branch directly."""
    card = render_field_card({"ego_mode": "GOD_MODE", "ego": {}}, game_id="TEST")
    text = str(card)
    assert "God Mode" in text
    assert "You have a body" not in text


def test_unknown_ego_mode_also_never_invents_a_body():
    """Negative control alongside the CLICK-world guard: an UNKNOWN ego_mode
    (nothing classified at all, not even CLICK vs EMBODIED) must say so
    honestly rather than defaulting toward either interpretation."""
    card = render_field_card({}, game_id="TEST")
    text = str(card)
    assert "not been determined yet" in text
    assert "You have a body" not in text


def test_firewall_no_hash_id_or_colour_leaks_into_rendered_prose():
    """SS4 row 5 -- worldline dicts carrying a `###` id and fabricated
    colour/class fields (the shape solver.py's _ring6_worldline_rows
    actually produces, plus fields nothing should ever add) must never
    surface in the rendered text. Broken by having _render_lever_section
    print the raw `id` field of every worldline it sees."""
    worldlines = [
        {"id": "###5", "cells": (4, 9), "anchor": (12, 30), "role": "LEVER",
         "seal": "FIRM", "fields": (), "cov": 10, "revisit": 2, "ticks": 3,
         "multi": 0, "colour": "red", "color": "blue", "class": 7},
        {"id": "###12", "cells": (1, 1), "anchor": (0, 0), "role": "GROUND",
         "seal": "FIRM", "fields": ("GROUND",), "cov": 5, "revisit": 0,
         "ticks": 1, "multi": 0, "colour": "green", "class_id": 3},
    ]
    d = {"worldlines": worldlines, "visual_objects": 14, "grid": (64, 64),
         "ego_mode": "EMBODIED", "ego": {"footprint": 4, "sealed": ["###5"]},
         "world_type": "NAV"}
    text = str(render_field_card(d, game_id="TEST"))
    for needle in ("###5", "###12", "red", "blue", "green", "colour", "color"):
        assert needle not in text, f"firewall leak: {needle!r} in rendered card"
    import re
    assert not re.search(r"\bclass\s*\d", text, re.IGNORECASE), (
        "firewall leak: a 'class N' pattern reached rendered prose"
    )
    assert not re.search(r"###\d+", text), (
        "firewall leak: a '###N' pattern reached rendered prose"
    )

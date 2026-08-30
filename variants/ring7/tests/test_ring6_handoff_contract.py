"""Ring 6's executable handoff contract.

These tests are dependency-free.  They grade the package topology, the prompt
boundary and the pure renderer without importing arcengine, TAAF or V4.
"""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARC_ROOT = HERE.parent / "ARC3-Inference"
SOLVER = ARC_ROOT / "inference" / "framework" / "solver.py"
PROMPTS = ARC_ROOT / "inference" / "agent" / "prompts.py"
RENDERER = ARC_ROOT / "inference" / "framework" / "virelai_field_card_v6.py"
PROBE_CONTRACT = ARC_ROOT / "inference" / "framework" / "virelai_probe_contract.py"
V4 = ARC_ROOT / "virelai_v4"


def _load_renderer():
    spec = importlib.util.spec_from_file_location("ring6_field_card", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_probe_contract():
    spec = importlib.util.spec_from_file_location("ring6_probe_contract", PROBE_CONTRACT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(name)


def test_v4_package_topology_matches_its_absolute_imports():
    assert (V4 / "virelai.py").is_file()
    assert not (ARC_ROOT / "inference" / "virelai_v4").exists()
    bad = []
    for path in V4.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("inference.virelai_v4"):
                    bad.append((path.name, node.module))
    assert not bad


def test_probe_call_is_inside_play_failure_boundary():
    tree = ast.parse(SOLVER.read_text(encoding="utf-8"), filename=str(SOLVER))
    play = _function(tree, "play")
    direct_calls = [
        node for node in play.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "_virelai_opening"
    ]
    assert not direct_calls, "opening call escaped play()'s outer try"
    guarded = [
        node for statement in play.body if isinstance(statement, ast.Try)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_virelai_opening"
    ]
    assert len(guarded) == 1


def test_ring7_prompt_purity_no_ontology_no_ring_lineage():
    """Ring 7 contract: the baseline prompt is untouched.  The ONLY Virelai
    surface Duck sees is the Captain report in its first user turn."""
    prompts = (ARC_ROOT / "inference" / "agent" / "prompts.py").read_text(encoding="utf-8")
    for absent in (
        "VIRELAI_WORLD_ADDENDUM",
        "ARC Grid Multiverse Ontology",
        "virelai_card()",
        "[MAP]",
        "Captain",
    ):
        assert absent not in prompts, absent
    agent = (ARC_ROOT / "inference" / "agent" / "tool_agent.py").read_text(encoding="utf-8")
    for absent in ("virelai_digest", "_virelai_state", "VIRELAI_WORLD_ADDENDUM"):
        assert absent not in agent, absent
    # and the handshake itself IS present
    assert "if virelai_card:" in agent
    assert "history_contains_report" in agent


def test_mechanism_and_observed_win_render_without_internal_ids():
    renderer = _load_renderer()
    card = {
        "game_id": "TEST",
        "grid": (64, 64),
        "ego_mode": "GOD_MODE",
        "ego_seal": "FIRM",
        "win_seen": True,
        "observed_transition": {
            "from_level": 1, "to_level": 2, "action": "MOUSE(row=8, col=9)"
        },
        "worldlines": [
            {
                "id": "###4", "_wid": 4, "cells": (1, 1), "anchor": (8, 9),
                "role": "LEVER", "seal": "FIRM", "fields": (), "cov": 4,
                "effects": [{
                    "anchor": (30, 30), "bbox": (30, 30, 33, 33),
                    "cells": 16, "mechanism": "TOGGLE",
                }],
            },
            {
                "id": "###7", "_wid": 7, "cells": (16, 16),
                "anchor": (30, 30), "role": "REACTIVE-DRIVEN",
                "seal": "PROVISIONAL", "fields": (), "cov": 4,
            },
        ],
    }
    text = str(renderer.render_field_card(card, game_id="TEST"))
    assert "alternated between previously observed states" in text
    assert "observed winning transition" in text
    assert "###" not in text
    assert "class " not in text.lower()


def test_multi_snapshot_report_preserves_observations_separately():
    renderer = _load_renderer()
    report = {
        "game_id": "TEST",
        "actions": 37,
        "lives": 2,
        "stop_reason": "TWO_LIVES_USED",
        "snapshots": [
            {"reason": "LIFE_END", "level": 1, "life": 1, "card": {}},
            {"reason": "LEVEL_ADVANCE", "level": 1, "life": 2,
             "card": {"win_seen": True, "observed_transition": {
                 "from_level": 1, "to_level": 2, "action": "RIGHT"}}},
        ],
    }
    text = renderer.render_probe_report(report, game_id="TEST")
    assert text.count("--- Probe snapshot") == 2
    assert "37 actions, 2 lives consumed" in text
    assert "TWO_LIVES_USED" in text
    assert "RIGHT" in text


def test_probe_contract_continues_after_level_win_but_stops_on_game_win():
    contract = _load_probe_contract()
    limits = contract.ProbeLimits(lives=2, actions=320, seconds=480)
    common = dict(
        environment_terminal=False, lives_used=0, actions_used=20,
        elapsed_seconds=30, limits=limits, harness_stop=False,
    )
    assert contract.level_boundary(1, 0) == "ADVANCE"
    assert contract.probe_stop_reason(state_name="NOT_FINISHED", **common) is None
    assert contract.probe_stop_reason(state_name="WIN", **common) == "GAME_WON"


def test_probe_contract_spends_exactly_two_lives_and_has_safety_caps():
    contract = _load_probe_contract()
    limits = contract.ProbeLimits(lives=2, actions=320, seconds=480)
    base = dict(state_name="NOT_FINISHED", environment_terminal=False,
                elapsed_seconds=0, limits=limits, harness_stop=False)
    assert contract.probe_stop_reason(lives_used=1, actions_used=319, **base) is None
    assert contract.probe_stop_reason(lives_used=2, actions_used=10, **base) == "TWO_LIVES_USED"
    assert contract.probe_stop_reason(lives_used=0, actions_used=320, **base) == "ACTION_CAP"
    timed = dict(base)
    timed["elapsed_seconds"] = 480
    assert contract.probe_stop_reason(lives_used=0, actions_used=1, **timed) == "TIME_CAP"

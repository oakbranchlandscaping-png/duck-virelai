"""Ring 6.2 regression tests for the Captain/TAAF action boundary.

Ring 6.1 forwarded ``GameAction.action_data.model_dump()`` verbatim. The live
arcengine model includes an internal ``game_id`` field for every action, while
TAAF rejects any data on simple actions. That single mismatch caused all 24
Captain ``ValueError`` stops in the Ring 6.1 run.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARC_ROOT = HERE.parent / "ARC3-Inference"
SOLVER = ARC_ROOT / "inference" / "framework" / "solver.py"
CONTRACT = ARC_ROOT / "inference" / "framework" / "virelai_probe_contract.py"


def _load_contract():
    spec = importlib.util.spec_from_file_location("ring62_probe_contract", CONTRACT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _function_source(path: Path, name: str) -> str:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            segment = ast.get_source_segment(src, node)
            assert segment is not None
            return segment
    raise AssertionError(f"function {name!r} not found")


class _Data:
    def model_dump(self):
        return {"game_id": "engine-private", "x": 17, "y": 23}


class _Simple:
    action_data = _Data()

    def is_simple(self):
        return True

    def is_complex(self):
        return False


class _Complex:
    action_data = _Data()

    def is_simple(self):
        return False

    def is_complex(self):
        return True


def test_simple_actions_carry_no_data():
    contract = _load_contract()
    assert contract.captain_action_data(_Simple()) == {}


def test_complex_actions_carry_only_public_coordinates():
    contract = _load_contract()
    data = contract.captain_action_data(_Complex())
    assert data == {"x": 17, "y": 23}
    assert "game_id" not in data


def test_captain_driver_uses_the_explicit_payload_bridge():
    body = _function_source(SOLVER, "_virelai_opening")
    assert "captain_action_data(act)" in body
    assert "act.action_data.model_dump()" not in body


def test_model_action_path_still_builds_its_own_payload():
    body = _function_source(SOLVER, "_normalize_actions")
    assert ".action_data" not in body

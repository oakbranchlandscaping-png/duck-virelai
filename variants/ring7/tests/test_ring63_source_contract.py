"""Static wiring and boundary invariants for Ring 6.3."""

from __future__ import annotations

import ast
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARC_ROOT = HERE.parent / "ARC3-Inference"
SOLVER = ARC_ROOT / "inference" / "framework" / "solver.py"
TOOL_AGENT = ARC_ROOT / "inference" / "agent" / "tool_agent.py"


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(name)


def test_false_card_injected_marker_is_retired():
    source = SOLVER.read_text(encoding="utf-8")
    assert '"CARD_INJECTED"' not in source
    for required in (
        '"REPORT_RENDERED"',
        '"REPORT_PERSISTED"',
        '"REPORT_ATTACHED"',
        '"REPORT_REQUEST_ACCEPTED"',
    ):
        assert required in source


def test_solver_offers_report_by_first_analysis_step_and_installs_observer():
    source = SOLVER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOLVER))
    play = _function(tree, "play")
    segment = ast.get_source_segment(source, play)
    assert segment is not None
    assert "if analysis_step == 1 else None" in segment
    assert "request_observer=self._ring63_request_observer" in segment


def test_tool_agent_report_append_is_not_nested_under_action_zero_gate():
    source = TOOL_AGENT.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TOOL_AGENT))
    prompt = _function(tree, "_build_user_prompt")
    outer_card_ifs = [
        node for node in prompt.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "virelai_card"
    ]
    assert len(outer_card_ifs) == 1
    assert "lines.append(virelai_card)" in (
        ast.get_source_segment(source, outer_card_ifs[0]) or ""
    )


def test_provider_observer_runs_after_payload_build_and_before_post():
    source = TOOL_AGENT.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TOOL_AGENT))
    chat = _function(tree, "_chat_completion")
    segment = ast.get_source_segment(source, chat) or ""
    built = segment.index("request_payload = build_chat_payload(")
    prepared = segment.index('notify("prepared", provider_payload=request_payload)')
    posted = segment.index("response = post_chat(request_payload)")
    assert built < prepared < posted


def test_level_and_life_boundary_helpers_never_reset_analysis_step():
    source = SOLVER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOLVER))
    for name in ("_execute_auto_reset", "_virelai_opening"):
        function = _function(tree, name)
        for node in ast.walk(function):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Attribute):
                        assert target.attr != "analysis_step"


def test_observer_is_silent_when_no_report_was_finalized():
    source = SOLVER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOLVER))
    observer = _function(tree, "_ring63_request_observer")
    body = observer.body
    first = body[1] if isinstance(body[0], ast.Expr) else body[0]
    assert isinstance(first, ast.If), "guard must precede all audit work"
    segment = ast.get_source_segment(source, first) or ""
    assert "_ring63_report_meta" in segment
    assert any(isinstance(node, ast.Return) for node in ast.walk(first))


def test_render_failure_assigns_honest_fallback_report():
    source = SOLVER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOLVER))
    opening = _function(tree, "_virelai_opening")
    handlers = [
        node for node in ast.walk(opening)
        if isinstance(node, ast.ExceptHandler)
        and "REPORT UNAVAILABLE" in (ast.get_source_segment(source, node) or "")
    ]
    assert len(handlers) == 1
    segment = ast.get_source_segment(source, handlers[0]) or ""
    assert "self._virelai_card" in segment
    assert "CAPTAIN PROBE REPORT" in segment

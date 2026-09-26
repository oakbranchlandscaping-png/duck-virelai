import json

from tools.evaluate_controller_pilot import evaluate


def _write(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_three_world_trace_evaluation_uses_executed_artifacts(tmp_path):
    for prefix in ("vc33", "ft09", "ls20"):
        artifact = tmp_path / "virelai" / f"{prefix}-fixture_p0"
        artifact.mkdir(parents=True)
        _write(artifact / "events.jsonl", [{"event": "TRANSITION", "transition_id": 1}])
        _write(artifact / "decision_envelopes.jsonl", [{
            "decision_id": f"D-{prefix}", "purpose": "TEST_RULE",
            "actions": [{"action": "LEFT"}],
            "prediction": {"expected": "CHANGED", "scope": {"representation": "CELLS"}},
        }])
        _write(artifact / "outcome_comparisons.jsonl", [{
            "comparison_id": f"OC-{prefix}", "decision_id": f"D-{prefix}",
            "transition_id": 1, "outcome": "SUPPORTED",
        }])
        _write(artifact / "revision_events.jsonl", [{
            "comparison_id": f"OC-{prefix}", "revision_kind": "SUPPORTED",
        }])
    report = evaluate(tmp_path)
    assert report["required_worlds_present"]
    assert report["engineering_passed"]
    assert report["behavioral_passed"]
    assert report["pilot_passed"]
    assert len(report["games"]) == 3


def test_missing_world_fails_pilot(tmp_path):
    (tmp_path / "virelai").mkdir()
    assert not evaluate(tmp_path)["engineering_passed"]


def test_production_layout_joins_bridge_decisions_to_runtime_outcomes(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for prefix in ("vc33", "ft09", "ls20"):
        stem = f"{prefix}-fixture_p0"
        runtime = tmp_path / "virelai" / stem
        runtime.mkdir(parents=True)
        _write(runtime / "events.jsonl", [{"event": "TRANSITION", "transition_id": 1}])
        _write(artifacts / f"{stem}_decision_envelopes.jsonl", [{
            "decision_id": f"D-{prefix}", "purpose": "TEST_RULE",
            "actions": [{"action": "LEFT"}],
            "prediction": {"expected": "CHANGED", "scope": {"representation": "CELLS"}},
        }])
        _write(runtime / "outcome_comparisons.jsonl", [{
            "comparison_id": f"OC-{prefix}", "decision_id": f"D-{prefix}",
            "transition_id": 1, "outcome": "SUPPORTED",
        }])
        _write(runtime / "revision_events.jsonl", [{
            "comparison_id": f"OC-{prefix}", "revision_kind": "SUPPORTED",
        }])
    report = evaluate(tmp_path)
    assert report["engineering_passed"]
    assert report["behavioral_passed"]
    assert all("/artifacts/" in item["decision_path"] for item in report["games"])


def test_production_layout_missing_bridge_file_fails_loudly(tmp_path):
    for prefix in ("vc33", "ft09", "ls20"):
        runtime = tmp_path / "virelai" / f"{prefix}-fixture_p0"
        runtime.mkdir(parents=True)
        _write(runtime / "events.jsonl", [{"event": "TRANSITION", "transition_id": 1}])
        _write(runtime / "outcome_comparisons.jsonl", [{
            "comparison_id": f"OC-{prefix}", "decision_id": f"D-{prefix}",
            "transition_id": 1, "outcome": "SUPPORTED",
        }])
    report = evaluate(tmp_path)
    assert not report["engineering_passed"]
    assert not report["pilot_passed"]
    assert all(not item["checks"]["has_decisions"] for item in report["games"])

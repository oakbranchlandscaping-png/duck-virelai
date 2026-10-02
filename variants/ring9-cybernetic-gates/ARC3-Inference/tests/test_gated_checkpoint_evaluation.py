from __future__ import annotations

import json
import hashlib

from tools.evaluate_gated_checkpoint import evaluate


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_g0_checkpoint_requires_answer_then_joined_g1_probe(tmp_path):
    artifacts = tmp_path / "artifacts"
    stem = "vc33-fixture_p0"
    _write(artifacts / f"{stem}_gate_answers.jsonl", [{
        "gate_id": "G0-ACTION-METADATA", "answer_id": "G0-1",
        "action_metadata": [{"action": "ACTION1", "requires_coordinates": False}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until direct observation supplies evidence.",
    }])
    _write(artifacts / f"{stem}_probe_envelopes.jsonl", [{
        "probe_id": "G1-EGO:PAIR-ACTION1-1", "gate_id": "G1-EGO", "purpose": "PROBE",
    }])
    _write(artifacts / f"{stem}_gate_events.jsonl", [{
        "probe_id": "G1-EGO:PAIR-ACTION1-1", "evidence_id": "E-1",
    }])
    assert evaluate(tmp_path, "g0")["passed"]


def test_g0_checkpoint_fails_if_metadata_answer_is_missing(tmp_path):
    artifacts = tmp_path / "artifacts"
    stem = "vc33-fixture_p0"
    _write(artifacts / f"{stem}_probe_envelopes.jsonl", [{
        "probe_id": "G1-EGO:PAIR-ACTION1-1", "gate_id": "G1-EGO", "purpose": "PROBE",
    }])
    _write(artifacts / f"{stem}_gate_events.jsonl", [{
        "probe_id": "G1-EGO:PAIR-ACTION1-1", "evidence_id": "E-1",
    }])
    assert not evaluate(tmp_path, "g0")["passed"]


def test_g0_checkpoint_fails_when_expected_game_has_no_artifacts(tmp_path):
    report = evaluate(tmp_path, "g0", expected_games=["ft09-missing"])
    assert not report["passed"]
    assert report["games"][0]["game"] == "ft09-missing_p0"
    assert report["games"][0]["answers"] == 0


def test_expected_games_exclude_unrequested_artifacts_but_report_them(tmp_path):
    artifacts = tmp_path / "artifacts"
    _write(artifacts / "other-world_p0_gate_answers.jsonl", [])
    report = evaluate(tmp_path, "g0", expected_games=["vc33-target"])
    assert report["unexpected_artifact_games"] == ["other-world_p0"]


def _g1_fixture(tmp_path):
    artifacts = tmp_path / "artifacts"
    stem = "world-fixture_p0"
    probe_id = "G1-EGO:PAIR-ACTION1-1"
    demo_id = "G1-EGO:DEMONSTRATE:A1"
    certificate = {
        "schema": "virelai-g1-coverage-certificate-v1",
        "state": "DEMONSTRATION_REQUIRED",
        "stop_reason": "DISCRIMINATING_EFFECT_OBSERVED",
        "simple_action_pairs": [{
            "action": "ACTION1", "required_presses": 2, "observed_presses": 2,
            "effect_observed": True, "outcomes_consistent": True,
        }],
        "coordinate": {"state": "NOT_APPLICABLE"},
        "inertness_claim_permitted": False,
    }
    pending = {
        "prediction_id": "PRED-1", "probe_id": demo_id,
        "declared_at_transition": 2,
    }
    _write(artifacts / f"{stem}_gate_answers.jsonl", [
        {
            "gate_id": "G0-ACTION-METADATA", "answer_id": "G0-1",
            "action_metadata": [{"action": "ACTION1", "requires_coordinates": False}],
            "semantic_claims": [],
            "epistemic_limit": "Effects remain unknown until direct observation supplies evidence.",
        },
        {
            "gate_id": "G1-EGO", "answer_id": "A1", "answer_kind": "EMBODIED",
            "subjects": ["single red component"],
            "mechanism": "The red component moves under direct action.",
            "action_laws": {"ACTION1": "moves the component one cell"},
            "conditions": [], "constraints": [], "evidence_refs": ["E-1"],
            "competing_models": ["remote animation"],
            "falsifier": "The declared component remains still.",
            "novel_prediction": {
                "action": {"action": "ACTION1"},
                "scope": {"representation": "CELLS", "cells": [[1, 1]]},
                "predicate": "ANY_CHANGE",
                "because": "the action directly moves it",
                "novelty": "this transition was not observed",
            },
            "limitations": [], "coverage_certificate": certificate,
            "pending_prediction": pending,
        },
    ])
    _write(artifacts / f"{stem}_probe_envelopes.jsonl", [
        {
            "probe_id": probe_id, "gate_id": "G1-EGO", "purpose": "PROBE",
            "actions": [{"action": "ACTION1"}], "declared_at_transition": 0,
        },
        {
            "probe_id": demo_id, "gate_id": "G1-EGO", "purpose": "DEMONSTRATE",
            "actions": [{"action": "ACTION1"}], "declared_at_transition": 2,
        },
    ])
    comparison = {
        "comparison_id": "CMP-1", "prediction_id": "PRED-1",
        "probe_id": demo_id, "transition_id": 3, "outcome": "SUPPORTED",
    }
    _write(artifacts / f"{stem}_gate_events.jsonl", [
        {"probe_id": probe_id, "evidence_id": "E-1"},
        {
            "probe_id": demo_id, "evidence_id": "E-2",
            "demonstration_comparison": comparison,
            "ego_law": {
                "law_id": "EL-1", "status": "OBSERVED",
                "demonstration_ref": "CMP-1",
            },
        },
    ])
    _write(artifacts / f"{stem}_probe_outcomes.jsonl", [
        {"probe_id": probe_id, "evidence_id": "E-1"},
        {"probe_id": demo_id, "evidence_id": "E-2"},
    ])
    _write(artifacts / f"{stem}_probe_frames.jsonl", [
        {"probe_id": probe_id, "frame_ref": "F-0"},
        {"probe_id": demo_id, "frame_ref": "F-2"},
    ])
    receipt = {
        "schema": "virelai-g1-execution-receipt-v1",
        "package": {
            "name": "ring9-fixture", "sha256": "a" * 64,
            "manifest_sha256": "b" * 64,
        },
        "model": {"id": "fixture-model"},
        "budgets": {
            "max_environment_actions_per_world": 20,
            "max_runtime_seconds_per_world": 1200,
            "context_window_tokens": 65536,
            "max_output_tokens_per_turn": "server_default",
            "tool_output_tokens": 1024,
        },
        "worlds": ["world-fixture"], "passes": 1, "concurrency": 1,
        "mode": "gated",
    }
    receipt_path = tmp_path / "execution_receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True))
    return stem, receipt_path


def test_g1_separates_automated_acceptance_from_human_correctness(tmp_path):
    _stem, receipt_path = _g1_fixture(tmp_path)
    report = evaluate(tmp_path, "g1", receipt_path=receipt_path)
    game = report["games"][0]
    assert game["automated_acceptance"] is True
    assert game["grades"]["correctness"]["status"] == "REVIEW_REQUIRED"
    assert game["later_consumption"]["required_for_g1"] is False
    assert report["passed"] is False


def test_g1_evaluator_accepts_frozen_g2_reliability_v2_receipt(tmp_path):
    _stem, receipt_path = _g1_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text())
    receipt["schema"] = "virelai-g2-reliability-execution-receipt-v2"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True))
    report = evaluate(tmp_path, "g1", receipt_path=receipt_path)
    assert report["execution_receipt"]["checks"]["schema"]["passed"]


def test_g1_evaluator_accepts_g3_nav_v6_receipt(tmp_path):
    _stem, receipt_path = _g1_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text())
    receipt["schema"] = "virelai-g3-nav-reachability-v6-execution-receipt-v1"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True))
    report = evaluate(tmp_path, "g1", receipt_path=receipt_path)
    assert report["execution_receipt"]["checks"]["schema"]["passed"]


def test_click_only_interface_axiom_passes_automated_g1_without_actions(tmp_path):
    artifacts = tmp_path / "artifacts"
    stem = "click-world_p0"
    certificate = {
        "schema": "virelai-g1-coverage-certificate-v1",
        "state": "CLOSED",
        "stop_reason": "ACTION_SURFACE_POINTER_EGO",
        "simple_action_pairs": [],
        "hybrid_post_click_pairs": [],
        "coordinate": {"state": "DEFERRED_TO_LATER_TARGETS"},
        "inertness_claim_permitted": False,
    }
    law = {
        "law_id": "EL-pointer",
        "law_version_id": "ELV-pointer",
        "status": "INTERFACE_AXIOM",
        "demonstration_ref": "G0-ACTION-METADATA",
    }
    _write(artifacts / f"{stem}_gate_answers.jsonl", [
        {
            "gate_id": "G0-ACTION-METADATA",
            "answer_id": "G0-1",
            "action_metadata": [
                {"action": "ACTION6", "requires_coordinates": True}
            ],
            "semantic_claims": [],
            "epistemic_limit": "Effects remain unknown until direct observation supplies evidence.",
        },
        {
            "gate_id": "G1-EGO",
            "answer_id": "A-pointer",
            "answer_kind": "POINTER_GOD_MODE",
            "subjects": ["ACTION6 site-selecting locus"],
            "mechanism": "Duck places its control locus at each selected coordinate.",
            "action_laws": {
                "ACTION6": "places the control locus at supplied coordinates"
            },
            "evidence_refs": ["G0-ACTION-METADATA"],
            "competing_models": ["persistent embodied body"],
            "falsifier": "ACTION6 no longer accepts selected coordinates",
            "novel_prediction": {},
            "coverage_certificate": certificate,
            "pending_prediction": None,
            "ego_law": law,
        },
    ])
    receipt = {
        "schema": "virelai-g1-execution-receipt-v1",
        "package": {
            "name": "pointer-fixture", "sha256": "a" * 64,
            "manifest_sha256": "b" * 64,
        },
        "model": {"id": "fixture-model"},
        "budgets": {
            "max_environment_actions_per_world": 20,
            "max_runtime_seconds_per_world": 1200,
            "context_window_tokens": 65536,
            "max_output_tokens_per_turn": "server_default",
            "tool_output_tokens": 1024,
        },
        "worlds": ["click-world"],
        "passes": 1,
        "concurrency": 1,
        "mode": "gated",
    }
    receipt_path = tmp_path / "execution_receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True))
    report = evaluate(tmp_path, "g1", receipt_path=receipt_path)
    game = report["games"][0]
    assert game["automated_acceptance"] is True
    assert game["grades"]["prediction"]["status"] == "PASS"
    assert game["grades"]["demonstration"]["status"] == "PASS"
    assert game["grades"]["correctness"]["status"] == "REVIEW_REQUIRED"


def test_g1_pass_requires_receipt_bound_human_frame_review(tmp_path):
    stem, receipt_path = _g1_fixture(tmp_path)
    review_path = tmp_path / "human_review.json"
    review_path.write_text(json.dumps({
        "schema": "virelai-g1-human-review-v1",
        "execution_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "reviews": [{
            "game": stem, "reviewer": "fixture-reviewer",
            "reviewed_at": "2026-09-19T12:00:00Z",
            "evidence_refs_reviewed": ["E-1", "E-2", "F-0", "F-2"],
            "verdicts": {
                "ego_identity_matches_frames": True,
                "action_laws_match_transitions": True,
                "prediction_was_prospective_and_novel": True,
                "scope_matches_demonstration": True,
                "remote_or_counter_change_not_misattributed": True,
            },
        }],
    }))
    report = evaluate(
        tmp_path, "g1", receipt_path=receipt_path,
        human_review_path=review_path,
    )
    assert report["execution_receipt"]["status"] == "PASS"
    assert report["games"][0]["grades"]["correctness"]["status"] == "PASS"
    assert report["passed"] is True


def test_g1_rejects_review_bound_to_a_different_execution(tmp_path):
    stem, receipt_path = _g1_fixture(tmp_path)
    review_path = tmp_path / "human_review.json"
    review_path.write_text(json.dumps({
        "schema": "virelai-g1-human-review-v1",
        "execution_receipt_sha256": "0" * 64,
        "reviews": [{"game": stem}],
    }))
    report = evaluate(
        tmp_path, "g1", receipt_path=receipt_path,
        human_review_path=review_path,
    )
    assert report["human_review"]["status"] == "FAIL"
    assert report["games"][0]["grades"]["correctness"]["status"] == "REVIEW_REQUIRED"
    assert report["passed"] is False

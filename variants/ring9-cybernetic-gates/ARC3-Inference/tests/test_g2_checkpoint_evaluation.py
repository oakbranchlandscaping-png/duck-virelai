"""Production-shaped tests for the receipt-bound G2 counter-checkpoint evaluator.

Fixtures are produced by driving the real CyberneticGateMachine through
G0 -> G1 -> G2 and writing every artifact row exactly the way
inference/agent/tool_agent.py writes it (failure class 7: a fixture richer
than production proves nothing).  Planted defects then confirm the evaluator
catches the historical failure classes it exists for.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from inference.framework.virelai_gates import CyberneticGateMachine
from tools.evaluate_g2_counter_checkpoint import evaluate


GRID = (
    (7, 7, 7, 7, 0, 0),
    (0, 0, 0, 0, 0, 0),
    (0, 2, 2, 0, 3, 0),
    (0, 0, 0, 0, 0, 0),
)
BAR = ((0, 0), (0, 1), (0, 2), (0, 3))
STEM = "vc33-fixture_p0"
WORLD = "vc33-fixture"


def _write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


class _Recorder:
    """Write artifact rows with the exact shapes tool_agent.py produces."""

    def __init__(self):
        self.answers: list[dict] = []
        self.envelopes: list[dict] = []
        self.events: list[dict] = []
        self.outcomes: list[dict] = []
        self.frames: list[dict] = []

    def record_answer(self, machine, payload):
        gate_id = machine.gate_id
        answer = machine.submit_answer(payload)
        record = {
            "schema": "virelai-cybernetic-gates-v1",
            "gate_id": gate_id,
            **asdict(answer),
        }
        if gate_id == "G1-EGO":
            snapshot = machine.ego.snapshot()
            record.update({
                "gate_status_after_answer": snapshot["status"],
                "coverage_certificate": snapshot["coverage_certificate"],
                "pending_prediction": snapshot["pending_prediction"],
                "ego_law": snapshot["ego_law"],
            })
        elif gate_id == "G2-COUNTER":
            snapshot = machine.counter.snapshot()
            record.update({
                "gate_status_after_answer": snapshot["status"],
                "counter_candidate": snapshot["candidate"],
                "pending_prediction": snapshot["pending_prediction"],
            })
        self.answers.append(record)
        return answer

    def record_probe(self, machine, outcome_builder):
        capability = machine.next_probe_capability()
        assert capability is not None
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        self.envelopes.append({
            "schema": "virelai-cybernetic-gates-v1",
            "probe_token": capability["probe_token"],
            **asdict(probe),
        })
        outcome = dict(outcome_builder(probe, capability["actions"][0]))
        outcome["probe_id"] = probe.probe_id
        event = machine.record_outcome(probe, outcome)
        outcome["evidence_id"] = event["evidence_id"]
        self.events.append(json.loads(json.dumps(event, sort_keys=True, default=str)))
        self.outcomes.append(outcome)
        for kind in ("before", "after"):
            self.frames.append({
                "kind": kind,
                "evidence_id": event["evidence_id"],
                "probe_id": probe.probe_id,
            })
        return event, outcome


def _outcome(transition_id, action, bar_before, bar_after, *, game_over=False):
    changed = [
        {"row": 0, "col": col, "before": bar_before[col], "after": bar_after[col]}
        for col in range(4)
        if bar_before[col] != bar_after[col]
    ]
    acted = (
        {"row": int(action["row"]), "col": int(action["col"])}
        if action.get("row") is not None else None
    )
    def _value(row, col, bar):
        return bar[col] if row == 0 and col < 4 else GRID[row][col]
    return {
        "transition_id": transition_id,
        "shape_before": [4, 6],
        "shape_after": [4, 6],
        "action": dict(action),
        "acted_site": acted,
        "board_changed": bool(changed),
        "changed_cell_count": len(changed),
        "changed_cells": changed,
        "site_transitions": [
            {
                "row": row, "col": col,
                "before": _value(row, col, bar_before),
                "after": _value(row, col, bar_after),
                "outcome": (
                    "CHANGED"
                    if _value(row, col, bar_before) != _value(row, col, bar_after)
                    else "HELD"
                ),
            }
            for row in range(4) for col in range(6)
        ],
        "boundary_event": {
            "state": "GAME_OVER" if game_over else "PLAYING",
            "game_over": game_over,
        },
    }


def _drive_locked_g2(*, lock_on_demonstration=True):
    """Run the real gate machine to a locked G2 and return the recorded rows."""
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=GRID)
    recorder = _Recorder()
    recorder.record_answer(machine, {
        "answer_id": "G0-click",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until controlled observation reveals them.",
    })
    recorder.record_answer(machine, {
        "answer_id": "G1-pointer",
        "answer_kind": "POINTER_GOD_MODE",
        "subjects": ["the ACTION6 site-selecting control locus"],
        "mechanism": "Duck moves its pointer ego by supplying a new grid coordinate",
        "action_laws": {"ACTION6": "places direct intervention at the supplied grid coordinate"},
        "conditions": ["the coordinate is legal"],
        "constraints": ["target effects remain unknown"],
        "evidence_refs": ["G0-ACTION-METADATA"],
        "competing_models": ["a persistent embodied grid object is controlled"],
        "falsifier": "ACTION6 requires no selected coordinate for direct intervention",
        "limitations": ["no target response has been classified"],
    })
    assert machine.gate_id == "G2-COUNTER"

    bar = [7, 7, 7, 7]
    transition = 0
    witnesses = 0
    while witnesses < 2:
        def build(probe, action, _bar=tuple(bar)):
            nonlocal transition, witnesses, bar
            transition += 1
            acted_in_bar = (
                action.get("row") is not None
                and (int(action["row"]), int(action["col"])) in BAR
            )
            before = tuple(bar)
            if acted_in_bar:
                return _outcome(transition, action, before, before)
            tick_count = (
                1 if not lock_on_demonstration or witnesses == 0 else 2
            )
            for _ in range(tick_count):
                tick = bar.index(7)
                bar = [4 if i == tick else value for i, value in enumerate(bar)]
            witnesses += 1
            return _outcome(transition, action, before, tuple(bar))
        recorder.record_probe(machine, build)
    assert machine.counter.status == "ANSWER_REQUIRED"
    candidate = machine.counter.candidate
    template = machine.gate_view()["answer_template"]
    recorder.record_answer(machine, {
        "answer_id": "G2-top-strip",
        "candidate_id": candidate.candidate_id,
        "tracked_variable": "remaining visible units in the top strip",
        "mechanism": "one top-strip cell rewrites from integer seven to integer four per intervention",
        "bookkeeping_reason": "the rewrite recurs away from distinct selected sites under every tested intervention",
        "conditions": ["fixed geometry in the current level"],
        "evidence_refs": list(candidate.witness_evidence_refs),
        "competing_models": ["the strip is a remote lever target"],
        "falsifier": "the next intervention leaves the strip unchanged or reverses it",
        "limitations": ["the terminal meaning of an exhausted strip is unknown"],
        "novel_prediction": template["novel_prediction"],
    })

    def demonstrate(probe, action):
        nonlocal transition, bar
        transition += 1
        before = tuple(bar)
        tick = bar.index(7)
        bar = [4 if i == tick else value for i, value in enumerate(bar)]
        return _outcome(
            transition, action, before, tuple(bar),
            game_over=lock_on_demonstration,
        )
    event, _ = recorder.record_probe(machine, demonstrate)
    assert event["counter_comparison"]["outcome"] == "SUPPORTED"
    assert event["counter_boundary"]["outcome"] == (
        "SUPPORTED" if lock_on_demonstration else "PENDING"
    )
    assert machine.counter.status == "CLOSED"
    return recorder


def test_mask_ready_handoff_is_a_complete_automated_baseline(tmp_path):
    recorder = _drive_locked_g2(lock_on_demonstration=False)
    _materialize(tmp_path, recorder)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert game["disposition"] == "REVIEW_REQUIRED"
    assert game["automated_acceptance"] is True
    assert not game["passed"]
    assert game["grades"]["baseline_lock"]["status"] == "PASS"


def _receipt():
    return {
        "schema": "virelai-g2-execution-receipt-v1",
        "package": {
            "name": "fixture-g2-package",
            "sha256": "a" * 64,
            "manifest_sha256": "b" * 64,
        },
        "model": {"id": "vrfai/Qwen3.6-27B-FP8"},
        "budgets": {
            "max_environment_actions_per_world": 48,
            "max_runtime_seconds_per_world": 1800,
            "context_window_tokens": 65536,
            "max_output_tokens_per_turn": "server_default",
            "tool_output_tokens": 1024,
        },
        "passes": 1,
        "concurrency": 1,
        "mode": "gated",
        "worlds": [WORLD],
    }


def _materialize(tmp_path, recorder):
    artifacts = tmp_path / "artifacts"
    _write_rows(artifacts / f"{STEM}_gate_answers.jsonl", recorder.answers)
    _write_rows(artifacts / f"{STEM}_probe_envelopes.jsonl", recorder.envelopes)
    _write_rows(artifacts / f"{STEM}_gate_events.jsonl", recorder.events)
    _write_rows(artifacts / f"{STEM}_probe_outcomes.jsonl", recorder.outcomes)
    _write_rows(artifacts / f"{STEM}_probe_frames.jsonl", recorder.frames)
    receipt_path = tmp_path / "execution_receipt.json"
    receipt_path.write_text(json.dumps(_receipt(), indent=2, sort_keys=True))
    return artifacts, receipt_path


def test_g2_evaluator_accepts_frozen_reliability_v2_receipt(tmp_path):
    recorder = _drive_locked_g2()
    _artifacts, receipt_path = _materialize(tmp_path, recorder)
    receipt = json.loads(receipt_path.read_text())
    receipt["schema"] = "virelai-g2-reliability-execution-receipt-v2"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    report = evaluate(tmp_path, [WORLD], receipt_path=receipt_path)
    assert report["execution_receipt"]["checks"]["schema"]["passed"]


def _review(receipt_path, *, wrong_binding=False):
    digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    refs = set()
    return {
        "schema": "virelai-g2-human-review-v1",
        "execution_receipt_sha256": ("f" * 64) if wrong_binding else digest,
        "reviews": [{
            "game": STEM,
            "reviewer": "director",
            "reviewed_at": "2026-09-19T00:00:00Z",
            "verdicts": {
                "tracked_variable_matches_frames": True,
                "footprint_holds_only_bookkeeping_no_world_object": True,
                "bookkeeping_interpretation_justified_by_varied_interventions": True,
                "boundary_consequence_visible_at_extremum": True,
                "mask_scope_complete_and_reversible": True,
                "confirmation_action_was_counter_only": True,
            },
            "evidence_refs_reviewed": sorted(refs),
        }],
    }


def _write_review(tmp_path, recorder, receipt_path, **kwargs):
    review = _review(receipt_path, **kwargs)
    review["reviews"][0]["evidence_refs_reviewed"] = sorted({
        row["evidence_id"] for row in recorder.events if row.get("evidence_id")
    })
    (tmp_path / "human_review.json").write_text(
        json.dumps(review, indent=2, sort_keys=True)
    )


def test_locked_g2_passes_automated_grades_and_requires_human_review(tmp_path):
    recorder = _drive_locked_g2()
    _materialize(tmp_path, recorder)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert game["automated_acceptance"], json.dumps(game["grades"], indent=2)
    assert game["disposition"] == "REVIEW_REQUIRED"
    assert report["human_review_required"]
    assert not report["passed"]
    packet = report["review_packet"]["games"][0]
    assert packet["candidate"] and packet["mask_law"] and packet["boundary"]


def test_locked_g2_with_receipt_bound_review_passes(tmp_path):
    recorder = _drive_locked_g2()
    _, receipt_path = _materialize(tmp_path, recorder)
    _write_review(tmp_path, recorder, receipt_path)
    report = evaluate(tmp_path, [WORLD])
    assert report["games"][0]["disposition"] == "PASS"
    assert report["passed"]


def test_review_bound_to_a_different_receipt_is_rejected(tmp_path):
    recorder = _drive_locked_g2()
    _, receipt_path = _materialize(tmp_path, recorder)
    _write_review(tmp_path, recorder, receipt_path, wrong_binding=True)
    report = evaluate(tmp_path, [WORLD])
    assert report["games"][0]["disposition"] == "REVIEW_REQUIRED"
    assert not report["passed"]


def test_one_sided_mask_is_rejected(tmp_path):
    recorder = _drive_locked_g2()
    support_only = None
    for row in recorder.events:
        law = row.get("mask_law")
        if isinstance(law, dict):
            support_only = [list(cell) for cell in law["cells"][:2]]
            law["cells"] = support_only
    assert support_only is not None
    _, receipt_path = _materialize(tmp_path, recorder)
    _write_review(tmp_path, recorder, receipt_path)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert not game["automated_acceptance"]
    assert not game["grades"]["baseline_lock"]["checks"]["mask_covers_footprint"]["passed"]
    assert not report["passed"]


def test_non_counter_only_confirmation_is_rejected(tmp_path):
    recorder = _drive_locked_g2()
    comparison_ref = next(
        row["counter_comparison"]["evidence_ref"]
        for row in recorder.events
        if isinstance(row.get("counter_comparison"), dict)
        and row["counter_comparison"]["outcome"] == "SUPPORTED"
    )
    for outcome in recorder.outcomes:
        if outcome.get("evidence_id") != comparison_ref:
            continue
        outcome["changed_cells"] = list(outcome["changed_cells"]) + [
            {"row": 2, "col": 1, "before": 2, "after": 5}
        ]
        for site in outcome["site_transitions"]:
            if site["row"] == 2 and site["col"] == 1:
                site["after"] = 5
                site["outcome"] = "CHANGED"
    _, receipt_path = _materialize(tmp_path, recorder)
    _write_review(tmp_path, recorder, receipt_path)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert not game["grades"]["prediction"]["checks"]["confirmation_counter_only"]["passed"]
    assert not report["passed"]


def test_prediction_journaled_after_comparison_is_rejected(tmp_path):
    recorder = _drive_locked_g2()
    comparison = next(
        row["counter_comparison"] for row in recorder.events
        if isinstance(row.get("counter_comparison"), dict)
    )
    for row in recorder.answers:
        pending = row.get("pending_prediction")
        if isinstance(pending, dict):
            pending["declared_at_transition"] = int(comparison["transition_id"])
    _, receipt_path = _materialize(tmp_path, recorder)
    _write_review(tmp_path, recorder, receipt_path)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert not game["grades"]["prediction"]["checks"]["declared_before_observation"]["passed"]
    assert not report["passed"]


def test_world_without_g2_artifacts_is_not_reached(tmp_path):
    recorder = _drive_locked_g2()
    recorder.answers = [
        row for row in recorder.answers if row.get("gate_id") != "G2-COUNTER"
    ]
    recorder.envelopes, recorder.events = [], []
    recorder.outcomes, recorder.frames = [], []
    _materialize(tmp_path, recorder)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert game["disposition"] == "NOT_REACHED"
    assert game["g1_closed"]
    assert not report["passed"]


def test_run_ending_before_boundary_is_budget_exhausted_not_fail(tmp_path):
    recorder = _drive_locked_g2()
    boundary_index = next(
        index for index, row in enumerate(recorder.events)
        if isinstance(row.get("counter_boundary"), dict)
        and row["counter_boundary"]["outcome"] == "SUPPORTED"
    )
    kept = {row["probe_id"] for row in recorder.events[:boundary_index]}
    recorder.events = recorder.events[:boundary_index]
    recorder.envelopes = [row for row in recorder.envelopes if row["probe_id"] in kept]
    recorder.outcomes = [row for row in recorder.outcomes if row["probe_id"] in kept]
    recorder.frames = [row for row in recorder.frames if row["probe_id"] in kept]
    _materialize(tmp_path, recorder)
    report = evaluate(tmp_path, [WORLD])
    game = report["games"][0]
    assert game["disposition"] == "BUDGET_EXHAUSTED"
    assert "grades" not in game
    assert not report["passed"]

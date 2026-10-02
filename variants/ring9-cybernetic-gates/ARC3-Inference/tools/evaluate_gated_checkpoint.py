#!/usr/bin/env python3
"""Evaluate executed G0/G1 artifacts without mistaking schema for understanding."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


OPAQUE_ACTION = re.compile(r"^ACTION[0-9]+$")
RECEIPT_SCHEMAS = frozenset({
    "virelai-g1-execution-receipt-v1",
    "virelai-g2-execution-receipt-v1",
    "virelai-g2-reliability-execution-receipt-v2",
    "virelai-g3-nav-reachability-v5-execution-receipt-v1",
    "virelai-g3-nav-reachability-v6-execution-receipt-v1",
    "virelai-g3-nav-reachability-v7-execution-receipt-v1",
})
REVIEW_SCHEMA = "virelai-g1-human-review-v1"
REPORT_SCHEMA = "virelai-gated-checkpoint-evaluation-v2"


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _stems(artifacts: Path) -> list[str]:
    suffixes = (
        "_gate_answers.jsonl", "_probe_envelopes.jsonl", "_gate_events.jsonl",
        "_probe_outcomes.jsonl", "_probe_frames.jsonl",
    )
    return sorted({
        path.name.removesuffix(suffix)
        for suffix in suffixes
        for path in artifacts.glob(f"*{suffix}")
    })


def _check(value: Any, detail: str) -> dict[str, Any]:
    return {"passed": bool(value), "detail": detail}


def _grade(checks: Mapping[str, dict[str, Any]], *, pending: bool = False) -> dict[str, Any]:
    status = "REVIEW_REQUIRED" if pending else (
        "PASS" if checks and all(item["passed"] for item in checks.values()) else "FAIL"
    )
    return {"status": status, "checks": dict(checks)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_optional(run_dir: Path, supplied: Path | None, name: str) -> Path | None:
    if supplied is not None:
        return supplied
    for candidate in (run_dir / name, run_dir.parent / name):
        if candidate.is_file():
            return candidate
    return None


def _world_matches(stem: str, world: str) -> bool:
    return stem == world or stem.startswith(f"{world}_p")


def _execution_receipt(
    path: Path | None, stems: list[str], expected_games: list[str] | None,
) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    parse_ok = False
    if path and path.is_file():
        try:
            value = json.loads(path.read_text())
            raw = value if isinstance(value, dict) else {}
            parse_ok = isinstance(value, dict)
        except (OSError, json.JSONDecodeError):
            pass
    package = raw.get("package") if isinstance(raw.get("package"), dict) else {}
    model = raw.get("model") if isinstance(raw.get("model"), dict) else {}
    budgets = raw.get("budgets") if isinstance(raw.get("budgets"), dict) else {}
    worlds = raw.get("worlds") if isinstance(raw.get("worlds"), list) else []
    required_worlds = expected_games or stems
    alignment = (
        len(worlds) == len(required_worlds)
        and all(any(_world_matches(stem, str(world)) for stem in stems) for world in worlds)
        and all(any(_world_matches(stem, str(world)) for world in worlds) for stem in stems)
    )
    checks = {
        "receipt_present_and_json": _check(parse_ok, "Execution receipt exists and is a JSON object."),
        "schema": _check(
            raw.get("schema") in RECEIPT_SCHEMAS,
            "schema must be a supported Ring 9 execution receipt: "
            + ", ".join(sorted(RECEIPT_SCHEMAS)) + ".",
        ),
        "package_identity": _check(
            bool(package.get("name"))
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(package.get("sha256") or "")))
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(package.get("manifest_sha256") or ""))),
            "Package name, package SHA-256, and manifest SHA-256 are required.",
        ),
        "model_identity": _check(bool(model.get("id")), "Exact model id is required."),
        "budgets": _check(
            isinstance(budgets.get("max_environment_actions_per_world"), int)
            and budgets.get("max_environment_actions_per_world", 0) > 0
            and isinstance(budgets.get("max_runtime_seconds_per_world"), int)
            and budgets.get("max_runtime_seconds_per_world", 0) > 0
            and isinstance(budgets.get("context_window_tokens"), int)
            and budgets.get("context_window_tokens", 0) > 0
            and (
                (
                    isinstance(budgets.get("max_output_tokens_per_turn"), int)
                    and budgets.get("max_output_tokens_per_turn", 0) > 0
                )
                or budgets.get("max_output_tokens_per_turn") == "server_default"
            )
            and isinstance(budgets.get("tool_output_tokens"), int)
            and budgets.get("tool_output_tokens", 0) > 0,
            "Action, runtime, context, model-output, and tool-output limits are required.",
        ),
        "passes": _check(
            isinstance(raw.get("passes"), int) and raw.get("passes", 0) > 0,
            "Pass count is required.",
        ),
        "concurrency": _check(
            isinstance(raw.get("concurrency"), int) and raw.get("concurrency", 0) > 0,
            "Concurrency is required.",
        ),
        "gated_mode": _check(raw.get("mode") == "gated", "Receipt mode must be gated."),
        "world_alignment": _check(
            alignment, "Receipt worlds must match this evaluation's artifact worlds exactly."
        ),
    }
    grade = _grade(checks)
    grade.update({
        "path": str(path) if path else None,
        "sha256": _sha256(path) if path and path.is_file() else None,
        "configuration": raw,
    })
    return grade


def _g0_checks(
    answers: list[dict], probes: list[dict], events: list[dict],
) -> dict[str, dict[str, Any]]:
    g0 = [row for row in answers if row.get("gate_id") == "G0-ACTION-METADATA"]
    metadata = g0[0].get("action_metadata") if g0 else None
    first_probe = probes[0] if probes else {}
    first_event = events[0] if events else {}
    g1_answer = next(
        (row for row in answers if row.get("gate_id") == "G1-EGO"), None
    )
    interface_exit = (
        isinstance(g1_answer, dict)
        and isinstance(g1_answer.get("ego_law"), dict)
        and g1_answer["ego_law"].get("status") == "INTERFACE_AXIOM"
    )
    return {
        "one_g0_answer": _check(len(g0) == 1, "Exactly one G0 answer is required."),
        "opaque_metadata_nonempty": _check(
            bool(metadata) and all(
                isinstance(item, dict)
                and bool(OPAQUE_ACTION.fullmatch(str(item.get("action", ""))))
                and isinstance(item.get("requires_coordinates"), bool)
                for item in metadata
            ),
            "G0 must preserve opaque action ids and coordinate affordances.",
        ),
        "no_semantic_claims": _check(
            bool(g0) and g0[0].get("semantic_claims") == [], "G0 cannot assign meanings."
        ),
        "states_epistemic_limit": _check(
            bool(g0) and len(str(g0[0].get("epistemic_limit") or "").split()) >= 5,
            "G0 must state that action effects remain unknown.",
        ),
        "g1_opened_after_g0": _check(
            first_probe.get("gate_id") == "G1-EGO" or interface_exit,
            "G1 must open as a probe or an interface-grounded answer."
        ),
        "first_probe_executed_and_joined": _check(
            (
                bool(first_probe)
                and first_event.get("probe_id") == first_probe.get("probe_id")
            )
            or interface_exit,
            "The first G1 probe must be joined unless the interface answers G1.",
        ),
    }


def _g1_grades(
    answers: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    events: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    review: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    g1 = [row for row in answers if row.get("gate_id") == "G1-EGO"]
    answer = g1[-1] if g1 else {}
    probe_ids = [str(row.get("probe_id") or "") for row in probes]
    event_probe_ids = [str(row.get("probe_id") or "") for row in events]
    outcome_probe_ids = [str(row.get("probe_id") or "") for row in outcomes]
    evidence_ids = {str(row.get("evidence_id")) for row in events if row.get("evidence_id")}
    actions = [action for probe in probes for action in (probe.get("actions") or [])]
    demonstrations = [row for row in probes if row.get("purpose") == "DEMONSTRATE"]
    certificate = answer.get("coverage_certificate") or {}
    coordinate = (
        certificate.get("coordinate")
        if isinstance(certificate.get("coordinate"), dict)
        else {}
    )
    simple_pairs = (
        certificate.get("simple_action_pairs")
        if isinstance(certificate.get("simple_action_pairs"), list)
        else []
    )
    hybrid_post_click_pairs = (
        certificate.get("hybrid_post_click_pairs")
        if isinstance(certificate.get("hybrid_post_click_pairs"), list)
        else []
    )
    prediction = (
        answer.get("novel_prediction")
        if isinstance(answer.get("novel_prediction"), dict)
        else {}
    )
    pending = (
        answer.get("pending_prediction")
        if isinstance(answer.get("pending_prediction"), dict)
        else {}
    )
    target_demo_id = str(pending.get("probe_id") or "")
    target_demonstrations = [
        row for row in demonstrations if str(row.get("probe_id")) == target_demo_id
    ]
    demonstration_ids = {target_demo_id} if target_demo_id else set()
    demonstration_events = [
        row for row in events if str(row.get("probe_id")) in demonstration_ids
    ]
    demo_event = demonstration_events[-1] if demonstration_events else {}
    comparison = demo_event.get("demonstration_comparison") or {}
    law = answer.get("ego_law") or demo_event.get("ego_law") or {}
    interface_exit = (
        law.get("status") == "INTERFACE_AXIOM"
        and certificate.get("stop_reason") == "ACTION_SURFACE_POINTER_EGO"
    )
    refs = {str(item) for item in answer.get("evidence_refs") or []}

    protocol = _grade({
        "g0_contract": _check(
            all(item["passed"] for item in _g0_checks(answers, probes, events).values()),
            "G0 preceded G1.",
        ),
        "one_or_more_g1_answers": _check(
            bool(g1), "At least one accepted G1 answer is required; the latest revision is graded."
        ),
        "unique_probe_ids": _check(
            interface_exit
            or (bool(probe_ids) and len(probe_ids) == len(set(probe_ids)) and all(probe_ids)),
            "Probe ids are nonempty and unique, or G1 closed from the interface.",
        ),
        "exact_probe_event_join": _check(
            set(probe_ids) == set(event_probe_ids) and len(probe_ids) == len(event_probe_ids),
            "Every admitted probe has exactly one compact event.",
        ),
        "exact_probe_outcome_join": _check(
            set(probe_ids) == set(outcome_probe_ids) and len(probe_ids) == len(outcome_probe_ids),
            "Every admitted probe has exactly one lossless outcome.",
        ),
        "opaque_actions_only": _check(
            interface_exit or (bool(actions) and all(
                isinstance(item, dict)
                and bool(OPAQUE_ACTION.fullmatch(str(item.get("action") or "")))
                for item in actions
            )),
            "All executed probe actions retain opaque ids.",
        ),
        "frame_archive_present": _check(
            bool(frames) or interface_exit,
            "Frames are present unless G1 closed without an environment action."
        ),
    })
    coverage = _grade({
        "certificate_persisted": _check(
            certificate.get("schema") == "virelai-g1-coverage-certificate-v1",
            "Declaration-time coverage certificate is persisted.",
        ),
        "discriminating_effect": _check(
            certificate.get("stop_reason") in {
                "DISCRIMINATING_EFFECT_OBSERVED", "ACTION_SURFACE_POINTER_EGO"
            },
            "Coverage ended on sufficient behavioral or interface evidence.",
        ),
        "simple_pairs_complete": _check(
            all(
                row.get("observed_presses") == row.get("required_presses") == 2
                for row in simple_pairs
            ),
            "Every applicable non-coordinate action has its consecutive pair.",
        ),
        "hybrid_activation_pairs_complete": _check(
            all(
                row.get("observed_presses") == row.get("required_presses") == 2
                for row in hybrid_post_click_pairs
            ),
            "Every scheduled post-click hybrid activation pair is complete.",
        ),
        "coordinate_policy_complete": _check(
            coordinate.get("state") in {
                "READY", "NOT_APPLICABLE", "DEFERRED_TO_LATER_TARGETS"
            },
            "Coordinate coverage is ready or inapplicable.",
        ),
        "unknowns_not_called_inert": _check(
            certificate.get("inertness_claim_permitted") is False,
            "Untested members remain unknown, never inert.",
        ),
    })
    explanation = _grade({
        "identity_and_subjects": _check(
            bool(str(answer.get("answer_kind") or "").strip()) and bool(answer.get("subjects")),
            "Answer identifies a control mode and subject.",
        ),
        "mechanism": _check(
            len(str(answer.get("mechanism") or "").split()) >= 4,
            "Mechanism is more than a label.",
        ),
        "opaque_action_laws": _check(
            isinstance(answer.get("action_laws"), dict)
            and bool(answer.get("action_laws"))
            and all(
                bool(OPAQUE_ACTION.fullmatch(str(key))) and len(str(value).split()) >= 3
                for key, value in answer["action_laws"].items()
            ),
            "At least one opaque action has an explanatory law.",
        ),
        "direct_evidence": _check(
            (
                refs == {"G0-ACTION-METADATA"}
                if interface_exit
                else bool(refs) and refs <= evidence_ids
            ),
            "The answer cites its interface prerequisite or direct G1 evidence.",
        ),
        "alternative_and_falsifier": _check(
            bool(answer.get("competing_models"))
            and len(str(answer.get("falsifier") or "").split()) >= 3,
            "Answer preserves an alternative and falsifier.",
        ),
    })
    prediction_grade = _grade({
        "required_for_closure": _check(
            interface_exit or bool(pending),
            "Prediction is required for behavioral laws and waived for interface axioms.",
        ),
        "prospective_claim_persisted": _check(
            interface_exit or (bool(pending) and pending.get("probe_id") in demonstration_ids),
            "Controller-journaled prediction binds the future demonstration.",
        ),
        "action_scope_predicate": _check(
            interface_exit or (
                isinstance(prediction.get("action"), dict)
                and bool(OPAQUE_ACTION.fullmatch(
                    str(prediction.get("action", {}).get("action") or "")
                ))
                and isinstance(prediction.get("scope"), dict)
                and bool(prediction.get("scope"))
                and bool(prediction.get("predicate"))
            ),
            "Prediction declares an opaque action, grounded scope, and predicate.",
        ),
        "reason_and_novelty": _check(
            interface_exit or (
                len(str(prediction.get("because") or "").split()) >= 3
                and len(str(prediction.get("novelty") or "").split()) >= 3
            ),
            "Prediction explains entailment and novelty.",
        ),
        "declared_before_observation": _check(
            interface_exit or (
                bool(pending)
                and bool(target_demonstrations)
                and int(pending.get("declared_at_transition", -1))
                == int(target_demonstrations[-1].get("declared_at_transition", -2))
                and int(comparison.get("transition_id", -1))
                > int(pending.get("declared_at_transition", -1))
            ),
            "Prediction was journaled at the pre-action boundary and compared on a later transition.",
        ),
    })
    demonstration = _grade({
        "required_for_closure": _check(
            interface_exit or bool(target_demonstrations),
            "Demonstration is required for behavioral laws and waived for interface axioms.",
        ),
        "one_joined_demonstration": _check(
            interface_exit or len(target_demonstrations) == len(demonstration_events) == 1,
            "The latest answer's prospective demonstration is joined exactly once.",
        ),
        "scoped_verdict_supported": _check(
            interface_exit or comparison.get("outcome") == "SUPPORTED",
            "Scoped verifier supported the declared predicate.",
        ),
        "comparison_binding": _check(
            interface_exit or (
                comparison.get("probe_id") in demonstration_ids
                and comparison.get("prediction_id") == pending.get("prediction_id")
            ),
            "Comparison binds the journaled prediction and demonstration probe.",
        ),
        "observed_ego_law": _check(
            (
                law.get("status") == "INTERFACE_AXIOM"
                and law.get("demonstration_ref") == "G0-ACTION-METADATA"
            ) or (
                law.get("status") == "OBSERVED"
                and law.get("demonstration_ref") == comparison.get("comparison_id")
            ),
            "Supported comparison produced a versioned observed EgoLaw.",
        ),
    })

    if review is not None:
        verdicts = review.get("verdicts") if isinstance(review.get("verdicts"), dict) else {}
        reviewed_refs = {str(item) for item in review.get("evidence_refs_reviewed") or []}
        required_review_refs = set(refs)
        if demo_event.get("evidence_id"):
            required_review_refs.add(str(demo_event["evidence_id"]))
        correctness = _grade({
            "reviewer": _check(
                bool(str(review.get("reviewer") or "").strip()),
                "Reviewer identity is recorded.",
            ),
            "reviewed_at": _check(
                bool(str(review.get("reviewed_at") or "").strip()),
                "Review time is recorded.",
            ),
            "ego_identity_matches_frames": _check(
                verdicts.get("ego_identity_matches_frames") is True,
                "Reviewer confirms identity against frames.",
            ),
            "action_laws_match_transitions": _check(
                verdicts.get("action_laws_match_transitions") is True,
                "Reviewer confirms laws against transitions.",
            ),
            "prediction_was_prospective_and_novel": _check(
                verdicts.get("prediction_was_prospective_and_novel") is True,
                "Reviewer confirms prospective novelty.",
            ),
            "scope_matches_demonstration": _check(
                verdicts.get("scope_matches_demonstration") is True,
                "Reviewer confirms claimed scope.",
            ),
            "remote_or_counter_change_not_misattributed": _check(
                verdicts.get("remote_or_counter_change_not_misattributed") is True,
                "Reviewer confirms causal attribution.",
            ),
            "evidence_reviewed": _check(
                bool(reviewed_refs) and required_review_refs <= reviewed_refs,
                "Review names every cited and demonstration evidence record inspected.",
            ),
        })
    else:
        correctness = _grade({
            "human_review": _check(
                False, "A human must inspect the supplied frames and claims."
            )
        }, pending=True)

    grades = {
        "protocol": protocol,
        "coverage": coverage,
        "explanation": explanation,
        "prediction": prediction_grade,
        "demonstration": demonstration,
        "correctness": correctness,
    }
    packet = {
        "answer": answer,
        "demonstration_probe": (
            target_demonstrations[-1] if target_demonstrations else None
        ),
        "demonstration_event": demo_event or None,
        "cited_events": [
            row for row in events if row.get("evidence_id") in refs
        ],
        "lossless_outcomes": outcomes,
        "frames": frames,
        "review_questions": [
            "Does the named ego/control mode match the visible before/after frames?",
            "Do the opaque action laws describe only demonstrated transitions?",
            "Was the demonstration prediction declared before a genuinely new transition?",
            "Does the claimed scope match the changed footprint without absorbing remote or counter change?",
        ],
    }
    return grades, packet


def _reviews(
    path: Path | None, receipt_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    raw: dict[str, Any] = {}
    if path and path.is_file():
        try:
            value = json.loads(path.read_text())
            raw = value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
    rows = raw.get("reviews") if isinstance(raw.get("reviews"), list) else []
    checks = {
        "schema": _check(
            raw.get("schema") == REVIEW_SCHEMA, f"schema must be {REVIEW_SCHEMA}."
        ),
        "receipt_binding": _check(
            bool(receipt_sha256)
            and raw.get("execution_receipt_sha256") == receipt_sha256,
            "Review must bind to this exact execution receipt.",
        ),
        "unique_games": _check(
            len(rows) == len({str(row.get("game")) for row in rows}),
            "One review row per game.",
        ),
    }
    valid_header = all(item["passed"] for item in checks.values())
    return {
        "path": str(path) if path else None,
        "status": "PASS" if valid_header else ("MISSING" if path is None else "FAIL"),
        "checks": checks,
    }, ({str(row.get("game")): row for row in rows} if valid_header else {})


def evaluate(
    run_dir: Path,
    stage: str,
    expected_games: list[str] | None = None,
    *,
    receipt_path: Path | None = None,
    human_review_path: Path | None = None,
) -> dict[str, Any]:
    artifacts = run_dir / "artifacts" if (run_dir / "artifacts").is_dir() else run_dir
    discovered = _stems(artifacts)
    if expected_games:
        stems = [
            next((s for s in discovered if _world_matches(s, game)), f"{game}_p0")
            for game in expected_games
        ]
    else:
        stems = discovered

    receipt: dict[str, Any] | None = None
    review_header: dict[str, Any] | None = None
    review_by_game: dict[str, dict[str, Any]] = {}
    if stage == "g1":
        receipt_path = _resolve_optional(run_dir, receipt_path, "execution_receipt.json")
        receipt = _execution_receipt(receipt_path, stems, expected_games)
        human_review_path = _resolve_optional(
            run_dir, human_review_path, "human_review.json"
        )
        review_header, review_by_game = _reviews(
            human_review_path, receipt.get("sha256")
        )

    games: list[dict[str, Any]] = []
    review_packets: list[dict[str, Any]] = []
    for stem in stems:
        answers = _rows(artifacts / f"{stem}_gate_answers.jsonl")
        probes = _rows(artifacts / f"{stem}_probe_envelopes.jsonl")
        events = _rows(artifacts / f"{stem}_gate_events.jsonl")
        reuse = _rows(artifacts / f"{stem}_gate_reuse.jsonl")
        counts = {
            "answers": len(answers), "probes": len(probes),
            "events": len(events), "reuse": len(reuse),
        }
        if stage == "g0":
            checks = _g0_checks(answers, probes, events)
            passed = all(item["passed"] for item in checks.values())
            games.append({
                "game": stem,
                **counts,
                "checks": {key: item["passed"] for key, item in checks.items()},
                "check_details": checks,
                "passed": passed,
            })
            continue

        outcomes = _rows(artifacts / f"{stem}_probe_outcomes.jsonl")
        frames = _rows(artifacts / f"{stem}_probe_frames.jsonl")
        review = review_by_game.get(stem)
        grades, packet = _g1_grades(
            answers, probes, events, outcomes, frames, review
        )
        automated = all(
            grades[name]["status"] == "PASS"
            for name in (
                "protocol", "coverage", "explanation",
                "prediction", "demonstration",
            )
        )
        satisfied = automated and grades["correctness"]["status"] == "PASS"
        games.append({
            "game": stem,
            **counts,
            "outcomes": len(outcomes),
            "frames": len(frames),
            "grades": grades,
            "automated_acceptance": automated,
            "g1_satisfied": satisfied,
            "passed": satisfied,
            "later_consumption": {
                "status": "OBSERVED" if reuse else "NOT_OBSERVED",
                "events": len(reuse),
                "required_for_g1": False,
            },
        })
        review_packets.append({"game": stem, **packet})

    unexpected = [stem for stem in discovered if stem not in stems] if expected_games else []
    if stage == "g0":
        passed = bool(games) and not unexpected and all(game["passed"] for game in games)
        return {
            "schema": REPORT_SCHEMA,
            "stage": "G0",
            "run_dir": str(run_dir),
            "expected_games": expected_games or [],
            "unexpected_artifact_games": unexpected,
            "games": games,
            "passed": passed,
            "human_review_required": False,
            "claim_limit": (
                "G0 pass proves action-surface acknowledgement and ordered G1 entry; "
                "it does not prove a correct ego model."
            ),
        }

    receipt_pass = bool(receipt and receipt["status"] == "PASS")
    passed = (
        bool(games)
        and not unexpected
        and receipt_pass
        and all(game["g1_satisfied"] for game in games)
    )
    return {
        "schema": REPORT_SCHEMA,
        "stage": "G1",
        "run_dir": str(run_dir),
        "expected_games": expected_games or [],
        "unexpected_artifact_games": unexpected,
        "execution_receipt": receipt,
        "human_review": review_header,
        "games": games,
        "passed": passed,
        "human_review_required": any(
            game["grades"]["correctness"]["status"] != "PASS"
            for game in games
        ),
        "review_packet": {
            "schema": "virelai-g1-human-review-packet-v1",
            "execution_receipt_sha256": receipt.get("sha256") if receipt else None,
            "games": review_packets,
        },
        "claim_limit": (
            "Automated grades establish protocol, coverage, declared explanation quality, "
            "prospectivity, and scoped verifier behavior. Only a receipt-bound human frame "
            "review can establish behavioral correctness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--stage", choices=("g0", "g1"), required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-packet-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--human-review", type=Path)
    parser.add_argument("--expected-game", action="append", default=[])
    args = parser.parse_args()
    report = evaluate(
        args.run_dir.resolve(),
        args.stage,
        args.expected_game or None,
        receipt_path=args.receipt,
        human_review_path=args.human_review,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    if args.review_packet_output and report.get("review_packet"):
        args.review_packet_output.write_text(
            json.dumps(report["review_packet"], indent=2, sort_keys=True) + "\n"
        )
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

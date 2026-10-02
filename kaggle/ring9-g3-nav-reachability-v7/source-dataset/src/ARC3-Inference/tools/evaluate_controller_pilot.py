#!/usr/bin/env python3
"""Grade controller acceptance traces without grading prompt echo as adoption."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


TARGET_PREFIXES = ("vc33", "ft09", "ls20")


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _decision_path(run_dir: Path, artifact: Path) -> Path:
    """Resolve the file written by the real Duck action bridge.

    Runtime semantic artifacts live under ``virelai/<run_stem>/`` while the Duck
    bridge writes its prospective envelopes beside the runtime-state artifact in
    ``artifacts/``.  Keep the legacy co-located path readable for old fixtures,
    but prefer the production path when it exists.
    """
    production = run_dir / "artifacts" / f"{artifact.name}_decision_envelopes.jsonl"
    if production.exists():
        return production
    return artifact / "decision_envelopes.jsonl"


def evaluate(run_dir: Path) -> dict:
    virelai_root = run_dir / "virelai"
    games = []
    for artifact in sorted(virelai_root.iterdir() if virelai_root.exists() else ()):
        if not artifact.is_dir() or not artifact.name.startswith(TARGET_PREFIXES):
            continue
        decisions_path = _decision_path(run_dir, artifact)
        decisions = _rows(decisions_path)
        outcomes = _rows(artifact / "outcome_comparisons.jsonl")
        revisions = _rows(artifact / "revision_events.jsonl")
        transition_ids = {
            int(row["transition_id"])
            for row in _rows(artifact / "events.jsonl")
            if row.get("event") == "TRANSITION" and row.get("transition_id") is not None
        }
        decision_ids = {row.get("decision_id") for row in decisions}
        outcome_decisions = {row.get("decision_id") for row in outcomes}
        joined_once = Counter(row.get("decision_id") for row in outcomes)
        tests = [row for row in decisions if row.get("purpose") in {"TEST_RULE", "RECONFIRM_TRANSFER"}]
        checks = {
            "has_decisions": bool(decisions),
            "all_outcomes_reference_decisions": outcome_decisions <= decision_ids,
            "each_outcome_joins_existing_transition": all(
                int(row.get("transition_id") or -1) in transition_ids for row in outcomes
            ),
            "no_decision_has_multiple_outcomes": all(count == 1 for count in joined_once.values()),
            "tests_are_single_action_and_predictive": all(
                len(row.get("actions") or ()) == 1
                and isinstance(row.get("prediction"), dict)
                and isinstance((row.get("prediction") or {}).get("scope"), dict)
                for row in tests
            ),
            "revisions_reference_comparisons": {
                row.get("comparison_id") for row in revisions
            } <= {row.get("comparison_id") for row in outcomes},
        }
        behavioral_checks = {
            "has_prospective_test": bool(tests),
            "has_matched_prediction": any(
                row.get("outcome") in {"SUPPORTED", "CONTRADICTED", "INDETERMINATE"}
                for row in outcomes
            ),
            "has_semantic_revision": any(
                row.get("revision_kind")
                not in {None, "NO_SEMANTIC_CHANGE"}
                for row in revisions
            ),
        }
        games.append({
            "game": artifact.name,
            "decision_path": str(decisions_path),
            "decisions": len(decisions),
            "purposes": dict(Counter(row.get("purpose") for row in decisions)),
            "outcomes": dict(Counter(row.get("outcome") for row in outcomes)),
            "revisions": dict(Counter(row.get("revision_kind") for row in revisions)),
            "checks": checks,
            "behavioral_checks": behavioral_checks,
            "engineering_passed": all(checks.values()),
            "behavioral_passed": all(behavioral_checks.values()),
        })
    required_present = {item["game"][:4] for item in games} == set(TARGET_PREFIXES)
    report = {
        "schema": "virelai-controller-pilot-evaluation-v1",
        "run_dir": str(run_dir),
        "required_worlds_present": required_present,
        "games": games,
        "engineering_passed": required_present and all(item["engineering_passed"] for item in games),
        "behavioral_passed": required_present and all(item["behavioral_passed"] for item in games),
        "human_review_required": [
            "Was the selected focus useful given only prior evidence?",
            "Did Duck correct contract errors without wasting actions?",
            "Were declared scopes faithful to what Duck said it was testing?",
            "Were outcome verdicts accurate in observable reality?",
            "Did a later decision retrieve or use a prior revision?",
        ],
    }
    report["pilot_passed"] = report["engineering_passed"] and report["behavioral_passed"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.run_dir.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["pilot_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

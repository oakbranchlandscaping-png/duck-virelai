#!/usr/bin/env python3
"""Audit H4 target classes against recorded visible boards, without game mechanics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inference.framework.adaptive_ego_coverage import AdaptiveCoordinateCoverage


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def audit(artifacts: Path) -> dict[str, Any]:
    worlds = []
    event_paths = sorted(
        path
        for path in artifacts.glob("*_events.jsonl")
        if not path.name.endswith("_gate_events.jsonl")
    )
    for path in event_paths:
        initial = next(
            (row.get("board") for row in _rows(path) if isinstance(row.get("board"), list)),
            None,
        )
        if initial is None:
            worlds.append({"world": path.stem.removesuffix("_events"), "status": "NO_VISIBLE_BOARD"})
            continue
        planner = AdaptiveCoordinateCoverage(initial)
        class_sizes = sorted((len(item.member_ids) for item in planner.classes), reverse=True)
        worlds.append({
            "world": path.stem.removesuffix("_events"),
            "status": "OBSERVED",
            "components": len(planner.candidates),
            "target_classes": len(planner.classes),
            "initial_representatives": len(planner.initial_representatives()),
            "largest_class": class_sizes[0] if class_sizes else 0,
        })
    return {
        "schema": "virelai-h4-adaptive-coverage-audit-v1",
        "source": str(artifacts),
        "claim_limit": (
            "Classifies visible frame-zero components only; does not infer ego identity, "
            "action meaning, mechanics, or behavioral success."
        ),
        "worlds": worlds,
        "passed": bool(worlds) and all(row["status"] == "OBSERVED" for row in worlds),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.artifacts.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

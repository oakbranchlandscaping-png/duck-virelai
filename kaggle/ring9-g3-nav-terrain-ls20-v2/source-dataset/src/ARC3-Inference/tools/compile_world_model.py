"""Compile existing semantic artifacts into deterministic canonical model shells."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inference.framework.virelai_world_model import (
    canonical_bytes,
    from_semantic_library,
    model_sha256,
    with_level_lessons,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.output_root.resolve()
    if root.exists():
        raise SystemExit(f"Refusing to reuse output root: {root}")
    root.mkdir(parents=True)
    rows = []
    for source in args.sources:
        payload = json.loads(source.read_text(encoding="utf-8"))
        first = from_semantic_library(payload)
        lessons_path = source.with_name("level_lessons.jsonl")
        lessons = (
            [json.loads(line) for line in lessons_path.read_text(encoding="utf-8").splitlines() if line]
            if lessons_path.exists() else []
        )
        first = with_level_lessons(first, lessons)
        second = from_semantic_library(
            json.loads(source.read_text(encoding="utf-8"))
        )
        second = with_level_lessons(second, lessons)
        first_bytes = canonical_bytes(first)
        second_bytes = canonical_bytes(second)
        deterministic = first_bytes == second_bytes
        target = root / f"{first.game_id}.world_model.json"
        target.write_bytes(first_bytes)
        rows.append(
            {
                "game_id": first.game_id,
                "source": str(source.resolve()),
                "target": str(target),
                "bytes": len(first_bytes),
                "sha256": model_sha256(first),
                "deterministic": deterministic,
                "objects": len(first.objects),
                "mechanics": len(first.mechanics),
                "wins": len(first.wins),
                "level_diffs": len(first.level_diffs),
            }
        )
    report = {
        "schema": "virelai-world-model-schema-gate-v1",
        "models": rows,
        "passed": bool(rows) and all(row["deterministic"] for row in rows),
    }
    (root / "schema_gate_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

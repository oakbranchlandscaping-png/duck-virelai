"""Freeze immutable hashes and observed win boundaries for an archive corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from inference.framework.virelai_runtime import verify_frame_archive


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def freeze(source_root: Path) -> dict[str, Any]:
    games: list[dict[str, Any]] = []
    for source in sorted(path.parent for path in source_root.rglob("frames.jsonl")):
        integrity = verify_frame_archive(source)
        events = read_jsonl(source / "events.jsonl")
        boundaries = [
            {
                "transition_id": int(event["transition_id"]),
                "from_node": int(event["from_node"]),
                "to_node": int(event["to_node"]),
                "level_before": int(event["level_before"]),
                "level_after": int(event["level_after"]),
                "actor": str(event["actor"]),
                "action_id": int(event["action_id"]),
                "action_name": str(event["action_name"]),
                "level_completed": bool(event.get("level_completed")),
                "run_complete": bool(event.get("run_complete")),
            }
            for event in events
            if event.get("event") == "TRANSITION"
            and (event.get("level_completed") or event.get("run_complete"))
        ]
        games.append(
            {
                "archive": str(source.resolve()),
                "archive_name": source.name,
                "game_id": str(next((e.get("game_id") for e in events if e.get("game_id")), source.name)),
                "frames_sha256": sha256(source / "frames.bin"),
                "index_sha256": sha256(source / "frames.jsonl"),
                "events_sha256": sha256(source / "events.jsonl"),
                "integrity": integrity,
                "win_boundaries": boundaries,
            }
        )
    return {
        "schema": "virelai-win-corpus-v1",
        "source_root": str(source_root.resolve()),
        "games": games,
        "game_count": len(games),
        "win_boundary_count": sum(len(game["win_boundaries"]) for game in games),
        "passed": bool(games) and all(game["integrity"]["passed"] for game in games),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite frozen corpus: {args.output}")
    report = freeze(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({key: value for key, value in report.items() if key != "games"}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

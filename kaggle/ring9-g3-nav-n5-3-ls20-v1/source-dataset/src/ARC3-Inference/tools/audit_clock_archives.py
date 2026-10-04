"""Recompute Ring 8 clock candidates from persisted canonical archives."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from inference.framework.virelai_clock import compile_clock_patterns
from inference.framework.virelai_runtime import CellDelta, TransitionRecord


def _transitions(path: Path) -> list[TransitionRecord]:
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("event") != "TRANSITION":
            continue
        payload.pop("schema", None)
        payload.pop("event", None)
        payload["cell_deltas"] = tuple(CellDelta(**item) for item in payload["cell_deltas"])
        result.append(TransitionRecord(**payload))
    return result


def _latest_record(archive: Path):
    index = [json.loads(line) for line in (archive / "frames.jsonl").read_text().splitlines()]
    meta = index[-1]
    layer = meta["layers"][-1]
    binary = (archive / "frames.bin").read_bytes()
    start = int(meta["archive_offset"]) + int(layer["byte_offset"])
    payload = binary[start : start + int(layer["byte_length"])]
    return SimpleNamespace(
        layers=(SimpleNamespace(rows=int(layer["rows"]), cols=int(layer["cols"])),),
        layer_bytes=lambda _index: payload,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_output", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.run_output.resolve()
    rows = []
    for archive in sorted((root / "virelai").iterdir()):
        if not archive.is_dir():
            continue
        transitions = _transitions(archive / "events.jsonl")
        latest = _latest_record(archive)
        level = max((item.level_after for item in transitions), default=1)
        candidates = compile_clock_patterns(transitions, latest, level=level)
        rows.append({"game": archive.name, "level": level, "candidates": candidates})
    report = {"schema": "virelai-clock-archive-audit-v1", "games": rows}
    target = args.output or root / "clock_archive_audit.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "games": len(rows),
        "games_with_candidates": sum(bool(row["candidates"]) for row in rows),
        "candidate_counts": {row["game"].split("-")[0]: len(row["candidates"]) for row in rows},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Replay a lossless archive and render the canonical physics grammar offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inference.framework.virelai_runtime import VirelaiRuntime, verify_frame_archive
from tools.replay_continuity_archives import _frames, _read_jsonl


def compile_archive(source: Path, level: int | None = None) -> tuple[dict, str]:
    integrity = verify_frame_archive(source)
    if not integrity.get("passed"):
        raise ValueError(f"source archive failed integrity: {source}")
    frames = _frames(source)
    events = [row for row in _read_jsonl(source / "events.jsonl") if row.get("event") == "TRANSITION"]
    if len(frames) != len(events) + 1:
        raise ValueError("frame/transition count mismatch")
    runtime = VirelaiRuntime(game_id=frames[0].game_id)
    runtime.observe_initial(frames[0])
    for event, frame in zip(events, frames[1:]):
        runtime.observe_transition(
            frame=frame,
            action_id=int(event.get("action_id") or 0),
            action_name=str(event.get("action_name") or ""),
            acted_cell=tuple(event["acted_cell"]) if event.get("acted_cell") is not None else None,
            actor=str(event.get("actor") or "DUCK"),
            result={
                "level": int(event.get("level_after") or 1),
                "level_completed": bool(event.get("level_completed")),
                "game_over": bool(event.get("game_over")),
                "run_complete": bool(event.get("run_complete")),
            },
        )
    response = runtime.query("physics", {"level": level} if level is not None else {})
    if response.get("error"):
        raise ValueError(f"physics query failed: {response['error']}")
    manual = dict(response["data"])
    text = str(manual.pop("text"))
    manual["query_latency_ms"] = response["latency_ms"]
    manual["query_budget_breached"] = response["budget_breached"]
    warm = runtime.query("physics", {"level": level} if level is not None else {})
    manual["warm_query_latency_ms"] = warm["latency_ms"]
    manual["warm_query_budget_breached"] = warm["budget_breached"]
    runtime.flush()
    return manual, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--level", type=int)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()
    manual, text = compile_archive(args.source, args.level)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(manual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

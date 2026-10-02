"""Replay one lossless Virelai archive and render its new-level memory card."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inference.framework.virelai_runtime import VirelaiRuntime, verify_frame_archive
from tools.replay_continuity_archives import _frames, _read_jsonl


def render(source: Path) -> dict:
    integrity = verify_frame_archive(source)
    if not integrity.get("passed"):
        raise ValueError(f"source archive failed integrity: {source}")
    frames = _frames(source)
    events = [
        row for row in _read_jsonl(source / "events.jsonl")
        if row.get("event") == "TRANSITION"
    ]
    if len(frames) != len(events) + 1:
        raise ValueError("frame/transition count mismatch")
    runtime = VirelaiRuntime(game_id=frames[0].game_id)
    runtime.observe_initial(frames[0])
    entered_level = 1
    for event, frame in zip(events, frames[1:]):
        runtime.observe_transition(
            frame=frame,
            action_id=int(event.get("action_id") or 0),
            action_name=str(event.get("action_name") or ""),
            acted_cell=(
                tuple(event["acted_cell"])
                if event.get("acted_cell") is not None else None
            ),
            actor=str(event.get("actor") or "DUCK"),
            result={
                "level": int(event.get("level_after") or entered_level),
                "level_completed": bool(event.get("level_completed")),
                "game_over": bool(event.get("game_over")),
                "run_complete": bool(event.get("run_complete")),
            },
        )
        entered_level = max(entered_level, int(event.get("level_after") or 1))
    response = runtime.query("card", {"level": entered_level})
    runtime.flush()
    if response.get("error"):
        raise ValueError(response["error"])
    return response["data"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    card = render(args.source)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(card["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

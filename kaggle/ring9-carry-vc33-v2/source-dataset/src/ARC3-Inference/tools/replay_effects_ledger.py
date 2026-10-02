"""Replay real ARC recording JSONL files into the passive effects ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from inference.framework.virelai_runtime import VirelaiRuntime, verify_frame_archive


def _load_recording(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        data = payload.get("data", payload)
        if not isinstance(data, dict) or not isinstance(data.get("frame"), list):
            raise ValueError(f"{path}:{line_number}: missing frame data")
        records.append(data)
    if not records:
        raise ValueError(f"{path}: recording contains zero frames")
    return records


def _frame(data: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        frame=data["frame"],
        game_id=str(data.get("game_id") or "recording"),
        guid=data.get("guid"),
        state=str(data.get("state") or ""),
        levels_completed=int(data.get("levels_completed") or 0),
        win_levels=int(data.get("win_levels") or 0),
        full_reset=bool(data.get("full_reset")),
        available_actions=tuple(int(value) for value in data.get("available_actions") or ()),
    )


def _acted_cell(action: dict[str, Any]) -> tuple[int, int] | None:
    data = action.get("data") or {}
    if "row" in data and "col" in data:
        return (int(data["row"]), int(data["col"]))
    if "y" in data and "x" in data:
        return (int(data["y"]), int(data["x"]))
    return None


def _archived_frames(artifact_dir: Path) -> list[list[list[list[int]]]]:
    binary = (artifact_dir / "frames.bin").read_bytes()
    frames: list[list[list[list[int]]]] = []
    for line in (artifact_dir / "frames.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        base = int(record["archive_offset"])
        layers: list[list[list[int]]] = []
        for layer in record["layers"]:
            rows = int(layer["rows"])
            cols = int(layer["cols"])
            start = base + int(layer["byte_offset"])
            raw = binary[start : start + int(layer["byte_length"])]
            layers.append(
                [list(raw[row * cols : (row + 1) * cols]) for row in range(rows)]
            )
        frames.append(layers)
    return frames


def replay_recording(recording: Path, output_root: Path) -> dict[str, Any]:
    source = Path(recording).resolve()
    records = _load_recording(source)
    game_id = str(records[0].get("game_id") or source.stem)
    recording_root = Path(output_root) / source.stem
    runtime = VirelaiRuntime(game_id=game_id, artifact_root=recording_root)
    runtime.observe_initial(_frame(records[0]))
    previous = records[0]
    for data in records[1:]:
        action = data.get("action_input") or {}
        action_id = int(action.get("id") or 0)
        levels_before = int(previous.get("levels_completed") or 0)
        levels_after = int(data.get("levels_completed") or 0)
        state = str(data.get("state") or "").upper()
        win_levels = int(data.get("win_levels") or 0)
        runtime.observe_transition(
            frame=_frame(data),
            action_id=action_id,
            action_name=f"ACTION{action_id}",
            acted_cell=_acted_cell(action),
            actor="DUCK",
            result={
                "level": max(1, levels_after + 1),
                "level_completed": levels_after > levels_before,
                "game_over": state in {"LOST", "GAME_OVER"},
                "run_complete": state in {"WON", "WIN"}
                or (win_levels > 0 and levels_after >= win_levels),
            },
        )
        previous = data
    effects = runtime.query("effects")
    runtime.flush()
    artifact_dir = recording_root / game_id
    integrity = verify_frame_archive(artifact_dir)
    archived_frames = _archived_frames(artifact_dir) if integrity["passed"] else []
    source_frames = [record["frame"] for record in records]
    events = [
        json.loads(line)
        for line in (artifact_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    transitions = [event for event in events if event.get("event") == "TRANSITION"]
    canonical_complete = len(transitions) == len(records) - 1 and all(
        len(event.get("cell_deltas") or []) == int(event.get("cell_delta_count", -1))
        for event in transitions
    )
    checks = {
        "n_plus_one": len(records) == len(transitions) + 1,
        "archive_integrity": integrity["passed"],
        "frame_equality": archived_frames == source_frames,
        "canonical_transitions_complete": canonical_complete,
        "effects_cover_recorded_actions": (
            sum(item["presses"] for item in effects["data"]["entries"])
            == len(records) - 1
        ),
    }
    return {
        "recording": str(source),
        "recording_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "game_id": game_id,
        "source_frames": len(records),
        "transitions": len(transitions),
        "artifact_dir": str(artifact_dir),
        "checks": checks,
        "integrity": integrity,
        "effects": effects,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("recordings", nargs="+", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    campaign_root = repo.parents[2]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = (
        args.output_root or campaign_root / "runs" / f"ring80b-replay-{stamp}"
    ).resolve()
    if output_root.exists():
        raise SystemExit(f"Refusing to reuse existing output root: {output_root}")
    output_root.mkdir(parents=True)
    try:
        results = [replay_recording(path, output_root) for path in args.recordings]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Replay failed: {type(exc).__name__}: {exc}")
        return 1
    report = {
        "schema": "virelai-effects-ledger-replay-v1",
        "output_root": str(output_root),
        "recordings": results,
        "passed": bool(results) and all(item["passed"] for item in results),
    }
    (output_root / "replay_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Replay existing lossless Ring 8 archives through the continuity shadow."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from inference.framework.virelai_runtime import VirelaiRuntime, verify_frame_archive


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _frames(source: Path) -> list[SimpleNamespace]:
    binary = (source / "frames.bin").read_bytes()
    result: list[SimpleNamespace] = []
    for item in _read_jsonl(source / "frames.jsonl"):
        base = int(item["archive_offset"])
        layers: list[list[list[int]]] = []
        for layer in item["layers"]:
            rows, cols = int(layer["rows"]), int(layer["cols"])
            start = base + int(layer["byte_offset"])
            raw = binary[start : start + int(layer["byte_length"])]
            layers.append([list(raw[row * cols : (row + 1) * cols]) for row in range(rows)])
        result.append(
            SimpleNamespace(
                frame=layers,
                game_id=str(item.get("game_id") or source.name),
                guid=item.get("guid"),
                state=str(item.get("state") or ""),
                levels_completed=int(item.get("levels_completed") or 0),
                win_levels=int(item.get("win_levels") or 0),
                full_reset=bool(item.get("full_reset")),
                available_actions=tuple(int(value) for value in item.get("available_actions") or ()),
            )
        )
    return result


def replay(source: Path, output_root: Path) -> dict[str, Any]:
    source = source.resolve()
    source_integrity = verify_frame_archive(source)
    if not source_integrity["passed"]:
        return {"source": str(source), "passed": False, "source_integrity": source_integrity}
    frames = _frames(source)
    events = _read_jsonl(source / "events.jsonl")
    transitions = [item for item in events if item.get("event") == "TRANSITION"]
    by_to_node = {int(item["to_node"]): item for item in transitions}
    if len(frames) != len(transitions) + 1:
        return {
            "source": str(source),
            "passed": False,
            "error": "source violates N+1 frame invariant",
            "frames": len(frames),
            "transitions": len(transitions),
        }
    runtime = VirelaiRuntime(
        game_id=str(frames[0].game_id),
        run_stem=source.name,
        artifact_root=output_root,
    )
    runtime.observe_initial(frames[0])
    for node_index, frame in enumerate(frames[1:], start=1):
        event = by_to_node[node_index]
        acted_cell = event.get("acted_cell")
        runtime.observe_transition(
            frame=frame,
            action_id=int(event.get("action_id") or 0),
            action_name=str(event.get("action_name") or ""),
            acted_cell=tuple(acted_cell) if acted_cell is not None else None,
            actor=str(event.get("actor") or "DUCK"),
            result={
                "level": int(event.get("level_after") or 1),
                "level_completed": bool(event.get("level_completed")),
                "game_over": bool(event.get("game_over")),
                "run_complete": bool(event.get("run_complete")),
            },
        )
    world_response = runtime.query("world", {"limit": 50})
    runtime.flush()
    target = output_root / source.name
    target_integrity = verify_frame_archive(target)
    continuity = json.loads((target / "continuity_summary.json").read_text(encoding="utf-8"))
    checks = {
        "source_archive_integrity": bool(source_integrity["passed"]),
        "target_archive_integrity": bool(target_integrity["passed"]),
        "n_plus_one": len(frames) == len(runtime.transitions) + 1,
        "frame_payload_equal": (source / "frames.bin").read_bytes() == (target / "frames.bin").read_bytes(),
        "continuity_current": continuity["compiled_through_node"] == len(frames) - 1,
        "continuity_fault_free": continuity["faults"] == 0,
        "continuity_hidden": continuity["duck_visible"] is False,
        "world_model_available": world_response.get("error") is None,
        "world_model_persisted": (target / "world_model.json").is_file(),
    }
    return {
        "source": str(source),
        "source_sha256": hashlib.sha256((source / "frames.bin").read_bytes()).hexdigest(),
        "target": str(target),
        "frames": len(frames),
        "transitions": len(transitions),
        "tracks": continuity["tracks"],
        "stitches": continuity["stitches"],
        "ambiguous_terminations": continuity["ambiguous_terminations"],
        "compile_performance": continuity["compile_performance"],
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise SystemExit(f"Refusing to reuse output root: {output_root}")
    output_root.mkdir(parents=True)
    sources: list[Path] = []
    for candidate in args.sources:
        if (candidate / "frames.jsonl").is_file():
            sources.append(candidate)
        else:
            sources.extend(sorted(path.parent for path in candidate.rglob("frames.jsonl")))
    unique_sources = list(dict.fromkeys(path.resolve() for path in sources))
    results = [replay(source, output_root) for source in unique_sources]
    report = {
        "schema": "virelai-continuity-replay-v1",
        "sources": len(unique_sources),
        "frames": sum(int(item.get("frames") or 0) for item in results),
        "transitions": sum(int(item.get("transitions") or 0) for item in results),
        "tracks": sum(int(item.get("tracks") or 0) for item in results),
        "stitches": sum(int(item.get("stitches") or 0) for item in results),
        "failures": sum(not item.get("passed", False) for item in results),
        "results": results,
        "passed": bool(results) and all(item.get("passed", False) for item in results),
    }
    (output_root / "replay_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

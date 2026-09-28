"""Deterministic compact-journal and bounded-effects-query performance gate."""
from __future__ import annotations

import argparse
import gc
import json
import tempfile
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

from inference.framework.virelai_runtime import (
    CAPTURE_BREACH_MS,
    CAPTURE_P95_BUDGET_MS,
    RAW_QUERY_BREACH_MS,
    VirelaiRuntime,
    verify_frame_archive,
)


@dataclass
class FixtureFrame:
    frame: list[list[list[int]]]
    game_id: str = "ring80a-benchmark"
    guid: str | None = None
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 1
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 2, 3, 4)


def fixture_frame(step: int) -> FixtureFrame:
    underlay = [[3] * 64 for _ in range(64)]
    grid = [[0] * 64 for _ in range(64)]
    grid[step % 64][(step // 64) % 64] = step % 16
    return FixtureFrame(frame=[underlay, grid])


def _edge_fixture_report(root: Path) -> dict[str, object]:
    runtime = VirelaiRuntime(game_id="ring80b-edge-fixtures", artifact_root=root)
    frames = [
        FixtureFrame(frame=[[[9]], [[0, 0], [0, 0]]]),
        FixtureFrame(frame=[[[8]], [[0, 1], [0, 0]]]),
        FixtureFrame(frame=[[[7]], [[0, 1], [0, 0]]]),  # visible self-loop/tick
        FixtureFrame(frame=[[[6]], [[0, 0], [0, 0]]]),  # revisit
        FixtureFrame(frame=[[[5]], [[0, 0, 0], [0, 0, 0]]]),  # geometry change
    ]
    runtime.observe_initial(frames[0])
    action_names = ("UP", "TICK", "DOWN", "MOUSE(row=0, col=0)")
    for step, frame in enumerate(frames[1:], start=1):
        runtime.observe_transition(
            frame=frame,
            action_id=0 if action_names[step - 1] == "TICK" else step,
            action_name=action_names[step - 1],
            acted_cell=(0, 0) if step == 4 else None,
            actor="SYSTEM" if action_names[step - 1] == "TICK" else "DUCK",
            result={"level": 1},
        )
    runtime.flush()
    first, tick, revisit, geometry = runtime.transitions
    integrity = verify_frame_archive(root / "ring80b-edge-fixtures")
    checks = {
        "multi_layer": all(len(record.layers) == 2 for record in runtime.journal.iter_records()),
        "exact_cell_rewrite": (
            first.cell_delta_count == 1
            and first.cell_deltas[0].before_class == 0
            and first.cell_deltas[0].after_class == 1
        ),
        "visible_self_loop": tick.visible_self_loop,
        "ticking_state": tick.actor == "SYSTEM" and tick.action_name == "TICK",
        "revisit": revisit.target_seen_before,
        "geometry_change": (
            geometry.geometry_changed
            and geometry.before_shape == (2, 2)
            and geometry.after_shape == (2, 3)
            and not geometry.cell_deltas
        ),
        "archive_integrity": integrity["passed"],
    }
    return {"passed": all(checks.values()), "checks": checks, "archive": integrity}


def run(action_count: int) -> tuple[dict[str, object], bool]:
    with tempfile.TemporaryDirectory(prefix="ring80a_benchmark_") as directory:
        gc.collect()
        tracemalloc.start()
        baseline_memory, _ = tracemalloc.get_traced_memory()
        runtime = VirelaiRuntime(game_id="ring80a-benchmark", artifact_root=Path(directory))
        runtime.observe_initial(fixture_frame(0))
        for step in range(1, action_count + 1):
            runtime.observe_transition(
                frame=fixture_frame(step),
                action_id=1,
                action_name="UP",
                acted_cell=None,
                actor="DUCK",
                result={"level": 1},
            )
        for _ in range(100):
            runtime.query("effects")
        runtime.flush()
        integrity = verify_frame_archive(Path(directory) / "ring80a-benchmark")
        edge_fixtures = _edge_fixture_report(Path(directory))
        overview = runtime.query("overview")["data"]
        capture = overview["capture_performance"]
        query_values = runtime._query_timings_ms  # benchmark-only instrumentation read
        query_p95 = sorted(query_values)[max(0, (95 * len(query_values) + 99) // 100 - 1)]
        raw_payload_bytes = sum(len(record.payload) for record in runtime.journal.iter_records())
        archive_bytes = (Path(directory) / "ring80a-benchmark" / "frames.bin").stat().st_size
        memory_limit = int(raw_payload_bytes * 1.5 + 2 * 1024 * 1024)
        gc.collect()
        current_memory, _ = tracemalloc.get_traced_memory()
        journal_memory = max(0, current_memory - baseline_memory)
        tracemalloc.stop()
        result: dict[str, object] = {
            "actions": action_count,
            "frames": len(runtime.journal),
            "transitions": len(runtime.transitions),
            "raw_payload_bytes": raw_payload_bytes,
            "archive_bytes": archive_bytes,
            "measured_journal_memory_bytes": journal_memory,
            "memory_limit_bytes": memory_limit,
            "capture": capture,
            "raw_query_p95_ms": round(query_p95, 3),
            "raw_query_breach_ms": RAW_QUERY_BREACH_MS,
            "archive_integrity": integrity,
            "edge_fixtures": edge_fixtures,
            "effects": runtime.query("effects")["data"],
            "continuity_shadow": runtime._continuity_summary,
        }
        continuity = runtime._continuity_summary or {}
        passed = bool(
            len(runtime.journal) == action_count + 1
            and len(runtime.transitions) == action_count
            and archive_bytes == raw_payload_bytes
            and journal_memory <= memory_limit
            and float(capture["p95_ms"]) <= CAPTURE_P95_BUDGET_MS
            and float(capture["breach_ratio"]) <= 0.01
            and query_p95 <= RAW_QUERY_BREACH_MS
            and integrity["passed"]
            and edge_fixtures["passed"]
            and continuity.get("compiled_through_node") == action_count
            and continuity.get("faults") == 0
            and continuity.get("duck_visible") is False
        )
        result["passed"] = passed
        result["capture_breach_ms"] = CAPTURE_BREACH_MS
        return result, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actions", type=int, default=500)
    args = parser.parse_args()
    result, passed = run(max(1, args.actions))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Recompile probe observations from recorded viewer boards and gate artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inference.agent.runtime_state import Frame
from inference.framework.probe_evidence import compact_probe_outcome, compile_probe_outcome


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def replay(artifacts: Path) -> dict[str, Any]:
    stems = sorted(
        path.name.removesuffix("_probe_envelopes.jsonl")
        for path in artifacts.glob("*_probe_envelopes.jsonl")
    )
    games: list[dict[str, Any]] = []
    for stem in stems:
        viewer = _rows(artifacts / f"{stem}_events.jsonl")
        probes = _rows(artifacts / f"{stem}_probe_envelopes.jsonl")
        gate_events = _rows(artifacts / f"{stem}_gate_events.jsonl")
        gate_answers = _rows(artifacts / f"{stem}_gate_answers.jsonl")
        board_events = [row for row in viewer if isinstance(row.get("board"), list)]
        action_events = [row for row in board_events if row.get("type") == "action"]
        checks = {
            "one_recorded_probe": len(probes) == 1,
            "one_recorded_action": len(action_events) == 1,
            "before_board_available": len(board_events) >= 2,
            "probe_event_join": bool(probes)
            and bool(gate_events)
            and probes[0].get("probe_id") == gate_events[0].get("probe_id"),
        }
        observation = None
        if all(checks.values()):
            action_event = action_events[0]
            action_index = board_events.index(action_event)
            before_event = board_events[action_index - 1]
            probe = probes[0]
            action = (probe.get("actions") or [{}])[0]
            callback = dict(gate_events[0].get("outcome") or action_event)
            callback.setdefault("board_changed", action_event.get("board_changed"))
            callback.setdefault("state", action_event.get("state"))
            before = Frame(
                grid=tuple(tuple(int(cell) for cell in row) for row in before_event["board"]),
                step=int(before_event.get("action_num") or 0),
                level=int(before_event.get("level") or 1),
            )
            after = Frame(
                grid=tuple(tuple(int(cell) for cell in row) for row in action_event["board"]),
                step=int(action_event.get("action_num") or 1),
                level=int(action_event.get("level") or 1),
            )
            action_surface = next(
                (
                    row.get("action_metadata") or []
                    for row in gate_answers
                    if row.get("gate_id") == "G0-ACTION-METADATA"
                ),
                [],
            )
            available_before = [
                str(item.get("action")) for item in action_surface if isinstance(item, dict)
            ]
            observation = compact_probe_outcome(compile_probe_outcome(
                probe_id=str(probe["probe_id"]),
                transition_id=int(action_event.get("action_num") or 1),
                action=action,
                before_frame=before,
                after_frame=after,
                available_actions_before=available_before,
                available_actions_after=list(callback.get("valid_actions") or []),
                callback_payload=callback,
            ))
        games.append({
            "game": stem,
            "checks": checks,
            "passed": all(checks.values()),
            "observation": observation,
        })
    return {
        "schema": "virelai-h2-evidence-replay-v1",
        "source": str(artifacts),
        "claim_limit": (
            "Recompiles integer-grid observations from recorded artifacts; does not infer game mechanics."
        ),
        "games": games,
        "passed": bool(games) and all(game["passed"] for game in games),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = replay(args.artifacts.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Compile a bounded, role-free player view from verified continuity artifacts.

This is an offline presentation gate.  It does not alter Duck prompts or tools.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def compile_view(game_root: Path, *, level: int | None = None, limit: int = 20) -> dict[str, Any]:
    tracks = _json(game_root / "continuity_tracks.json")
    targeted = _jsonl(game_root / "acted_on.jsonl")
    targeted_by_track: dict[int, list[dict[str, Any]]] = {}
    for record in targeted:
        track_id = record.get("worldline_id")
        if track_id is not None and record.get("status") == "RESOLVED":
            targeted_by_track.setdefault(int(track_id), []).append(record)

    if level is None:
        level = max((int(track["level"]) for track in tracks), default=1)
    stitches_by_edge: dict[tuple[int, int], list[tuple[str, str]]] = {}
    for other in tracks:
        if int(other["level"]) != level:
            continue
        for stitch in other["stitches"]:
            stitches_by_edge.setdefault(
                (int(stitch["from_node"]), int(stitch["to_node"])), []
            ).append((str(other["display_id"]), str(stitch["verb"])))
    entries = []
    for track in tracks:
        if int(track["level"]) != level:
            continue
        observations = track["observations"]
        stitches = track["stitches"]
        first, latest = observations[0], observations[-1]
        verb_counts = Counter(item["verb"] for item in stitches)
        nonstill = sum(count for verb, count in verb_counts.items() if verb != "STILL")
        presses = targeted_by_track.get(int(track["track_id"]), [])
        stitch_by_edge = {
            (int(item["from_node"]), int(item["to_node"])): item for item in stitches
        }
        targeted_outcomes: Counter[str] = Counter()
        coincident: dict[str, Counter[str]] = {}
        unresolved_target_responses = 0
        for press in presses:
            edge_key = (int(press["issued_from_node"]), int(press["result_node"]))
            stitch = stitch_by_edge.get(edge_key)
            if stitch is None:
                unresolved_target_responses += 1
            else:
                targeted_outcomes[str(stitch["verb"])] += 1
            for affected_handle, form in stitches_by_edge.get(edge_key, []):
                if form == "STILL":
                    continue
                coincident.setdefault(affected_handle, Counter())[form] += 1
        coincident_rows = [
            {
                "handle": handle,
                "observed_forms_after_targeting": dict(sorted(forms.items())),
                "observations": sum(forms.values()),
            }
            for handle, forms in coincident.items()
        ]
        coincident_rows.sort(key=lambda item: (-item["observations"], item["handle"]))
        entries.append({
            "handle": track["display_id"],
            "level": int(track["level"]),
            "observed_from_step": int(track["born_node"]),
            "observed_through_step": int(track["last_seen_node"]),
            "end_reason": track["end_reason"],
            "observations": len(observations),
            "first": {
                "integer": int(first["class_id"]),
                "cells": int(first["cell_count"]),
                "bbox": first["bbox"],
            },
            "latest": {
                "integer": int(latest["class_id"]),
                "cells": int(latest["cell_count"]),
                "bbox": latest["bbox"],
            },
            "observed_forms": dict(sorted(verb_counts.items())),
            "targeted": {
                "presses": len(presses),
                "observed_self_responses": dict(sorted(targeted_outcomes.items())),
                "responses_without_continuing_link": unresolved_target_responses,
                "coincident_worldline_changes": coincident_rows[:8],
                "coincident_changes_truncated": len(coincident_rows) > 8,
            },
            "_rank": (bool(presses), nonstill, len(stitches)),
        })
    entries.sort(
        key=lambda item: (
            -int(item["_rank"][0]), -item["_rank"][1], -item["_rank"][2], item["handle"]
        )
    )
    total = len(entries)
    entries = entries[: max(1, limit)]
    for item in entries:
        item.pop("_rank", None)
    return {
        "schema": "virelai-player-worldlines-preview-v1",
        "game": game_root.name,
        "level": level,
        "correspondence_status": (
            "INTERIM_O9 visible correspondence; handles are evidence-backed tracking "
            "hypotheses, not proven semantic identities"
        ),
        "roles_inferred": False,
        "total_level_worldlines": total,
        "worldlines_returned": len(entries),
        "truncated": len(entries) < total,
        "worldlines": entries,
    }


def render_markdown(view: dict[str, Any]) -> str:
    lines = [
        f"# Player worldlines preview — {view['game']} · level {view['level']}",
        "",
        f"Status: {view['correspondence_status']}.",
        "No ego, lever, counter, cause, or objective labels are inferred.",
        "",
        f"Showing {view['worldlines_returned']} of {view['total_level_worldlines']} histories.",
        "",
    ]
    for item in view["worldlines"]:
        first, latest, targeted = item["first"], item["latest"], item["targeted"]
        lines.extend([
            f"## {item['handle']}",
            "",
            f"- Seen: steps {item['observed_from_step']}–{item['observed_through_step']} "
            f"({item['observations']} frames); end: {item['end_reason']}.",
            f"- First: integer {first['integer']}, {first['cells']} cells, bbox {first['bbox']}.",
            f"- Latest: integer {latest['integer']}, {latest['cells']} cells, bbox {latest['bbox']}.",
            f"- Observed history: {item['observed_forms']}.",
            f"- Directly targeted {targeted['presses']} times; observed self-response: "
            f"{targeted['observed_self_responses'] or 'none'}; responses without a continuing "
            f"link: {targeted['responses_without_continuing_link']}.",
            f"- Other tracked changes immediately after those targets: "
            f"{targeted['coincident_worldline_changes'] or 'none'}.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--level", type=int)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    view = compile_view(args.game_root.resolve(), level=args.level, limit=args.limit)
    if args.json_output:
        args.json_output.write_text(json.dumps(view, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(view), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(json.dumps(view, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Create immutable player physics grammars from completed level histories."""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
from typing import Any

from tools.render_physics_grammar import compile_grammar, render_markdown


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def compile_post_win(
    library: dict[str, Any], capsules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grammar = compile_grammar(library)
    level_rows = {int(item["level"]): item for item in grammar["levels"]}
    outputs = []
    for capsule in capsules:
        level = int(capsule["completed_level"])
        if level not in level_rows:
            continue
        row = dict(level_rows[level])
        row["observed_win"] = {
            "actor": capsule.get("actor"),
            "action": capsule.get("action_name"),
            "acted_cell": capsule.get("acted_cell"),
            "transition_id": capsule.get("transition_id"),
            "status": "OBSERVED_LEVEL_COMPLETION",
            "causal_limit": (
                "This action ended the level. The record does not yet prove which preceding "
                "configuration made it successful."
            ),
        }
        outputs.append({
            "schema": "virelai-post-win-physics-grammar-v1",
            "game": grammar["game"],
            "completed_level": level,
            "basis": grammar["basis"],
            "levels": [row],
        })
    return outputs


def _visible_frames(game_root: Path) -> dict[int, list[list[int]]]:
    binary = (game_root / "frames.bin").read_bytes()
    frames = {}
    for item in _jsonl(game_root / "frames.jsonl"):
        layer = item["layers"][-1]
        rows, cols = int(layer["rows"]), int(layer["cols"])
        start = int(item["archive_offset"]) + int(layer["byte_offset"])
        raw = binary[start:start + int(layer["byte_length"])]
        frames[int(item["node_index"])] = [
            list(raw[row * cols:(row + 1) * cols]) for row in range(rows)
        ]
    return frames


def _region_state(frame: list[list[int]], bbox: list[int]) -> dict[str, Any]:
    top, left, bottom, right = bbox
    counts = Counter(
        frame[row][col]
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    )
    return {"integer_counts": {str(key): counts[key] for key in sorted(counts)}}


def _known_regions(library: dict[str, Any], level: int) -> list[dict[str, Any]]:
    boxes = []
    for segment in library.get("segments", []):
        if int(segment.get("level", 0)) != level:
            continue
        mechanics = segment.get("lever_mechanics") or {}
        for item in mechanics.get("reactive_controls", []):
            bbox = (item.get("visible") or {}).get("bbox")
            if bbox is not None:
                boxes.append(tuple(bbox))
        for item in mechanics.get("levers", []):
            bbox = (item.get("visible") or {}).get("bbox")
            if bbox is not None:
                boxes.append(tuple(bbox))
            for target in item.get("targets", []):
                target_bbox = (target.get("visible") or {}).get("bbox")
                if target_bbox is not None:
                    boxes.append(tuple(target_bbox))
    unique = sorted(set(boxes))
    return [
        {"name": f"Observed mechanic region {chr(65 + index)}", "bbox": list(bbox)}
        for index, bbox in enumerate(unique)
    ]


def _minimal_separator(win: list[Any], failed: list[list[Any]]) -> tuple[int, ...] | None:
    if not failed:
        return None
    candidates = [index for index in range(len(win)) if any(row[index] != win[index] for row in failed)]
    # A large conjunction is neither player-useful nor safe on the query path. Exact within
    # the declared three-region explanation budget; abstain beyond it.
    for width in range(1, min(3, len(candidates)) + 1):
        for chosen in combinations(candidates, width):
            if all(any(row[index] != win[index] for index in chosen) for row in failed):
                return chosen
    return None


def _win_configuration(
    *, game_root: Path, library: dict[str, Any], capsule: dict[str, Any],
    frames: dict[int, list[list[int]]], events: list[dict[str, Any]],
) -> dict[str, Any]:
    level = int(capsule["completed_level"])
    regions = _known_regions(library, level)
    pre_node = int(capsule["pre_win_ref"]["node_index"])
    win_node = int(capsule["winning_render_ref"]["node_index"])
    if pre_node not in frames or win_node not in frames or not regions:
        return {
            "status": "INSUFFICIENT_OBJECT_MODEL", "earlier_same_action_failures": 0,
            "distinguishing_conditions": [], "winning_target_change": None,
        }
    win_states = [_region_state(frames[pre_node], item["bbox"]) for item in regions]
    earlier = [
        item for item in events
        if item.get("event") == "TRANSITION"
        and int(item.get("level_before", 0)) == level
        and int(item.get("transition_id", 0)) < int(capsule["transition_id"])
        and item.get("action_name") == capsule.get("action_name")
        and not item.get("level_completed")
        and int(item.get("from_node", -1)) in frames
    ]
    failed_states = [
        [_region_state(frames[int(event["from_node"])], item["bbox"]) for item in regions]
        for event in earlier
    ]
    chosen = _minimal_separator(win_states, failed_states)
    conditions = [] if chosen is None else [
        {
            **regions[index],
            "winning_pre_state": win_states[index],
            "failed_pre_states": [
                json.loads(value) for value in sorted(
                    {json.dumps(row[index], sort_keys=True) for row in failed_states}
                )
            ],
        }
        for index in chosen
    ]
    acted = capsule.get("acted_cell")
    target = next((item for item in regions if acted is not None and
                   item["bbox"][0] <= acted[0] <= item["bbox"][2] and
                   item["bbox"][1] <= acted[1] <= item["bbox"][3]), None)
    target_change = None if target is None else {
        **target,
        "before": _region_state(frames[pre_node], target["bbox"]),
        "after": _region_state(frames[win_node], target["bbox"]),
    }
    status = (
        "MINIMAL_OBSERVED_SEPARATOR" if conditions else
        "NO_EARLIER_EXACT_ACTION_CONTRAST" if not earlier else
        "NO_SEPARATOR_WITHIN_THREE_REGION_BUDGET"
    )
    return {
        "status": status,
        "earlier_same_action_failures": len(earlier),
        "distinguishing_conditions": conditions,
        "winning_target_change": target_change,
        "causal_limit": (
            "The separator distinguishes this recorded win from the recorded exact-action "
            "failures. It is a candidate necessary context in this record, not a proven cause."
        ),
    }
def render_post_win(grammar: dict[str, Any]) -> str:
    text = render_markdown(grammar).rstrip()
    level = grammar["levels"][0]
    win = level["observed_win"]
    explanation = level.get("win_explanation") or {}
    lines = [
        text + "\n\n### Observed level completion\n\n"
        f"- Actor: {win['actor']}.\n"
        f"- Winning action: {win['action']}; acted cell {win['acted_cell']}; "
        f"transition {win['transition_id']}.\n"
        f"- Limit: {win['causal_limit']}\n",
        "### How this winning state differed\n",
    ]
    if explanation.get("distinguishing_conditions"):
        lines.append(
            f"Compared with {explanation['earlier_same_action_failures']} earlier failed use(s) "
            "of this exact action, the smallest observed separator was:\n"
        )
        for condition in explanation["distinguishing_conditions"]:
            lines.append(
                f"- {condition['name']} at {condition['bbox']}: winning pre-state "
                f"{condition['winning_pre_state']['integer_counts']}; earlier failed states "
                f"{[item['integer_counts'] for item in condition['failed_pre_states']]}."
            )
    else:
        lines.append(
            f"No object-level separator was earned: {explanation.get('status', 'UNMEASURED')}."
        )
    if explanation.get("winning_target_change"):
        target = explanation["winning_target_change"]
        lines.append(
            f"- Winning target {target['name']} at {target['bbox']} changed from "
            f"{target['before']['integer_counts']} to {target['after']['integer_counts']}."
        )
    lines.append(f"\nLimit: {explanation.get('causal_limit', win['causal_limit'])}\n")
    return "\n".join(lines)


def write_post_win(game_root: Path, output_dir: Path) -> list[dict[str, Any]]:
    library = json.loads((game_root / "semantic_library.json").read_text(encoding="utf-8"))
    capsules = _jsonl(game_root / "win_capsules.jsonl")
    outputs = compile_post_win(library, capsules)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not outputs:
        (output_dir / "index.json").write_text("[]", encoding="utf-8")
        return []
    frames = _visible_frames(game_root)
    events = _jsonl(game_root / "events.jsonl")
    capsule_by_level = {int(item["completed_level"]): item for item in capsules}
    for grammar in outputs:
        capsule = capsule_by_level[int(grammar["completed_level"])]
        grammar["levels"][0]["win_explanation"] = _win_configuration(
            game_root=game_root, library=library, capsule=capsule, frames=frames, events=events,
        )
    index = []
    for grammar in outputs:
        level = grammar["completed_level"]
        json_name = f"level_{level}_physics_grammar.json"
        md_name = f"LEVEL_{level}_PHYSICS_GRAMMAR.md"
        (output_dir / json_name).write_text(json.dumps(grammar, indent=2, sort_keys=True), encoding="utf-8")
        (output_dir / md_name).write_text(render_post_win(grammar), encoding="utf-8")
        index.append({"completed_level": level, "json": json_name, "markdown": md_name})
    (output_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    index = write_post_win(args.game_root.resolve(), args.output_dir.resolve())
    print(json.dumps({"post_win_grammars": len(index), "items": index}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

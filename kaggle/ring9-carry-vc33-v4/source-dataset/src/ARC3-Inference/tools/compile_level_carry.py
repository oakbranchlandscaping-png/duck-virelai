"""Compile conservative level-to-level memory from immutable post-win artifacts."""
from __future__ import annotations

import argparse
from collections import deque
import json
from math import gcd
from pathlib import Path
from typing import Any, Iterable

from tools.compile_post_win_grammars import _jsonl
from tools.compile_post_win_grammars import render_post_win


def _normalized_shape(cells: Iterable[tuple[int, int]]) -> tuple[int, int, tuple[int, ...]]:
    """Port of V4 cross_level_identity.scale_normalized_shape."""
    cells = set(cells)
    if not cells:
        return (0, 0, ())
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    mask = tuple(int((r0 + r, c0 + c) in cells) for r in range(height) for c in range(width))
    scale = gcd(height, width)
    while scale > 1:
        uniform = all(
            len({mask[(br * scale + dr) * width + bc * scale + dc]
                 for dr in range(scale) for dc in range(scale)}) == 1
            for br in range(height // scale) for bc in range(width // scale)
        )
        if uniform:
            mask = tuple(mask[(br * scale) * width + bc * scale]
                         for br in range(height // scale) for bc in range(width // scale))
            height, width = height // scale, width // scale
            scale = gcd(height, width)
        else:
            scale -= 1
    return height, width, mask


def _frames(game_root: Path) -> dict[tuple[int, int], list[list[int]]]:
    binary = (game_root / "frames.bin").read_bytes()
    result = {}
    for item in _jsonl(game_root / "frames.jsonl"):
        for layer_index, layer in enumerate(item["layers"]):
            rows, cols = int(layer["rows"]), int(layer["cols"])
            start = int(item["archive_offset"]) + int(layer["byte_offset"])
            raw = binary[start:start + int(layer["byte_length"])]
            result[(int(item["node_index"]), layer_index)] = [
                list(raw[row * cols:(row + 1) * cols]) for row in range(rows)
            ]
    return result


def _components(frame: list[list[int]], allowed: set[int]) -> list[dict[str, Any]]:
    rows, cols = len(frame), len(frame[0])
    seen: set[tuple[int, int]] = set()
    output = []
    for row in range(rows):
        for col in range(cols):
            value = frame[row][col]
            if value not in allowed or (row, col) in seen:
                continue
            queue, cells = deque([(row, col)]), []
            seen.add((row, col))
            while queue:
                rr, cc = queue.popleft(); cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen and frame[nr][nc] == value:
                        seen.add((nr, nc)); queue.append((nr, nc))
            output.append({
                "integer_class": value,
                "bbox": [min(r for r, _ in cells), min(c for _, c in cells),
                         max(r for r, _ in cells), max(c for _, c in cells)],
                "cell_count": len(cells),
                "shape": _normalized_shape(cells),
            })
    return output


def compile_level_carry(game_root: Path, post_win_dir: Path) -> list[dict[str, Any]]:
    library = json.loads((game_root / "semantic_library.json").read_text(encoding="utf-8"))
    frames = _frames(game_root)
    outputs = []
    for capsule in _jsonl(game_root / "win_capsules.jsonl"):
        if capsule.get("terminal") or not capsule.get("successor_spawn_ref"):
            continue
        level = int(capsule["completed_level"])
        grammar_path = post_win_dir / f"level_{level}_physics_grammar.json"
        if not grammar_path.exists():
            continue
        grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
        pre_ref, spawn_ref = capsule["pre_win_ref"], capsule["successor_spawn_ref"]
        pre = frames.get((int(pre_ref["node_index"]), int(pre_ref.get("layer_index", 0))))
        spawn = frames.get((int(spawn_ref["node_index"]), int(spawn_ref.get("layer_index", 0))))
        if pre is None or spawn is None:
            continue
        level_grammar = grammar["levels"][0]
        typed_regions = []
        for control in level_grammar.get("remote_levers", []) + level_grammar.get("self_reactive_controls", []):
            location = control.get("location")
            if location is not None:
                typed_regions.append({"name": control["name"], "bbox": location})
        priors = []
        for region in typed_regions:
            top, left, bottom, right = region["bbox"]
            by_class: dict[int, list[tuple[int, int]]] = {}
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    by_class.setdefault(pre[row][col], []).append((row, col))
            # Mechanic boxes can contain background. A type prior describes the
            # visible object, not every integer occurring inside its rectangle.
            foreground = [(value, cells) for value, cells in by_class.items() if value != 0]
            choices = foreground or list(by_class.items())
            value, cells = max(choices, key=lambda item: (len(item[1]), -item[0]))
            priors.append({"source": region, "integer_class": value,
                           "shape": _normalized_shape(cells)})
        candidates = _components(spawn, {item["integer_class"] for item in priors})
        matches = []
        for prior in priors:
            found = [candidate for candidate in candidates
                     if prior["integer_class"] == candidate["integer_class"]
                     and prior["shape"] == candidate["shape"]]
            if found:
                matches.append({
                    "prior_region": prior["source"],
                    "integer_class": prior["integer_class"],
                    "candidate_count": len(found),
                    "new_spawn_candidates": [
                        {k: v for k, v in candidate.items() if k != "shape"}
                        for candidate in found[:12]
                    ],
                    "truncated": len(found) > 12,
                    "basis": "same integer class and scale-normalized visible shape",
                    "status": ("UNTESTED_TYPE_CORRESPONDENCE" if len(found) == 1
                               else "AMBIGUOUS_UNTESTED_TYPE_CORRESPONDENCE"),
                })
        outputs.append({
            "schema": "virelai-level-carry-v1", "game": library.get("game_id"),
            "completed_level": level, "new_level": level + 1,
            "completed_level_grammar": grammar,
            "candidate_type_correspondences": matches,
            "carry_rule": "The completed-level mechanics and win record are evidence about the prior level and hypotheses for this one, not guarantees.",
            "must_relearn": ["current object locations and instances", "control role",
                             "each mechanism and affected region", "the winning condition"],
        })
    return outputs


def render_level_carry(item: dict[str, Any]) -> str:
    lines = [
        f"# What survived into level {item['new_level']}", "",
        f"## How level {item['completed_level']} worked and ended", "",
        render_post_win(item["completed_level_grammar"]).rstrip(), "",
        f"## What may correspond in level {item['new_level']}", "",
    ]
    matches = item["candidate_type_correspondences"]
    if not matches:
        lines.append("- No learned control type has a visible new-spawn match. Do not force one.")
    for match in matches:
        source = match["prior_region"]
        boxes = [candidate["bbox"] for candidate in match["new_spawn_candidates"]]
        ambiguity = "ambiguous" if match["candidate_count"] > 1 else "single visible candidate"
        lines.append(
            f"- {source['name']} from {source['bbox']}: {ambiguity}; class "
            f"{match['integer_class']}, candidate location(s) {boxes}. This is untested."
        )
    lines.extend(["", "## Boundary rule", "", f"- {item['carry_rule']}",
                  "- Relearn: " + "; ".join(item["must_relearn"]) + ".", ""])
    return "\n".join(lines)


def write_level_carry(game_root: Path, post_win_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    outputs = compile_level_carry(game_root, post_win_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for item in outputs:
        name = f"after_level_{item['completed_level']}_carry.json"
        markdown = f"AFTER_LEVEL_{item['completed_level']}_CARRY.md"
        (output_dir / name).write_text(json.dumps(item, indent=2, sort_keys=True), encoding="utf-8")
        (output_dir / markdown).write_text(render_level_carry(item), encoding="utf-8")
        index.append({"completed_level": item["completed_level"], "new_level": item["new_level"],
                      "artifact": name, "markdown": markdown})
    (output_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--post-win-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.game_root.resolve()
    post = args.post_win_dir.resolve() if args.post_win_dir else root / "post_win_grammars_v3"
    print(json.dumps(write_level_carry(root, post, args.output_dir.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

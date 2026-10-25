#!/usr/bin/env python3
"""List every object in each level's entry frame, for authoring an answer key (WO-PE-03C; F4).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §1 F4, §3.

Reads a frame recording of play in the golden format (``*.golden.jsonl``: one header line, then one line per frame
with ``frame`` (layers; the settled grid is the last), ``levels_completed`` and ``action``). A level's entry frame is
the first frame and each frame where ``levels_completed`` rises.

For each entry frame it prints the board hash a key cites (``construction.entry_frames``) and every object in the
census segmentation (``library_census.board_cut``: single-class, 4-connected): handle, class, anchor, bbox and cell
count. It reads no solver output, no world model and no report.

    python tools/paper_key_frames.py RECORDING.golden.jsonl [--out DIR]

With ``--out`` it also writes ``<game>_entry_objects.json`` (the listing) and ``<game>_key_skeleton.json`` (a key
with the game, levels and entry frames filled and no items, for the Director to author).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.framework.library_census import board_cut  # noqa: E402
from inference.framework.win_episode import board_sha256  # noqa: E402


def entry_frames(lines: list[dict]) -> tuple[str, dict[int, list[list[int]]]]:
    """(game_id, level -> settled entry grid) from a golden recording's frame lines."""
    game_id, found, completed = "", {}, None
    for row in lines:
        if "frame" not in row:
            continue
        game_id = game_id or str(row.get("game_id") or "")
        done = int(row.get("levels_completed") or 0)
        if completed is None or done > completed:
            found.setdefault(done + 1, [[int(v) for v in r] for r in row["frame"][-1]])
            completed = done
    return game_id, found


def objects(grid: list[list[int]], level: int) -> list[dict]:
    cut = board_cut(grid, node=0, level=level)
    rows = [{"handle": f"c{r.class_id}@{r.anchor[0]},{r.anchor[1]}", "class": r.class_id, "anchor": list(r.anchor),
             "bbox": list(r.bbox), "cell_count": r.cell_count} for r in cut.regions]
    return sorted(rows, key=lambda r: (r["anchor"], r["class"]))


def listing(path: Path) -> dict:
    lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    game_id, frames = entry_frames(lines)
    return {"game_id": game_id, "recording": path.name,
            "levels": {str(level): {"board_sha256": board_sha256(grid), "objects": objects(grid, level)}
                       for level, grid in sorted(frames.items())}}


def skeleton(found: dict) -> dict:
    return {"schema": "virelai-paper-key-v1", "game_id": found["game_id"],
            "levels": [int(level) for level in found["levels"]],
            "construction": {"author": "Director", "method": "PLAY", "frozen_on": "YYYY-MM-DD", "commit": None,
                             "blind_to_reports": True,
                             "entry_frames": {level: row["board_sha256"] for level, row in found["levels"].items()}},
            "sources": [], "items": []}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("recording", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    found = listing(args.recording)
    for level, row in found["levels"].items():
        print(f"{found['game_id']} level {level} entry board_sha256 {row['board_sha256']}")
        for obj in row["objects"]:
            print(f"  {obj['handle']:<14} class {obj['class']:>2}  anchor {obj['anchor']}  bbox {obj['bbox']}"
                  f"  cells {obj['cell_count']}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / f"{found['game_id']}_entry_objects.json").write_text(json.dumps(found, indent=1, sort_keys=True) + "\n")
        (args.out / f"{found['game_id']}_key_skeleton.json").write_text(json.dumps(skeleton(found), indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

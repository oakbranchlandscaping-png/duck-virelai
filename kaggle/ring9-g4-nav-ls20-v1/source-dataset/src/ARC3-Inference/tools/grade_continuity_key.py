"""Grade continuity stitches against a frozen key and Tufa's shape-hash rule."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.inspect_archive_components import segment_visible_components
from tools.replay_continuity_archives import _frames, _read_jsonl


def _validate_archive_provenance(key: dict, source_root: Path) -> list[dict[str, str]]:
    """Refuse to grade a hand key against recordings it did not label."""
    rows: list[dict[str, str]] = []
    for game, expected in sorted(key.get("archives", {}).items()):
        frames_path = source_root / game / "frames.bin"
        if not frames_path.is_file():
            raise FileNotFoundError(f"missing keyed recording: {frames_path}")
        actual_hash = hashlib.sha256(frames_path.read_bytes()).hexdigest()
        expected_hash = str(expected["frames_bin_sha256"])
        if actual_hash != expected_hash:
            raise ValueError(
                "recording provenance mismatch for "
                f"{game}: expected frames.bin sha256 {expected_hash}, got {actual_hash}"
            )
        rows.append({
            "game": game,
            "frames_bin_sha256": actual_hash,
            "status": "MATCH",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("key", type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--replay-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = json.loads(args.key.read_text(encoding="utf-8"))
    archive_provenance = _validate_archive_provenance(key, args.source_root)
    source_cache = {}
    event_cache = {}
    rows = []
    for judgment in key["judgments"]:
        game = judgment["game"]
        if game not in source_cache:
            source_cache[game] = _frames(args.source_root / game)
            event_cache[game] = _read_jsonl(args.replay_root / game / "continuity.jsonl")
        before_frame = source_cache[game][int(judgment["step_before"])]
        after_frame = source_cache[game][int(judgment["step_after"])]

        def components(frame, step, level):
            layers = []
            payload = bytearray()
            for raw_layer in frame.frame:
                rows_count = len(raw_layer)
                cols_count = len(raw_layer[0]) if raw_layer else 0
                offset = len(payload)
                for row in raw_layer:
                    payload.extend(row)
                layers.append(type("Layer", (), {"rows": rows_count, "cols": cols_count, "byte_offset": offset, "byte_length": rows_count * cols_count})())
            record = type("Record", (), {
                "node_index": step,
                "layers": layers,
                "layer_bytes": lambda self, index: bytes(payload[layers[index].byte_offset : layers[index].byte_offset + layers[index].byte_length]),
            })()
            return {item.component_id: item for item in segment_visible_components(record, level=level)}

        before = components(before_frame, int(judgment["step_before"]), int(judgment["level"]))[int(judgment["node_before"])]
        after_level = int(judgment["level"]) + (1 if int(judgment["step_after"]) > int(judgment["step_before"]) and after_frame.levels_completed > before_frame.levels_completed else 0)
        after = components(after_frame, int(judgment["step_after"]), after_level)[int(judgment["node_after"])]
        stitch = next(
            (
                item
                for item in event_cache[game]
                if item.get("event") == "STITCH"
                and int(item["from_node"]) == int(judgment["step_before"])
                and int(item["from_component"]) == int(judgment["node_before"])
                and int(item["to_node"]) == int(judgment["step_after"])
                and int(item["to_component"]) == int(judgment["node_after"])
            ),
            None,
        )
        predicted = "CONTINUE" if stitch else "DISCONTINUE"
        expected = judgment["expected"]
        verb_correct = not judgment.get("verb") or bool(stitch and stitch.get("verb") == judgment["verb"])
        tufa_predicted = "CONTINUE" if before.shape_hash == after.shape_hash else "DISCONTINUE"
        rows.append({
            "game": game,
            "pair": [judgment["step_before"], judgment["node_before"], judgment["step_after"], judgment["node_after"]],
            "expected": expected,
            "virelai": predicted,
            "virelai_verb": stitch.get("verb") if stitch else None,
            "virelai_correct": predicted == expected and verb_correct,
            "tufa_shape_hash": tufa_predicted,
            "tufa_correct": tufa_predicted == expected,
        })
    report = {
        "schema": "virelai-continuity-grade-v1",
        "archive_provenance": archive_provenance,
        "judgments": len(rows),
        "virelai_correct": sum(row["virelai_correct"] for row in rows),
        "virelai_false_links": sum(row["expected"] == "DISCONTINUE" and row["virelai"] == "CONTINUE" for row in rows),
        "virelai_missed_links": sum(row["expected"] == "CONTINUE" and row["virelai"] != "CONTINUE" for row in rows),
        "tufa_correct": sum(row["tufa_correct"] for row in rows),
        "virelai_only_correct_links": sum(row["expected"] == "CONTINUE" and row["virelai_correct"] and not row["tufa_correct"] for row in rows),
        "virelai_prevents_tufa_false_links": sum(row["expected"] == "DISCONTINUE" and row["virelai_correct"] and not row["tufa_correct"] for row in rows),
        "rows": rows,
    }
    report["passed"] = report["virelai_correct"] == report["judgments"] and report["virelai_false_links"] == 0
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Print literal component observations from a lossless archive; no matching."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from inference.framework.virelai_continuity import segment_visible_components


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--nodes", default="0:5", help="Python-style start:stop")
    parser.add_argument("--max-components", type=int, default=30)
    args = parser.parse_args()
    start_text, stop_text = (args.nodes.split(":", 1) + [""])[:2]
    start = int(start_text or 0)
    stop = int(stop_text) if stop_text else None
    indexes = [json.loads(line) for line in (args.archive / "frames.jsonl").read_text().splitlines() if line.strip()]
    binary = (args.archive / "frames.bin").read_bytes()
    for item in indexes[start:stop]:
        base = int(item["archive_offset"])
        layers = []
        for layer in item["layers"]:
            rows, cols = int(layer["rows"]), int(layer["cols"])
            offset = base + int(layer["byte_offset"])
            raw = binary[offset : offset + int(layer["byte_length"])]
            layers.append(SimpleNamespace(rows=rows, cols=cols, raw=raw))
        record = SimpleNamespace(
            node_index=int(item["node_index"]),
            layers=layers,
            layer_bytes=lambda index, layers=layers: layers[index].raw,
        )
        level = max(1, int(item.get("levels_completed") or 0) + 1)
        components = segment_visible_components(record, level=level)
        shown = sorted(components, key=lambda component: (component.cell_count, component.component_id))[: args.max_components]
        print(json.dumps({
            "node": record.node_index,
            "level": level,
            "state": item.get("state"),
            "action_id": item.get("action_id"),
            "components": [component.reference() for component in shown],
            "component_count": len(components),
            "omitted_largest": max(0, len(components) - len(shown)),
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

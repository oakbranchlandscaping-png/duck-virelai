#!/usr/bin/env python3
"""Compile replay-only controller artifacts from persisted world models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from inference.framework.virelai_controller import (
    build_controller_snapshot,
    canonical_controller_bytes,
)
from inference.framework.virelai_world_model import world_model_from_dict


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("world_models", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in sorted(args.world_models, key=lambda item: str(item)):
        model = world_model_from_dict(json.loads(path.read_text()))
        first = canonical_controller_bytes(build_controller_snapshot(model))
        second = canonical_controller_bytes(build_controller_snapshot(model))
        if first != second:
            raise RuntimeError(f"non-deterministic replay: {path}")
        destination = args.output_dir / f"{model.game_id}.controller.json"
        destination.write_bytes(first)
        manifest.append({
            "game_id": model.game_id,
            "source": str(path),
            "output": str(destination),
            "bytes_equal_on_recompile": True,
        })
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"compiled": len(manifest), "output_dir": str(args.output_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate the self-hosting Kaggle kernels from the kit (Director pushes them with the Kaggle CLI).

Author: Claude (Alpha build seat), 2026-10-01.

  wheelhouse-v3/       builds the vLLM wheelhouse byte for byte from wheelhouse_v3.lock.json into
                       /kaggle/working (about 5.2 GB; internet on, no GPU). Make it a
                       dataset from the notebook's output.
  model-<slug>/        mirrors one pinned Hugging Face model revision into a private dataset you own,
                       through the Kaggle CLI with your credentials as notebook secrets.

Usage:
  python3 make_kernels.py OWNER [--model REPO=DATASET_SLUG[@REVISION]] ...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
MAIN_LINE = 'if __name__ == "__main__":\n    sys.exit(main(sys.argv))\n'
MIRROR_MAIN_LINE = 'if __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))\n'


def _metadata(owner: str, slug: str, title: str, code_file: str) -> dict:
    return {
        "id": f"{owner}/{slug}", "title": title, "code_file": code_file, "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": True, "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
        "model_sources": [],
    }


def wheelhouse_kernel(owner: str, out: Path) -> Path:
    source = (KIT / "build_wheelhouse.py").read_text()
    lock = json.loads((KIT / "wheelhouse_v3.lock.json").read_text())
    if source.count("EMBEDDED_LOCK: dict[str, Any] | None = None") != 1 or source.count(MAIN_LINE) != 1:
        raise RuntimeError("build_wheelhouse.py changed shape; update make_kernels.py")
    source = source.replace("EMBEDDED_LOCK: dict[str, Any] | None = None",
                            "EMBEDDED_LOCK: dict[str, Any] | None = " + json.dumps(lock, sort_keys=True))
    target = out / "wheelhouse-v3"
    target.mkdir(parents=True, exist_ok=True)
    (target / "build_wheelhouse_v3.py").write_text(source)
    meta = _metadata(owner, "virelai-build-vllm-wheelhouse-v3", "virelai-build-vllm-wheelhouse-v3", "build_wheelhouse_v3.py")
    (target / "kernel-metadata.json").write_text(json.dumps(meta, indent=1) + "\n")
    return target


def model_kernel(owner: str, spec: str, out: Path) -> Path:
    match = re.fullmatch(r"([\w.\-]+/[\w.\-]+)=([a-z0-9][a-z0-9\-]{4,48})(?:@([\w.\-]+))?", spec)
    if not match:
        raise SystemExit(f"--model must be REPO=DATASET_SLUG[@REVISION], got {spec!r}")
    repo, slug, revision = match.group(1), match.group(2), match.group(3) or "main"
    source = (KIT / "mirror_model.py").read_text()
    if source.count(MIRROR_MAIN_LINE) != 1:
        raise RuntimeError("mirror_model.py changed shape; update make_kernels.py")
    argv = ["--repo", repo, "--revision", revision, "--out", "/tmp/model-mirror", "--dataset", f"{owner}/{slug}",
            "--exclude", "original/*", "--publish", "--kaggle-secrets"]
    source = source.replace(MIRROR_MAIN_LINE, f'if __name__ == "__main__":\n    sys.exit(main({argv!r}))\n')
    target = out / f"model-{slug}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "mirror_model_kernel.py").write_text(source)
    meta = _metadata(owner, f"virelai-mirror-{slug}"[:50], f"virelai-mirror-{slug}"[:50], "mirror_model_kernel.py")
    (target / "kernel-metadata.json").write_text(json.dumps(meta, indent=1) + "\n")
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("owner")
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--out", type=Path, default=KIT / "kernels")
    args = parser.parse_args(argv)
    print(wheelhouse_kernel(args.owner, args.out))
    for spec in args.model:
        print(model_kernel(args.owner, spec, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

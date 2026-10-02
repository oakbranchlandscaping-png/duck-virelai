#!/usr/bin/env python3
"""Build the v7 Kaggle kernel-v2 overlay with the last proven Python 3.12 image.

Author: Sol (Alpha build seat), 2026-10-02.

The frozen v7 source dataset and notebook are unchanged. Kaggle version 1 selected a
new Python 3.13 image, but the attached offline wheelhouse is explicitly CPython 3.12.
This overlay pins the exact image digest recorded on the successful v6 execution.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaggle" / "ring9-g3-nav-reachability-v7" / "kernel"
OUT = ROOT / "kaggle" / "ring9-g3-nav-reachability-v7-kernel-v2"
NOTEBOOK = "taaf_kaggle_run_share.ipynb"
NOTEBOOK_SHA256 = "7a65fc93e210975b3b942797bc19c70a2a053fde6ab38a9d6c19d7e20659cb86"
PROVEN_DOCKER_IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite existing overlay: {OUT}")
    if sha256(SOURCE / NOTEBOOK) != NOTEBOOK_SHA256:
        raise RuntimeError("The frozen v7 notebook changed; refusing to build a runtime-only overlay.")
    shutil.copytree(SOURCE, OUT)
    metadata_path = OUT / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["docker_image"] = PROVEN_DOCKER_IMAGE
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if sha256(OUT / NOTEBOOK) != NOTEBOOK_SHA256:
        raise RuntimeError("The kernel overlay changed notebook bytes.")
    print(f"overlay: {OUT}")
    print(f"notebook sha256: {NOTEBOOK_SHA256}")
    print(f"docker image: {PROVEN_DOCKER_IMAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

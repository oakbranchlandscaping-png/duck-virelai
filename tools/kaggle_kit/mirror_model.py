#!/usr/bin/env python3
"""Mirror a pinned Hugging Face model revision into a private Kaggle dataset you own.

Author: Claude (Alpha build seat), 2026-10-01. Director rulings 2026-10-01: depend on no one; prepare
to run the most capable model Kaggle allows.

Kaggle runs offline, so the model must be a Kaggle dataset (or model) attached to the notebook.
This script:
  1. resolves ``--revision`` to the repository's exact commit and records it (a branch name drifts;
     a commit does not);
  2. refuses to start if the free disk cannot hold the files;
  3. downloads the snapshot (``huggingface_hub``), verifying each LFS file against the sha256 the
     Hub publishes;
  4. writes ``MIRROR.json`` (repo, commit, every file with size and digest);
  5. with ``--publish``, creates the dataset (private) or adds a new version, with the Kaggle CLI.

It runs on a Mac or inside a Kaggle notebook with internet on. In a notebook, write to a scratch
directory with room (not /kaggle/working, which holds about 20 GB) and give the Kaggle CLI your
credentials as notebook secrets KAGGLE_USERNAME and KAGGLE_KEY; ``--kaggle-secrets`` loads them.
The script never prints a credential.

Usage:
  python3 mirror_model.py --repo ORG/NAME [--revision main] --out DIR --dataset OWNER/SLUG \
      [--title "..."] [--exclude "original/*"] [--publish] [--kaggle-secrets]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def _excluded(name: str, patterns: list[str]) -> bool:
    from fnmatch import fnmatch

    return any(fnmatch(name, pattern) for pattern in patterns)


def plan(repo: str, revision: str, exclude: list[str]) -> dict[str, Any]:
    """The exact commit and the files to fetch, with sizes and LFS digests (no download)."""
    from huggingface_hub import HfApi

    info = HfApi().model_info(repo, revision=revision, files_metadata=True)
    files = []
    for sibling in info.siblings:
        if _excluded(sibling.rfilename, exclude):
            continue
        lfs = getattr(sibling, "lfs", None)
        files.append({
            "path": sibling.rfilename, "size": int(sibling.size or 0),
            "sha256": (lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None)) if lfs else None,
        })
    card = getattr(info, "card_data", None) or {}
    return {
        "schema": "virelai-model-mirror-v1", "repo": repo, "revision_requested": revision, "commit": info.sha,
        "license": (card.get("license") if isinstance(card, dict) else getattr(card, "license", None)),
        "excluded_patterns": exclude, "files": files, "bytes": sum(item["size"] for item in files),
    }


def download(manifest: dict[str, Any], out: Path) -> None:
    from huggingface_hub import snapshot_download

    free = shutil.disk_usage(out if out.exists() else out.parent).free
    if manifest["bytes"] > 0.95 * free:
        raise SystemExit(f"Not enough disk: need {manifest['bytes'] / 1e9:.1f} GB, free {free / 1e9:.1f} GB at {out}.")
    snapshot_download(
        repo_id=manifest["repo"], revision=manifest["commit"], local_dir=str(out),
        allow_patterns=[item["path"] for item in manifest["files"]],
    )
    for item in manifest["files"]:
        path = out / item["path"]
        if not path.is_file() or path.stat().st_size != item["size"]:
            raise SystemExit(f"Incomplete download: {item['path']}")
        if item["sha256"] and _sha256(path) != item["sha256"]:
            raise SystemExit(f"sha256 mismatch: {item['path']}")
    shutil.rmtree(out / ".cache", ignore_errors=True)  # huggingface_hub's local bookkeeping


def _kaggle_env(use_secrets: bool) -> dict[str, str]:
    env = dict(os.environ)
    if use_secrets:
        from kaggle_secrets import UserSecretsClient  # available inside Kaggle notebooks

        client = UserSecretsClient()
        env["KAGGLE_USERNAME"] = client.get_secret("KAGGLE_USERNAME")
        env["KAGGLE_KEY"] = client.get_secret("KAGGLE_KEY")
    return env


def publish(out: Path, dataset: str, title: str, use_secrets: bool) -> None:
    """Create the private dataset, or add a version if it exists. Large files go up as they are."""
    (out / "dataset-metadata.json").write_text(json.dumps(
        {"title": title, "id": dataset, "licenses": [{"name": "other"}]}, indent=1) + "\n")
    env = _kaggle_env(use_secrets)
    exists = subprocess.run(["kaggle", "datasets", "status", dataset], env=env, capture_output=True, text=True)
    if exists.returncode == 0 and "ready" in exists.stdout.lower():
        command = ["kaggle", "datasets", "version", "-p", str(out), "-m", "mirror update", "-r", "skip"]
    else:
        command = ["kaggle", "datasets", "create", "-p", str(out), "-r", "skip"]
    subprocess.run(command, env=env, check=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset", required=True, help="OWNER/SLUG of the Kaggle dataset to create")
    parser.add_argument("--title", default=None)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--kaggle-secrets", action="store_true")
    args = parser.parse_args(argv)
    manifest = plan(args.repo, args.revision, args.exclude)
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=1))
    if args.plan_only:
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    download(manifest, args.out)
    (args.out / "MIRROR.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    if args.publish:
        title = (args.title or f"{args.repo.split('/')[-1]} {manifest['commit'][:8]}")[:50]  # Kaggle: 6-50 chars
        publish(args.out, args.dataset, title, args.kaggle_secrets)
    print(f"mirrored {args.repo}@{manifest['commit']} ({manifest['bytes'] / 1e9:.1f} GB) to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Rebuild a vLLM wheelhouse, byte for byte, from a digest-pinned lock (self-hosted dependencies).

Author: Claude (Alpha build seat), 2026-10-01. Director ruling 2026-10-01: depend on no one.

The Ring 9 setup command installs vLLM offline from a Kaggle dataset holding wheels and a
``requirements.lock`` (``pip install --no-index --find-links WHEELHOUSE -r requirements.lock``). The
third-party wheelhouse it used became unreadable (403). Its exact contents are recoverable: the
exit run's log lists every wheel pip installed from it, line by line, and every one of those files
is on PyPI under the same name. ``wheelhouse_v3.lock.json`` pins each file with PyPI's sha256.

This script downloads each pinned file from its PyPI URL, refuses any byte that does not match the
pinned digest, and writes the wheelhouse: the wheels, ``requirements.lock`` (``name==version`` in the
original line order), ``SHA256SUMS`` and ``BUILD_REPORT.json``. Standard library only, so it runs in a
bare Kaggle notebook with internet on, on a Mac, or anywhere else.

Usage:
  python3 build_wheelhouse.py LOCK.json OUT_DIR
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

EMBEDDED_LOCK: dict[str, Any] | None = None  # a generated Kaggle kernel inlines its lock here


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def requirement_lines(lock: dict[str, Any]) -> list[str]:
    """``name==version`` per wheel, in the lock's line order (pip resolves files via find-links)."""
    rows = sorted(lock["wheels"], key=lambda row: row["line"])
    if [row["line"] for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("lock lines must run 1..N without gaps")
    return [f"{row['name']}=={row['version']}" for row in rows]


def fetch(row: dict[str, Any], out: Path, attempts: int = 4) -> str:
    """Download one pinned wheel; return ``EXACT`` or raise. An existing verified file is kept."""
    target = out / row["filename"]
    if target.exists() and _sha256(target) == row["sha256"]:
        return "EXACT"
    for attempt in range(1, attempts + 1):
        partial = target.with_suffix(".part")
        try:
            with urllib.request.urlopen(row["url"], timeout=120) as response, partial.open("wb") as handle:
                while block := response.read(1 << 20):
                    handle.write(block)
            if _sha256(partial) != row["sha256"]:
                raise ValueError(f"sha256 mismatch for {row['filename']}")
            partial.replace(target)
            return "EXACT"
        except Exception:  # retried, then raised: a wheelhouse is complete or it is refused
            partial.unlink(missing_ok=True)
            if attempt == attempts:
                raise
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def build(lock: dict[str, Any], out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    for row in sorted(lock["wheels"], key=lambda item: item["line"]):
        fetch(row, out)
    (out / "requirements.lock").write_text("\n".join(requirement_lines(lock)) + "\n")
    sums = [f"{row['sha256']}  {row['filename']}" for row in lock["wheels"]]
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    stray = sorted(p.name for p in out.glob("*.whl") if p.name not in {row["filename"] for row in lock["wheels"]})
    if stray:
        raise RuntimeError(f"unpinned wheels in the output: {stray[:5]}")
    report = {
        "schema": "virelai-wheelhouse-build-v1", "wheels": len(lock["wheels"]),
        "bytes": sum(int(row["size"]) for row in lock["wheels"]), "stamp": lock.get("stamp"),
        "source": lock.get("source"), "all_digests_verified": True, "seconds": round(time.time() - started, 1),
    }
    (out / "BUILD_REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return report


def main(argv: list[str]) -> int:
    if EMBEDDED_LOCK is not None:
        # The output folder's root becomes the dataset's root, where setup expects requirements.lock.
        lock, out = EMBEDDED_LOCK, Path(argv[1] if len(argv) > 1 else "/kaggle/working")
    elif len(argv) == 3:
        lock, out = json.loads(Path(argv[1]).read_text()), Path(argv[2])
    else:
        print(__doc__)
        return 2
    print(json.dumps(build(lock, out), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

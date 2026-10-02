#!/usr/bin/env python3
"""Static integrity and secret check for a frozen Ring 9 Kaggle checkpoint package.

Author: Claude (Alpha build seat), 2026-09-27.

Stdlib only; safe to run on any machine before upload. It verifies what the Kaggle
notebook will verify at startup, plus the checks the notebook cannot make:

  1. every source-manifest and package-manifest hash re-derives from the files on disk;
  2. the source manifest covers exactly the source-dataset files it should;
  3. both execution receipts are identical and bind both manifests by hash;
  4. src.zip holds exactly the src/ tree, byte for byte, under a leading src/ prefix;
  5. the kernel metadata runs offline on GPU and leads with the package's own dataset;
  6. no .env file (other than .env.example) and no key-shaped token exists anywhere,
     including inside src.zip;
  7. runtime setup values and their frozen receipt use the same semantic encoding;
  8. optionally, every bundled source file is byte-identical to a `git archive` export
     of the source commit (pass --source-export DIR).

Usage:
  python3 tools/verify_kaggle_package.py kaggle/<package> [--source-export DIR]

Exit status is 0 only when every check passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

VARIANT_REL = "variants/ring9-cybernetic-gates"
SOURCE_EXCLUDED = {"dataset-metadata.json", "execution_receipt.json", "source-manifest.json", "src.zip"}
PACKAGE_EXCLUDED = {"execution_receipt.json", "package-manifest.json"}
DOTENV = re.compile(r"^\.env(\..+)?$")
SECRETS = (
    re.compile(rb"sk-or-v1-[A-Za-z0-9]{32,}"),
    re.compile(rb"sk-(?:ant|proj)-[A-Za-z0-9_-]{24,}"),
    re.compile(rb"(?:OPENROUTER|OPENAI|ANTHROPIC|ARC|KAGGLE|HF)_(?:API_)?(?:KEY|TOKEN)\s*=\s*['\"]?[A-Za-z0-9_-]{16,}"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("package", type=Path)
    parser.add_argument("--source-export", type=Path, default=None)
    args = parser.parse_args()
    out: Path = args.package
    bundle = out / "source-dataset"
    results: list[tuple[bool, str]] = []

    def check(ok: bool, label: str) -> None:
        results.append((ok, label))
        print(("PASS " if ok else "FAIL ") + label)

    source_manifest = json.loads((bundle / "source-manifest.json").read_text())
    bad = [k for k, v in source_manifest.items() if not (bundle / k).is_file() or sha(bundle / k) != v]
    check(not bad, f"source-manifest re-derives ({len(source_manifest)} files){'; bad: ' + str(bad[:5]) if bad else ''}")
    expected = {
        str(p.relative_to(bundle)) for p in bundle.rglob("*")
        if p.is_file() and p.name not in SOURCE_EXCLUDED
    }
    check(set(source_manifest) == expected, "source-manifest covers exactly the source-dataset files")

    package_manifest = json.loads((out / "package-manifest.json").read_text())
    bad = [k for k, v in package_manifest.items() if not (out / k).is_file() or sha(out / k) != v]
    check(not bad, f"package-manifest re-derives ({len(package_manifest)} files){'; bad: ' + str(bad[:5]) if bad else ''}")

    inner = json.loads((bundle / "execution_receipt.json").read_text())
    outer = json.loads((out / "execution_receipt.json").read_text())
    check(
        inner == outer
        and inner["package"]["manifest_sha256"] == sha(bundle / "source-manifest.json")
        and inner["package"]["sha256"] == sha(out / "package-manifest.json"),
        "execution receipts identical and bind both manifests",
    )

    setup_commands = json.loads((bundle / "setup_commands.json").read_text())
    setup_text = "\n".join(str(command) for command in setup_commands)
    output_caps = re.findall(r"'LOCAL_ANALYZER_MAX_OUTPUT':\s*'(-?\d+)'", setup_text)
    expected_output_cap = None
    if len(output_caps) == 1:
        raw_output_cap = int(output_caps[0])
        expected_output_cap = "server_default" if raw_output_cap <= 0 else raw_output_cap
    receipt_output_cap = inner.get("budgets", {}).get("max_output_tokens_per_turn")
    check(
        expected_output_cap is not None and receipt_output_cap == expected_output_cap,
        "runtime output cap and execution receipt use the same semantic encoding"
        f" (setup={expected_output_cap!r}, receipt={receipt_output_cap!r})",
    )

    with zipfile.ZipFile(bundle / "src.zip") as archive:
        names = archive.namelist()
        tree = sorted(str(p.relative_to(bundle)) for p in (bundle / "src").rglob("*") if p.is_file())
        same = sorted(names) == tree and all(archive.read(n) == (bundle / n).read_bytes() for n in names)
        check(same and all(n.startswith("src/") for n in names), f"src.zip byte-identical to src/ ({len(names)} files, src/ prefix)")

        kernel = json.loads((out / "kernel" / "kernel-metadata.json").read_text())
        dataset = json.loads((bundle / "dataset-metadata.json").read_text())
        check(
            kernel.get("enable_internet") is False and kernel.get("enable_gpu") is True
            and kernel["dataset_sources"][0] == dataset["id"],
            f"kernel runs offline on GPU and leads with {dataset['id']}",
        )

        findings: list[str] = []

        def scan(label: str, name: str, data: bytes) -> None:
            if DOTENV.match(name) and name != ".env.example":
                findings.append(f"dotenv:{label}")
            if any(p.search(data) for p in SECRETS):
                findings.append(f"token:{label}")

        for path in sorted(out.rglob("*")):
            if path.is_file():
                scan(str(path.relative_to(out)), path.name, path.read_bytes())
        for name in names:
            scan(f"src.zip!{name}", Path(name).name, archive.read(name))
        check(not findings, f"secret scan (files and zip entries): {findings[:10] or 'clean'}")

    if args.source_export is not None:
        variant = args.source_export / VARIANT_REL
        diffs = []
        for repo in ("ARC3-Inference", "tufa-arc-agi-framework"):
            for path in (bundle / "src" / repo).rglob("*"):
                if path.is_file():
                    twin = variant / repo / path.relative_to(bundle / "src" / repo)
                    if not twin.is_file() or twin.read_bytes() != path.read_bytes():
                        diffs.append(str(path.relative_to(bundle)))
        check(not diffs, f"bundled source byte-identical to the committed export (diffs={len(diffs)})")

    passed = sum(ok for ok, _ in results)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

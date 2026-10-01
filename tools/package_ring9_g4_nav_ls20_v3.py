#!/usr/bin/env python3
"""Package the narrow Kaggle model-mount repair for the R9-R19 ls20 NAV checkpoint.

Author: Sol (Alpha build seat), 2026-10-01.

V2 attached its dataset wheelhouse and Kaggle model source, but constructed the model path with
the metadata spelling ``PyTorch``. Kaggle normalizes model mount directories. V3 resolves the
framework component case-insensitively and, within the exact owner/model root, falls back to the
unique directory containing ``config.json``. No solver source, model, parser, world, budget or
behavioral criterion changes.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import package_ring9_g4_nav_ls20 as common


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "kaggle" / "ring9-g4-nav-ls20-v2"
BASE_PACKAGE_SHA256 = "3b6e522413d1ce657551e7f73cca7b785235dca10020d53dae929d5dec0b283d"
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", "ring9-g4-nav-ls20-v3")
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v2"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v3"
OLD_KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v2"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v3"
OLD_PACKAGE_NAME = "ring9-g4-nav-ls20-v2"
PACKAGE_NAME = "ring9-g4-nav-ls20-v3"


def _rewrite_notebook(path: Path) -> None:
    notebook = json.loads(path.read_text())
    old_mapping = (
        "for ref in MODEL_SOURCES:\n"
        "    owner, slug, framework, variation, version = ref.split('/', 4)\n"
        "    candidate = Path('/kaggle/input/models') / owner / slug / framework / variation / version\n"
        "    kaggle_input_paths[f'{owner}/{slug}'] = str(candidate)\n"
    )
    new_mapping = (
        "for ref in MODEL_SOURCES:\n"
        "    owner, slug, framework, variation, version = ref.split('/', 4)\n"
        "    model_root = Path('/kaggle/input/models') / owner / slug\n"
        "    candidates = [\n"
        "        model_root / framework / variation / version,\n"
        "        model_root / framework.lower() / variation / version,\n"
        "    ]\n"
        "    resolved = _first_existing(candidates)\n"
        "    if resolved is None and model_root.is_dir():\n"
        "        config_roots = sorted({p.parent for p in model_root.rglob('config.json')})\n"
        "        if len(config_roots) == 1:\n"
        "            resolved = config_roots[0]\n"
        "        elif len(config_roots) > 1:\n"
        "            raise RuntimeError(f'Ambiguous Kaggle model mount for {ref}: {config_roots}')\n"
        "    kaggle_input_paths[f'{owner}/{slug}'] = str(resolved or candidates[1])\n"
    )
    replacements = 0
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
        source = "".join(cell.get("source", []))
        source = source.replace(OLD_DATASET_ID, DATASET_ID)
        source = source.replace(OLD_PACKAGE_NAME, PACKAGE_NAME)
        if old_mapping in source:
            source = source.replace(old_mapping, new_mapping)
            replacements += 1
        cell["source"] = source.splitlines(True)
    if replacements != 1:
        raise RuntimeError(f"Expected one model-mount mapping, found {replacements}.")
    notebook["cells"][0]["source"] = [
        "# Ring 9 G4 NAV checkpoint, ls20, mount repair v3 (R9-R06 to R9-R19)\n",
        "V2 attached the exact wheelhouse and pinned Qwen3.8 model source, but assumed a "
        "case-preserving model mount. V3 resolves Kaggle's normalized model directory; all "
        "behavioral inputs and criteria are unchanged.\n",
    ]
    rendered = json.dumps(notebook)
    for marker in (DATASET_ID, "framework.lower()", "rglob('config.json')"):
        if marker not in rendered:
            raise RuntimeError(f"Notebook is missing v3 marker: {marker}")
    if OLD_DATASET_ID in rendered:
        raise RuntimeError("Notebook retained the v2 source identity.")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile("".join(cell["source"]), "<ring9-g4-nav-ls20-v3-notebook>", "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _build() -> dict[str, Any]:
    if common._sha256(BASE / "package-manifest.json") != BASE_PACKAGE_SHA256:
        raise RuntimeError("The v2 package manifest changed.")
    shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns(".DS_Store", "RUN_STATUS.md"))
    bundle, kernel = OUT / "source-dataset", OUT / "kernel"

    dataset = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset.update(id=DATASET_ID, title="Virelai Ring 9 G4 NAV ls20 v3")
    common._write_json(bundle / "dataset-metadata.json", dataset)
    bundle_meta = json.loads((bundle / "taaf-kaggle-bundle.json").read_text())
    bundle_meta.update(created_at=datetime.now(timezone.utc).isoformat(), benchmark_label=PACKAGE_NAME)
    common._write_json(bundle / "taaf-kaggle-bundle.json", bundle_meta)

    metadata_path = kernel / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("id") != OLD_KERNEL_ID or metadata.get("dataset_sources", [None])[0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel identity does not match v2.")
    metadata["id"] = KERNEL_ID
    metadata["title"] = KERNEL_ID.split("/", 1)[1]
    metadata["dataset_sources"][0] = DATASET_ID
    common._write_json(metadata_path, metadata)
    _rewrite_notebook(kernel / "taaf_kaggle_run_share.ipynb")

    checkpoint_path = bundle / "checkpoint-preflight.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["stage"] = "G4-NAV-LS20-V3-MODEL-MOUNT-REPAIR"
    checkpoint["claim_limits"] = [
        *checkpoint.get("claim_limits", []),
        "V3 changes only model mount discovery after V2 proved the wheelhouse mount and exposed Kaggle's normalized model path.",
    ]
    common._write_json(checkpoint_path, checkpoint)

    receipt_path = bundle / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["schema"] = "virelai-g4-nav-ls20-v3-execution-receipt-v1"
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["package"]["sha256"] = "0" * 64
    common._write_json(receipt_path, receipt)

    (OUT / "RUN.md").write_text(
        "# Ring 9 G4 NAV ls20, v3 model-mount repair\n\n"
        "Source, Qwen3.8 revision, exact wheelhouse, parser, world, budgets and rubric are unchanged "
        "from v2. This package only resolves Kaggle's normalized model mount directory.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(
        (BASE / "TEST_RESULTS.txt").read_text()
        + "V3 packaging: model mount resolution handles framework case normalization and a unique "
          "config.json root; notebook code cells compile; independent package verification required.\n"
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G4 NAV ls20 v3\n\nFrozen v2 payload with only the Kaggle model-mount resolver repaired.\n"
    )
    (bundle / "preamble.txt").write_text(
        "R9-R19 ls20 NAV checkpoint v3: v2 model and runtime, normalized Kaggle model-mount repair.\n"
    )

    source_manifest = common._source_manifest(bundle)
    common._write_json(bundle / "source-manifest.json", source_manifest)
    source_manifest_sha = common._sha256(bundle / "source-manifest.json")
    receipt = json.loads(receipt_path.read_text())
    receipt["package"]["manifest_sha256"] = source_manifest_sha
    common._write_json(receipt_path, receipt)
    package_manifest = common._package_manifest(OUT)
    common._write_json(OUT / "package-manifest.json", package_manifest)
    package_sha = common._sha256(OUT / "package-manifest.json")
    receipt["package"]["sha256"] = package_sha
    common._write_json(receipt_path, receipt)
    common._write_json(OUT / "execution_receipt.json", receipt)
    common._secret_guard(OUT)
    return {"out": str(OUT), "source files": len(source_manifest), "package files": len(package_manifest),
            "package sha256": package_sha, "source manifest sha256": source_manifest_sha}


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite existing package: {OUT}")
    try:
        result = _build()
    except BaseException:
        shutil.rmtree(OUT, ignore_errors=True)
        raise
    for key, value in result.items():
        print(f"{key}: {value}")
    print("secret guard: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

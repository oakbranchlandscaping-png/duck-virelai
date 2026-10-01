#!/usr/bin/env python3
"""Repackage the R9-R19 ls20 NAV checkpoint with accessible Kaggle runtime assets.

Author: Sol (Alpha build seat), 2026-10-01.

Version 1 verified and mounted its own source, but Kaggle refused both third-party runtime dataset
references and the run stopped before model startup. Version 2 preserves source commit 72adbe3,
the world, budgets and rubric. It points at a byte-identical mirror of the 174-wheel vLLM
wheelhouse and a pinned, unmodified Qwen3.8-27B-FP8 Kaggle model source. The model change is
receipt-bound and must remain explicit in every behavioral comparison.
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

import package_ring9_g4_nav_ls20 as v1
from kaggle_kit.dependencies import Dependencies, THIRD_PARTY_V3, retarget_setup


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "kaggle" / "ring9-g4-nav-ls20-v1"
BASE_PACKAGE_SHA256 = "6beafc84860777cf63b36bca042dbff6e853aed22fa1220d927f56a3957f2f23"
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", "ring9-g4-nav-ls20-v2")
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v2"
OLD_KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v2"
OLD_PACKAGE_NAME = "ring9-g4-nav-ls20-v1"
PACKAGE_NAME = "ring9-g4-nav-ls20-v2"
MODEL_SOURCE = "mikedan7/qwen3-8-27b-fp8-official/PyTorch/hf-fp8/1"
DEPENDENCIES = Dependencies(
    wheelhouse="mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3",
    model="mikedan7/qwen3-8-27b-fp8-official",
    served_model_name="Qwen/Qwen3.8-27B-FP8",
    max_model_len=65536,
    tool_call_parser="qwen3_xml",
    reasoning_parser="qwen3",
)


def _rewrite_notebook(path: Path) -> None:
    notebook = json.loads(path.read_text())
    old_sources = (
        'DATASET_SOURCES = ["stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v1", '
        '"driessmit1/arc3-vllm-h100-wheelhouse-v3", '
        '"driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"]'
    )
    new_sources = (
        'DATASET_SOURCES = ["stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v2", '
        '"mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3"]\n'
        f'MODEL_SOURCES = ["{MODEL_SOURCE}"]'
    )
    model_mapping_anchor = (
        "for ref in KERNEL_SOURCES:\n"
        "    candidates = _kernel_mount_candidates(ref)\n"
        "    kaggle_input_paths[ref] = str(_first_existing(candidates) or candidates[0])\n"
    )
    model_mapping = model_mapping_anchor + (
        "for ref in MODEL_SOURCES:\n"
        "    owner, slug, framework, variation, version = ref.split('/', 4)\n"
        "    candidate = Path('/kaggle/input/models') / owner / slug / framework / variation / version\n"
        "    kaggle_input_paths[f'{owner}/{slug}'] = str(candidate)\n"
    )
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
        source = "".join(cell.get("source", []))
        if old_sources in source:
            source = source.replace(old_sources, new_sources)
        source = source.replace(OLD_DATASET_ID, DATASET_ID)
        source = source.replace(OLD_PACKAGE_NAME, PACKAGE_NAME)
        if model_mapping_anchor in source:
            source = source.replace(model_mapping_anchor, model_mapping)
        cell["source"] = source.splitlines(True)
    notebook["cells"][0]["source"] = [
        "# Ring 9 G4 NAV checkpoint, ls20, runtime repair v2 (R9-R06 to R9-R19)\n",
        "The v1 source mounted and verified but its vanished third-party runtime inputs did not. "
        "This version uses the byte-identical wheelhouse mirror and a pinned Qwen3.8 Kaggle model "
        "source; the behavioral rubric is unchanged and the model difference is explicit.\n",
    ]
    rendered = json.dumps(notebook)
    required = [DATASET_ID, DEPENDENCIES.wheelhouse, MODEL_SOURCE, "MODEL_SOURCES", "qwen3-8-27b-fp8-official"]
    forbidden = [OLD_DATASET_ID, THIRD_PARTY_V3.wheelhouse, THIRD_PARTY_V3.model]
    for needle in required:
        if needle not in rendered:
            raise RuntimeError(f"Notebook is missing required v2 marker: {needle}")
    for needle in forbidden:
        if needle in rendered:
            raise RuntimeError(f"Notebook retained stale v1 runtime marker: {needle}")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile("".join(cell["source"]), "<ring9-g4-nav-ls20-v2-notebook>", "exec",
                    flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _rewrite_runtime(bundle: Path, kernel: Path) -> None:
    setup_path = bundle / "setup_commands.json"
    setup = json.loads(setup_path.read_text())
    if len(setup) != 1:
        raise RuntimeError("Expected exactly one setup command.")
    setup = [retarget_setup(setup[0], DEPENDENCIES)]
    v1._write_json(setup_path, setup)

    metadata_path = kernel / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("id") != OLD_KERNEL_ID or metadata.get("dataset_sources", [None])[0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel identity does not match v1.")
    metadata["id"] = KERNEL_ID
    metadata["title"] = KERNEL_ID.split("/", 1)[1]
    metadata["dataset_sources"] = [DATASET_ID, DEPENDENCIES.wheelhouse]
    metadata["model_sources"] = [MODEL_SOURCE]
    v1._write_json(metadata_path, metadata)


def _rewrite_records(bundle: Path) -> None:
    checkpoint_path = bundle / "checkpoint-preflight.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["stage"] = "G4-NAV-LS20-V2-RUNTIME-REPAIR"
    checkpoint["model"] = DEPENDENCIES.served_model_name
    checkpoint["dependencies"] = DEPENDENCIES.record() | {"model_source": MODEL_SOURCE}
    checkpoint["claim_limits"] = [
        *checkpoint.get("claim_limits", []),
        "Version 2 changes Duck from Qwen3.6-27B-FP8 to pinned Qwen3.8-27B-FP8; behavioral results are not model-controlled comparisons with earlier runs.",
        "The wheelhouse mirror's 174 wheel files and digests exactly match the pinned reconstruction; five non-wheel metadata files are extra.",
    ]
    v1._write_json(checkpoint_path, checkpoint)

    receipt_path = bundle / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["schema"] = "virelai-g4-nav-ls20-v2-execution-receipt-v1"
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["package"]["sha256"] = "0" * 64
    receipt["model"] = {"id": DEPENDENCIES.served_model_name, "source": MODEL_SOURCE,
                        "pinned_revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}
    receipt["dependencies"] = DEPENDENCIES.record()
    v1._write_json(receipt_path, receipt)


def _build() -> dict[str, Any]:
    if v1._sha256(BASE / "package-manifest.json") != BASE_PACKAGE_SHA256:
        raise RuntimeError("The v1 package manifest changed.")
    shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns(".DS_Store", "RUN_STATUS.md"))
    bundle, kernel = OUT / "source-dataset", OUT / "kernel"

    dataset = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset.update(id=DATASET_ID, title="Virelai Ring 9 G4 NAV ls20 v2")
    v1._write_json(bundle / "dataset-metadata.json", dataset)
    bundle_meta = json.loads((bundle / "taaf-kaggle-bundle.json").read_text())
    bundle_meta.update(created_at=datetime.now(timezone.utc).isoformat(), benchmark_label=PACKAGE_NAME)
    v1._write_json(bundle / "taaf-kaggle-bundle.json", bundle_meta)

    _rewrite_runtime(bundle, kernel)
    _rewrite_notebook(kernel / "taaf_kaggle_run_share.ipynb")
    _rewrite_records(bundle)

    (OUT / "RUN.md").write_text(
        "# Ring 9 G4 NAV ls20, v2 runtime repair\n\n"
        "Source and rubric are unchanged from v1. V1 verified its source but failed before model "
        "startup because its two third-party runtime datasets were no longer mountable. V2 uses "
        "the byte-identical 174-wheel mirror and pinned Qwen3.8 model source. The model change is "
        "receipt-bound and must remain explicit in review.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(
        (BASE / "TEST_RESULTS.txt").read_text()
        + "\nV2 packaging: wheel checksum comparison 174/174 exact; notebook code cells compile; "
          "model revision pinned; independent package verification required before upload.\n"
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G4 NAV ls20 v2\n\nFrozen source from 72adbe3 with repaired, receipt-bound Kaggle runtime references.\n"
    )
    (bundle / "preamble.txt").write_text(
        "R9-R19 ls20 NAV checkpoint v2: source 72adbe3, exact mirrored vLLM wheel set, pinned "
        "Qwen3.8-27B-FP8. Human review required.\n"
    )

    source_manifest = v1._source_manifest(bundle)
    v1._write_json(bundle / "source-manifest.json", source_manifest)
    source_manifest_sha = v1._sha256(bundle / "source-manifest.json")
    receipt = json.loads((bundle / "execution_receipt.json").read_text())
    receipt["package"]["manifest_sha256"] = source_manifest_sha
    v1._write_json(bundle / "execution_receipt.json", receipt)

    package_manifest = v1._package_manifest(OUT)
    v1._write_json(OUT / "package-manifest.json", package_manifest)
    package_sha = v1._sha256(OUT / "package-manifest.json")
    receipt["package"]["sha256"] = package_sha
    v1._write_json(bundle / "execution_receipt.json", receipt)
    v1._write_json(OUT / "execution_receipt.json", receipt)
    v1._secret_guard(OUT)
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

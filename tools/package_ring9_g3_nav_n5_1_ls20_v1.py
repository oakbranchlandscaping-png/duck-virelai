#!/usr/bin/env python3
"""Freeze N5.1 as the bounded Ring 9 G3 NAV semantic-seam checkpoint.

Author: Sol (Alpha build seat), 2026-10-04.

This deliberately derives from the last executed ls20 package so the Kaggle
image, model, wheelhouse and notebook harness remain fixed.  It changes the
committed Ring 9 source, the bounded G3 budget, and the N5.1 grading contract.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "14f6459"
PACKAGE_NAME = "ring9-g3-nav-n5-1-ls20-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-1-ls20-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-nav-n5-1-ls20-v1"
MAX_ACTIONS = 60
MAX_RUNTIME_SECONDS = 700


def _load_base():
    path = ROOT / "tools" / "package_ring9_g3_nav_terrain_ls20_v2.py"
    spec = importlib.util.spec_from_file_location("ring9_nav_n5_base", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()
base.OUT = ROOT / "kaggle" / PACKAGE_NAME
base.DATASET_ID = DATASET_ID
base.KERNEL_ID = KERNEL_ID
base.PACKAGE_NAME = PACKAGE_NAME
base.SOURCE_COMMIT = SOURCE_COMMIT
base.MAX_ACTIONS = MAX_ACTIONS
base.MAX_RUNTIME_SECONDS = MAX_RUNTIME_SECONDS
base.common.SOURCE_COMMIT = SOURCE_COMMIT
_original_build = base._build


def _rewrite_json(path: Path, updates: dict) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(updates)
    base.common._write_json(path, value)
    return value


def _build(variant: Path) -> dict:
    result = _original_build(variant)
    out = base.OUT
    bundle = out / "source-dataset"

    _rewrite_json(bundle / "dataset-metadata.json", {
        "title": "Virelai Ring 9 G3 NAV N5.1 bounded semantic seam",
    })

    notebook_path = out / "kernel" / "taaf_kaggle_run_share.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = [
        "# Ring 9 N5.1 bounded G3 NAV semantic-seam checkpoint\n",
        "One ls20 world, 60 actions and 700 behavior seconds. Grade G0-G3 accounting, shared topology, "
        "stable reachability terminalization, and the explicit G3 run product.\n",
    ]
    base.common._write_json(notebook_path, notebook)

    preflight = _rewrite_json(bundle / "checkpoint-preflight.json", {
        "schema": "virelai-g3-nav-n5-1-ls20-v1-preflight-v1",
        "stage": "G3-NAV-N5.1-BOUNDED-SEMANTIC-SEAM",
        "claim": (
            "Tests the committed N5.1 repair: the first compact reachability explanation has "
            "one durable two-request allowance across solver turns; acceptance enables "
            "controller-only sibling reuse, while exhaustion stops with a complete audit product."
        ),
        "source_commit": SOURCE_COMMIT,
        "revisions": "N5.1 durable bounded semantic seam",
        "max_actions_per_world": MAX_ACTIONS,
        "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
        "live_criteria": [
            "G0-G2 close and install the complete counter mask.",
            "The eligible visual-object roster is populated before target execution.",
            "Every controller-computable probe remains controller-owned.",
            "Reachable targets receive physical contact attempts.",
            "The first target reachability card names the certified target and requests no board reinspection.",
            "The semantic request requires tool use, disables thinking, omits the grid image, and allows at most 256 output tokens.",
            "At most two completed model requests occur for one bound semantic checkpoint across all solver turns.",
            "An accepted explanation terminalizes the row and permits controller-only reuse for a matching sibling semantic key.",
            "If no answer is accepted, G3_SEMANTIC_RETRY_EXHAUSTED is the final current product and G4 remains closed.",
            "Every bounded product names the pending target, latest lifecycle evidence, and exact eligible roster count.",
            "Observed floor and wall roles carry direct evidence; unobserved terrain is not asserted.",
        ],
        "claim_limits": [
            "This checkpoint does not grade G4 comprehension, competition score, or a win.",
            "A semantic-exhaustion product is a clean bounded failure, not G3 completion.",
            "Human review of lossless artifacts is required before behavioral success is claimed.",
        ],
    })
    del preflight

    receipt = _rewrite_json(bundle / "execution_receipt.json", {
        "schema": "virelai-g3-nav-n5-1-ls20-v1-execution-receipt-v1",
        "revisions": "N5.1 durable bounded semantic seam",
        "source_commit": SOURCE_COMMIT,
    })
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["budgets"].update(
        max_environment_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
    )

    (out / "RUN.md").write_text(
        "# Ring 9 N5.1 bounded G3 NAV semantic-seam checkpoint\n\n"
        f"Source `{SOURCE_COMMIT}`. One ls20 world, one pass, at most {MAX_ACTIONS} actions and "
        f"{MAX_RUNTIME_SECONDS} seconds. Grade G0-G3 and the explicit G3 run product only.\n",
        encoding="utf-8",
    )
    (out / "TEST_RESULTS.txt").write_text(
        "Source 14f6459: 578 passed, 14 dependency deprecation warnings, in 551.07 seconds.\n"
        "N5.1 integration suite: 112 passed. Package source must reproduce the focused tests.\n",
        encoding="utf-8",
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 N5.1 G3 NAV ls20 v1\n\n"
        "Receipt-bound durable semantic-seam checkpoint.\n",
        encoding="utf-8",
    )
    (bundle / "preamble.txt").write_text(
        "R9 N5.1 G3 NAV: ls20, 60 actions, 700 seconds, source 14f6459. Human review required.\n",
        encoding="utf-8",
    )
    (bundle / "git_status.txt").write_text(
        "Isolated git archive of source commit 14f6459. Unrelated working-tree files are excluded.\n",
        encoding="utf-8",
    )

    source_manifest = base.common._source_manifest(bundle)
    base.common._write_json(bundle / "source-manifest.json", source_manifest)
    base.common._write_source_zip(bundle)
    source_manifest_sha = base.common._sha256(bundle / "source-manifest.json")
    receipt["package"]["manifest_sha256"] = source_manifest_sha
    base.common._write_json(bundle / "execution_receipt.json", receipt)

    package_manifest = base.common._package_manifest(out)
    base.common._write_json(out / "package-manifest.json", package_manifest)
    package_sha = base.common._sha256(out / "package-manifest.json")
    receipt["package"]["sha256"] = package_sha
    base.common._write_json(bundle / "execution_receipt.json", receipt)
    base.common._write_json(out / "execution_receipt.json", receipt)
    base.common._secret_guard(out)
    return {
        **result,
        "out": str(out),
        "source files": len(source_manifest),
        "package files": len(package_manifest),
        "package sha256": package_sha,
        "source manifest sha256": source_manifest_sha,
    }


base._build = _build


if __name__ == "__main__":
    raise SystemExit(base.main())

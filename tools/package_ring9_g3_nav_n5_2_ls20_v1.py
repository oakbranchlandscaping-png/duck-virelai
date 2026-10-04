#!/usr/bin/env python3
"""Freeze N5.2 as the bounded Ring 9 G3 NAV route-handoff checkpoint.

Author: Sol (Alpha build seat), 2026-10-04.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "6c10b8e"
PACKAGE_NAME = "ring9-g3-nav-n5-2-ls20-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-2-ls20-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-nav-n5-2-ls20-v1"
MAX_ACTIONS = 60
MAX_RUNTIME_SECONDS = 700


def _load_n51():
    path = ROOT / "tools" / "package_ring9_g3_nav_n5_1_ls20_v1.py"
    spec = importlib.util.spec_from_file_location("ring9_nav_n5_1_base", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


n51 = _load_n51()
base = n51.base
base.OUT = ROOT / "kaggle" / PACKAGE_NAME
base.DATASET_ID = DATASET_ID
base.KERNEL_ID = KERNEL_ID
base.PACKAGE_NAME = PACKAGE_NAME
base.SOURCE_COMMIT = SOURCE_COMMIT
base.MAX_ACTIONS = MAX_ACTIONS
base.MAX_RUNTIME_SECONDS = MAX_RUNTIME_SECONDS
base.common.SOURCE_COMMIT = SOURCE_COMMIT
_n51_build = n51._build


def _rewrite_json(path: Path, updates: dict) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(updates)
    base.common._write_json(path, value)
    return value


def _build(variant: Path) -> dict:
    result = _n51_build(variant)
    out = base.OUT
    bundle = out / "source-dataset"

    _rewrite_json(bundle / "dataset-metadata.json", {
        "title": "Virelai Ring 9 G3 NAV N5.2 bounded route handoff",
    })
    notebook_path = out / "kernel" / "taaf_kaggle_run_share.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = [
        "# Ring 9 N5.2 bounded G3 NAV route-handoff checkpoint\n",
        "One ls20 world, 60 actions and 700 behavior seconds. Grade G0-G3 accounting, semantic reuse, "
        "and the bounded controller-to-Duck route handoff.\n",
    ]
    base.common._write_json(notebook_path, notebook)

    preflight = _rewrite_json(bundle / "checkpoint-preflight.json", {
        "schema": "virelai-g3-nav-n5-2-ls20-v1-preflight-v1",
        "stage": "G3-NAV-N5.2-BOUNDED-ROUTE-HANDOFF",
        "claim": (
            "Tests the N5.2 repair: when the controller cannot compute a route step, Duck gets one "
            "compact action choice for the current certified G3 revision; a successful action returns "
            "ownership to the controller and a failed choice emits a complete bounded product."
        ),
        "source_commit": SOURCE_COMMIT,
        "revisions": "N5.2 bounded route handoff after semantic reuse",
        "max_actions_per_world": MAX_ACTIONS,
        "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
        "live_criteria": [
            "G0-G2 close and install the complete counter mask.",
            "The eligible visual-object roster is populated before target execution.",
            "Every controller-computable probe remains controller-owned.",
            "The first reachability explanation remains bounded and accepted, with sibling reuse.",
            "A controller route handoff produces at most one required-tool, no-thinking, 256-token request.",
            "A successful Duck route action returns control to the controller after the new revision.",
            "A failed or empty route choice emits G3_ROUTE_RETRY_EXHAUSTED and preserves G4 closure.",
            "Every bounded product names the pending target, latest lifecycle evidence, and exact eligible roster count.",
        ],
        "claim_limits": [
            "This checkpoint does not grade G4 comprehension, competition score, or a win.",
            "A route-exhaustion product is a clean bounded failure, not G3 completion.",
            "Human review of lossless artifacts is required before behavioral success is claimed.",
        ],
    })
    del preflight

    receipt = _rewrite_json(bundle / "execution_receipt.json", {
        "schema": "virelai-g3-nav-n5-2-ls20-v1-execution-receipt-v1",
        "revisions": "N5.2 bounded route handoff after semantic reuse",
        "source_commit": SOURCE_COMMIT,
    })
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["budgets"].update(
        max_environment_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
    )

    (out / "RUN.md").write_text(
        "# Ring 9 N5.2 bounded G3 NAV route-handoff checkpoint\n\n"
        f"Source `{SOURCE_COMMIT}`. One ls20 world, one pass, at most {MAX_ACTIONS} actions and "
        f"{MAX_RUNTIME_SECONDS} seconds. Grade G0-G3, semantic reuse and route handoff only.\n",
        encoding="utf-8",
    )
    (out / "TEST_RESULTS.txt").write_text(
        "Source 6c10b8e: N5.2 focused suite passed, with 14 dependency deprecation warnings.\n"
        "Package source must reproduce the bounded semantic and route-handoff behavior.\n",
        encoding="utf-8",
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 N5.2 G3 NAV ls20 v1\n\n"
        "Receipt-bound bounded route-handoff checkpoint.\n",
        encoding="utf-8",
    )
    (bundle / "preamble.txt").write_text(
        "R9 N5.2 G3 NAV: ls20, 60 actions, 700 seconds, source 6c10b8e. Human review required.\n",
        encoding="utf-8",
    )
    (bundle / "git_status.txt").write_text(
        "Isolated git archive of source commit 6c10b8e. Unrelated working-tree files are excluded.\n",
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

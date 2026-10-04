#!/usr/bin/env python3
"""Freeze N5.3 as the bounded Ring 9 G3 NAV first-witness checkpoint.

Author: Sol (Alpha build seat), 2026-10-04.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "aa799b5"
PACKAGE_NAME = "ring9-g3-nav-n5-3-ls20-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-nav-n5-3-ls20-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-nav-n5-3-ls20-v1"
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
        "title": "Virelai Ring 9 G3 NAV N5.3 first-witness sweep",
    })
    notebook_path = out / "kernel" / "taaf_kaggle_run_share.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = [
        "# Ring 9 N5.3 G3 NAV first-witness checkpoint\n",
        "One ls20 world, 60 actions and 700 behavior seconds. Grade first positive NAV contact, "
        "durable lever discovery, ranked-roster advance and the G4 handoff.\n",
    ]
    base.common._write_json(notebook_path, notebook)

    preflight = _rewrite_json(bundle / "checkpoint-preflight.json", {
        "schema": "virelai-g3-nav-n5-3-ls20-v1-preflight-v1",
        "stage": "G3-NAV-N5.3-FIRST-WITNESS-SWEEP",
        "claim": (
            "Tests the N5.3 repair: the first attributed counter- and ego-masked NAV contact residue "
            "is preserved as LEVER_FOUND, advances the ranked sweep without G3 confirmation, and "
            "enters G4 with the original discovery evidence."
        ),
        "source_commit": SOURCE_COMMIT,
        "revisions": "N5.3 NAV first-witness sweep and G4 handoff",
        "max_actions_per_world": MAX_ACTIONS,
        "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
        "live_criteria": [
            "G0-G2 close and install the complete counter mask.",
            "The eligible visual-object roster is populated before target execution.",
            "Every controller-computable probe remains controller-owned.",
            "The first attributed positive NAV contact emits lever_discovery.status LEVER_FOUND.",
            "The discovery records the exact target, procedure, local residue and remote residue.",
            "No pending G3 confirmation is created for the discovered NAV lever.",
            "The lifecycle becomes G4-READY and the scheduler advances to the next ranked target.",
            "Later null or changed-state contacts cannot erase the first positive witness.",
            "If the roster completes, G4 accepts the single discovery evidence without inventing confirmation.",
        ],
        "claim_limits": [
            "This checkpoint grades G3 discovery and handoff, not completed G4 typing, score, or a win.",
            "Separate visual components of one contact surface may remain separate G3 rows until later consolidation.",
            "Human review of lossless artifacts is required before behavioral success is claimed.",
        ],
    })
    del preflight

    receipt = _rewrite_json(bundle / "execution_receipt.json", {
        "schema": "virelai-g3-nav-n5-3-ls20-v1-execution-receipt-v1",
        "revisions": "N5.3 NAV first-witness sweep and G4 handoff",
        "source_commit": SOURCE_COMMIT,
    })
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["budgets"].update(
        max_environment_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
    )

    (out / "RUN.md").write_text(
        "# Ring 9 N5.3 G3 NAV first-witness checkpoint\n\n"
        f"Source `{SOURCE_COMMIT}`. One ls20 world, one pass, at most {MAX_ACTIONS} actions and "
        f"{MAX_RUNTIME_SECONDS} seconds. Grade the first witness, roster advance and G4 handoff.\n",
        encoding="utf-8",
    )
    (out / "TEST_RESULTS.txt").write_text(
        "Source aa799b5: 77 focused G3-to-G4 tests passed.\n"
        "Package source must preserve the first NAV lever witness and continue the ranked sweep.\n",
        encoding="utf-8",
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 N5.3 G3 NAV ls20 v1\n\n"
        "Receipt-bound first-witness sweep checkpoint.\n",
        encoding="utf-8",
    )
    (bundle / "preamble.txt").write_text(
        "R9 N5.3 G3 NAV: ls20, 60 actions, 700 seconds, source aa799b5. Human review required.\n",
        encoding="utf-8",
    )
    (bundle / "git_status.txt").write_text(
        "Isolated git archive of source commit aa799b5. Unrelated working-tree files are excluded.\n",
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

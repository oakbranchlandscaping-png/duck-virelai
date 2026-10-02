#!/usr/bin/env python3
"""Package the efficient ls20 G3 NAV terrain/reachability Kaggle canary.

Author: Sol (Alpha build seat), 2026-10-02.

V4 keeps the proven v3 Kaggle runtime and model mounts, replaces the solver
source with commit 2b2a3d6, and narrows the behavior window.  It is an
infrastructure checkpoint, not a score run or a full gate-stack evaluation.
"""
from __future__ import annotations

import ast
import json
import os
import pickle
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import package_ring9_g4_nav_ls20 as common


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "kaggle" / "ring9-g4-nav-ls20-v3"
BASE_PACKAGE_SHA256 = "0c70228a4786bad598aa8c111ddd4bf1e84ff7b142ced5de28b83e3e7e6fbe41"
OUT = ROOT / "kaggle" / os.environ.get(
    "VIRELAI_PACKAGE_DIR", "ring9-g3-nav-reachability-v4"
)
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-nav-ls20-v3"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v4"
OLD_KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v3"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v4"
OLD_PACKAGE_NAME = "ring9-g4-nav-ls20-v3"
PACKAGE_NAME = "ring9-g3-nav-reachability-v4"
SOURCE_COMMIT = "2b2a3d6da901ddcecb16e90b51f5ac9dc9ea75f5"
MAX_ACTIONS = 96
MAX_RUNTIME_SECONDS = 2700
MAX_OUTPUT_TOKENS = 2048
TEMPERATURE = "0.2"
ENABLE_THINKING = "0"
WORLDS = ["ls20-9607627b"]


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label}, found {count}.")
    return source.replace(old, new)


def _rewrite_notebook(path: Path) -> None:
    notebook = json.loads(path.read_text())
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
        source = "".join(cell.get("source", []))
        source = source.replace(OLD_DATASET_ID, DATASET_ID)
        source = source.replace(OLD_PACKAGE_NAME, PACKAGE_NAME)
        cell["source"] = source.splitlines(True)

    run = "".join(notebook["cells"][14]["source"])
    run = _replace_once(
        run,
        "bm.solver.max_actions_per_game = 200",
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        "action budget",
    )
    run = _replace_once(
        run,
        "bm.solver.max_runtime_s_per_game = 10800.0",
        f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}",
        "runtime budget",
    )
    run = _replace_once(
        run,
        "timedelta(seconds=10800)",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "behavior deadline",
    )
    notebook["cells"][14]["source"] = run.splitlines(True)
    notebook["cells"][0]["source"] = [
        "# Ring 9 G3 NAV terrain/reachability canary v4\n",
        "One ls20 world, 96 actions and 45 minutes: prove refusal memory, confirmation/contact "
        "separation, provisional target release, and reopening after world deltas.\n",
    ]
    rendered = json.dumps(notebook)
    source_text = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    required = [
        DATASET_ID,
        f'bm.label = "{PACKAGE_NAME}"',
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "framework.lower()",
        "rglob('config.json')",
    ]
    for marker in required:
        if marker not in source_text:
            raise RuntimeError(f"Notebook is missing v4 marker: {marker}")
    for stale in (OLD_DATASET_ID, OLD_PACKAGE_NAME, "max_actions_per_game = 200"):
        if stale in rendered:
            raise RuntimeError(f"Notebook retained stale v3 marker: {stale}")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell["source"]),
                "<ring9-g3-nav-reachability-v4-notebook>",
                "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _rewrite_setup(bundle: Path) -> None:
    path = bundle / "setup_commands.json"
    setup = json.loads(path.read_text())
    if len(setup) != 1:
        raise RuntimeError("Expected one setup command.")
    command = setup[0]
    command = _replace_once(
        command,
        "'LOCAL_ANALYZER_MAX_OUTPUT': '0'",
        f"'LOCAL_ANALYZER_MAX_OUTPUT': '{MAX_OUTPUT_TOKENS}'",
        "model output cap",
    )
    command = _replace_once(
        command,
        "'LOCAL_ANALYZER_ENABLE_THINKING': '1'",
        f"'LOCAL_ANALYZER_ENABLE_THINKING': '{ENABLE_THINKING}'",
        "thinking setting",
    )
    command = _replace_once(
        command,
        "'LOCAL_ANALYZER_TEMPERATURE': '0.6'",
        f"'LOCAL_ANALYZER_TEMPERATURE': '{TEMPERATURE}'",
        "temperature",
    )
    common._write_json(path, [command])


def _rewrite_benchmark(bundle: Path, variant: Path) -> None:
    path = bundle / "benchmark_initial.pkl"
    sys.dont_write_bytecode = True
    sys.path[:0] = [
        str(variant / "ARC3-Inference"),
        str(variant / "tufa-arc-agi-framework" / "src"),
    ]
    with path.open("rb") as handle:
        benchmark = pickle.load(handle)
    benchmark.label = PACKAGE_NAME
    benchmark.n_passes = 1
    benchmark.game_weights = None
    benchmark.solver.label = PACKAGE_NAME
    benchmark.solver.virelai_mode = "gated"
    benchmark.solver.max_actions_per_game = MAX_ACTIONS
    benchmark.solver.max_runtime_s_per_game = float(MAX_RUNTIME_SECONDS)
    benchmark.solver.concurrency = 1
    benchmark.solver.save_request_logs = True
    with path.open("wb") as handle:
        pickle.dump(benchmark, handle)


def _build(variant: Path) -> dict[str, Any]:
    if common._sha256(BASE / "package-manifest.json") != BASE_PACKAGE_SHA256:
        raise RuntimeError("The v3 package manifest changed.")
    shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns(".DS_Store", "RUN_STATUS.md"))
    bundle, kernel = OUT / "source-dataset", OUT / "kernel"

    common._copy_source(bundle, variant)
    gates = bundle / "src" / "ARC3-Inference" / "inference" / "framework"
    required_source = (
        (gates / "nav_route.py", "ReachabilityCertificate"),
        (gates / "virelai_gates.py", "TARGET_REACHABILITY"),
        (gates / "virelai_gates.py", "virelai-nav-world-state-transition-v1"),
        (gates / "lever_lifecycle.py", "PRESUMED_UNREACHABLE"),
    )
    for source, marker in required_source:
        if marker not in source.read_text():
            raise RuntimeError(f"Packaged source is missing {marker} in {source.name}.")

    dataset = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset.update(id=DATASET_ID, title="Virelai Ring 9 G3 NAV reachability v4")
    common._write_json(bundle / "dataset-metadata.json", dataset)
    bundle_meta = json.loads((bundle / "taaf-kaggle-bundle.json").read_text())
    bundle_meta.update(
        created_at=datetime.now(timezone.utc).isoformat(),
        benchmark_label=PACKAGE_NAME,
    )
    common._write_json(bundle / "taaf-kaggle-bundle.json", bundle_meta)

    metadata_path = kernel / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("id") != OLD_KERNEL_ID:
        raise RuntimeError("Base kernel identity does not match v3.")
    metadata["id"] = KERNEL_ID
    metadata["title"] = KERNEL_ID.split("/", 1)[1]
    metadata["dataset_sources"][0] = DATASET_ID
    common._write_json(metadata_path, metadata)
    _rewrite_notebook(kernel / "taaf_kaggle_run_share.ipynb")
    _rewrite_setup(bundle)
    _rewrite_benchmark(bundle, variant)

    preflight_path = bundle / "checkpoint-preflight.json"
    preflight = json.loads(preflight_path.read_text())
    preflight.update(
        schema="virelai-g3-nav-reachability-v4-preflight-v1",
        stage="G3-NAV-TERRAIN-REACHABILITY-V4-CANARY",
        claim=(
            "Efficiently tests whether ls20 G3 NAV learns floor and refused edges, grades lever "
            "confirmation only on contact, releases an exhausted target provisionally, and "
            "reopens topology knowledge after a counter-masked world delta."
        ),
        source_commit=SOURCE_COMMIT,
        revisions="R9-R19 plus G3 NAV terrain/reachability",
        worlds=WORLDS,
        max_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS,
        inference_profile={
            "enable_thinking": False,
            "temperature": float(TEMPERATURE),
            "purpose": "fast infrastructure canary; not a model-quality comparison",
        },
        live_criteria=[
            "C1: G0-G2 open G3 on ls20 with a demonstrated NAV control map and total counter mask.",
            "C2: a failed APPROACH becomes a refused (stand, action) edge and the unchanged edge is not immediately retried.",
            "C3: a pending NAV lever confirmation remains ROUTING and ungraded until terminal contact.",
            "C4: exhaustion, if reached, produces an evidence-bound PRESUMED_UNREACHABLE explanation, advances the ranked target, and makes no inertness claim.",
            "C5: any non-counter, non-ego world delta invalidates old-state refusal evidence and reopens provisional reachability conclusions.",
            "C6: the run ends at planned stop or the explicit 96-action/2700-second cap without crashing.",
        ],
        claim_limits=[
            "This canary does not grade competition score, level completion, or the full gate stack.",
            "Criteria not reached inside the narrow budget remain ungraded rather than failed.",
            "The 2048-token, thinking-off inference profile differs from v3 and is not a model-quality comparison.",
            "Human review of lossless artifacts is required before claiming behavioral success.",
        ],
    )
    common._write_json(preflight_path, preflight)

    receipt_path = bundle / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt.update(
        schema="virelai-g3-nav-reachability-v4-execution-receipt-v1",
        revisions="R9-R19 plus G3 NAV terrain/reachability",
        source_commit=SOURCE_COMMIT,
        worlds=WORLDS,
        inference_profile={
            "enable_thinking": False,
            "temperature": float(TEMPERATURE),
        },
    )
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["package"]["sha256"] = "0" * 64
    receipt["budgets"].update(
        max_environment_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS,
    )
    common._write_json(receipt_path, receipt)

    (OUT / "RUN.md").write_text(
        "# Ring 9 G3 NAV reachability v4 canary\n\n"
        "One ls20 world, one pass, 96 actions and 2700 seconds of behavior time. The same pinned "
        "Qwen3.8-27B-FP8 runtime is used with a 2048-token answer cap, thinking disabled and "
        "temperature 0.2. This tests the G3 NAV controller mechanics, not score or full completion.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(
        "Source 2b2a3d6: full Ring 9 suite 527 passed; focused NAV test 17 passed; Ruff clean.\n"
        "Package guards require ReachabilityCertificate, TARGET_REACHABILITY, world-state topology "
        "invalidation, PRESUMED_UNREACHABLE, compiled notebook code and exact manifests.\n"
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G3 NAV reachability v4\n\n"
        "Receipt-bound, efficient ls20 terrain/reachability canary.\n"
    )
    (bundle / "preamble.txt").write_text(
        "R9 G3 NAV reachability v4: ls20, 96 actions, 2700 seconds, 2048 output tokens, "
        "thinking off. Human artifact review required.\n"
    )
    (bundle / "git_status.txt").write_text(
        f"Isolated source export of commit {SOURCE_COMMIT}. Existing working-tree changes outside "
        "the export are excluded.\n"
    )

    source_manifest = common._source_manifest(bundle)
    common._write_json(bundle / "source-manifest.json", source_manifest)
    common._write_source_zip(bundle)
    source_manifest_sha = common._sha256(bundle / "source-manifest.json")
    receipt["package"]["manifest_sha256"] = source_manifest_sha
    common._write_json(receipt_path, receipt)

    package_manifest = common._package_manifest(OUT)
    common._write_json(OUT / "package-manifest.json", package_manifest)
    package_sha = common._sha256(OUT / "package-manifest.json")
    receipt["package"]["sha256"] = package_sha
    common._write_json(receipt_path, receipt)
    common._write_json(OUT / "execution_receipt.json", receipt)
    common._secret_guard(OUT)
    return {
        "out": str(OUT),
        "source files": len(source_manifest),
        "package files": len(package_manifest),
        "package sha256": package_sha,
        "source manifest sha256": source_manifest_sha,
    }


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite existing package: {OUT}")
    common.SOURCE_COMMIT = SOURCE_COMMIT
    with tempfile.TemporaryDirectory() as workdir:
        variant = common._committed_source(Path(workdir))
        try:
            result = _build(variant)
        except BaseException:
            shutil.rmtree(OUT, ignore_errors=True)
            raise
    for key, value in result.items():
        print(f"{key}: {value}")
    print("secret guard: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

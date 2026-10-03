#!/usr/bin/env python3
"""Package the bounded ls20 controller-ownership G1/G2/G3 Kaggle canary.

Author: Sol (Alpha build seat), 2026-10-03.

This freezes the controller-ownership parity build. It uses the proven v7 runtime but spends its
narrow budget only on deterministic G0/G1, one semantic ego explanation, the bound G1
demonstration, controller-certified G2 closure, and entry into G3.
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
BASE = ROOT / "kaggle" / "ring9-g3-nav-reachability-v7"
BASE_PACKAGE_SHA256 = "42199149aa4a640af04273bb01419b8429f159d8da7d4ede1930034eda36d6bd"
OUT = ROOT / "kaggle" / os.environ.get(
    "VIRELAI_PACKAGE_DIR", "ring9-controller-first-ls20-v2"
)
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-nav-reachability-v7"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-controller-first-ls20-v2"
OLD_KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-nav-reachability-v7"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v2"
OLD_PACKAGE_NAME = "ring9-g3-nav-reachability-v7"
PACKAGE_NAME = "ring9-controller-first-ls20-v2"
SOURCE_COMMIT = "4e1be00f59c1c430391603c572bfd1dcaa4f87cb"
MAX_ACTIONS = 16
MAX_RUNTIME_SECONDS = 1200
MAX_OUTPUT_TOKENS = 4096
MODEL_REQUEST_TIMEOUT_SECONDS = 600
TEMPERATURE = "0.6"
ENABLE_THINKING = "1"
DUPLICATE_READ_ONLY_LIMIT = 2
MAX_READ_ONLY_WITHOUT_PROGRESS = 8
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
        "bm.solver.max_actions_per_game = 96",
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        "action budget",
    )
    run = _replace_once(
        run,
        "bm.solver.max_runtime_s_per_game = 2700.0",
        f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}",
        "runtime budget",
    )
    run = _replace_once(
        run,
        "timedelta(seconds=2700)",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "behavior deadline",
    )
    notebook["cells"][14]["source"] = run.splitlines(True)
    notebook["cells"][0]["source"] = [
        "# Ring 9 controller ownership through G3 canary v2\n",
        "One ls20 world, 16 actions and 20 minutes: controller-run G0 and G1 probes, one Duck "
        "ego explanation, controller-run demonstration, controller-certified G2, its bound demonstration, and G3 entry. \n",
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
            raise RuntimeError(f"Notebook is missing v2 marker: {marker}")
    for stale in (OLD_DATASET_ID, OLD_PACKAGE_NAME, "max_actions_per_game = 200"):
        if stale in rendered:
            raise RuntimeError(f"Notebook retained stale base marker: {stale}")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell["source"]),
                "<ring9-controller-first-ls20-v2-notebook>",
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
        (
            f"'LOCAL_ANALYZER_MAX_OUTPUT': '{MAX_OUTPUT_TOKENS}',\n"
            f"    'LOCAL_ANALYZER_TIMEOUT': '{MODEL_REQUEST_TIMEOUT_SECONDS}'"
        ),
        "model output cap",
    )
    required = (
        f"'LOCAL_ANALYZER_ENABLE_THINKING': '{ENABLE_THINKING}'",
        f"'LOCAL_ANALYZER_TEMPERATURE': '{TEMPERATURE}'",
        f"'LOCAL_ANALYZER_DUPLICATE_READ_ONLY_LIMIT': '{DUPLICATE_READ_ONLY_LIMIT}'",
        f"'LOCAL_ANALYZER_MAX_READ_ONLY_WITHOUT_PROGRESS': '{MAX_READ_ONLY_WITHOUT_PROGRESS}'",
    )
    for marker in required:
        if marker not in command:
            raise RuntimeError(f"The proven v7 setup is missing {marker}.")
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
        raise RuntimeError("The v7 package manifest changed.")
    shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns(".DS_Store", "RUN_STATUS.md"))
    bundle, kernel = OUT / "source-dataset", OUT / "kernel"

    common._copy_source(bundle, variant)
    gates = bundle / "src" / "ARC3-Inference" / "inference" / "framework"
    required_source = (
        (gates / "controller_executor.py", 'if machine.gate_id == "G2-COUNTER"'),
        (gates / "controller_executor.py", "Every exact G1 probe"),
        (gates / "controller_executor.py", "_certified_answer_step(machine, view, refused=refused)"),
        (
            bundle / "src" / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py",
            "retaining controller ownership after wake",
        ),
        (gates / "virelai_gates.py", "def planned_nav_step"),
        (gates / "virelai_gates.py", "CONTROLLER_OBSERVED_EGO_REFUSAL_WITHOUT_TARGET_DELTA"),
        (bundle / "src" / "ARC3-Inference" / "inference" / "agent" / "tool_agent.py", "no_progress_tool_loop"),
        (bundle / "src" / "ARC3-Inference" / "inference" / "agent" / "tool_agent.py", "contract_repair_loop"),
        (gates / "card_builder.py", 'candidates.append(("accepted_model"'),
    )
    for source, marker in required_source:
        if marker not in source.read_text():
            raise RuntimeError(f"Packaged source is missing {marker} in {source.name}.")

    dataset = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset.update(id=DATASET_ID, title="Virelai Ring 9 controller-first ls20 v2")
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
        raise RuntimeError("Base kernel identity does not match v7.")
    metadata["id"] = KERNEL_ID
    metadata["title"] = KERNEL_ID.split("/", 1)[1]
    metadata["dataset_sources"][0] = DATASET_ID
    metadata["docker_image"] = (
        "gcr.io/kaggle-private-byod/python@sha256:"
        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
    )
    common._write_json(metadata_path, metadata)
    _rewrite_notebook(kernel / "taaf_kaggle_run_share.ipynb")
    _rewrite_setup(bundle)
    _rewrite_benchmark(bundle, variant)

    preflight_path = bundle / "checkpoint-preflight.json"
    preflight = json.loads(preflight_path.read_text())
    preflight.update(
        schema="virelai-controller-first-ls20-v2-preflight-v1",
        stage="CONTROLLER-OWNERSHIP-THROUGH-G3-CANARY",
        claim=(
            "Tests whether Virelai executes G0, every exact G1 Delphi action and the prospective "
            "demonstration without model action selection; Duck explains the ego once; then the "
            "controller pursues the counter, submits the certified G2 answer, demonstrates it, "
            "installs the mask, and enters G3."
        ),
        source_commit=SOURCE_COMMIT,
        revisions="controller ownership parity through NAV G4 at 4e1be00",
        worlds=WORLDS,
        max_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS,
        inference_profile={
            "enable_thinking": True,
            "temperature": float(TEMPERATURE),
            "duplicate_read_only_limit": DUPLICATE_READ_ONLY_LIMIT,
            "max_read_only_without_progress": MAX_READ_ONLY_WITHOUT_PROGRESS,
            "model_request_timeout_seconds": MODEL_REQUEST_TIMEOUT_SECONDS,
            "purpose": "bounded action-ownership checkpoint; not a score run",
        },
        live_criteria=[
            "C0: G0 closes through CONTROLLER with zero model requests.",
            "C1: ACTION1x2, ACTION2x2, ACTION3x2 and ACTION4x2 are controller actions.",
            "C2: Duck explains the embodied ego and its movement laws at human-readable mechanism level.",
            "C3: the prospective ego demonstration is controller-owned, is graded SUPPORTED, and closes G1.",
            "C4: deterministic G2 pursuit produces the recurrent counter candidate without a Duck action.",
            "C5: the certified G2 answer and its bound demonstration are controller-owned.",
            "C6: G2 installs the complete mask and the gate machine enters G3.",
            "C7: every environment action is controller-owned; every Duck call is a semantic boundary.",
            "C8: the run ends at the explicit 16-action/1200-second cap or another controlled stop without crashing.",
        ],
        claim_limits=[
            "This canary does not grade competition score, level completion, or the full gate stack.",
            "It requires G3 entry but does not require G3 closure, lever discovery, G4 entry, or a win.",
            "Duck may be called if certified evidence cannot compute a lawful step; such a call fails C7 if it selects an environment action.",
            "Human review of lossless artifacts is required before claiming behavioral success.",
        ],
    )
    common._write_json(preflight_path, preflight)

    receipt_path = bundle / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt.update(
        schema="virelai-controller-first-ls20-v2-execution-receipt-v1",
        revisions="controller ownership parity through NAV G4 at 4e1be00",
        source_commit=SOURCE_COMMIT,
        worlds=WORLDS,
        inference_profile={
            "enable_thinking": True,
            "temperature": float(TEMPERATURE),
            "duplicate_read_only_limit": DUPLICATE_READ_ONLY_LIMIT,
            "max_read_only_without_progress": MAX_READ_ONLY_WITHOUT_PROGRESS,
            "model_request_timeout_seconds": MODEL_REQUEST_TIMEOUT_SECONDS,
        },
    )
    receipt["package"]["name"] = PACKAGE_NAME
    receipt["package"]["sha256"] = "0" * 64
    receipt["budgets"].update(
        max_environment_actions_per_world=MAX_ACTIONS,
        max_runtime_seconds_per_world=MAX_RUNTIME_SECONDS,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS,
    )
    if receipt["budgets"]["max_output_tokens_per_turn"] != MAX_OUTPUT_TOKENS:
        raise RuntimeError("The frozen receipt must carry the bounded model output cap.")
    common._write_json(receipt_path, receipt)

    (OUT / "RUN.md").write_text(
        "# Ring 9 controller-first ls20 v2 canary\n\n"
        "One ls20 world, one pass, 16 actions and 1200 seconds of behavior time. The pinned "
        "Qwen3.8-27B-FP8 runtime uses a 4096-token output cap, thinking enabled and temperature "
        "0.6. This tests controller ownership from G0 through certified G2 closure and G3 entry.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(
        "Source 4e1be00: full Ring 9 suite 549 passed; focused ownership regression tests 47 passed.\n"
        "V2 guards require exact-action priority, controller-certified NAV G2/G3/G4.1 answers, "
        "the G2 route planner, and counter-noise-safe refusal attribution. Notebook code must compile.\n"
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 controller-first ls20 v2\n\n"
        "Receipt-bound ls20 controller-ownership canary through G3 entry.\n"
    )
    (bundle / "preamble.txt").write_text(
        "R9 controller-first ls20 v2: ls20, 16 actions, 1200 seconds, 4096-token output cap, "
        "thinking enabled, Python 3.12 image pinned. Human review required.\n"
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

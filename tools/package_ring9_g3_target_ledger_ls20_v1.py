#!/usr/bin/env python3
"""Package the ls20 G3 visual-target execution-ledger Kaggle checkpoint.

Author: Sol (Alpha build seat), 2026-10-03.

This freezes the controller-ownership and target-ledger build. It reuses the successful v2 runtime,
then gives deterministic G3 enough actions to execute the ranked NAV roster.
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
BASE = ROOT / "kaggle" / "ring9-controller-first-ls20-v2"
BASE_PACKAGE_SHA256 = "b24e6bb6bdf1ae8180ec0ce4d57ee260a1593ac273b49936a97876d0889e2dd1"
OUT = ROOT / "kaggle" / os.environ.get(
    "VIRELAI_PACKAGE_DIR", "ring9-g3-target-ledger-ls20-v1"
)
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-controller-first-ls20-v2"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-target-ledger-ls20-v1"
OLD_KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v2"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g3-target-ledger-ls20-v1"
OLD_PACKAGE_NAME = "ring9-controller-first-ls20-v2"
PACKAGE_NAME = "ring9-g3-target-ledger-ls20-v1"
SOURCE_COMMIT = "8606448e0755974ee9cb045b71c276bd43dae8b2"
MAX_ACTIONS = 96
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
        "bm.solver.max_actions_per_game = 16",
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        "action budget",
    )
    run = _replace_once(
        run,
        "bm.solver.max_runtime_s_per_game = 1200.0",
        f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}",
        "runtime budget",
    )
    run = _replace_once(
        run,
        "timedelta(seconds=1200)",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "behavior deadline",
    )
    notebook["cells"][14]["source"] = run.splitlines(True)
    notebook["cells"][0]["source"] = [
        "# Ring 9 G3 visual-target execution ledger checkpoint v1\n",
        "One ls20 world, 96 actions and 20 minutes: prove that the prepopulated visual-object "
        "roster is executed and every eligible object ends reachable and typed, or provisionally "
        "unreachable under an evidence-bound route certificate.\n",
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
            raise RuntimeError(f"Notebook is missing target-ledger marker: {marker}")
    for stale in (OLD_DATASET_ID, OLD_PACKAGE_NAME, "max_actions_per_game = 200"):
        if stale in rendered:
            raise RuntimeError(f"Notebook retained stale base marker: {stale}")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell["source"]),
                "<ring9-g3-target-ledger-ls20-v1-notebook>",
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
    required = (
        f"'LOCAL_ANALYZER_MAX_OUTPUT': '{MAX_OUTPUT_TOKENS}'",
        f"'LOCAL_ANALYZER_TIMEOUT': '{MODEL_REQUEST_TIMEOUT_SECONDS}'",
        f"'LOCAL_ANALYZER_ENABLE_THINKING': '{ENABLE_THINKING}'",
        f"'LOCAL_ANALYZER_TEMPERATURE': '{TEMPERATURE}'",
        f"'LOCAL_ANALYZER_DUPLICATE_READ_ONLY_LIMIT': '{DUPLICATE_READ_ONLY_LIMIT}'",
        f"'LOCAL_ANALYZER_MAX_READ_ONLY_WITHOUT_PROGRESS': '{MAX_READ_ONLY_WITHOUT_PROGRESS}'",
    )
    for marker in required:
        if marker not in command:
            raise RuntimeError(f"The proven controller-first v2 setup is missing {marker}.")
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
        raise RuntimeError("The successful controller-first v2 package manifest changed.")
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
        (gates / "virelai_gates.py", "UNREACHABLE_IN_CURRENT_WORLD_STATE"),
        (gates / "virelai_gates.py", "_nav_contact_records"),
        (
            bundle / "src" / "ARC3-Inference" / "inference" / "agent" / "gate_artifacts.py",
            "_write_g3_target_ledger",
        ),
    )
    for source, marker in required_source:
        if marker not in source.read_text():
            raise RuntimeError(f"Packaged source is missing {marker} in {source.name}.")

    dataset = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset.update(id=DATASET_ID, title="Virelai Ring 9 G3 target ledger ls20 v1")
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
        raise RuntimeError("Base kernel identity does not match controller-first v2.")
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
        schema="virelai-g3-target-ledger-ls20-v1-preflight-v1",
        stage="G3-NAV-COMPLETE-TARGET-LEDGER",
        claim=(
            "Tests whether Virelai populates the complete counter-filtered visual-object roster "
            "before G3 execution, then uses controller-owned NAV actions to execute every eligible "
            "row and classify it as reachable with a physics type or provisionally unreachable "
            "after exhausting the demonstrated reachable component."
        ),
        source_commit=SOURCE_COMMIT,
        revisions="G3 visual target execution ledger at 8606448",
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
            "purpose": "complete G3 NAV target-accounting checkpoint; not a score run",
        },
        live_criteria=[
            "C0: G0-G2 repeat the already-proven controller-owned closure and install the complete counter mask.",
            "C1: the G3 target-ledger artifact states that its roster was populated before execution.",
            "C2: every counter-filtered eligible rank is present with stable identity and visual type.",
            "C3: every eligible row reaches execution_status EXECUTED.",
            "C4: every eligible row ends REACHABLE or UNREACHABLE_IN_CURRENT_WORLD_STATE.",
            "C5: every reachable row has contact evidence, contact type, and a non-pending physics type.",
            "C6: every unreachable row has exhausted-route evidence and explicit reopen conditions.",
            "C7: counter-role exclusions remain separate and complete.",
            "C8: every mechanical environment action remains controller-owned.",
            "C9: the run ends after complete accounting or at the explicit 96-action/1200-second safety cap without crashing.",
        ],
        claim_limits=[
            "This checkpoint does not grade competition score, level completion, G4 closure, or a win.",
            "UNREACHABLE_IN_CURRENT_WORLD_STATE is provisional and must reopen after a relevant world or routing change.",
            "Duck may explain a semantic boundary but may not select a controller-computable environment action.",
            "Human review of lossless artifacts is required before claiming behavioral success.",
        ],
    )
    common._write_json(preflight_path, preflight)

    receipt_path = bundle / "execution_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt.update(
        schema="virelai-g3-target-ledger-ls20-v1-execution-receipt-v1",
        revisions="G3 visual target execution ledger at 8606448",
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
        "# Ring 9 G3 target ledger ls20 v1\n\n"
        "One ls20 world, one pass, 96 actions and 1200 seconds of behavior time. The pinned "
        "Qwen3.8-27B-FP8 runtime uses a 4096-token output cap, thinking enabled and temperature "
        "0.6. This tests complete, evidence-bound execution of the G3 NAV target roster.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(
        "Source 8606448: full Ring 9 suite 553 passed; focused target-ledger suites 40 passed.\n"
        "Guards require the complete roster artifact, observed-contact reachability, provisional "
        "route-exhaustion labels, reopening after world changes, and controller action ownership.\n"
    )
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G3 target ledger ls20 v1\n\n"
        "Receipt-bound ls20 checkpoint for complete G3 NAV target accounting.\n"
    )
    (bundle / "preamble.txt").write_text(
        "R9 G3 target ledger ls20 v1: ls20, 96 actions, 1200 seconds, 4096-token output cap, "
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

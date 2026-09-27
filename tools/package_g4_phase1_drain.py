#!/usr/bin/env python3
"""Freeze the one-world Ring 9 G4 Phase-1 drain (S1 return edge) checkpoint.

Derived from the frozen G3 vc33 closure v3 package. The G3-v3 notebook already carries the
final-form receipt binding, the benchmark-start behavior deadline, and the nested src.zip mount
branch, so this G3 -> G4 transform only relabels the package, widens the behavior budget, and
restates the claim and the preregistered S1 exit criteria. No receipt-region surgery is repeated.

Source provenance (changed from the G1-G3 packagers): the bundled source is exported from the
committed tree at SOURCE_COMMIT with `git archive`, never copied from the working tree. Earlier
packagers copied the working tree and therefore shipped gitignored local files, including the
ARC3-Inference `.env` holding API keys. A secret guard now refuses to finish a package that
contains any `.env*` file (other than `.env.example`) or a key-shaped token.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import pickle
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VARIANT_REL = "variants/ring9-cybernetic-gates"
SOURCE_PATHS = ("ARC3-Inference", "tufa-arc-agi-framework")
BASE = ROOT / "kaggle" / "ring9-g3-vc33-closure-v3"
OUT = ROOT / "kaggle" / "ring9-g4-phase1-drain-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-phase1-drain-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1"
PACKAGE_NAME = "ring9-g4-phase1-drain-v1"
OLD_PACKAGE_NAME = "ring9-g3-vc33-closure-v3"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g3-vc33-closure-v3"
WORLDS = ["vc33-5430563c"]
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 160
MAX_RUNTIME_SECONDS = 7200
OLD_MAX_ACTIONS = 96
OLD_MAX_RUNTIME_SECONDS = 2700
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = "f8a967e909049577885bf7f9b473c98bd45b20f7"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} (S1: pending-lever return edge).\n"
    "373 passed, 1 skipped with the vendored TAAF runtime on the import path "
    "(isolated Python 3.12 export; the skip is a recorded ft09 artifact outside the source "
    "package). Director-run Mac pytest at the same commit: 374 passed.\n"
    "16 focused G4.2 orbit and G4.3 limits tests passed, including the two-lever Phase-1 drain "
    "and the G4.3 open guard.\n"
)

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", ".DS_Store", "__pycache__", ".pytest_cache", ".ruff_cache",
    "*.pyc", "arc3_inference.egg-info", "offline-gates", "tests", "variants", "runs",
)
BASE_IGNORE = shutil.ignore_patterns(".DS_Store", "source-dataset 2", "RUN_STATUS.md")
DOTENV_NAME = re.compile(r"^\.env(\..+)?$")
DOTENV_ALLOWED = {".env.example"}
SECRET_PATTERNS = (
    re.compile(rb"sk-or-v1-[A-Za-z0-9]{32,}"),
    re.compile(rb"sk-(?:ant|proj)-[A-Za-z0-9_-]{24,}"),
    re.compile(rb"(?:OPENROUTER|OPENAI|ANTHROPIC|ARC|KAGGLE|HF)_(?:API_)?(?:KEY|TOKEN)\s*=\s*['\"]?[A-Za-z0-9_-]{16,}"),
)

# Preregistered S1 exit criteria (BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1, graded from
# artifact state, not prose). Only criteria observable in a live run are listed as live grades.
S1_LIVE_CRITERIA = [
    "C1: every confirmed lever drains through Phase 1 - each G4.2 orbit reaches a period with "
    "a stop disposition and lands a lever class (TOGGLE/CYCLE/ABSORBING/RECURRENT).",
    "C2: the final LeverOrbitSet lists every confirmed lever in lever_entities with "
    "pending_lever_entities empty; products accumulate and are never replaced.",
    "C3: no prior lever's orbit or class is invalidated anywhere in the gate journal.",
    "C4: after the first lever's orbit is accepted, the active gate remains G4.2 for the next "
    "pending lever; G4.3 opens only after pending_lever_entities is empty.",
]
S1_OFFLINE_ONLY = [
    "C5 (newborn append) is not graded live: S1 wires the queue behavior through pending "
    "lever entities; a mid-orbit newborn reopen is slice S4.",
    "C6 (suite green) is established offline before packaging; see TEST_RESULTS.txt.",
]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _committed_source(workdir: Path) -> Path:
    """Return the variant directory exactly as committed at SOURCE_COMMIT.

    In the repository this runs `git archive SOURCE_COMMIT`. Where git is unavailable, set
    VIRELAI_SOURCE_EXPORT to an extracted `git archive` of the same commit whose
    `.source-commit` stamp names SOURCE_COMMIT. The working tree is never used.
    """
    export = os.environ.get("VIRELAI_SOURCE_EXPORT")
    if export:
        root = Path(export)
        stamp = (root / ".source-commit").read_text().strip()
        if stamp != SOURCE_COMMIT:
            raise RuntimeError(f"Source export is commit {stamp}, expected {SOURCE_COMMIT}.")
    else:
        paths = [f"{VARIANT_REL}/{name}" for name in SOURCE_PATHS]
        archive = subprocess.run(
            ["git", "-C", str(ROOT), "archive", "--format=tar", SOURCE_COMMIT, "--", *paths],
            check=True, capture_output=True,
        ).stdout
        root = workdir / "committed-source"
        root.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as handle:
            handle.extractall(root, filter="data")
    variant = root / VARIANT_REL
    for name in SOURCE_PATHS:
        if not (variant / name).is_dir():
            raise RuntimeError(f"Committed source export is missing {name}.")
    return variant


def _copy_source(bundle: Path, variant: Path) -> None:
    src = bundle / "src"
    shutil.rmtree(src, ignore_errors=True)
    src.mkdir()
    for name in SOURCE_PATHS:
        shutil.copytree(variant / name, src / name, ignore=IGNORE)
    gates = src / "ARC3-Inference" / "inference" / "framework" / "virelai_gates.py"
    if "_effective_target_id" not in gates.read_text():
        raise RuntimeError("Packaged source does not carry the S1 return edge.")


def _secret_guard(out: Path) -> None:
    """Refuse a package that carries a dotenv file or a key-shaped token anywhere."""
    findings: list[str] = []

    def scan(label: str, name: str, data: bytes) -> None:
        if DOTENV_NAME.match(name) and name not in DOTENV_ALLOWED:
            findings.append(f"dotenv file: {label}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(data):
                findings.append(f"key-shaped token: {label}")
                break

    for path in sorted(out.rglob("*")):
        if not path.is_file():
            continue
        label = str(path.relative_to(out))
        scan(label, path.name, path.read_bytes())
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for entry in archive.namelist():
                    scan(f"{label}!{entry}", Path(entry).name, archive.read(entry))
    if findings:
        raise RuntimeError("Secret guard refused the package: " + "; ".join(findings[:20]))


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label}, found {count}.")
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

    run_cell = notebook["cells"][14]
    source = "".join(run_cell["source"])
    source = _replace_once(
        source,
        f"bm.solver.max_actions_per_game = {OLD_MAX_ACTIONS}\n",
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}\n",
        "benchmark action budget",
    )
    source = _replace_once(
        source,
        f"bm.solver.max_runtime_s_per_game = {float(OLD_MAX_RUNTIME_SECONDS)}\n",
        f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}\n",
        "benchmark runtime budget",
    )
    source = _replace_once(
        source,
        f"soft_end = datetime.now() + timedelta(seconds={OLD_MAX_RUNTIME_SECONDS})\n",
        f"soft_end = datetime.now() + timedelta(seconds={MAX_RUNTIME_SECONDS})\n",
        "benchmark-start behavior deadline",
    )
    source = _replace_once(
        source,
        "G0-G3 execution receipt verified",
        "G0-G4 execution receipt verified",
        "receipt success marker",
    )

    required_once = {
        "package label": f'bm.label = "{PACKAGE_NAME}"',
        "benchmark action budget": f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        "benchmark runtime budget": f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}",
        "behavior deadline": f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "receipt comparison": "Execution receipt mismatch before benchmark start",
        "receipt success marker": "G0-G4 execution receipt verified",
        "gated mode": 'bm.solver.virelai_mode = "gated"',
    }
    for label, needle in required_once.items():
        count = source.count(needle)
        if count != 1:
            raise RuntimeError(f"Expected one {label}, found {count}.")
    run_cell["source"] = source.splitlines(True)

    notebook["cells"][0]["source"] = [
        "# Ring 9 G4 vc33 Phase-1 drain checkpoint (S1 return edge)\n",
        "Private one-world diagnostic: every confirmed lever is orbited and classified before any "
        "Phase-2 gate opens.\n",
    ]

    notebook_text = json.dumps(notebook)
    forbidden = {
        "stale G3 package name": OLD_PACKAGE_NAME,
        "stale G3 dataset": OLD_DATASET_ID,
        "stale G3 receipt marker": "G0-G3 execution receipt verified",
        "stale G3 action budget": f"max_actions_per_game = {OLD_MAX_ACTIONS}\\n",
        "stale G3 runtime budget": f"max_runtime_s_per_game = {float(OLD_MAX_RUNTIME_SECONDS)}",
        "notebook-wide target deadline": 'getattr(target, "max_runtime_s"',
    }
    for label, needle in forbidden.items():
        if needle in notebook_text:
            raise RuntimeError(f"Packaged notebook retained {label}.")
    if "nested_source" not in notebook_text:
        raise RuntimeError("Packaged notebook lost the verified Kaggle src.zip mount branch.")

    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell["source"]), "<g4-phase1-drain-notebook>", "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _rewrite_benchmark(bundle: Path, variant: Path) -> None:
    sys.path[:0] = [
        str(variant / "ARC3-Inference"),
        str(variant / "tufa-arc-agi-framework" / "src"),
    ]
    path = bundle / "benchmark_initial.pkl"
    with path.open("rb") as handle:
        benchmark = pickle.load(handle)
    benchmark.label = PACKAGE_NAME
    benchmark.n_passes = PASSES
    benchmark.game_weights = None
    benchmark.games = [
        game for game in benchmark.games
        if getattr(game, "env_name", None) in WORLDS
    ]
    if [game.env_name for game in benchmark.games] != WORLDS:
        raise RuntimeError("The frozen benchmark does not contain the exact requested vc33 world.")
    benchmark.solver.label = PACKAGE_NAME
    benchmark.solver.virelai_mode = "gated"
    benchmark.solver.max_actions_per_game = MAX_ACTIONS
    benchmark.solver.max_runtime_s_per_game = float(MAX_RUNTIME_SECONDS)
    benchmark.solver.concurrency = CONCURRENCY
    benchmark.solver.save_request_logs = True
    with path.open("wb") as handle:
        pickle.dump(benchmark, handle)


def _source_manifest(bundle: Path) -> dict[str, str]:
    excluded = {
        "dataset-metadata.json", "execution_receipt.json",
        "source-manifest.json", "src.zip",
    }
    return {
        str(path.relative_to(bundle)): _sha256(path)
        for path in sorted(bundle.rglob("*"))
        if path.is_file() and path.name not in excluded
    }


def _write_source_zip(bundle: Path) -> None:
    archive = bundle / "src.zip"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted((bundle / "src").rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(bundle))


def _package_manifest(out: Path) -> dict[str, str]:
    excluded = {"execution_receipt.json", "package-manifest.json"}
    return {
        str(path.relative_to(out)): _sha256(path)
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name not in excluded
    }


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite existing package: {OUT}")
    with tempfile.TemporaryDirectory() as workdir:
        variant = _committed_source(Path(workdir))
        try:
            summary = _build(variant)
            _secret_guard(OUT)
        except BaseException:
            shutil.rmtree(OUT, ignore_errors=True)
            raise
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("secret guard: clean")
    return 0


def _build(variant: Path) -> dict[str, Any]:
    shutil.copytree(BASE, OUT, ignore=BASE_IGNORE)
    bundle = OUT / "source-dataset"
    _copy_source(bundle, variant)
    criteria_md = "".join(f"- {line}\n" for line in S1_LIVE_CRITERIA)
    (OUT / "RUN.md").write_text(
        "# Ring 9 G4 vc33 Phase-1 drain checkpoint (S1 return edge)\n\n"
        f"Source commit `{SOURCE_COMMIT}`. This private diagnostic runs the gated Duck on vc33 "
        f"for one pass, with at most {MAX_ACTIONS} environment actions and {MAX_RUNTIME_SECONDS} "
        "seconds of behavior time after model setup.\n\n"
        "The checkpoint carries the G0-G3 path into G4 and tests the S1 descent controller: the "
        "machine must hold G4.2 until every confirmed lever is orbited with consecutive same-lever "
        "presses to a period and classified, and only then open G4.3 (Phase 2).\n\n"
        "## Preregistered live grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Precondition: S1 is gradable only if the run closes G3 with at least two confirmed levers. "
        "G3 closure on this exact served model has not yet been observed on Kaggle; a stall at or "
        "before G3 is a G3-on-this-model finding and leaves S1 ungraded, not failed.\n\n"
        f"Dataset: `{DATASET_ID}`  \n"
        f"Notebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the "
        "benchmark starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 G4 Phase-1 Drain v1"
    _write_json(bundle / "dataset-metadata.json", dataset_metadata)

    kernel_metadata = json.loads((OUT / "kernel" / "kernel-metadata.json").read_text())
    kernel_metadata["id"] = KERNEL_ID
    kernel_metadata["title"] = "taaf-virelai-ring9-g4-phase1-drain-v1"
    if kernel_metadata["dataset_sources"][0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel metadata does not lead with the G3-v3 source dataset.")
    kernel_metadata["dataset_sources"][0] = DATASET_ID
    if kernel_metadata.get("enable_internet") is not False or kernel_metadata.get("enable_gpu") is not True:
        raise RuntimeError("Kernel must run offline on GPU.")
    _write_json(OUT / "kernel" / "kernel-metadata.json", kernel_metadata)

    bundle_metadata = json.loads((bundle / "taaf-kaggle-bundle.json").read_text())
    bundle_metadata["created_at"] = datetime.now(timezone.utc).isoformat()
    bundle_metadata["benchmark_label"] = PACKAGE_NAME
    _write_json(bundle / "taaf-kaggle-bundle.json", bundle_metadata)

    checkpoint = {
        "schema": "virelai-gated-checkpoint-preflight-v2",
        "stage": "G0-G4.2-PHASE1-DRAIN",
        "claim": (
            "Evaluates the G0-G3 path into G4 and the S1 descent controller: after the first "
            "lever's orbit is accepted the machine stays in G4.2 for every pending lever, each "
            "orbit is classified, and G4.3 (Phase 2) opens only once no lever is pending."
        ),
        "source_commit": SOURCE_COMMIT,
        "worlds": WORLDS,
        "model": MODEL,
        "passes": PASSES,
        "concurrency": CONCURRENCY,
        "max_actions_per_world": MAX_ACTIONS,
        "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
        "context_window_tokens": CONTEXT_WINDOW,
        "max_output_tokens_per_turn": "server_default",
        "tool_output_tokens": TOOL_OUTPUT_TOKENS,
        "virelai_mode": "gated",
        "semantic_action_aliases_exposed": False,
        "s1_live_criteria": S1_LIVE_CRITERIA,
        "s1_offline_only": S1_OFFLINE_ONLY,
        "required_mounted_directories": [
            "src/ARC3-Inference", "src/tufa-arc-agi-framework",
        ],
        "required_mounted_files": [
            "source-manifest.json", "checkpoint-preflight.json",
            "execution_receipt.json", "taaf-kaggle-bundle.json",
            "benchmark_initial.pkl", "deploy_target.pkl", "setup_commands.json",
        ],
        "source_delivery": (
            "Kaggle may mount src/ directly or transport it as src.zip; "
            "the notebook verifies extracted files before imports."
        ),
        "claim_limits": [
            "Automated grades do not establish semantic correctness.",
            "S1 is gradable only if G3 closes with at least two confirmed levers; G3 closure on "
            "this served model has not yet been observed on Kaggle.",
            "Phase-2 content (reversal, persistence, couplings) is out of scope; G4.3 opening is "
            "graded only as the S1 gate edge, not as a Phase-2 result.",
            "A receipt-bound human frame review is required for G1-G4 semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G4 vc33 Phase-1 drain checkpoint\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact "
        "execution receipt before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 G4 Phase-1 drain (S1) exact-model checkpoint: vc33 only, one pass, "
        f"{MAX_ACTIONS} actions and {MAX_RUNTIME_SECONDS} seconds of behavior time after model "
        f"setup. Source {SOURCE_COMMIT[:7]}. Human review required.\n"
    )
    (bundle / "git_status.txt").write_text(
        f"Isolated source export of commit {SOURCE_COMMIT}. Source-manifest and "
        "package-manifest hashes define the exact checkpoint; working-tree changes outside "
        "this export are not included.\n"
    )

    _rewrite_benchmark(bundle, variant)
    _rewrite_notebook(OUT / "kernel" / "taaf_kaggle_run_share.ipynb")

    source_manifest = _source_manifest(bundle)
    _write_json(bundle / "source-manifest.json", source_manifest)
    _write_source_zip(bundle)
    manifest_sha256 = _sha256(bundle / "source-manifest.json")

    receipt = {
        "schema": "virelai-g4-phase1-drain-execution-receipt-v1",
        "package": {
            "name": PACKAGE_NAME,
            "sha256": "0" * 64,
            "manifest_sha256": manifest_sha256,
        },
        "model": {"id": MODEL},
        "budgets": {
            "max_environment_actions_per_world": MAX_ACTIONS,
            "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
            "context_window_tokens": CONTEXT_WINDOW,
            "max_output_tokens_per_turn": "server_default",
            "tool_output_tokens": TOOL_OUTPUT_TOKENS,
        },
        "worlds": WORLDS,
        "passes": PASSES,
        "concurrency": CONCURRENCY,
        "mode": "gated",
        "behavior_window_starts_at_benchmark": True,
    }
    _write_json(bundle / "execution_receipt.json", receipt)

    package_manifest = _package_manifest(OUT)
    _write_json(OUT / "package-manifest.json", package_manifest)
    package_sha256 = _sha256(OUT / "package-manifest.json")
    receipt["package"]["sha256"] = package_sha256
    _write_json(bundle / "execution_receipt.json", receipt)
    _write_json(OUT / "execution_receipt.json", receipt)

    # Receipt files are deliberately outside both manifests to avoid a digest cycle.
    return {
        "out": str(OUT),
        "source files": len(source_manifest),
        "package files": len(package_manifest),
        "package sha256": package_sha256,
        "source manifest sha256": manifest_sha256,
    }


if __name__ == "__main__":
    raise SystemExit(main())

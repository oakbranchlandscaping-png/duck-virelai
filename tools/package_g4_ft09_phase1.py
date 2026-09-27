#!/usr/bin/env python3
"""Freeze the one-world Ring 9 G4 ft09 checkpoint (full Phase-1 drain, then G4.3).

Author: Claude (Alpha build seat), 2026-09-27.

Derived from the frozen, committed `ring9-g4-phase1-drain-v1` package: its notebook carries the
receipt binding, the benchmark-start deadline and the nested src.zip mount branch proven on Kaggle.
This transform switches the world to ft09, widens the budget, restates the claim and the
preregistered criteria, and re-vendors source from a committed export.

Why ft09 (Director, 2026-09-27): on vc33 the second lever's orbit crosses a level boundary, so Phase
1 cannot fully drain there. ft09's controls historically return to an exact prior state (period 2)
without a level change, so the full drain and the Phase-2 (G4.3) opening become observable.

Source provenance: exported with `git archive SOURCE_COMMIT` (or a `VIRELAI_SOURCE_EXPORT` directory
whose `.source-commit` stamp matches); never the working tree. The secret guard refuses any `.env*`
(other than `.env.example`) or key-shaped token anywhere in the package, including src.zip entries.
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
BASE = ROOT / "kaggle" / "ring9-g4-phase1-drain-v1"
OUT = ROOT / "kaggle" / "ring9-g4-ft09-phase1-v1"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-phase1-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-ft09-phase1-v1"
PACKAGE_NAME = "ring9-g4-ft09-phase1-v1"
OLD_PACKAGE_NAME = "ring9-g4-phase1-drain-v1"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-phase1-drain-v1"
WORLDS = ["ft09-0d8bbf25"]
OLD_WORLDS = ["vc33-5430563c"]
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 200
MAX_RUNTIME_SECONDS = 10800
OLD_MAX_ACTIONS = 160
OLD_MAX_RUNTIME_SECONDS = 7200
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = "8cfb7827cb94cb711c7924e877b41f3365765cde"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} (S1 return edge + boundary release).\n"
    "Isolated Python 3.12 export: 377 passed, 1 skipped (a recorded ft09 artifact outside the "
    "source package). Director-run Mac pytest at the same commit with the protocol's two ignored "
    "suites: 366 passed.\n"
    "Boundary-release tests (4) failed on f8a967e and pass here, including a replay of the real "
    "Kaggle vc33 v1 G4.2 segment that reproduces every recorded masked address.\n"
)

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", ".DS_Store", "__pycache__", ".pytest_cache", ".ruff_cache",
    "*.pyc", "arc3_inference.egg-info", "offline-gates", "tests", "variants", "runs",
)
BASE_IGNORE = shutil.ignore_patterns(".DS_Store", "RUN_STATUS.md")
DOTENV_NAME = re.compile(r"^\.env(\..+)?$")
DOTENV_ALLOWED = {".env.example"}
SECRET_PATTERNS = (
    re.compile(rb"sk-or-v1-[A-Za-z0-9]{32,}"),
    re.compile(rb"sk-(?:ant|proj)-[A-Za-z0-9_-]{24,}"),
    re.compile(rb"(?:OPENROUTER|OPENAI|ANTHROPIC|ARC|KAGGLE|HF)_(?:API_)?(?:KEY|TOKEN)\s*=\s*['\"]?[A-Za-z0-9_-]{16,}"),
)

PRECONDITION = (
    "P: G3 closes on ft09 with at least two confirmed levers and a G4.1 anatomy for each. A stall at "
    "or before G3 is a G0-G3-on-ft09 finding (ft09 has never been through the ladder live) and leaves "
    "the G4 criteria ungraded, not failed."
)
LIVE_CRITERIA = [
    "C1: every confirmed lever drains through Phase 1 - each G4.2 orbit reaches a masked null or an "
    "exact prior-state recurrence and lands a class (TOGGLE / CYCLE / ABSORBING / RECURRENT).",
    "C2: the final LeverOrbitSet has pending_lever_entities empty and phase1_status COMPLETE; products "
    "accumulate and are never replaced.",
    "C3: no prior lever's orbit or class is invalidated.",
    "C4: after each accepted orbit the gate stays in G4.2 while any lever is pending; G4.3 opens only "
    "once phase1_status is COMPLETE.",
    "C5: G4.3 re-confirms a recurrence by one predicted additional period, grading every masked "
    "address (EXACT_RECURRENCE_RECONFIRMED or RECURRENCE_DIVERGED at the first mismatch).",
    "C6: Duck's accepted answers distinguish an observed finite recurrence from a universal or "
    "unconditional law.",
    "C7: no deadlock. If a boundary interrupts an orbit, the lever is recorded as interrupted and "
    "leaves pending; a level transition closes the level's G4 study with the "
    "G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9 card.",
]
INFRA_CRITERIA = [
    "I1: G0 assigns CLICK/God Mode from metadata.",
    "I2: G2 closes with a valid mask or the bounded COUNTER_NOT_OBSERVED_WITHIN_OPENING product; it "
    "does not stall.",
    "I3: G3 inherits the ranked opening frontier and completes the click sweep.",
    "I4: G4.2 records recurrences without ticker contamination.",
]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _committed_source(workdir: Path) -> Path:
    """Return the variant directory exactly as committed at SOURCE_COMMIT (never the working tree)."""
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
    gates = (src / "ARC3-Inference" / "inference" / "framework" / "virelai_gates.py").read_text()
    for marker in ("_effective_target_id", "_phase1_hold_reason", "_record_interruption"):
        if marker not in gates:
            raise RuntimeError(f"Packaged source does not carry {marker}.")


def _secret_guard(out: Path) -> None:
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
    required_once = {
        "package label": f'bm.label = "{PACKAGE_NAME}"',
        "benchmark action budget": f"bm.solver.max_actions_per_game = {MAX_ACTIONS}",
        "benchmark runtime budget": f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}",
        "behavior deadline": f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        "receipt comparison": "Execution receipt mismatch before benchmark start",
        "receipt success marker": "G0-G4 execution receipt verified",
        "gated mode": 'bm.solver.virelai_mode = "gated"',
        "world allowlist read": 'checkpoint["worlds"]',
    }
    for label, needle in required_once.items():
        count = source.count(needle)
        if count != 1:
            raise RuntimeError(f"Expected one {label}, found {count}.")
    run_cell["source"] = source.splitlines(True)

    notebook["cells"][0]["source"] = [
        "# Ring 9 G4 ft09 checkpoint: full Phase-1 drain, then G4.3\n",
        "Private one-world diagnostic: every confirmed lever is orbited and classified, then Phase 2 "
        "(G4.3) re-confirms recurrences.\n",
    ]

    notebook_text = json.dumps(notebook)
    forbidden = {
        "stale G4 package name": OLD_PACKAGE_NAME,
        "stale G4 dataset": OLD_DATASET_ID,
        "stale world": OLD_WORLDS[0],
        "stale action budget": f"max_actions_per_game = {OLD_MAX_ACTIONS}\\n",
        "stale runtime budget": f"max_runtime_s_per_game = {float(OLD_MAX_RUNTIME_SECONDS)}",
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
                "".join(cell["source"]), "<g4-ft09-notebook>", "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _rewrite_benchmark(bundle: Path, variant: Path) -> None:
    sys.path[:0] = [
        str(variant / "ARC3-Inference"),
        str(variant / "tufa-arc-agi-framework" / "src"),
    ]
    import taaf.game_api  # noqa: PLC0415 - resolved from the committed export above

    path = bundle / "benchmark_initial.pkl"
    with path.open("rb") as handle:
        benchmark = pickle.load(handle)
    template = next(
        (game for game in benchmark.games if getattr(game, "env_name", None) in OLD_WORLDS), None
    )
    if template is None:
        raise RuntimeError("The base benchmark does not contain the expected vc33 game template.")
    # The notebook rebuilds the offline game list from the competition files using the checkpoint
    # allowlist; the pickled game only has to name the world and carry the same arcade spec.
    benchmark.games = [
        taaf.game_api.GameAPI(env_name=world, arcade_spec=template.arcade_spec) for world in WORLDS
    ]
    benchmark.label = PACKAGE_NAME
    benchmark.n_passes = PASSES
    benchmark.game_weights = None
    benchmark.solver.label = PACKAGE_NAME
    benchmark.solver.virelai_mode = "gated"
    benchmark.solver.max_actions_per_game = MAX_ACTIONS
    benchmark.solver.max_runtime_s_per_game = float(MAX_RUNTIME_SECONDS)
    benchmark.solver.concurrency = CONCURRENCY
    benchmark.solver.save_request_logs = True
    if [game.env_name for game in benchmark.games] != WORLDS:
        raise RuntimeError("The rewritten benchmark does not name exactly the requested world.")
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
    criteria_md = "".join(f"- {line}\n" for line in (PRECONDITION, *LIVE_CRITERIA, *INFRA_CRITERIA))
    (OUT / "RUN.md").write_text(
        "# Ring 9 G4 ft09 checkpoint: full Phase-1 drain, then G4.3\n\n"
        f"Source commit `{SOURCE_COMMIT}`. This private diagnostic runs the gated Duck on "
        f"`{WORLDS[0]}` for one pass, with at most {MAX_ACTIONS} environment actions and "
        f"{MAX_RUNTIME_SECONDS} seconds of behavior time after model setup.\n\n"
        "The question: with levers that return to an exact prior state instead of crossing a level, "
        "does the machine orbit and classify every lever, report Phase 1 complete, and only then open "
        "G4.3, which re-confirms each recurrence by one predicted period?\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Historical context, not a prediction to grade against: a September 8 controlled artifact found "
        "five self-reactive ft09 controls, four with exact two-state returns, and an independent ticker. "
        "Do not compare this run's scores or action counts with vc33.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the benchmark "
        "starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 G4 ft09 Phase-1 v1"
    _write_json(bundle / "dataset-metadata.json", dataset_metadata)

    kernel_metadata = json.loads((OUT / "kernel" / "kernel-metadata.json").read_text())
    if kernel_metadata["dataset_sources"][0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel metadata does not lead with the G4 source dataset.")
    kernel_metadata["id"] = KERNEL_ID
    kernel_metadata["title"] = "taaf-virelai-ring9-g4-ft09-phase1-v1"
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
        "stage": "G0-G4.3-FT09-PHASE1-DRAIN",
        "claim": (
            "Evaluates the G0-G3 path on ft09 into G4, the full Phase-1 drain of every confirmed lever "
            "with the S1 return edge and the boundary release, and G4.3 recurrence re-confirmation "
            "once Phase 1 is complete."
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
        "precondition": PRECONDITION,
        "live_criteria": LIVE_CRITERIA,
        "infrastructure_criteria": INFRA_CRITERIA,
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
            "ft09 has never been through the gate ladder live; G0-G3 closure is a precondition.",
            "Phase-2 couplings, sequences (ABA/ABC) and cross-level work are out of scope.",
            "A receipt-bound human frame review is required for semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G4 ft09 checkpoint\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 G4 ft09 exact-model checkpoint: {WORLDS[0]} only, one pass, {MAX_ACTIONS} actions "
        f"and {MAX_RUNTIME_SECONDS} seconds of behavior time after model setup. Source "
        f"{SOURCE_COMMIT[:7]}. Human review required.\n"
    )
    (bundle / "git_status.txt").write_text(
        f"Isolated source export of commit {SOURCE_COMMIT}. Source-manifest and package-manifest "
        "hashes define the exact checkpoint; working-tree changes outside this export are not "
        "included.\n"
    )

    _rewrite_benchmark(bundle, variant)
    _rewrite_notebook(OUT / "kernel" / "taaf_kaggle_run_share.ipynb")

    source_manifest = _source_manifest(bundle)
    _write_json(bundle / "source-manifest.json", source_manifest)
    _write_source_zip(bundle)
    manifest_sha256 = _sha256(bundle / "source-manifest.json")

    receipt = {
        "schema": "virelai-g4-ft09-phase1-execution-receipt-v1",
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

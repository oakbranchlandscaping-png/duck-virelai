#!/usr/bin/env python3
"""Freeze the Ring 9 ft09 guided v2 checkpoint (revisions R9-R04 and R9-R05).

Author: Claude (Alpha build seat), 2026-09-28.

Derived from the frozen, committed `ring9-g4-ft09-guided-v1` package (`b68228a`), whose notebook
ran cleanly on Kaggle on 2026-09-28 (receipt byte-identical; G2 closed live under axiom A1; the run
then crashed at G3 entry on the card-size guard). Same world, model and budget. This transform
renames the package, restates the claim and the preregistered criteria, and re-vendors source from
the committed export at SOURCE_COMMIT.

What the source adds over guided v1 (REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md):
  R9-R04  the G3 card is bounded regardless of world size (axiom A6); the G2 counter label's
          trigger must agree with the record (A1 v2).
  R9-R05  an object that recolours in place keeps its entity identity, so G3 can witness ft09's
          self-recolouring controls as levers; the ft09 ladder passes offline.
See BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md.

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
BASE = ROOT / "kaggle" / "ring9-g4-ft09-guided-v1"
BASE_PACKAGE_SHA256 = "ed456471b668af375a0a466b39097f091cd789dc23a466ef38785ea88608b1d8"
OUT = ROOT / "kaggle" / "ring9-g4-ft09-guided-v2"
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v2"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v2"
PACKAGE_NAME = "ring9-g4-ft09-guided-v2"
OLD_PACKAGE_NAME = "ring9-g4-ft09-guided-v1"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v1"
OLD_KERNEL_TITLE = "taaf-virelai-ring9-g4-ft09-guided-v1"
WORLDS = ["ft09-0d8bbf25"]
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 200
MAX_RUNTIME_SECONDS = 10800
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = "4329185bd77eec5f3a4bb8c73d76f08bd36cb1ce"
REVISIONS = "R9-R04 + R9-R05"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} ({REVISIONS}: G3 bounded card and counter trigger label; G3 "
    "entity identity survives recolour).\n"
    "Cloud Python 3.12, full suite: 411 passed, 1 skipped (a recorded ft09 artifact outside the "
    "source package). Director-run Mac pytest at the same commit with the protocol's two ignored "
    "suites: 400 passed.\n"
    "Offline ft09 ladder (tests/test_ft09_ladder_offline.py): the real 57-transition G2 record, then "
    "the recorded control law continued by hypothesis, reaches G4-A SATISFIED with both controls "
    "confirmed at transition 131 of 200; every binding card is under the 24,000-character budget "
    "(largest 15,792).\n"
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
    "P: G3 closes on ft09 with at least two confirmed levers and a G4.1 anatomy for each. G2 "
    "criteria are graded regardless; a stall at or before G3 leaves the G4 criteria ungraded, not "
    "failed."
)
LIVE_CRITERIA = [
    "G2-1 (axiom A1): G2 closes either with a counter model and mask after one frozen "
    "footprint-scoped prediction (COUNTER_REWRITE or COUNTER_SILENT, on an action Duck chose) is "
    "SUPPORTED, or as COUNTER_NOT_OBSERVED after every ranked object was clicked. Record which.",
    "G2-2 (purity, recomputed from artifacts): every recorded change inside the mask footprint "
    "follows the counter rewrite or its inverse, and at least one witness acted away from the "
    "footprint.",
    "G2-3 (A1 v2, recomputed from artifacts): the accepted counter model's trigger is admissible "
    "for the trigger class computed from the whole G2 record (EVERY_TRANSITION, "
    "EFFECTIVE_TRANSITIONS_ONLY, IRREGULAR, or OPEN admitting either simple class).",
    "A6-1 (axiom A6): no binding gate card exceeds the runtime's 24,000-character budget at any "
    "gate; a run that ends on the card-size guard fails this criterion.",
    "G3-1 (prediction from the offline ladder, R9-R05): G3 witnesses both ft09 control tiles as "
    "levers (LOCAL_LEVER_WITNESS, prospectively confirmed) and neither is filed as "
    "UNRESOLVED_ATTRIBUTION. Graded only if G2 closes with a counter model.",
    "A-1 (G4-A): every lever ends with a CONFIRMED or DIVERGED run and an accepted explanation, or "
    "is recorded as interrupted; the final LeverOrbitSet is phase1_status COMPLETE or "
    "CLOSED_BY_LEVEL_BOUNDARY with nothing pending, and no prior lever's run or class is "
    "invalidated.",
    "A-2 (audit fidelity, recomputed from gate events): each accepted run is a consecutive "
    "same-click sequence of Duck-chosen presses whose stop and confirmation dispositions match the "
    "masked states; broken runs are recorded, never counted.",
    "A-3: Duck's accepted explanations distinguish the observed finite run from a universal or "
    "unconditional law.",
    "N-1 (axiom A2): no gate idles without a legal move. Any such stall ends as "
    "controller_no_legal_move within the watchdog limit; a declared end (level closed, "
    "WAIT_FOR_NEXT_G4_SLICE) is reported with its idle time, not failed.",
    "R (reported, not graded): actions and wall time per gate; Duck's G2 and G4-A choices (lever "
    "presses versus other actions, broken runs, rejected G2 candidates or labels); the prediction "
    "form Duck chose in G2; bar cells remaining at the end; the largest card per gate.",
]
INFRA_CRITERIA = [
    "I1: G0 assigns CLICK/God Mode from metadata; guided capabilities (GUIDED_ACTION) are served "
    "for G2 and G4-A.",
    "I2: the downloaded execution receipt is byte-identical to the package receipt.",
    "I3: G3 inherits the G2 frontier (the ranked prefix Duck covered) and completes the click sweep.",
    "I4: with the counter masked, G4-A runs record nulls and recurrences without counter "
    "contamination.",
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
    agent = (src / "ARC3-Inference" / "inference" / "agent" / "tool_agent.py").read_text()
    if "_controller_no_legal_move" not in agent:
        raise RuntimeError("Packaged source does not carry the axiom-A2 watchdog.")
    if not (src / "ARC3-Inference" / "inference" / "framework" / "g4_guided.py").is_file():
        raise RuntimeError("Packaged source does not carry g4_guided.py.")
    for marker in (
        "_LeverStudyTarget", "COUNTER_TARGET", "_purity_violations", "legal_move_status",
        "_phase1_hold_reason", "_bound_working_card", "record_trigger",
    ):
        if marker not in gates:
            raise RuntimeError(f"Packaged source does not carry {marker}.")
    entities = (src / "ARC3-Inference" / "inference" / "framework" / "entity_observation.py").read_text()
    if "_continuity_match" not in entities:
        raise RuntimeError("Packaged source does not carry the R9-R05 continuity rule.")


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

    # Same world and budget as the base package: only identities change in the run cell.
    run_source = "".join(notebook["cells"][14]["source"])
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
        count = run_source.count(needle)
        if count != 1:
            raise RuntimeError(f"Expected one {label}, found {count}.")

    notebook["cells"][0]["source"] = [
        "# Ring 9 ft09 guided checkpoint v2: stated-target G2 and G4-A (R9-R04, R9-R05)\n",
        "Private one-world diagnostic: Duck executes stated targets (counter axiom A1 with a "
        "record-checked trigger, guided lever study G4-A); G3 stays scripted with a bounded card "
        "and recolour-safe entity identity; the no-legal-move watchdog is armed.\n",
    ]

    notebook_text = json.dumps(notebook)
    forbidden = {
        "stale package name": OLD_PACKAGE_NAME,
        "stale dataset": OLD_DATASET_ID,
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
                "".join(cell["source"]), "<g4-ft09-guided-v2-notebook>", "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
    path.write_text(json.dumps(notebook, indent=1) + "\n")


def _rewrite_benchmark(bundle: Path, variant: Path) -> None:
    # Same world and arcade spec as the base package; no game rebuild. Unpickling imports the
    # solver classes: import them from the export without writing bytecode, so neither the
    # export nor the bundle gains or rewrites a __pycache__ file (the repo tracks some .pyc).
    path = bundle / "benchmark_initial.pkl"
    sys.dont_write_bytecode = True
    sys.path[:0] = [
        str(variant / "ARC3-Inference"),
        str(variant / "tufa-arc-agi-framework" / "src"),
    ]
    with path.open("rb") as handle:
        benchmark = pickle.load(handle)
    if [game.env_name for game in benchmark.games] != WORLDS:
        raise RuntimeError("The base benchmark does not name exactly the requested world.")
    benchmark.label = PACKAGE_NAME
    benchmark.n_passes = PASSES
    benchmark.game_weights = None
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
    if _sha256(BASE / "package-manifest.json") != BASE_PACKAGE_SHA256:
        raise RuntimeError("Base package manifest does not match the committed ft09 package.")
    shutil.copytree(BASE, OUT, ignore=BASE_IGNORE)
    bundle = OUT / "source-dataset"
    _copy_source(bundle, variant)
    criteria_md = "".join(f"- {line}\n" for line in (PRECONDITION, *LIVE_CRITERIA, *INFRA_CRITERIA))
    (OUT / "RUN.md").write_text(
        "# Ring 9 ft09 guided checkpoint v2\n\n"
        f"Source commit `{SOURCE_COMMIT}` ({REVISIONS}). This private diagnostic runs the gated Duck "
        f"on `{WORLDS[0]}` for one pass, with at most {MAX_ACTIONS} environment actions and "
        f"{MAX_RUNTIME_SECONDS} seconds of behavior time after model setup.\n\n"
        "The question: with the G3 card bounded (A6), the counter label checked against the record "
        "(A1 v2) and recolour-safe entity identity (R9-R05), does the stated-target ladder carry "
        "ft09 past G3 to a G4-A lever study that Duck executes by its own presses?\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Baseline for comparison of controller behavior only (not scores): `ring9-g4-ft09-guided-v1` "
        "(G2 closed live at transition 57 under A1; the run crashed at G3 entry on a 67,939-character "
        "card). Prior evidence, not a prediction to grade against: the bar ticked on 3 of 3 control "
        "clicks and 0 of 54 dead clicks. Offline, the recorded control law continued by hypothesis "
        "reaches G4-A SATISFIED at transition 131.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the "
        "benchmark starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 G4 ft09 guided v2"
    _write_json(bundle / "dataset-metadata.json", dataset_metadata)

    kernel_metadata = json.loads((OUT / "kernel" / "kernel-metadata.json").read_text())
    if kernel_metadata["dataset_sources"][0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel metadata does not lead with the G4 source dataset.")
    kernel_metadata["id"] = KERNEL_ID
    if kernel_metadata.get("title") != OLD_KERNEL_TITLE:
        raise RuntimeError("Base kernel metadata title is not the committed ft09 kernel.")
    kernel_metadata["title"] = "taaf-virelai-ring9-g4-ft09-guided-v2"
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
        "stage": "G0-G4A-FT09-GUIDED-V2",
        "claim": (
            "Evaluates the stated-target ladder on ft09 with R9-R04 and R9-R05: G2 under the "
            "counter axiom with a record-checked trigger, the scripted G3 sweep with a bounded card "
            "and recolour-safe identity, and the guided G4-A lever study, with the axiom-A2 "
            "no-legal-move watchdog armed."
        ),
        "source_commit": SOURCE_COMMIT,
        "revisions": REVISIONS,
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
            "G2 has closed live once (guided v1); G3 and G4 on ft09 are proven offline only, under a control law extrapolated from three clicks.",
            "Duck's action choices are the object of study; the offline ladder replaced Duck with a trivial policy.",
            "G4-B (lever relations), G4-C and cross-level work are out of scope.",
            "A receipt-bound human frame review is required for semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 ft09 guided checkpoint v2\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 ft09 guided v2 exact-model checkpoint: {WORLDS[0]} only, one pass, {MAX_ACTIONS} actions "
        f"and {MAX_RUNTIME_SECONDS} seconds of behavior time after model setup. Source "
        f"{SOURCE_COMMIT[:7]} ({REVISIONS}). Human review required.\n"
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
        "schema": "virelai-g4-ft09-guided-execution-receipt-v1",
        "revisions": REVISIONS,
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

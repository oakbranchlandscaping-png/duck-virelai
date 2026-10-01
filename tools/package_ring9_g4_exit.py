#!/usr/bin/env python3
"""Freeze the G4 CLICK exit run: ring9-g4-exit-v1, ft09 then vc33 (R9-R06 to R9-R14).

Author: Claude (Alpha build seat), 2026-09-30. BUILD_PLAN_G4_CLICK_COMPLETION_v11 (the exit ruling:
a supported LeverReactionLaw set on both ft09 and vc33, level 1).

Derived from the frozen, committed `ring9-g4b-ft09-v1` package (`08d9afc`): the same model and the
same per-world budget. The world allowlist gains vc33, run after ft09 at concurrency 1; the notebook's
behaviour window is the per-world allowance times the number of worlds, so neither world can starve
the other. What the source adds over ring9-g4b-ft09-v1:
  R9-R13  G4-C: Duck freezes one new prediction drawn from its description (untested action and
          board); SUPPORTED certifies the LeverReactionLawSet, CONTRADICTED reopens G4-B.
  R9-R14  the live G4-B fixes: a refusal puts its reason first; the observed step follows every
          transition.
vc33 has not run on the memory stack before; ft09 has passed through G4-B live twice.

Source provenance: exported with `git archive SOURCE_COMMIT` by the Director, supplied as
`VIRELAI_SOURCE_EXPORT` with a `.source-commit` stamp; never the working tree. The secret guard
refuses any `.env*` (other than `.env.example`) or key-shaped token anywhere in the package.
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
BASE = ROOT / "kaggle" / "ring9-g4b-ft09-v1"
BASE_PACKAGE_SHA256 = "016598b7590bc5a7864d01e32de4e522f4f314e546f266c6f0695146db645185"
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", "ring9-g4-exit-v1")
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-exit-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-g4-exit-v1"
PACKAGE_NAME = "ring9-g4-exit-v1"
KERNEL_TITLE = "taaf-virelai-ring9-g4-exit-v1"
OLD_PACKAGE_NAME = "ring9-g4b-ft09-v1"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4b-ft09-v1"
OLD_KERNEL_TITLE = "taaf-virelai-ring9-g4b-ft09-v1"
BASE_WORLDS = ["ft09-0d8bbf25"]
WORLDS = ["ft09-0d8bbf25", "vc33-5430563c"]  # sequential, ft09 first
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 200
MAX_RUNTIME_SECONDS = 10800
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = os.environ.get("VIRELAI_SOURCE_COMMIT", "d2bf323eaf2fe08a0b64b058e1b958417f344fd1")
REVISIONS = "R9-R06 to R9-R14"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} ({REVISIONS}: Virelai memory, G4-B, G4-C, the clean stop and the "
    "live G4-B fixes).\n"
    "Cloud Python 3.12, full suite: 486 passed, 1 skipped. Director-run Mac pytest at the same "
    "commit, full suite with the bundled framework on PYTHONPATH: 487 passed.\n"
    "Offline ft09 (tests/test_g4b_relations.py, production ToolAgent, a card-only Duck) on the world "
    "the live memory-v1 record defines: the controller repeats the 108 live actions; G4-B 8 SUPPORTED "
    "predictions and a description; G4-C one new SUPPORTED prediction; LeverReactionLawSet COMPLETE; "
    "planned stop. tests/test_g4c_law.py: a contradicted G4-C prediction reopens G4-B and the level "
    "closes on a new test. vc33 has no offline world model on this stack; its first live run is here.\n"
)
PREFLIGHT_PROMPT_BODY_CHARS = 4_000
PREFLIGHT_TOOL_OUTPUT_CHARS = 2 * 4 * TOOL_OUTPUT_TOKENS
PREFLIGHT_OUTPUT_RESERVE_TOKENS = 16_384

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
    "Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them "
    "ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, "
    "gate answers, probe envelopes, annotations), not from prose."
)
LIVE_CRITERIA = [
    "Each criterion below is graded per world (ft09, then vc33) unless it says otherwise.",
    "M5-1 (axiom A6): no binding card exceeds the 16,200-character slot budget, and the 24,000 guard "
    "never fires. M5-2: G0 through G4.1 close with zero model calls; Duck's first turn is the "
    "orientation, accepted within 2 turns (F1 fixed).",
    "G2 (A1): a counter model and mask with a SUPPORTED frozen prediction, purity and trigger "
    "admissibility recomputed from artifacts, or COUNTER_NOT_OBSERVED after every ranked object. "
    "Record whether the trigger class was OPEN (then the label is Duck's; deviation 1). "
    "G3: at least two levers witnessed, none UNRESOLVED_ATTRIBUTION, no re-click of a G2 total null.",
    "A (G4-A): every lever ends CONFIRMED or DIVERGED with an accepted explanation (or interrupted), "
    "the LeverOrbitSet COMPLETE or CLOSED_BY_LEVEL_BOUNDARY; same-level deaths re-study (D4); audit "
    "fidelity and scoped explanations as before.",
    "B (G4-B): every G4-B action is exactly a frozen prediction's, taken by the CONTROLLER, graded on a "
    "later transition with a current freeze stamp (F2 fixed); grades re-derive from the masked frames; "
    "every lever pressed in a graded prediction; the description accepted, each relation citing only "
    "SUPPORTED predictions that pressed or named its levers; open_conditions equal the recorded "
    "missing conditions.",
    "C (G4-C): each law prediction is untested (no graded prediction took its action from its masked "
    "board), names valid relations, is taken by the CONTROLLER and graded; a CONTRADICTED one reopens "
    "G4-B and stays on the record; the gate closes on a SUPPORTED one with the LeverReactionLawSet "
    "COMPLETE, or on a level change.",
    "E (R9-I02): each world ends with solver_note 'planned_stop:', not crashed, with no model request "
    "after its last gate closed.",
    "EXIT (both worlds; BUILD_PLAN v11): the CLICK branch of G4 closes if and only if both ft09 and vc33 "
    "end level 1's G4 with a LeverReactionLawSet of status COMPLETE.",
    "N-1 (axiom A2): no gate idles without a legal move.",
    "R (reported, not graded): each world's description verbatim and its law test; every prediction; "
    "reopenings of G4-B; relation tests beyond single-lever runs; Duck turns, requests and minutes per "
    "gate; deaths and re-studies; bar remaining; largest card per gate; vc33's lever count, lever "
    "classes and counter trigger class.",
]
INFRA_CRITERIA = [
    "I1: G0 assigns CLICK/God Mode from metadata, and the controller executor is on (probe "
    "envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).",
    "I2: the downloaded execution receipt is byte-identical to the package receipt.",
    "I3: the run writes the memory artifacts: turn ledger, gate answers with executor, and "
    "annotations if Duck oriented.",
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
    framework = src / "ARC3-Inference" / "inference" / "framework"
    memory_markers = {  # R9-R06 to R9-R12: every stage must be in the package
        framework / "card_builder.py": "CARD_BUDGET",
        framework / "memory_store.py": "PULL_CHARS",
        framework / "g3_inheritance.py": "G2NullInheritance",
        framework / "controller_executor.py": "_orbit_step",
        framework / "annotation_lane.py": "SUBMIT_ORIENTATION",
        framework / "recall.py": "recall_slot",
        framework / "g4_guided.py": "restudy_next_life",
        framework / "solver.py": "controller_executor_enabled",
        src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py": "request_rerun",
        src / "ARC3-Inference" / "inference" / "agent" / "tool_agent.py": "If next_operation is SUBMIT_ORIENTATION",
        framework / "g4b_gate.py": "LeverRelationsTarget",  # R9-R12
        framework / "g4_relations.py": "validate_relations_answer",
        framework / "controller_executor.py": "def ladder_end",
        framework / "solver.py": "_turn_ends_game",
        src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py": "_planned_stop",
        framework / "g4_orbits.py": "def string_list",
        framework / "record_replay.py": "_replay_reset",
        framework / "g4c_gate.py": "LeverLawTarget",  # R9-R13
        src / "ARC3-Inference" / "inference" / "agent" / "memory_queries.py": "_refused_state",  # R9-R14
        framework / "virelai_gates.py": "_high_step",
    }
    for path, marker in memory_markers.items():
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry {marker} in {path.name}.")


PREFLIGHT_SCRIPT = """
import json, sys
from pathlib import Path
from inference.agent.tool_agent import ToolAgent
from inference.framework.card_builder import CARD_BUDGET, worst_case_request_chars
agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                  controller_executor_enabled=True)
tools = len(json.dumps(agent._tools(Path("unused_tool_runtime_state.json"))))
body, outputs, reserve = (int(x) for x in sys.argv[1:4])
chars = worst_case_request_chars(system_prompt_chars=len(agent._system_prompt), tool_schema_chars=tools,
                                 prompt_body_chars=body, tool_output_chars=outputs,
                                 output_reserve_chars=3 * reserve)
print(json.dumps({"system_prompt_chars": len(agent._system_prompt), "tool_schema_chars": tools,
                  "card_budget_chars": CARD_BUDGET, "worst_case_request_chars": chars,
                  "worst_case_tokens_at_3_chars": chars // 3}))
"""


def _request_preflight(bundle: Path) -> dict[str, Any]:
    """T10: the largest request a turn can make, from the packaged source, fits the window."""
    src = bundle / "src"
    env = {
        **os.environ, "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([str(src / "ARC3-Inference"), str(src / "tufa-arc-agi-framework" / "src")]),
    }
    with tempfile.TemporaryDirectory() as scratch:
        output = subprocess.run(
            [sys.executable, "-c", PREFLIGHT_SCRIPT, str(PREFLIGHT_PROMPT_BODY_CHARS),
             str(PREFLIGHT_TOOL_OUTPUT_CHARS), str(PREFLIGHT_OUTPUT_RESERVE_TOKENS)],
            check=True, capture_output=True, text=True, env=env, cwd=scratch,
        ).stdout
    result = json.loads(output.strip().splitlines()[-1])
    result.update(context_window_tokens=CONTEXT_WINDOW, output_reserve_tokens=PREFLIGHT_OUTPUT_RESERVE_TOKENS)
    if result["worst_case_tokens_at_3_chars"] >= CONTEXT_WINDOW:
        raise RuntimeError(f"Request preflight refused the package: {result}")
    if list(src.rglob("__pycache__")):
        raise RuntimeError("Request preflight left bytecode in the packaged source.")
    return result


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
    # The base package already refuses to start with the controller executor off; keep exactly one.
    if run_source.count('print("taaf.kaggle: controller executor on", flush=True)') != 1:
        raise RuntimeError("Base notebook lost its controller-executor check.")
    # Worlds run one after another: the behaviour window is the per-world allowance times the worlds.
    run_source = _replace_once(
        run_source, f"timedelta(seconds={MAX_RUNTIME_SECONDS})",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS * len(WORLDS)})", "behaviour window",
    )
    notebook["cells"][14]["source"] = run_source.splitlines(True)

    notebook["cells"][0]["source"] = [
        "# Ring 9 G4 CLICK exit, ft09 and vc33 (R9-R06 to R9-R14)\n",
        "Private two-world diagnostic, run one world after the other: the controller executes every "
        "computable step through G4-A; Duck freezes every G4-B and G4-C prediction, describes each "
        "world's lever set, and tests the description on an untested board. The exit is a supported "
        "LeverReactionLaw set on both worlds. Each world stops cleanly where the ladder ends.\n",
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
                "".join(cell["source"]), "<ring9-g4-exit-v1-notebook>", "exec",
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
    if [game.env_name for game in benchmark.games] != BASE_WORLDS:
        raise RuntimeError("The base benchmark does not name exactly the base world.")
    # The notebook rebuilds the game list from the checkpoint allowlist (WORLDS) at run time.
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
    preflight = _request_preflight(bundle)
    (OUT / "RUN.md").write_text(
        "# Ring 9 G4 CLICK exit, ft09 and vc33\n\n"
        f"Source commit `{SOURCE_COMMIT}` ({REVISIONS}). This private diagnostic runs the gated agent "
        f"on {', '.join(f'`{world}`' for world in WORLDS)}, one after the other, one pass each, with at "
        f"most {MAX_ACTIONS} environment actions and {MAX_RUNTIME_SECONDS} seconds of behaviour time per "
        f"world ({MAX_RUNTIME_SECONDS * len(WORLDS)} s for the run) after model setup. Same model and "
        "per-world budget as `ring9-g4b-ft09-v1`.\n\n"
        "The question (the G4 CLICK exit, BUILD_PLAN v11): does each world end level 1's G4 with a "
        "supported LeverReactionLaw set: every lever studied alone, relations tested by graded "
        "predictions, and a description that predicts one untested case?\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Baselines for behaviour only: ft09 passed G0 to G4-B live twice (`ring9-memory-ft09-v1`, "
        "`ring9-g4b-ft09-v1`), with identical controller actions both times. vc33 reached G3 and G4.1 "
        "on earlier stacks (`ring9-g3-vc33-closure-v1` to `v3`) and has not run on the memory stack.\n\n"
        f"Request preflight (T10): worst case {preflight['worst_case_tokens_at_3_chars']} tokens "
        f"against a {CONTEXT_WINDOW}-token window, for one request.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the "
        "benchmark starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 G4 exit v1"
    _write_json(bundle / "dataset-metadata.json", dataset_metadata)

    kernel_metadata = json.loads((OUT / "kernel" / "kernel-metadata.json").read_text())
    if kernel_metadata["dataset_sources"][0] != OLD_DATASET_ID:
        raise RuntimeError("Base kernel metadata does not lead with the G4 source dataset.")
    kernel_metadata["id"] = KERNEL_ID
    if kernel_metadata.get("title") != OLD_KERNEL_TITLE:
        raise RuntimeError("Base kernel metadata title is not the committed ft09 kernel.")
    kernel_metadata["title"] = KERNEL_TITLE
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
        "stage": "G4-CLICK-EXIT-V1",
        "claim": (
            "Evaluates the G4 CLICK exit (BUILD_PLAN v11) live on ft09 and vc33, one after the other: "
            "Virelai memory through G4-A, G4-B relations from Duck-frozen predictions the controller "
            "takes and the gate grades, and G4-C's untested law prediction certifying a "
            "LeverReactionLaw set (a contradiction reopens G4-B); each world stops cleanly."
        ),
        "controller_executor": True,
        "request_preflight": preflight,
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
            "G4-C and the R9-R14 fixes are proven offline only; vc33 has no offline world on this stack.",
            "Duck's predictions, descriptions and law tests are the object of study.",
            "The gates require coverage and supported citations; they cannot require that Duck's tests are interesting.",
            "Cross-level work (G9) and scoring are out of scope; closing G4 does not score.",
            "A receipt-bound human frame review is required for semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 G4 CLICK exit v1\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 G4 CLICK exit v1 exact-model checkpoint: {', '.join(WORLDS)}, one pass each, {MAX_ACTIONS} "
        f"actions and {MAX_RUNTIME_SECONDS} seconds of behavior time per world after model setup. Source "
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
        "controller_executor": True,
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

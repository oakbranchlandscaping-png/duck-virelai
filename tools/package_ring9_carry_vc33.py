#!/usr/bin/env python3
"""Freeze the first live cross-level run: ring9-carry-vc33-v1, vc33 alone (R9-R06 to R9-R18).

Author: Claude (Alpha build seat), 2026-10-01. Director rulings 2026-10-01: life record first;
carry hypotheses only (G0-G2 run again on each level); "learn how to win" is recorded only;
tools/live_level_carry_gate.py (a hard-coded winning click list for one world) is left out of the
shipped source.

Derived from the frozen, committed `ring9-g4-exit-v1` package (`10b1310`): the same model and the
same per-world budget. The world allowlist is vc33 alone: it is the world that leaves level 1. What
the source adds over ring9-g4-exit-v1:
  R9-R15  replay fidelity; controller actions labelled CONTROLLER.
  R9-R16  the life record: every transition carries its life and level; a reset is a recorded row;
          a test cut off by a death or level change is INDETERMINATE; declared persistence tiers.
  R9-R17  the level freeze: a finished level's model is frozen and the ladder restarts at G0 on the
          next level's board instead of ending the run.
  R9-R18  G9-A: the frozen level's levers carried as type-matched predictions the next level grades.

Source provenance: exported with `git archive SOURCE_COMMIT` by the Director, supplied as
`VIRELAI_SOURCE_EXPORT` with a `.source-commit` stamp; never the working tree. The secret guard
refuses any `.env*` (other than `.env.example`) or key-shaped token anywhere in the package. The
world-content guard refuses the excluded tool and any world name in the solver's executable code
other than the harness's public game roster.
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
BASE = ROOT / "kaggle" / "ring9-g4-exit-v1"
BASE_PACKAGE_SHA256 = "80fac5e2ab427385ce39f15b9f48d849530dc5539dfecc8076cc2cd2e2e32b38"
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", "ring9-carry-vc33-v1")
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-carry-vc33-v1"
PACKAGE_NAME = "ring9-carry-vc33-v1"
KERNEL_TITLE = "taaf-virelai-ring9-carry-vc33-v1"
OLD_PACKAGE_NAME = "ring9-g4-exit-v1"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-exit-v1"
OLD_KERNEL_TITLE = "taaf-virelai-ring9-g4-exit-v1"
BASE_WORLDS = ["ft09-0d8bbf25"]  # the base benchmark pickle; the notebook builds games from WORLDS
BASE_WINDOW_SECONDS = 21600  # the base notebook's two-world behaviour window
WORLDS = ["vc33-5430563c"]
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 200
MAX_RUNTIME_SECONDS = 10800
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = os.environ.get("VIRELAI_SOURCE_COMMIT", "fbbc7f4a9f1decc669d2aa599dc37903a4431e90")
REVISIONS = "R9-R06 to R9-R18"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} ({REVISIONS}: Virelai memory, G4-B, G4-C, the clean stop, the live "
    "G4-B fixes, replay fidelity, the life record, the level freeze and G9-A carry).\n"
    "Cloud Python 3.12, full suite: 509 passed, 1 skipped. Director-run Mac pytest at the same "
    "commit, full suite with the bundled framework on PYTHONPATH: 510 passed.\n"
    "Offline vc33 (the live ring9-g4-exit-v1 record, tests/test_r9_r17_level_freeze.py and "
    "tests/test_r9_r18_carry.py): level 1 freezes at transition 26 with E0004 explained (ABSORBING), "
    "E0005 interrupted, and the win recorded (the same click failed 7 times before: UNTESTED); the "
    "ladder restarts at G0 on level 2's spawn board; 4 same-type carry candidates are frozen before "
    "any click. On a stand-in level 2 (the real one has never been played) the controller certifies "
    "G0-G2, G3's sweep grades the candidates (2 RECONFIRMED, 2 FALSIFIED) and certifies the 2 "
    "responsive objects on its own evidence, and the ladder reaches G4-A.\n"
)
PREFLIGHT_PROMPT_BODY_CHARS = 4_000
PREFLIGHT_TOOL_OUTPUT_CHARS = 2 * 4 * TOOL_OUTPUT_TOKENS
PREFLIGHT_OUTPUT_RESERVE_TOKENS = 16_384

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", ".DS_Store", "__pycache__", ".pytest_cache", ".ruff_cache",
    "*.pyc", "arc3_inference.egg-info", "offline-gates", "tests", "variants", "runs",
    "live_level_carry_gate.py",  # a hard-coded winning click list for one world (ruling 2026-10-01)
)
WORLD_NAME = re.compile(r"\b(?:[a-z][a-z0-9]{3}-[0-9a-f]{8}|ft09|vc33|ls20)\b")
WORLD_ROSTER_FILE = "inference/framework/kaggle.py"  # the harness's public game roster: infrastructure
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
    "One world, vc33. Level-1 criteria repeat the exit run's; the new criteria are X (cross-level) and L "
    "(lives).",
    "M5-1 (axiom A6): no binding card exceeds the 16,200-character slot budget, and the 24,000 guard "
    "never fires. M5-2: G0 through G4.1 close with zero model calls on each level; Duck's first turn on "
    "each level is the orientation, accepted within 2 turns.",
    "G2/G3 (level 1): as in ring9-g4-exit-v1 (counter EVERY_TRANSITION, 2 levers witnessed). On level 2: "
    "a counter model and mask certified again (ruling: G0-G2 run again), and G3's levers witnessed on "
    "level 2's own evidence.",
    "A (G4-A): every lever ends CONFIRMED or DIVERGED with an accepted explanation, or interrupted; the "
    "LeverOrbitSet COMPLETE or CLOSED_BY_LEVEL_BOUNDARY.",
    "X-1 (level freeze, R9-R17): if level 1 ends, LevelModel(1) is frozen at that transition from the "
    "gate machine's own record, with its products, lever roster and, if won, the win record (action, "
    "acted lever, earlier same-action failures, hypothesis UNTESTED). The run does not stop: the "
    "ladder restarts at G0 on level 2, and every later row is tagged level 2.",
    "X-2 (carry, R9-R18): at level-2 entry, every carry candidate is frozen (declared_at_transition = "
    "the entry transition) before any level-2 click; each is graded only by a level-2 click after "
    "level 2's counter mask is certified, never on a terminal transition; RECONFIRMED means a masked "
    "change with the carried locality. Grades re-derive from the frames. Reported: candidates, "
    "RECONFIRMED, FALSIFIED, UNCONFIRMED (never clicked), not found.",
    "X-3 (no verdict carried): no level-2 product exists before level 2's own gate certifies it; G3 "
    "certifies level-2 levers on level-2 evidence, whatever the carry says.",
    "L-1 (life record, R9-R16): every death is a RESET row that opens the next life; a G4-B or G4-C "
    "prediction taken on a transition that ends a life or a level is INDETERMINATE, not graded.",
    "B/C (G4-B, G4-C), if reached on any level: as in ring9-g4-exit-v1.",
    "E: the run ends with solver_note 'planned_stop:' (ladder through G4-C, or a level change with no "
    "lossless board), or by the action or time budget; never crashed. No model request after a planned "
    "stop.",
    "N-1 (axiom A2): no gate idles without a legal move.",
    "R (reported, not graded): actions and Duck time per level; level-2 lever count, classes and types "
    "versus level 1; the carry line Duck saw; whether a second level was won and by whom (controller or "
    "Duck); the level-1 win record verbatim. A level won by the G4-A study is the study's, not the "
    "model's: the review must not credit it to the model.",
]
INFRA_CRITERIA = [
    "I0: the shipped source holds no tools/live_level_carry_gate.py and no world name in the solver's "
    "executable code other than the harness's public game roster (packager guard).",
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
        framework / "record_replay.py": "_submit_ready_answers",  # R9-R15, R9-R17
        src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py": '"actor": CONTROLLER',
        framework / "life_record.py": "class LifeRecord",  # R9-R16
        framework / "level_model.py": "def freeze_level",  # R9-R17
        framework / "virelai_gates.py": "def _advance_level",
        framework / "carry.py": "class CarryLedger",  # R9-R18
    }
    for path, marker in memory_markers.items():
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry {marker} in {path.name}.")
    _world_content_guard(src / "ARC3-Inference")


def _world_content_guard(app: Path) -> None:
    """The excluded tool is absent, and the solver's executable code names no world (I0).

    Docstrings and comments are prose about past runs and are not scanned; every string constant and
    identifier is. The harness's public game roster (``kaggle.py``) is infrastructure and allowed.
    """
    if list(app.rglob("live_level_carry_gate.py")):
        raise RuntimeError("The shipped source carries tools/live_level_carry_gate.py.")
    found: list[str] = []
    for path in sorted((app / "inference").rglob("*.py")):
        if str(path.relative_to(app)) == WORLD_ROSTER_FILE:
            continue
        tree = ast.parse(path.read_text())
        docs = {
            id(node.body[0].value) for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
        }
        for node in ast.walk(tree):
            text = node.value if isinstance(node, ast.Constant) and id(node) not in docs else getattr(node, "id", None)
            if isinstance(text, str) and WORLD_NAME.search(text):
                found.append(f"{path.relative_to(app)}:{node.lineno}")
    if found:
        raise RuntimeError("World names in the solver's executable code: " + ", ".join(found[:10]))


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
        "behavior deadline": f"timedelta(seconds={BASE_WINDOW_SECONDS})",
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
        run_source, f"timedelta(seconds={BASE_WINDOW_SECONDS})",
        f"timedelta(seconds={MAX_RUNTIME_SECONDS * len(WORLDS)})", "behaviour window",
    )
    notebook["cells"][14]["source"] = run_source.splitlines(True)

    notebook["cells"][0]["source"] = [
        "# Ring 9 cross-level, vc33 (R9-R06 to R9-R18)\n",
        "Private one-world diagnostic: the first live run of the life record, the level freeze and "
        "G9-A carry. When a level ends, its model is frozen and the ladder restarts on the next level, "
        "where the previous level's levers are carried as predictions that level's own probes grade.\n",
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
                "".join(cell["source"]), "<ring9-carry-vc33-v1-notebook>", "exec",
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
        "# Ring 9 cross-level, vc33\n\n"
        f"Source commit `{SOURCE_COMMIT}` ({REVISIONS}). This private diagnostic runs the gated agent "
        f"on {', '.join(f'`{world}`' for world in WORLDS)}, one pass, with at most {MAX_ACTIONS} "
        f"environment actions and {MAX_RUNTIME_SECONDS} seconds of behaviour time after model setup. "
        "Same model and per-world budget as `ring9-g4-exit-v1`.\n\n"
        "The question: when a level ends, does the machine freeze what it established, restart its "
        "ladder on the next level's board, and test what it carried there, without carrying any "
        "verdict? In `ring9-g4-exit-v1`, vc33's G4-A study completed level 1 at transition 26 and the "
        "run stopped (cross-level work was not built).\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Baseline for behaviour only: `ring9-g4-exit-v1` vc33 (26 actions, level 1 won by the G4-A "
        "study of E0005, 7 earlier same-click failures). The controller is deterministic until Duck "
        "acts on its own turn, so level 1 should repeat that run unless Duck intervenes.\n\n"
        f"Request preflight (T10): worst case {preflight['worst_case_tokens_at_3_chars']} tokens "
        f"against a {CONTEXT_WINDOW}-token window, for one request.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the "
        "benchmark starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 carry vc33 v1"
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
        "stage": "G9A-CARRY-VC33-V1",
        "claim": (
            "Evaluates the life record, the level freeze and G9-A carry live on vc33: a finished "
            "level's model is frozen from the gate machine's own record, the ladder restarts at G0 on "
            "the next level's board, and the frozen level's levers are carried as type-matched "
            "predictions the next level's own probes grade; nothing carried is a verdict."
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
            "Level 2 of vc33 has never been played: the level freeze and the carry are proven offline on the live level-1 record and a stand-in level 2 only.",
            "Duck's predictions, descriptions and law tests are the object of study.",
            "The gates require coverage and supported citations; they cannot require that Duck's tests are interesting.",
            "G9-B (carried relations as Duck predictions) is not built; a level won by the G4-A study is the study's, not the model's; scoring is out of scope.",
            "A receipt-bound human frame review is required for semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 carry vc33 v1\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 carry vc33 v1 exact-model checkpoint: {', '.join(WORLDS)}, one pass, {MAX_ACTIONS} "
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

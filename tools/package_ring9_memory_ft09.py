#!/usr/bin/env python3
"""Freeze the first live test of Virelai memory: ring9-memory-ft09-v1 (R9-R06 to R9-R11).

Author: Claude (Alpha build seat), 2026-09-29. Stage M-5 of DESIGN_VIRELAI_MEMORY_v2_2026-09-29.

Derived from the frozen, committed `ring9-g4-ft09-guided-v2` package (`ceab138`): the same world,
model and budget, so the only thing that changes between the two live runs is the source. This
transform renames the package, restates the claim and the preregistered criteria (DESIGN §12), runs
the request preflight (T10) against the packaged source, and re-vendors source from the committed
export at SOURCE_COMMIT.

What the source adds over guided v2 (REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md):
  R9-R06  instruments: replay harness, record index, memory store, turn ledger
  R9-R07  the slot-built card (the card that overflowed v2 at 25,502 characters is ~4,700)
  R9-R08  the controller executor: G0-G3 without model calls; G3 inherits G2's total nulls (D5)
  R9-R09  the orientation turn, the UNCERTIFIED lane (D6), injected recall, one pull interface
  R9-R10  the controller certifies G4.1 and runs G4-A levers, Duck explains (D3); lives (D4);
          counter, action and time budget wakes
  R9-R11  Duck is told, every turn, how to take an orientation or handoff step
Offline reference (not a graded prediction): G4-A satisfied in 92 actions with 7 Duck turns.

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
BASE = ROOT / "kaggle" / "ring9-g4-ft09-guided-v2"
BASE_PACKAGE_SHA256 = "d4047476837f5f2c55f0d519397ded699f99373dd0b5d3780d523be2d719a476"
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", "ring9-memory-ft09-v1")
DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-memory-ft09-v1"
KERNEL_ID = "stephenkaskin/taaf-virelai-ring9-memory-ft09-v1"
PACKAGE_NAME = "ring9-memory-ft09-v1"
KERNEL_TITLE = "taaf-virelai-ring9-memory-ft09-v1"
OLD_PACKAGE_NAME = "ring9-g4-ft09-guided-v2"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v2"
OLD_KERNEL_TITLE = "taaf-virelai-ring9-g4-ft09-guided-v2"
WORLDS = ["ft09-0d8bbf25"]
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = 200
MAX_RUNTIME_SECONDS = 10800
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = 1
PASSES = 1
SOURCE_COMMIT = os.environ.get("VIRELAI_SOURCE_COMMIT", "8ca9fc94e012839db7bbe1ffe10733a75277a882")
REVISIONS = "R9-R06 to R9-R11"
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} ({REVISIONS}: Virelai memory stages M-0 to M-4 and the "
    "live-readiness prompt line).\n"
    "Cloud Python 3.12, full suite: 469 passed, 1 skipped (a recorded ft09 artifact outside the "
    "source package). Director-run Mac pytest at the same commit, full suite with the bundled "
    "framework on PYTHONPATH: 470 passed.\n"
    "Offline ft09 (tests/test_memory_m4.py, production ToolAgent, a card-only Duck): the v2 record's "
    "initial grid and recorded law, continued by hypothesis for tiles the live run never reached, "
    "reaches G4-A SATISFIED in 92 actions with 7 Duck turns (orientation, 5 orbit explanations, one "
    "counter-budget wake); G0-G3 take 72 actions and 0 model calls; the largest card is under 8,000 "
    "characters against the 16,200 slot budget.\n"
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
    "M5-1 (axiom A6, memory M-1): no binding card exceeds the 16,200-character slot budget at any "
    "turn (turn ledger card_chars), and the runtime's 24,000-character guard never fires.",
    "M5-2 (memory M8, rulings D2 and D3): G0 through G4.1 close with zero model calls: every turn "
    "ledger row before Duck's first is executor CONTROLLER with no model request, and Duck's first "
    "turn is the orientation turn.",
    "G2-1 (axiom A1): G2 closes with a counter model and mask after one frozen footprint-scoped "
    "prediction is SUPPORTED, or as COUNTER_NOT_OBSERVED after every ranked object was clicked. "
    "Record which, and whether the label was the controller's (an OPEN or IRREGULAR record hands "
    "it to Duck).",
    "G2-2 (purity, recomputed from artifacts): every recorded change inside the mask footprint "
    "follows the counter rewrite or its inverse, and at least one witness acted away from the "
    "footprint.",
    "G2-3 (A1 v2, recomputed from artifacts): the accepted trigger is admissible for the trigger "
    "class computed from the whole G2 record.",
    "G3-1 (ruling D5; prediction from the v2 record): G3 closes with at least two ft09 control "
    "tiles witnessed as levers, none filed UNRESOLVED_ATTRIBUTION, and G3 re-clicks no object G2 saw "
    "as a total null.",
    "G4-1 (the G4.1 split): every G3 lever has a G4.1 anatomy answer, each by the controller.",
    "A-1 (G4-A): every lever ends with a CONFIRMED or DIVERGED run and an accepted explanation, or is "
    "recorded as interrupted; the final LeverOrbitSet is COMPLETE or CLOSED_BY_LEVEL_BOUNDARY with "
    "nothing pending, and no prior lever's run or class is invalidated.",
    "A-2 (audit fidelity, recomputed from gate events): each accepted run is a consecutive "
    "same-click press sequence whose stop and confirmation dispositions match the masked states; "
    "every press carries its executor; broken runs are recorded, never counted.",
    "A-3: Duck's accepted orbit explanations distinguish the observed finite run from a universal "
    "or unconditional law.",
    "L-1 (ruling D4; the open ft09 question): report whether the counter bar reaching zero ends the "
    "life (a GAME_OVER boundary on that transition). If any death interrupts a lever study on the "
    "same level, that lever is re-studied (life_restudies) and the study still ends COMPLETE or "
    "CLOSED_BY_LEVEL_BOUNDARY.",
    "N-1 (axiom A2): no gate idles without a legal move; a declared end is reported with its idle "
    "time, not failed.",
    "R (reported, not graded): Duck turns and model requests per gate; minutes to G3 closure and to "
    "G4-A; actions per gate; every stop-and-wake reason; bar cells remaining at the end; the largest "
    "card per gate; Duck's orientation notes; any extra-run request.",
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
    memory_markers = {  # R9-R06 to R9-R11: every memory stage must be in the package
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
    # The executor is the object of this run: refuse to start if the environment turned it off.
    marker = 'print("taaf.kaggle: G0-G4 execution receipt verified", flush=True)'
    run_source = _replace_once(run_source, marker, marker + (
        '\nif os.environ.get("VIRELAI_CONTROLLER_EXECUTOR", "1").strip() == "0":\n'
        '    raise RuntimeError("This checkpoint requires the controller executor; it is disabled.")\n'
        'print("taaf.kaggle: controller executor on", flush=True)'
    ), "receipt success print")
    notebook["cells"][14]["source"] = run_source.splitlines(True)

    notebook["cells"][0]["source"] = [
        "# Ring 9 memory, ft09 v1: the first live test of Virelai memory (R9-R06 to R9-R11)\n",
        "Private one-world diagnostic: the controller executes every computable step from G0 to the "
        "G4-A lever runs; Duck orients once, explains each confirmed lever orbit, and is woken by "
        "every stop condition. Cards are slot-built and bounded; recall is injected and pulled.\n",
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
                "".join(cell["source"]), "<ring9-memory-ft09-v1-notebook>", "exec",
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
    preflight = _request_preflight(bundle)
    (OUT / "RUN.md").write_text(
        "# Ring 9 memory, ft09 v1\n\n"
        f"Source commit `{SOURCE_COMMIT}` ({REVISIONS}). This private diagnostic runs the gated agent "
        f"on `{WORLDS[0]}` for one pass, with at most {MAX_ACTIONS} environment actions and "
        f"{MAX_RUNTIME_SECONDS} seconds of behavior time after model setup. Same world, model and "
        "budget as `ring9-g4-ft09-guided-v2`: only the source changed.\n\n"
        "The question: with Virelai memory (a bounded slot-built card, the controller executor, "
        "recall, the orientation turn, the G4 economy and the lives rule), does ft09 reach G4-A with "
        "Duck spending its turns only on judgment, and every card within budget?\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        "Baseline for comparison of behavior only (not scores): `ring9-g4-ft09-guided-v2`: G2 closed "
        "live; G3 confirmed five levers; the run crashed on a 25,502-character card at the fifth "
        "dossier, after 121 actions and about 130 Duck turns. Offline reference, not a graded "
        "prediction: G4-A SATISFIED in 92 actions with 7 Duck turns, on the v2 record's law "
        "continued by hypothesis.\n\n"
        f"Request preflight (T10): worst case {preflight['worst_case_tokens_at_3_chars']} tokens "
        f"against a {CONTEXT_WINDOW}-token window.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n\n"
        "The notebook verifies the mounted source manifest and execution receipt before the "
        "benchmark starts. This is not a score comparison or competition submission.\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = "Virelai Ring 9 memory ft09 v1"
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
        "stage": "MEMORY-M5-FT09-V1",
        "claim": (
            "Evaluates Virelai memory (R9-R06 to R9-R11) live on ft09: the slot-built card, the "
            "controller executor from G0 through the G4-A lever runs, G3's inherited G2 nulls, the "
            "orientation turn and UNCERTIFIED lane, injected and pulled recall, the lives rule, and "
            "the counter, action and time budget wakes, with the axiom-A2 watchdog armed."
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
            "Every memory stage is proven offline only; ft09's behaviour beyond the tiles the v2 run reached is a hypothesis.",
            "Duck's turns (orientation, explanations, the steps it is woken for) are the object of study; offline, a card-only policy stood in for Duck.",
            "Whether an empty counter bar ends the life on ft09 is unknown; criterion L-1 records it.",
            "G4-B (lever relations), G4-C and cross-level work are out of scope.",
            "A receipt-bound human frame review is required for semantic correctness.",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        "# Ring 9 memory, ft09 v1\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 memory ft09 v1 exact-model checkpoint: {WORLDS[0]} only, one pass, {MAX_ACTIONS} actions "
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

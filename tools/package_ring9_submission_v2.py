#!/usr/bin/env python3
"""Freeze a Ring 9 submission package: the dry run or the scored submission (pinned image).

Author: Claude (Alpha build seat), 2026-10-06. DIRECTIVE_COMPETITION_ENDGAME_v2 D-2 (play every hidden
game inside the run, slice the time, hold a hard guard on the deadline); BUILD_PLAN_PORTS_AND_PILLARS_v1
§1 Track S; BUILD_SLICE_SUB_1_SUBMISSION_MODE.

``VIRELAI_SUBMISSION_MODE`` selects the package:
  ``dryrun``  plays the harness's competition-arcade simulator (``taaf.competition_arcade``: the 110
              official clones of the 25 public games) through the same gateway-shaped code a real
              rerun uses, inside a compressed window. Not scored.
  ``submit``  in a Kaggle competition rerun (``KAGGLE_IS_COMPETITION_RERUN``) plays the live
              competition Arcade at the gateway, with the run's deadline taken from the notebook's own
              start. Run interactively it behaves as the dry run, so a Save & Run before submitting
              exercises the same path.

Everything else is the canary packager (``package_ring9_unified_canary_v1.py``): the frozen base package,
the pinned Python 3.12 image, the Director's own wheelhouse and ``vrfai/Qwen3.6-27B-FP8`` (D-3), the
secret, world-content, request-size and single-tree marker guards. The changes are in the notebook's run
cell: the game list comes from a competition-shaped Arcade, the world allowlist becomes a count and
uniqueness contract, the soft end is computed from the notebook's start, and the session settings are the
submission's (concurrency, per-game slice, action cap).

v2 (Claude, 2026-10-09; Director: "lets do B"): the source carries SUB-3 (a free-play action reports its
outcome to Duck; the sandbox host logs any error it hides), the action cap rises from 400 to 1,000 (an
action on a level that is never cleared costs no score under RHAE), and the per-game slice falls from 2,700 s
to 2,550 s so that 11 waves of 10 games, each overrunning by the observed 45 s, end at least 20 minutes
before the soft end (RULINGS_CONSOLIDATION_v2, noted item; the v1 rehearsal's setup took 843 s).

Source provenance: exported with ``git archive SOURCE_COMMIT`` by the Director, supplied as
``VIRELAI_SOURCE_EXPORT`` with a ``.source-commit`` stamp; never the working tree.
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
RUN_WALL_SECONDS = 9 * 3600  # D-2: the submission notebook's runtime limit (Kaggle fact to confirm)
EXIT_MARGIN_SECONDS = 25 * 60  # the soft end leaves this before the wall for teardown and scoring
MODES = {  # BUILD_SLICE_SUB_1 §3: 10 concurrent games (the server's own figure, DIAG_R5 §1)
    "dryrun": {"package": "ring9-submission-dryrun-v3", "concurrency": 10, "max_actions": 1000,
               "max_runtime_seconds": 600, "dry_run_window_seconds": 2 * 3600, "game_count": 110},
    "submit": {"package": "ring9-submission-v2", "concurrency": 10, "max_actions": 1000,
               "max_runtime_seconds": 2550, "dry_run_window_seconds": 2 * 3600, "game_count": 110},
}
MODE = os.environ.get("VIRELAI_SUBMISSION_MODE", "")
if MODE not in MODES:
    raise SystemExit(f"Set VIRELAI_SUBMISSION_MODE to one of {sorted(MODES)}.")
SPEC = MODES[MODE]
PACKAGE_NAME = SPEC["package"]
OUT = ROOT / "kaggle" / os.environ.get("VIRELAI_PACKAGE_DIR", PACKAGE_NAME)
DATASET_ID = f"stephenkaskin/taaf-duck-virelai-{PACKAGE_NAME}"
KERNEL_ID = f"stephenkaskin/taaf-virelai-{PACKAGE_NAME}"
KERNEL_TITLE = f"taaf-virelai-{PACKAGE_NAME}"
OLD_PACKAGE_NAME = "ring9-g4-exit-v1"
OLD_DATASET_ID = "stephenkaskin/taaf-duck-virelai-ring9-g4-exit-v1"
OLD_KERNEL_TITLE = "taaf-virelai-ring9-g4-exit-v1"
BASE_WORLDS = ["ft09-0d8bbf25"]  # the base benchmark pickle; the notebook builds games from WORLDS
BASE_WINDOW_SECONDS = 21600  # the base notebook's two-world behaviour window
BASE_MAX_ACTIONS, BASE_MAX_RUNTIME_SECONDS = 200, 10800  # the base notebook's per-world budgets
WORLDS: list[str] = []  # submission-shaped: the game list is the competition Arcade's, checked by count
MODEL = "vrfai/Qwen3.6-27B-FP8"
MAX_ACTIONS = SPEC["max_actions"]
MAX_RUNTIME_SECONDS = SPEC["max_runtime_seconds"]
CONTEXT_WINDOW = 65536
TOOL_OUTPUT_TOKENS = 1024
CONCURRENCY = SPEC["concurrency"]
PASSES = 1
SOURCE_COMMIT = os.environ.get("VIRELAI_SOURCE_COMMIT", "")
if not re.fullmatch(r"[0-9a-f]{40}", SOURCE_COMMIT):
    raise SystemExit("Set VIRELAI_SOURCE_COMMIT to the full 40-character commit of the single tree.")
REVISIONS = (
    "Ring 9 single tree: R9-R06 to R9-R24 (click) and N1 to N5.3 (NAV), merged 501a6e6, F1 fa9617b, "
    "step 4' NAV record b04ad10..e8d1f92, SUB-1 d751a5b, NAV cell-site targeting 4970953, SUB-2 a2200c2, SUB-3 (free-play outcome)"
)
TEST_RESULTS = (
    f"Source commit {SOURCE_COMMIT} ({REVISIONS}).\n"
    "Unification (Sol, 501a6e6): a true merge of main 130a374 (NAV line) and r9-r20-level-entry c9b246b "
    "(click line); CLICK G3 records the first witness (Director ruling F2a, 2026-10-05); legacy click records "
    "replay their confirmation path (record_replay.record_protocol).\n"
    "Review (Claude, REVIEW_RING9_UNIFICATION_v1): mechanical re-merge diffed against the merge; no test lost; "
    "click pre-flights byte-identical to c9b246b (tools/check_g4_controller_first_from_record.py on the v7 "
    "record, tools/check_mu_partial_close_from_record.py on the v6 record). F1 (a released NAV target "
    "PRESUMED_UNREACHABLE counted as unbounded, so a completed NAV roster had no legal move): fixed in "
    "fa9617b, 2 fail-first tests (both fail at 501a6e6).\n"
    "At f86d6ef (the merge plus F1): cloud and Director-run Mac pytest, 607 passed, 1 skipped.\n"
    "Step 4' (Sol, b04ad10..e8d1f92): the ls20 N5.1 live record as a replay fixture "
    "(test_ring9_nav_live_replay.py); NAV intervention and attributed residue on record rows; "
    "check_inventory_claims restored with PRESUMED_UNREACHABLE; record_replay replay_from_g0.\n"
    "SUB-1 (Claude, d751a5b): test_s1_concurrent_replay.py (5 live records replayed serially and on a "
    "thread pool, identical game for game; a fail-first shared-cache leak is seen) and "
    "test_s2_run_deadline.py (soft end, per-game slice, action cap, request timeout), 2 + 5 passed.\n"
    "At d751a5b: Director-run Mac pytest 617 passed, 1 skipped; cloud Python 3.12 full suite on the "
    "d751a5b export: 617 passed, 1 skipped (618 collected; run in two parts after a session time limit).\n"
    "NAV cell-site targeting (Sol, 4970953): G1 bearings compiled from recorded cell flow; G3 resolves each "
    "roster identity to its current sites. At c5e8ff6: Director-run Mac pytest 619 passed, 1 skipped.\n"
    "Submission dry run (d751a5b, 110 clones): machinery passed; D-1 ACTION7 unmapped, D-2 controller refusal "
    "spin, D-3 controlled stops ended games (REVIEW_RING9_SUBMISSION_DRYRUN_V1_KAGGLE_2026-10-07).\n"
    "SUB-2 (Claude, a2200c2): ACTION7 mapped; a stalled controller rests the level in play after 3 turns; idle "
    "back-off; in submission mode a controlled stop rests the level in free play once (Director ruling D-3, "
    "2026-10-07). 8 fail-first tests. Cloud full suite 627 passed, 1 skipped; Director-run Mac pytest at the "
    "same source 627 passed, 1 skipped. 419f4fd adds documents only.\n"
    "Submission v1 rehearsal (Kaggle save run of ring9-submission-v1, 2026-10-08): 36 of 110 clones played in "
    "the 2-h window, all 25 worlds once; no crash; D-1, D-2 and D-3 passed; 6 levels cleared. New defect: "
    "every free-play action ran and was recorded but was reported to Duck as 'action failed in sandbox host' "
    "(685 of 685; the play gate's event had no outcome).\n"
    "SUB-3 (Claude, 2026-10-09): the play gate's event carries its compacted outcome; the sandbox host logs the "
    "type, message and raising line of any error it hides. 3 fail-first tests "
    "(test_sub3_free_play_outcome.py) on the real tool path.\n"
)
TEST_RESULTS += (
    "Self-hosted dependencies (v2): tools/kaggle_kit committed 86fa9ed, kit tests 6 passed on the Mac. "
    "Wheelhouse stephenkaskin/virelai-vllm-wheelhouse-v3: 174 PyPI-pinned wheels, every digest verified "
    "at build, Kaggle listing 177 files with every wheel's name and size equal to the lock. Model "
    "stephenkaskin/virelai-qwen3-6-27b-fp8: vrfai/Qwen3.6-27B-FP8 at commit 70462b01, every LFS digest "
    "verified at download; the weights have one version (2026-04-25), so they are the weights every "
    "earlier run loaded. Record: RECORD_SELF_HOSTED_DEPENDENCIES_v1_2026-10-02.md.\n"
)


def _load_dependencies() -> Any:
    import importlib.util

    path = ROOT / "tools" / "kaggle_kit" / "dependencies.py"
    spec = importlib.util.spec_from_file_location("kaggle_kit_dependencies", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


DEPENDENCIES = _load_dependencies()
OLD_DEPS = DEPENDENCIES.THIRD_PARTY_V3  # what ring9-g4-exit-v1 (the base) mounts
DEPS = DEPENDENCIES.SELF_HOSTED_V3
OLD_OWNER = OLD_DEPS.wheelhouse.split("/")[0]
if DEPS.served_model_name != MODEL or OLD_DEPS.served_model_name != MODEL:
    raise RuntimeError("v2 changes where the model comes from, never which model is served.")
ENVIRONMENT = {  # the Kaggle image ring9-carry-vc33-v2 ran on (kaggle kernels pull -m), Python 3.12
    "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    "docker_image_pinning_type": "original",
    "machine_shape": "NvidiaRtxPro6000",
    "python": "3.12 (the wheelhouse's compiled wheels are cp312)",
    "source": "ring9-carry-vc33-v2 kernel metadata, 2026-10-02",
}
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
COMMON_INFRA = [
    "I0: the shipped source holds no tools/live_level_carry_gate.py and no world name in the solver's "
    "executable code other than the harness's public game roster (packager guard).",
    "I2: the downloaded execution receipt is byte-identical to the package receipt.",
    "I3: the run writes the memory artifacts: turn ledger, gate answers with executor, probe envelopes.",
    "I5: the setup log names the wheelhouse and model paths under stephenkaskin's two datasets, pip installs "
    "from the wheelhouse with no index, and vLLM serves vrfai/Qwen3.6-27B-FP8.",
    "I8 (pinned environment): the log shows Python 3.12 paths and the 174-wheel install succeeds.",
    "I11 (axiom A2): no gate idles without a legal move; a state with no probe, no acceptable answer and no "
    "declared end is ended by the watchdog within three checks. Reported: whether the notebook's end "
    "followed the run's end.",
    "U-SRC: setup prints 'source manifest verified' with this package's file count, and the source commit "
    "is the single tree's.",
]
SUBMISSION_CRITERIA = [
    "C-1: the run completes without a crash: every game is started, plays until its own stop "
    "(win, slice, action cap or the run's soft end) and is finished by the harness.",
    "C-2: every game has a gate record, and each game's play is receipted GATED or FREE_PLAY per transition "
    "(gate events); the review tabulates where each game's ladder rested.",
    "C-3: no artifact of one game carries another game's identity or evidence (cross-game mixing check on "
    "the per-game artifact stems).",
    "C-4 (v2 wording; the 2-h rehearsal cannot fit 110 games of 2,550 s): any game still playing at the soft "
    "end is cancelled cleanly with its artifacts written, the benchmark closes within 5 minutes of the soft "
    "end, and the notebook ends within the exit margin.",
    "C-5: with 10 concurrent games, Duck turns still complete inside the 60 s turn budget at a rate the "
    "review reports (turns cut by the clock, per game and overall).",
    "C-6: prompt tokens stay under the 65,536-token window (max reported per turn).",
    "C-7: vc33 clones clear level 1 at least, as v8 did; any other cleared level is reported by game.",
    "R (reported): per game, the gate where the ladder rested, actions, Duck turns and seconds, levels "
    "cleared; overall, the engine score the harness reports.",
    "D-1 to D-3 (from v1): no 'Unknown action'; no more than 3 consecutive stalled controller turns; controlled "
    "stops counted with the gate they rested.",
    "S-3: no executed free-play action is reported to Duck as failed (no 'action failed in sandbox host.' in a "
    "turn whose FREE_PLAY transition was recorded), Duck turns that act in free play are ledgered as executed, "
    "and every 'sandbox host hid' line in the kernel log is counted by type and site.",
    "W (reported): output size per world, and the 110-game rerun's projected working-directory use "
    "(per-world size times clone count) against the working directory's limit; the 1,000-action cap must not "
    "put the rerun at risk of filling the disk.",
]
LIVE_CRITERIA = SUBMISSION_CRITERIA
INFRA_CRITERIA = COMMON_INFRA

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
    r9_r24 = (
        (framework / "level_record.py", "def level_boards"),
        (framework / "record_relations.py", 'RECORD_KIND = "LEVER_RELATIONS_FROM_RECORD"'),
        (framework / "play_gate.py", "class PlayTarget"),
        (framework / "play_gate.py", "def charge_or_close"),
        (framework / "g4b_gate.py", "def record_answer"),
        (framework / "virelai_gates.py", 'PLAY_GATE_ID = "PLAY-NORMAL"'),
        (framework / "controller_executor.py", "the level's record certifies the relations"),
        (src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py", "def duck_turn_allowed"),
        (src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py", "def rest_if_no_legal_move"),
    )
    for path, marker in r9_r24:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry R9-R24 {marker!r} in {path.name}.")
    r9_r23 = (
        (framework / "mu_bucket.py", "class MuBucket"),
        (framework / "mu_return.py", "def return_to_mu"),
        (framework / "mu_return.py", "def revisit_probe"),
        (framework / "g3_inventory.py", "def check_inventory_claims"),
        (framework / "virelai_gates.py", "self.mu = MuBucket()"),
        (framework / "virelai_gates.py", '"closure": "PARTIAL" if partial else "COMPLETE"'),
        (framework / "virelai_gates.py", "def _emit_anatomy_product"),
        (framework / "controller_executor.py", "def return_to_mu_if_stuck"),
        (src / "ARC3-Inference" / "inference" / "agent" / "controller_turn.py", "return_to_mu_if_stuck(machine)"),
        (framework / "level_model.py", '"mu": machine.mu.snapshot()'),
        (framework / "life_record.py", '"mu": LEVEL'),
    )
    for path, marker in r9_r23:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry R9-R23 {marker!r} in {path.name}.")
    if "rewrite their own cells" in (framework / "controller_executor.py").read_text():
        raise RuntimeError("Packaged source still carries the inventory wording R9-R23 D17 replaced.")
    r9_r22 = (
        (framework / "lever_repeat.py", "def repeat_disposition"),
        (framework / "virelai_gates.py", "def _certify"),
        (framework / "virelai_gates.py", "DECLARED_ENDS = frozenset"),
        (framework / "virelai_gates.py", "def g3_pairs"),
        (framework / "g4_guided.py", "def typing"),
        (framework / "controller_executor.py", "REPEAT_TEXT"),
    )
    for path, marker in r9_r22:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry R9-R22 {marker!r} in {path.name}.")
    if "def _bound_contradicted" in (framework / "virelai_gates.py").read_text():
        raise RuntimeError("Packaged source still carries R9-R21 D4, which R9-R22 supersedes.")
    r9_r21 = (  # D4 is superseded by R9-R22 D7; D5 and D6 stand
        (framework / "virelai_gates.py", "def answer_blocked"),
        (framework / "controller_executor.py", "def _ladder_restarted"),
    )
    for path, marker in r9_r21:
        if marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry R9-R21 {marker!r} in {path.name}.")
    r9_r20 = (  # several markers per file: a dict keyed by path would keep only the last
        (framework / "virelai_gates.py", "def _refresh_settles"),
        (framework / "record_replay.py", "def record_like_live"),
    )
    for path, marker in r9_r20:
        if marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry R9-R20 {marker!r} in {path.name}.")
    unified = (  # the single tree: merge 501a6e6, F1 fa9617b, first-witness CLICK G3 (F2a)
        (framework / "virelai_gates.py", "Unified G3 law"),
        (framework / "virelai_gates.py", "self._legacy_confirmation_replay = bool(legacy_g3_confirmation_replay)"),
        (framework / "virelai_gates.py", '{"AMBIGUOUS", "BUDGET_STOPPED", "PRESUMED_UNREACHABLE"}'),
        (framework / "virelai_gates.py", '"schema": "virelai-g3-lever-discovery-v1"'),
        (framework / "record_replay.py", '"legacy_g3_confirmation_replay"'),
        (framework / "nav_route.py", "PRESUMED_UNREACHABLE"),
        (framework / "life_record.py", '"_legacy_confirmation_replay": GAME'),
    )
    for path, marker in unified:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source is not the single tree: no {marker!r} in {path.name}.")
    agent = src / "ARC3-Inference" / "inference" / "agent"
    sub2 = (  # SUB-2 (2026-10-07): the dry run's D-1, D-2 and D-3
        (agent / "action_names.py", '"ACTION7": "ACTION7"'),
        (agent / "controller_turn.py", "def rest_if_stalled"),
        (framework / "solver.py", "def _rest_after_controlled_stop"),
        (framework / "solver.py", "rest_on_controlled_stop: bool = False"),
    )
    for path, marker in sub2:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry SUB-2 {marker!r} in {path.name}.")
    sub3 = (  # SUB-3 (2026-10-09): free play reports its outcome; the sandbox host logs what it hides
        (framework / "play_gate.py", "def _event_outcome"),
        (framework / "play_gate.py", '"outcome": _event_outcome(outcome)'),
        (agent / "python_tool_sandbox.py", "def _hidden_error"),
    )
    for path, marker in sub3:
        if not path.is_file() or marker not in path.read_text():
            raise RuntimeError(f"Packaged source does not carry SUB-3 {marker!r} in {path.name}.")
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
    original = json.dumps(notebook)
    for ref in (OLD_DEPS.wheelhouse, OLD_DEPS.model):  # place 3: the notebook's DATASET_SOURCES
        if original.count(ref) != 1:
            raise RuntimeError(f"Expected the base notebook to name {ref} exactly once.")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
        source = "".join(cell.get("source", []))
        source = source.replace(OLD_DATASET_ID, DATASET_ID)
        source = source.replace(OLD_PACKAGE_NAME, PACKAGE_NAME)
        source = source.replace(OLD_DEPS.wheelhouse, DEPS.wheelhouse).replace(OLD_DEPS.model, DEPS.model)
        cell["source"] = source.splitlines(True)

    # Same world and budget as the base package: only identities change in the run cell.
    run_source = "".join(notebook["cells"][14]["source"])
    required_once = {
        "package label": f'bm.label = "{PACKAGE_NAME}"',
        "benchmark action budget": f"bm.solver.max_actions_per_game = {BASE_MAX_ACTIONS}",
        "benchmark runtime budget": f"bm.solver.max_runtime_s_per_game = {float(BASE_MAX_RUNTIME_SECONDS)}",
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
    # The canary's budgets replace the base's (each verified present exactly once above).
    run_source = _replace_once(
        run_source, f"bm.solver.max_actions_per_game = {BASE_MAX_ACTIONS}",
        f"bm.solver.max_actions_per_game = {MAX_ACTIONS}", "benchmark action budget",
    )
    run_source = _replace_once(
        run_source, f"bm.solver.max_runtime_s_per_game = {float(BASE_MAX_RUNTIME_SECONDS)}",
        f"bm.solver.max_runtime_s_per_game = {float(MAX_RUNTIME_SECONDS)}", "benchmark runtime budget",
    )
    run_source = _submission_run_cell(run_source)
    notebook["cells"][14]["source"] = run_source.splitlines(True)

    notebook["cells"][0]["source"] = [
        f"# Ring 9 submission ({MODE})\n",
        f"The single Ring 9 tree on every competition game: {CONCURRENCY} games at a time, each with a "
        f"{MAX_RUNTIME_SECONDS}-second slice and {MAX_ACTIONS} actions, inside the rerun's deadline. "
        "Self-hosted wheelhouse and model, pinned image. Run interactively, it plays the harness's "
        "competition-arcade simulator instead (not scored).\n",
    ]

    notebook_text = json.dumps(notebook)
    forbidden = {
        "stale package name": OLD_PACKAGE_NAME,
        "stale dataset": OLD_DATASET_ID,
        "notebook-wide target deadline": 'getattr(target, "max_runtime_s"',
        "old dependency owner": f"{OLD_OWNER}/",
    }
    for label, needle in forbidden.items():
        if needle in notebook_text:
            raise RuntimeError(f"Packaged notebook retained {label}.")
    for ref in (DEPS.wheelhouse, DEPS.model):
        if notebook_text.count(ref) != 1:
            raise RuntimeError(f"Packaged notebook must name {ref} exactly once.")
    if "nested_source" not in notebook_text:
        raise RuntimeError("Packaged notebook lost the verified Kaggle src.zip mount branch.")
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell["source"]), f"<{PACKAGE_NAME}-notebook>", "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
    path.write_text(json.dumps(notebook, indent=1) + "\n")


SUBMISSION_EDITS = (  # (label, base text, submission text): each base text must occur exactly once
    (
        "world allowlist",
        'expected_worlds = [str(game_id) for game_id in checkpoint["worlds"]]\n'
        'if not expected_worlds or len(expected_worlds) != len(set(expected_worlds)):\n'
        '    raise RuntimeError(f"Invalid checkpoint world allowlist: {expected_worlds}")\n',
        '# Ring 9 submission mode: the games are the competition Arcade\'s; the contract is a count.\n'
        'submission_contract = checkpoint["submission"]\n'
        'expected_worlds = []\n',
    ),
    (
        "offline game list",
        '    competition_env_files = str(Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels").parent / "environment_files")\n'
        '    bm.games = _offline_games(competition_env_files, expected_worlds)\n',
        '    # Dry run: the harness\'s competition-arcade simulator (the official public games cloned to the\n'
        '    # contract\'s count), played through the same gateway-shaped code as a real rerun.\n'
        '    import taaf.competition_arcade\n'
        '\n'
        '    competition_env_files = str(Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels").parent / "environment_files")\n'
        '    dry_run_arcade = taaf.competition_arcade.CompetitionArcadeServer(\n'
        '        total_runs=int(submission_contract["dry_run_game_count"]), environments_dir=competition_env_files,\n'
        '    ).start()\n'
        '    os.environ.setdefault("ARC_API_KEY", taaf.competition_arcade.DEFAULT_API_KEY)\n'
        '    os.environ["ARC_BASE_URL"] = dry_run_arcade.base_url.rstrip("/") + "/"\n'
        '    print(f"taaf.kaggle: dry-run competition arcade at {os.environ[\'ARC_BASE_URL\']}", flush=True)\n'
        '    bm.games = _competition_games()\n',
    ),
    (
        "world check",
        'if actual_worlds != expected_worlds:\n'
        '    raise RuntimeError(\n'
        '        f"Checkpoint world mismatch: expected {expected_worlds}, constructed {actual_worlds}"\n'
        '    )\n'
        'print(f"taaf.kaggle: checkpoint worlds verified: {actual_worlds}", flush=True)\n',
        'if not actual_worlds or len(actual_worlds) != len(set(actual_worlds)):\n'
        '    raise RuntimeError(f"Competition game list is empty or repeats an id: {len(actual_worlds)} games")\n'
        'if not TRUE_SUBMISSION and len(actual_worlds) != int(submission_contract["dry_run_game_count"]):\n'
        '    raise RuntimeError(\n'
        '        f"Dry run exposes {len(actual_worlds)} games, expected {submission_contract[\'dry_run_game_count\']}"\n'
        '    )\n'
        'print(f"taaf.kaggle: competition games verified: {len(actual_worlds)} unique ids", flush=True)\n',
    ),
    ("concurrency", "bm.solver.concurrency = 1\n",
     f"bm.solver.concurrency = {CONCURRENCY}\n"
     "bm.solver.rest_on_controlled_stop = True  # SUB-2 D-3 (Director, 2026-10-07): free play, not an end\n"),
    ("receipt worlds", '    "worlds": actual_worlds,\n', '    "worlds": "COMPETITION",\n'),
    (
        "soft end",
        f"soft_end = datetime.now() + timedelta(seconds={BASE_WINDOW_SECONDS})\n",
        'if TRUE_SUBMISSION:\n'
        '    # A rerun\'s wall clock starts with the notebook: model setup counts against it.\n'
        '    soft_end = datetime.fromtimestamp(NOTEBOOK_START_EPOCH) + timedelta(\n'
        '        seconds=int(submission_contract["run_wall_seconds"]) - int(submission_contract["exit_margin_seconds"])\n'
        '    )\n'
        'else:\n'
        '    soft_end = datetime.now() + timedelta(seconds=int(submission_contract["dry_run_window_seconds"]))\n'
        'print(f"taaf.kaggle: soft end {soft_end.isoformat(timespec=\'seconds\')}", flush=True)\n',
    ),
)


def _submission_run_cell(run_source: str) -> str:
    """D-2: games from a competition-shaped Arcade, a count contract, and the rerun's own deadline."""
    for label, old, new in SUBMISSION_EDITS:
        run_source = _replace_once(run_source, old, new, label)
    for needle in ("_offline_games(competition_env_files", 'checkpoint["worlds"]', "checkpoint worlds verified"):
        if needle in run_source:
            raise RuntimeError(f"Submission run cell still carries {needle!r}.")
    return run_source


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
    benchmark.solver.rest_on_controlled_stop = True  # SUB-2 D-3 (Director ruling 2026-10-07)
    benchmark.solver.save_request_logs = True
    _retarget_solver(benchmark.solver, bundle)
    with path.open("wb") as handle:
        pickle.dump(benchmark, handle)
    _retarget_deploy_target(bundle / "deploy_target.pkl")


def _changed_lines(before: str, after: str) -> list[tuple[int, str, str]]:
    old, new = before.splitlines(), after.splitlines()
    if len(old) != len(new):
        raise RuntimeError("A dependency edit must not add or remove setup-command lines.")
    return [(index, a, b) for index, (a, b) in enumerate(zip(old, new)) if a != b]


def _retarget_solver(solver: Any, bundle: Path) -> None:
    """Place 5: the pickled solver's dataset fields, cross-checked against the solver's own generator."""
    expected = {
        "kaggle_wheelhouse_dataset_source": OLD_DEPS.wheelhouse, "kaggle_model_dataset_source": OLD_DEPS.model,
        "kaggle_served_model_name": DEPS.served_model_name, "kaggle_vllm_max_model_len": DEPS.max_model_len,
        "kaggle_wheelhouse_stamp_text": DEPS.stamp,
    }
    for field, value in expected.items():
        if getattr(solver, field) != value:
            raise RuntimeError(f"Base solver {field} is {getattr(solver, field)!r}, expected {value!r}.")
    generated_old = solver.kaggle_setup_commands[0]
    solver.kaggle_wheelhouse_dataset_source = DEPS.wheelhouse
    solver.kaggle_model_dataset_source = DEPS.model
    generated_new = solver.kaggle_setup_commands[0]
    shipped_old = json.loads((BASE / "source-dataset" / "setup_commands.json").read_text())[0]
    shipped_new = json.loads((bundle / "setup_commands.json").read_text())[0]
    by_generator = _changed_lines(generated_old, generated_new)
    by_record = _changed_lines(shipped_old, shipped_new)
    if [line[1:] for line in by_generator] != [line[1:] for line in by_record] or len(by_record) != 4:
        raise RuntimeError(f"Dependency cross-check failed: generator {by_generator} vs record {by_record}.")


def _retarget_deploy_target(path: Path) -> None:
    """Place 4: the deploy target's declared extra datasets (unpickled with the export's taaf)."""
    with path.open("rb") as handle:
        target = pickle.load(handle)
    if list(target.additional_dataset_sources) != [OLD_DEPS.wheelhouse, OLD_DEPS.model]:
        raise RuntimeError(f"Base deploy target declares {target.additional_dataset_sources}.")
    target.additional_dataset_sources = [DEPS.wheelhouse, DEPS.model]
    with path.open("wb") as handle:
        pickle.dump(target, handle)


def _old_owner_guard(out: Path) -> None:
    """No package file outside the frozen source names the old dependency owner.

    RUN.md is exempt: it is the human record of why v2 exists, and it names what v1 depended on.
    """
    source = out / "source-dataset" / "src"
    found = [
        str(path.relative_to(out)) for path in sorted(out.rglob("*"))
        if path.is_file() and source not in path.parents and path.name not in {"src.zip", "RUN.md"}
        and OLD_OWNER.encode() in path.read_bytes()
    ]
    if found:
        raise RuntimeError(f"Package files still name {OLD_OWNER}: {found}")


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
        f"# Ring 9 submission package ({MODE}): the single tree on every competition game\n\n"
        f"Source commit `{SOURCE_COMMIT}` ({REVISIONS}). Settings: {CONCURRENCY} games at a time, each game "
        f"stopped at {MAX_RUNTIME_SECONDS} s or {MAX_ACTIONS} actions, gated mode, controller executor on.\n\n"
        "**In a competition rerun** (`KAGGLE_IS_COMPETITION_RERUN`): the games are the live competition "
        "Arcade's, at the Kaggle gateway; the soft end is the notebook's start plus "
        f"{RUN_WALL_SECONDS} s minus a {EXIT_MARGIN_SECONDS} s exit margin.\n\n"
        "**Interactively** (Save & Run, and this package's dry run): the games are the harness's "
        f"competition-arcade simulator ({SPEC['game_count']} clones of the 25 public games) at a local "
        f"gateway-shaped server, and the soft end is {SPEC['dry_run_window_seconds']} s after model setup. "
        "Not scored.\n\n"
        "## Preregistered grading (from artifact state, not prose)\n\n"
        f"{criteria_md}\n"
        f"Request preflight (T10): worst case {preflight['worst_case_tokens_at_3_chars']} tokens "
        f"against a {CONTEXT_WINDOW}-token window, for one request.\n\n"
        f"Dataset: `{DATASET_ID}`  \nNotebook: `{KERNEL_ID}`\n"
    )
    (OUT / "TEST_RESULTS.txt").write_text(TEST_RESULTS)

    dataset_metadata = json.loads((bundle / "dataset-metadata.json").read_text())
    dataset_metadata["id"] = DATASET_ID
    dataset_metadata["title"] = f"Virelai Ring 9 submission {MODE} v2"
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
    setup_path = bundle / "setup_commands.json"
    setup_commands, kernel_metadata = DEPENDENCIES.retarget(  # places 1 and 2
        json.loads(setup_path.read_text()), kernel_metadata, OLD_DEPS, DEPS,
    )
    if kernel_metadata["dataset_sources"] != [DATASET_ID, DEPS.wheelhouse, DEPS.model]:
        raise RuntimeError(f"Kernel mounts {kernel_metadata['dataset_sources']}.")
    setup_path.write_text(json.dumps(setup_commands, indent=2) + "\n")  # the base file's own format
    if kernel_metadata.get("machine_shape") != ENVIRONMENT["machine_shape"]:
        raise RuntimeError(f"Kernel machine shape is {kernel_metadata.get('machine_shape')!r}.")
    kernel_metadata["docker_image"] = ENVIRONMENT["docker_image"]  # pinned (v4): v3 met Python 3.13
    kernel_metadata["docker_image_pinning_type"] = ENVIRONMENT["docker_image_pinning_type"]
    _write_json(OUT / "kernel" / "kernel-metadata.json", kernel_metadata)

    bundle_metadata = json.loads((bundle / "taaf-kaggle-bundle.json").read_text())
    bundle_metadata["created_at"] = datetime.now(timezone.utc).isoformat()
    bundle_metadata["benchmark_label"] = PACKAGE_NAME
    _write_json(bundle / "taaf-kaggle-bundle.json", bundle_metadata)

    checkpoint = {
        "schema": "virelai-gated-checkpoint-preflight-v2",
        "stage": f"RING9-SUBMISSION-{MODE.upper()}-V1",
        "claim": (
            "The single Ring 9 tree plays every competition game inside the run's deadline: games run "
            "concurrently under a per-game slice, the ladder from G0 to normal play on each, with no gate weakened."
        ),
        "submission": {
            "mode": MODE,
            "run_wall_seconds": RUN_WALL_SECONDS,
            "exit_margin_seconds": EXIT_MARGIN_SECONDS,
            "dry_run_window_seconds": SPEC["dry_run_window_seconds"],
            "dry_run_game_count": SPEC["game_count"],
            "concurrency": CONCURRENCY,
        },
        "controller_executor": True,
        "request_preflight": preflight,
        "source_commit": SOURCE_COMMIT,
        "revisions": REVISIONS,
        "worlds": "COMPETITION",
        "model": MODEL,
        "dependencies": DEPS.record(),
        "environment": ENVIRONMENT,
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
            "Automated grades do not establish semantic correctness; a receipt-bound review is required.",
            "One world, one pass: a canary of the machinery, not a measure of generalisation or a score.",
            "The tree has been run live on two public worlds only; most competition games are unseen.",
            "A level won by the G4-A study is the study's, not the model's.",
            "Paper and prereg claims cite gated evidence only; FREE_PLAY transitions are tagged (R-2).",
        ],
    }
    _write_json(bundle / "checkpoint-preflight.json", checkpoint)
    (bundle / "README.dataset.md").write_text(
        f"# Ring 9 submission {MODE} v2\n\n"
        "Frozen gated source. The notebook verifies its source manifest and exact execution receipt "
        "before running. This is a private diagnostic, not a submission.\n"
    )
    (bundle / "preamble.txt").write_text(
        f"Ring 9 submission {MODE} v2 (single tree, self-hosted dependencies, pinned image): competition games, {CONCURRENCY} at a time, {MAX_ACTIONS} "
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
    _old_owner_guard(OUT)

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
        "dependencies": DEPS.record(),
        "environment": ENVIRONMENT,
        "budgets": {
            "max_environment_actions_per_world": MAX_ACTIONS,
            "max_runtime_seconds_per_world": MAX_RUNTIME_SECONDS,
            "context_window_tokens": CONTEXT_WINDOW,
            "max_output_tokens_per_turn": "server_default",
            "tool_output_tokens": TOOL_OUTPUT_TOKENS,
        },
        "worlds": "COMPETITION",
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

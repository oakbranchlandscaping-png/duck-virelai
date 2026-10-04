"""Fixed-action online smoke for the hidden continuity observer."""
from __future__ import annotations

import argparse
import hashlib
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import arc_agi
import arcengine
import taaf.game
import taaf.game_api

from inference.agent.tool_agent import _build_system_prompt, _python_tool_description
from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.virelai_runtime import verify_frame_archive

VC33_ACTIONS = [(25, 61), (46, 48), (30, 28), (34, 61), (25, 61), (30, 39), (34, 61), (25, 61)]
RING0_SYSTEM_SHA256 = "2ffc92d92f494419d8c97105d9045d203edcbc63bb0970e6a0ce64f9a70f4ccc"
RING0_PYTHON_DESCRIPTION_SHA256 = "70b4394c089117f7d4d764a4f6cc883495d850579ff05ee3850e5733a960135b"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def run(game_id: str, output_root: Path) -> dict:
    if output_root.exists():
        raise FileExistsError(f"Refusing to reuse output root: {output_root}")
    output_root.mkdir(parents=True)
    run_session = taaf.game.RunSession(record_intermediate_states=True)
    game = taaf.game_api.GameAPI(
        env_name=game_id,
        arcade_spec=taaf.game_api.ArcadeSpec(
            operation_mode=arc_agi.OperationMode.ONLINE,
            environments_dir="",
        ),
    )
    closed = False
    try:
        game.start_game(run_session)
        solver = HarnessSolver(virelai_mode="observe")
        solver.job_dir = output_root
        session = _HarnessGameSession(
            solver=solver,
            game=game,
            analyzer=SimpleNamespace(generated_tokens=0),
            game_index=0,
            pass_index=0,
            state_path=output_root / "state.json",
            transcript_path=output_root / "transcript.txt",
            analysis_html_relpath="analysis.html",
            stop_event=threading.Event(),
            viewer_data_path=output_root / "viewer.json",
        )
        session.seed_initial_history()
        session._observe_virelai_initial()
        results = []
        for index, (row, col) in enumerate(VC33_ACTIONS, 1):
            results.append(
                session._execute_action(
                    arcengine.ActionInput(
                        id=arcengine.GameAction.ACTION6,
                        data={"x": col, "y": row},
                    ),
                    batch_index=index,
                    batch_size=len(VC33_ACTIONS),
                    generated_tokens=0,
                    flush_viewer_payload=False,
                )
            )
            if results[-1].get("done"):
                break
        session._close_game_observer()
        closed = True
        run_stem = solver._run_stem(game.game_run.game_id, 0)
        artifact_dir = output_root / "virelai" / run_stem
        archive = verify_frame_archive(artifact_dir)
        raw_summary = json.loads((artifact_dir / "summary.json").read_text())
        continuity = json.loads((artifact_dir / "continuity_summary.json").read_text())
        system_prompt = _build_system_prompt(tool_output_tokens=1024, virelai_enabled=False)
        description = _python_tool_description(virelai_enabled=False)
        checks = {
            "all_actions_executed": all(item.get("executed") for item in results),
            "archive_n_plus_one": archive.get("frames") == len(results) + 1,
            "archive_integrity": bool(archive.get("passed")),
            "capture_p95_under_25ms": float(raw_summary["capture_performance"]["p95_ms"]) <= 25.0,
            "capture_max_under_50ms": float(raw_summary["capture_performance"]["max_ms"]) <= 50.0,
            "capture_zero_breaches": int(raw_summary["capture_performance"]["breaches"]) == 0,
            "continuity_current": continuity.get("compiled_through_node") == len(results),
            "continuity_fault_free": continuity.get("faults") == 0,
            "continuity_hidden": continuity.get("duck_visible") is False,
            "ring0_system_prompt": _sha(system_prompt) == RING0_SYSTEM_SHA256,
            "ring0_python_description": _sha(description) == RING0_PYTHON_DESCRIPTION_SHA256,
            "no_virelai_prompt_text": "virelai" not in (system_prompt + description).lower(),
        }
        report = {
            "schema": "virelai-live-continuity-shadow-v1",
            "game_id": game.game_run.game_id,
            "actions": VC33_ACTIONS[: len(results)],
            "archive": archive,
            "capture_performance": raw_summary["capture_performance"],
            "continuity": continuity,
            "checks": checks,
            "passed": all(checks.values()),
        }
        (output_root / "live_continuity_shadow_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        return report
    finally:
        if "session" in locals() and not closed:
            session._close_game_observer()
        if game.game_run is not None and game.game_run.final_score is None:
            game.finish_game()
        run_session.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default="vc33-5430563c")
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.game, args.output_root.resolve())
    except Exception as exc:
        print(f"Live continuity smoke failed: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

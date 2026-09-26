"""Eight-action online gate for the optional observational clock query."""
from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import arc_agi
import arcengine
import taaf.game
import taaf.game_api

from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.virelai_runtime import verify_frame_archive


VC33_ACTIONS = [(25, 61), (46, 48), (30, 28), (34, 61), (25, 61), (30, 39), (34, 61), (25, 61)]


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
        solver = HarnessSolver()
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
            action = arcengine.ActionInput(
                id=arcengine.GameAction.ACTION6,
                data={"x": col, "y": row},
            )
            result = session._execute_action(
                action,
                batch_index=index,
                batch_size=len(VC33_ACTIONS),
                generated_tokens=0,
                flush_viewer_payload=False,
            )
            results.append(result)
            if result.get("done"):
                break
        clock = session.query_virelai("clock")
        session._close_game_observer()
        closed = True
        run_stem = solver._run_stem(game.game_run.game_id, 0)
        archive = verify_frame_archive(output_root / "virelai" / run_stem)
        candidates = (clock.get("data") or {}).get("candidates") or []
        checks = {
            "eight_actions": len(results) == 8,
            "all_actions_executed": all(item.get("executed") for item in results),
            "query_current": clock.get("observed_through_step") == len(results),
            "candidate_present": bool(candidates),
            "witness_floor_met": all(item.get("witness_count", 0) >= 8 for item in candidates),
            "archive_n_plus_one": archive.get("frames") == len(results) + 1,
            "archive_integrity": bool(archive.get("passed")),
            "query_under_50ms": float(clock.get("latency_ms", 999999)) <= 50.0,
        }
        report = {
            "schema": "virelai-live-clock-smoke-v1",
            "game_id": game.game_run.game_id,
            "actions": VC33_ACTIONS[: len(results)],
            "clock": clock,
            "archive": archive,
            "checks": checks,
            "passed": all(checks.values()),
        }
        (output_root / "live_clock_report.json").write_text(
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
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.game, args.output_root.resolve())
    except Exception as exc:  # noqa: BLE001
        print(f"Live clock smoke failed: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

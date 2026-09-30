"""One-action online gate for the passive action-effects integration."""
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


def _choose_action(
    available: tuple[int, ...],
    *,
    requested: str,
    row: int,
    col: int,
) -> arcengine.ActionInput:
    actions = [arcengine.GameAction.from_id(int(value)) for value in available]
    if requested:
        selected = arcengine.GameAction.from_name(requested.upper())
        if selected not in actions:
            raise ValueError(
                f"Requested {selected.name} is not available; "
                f"available={[item.name for item in actions]}"
            )
    else:
        selected = next(
            (item for item in actions if item != arcengine.GameAction.RESET),
            None,
        )
        if selected is None:
            raise ValueError("No non-reset action is available.")
    data = {"x": int(col), "y": int(row)} if selected.is_complex() else {}
    return arcengine.ActionInput(id=selected, data=data)


def run(
    *,
    game_id: str,
    output_root: Path,
    action_name: str,
    row: int,
    col: int,
) -> dict:
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
    observer_closed = False
    try:
        game.start_game(run_session)
        action = _choose_action(
            tuple(game.current_state.available_actions),
            requested=action_name,
            row=row,
            col=col,
        )
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
        before_grid = [layer.tolist() for layer in game.current_state.raw.frame]
        action_result = session._execute_action(
            action,
            batch_index=1,
            batch_size=1,
            generated_tokens=0,
            flush_viewer_payload=False,
        )
        after_grid = [layer.tolist() for layer in game.current_state.raw.frame]
        effects = session.query_virelai("effects")
        session._close_game_observer()
        observer_closed = True

        run_stem = solver._run_stem(game.game_run.game_id, 0)
        artifact_dir = output_root / "virelai" / run_stem
        archive = verify_frame_archive(artifact_dir)
        data = effects.get("data") or {}
        entries = data.get("entries") or []
        entry = entries[0] if entries else {}
        checks = {
            "action_executed": bool(action_result.get("executed")),
            "query_current": effects.get("observed_through_step") == 1,
            "action_name_matches": entry.get("action")
            == action_result.get("action_display"),
            "one_press_recorded": entry.get("presses") == 1,
            "outcome_partitioned": entry.get("changed", 0)
            + entry.get("unchanged", 0) == 1,
            "two_frames": archive.get("frames") == 2,
            "archive_integrity": bool(archive.get("passed")),
            "before_after_available": bool(before_grid) and bool(after_grid),
        }
        report = {
            "schema": "virelai-live-effects-smoke-v1",
            "game_id": game.game_run.game_id,
            "action": {
                "id": int(action.id.value),
                "name": action.id.name,
                "data": dict(action.data),
            },
            "action_result": action_result,
            "effects": effects,
            "archive": archive,
            "checks": checks,
            "passed": all(checks.values()),
        }
        (output_root / "live_effects_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return report
    finally:
        if "session" in locals() and not observer_closed:
            session._close_game_observer()
        if game.game_run is not None and game.game_run.final_score is None:
            game.finish_game()
        run_session.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default="vc33-5430563c")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--action", default="")
    parser.add_argument("--row", type=int, default=32)
    parser.add_argument("--col", type=int, default=32)
    args = parser.parse_args()
    try:
        report = run(
            game_id=args.game,
            output_root=args.output_root.resolve(),
            action_name=args.action,
            row=args.row,
            col=args.col,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Live effects-ledger smoke failed: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

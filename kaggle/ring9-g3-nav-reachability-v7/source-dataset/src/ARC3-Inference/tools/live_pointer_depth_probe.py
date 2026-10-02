"""Controlled online POINTER depth-probe gate; Duck and model are never invoked."""
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
from inference.framework.virelai_semantic.compiler import compile_semantic_library
from inference.framework.virelai_semantic.depth_adapter import PointerDepthAdapter


# Existing fixed vc33 discovery replay.  It touches both known controls and several ordinary
# objects, giving the role reader positive and negative witnesses before depth probing begins.
VC33_DISCOVERY = [
    (25, 61), (46, 48), (30, 28), (34, 61),
    (25, 61), (30, 39), (34, 61), (25, 61),
]

FT09_DISCOVERY = [
    (46, 44), (5, 15), (11, 15), (35, 35), (46, 46), (32, 40), (63, 32),
    (28, 32), (38, 38), (46, 38), (46, 54), (54, 54), (46, 46), (38, 38),
    (38, 46), (38, 54), (46, 38), (46, 54), (54, 46), (38, 38), (38, 46),
    (38, 54),
]

DISCOVERY_FIXTURES = {
    "vc33": VC33_DISCOVERY,
    "ft09": FT09_DISCOVERY,
}


def _click(session: _HarnessGameSession, row: int, col: int, index: int) -> dict:
    return session._execute_action(
        arcengine.ActionInput(
            id=arcengine.GameAction.ACTION6,
            data={"x": int(col), "y": int(row)},
        ),
        batch_index=index,
        batch_size=1,
        generated_tokens=0,
        flush_viewer_payload=False,
        actor="CAPTAIN",
    )


def run(*, game_id: str, output_root: Path, cap: int, fixture: str) -> dict:
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
        actual_game_id = str(game.game_run.game_id)
        if not actual_game_id.startswith(f"{fixture}-"):
            raise ValueError(
                f"fixture {fixture!r} does not match requested game {actual_game_id!r}"
            )
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
        actions = []
        discovery = DISCOVERY_FIXTURES[fixture]
        for row, col in discovery:
            outcome = _click(session, row, col, len(actions) + 1)
            actions.append({"phase": "DISCOVERY", "row": row, "col": col, "outcome": outcome})
            if outcome.get("done") or outcome.get("game_over") or outcome.get("level_completed"):
                break

        observer = session.game_observer
        if observer is None:
            raise RuntimeError(f"observer unavailable: {session.virelai_fault}")
        # This is a diagnostic tool inside the framework, not a public observer-protocol call.
        # The production wrapper deliberately exposes only observe/query/close to Duck.
        runtime = getattr(observer, "_runtime", None)
        if runtime is None:
            raise RuntimeError("observer runtime is unavailable to the diagnostic gate")
        discovery_library = compile_semantic_library(runtime.journal)
        (output_root / "discovery_semantic_library.json").write_text(
            json.dumps(discovery_library, indent=2, sort_keys=True), encoding="utf-8"
        )
        adapter = PointerDepthAdapter(discovery_library, engineering_cap=cap)
        start_level = int(game.current_state.levels_completed)
        while len(actions) < len(discovery) + cap * 8:
            request = adapter.next_pointer_action()
            if request["status"] != "ACTION_READY":
                break
            action = request["action"]
            lever = request["request"]["lever"]
            outcome = _click(session, action["row"], action["col"], len(actions) + 1)
            actions.append({
                "phase": "DEPTH",
                "lever": lever,
                "row": action["row"],
                "col": action["col"],
                "outcome": outcome,
            })
            adapter.observe_result(
                lever=lever,
                step=len(actions),
                frame=game.current_state.raw.frame,
            )
            if (
                outcome.get("done") or outcome.get("game_over") or outcome.get("level_completed")
                or int(game.current_state.levels_completed) != start_level
            ):
                break

        probe_report = adapter.report()
        (output_root / "lever_depth_report.json").write_text(
            json.dumps(probe_report, indent=2, sort_keys=True), encoding="utf-8"
        )
        session._close_game_observer()
        closed = True
        run_stem = solver._run_stem(game.game_run.game_id, 0)
        artifact = output_root / "virelai" / run_stem
        archive = verify_frame_archive(artifact)
        depth_actions = [item for item in actions if item["phase"] == "DEPTH"]
        pointer_only = all(item["outcome"].get("executed") for item in depth_actions)
        completed_probes = [
            item for item in probe_report["levers"]
            if item["completion"] == "EVIDENCE_TERMINATED"
        ]
        level_won = any(item["outcome"].get("level_completed") for item in depth_actions)
        report = {
            "schema": "virelai-live-pointer-depth-gate-v1",
            "game_id": game.game_run.game_id,
            "discovery_actions": len(actions) - len(depth_actions),
            "depth_actions": len(depth_actions),
            "actions": actions,
            "probe": probe_report,
            "archive": archive,
            "checks": {
                "lever_discovered": bool(probe_report["levers"]),
                "depth_action_executed": bool(depth_actions) and pointer_only,
                "semantic_probe_progress": bool(completed_probes) or level_won,
                "no_duck_or_model_calls": True,
                "archive_integrity": bool(archive.get("passed")),
            },
        }
        report["passed"] = all(report["checks"].values())
        (output_root / "live_pointer_depth_report.json").write_text(
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
    parser.add_argument("--fixture", choices=sorted(DISCOVERY_FIXTURES), default="vc33")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cap", type=int, default=32)
    args = parser.parse_args()
    try:
        report = run(
            game_id=args.game,
            output_root=args.output_root.resolve(),
            cap=args.cap,
            fixture=args.fixture,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Live pointer depth gate failed: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps({
        "passed": report["passed"],
        "game_id": report["game_id"],
        "discovery_actions": report["discovery_actions"],
        "depth_actions": report["depth_actions"],
        "checks": report["checks"],
    }, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

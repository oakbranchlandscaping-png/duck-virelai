"""Live fixed-action gate for post-win grammar and next-level carry; no Duck/model calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from types import SimpleNamespace

from tools.live_pointer_depth_probe import _click
import arc_agi
import taaf.game
import taaf.game_api

from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.virelai_runtime import verify_frame_archive
from inference.framework.virelai_semantic.compiler import compile_semantic_library
from tools.compile_level_carry import write_level_carry
from tools.compile_post_win_grammars import write_post_win


VC33_LEVEL1_WIN = [
    (47, 48), (47, 51), (30, 39), (26, 62), (34, 62), (26, 62),
    (26, 62), (26, 62), (34, 62), (34, 62), (34, 62), (34, 62),
    (34, 62), (30, 39), (26, 62), (26, 62), (26, 62), (26, 62),
    (26, 62), (47, 48), (34, 62), (34, 62), (34, 62), (34, 62),
    (34, 62), (34, 62),
]


def run(game_id: str, output_root: Path) -> dict:
    if output_root.exists():
        raise FileExistsError(f"Refusing to reuse output root: {output_root}")
    output_root.mkdir(parents=True)
    run_session = taaf.game.RunSession(record_intermediate_states=True)
    game = taaf.game_api.GameAPI(
        env_name=game_id,
        arcade_spec=taaf.game_api.ArcadeSpec(
            operation_mode=arc_agi.OperationMode.ONLINE, environments_dir=""),
    )
    closed = False
    try:
        game.start_game(run_session)
        solver = HarnessSolver(virelai_mode="observe"); solver.job_dir = output_root
        import threading
        session = _HarnessGameSession(
            solver=solver, game=game, analyzer=SimpleNamespace(generated_tokens=0),
            game_index=0, pass_index=0, state_path=output_root / "state.json",
            transcript_path=output_root / "transcript.txt", analysis_html_relpath="analysis.html",
            stop_event=threading.Event(), viewer_data_path=output_root / "viewer.json")
        session.seed_initial_history(); session._observe_virelai_initial()
        actions, won = [], False
        for row, col in VC33_LEVEL1_WIN:
            outcome = _click(session, row, col, len(actions) + 1)
            actions.append({"row": row, "col": col, "outcome": outcome})
            if outcome.get("level_completed"):
                won = True; break
            if outcome.get("done") or outcome.get("game_over"):
                break
        stem = solver._run_stem(game.game_run.game_id, 0)
        artifact = output_root / "virelai" / stem
        observer = session.game_observer
        runtime = getattr(observer, "_runtime", None) if observer is not None else None
        if runtime is None:
            raise RuntimeError("observer runtime unavailable before semantic compilation")
        # A real Duck turn spends seconds generating before it can request the lesson.
        # Give the speculative compiler one second; this wait is gate-only, never production.
        time.sleep(1.0)
        lesson_query = observer.query("lesson", {"level": 1})
        mechanics_query = observer.query("mechanics", {"level": 1})
        win_query = observer.query("win", {"level": 1})
        carry_query = observer.query("carry", {"level": 1})
        (output_root / "duck_lesson_query.json").write_text(
            json.dumps(lesson_query, indent=2, sort_keys=True), encoding="utf-8")
        for name, response in (("mechanics", mechanics_query), ("win", win_query),
                               ("carry", carry_query)):
            (output_root / f"duck_{name}_query.json").write_text(
                json.dumps(response, indent=2, sort_keys=True), encoding="utf-8")
        library = compile_semantic_library(runtime.journal)
        (artifact / "semantic_library.json").write_text(
            json.dumps(library, indent=2, sort_keys=True), encoding="utf-8")
        session._close_game_observer(); closed = True
        archive = verify_frame_archive(artifact)
        post_dir, carry_dir = artifact / "post_win_grammars_v3", artifact / "level_carry_v1"
        post = write_post_win(artifact, post_dir)
        carry = write_level_carry(artifact, post_dir, carry_dir)
        report = {"schema": "virelai-live-level-carry-gate-v1", "game_id": game.game_run.game_id,
                  "actions": actions, "level_won": won, "archive": archive,
                  "post_win_grammars": post, "carry_artifacts": carry,
                  "lesson_query_latency_ms": lesson_query.get("latency_ms"),
                  "lesson_query_budget_breached": lesson_query.get("budget_breached"),
                  "lesson_has_physics_grammar": bool(
                      (mechanics_query.get("data") or {}).get("controls")),
                  "lesson_win_explanation_status": (
                      win_query.get("data") or {}).get("status"),
                  "lesson_type_correspondences": len(
                      (carry_query.get("data") or {}).get("candidate_controls", [])),
                  "focused_payload_bytes": {
                      name: len(json.dumps(response.get("data")))
                      for name, response in (("lesson", lesson_query),
                                             ("mechanics", mechanics_query),
                                             ("win", win_query), ("carry", carry_query))
                  },
                  "no_duck_or_model_calls": True}
        report["passed"] = bool(won and archive.get("passed") and post and carry
                                and report["lesson_has_physics_grammar"]
                                and report["lesson_win_explanation_status"] is not None
                                and not lesson_query.get("error")
                                and not lesson_query.get("budget_breached"))
        (output_root / "live_level_carry_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
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
        print(f"Live level carry gate failed: {type(exc).__name__}: {exc}"); return 1
    print(json.dumps({k: report[k] for k in ("passed", "game_id", "level_won",
                                             "post_win_grammars", "carry_artifacts",
                                             "lesson_query_latency_ms",
                                             "lesson_query_budget_breached",
                                             "lesson_has_physics_grammar",
                                             "lesson_win_explanation_status",
                                             "lesson_type_correspondences")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

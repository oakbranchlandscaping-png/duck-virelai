"""WO-L2a: the real paths that must write, and must not overwrite, the canonical world model.

Author: Claude (Alpha build seat), 2026-10-10. Sol's review of the WO-L2a interface: "Tests should fail for
observable behavior on the present tree (missing artifact on zero-action cancellation, query overwrite)".

Both tests drive production code, not the writer directly:

- ``_HarnessGameSession.play`` with the stop already requested: the initial board is observed
  (``solver.py:472``), the loop never runs, and ``finally`` cancels and closes (``:542-588``). This is the
  path the 77 v2 games that observed one board and never acted took.
- A legacy ``controller``/``intent``/``agenda`` query on the runtime after a v2 file exists: today it
  rewrites ``world_model.json`` as v1 (``virelai_runtime.py:1055-1080``).

They were strict xfails until the H2 hook and the legacy-writer separation landed (the WO-L2a hooks slice,
2026-10-11, under NOTE_SHARED_FILE_WO_L2A_HOOKS); the marks were removed with it.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import arcengine
import pytest

from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.virelai_runtime import VirelaiRuntime
from test_duck_native_observer import _Game

class _CancelledGame(_Game):
    def __init__(self):
        super().__init__()
        self.game_run.__dict__.update(
            solver_note=None, solver_analysis_html=None, final_score=None, levels_completed=0,
            number_of_levels=1, actions_per_level=[],
        )

    def finish_game(self):
        self.game_run.final_score = 0.0


def _cancelled_before_first_turn(tmp_path: Path) -> tuple[Path, _CancelledGame, list[int]]:
    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    game = _CancelledGame()
    calls: list[int] = []
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=SimpleNamespace(generated_tokens=0, analyze=lambda *a, **k: calls.append(1)),
        game_index=0, pass_index=0, state_path=tmp_path / "state.json", transcript_path=tmp_path / "t.txt",
        analysis_html_relpath="a.html", stop_event=threading.Event(), viewer_data_path=tmp_path / "v.json",
    )
    session.stop_event.set()
    session.play()
    return tmp_path / "virelai" / solver._run_stem("fixture", 0), game, calls


def test_the_cancelled_path_is_the_77_game_shape(tmp_path):
    """Premise, true today: one observed board, no model turn, no action, and the run is cancelled."""
    folder, game, calls = _cancelled_before_first_turn(tmp_path)
    assert calls == [] and game.game_run.history == [] and game.game_run.state == "cancelled"
    assert len((folder / "frames.jsonl").read_text().splitlines()) == 1


def test_a_zero_action_cancellation_writes_the_canonical_model(tmp_path):
    folder, _game, _calls = _cancelled_before_first_turn(tmp_path)
    model = json.loads((folder / "world_model.json").read_text())
    assert model["schema"] == "virelai-world-model-v7"
    assert model["manifest"]["status"] == "OBSERVED_NEVER_ACTED"
    assert model["levels"][0]["entry"]["source"] == "INITIAL_FRAME"
    assert {gate["disposition"] for gate in model["levels"][0]["certified"]["gates"]} == {"NOT_STARTED"}


@pytest.mark.parametrize("operation", ["controller", "intent", "agenda"])
def test_a_legacy_query_never_replaces_the_canonical_model(tmp_path, operation):
    runtime = VirelaiRuntime(game_id="fixture", run_stem="fixture_p0", artifact_root=tmp_path)
    raw = _Game().current_state.raw
    runtime.observe_initial(arcengine.FrameData(
        game_id=raw.game_id, frame=[layer.tolist() for layer in raw.frame], state=raw.state,
        levels_completed=0, win_levels=1, guid=raw.guid, full_reset=False, available_actions=raw.available_actions,
    ))
    canonical = tmp_path / "fixture_p0" / "world_model.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(b'{"schema":"virelai-world-model-v2"}')
    runtime.query(operation, {})
    assert canonical.read_bytes() == b'{"schema":"virelai-world-model-v2"}'

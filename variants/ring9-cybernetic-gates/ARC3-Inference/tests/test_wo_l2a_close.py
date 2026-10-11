"""WO-L2a close-out: live free play is recorded and accounted; the run's end reason is persisted honestly.

Author: Claude (Alpha build seat), 2026-10-11. Sol's rulings on the hooks findings (relayed by the Director):

1. "Free play belongs in the transition record ... the claimed live failure is not yet established ...
   reproduce this through the live gated play path before changing code."
2. "Keep canonical v2 writing scoped to gated mode ... they must not overwrite world_model.json."
3. "Capture the stop reason when a controlled stop actually ends the run ... A stop that rests the gates
   and resumes play is not the run's final reason."

Every test drives the production path: ``_HarnessGameSession.play`` with a real gated ``ToolAgent``, its
real gate machine, and the real python-tool ``action()`` bridge. Only the language model is absent: each
analyzer turn is a scripted function that acts through the same tool path Duck uses.
"""
from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import pytest

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.agent.tool_agent import ToolAgent
from inference.framework.play_gate import FREE_PLAY, rest_in_play
from inference.framework.solver import HarnessSolver, _HarnessGameSession
from inference.framework.world_model_v2 import read_world_model
from test_duck_native_observer import _Game, _state

PLAY = "PLAY-NORMAL"


class _LiveGame(_Game):
    """The fixture engine: every action changes the board and is kept in ``game_run.history``."""

    def __init__(self):
        super().__init__()
        self.game_run.__dict__.update(
            solver_note=None, solver_analysis_html=None, final_score=None, levels_completed=0,
            number_of_levels=1, actions_per_level=[],
        )

    def execute_action(self, action, *, generated_tokens, uncached_input_tokens):
        del generated_tokens, uncached_input_tokens
        self.current_state = _state(len(self.game_run.history) + 2)
        self.game_run.history.append(SimpleNamespace(action=action))
        return self.current_state

    def finish_game(self):
        self.game_run.final_score = 0.0


def _turn(**fields):
    return SimpleNamespace(**{"fatal_failure": None, "controlled_stop": "", "planned_stop": "",
                              "retryable_failure": False, "yielded_control": False, "step_executed": False,
                              **fields})


def _answer_g0(machine):
    if machine.g0_answer is None:
        machine.submit_answer({
            "answer_id": "G0-test",
            "action_metadata": [{"action": item.action, "requires_coordinates": item.requires_coordinates}
                                for item in machine.ego.affordances],
            "semantic_claims": [],
            "epistemic_limit": "Action effects remain unknown until they are observed through probes.",
        })


def _free_play(agent, state_path, machine):
    """One Duck free-play action through the real python-tool bridge and the play gate's token."""
    token = machine.next_probe_capability()["probe_token"]
    return agent._run_python_tool(state_path, {"code": f"r = action(['ACTION1'], decision={{'probe_token': {token!r}}})"})


def _live(tmp_path, script, *, mode="gated", rest_on_controlled_stop=False):
    """Run play() with a real gated ToolAgent; ``script[i]`` is analyzer turn i (agent, machine, state_path)."""
    solver = HarnessSolver(virelai_mode=mode)
    solver.job_dir = tmp_path
    solver.rest_on_controlled_stop = rest_on_controlled_stop
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True)
    turns: list[int] = []

    def analyze(state_path, action_count, *, valid_actions, step_env, **_kwargs):
        agent._ensure_session(state_path)
        agent._step_env_callback = step_env
        agent._current_valid_actions = list(valid_actions)
        machine = agent._ensure_gate_machine(state_path)
        _answer_g0(machine)
        turns.append(len(turns))
        return script[len(turns) - 1](agent, machine, state_path)

    agent.analyze = analyze
    game = _LiveGame()
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=agent, game_index=0, pass_index=0,
        state_path=tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}", transcript_path=tmp_path / "t.txt",
        analysis_html_relpath="a.html", stop_event=threading.Event(), viewer_data_path=tmp_path / "v.json",
    )
    session.play()
    return SimpleNamespace(agent=agent, game=game, turns=turns,
                           folder=tmp_path / "virelai" / solver._run_stem("fixture", 0), tmp=tmp_path)


def _model(run):
    payload = json.loads((run.folder / "world_model.json").read_text())
    read_world_model(payload)  # validates
    return payload


def _rest_and_play(agent, machine, state_path):
    rest_in_play(machine, "test: the level rests in normal play")
    result = _free_play(agent, state_path, machine)
    assert result.step_executed
    return _turn(step_executed=True)


def _stop(**fields):
    return lambda agent, machine, state_path: _turn(**fields)


def test_a_live_free_play_action_is_recorded_receipted_and_accounted(tmp_path):
    """Sol's directive: the row, the FREE_PLAY receipt and the final census all carry the action."""
    run = _live(tmp_path, [_rest_and_play, _stop(planned_stop="done")])
    machine = run.agent._gate_machine
    assert [record.action.id.name for record in run.game.game_run.history] == ["ACTION1"]
    (row,) = machine.transition_index
    assert row["transition_id"] == 1 and row["gate_id"] == PLAY and row["action"]["action"] == "ACTION1"
    (event,) = [json.loads(line) for line in (tmp_path / "fixture_gate_events.jsonl").read_text().splitlines()]
    assert event["receipt"] == FREE_PLAY and event["transition_id"] == 1
    assert event["evidence_id"] == row["evidence_id"]  # the row and the receipt are the same transition
    (level,) = _model(run)["levels"]
    assert level["record"]["transition_ids"] == [1]
    assert level["record"]["journal_check"]["ok"] is True
    assert level["record"]["journal_check"]["executed"] == level["record"]["journal_check"]["recorded"] == 1
    assert level["accounting"] == {"status": "ACCOUNTED", "missing": []}


def test_a_controlled_stop_that_ends_the_run_is_persisted_as_such(tmp_path):
    run = _live(tmp_path, [_rest_and_play, _stop(controlled_stop="no-progress tool loop")])
    assert run.game.game_run.solver_note == "controlled_stop: no-progress tool loop"
    assert _model(run)["manifest"]["persist_reason"] == "CONTROLLED_STOP"


def test_a_controlled_stop_that_rests_the_gates_is_not_the_runs_end(tmp_path):
    """Submission mode (D-3): the stop rests the level in normal play, and play resumes."""
    script = [_stop(controlled_stop="contract-repair loop"), _rest_and_play, _stop(planned_stop="done")]
    run = _live(tmp_path, script, rest_on_controlled_stop=True)
    assert run.turns == [0, 1, 2]  # play resumed after the rest
    assert run.agent._gate_machine.gate_id == PLAY
    assert _model(run)["manifest"]["persist_reason"] == "RUN_END"


def test_a_second_controlled_stop_in_normal_play_ends_the_run(tmp_path):
    script = [_stop(controlled_stop="contract-repair loop"), _rest_and_play,
              _stop(controlled_stop="no-progress tool loop")]
    run = _live(tmp_path, script, rest_on_controlled_stop=True)
    assert run.turns == [0, 1, 2]
    assert _model(run)["manifest"]["persist_reason"] == "CONTROLLED_STOP"


@pytest.mark.parametrize("mode", ["observe", "tool", "controller"])
def test_a_non_gated_mode_never_writes_the_canonical_model(tmp_path, mode):
    """Sol's ruling 2: canonical v2 output is scoped to gated mode; an existing file is left untouched."""
    canonical = tmp_path / "virelai" / HarnessSolver()._run_stem("fixture", 0) / "world_model.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(b'{"schema":"virelai-world-model-v2"}')
    run = _live(tmp_path, [_stop(planned_stop="done")], mode=mode)
    assert run.turns == [0]
    assert canonical.read_bytes() == b'{"schema":"virelai-world-model-v2"}'

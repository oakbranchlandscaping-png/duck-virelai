"""WO-RUNTIME-01 §11: the seven public terminal stops and the four controller-side rests, reproduced fail-first.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Labels (Sol's ruling 2, 2026-10-20):

* the seven stops are **exact stopping call, scripted state**: each turn's final tool call is the verbatim code from
  its public-25 prompt log (``runtime01_public_stop_calls.json``, sha256-pinned; only a stale capability token is
  rebound to the live one), played against the production agent in normal play after a rested ladder (the state
  every stop's ledger shows), with the stop's own read-only lead-in before the correction;
* re86, sc25 and wa30 (D22) and ar25 (D-2) are **ledger-faithful scripted reproductions** pinned to the exported
  ledger rows (``runtime01_rest_rows.json``); they are not exact frame replays.

On the base each stop ends the game (``_turn_ends_game``) and each rest abandons the ladder; after the build each
continues through the correct recovery.
"""
from __future__ import annotations

import hashlib
import json
import re
from types import SimpleNamespace

import pytest

from runtime01_support import FIXTURES, STOP_CALLS, PlayRun, Script
from inference.framework.record_replay import load_record, replay
from inference.framework.solver import _turn_ends_game
from inference.framework.virelai_gates import PLAY_GATE_ID

STOPS = json.loads(STOP_CALLS.read_text())["stops"]
RESTS = json.loads((FIXTURES / "runtime01_rest_rows.json").read_text())["worlds"]
TOKEN = re.compile(r"'P1_[A-Za-z0-9_\-]+'")


def _verbatim(stop: dict, token: str) -> str:
    assert hashlib.sha256(stop["code"].encode()).hexdigest() == stop["code_sha256"]
    return TOKEN.sub(repr(token), stop["code"])


def _seed_noop(run: PlayRun, code: str) -> None:
    """sb26's stop was R-8's refusal: the scripted state holds that same-board no-effect memory (t33)."""
    from inference.framework.g4_relations import masked_address
    from inference.framework.virelai_gates import _canonical

    match = re.search(r"'row': (\d+), 'col': (\d+)", code)
    if match is None:
        return
    machine = run.agent._gate_machine
    action = {"action": "ACTION6", "row": int(match.group(1)), "col": int(match.group(2))}
    key = _canonical([action, masked_address([list(row) for row in run.world.grid], machine.counter.mask_law)])
    machine._adapters[PLAY_GATE_ID]._noops[key] = [33]


@pytest.mark.parametrize("stop", STOPS, ids=[stop["world"][:4] for stop in STOPS])
def test_each_public_stop_continues_with_a_controller_action(tmp_path, monkeypatch, stop):
    lead_in = [f"print({n})" for n in range(1, 9)]  # the stop's read-only lead-in that drew the correction
    script = Script(lead_in + ["STOP"])
    run = PlayRun(tmp_path, monkeypatch, script)
    run.to_play()
    call = _verbatim(stop, run.live_token())
    script.items = lead_in + [call]
    if stop["class"] == "ACTION_REFUSED_BY_HARNESS":
        _seed_noop(run, call)
    before = len(run.env_calls)
    result = run.turn()
    assert len(run.env_calls) == before  # the stopping turn executed nothing, as in the run
    assert result.turn_outcome == "RECOVERABLE_NO_ACTION"
    expected = {"MALFORMED_ACTION": {"MALFORMED_ACTION"}, "ACTION_REFUSED_BY_HARNESS": {"ACTION_REFUSED"},
                "REPEATED_READ_ONLY_INSPECTION": {"READ_ONLY_REPEAT", "PYTHON_ERROR"},
                "REPEATED_LIBRARY_QUERY": {"READ_ONLY_REPEAT", "PYTHON_ERROR"}}[stop["class"]]
    assert result.recovery_reason in expected
    assert _turn_ends_game(result, SimpleNamespace(solver_note=None, state="playing")) is False
    calls = len(script.requests)
    resumed = run.turn()
    assert resumed.step_executed and len(run.env_calls) == before + 1 and len(script.requests) == calls
    assert run.rows("_probe_envelopes.jsonl")[-1]["executor"] == "CONTROLLER"


@pytest.mark.parametrize("world", [w for w in RESTS if w["mechanism_inferred"] == "D22"],
                         ids=lambda w: w["world"][:4])
def test_d22_reproduction_closes_g2_and_opens_g3(monkeypatch, world):
    from inference.agent.controller_turn import run_controller_turn
    from runtime01_support import guarded_agent  # noqa: F401  (the agent below is the production one)
    from inference.agent.tool_agent import ToolAgent

    assert world["gate_before_rest"] == "G2-COUNTER"
    assert all(len(row["sha256"]) == 64 for row in world["rows"])
    machine = replay(load_record("tests/fixtures/ls20_kaggle_unified_v1_record.json.gz"), max_steps=10,
                     measure=False).machine
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True)
    agent._gate_machine = machine
    monkeypatch.setattr(agent, "_ensure_gate_machine", lambda _path: machine)
    monkeypatch.setattr(machine, "legal_move_status",
                        lambda: {"gate_id": machine.gate_id, "legal": machine.gate_id != "G2-COUNTER",
                                 "reason": "scripted G2 dead end after its controller steps"})
    from pathlib import Path
    import tempfile

    log = Path(tempfile.mkdtemp()) / "analyzer.txt"
    state = log.with_name("x_runtime_state.json")
    for _turn in range(3):
        agent._step_env_callback = lambda payload: {"executed": False}
        run_controller_turn(agent, state, 10, None, log)
        if machine.gate_id != "G2-COUNTER":
            break
    assert machine._adapters[PLAY_GATE_ID].forced is None  # on the base: the level rested here
    assert machine.target_journal.active_product("G2-COUNTER").payload["status"] == "UNRESOLVED"
    assert machine.gate_id == "G3-LEVERS"


def test_ar25_reproduction_closes_the_refused_g3_question_and_g3_continues(monkeypatch, tmp_path):
    from inference.agent.controller_turn import run_controller_turn
    from inference.agent.tool_agent import ToolAgent

    world = next(w for w in RESTS if w["world"].startswith("ar25"))
    assert [row["outcome"] for row in world["rows"]][1:4] == ["controller_refused"] * 3
    machine = replay(load_record("tests/fixtures/vc33_kaggle_carry_v7_record.json.gz"), max_steps=8,
                     measure=False).machine
    assert machine.gate_id == "G3-LEVERS"
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True)
    agent._gate_machine = machine
    monkeypatch.setattr(agent, "_ensure_gate_machine", lambda _path: machine)

    def refuse(*_args, **_kwargs):
        raise RuntimeError("scripted: the gate refused the controller's action")

    monkeypatch.setattr(agent, "_gate_probe_begin", refuse)
    agent._step_env_callback = lambda payload: {"executed": False}
    log = tmp_path / "analyzer.txt"
    for _turn in range(5):  # the first turn answers G3's dossier and hands the choice to Duck; then 3 refusals + close
        agent._step_env_callback = lambda payload: {"executed": False}
        run_controller_turn(agent, tmp_path / "x_runtime_state.json", 8, None, log)
    assert machine._adapters[PLAY_GATE_ID].forced is None
    assert machine.gate_id == "G3-LEVERS"
    states = {s.state for s in machine._adapters["G3-LEVERS"].lifecycle_journal.entities.values()}
    assert "BUDGET_STOPPED" in states

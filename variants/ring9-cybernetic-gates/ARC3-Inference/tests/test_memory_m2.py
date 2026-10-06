"""Memory stage M-2 (R9-R08): the controller executor carries ft09 from G0 to G3 with no model call.

Author: Claude (Alpha build seat), 2026-09-29. DESIGN_VIRELAI_MEMORY_v2 §5.5, §10 (T6); memory law
M8; rulings D2 (G0-G3 without Duck) and D5 (G3 inherits G2's total nulls).

The world is ft09 continued from the live v2 record (``ft09_world.py``). The agent is the production
``ToolAgent`` with a model that fails the test if it is ever called before G3 closes.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from ft09_world import V2_RECORD, Ft09World
from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, Frame, HistoryEntry, write_runtime_state
from inference.agent.tool_agent import ToolAgent
from inference.framework import controller_executor as executor
from inference.framework.controller_executor import (
    CONTROLLER,
    DUCK,
    controller_answer,
    next_owned_step,
    wake_reason,
    wake_signals,
)
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import CyberneticGateMachine

_TOOL = Path(__file__).resolve().parents[1] / "tools" / "record_from_artifacts.py"
_SPEC = importlib.util.spec_from_file_location("record_from_artifacts", _TOOL)
record_tool = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(record_tool)

V2_G2_ACTIONS = 57


class ModelCalled(AssertionError):
    pass


class Run:
    """The production agent on the ft09 world, driven the way ``solver.play`` drives it."""

    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        self.world = Ft09World()
        self.state_path = tmp_path / f"ft09_{RUNTIME_STATE_FILENAME}"
        self.history: list[HistoryEntry] = []
        self.env_calls: list[dict] = []
        self.model_prompts: list[str] = []
        write_runtime_state(self.state_path, current_frame=self._frame(), history=[])
        self.agent = ToolAgent(
            model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
            controller_executor_enabled=True,
        )
        monkeypatch.setattr(self.agent, "_ensure_session", lambda _path: None)
        monkeypatch.setattr(self.agent, "_chat_completion", self._model)

    def _frame(self) -> Frame:
        return Frame(grid=tuple(tuple(row) for row in self.world.grid), step=self.world.transition_id, level=1)

    def _model(self, messages, **_kwargs):
        self.model_prompts.append(json.dumps(messages[-1].get("content"), default=str))
        raise ModelCalled(f"the model was called at {self.agent._gate_machine.gate_id}")

    def step_env(self, payload: dict) -> dict:
        self.env_calls.append(payload)
        outcome = self.world.step(payload["actions"][0])
        self.history.append(HistoryEntry(action="ACTION6", frame=self._frame()))
        write_runtime_state(self.state_path, current_frame=self._frame(), history=self.history)
        return {
            "executed": True, "action_num": self.world.transition_id, "transition_id": self.world.transition_id,
            "level": 1, "state": "NOT_FINISHED", "valid_actions": ["ACTION6"],
            "board_changed": bool(outcome["changed_cells"]), "done": False, "level_completed": False,
            "game_over": False,
        }

    def turn(self):
        return self.agent.analyze(
            self.state_path, self.world.transition_id, valid_actions=["ACTION6"], step_env=self.step_env,
            analysis_step=self.world.transition_id + 1,
        )

    def until_duck(self, limit: int = 400) -> int:
        turns = 0
        while not self.model_prompts and turns < limit:
            result = self.turn()
            turns += 1
            assert result is None or not result.fatal_failure
        return turns

    def rows(self, suffix: str) -> list[dict]:
        path = self.state_path.with_name(self.state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", suffix))
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture(scope="module")
def ft09_run(tmp_path_factory):
    monkeypatch = pytest.MonkeyPatch()
    run = Run(tmp_path_factory.mktemp("ft09"), monkeypatch)
    run.until_duck()
    yield run
    monkeypatch.undo()


def test_t6_ft09_g0_to_g3_closure_with_zero_model_calls(ft09_run):
    """T6: the controller closes G0-G3 (and, since R9-R10, certifies G4.1): the first model call is
    Duck's orientation turn at G4-A."""
    machine = ft09_run.agent._gate_machine
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    inventory = machine.target_journal.active_product("G3-LEVERS").payload
    assert len(inventory["lever_entities"]) == 5
    assert machine.target_journal.active_product("G4-REACTIONS") is not None
    assert len(ft09_run.model_prompts) == 1  # exactly one attempted call: Duck's orientation turn
    assert "CONTROLLER HANDOFF" in ft09_run.model_prompts[0]
    assert "SUBMIT_ORIENTATION" in ft09_run.model_prompts[0]
    assert len(ft09_run.env_calls) == 67  # first-witness G3 removes five confirmation actions


def test_one_action_per_turn_and_every_artifact_says_who_acted(ft09_run):
    envelopes = ft09_run.rows("_probe_envelopes.jsonl")
    assert len(envelopes) == len(ft09_run.env_calls) == 67
    assert all(len(call["actions"]) == 1 for call in ft09_run.env_calls)
    assert {row["executor"] for row in envelopes} == {CONTROLLER}
    assert {row["schema"] for row in envelopes} == {"virelai-cybernetic-gates-v1"}
    assert {json.dumps(row["protocol"]) for row in envelopes} == {'{"g3_inherits_g2_nulls": true}'}
    answers = ft09_run.rows("_gate_answers.jsonl")
    assert [row["gate_id"] for row in answers] == [
        "G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS", *["G4-REACTIONS"] * 5,
    ]
    assert {row["executor"] for row in answers} == {CONTROLLER}
    ledger = ft09_run.rows("_turn_ledger.jsonl")
    controller_rows = [row for row in ledger if row["executor"] == CONTROLLER]
    assert len(controller_rows) == 67
    assert all(row["request_count"] == 0 and row["step_executed"] for row in controller_rows)


def test_the_controller_repeats_ducks_live_g2_search_and_inherits_its_nulls(ft09_run):
    """G2 takes the same 57 actions Duck took live; G3 then re-clicks none of G2's 54 total nulls."""
    steps = load_record(V2_RECORD)["steps"]
    recorded = [step["action"] for step in steps]
    taken = [call["actions"][0] for call in ft09_run.env_calls]
    assert taken[:V2_G2_ACTIONS - 1] == recorded[:V2_G2_ACTIONS - 1]  # the search, in rank order
    lever = ft09_run.agent._gate_machine._adapters["G3-LEVERS"]
    assert lever._inheritance.count == 54
    g2_nulls = {(step["action"]["row"], step["action"]["col"]) for step in steps[:V2_G2_ACTIONS] if not step["changed"]}
    g3_clicks = {(a["row"], a["col"]) for a in taken[V2_G2_ACTIONS:]}
    assert not g2_nulls & g3_clicks


def test_the_run_replays_offline_under_its_recorded_protocol(ft09_run, tmp_path):
    record = record_tool.build_record(ft09_run.state_path.parent, "ft09", "ft09-offline")
    assert record["protocol"] == {
        "g3_inherits_g2_nulls": True,
        "replay_from_g0": True,
        "legacy_g3_confirmation_replay": False,
    }
    out = tmp_path / "record.json.gz"
    record_tool.write_record(record, out)
    result = replay(load_record(out), measure=False)
    assert (result.steps_replayed, result.stopped) == (67, None)
    assert result.machine.gate_id == "G4.2-LEVER-ORBITS"  # the anatomy answers replay too


def test_wake_does_not_transfer_a_computable_step_to_duck(tmp_path, monkeypatch):
    run = Run(tmp_path, monkeypatch)
    run.turn()
    run.agent._controller.wake = "a synthetic stop condition"
    run.turn()
    assert run.model_prompts == []
    assert len(run.env_calls) == 2
    assert run.agent._controller.wake is None
    log = run.state_path.with_name(f"{run.state_path.stem}_analyzer.txt").read_text()
    assert "retaining controller ownership after wake: a synthetic stop condition" in log


# ---- ownership and stop-and-wake, each in a synthetic case -------------------------------------

def _ft09_machine_at(gate_id: str) -> tuple[CyberneticGateMachine, Ft09World]:
    world = Ft09World()
    machine = CyberneticGateMachine(valid_actions=world.valid_actions, initial_grid=world.grid)
    while machine.gate_id != gate_id:
        step = next_owned_step(machine)
        assert step.owner == CONTROLLER, step.reason
        if step.answer is not None:
            machine.submit_answer(step.answer)
            continue
        probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
        machine.record_outcome(probe, world.step(step.action))
    return machine, world


def test_navigation_g0_and_exact_g1_probes_belong_to_controller_but_explanation_is_ducks():
    nav = CyberneticGateMachine(valid_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION4"], initial_grid=[[0, 1], [1, 0]])
    g0 = next_owned_step(nav)
    assert (g0.owner, g0.kind, g0.gate_id) == (CONTROLLER, executor.ANSWER, "G0-ACTION-METADATA")
    nav.submit_answer(g0.answer)
    expected = ["ACTION1", "ACTION1", "ACTION2", "ACTION2", "ACTION3", "ACTION3", "ACTION4", "ACTION4"]
    observed = []
    for transition, action_name in enumerate(expected, 1):
        step = next_owned_step(nav)
        assert (step.owner, step.kind, step.action) == (
            CONTROLLER, executor.ACTION, {"action": action_name},
        )
        probe = nav.validate_probe({"probe_token": step.probe_token}, [step.action])
        nav.record_outcome(probe, {
            "transition_id": transition, "board_changed": True,
            "changed_cell_count": 1, "changed_cells": [],
        })
        observed.append(step.action["action"])
    assert observed == expected
    answer_step = next_owned_step(nav)
    assert answer_step.owner == DUCK
    assert "explanation" in answer_step.reason


def test_navigation_g1_demonstration_returns_to_controller_and_card_retains_the_model():
    from inference.framework.card_builder import build_card

    nav = CyberneticGateMachine(valid_actions=["ACTION1"], initial_grid=[[0, 1], [1, 0]])
    nav.submit_answer(next_owned_step(nav).answer)
    for transition in (1, 2):
        step = next_owned_step(nav)
        probe = nav.validate_probe({"probe_token": step.probe_token}, [step.action])
        nav.record_outcome(probe, {
            "transition_id": transition, "board_changed": True,
            "changed_cell_count": 1, "changed_cells": [],
        })
    evidence = [item["evidence_id"] for item in nav.ego.evidence]
    nav.submit_answer({
        "answer_id": "A-nav-controller-first", "answer_kind": "embodied ego",
        "subjects": ["the directly controlled visible component"],
        "mechanism": "ACTION1 directly changes the same candidate ego while the surrounding field remains fixed",
        "action_laws": {"ACTION1": "repeats the observed candidate transformation"},
        "conditions": [], "constraints": [], "evidence_refs": evidence,
        "competing_models": ["the same component changes autonomously"],
        "falsifier": "the candidate fails to change on the next legal ACTION1",
        "novel_prediction": {
            "action": {"action": "ACTION1"}, "predicate": "ANY_CHANGE",
            "scope": {"representation": "CELLS", "cells": [[0, 1]]},
            "because": "the observed direct action law repeated twice",
            "novelty": "this test begins after the completed Delphi pair",
        },
        "limitations": ["collision behavior remains untested"],
    })
    card = build_card(nav).payload
    assert card["subject"]["accepted_model"]["action_laws"] == {
        "ACTION1": "repeats the observed candidate transformation",
    }
    assert card["subject"]["frozen_prediction"]["action"] == {"action": "ACTION1"}
    demonstration = next_owned_step(nav)
    assert (demonstration.owner, demonstration.kind, demonstration.action) == (
        CONTROLLER, executor.ACTION, {"action": "ACTION1"},
    )


def test_orientation_turn_belongs_to_duck():
    machine, _world = _ft09_machine_at("G4.2-LEVER-ORBITS")
    step = next_owned_step(machine)
    assert (step.owner, step.gate_id, step.reason) == (DUCK, "G4.2-LEVER-ORBITS", "the orientation turn is due")


def test_an_open_trigger_record_is_ducks_prediction_to_choose():
    machine, _world = _ft09_machine_at("G2-COUNTER")
    template = {"novel_prediction": {}, "trigger_options": {"record": {"class": "OPEN"}}}
    answer, reason = controller_answer(machine, {"answer_template": template})
    assert answer is None and "OPEN" in reason


def test_a_refused_controller_answer_hands_the_gate_to_duck():
    machine, _world = _ft09_machine_at("G2-COUNTER")
    while next_owned_step(machine).answer is None:
        step = next_owned_step(machine)
        probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
        machine.record_outcome(probe, _world.step(step.action))
    step = next_owned_step(machine)
    assert next_owned_step(machine, refused={step.refusal_key}).owner == DUCK


@pytest.mark.parametrize("result, event, expected", [
    ({"level_completed": True}, {}, "boundary event"),
    ({"game_over": True}, {}, "boundary event"),
    ({}, {"evidence_id": "E-1", "counter_comparison": {"outcome": "CONTRADICTED", "evidence_ref": "E-1"}}, "contradicted"),
    ({}, {"evidence_id": "E-2", "counter_comparison": {"outcome": "CONTRADICTED", "evidence_ref": "E-1"}}, None),
    ({}, {"confirmation": {"status": "CONTRADICTED"}}, "confirmation was CONTRADICTED"),
    ({}, {"attribution": {"disposition": "UNRESOLVED_ATTRIBUTION"}}, "UNRESOLVED_ATTRIBUTION"),
    ({}, {"bounded_ambiguity": {"disposition": "AMBIGUOUS_EGO_MASKED"}}, "ambiguous"),
    ({}, {"gate_id": "G2-COUNTER", "gate_status_after": "UNRESOLVED"}, "UNRESOLVED"),
])
def test_each_stop_and_wake_condition_fires(result, event, expected):
    machine, _world = _ft09_machine_at("G3-LEVERS")
    reason = wake_reason(machine, event, result)
    assert (reason is None) if expected is None else (expected in reason)


def test_a_rejected_counter_candidate_wakes_duck():
    machine, _world = _ft09_machine_at("G2-COUNTER")
    before = wake_signals(machine)
    machine.counter._rejected_candidates.append({"candidate_id": "C", "reason": "r", "violations": []})
    assert "rejected" in wake_reason(machine, {}, {}, before)


def test_a_nearly_spent_counter_wakes_duck(monkeypatch):
    machine, _world = _ft09_machine_at("G3-LEVERS")
    assert wake_reason(machine, {}, {}) is None
    monkeypatch.setattr(executor, "world_budgets", lambda _machine: {"counter_ticks_remaining": 2})
    assert "2 counter ticks left" in wake_reason(machine, {}, {}, {"ticks": 3})
    assert wake_reason(machine, {}, {}, {"ticks": 2}) is None  # a budget wake fires once, on crossing

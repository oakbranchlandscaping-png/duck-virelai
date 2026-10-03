"""R9-R12: G4-B (levers together), the clean stop at the ladder's end, and the M-5 review fixes.

Author: Claude (Alpha build seat), 2026-09-29.

G4-B is exercised on the real ft09 levers: the live memory-v1 record (tests/fixtures), replayed to
the point where G4-A closed, then continued on the offline ft09 world that record defines. The
end-to-end test drives the production ToolAgent with a card-only Duck through G0 to G4-B and checks
that the run then ends cleanly, with no model call after the ladder.
"""
from __future__ import annotations

import importlib.util
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from ft09_world import V1_RECORD, Ft09World
from inference.framework.annotation_lane import submit_notes
from inference.framework.card_builder import CARD_BUDGET, build_card, world_model_digest
from inference.framework.controller_executor import ladder_end, next_owned_step
from inference.framework.g4_orbits import G4OrbitError, validate_orbit_answer
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import GateContractError

RELATIONS = "G4-B-LEVER-RELATIONS"
ORBITS = "G4.2-LEVER-ORBITS"
TILES = {  # the eight ft09 levers the live run found, by click
    "E0053": (36, 36), "E0054": (36, 44), "E0055": (36, 52), "E0056": (44, 36),
    "E0057": (44, 52), "E0060": (52, 36), "E0061": (52, 44), "E0062": (52, 52),
}


def _click(entity: str) -> dict:
    row, col = TILES[entity]
    return {"action": "ACTION6", "row": row, "col": col}


@pytest.fixture
def g4b():
    return start_g4b()


def start_g4b():
    """The live v1 record replayed to G4-A's close, oriented, on the offline world it defines."""
    record = load_record(V1_RECORD)
    result = replay(record, measure=False)
    world = Ft09World(record)
    world.grid = [row[:] for row in result.grid]
    world.transition_id = max(step["transition_id"] for step in record["steps"])
    notes = [{"subject": "WORLD", "kind": "NAME", "text": "eight tiles that each toggle their own colour"}]
    submit_notes(result.machine, notes, source="ORIENTATION")  # the live orientation is not in the record
    return result.machine, world


def _predict(machine, entity: str, expected: dict | None = None, **extra) -> object:
    return machine.submit_answer({
        "answer_kind": "LEVER_PREDICTION", "action": _click(entity),
        "expected": expected if expected is not None else {entity: "STEPS"},
        "elsewhere": "NO_CHANGE", "because": f"pressing {entity} should step only its own tile", **extra,
    })


def _take(machine, world) -> dict:
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    return machine.record_outcome(probe, world.step(capability["actions"][0]))


def _ledger(machine) -> list[dict]:
    return machine.relations_view()["predictions"]


# ---- the gate ---------------------------------------------------------------------------------

def test_g4b_opens_after_g4a_on_the_real_ft09_levers_and_asks_for_a_prediction(g4b):
    machine, _world = g4b
    assert machine._adapters[ORBITS].assess().disposition == "SATISFIED"
    assert (machine.gate_id, machine.status) == (RELATIONS, "ANSWER_REQUIRED")
    card = build_card(machine)
    payload = card.payload
    assert payload["next_operation"] == "SUBMIT_GATE_ANSWER"
    assert payload["answer_template"]["answer_kind"] == "LEVER_PREDICTION"
    levers = payload["subject"]["levers"]
    assert len(levers) == 6 and payload["subject"]["levers_not_shown"] == 2  # A6: flat in the lever count
    states = {item["entity_id"]: item["state_now"] for item in levers}
    assert states["E0053"] == "S1" and set(states.values()) == {"S0", "S1"}  # G2 clicked E0053 once
    assert {item["class"] for item in levers} == {"TOGGLE"}
    assert len(card.render()) <= CARD_BUDGET and not card.over_budget
    owner = next_owned_step(machine)
    assert owner.owner == "DUCK" and "the next prediction" in owner.reason


def test_a_frozen_prediction_is_taken_exactly_by_the_controller_and_graded_on_the_masked_board(g4b):
    machine, world = g4b
    _predict(machine, "E0053")
    assert machine.gate_view()["next_operation"] == "CONTROLLER_TAKES_PREDICTION"
    step = next_owned_step(machine)
    assert (step.owner, step.action) == ("CONTROLLER", _click("E0053"))
    capability = machine.next_probe_capability()
    with pytest.raises(GateContractError, match="exact actions"):
        machine.validate_probe({"probe_token": capability["probe_token"]}, [_click("E0054")])
    _take(machine, world)
    graded = _ledger(machine)[0]
    assert graded["status"] == "SUPPORTED" and graded["missed"] == []
    assert graded["observed"]["E0053"] == "STEPS" and graded["observed_elsewhere"] == "NO_CHANGE"
    assert graded["transition_id"] > graded["declared_at_transition"]  # graded after it was frozen
    rows = {item["entity_id"]: item["state_now"] for item in machine.relations_view()["levers"]}
    assert (rows["E0053"], rows["E0054"]) == ("S0", "S0")  # E0053 stepped back to its first state


def test_a_wrong_prediction_is_contradicted_and_stays_on_the_record(g4b):
    machine, world = g4b
    _predict(machine, "E0054", {"E0054": "UNCHANGED", "E0053": "STEPS"})
    _take(machine, world)
    graded = _ledger(machine)[0]
    assert graded["status"] == "CONTRADICTED"
    assert sorted(graded["missed"]) == ["E0053", "E0054"]
    _predict(machine, "E0054", {"E0054": "CHANGES"})  # CHANGES is met by a recorded step
    _take(machine, world)
    assert [item["status"] for item in _ledger(machine)] == ["CONTRADICTED", "SUPPORTED"]
    assert build_card(machine).payload["progress"]["progress"]["predictions"] == {"supported": 1, "contradicted": 1}


def test_freezing_rules(g4b):
    machine, _world = g4b
    with pytest.raises(GateContractError, match="unknown lever"):
        _predict(machine, "E0053", {"E9999": "STEPS"})
    with pytest.raises(GateContractError, match="must be one of"):
        _predict(machine, "E0053", {"E0053": "TOGGLES"})
    with pytest.raises(GateContractError, match="at least 5 words"):
        _predict(machine, "E0053", because="toggle")
    _predict(machine, "E0053")
    with pytest.raises(GateContractError, match="frozen and not yet taken"):
        _predict(machine, "E0054")
    with pytest.raises(GateContractError, match="press every lever"):
        machine.submit_answer({"answer_kind": "LEVER_RELATIONS"})


def test_two_outcomes_of_one_action_from_one_board_are_a_missing_condition(g4b, monkeypatch):
    machine, world = g4b
    for _ in range(2):  # S0 -> S1 -> S0: the same masked board as the first press saw
        _predict(machine, "E0053")
        _take(machine, world)
    monkeypatch.setattr(world, "changes", lambda action: [])  # this time the click does nothing
    _predict(machine, "E0053")
    _take(machine, world)
    conditions = machine.relations_view()["missing_conditions"]
    assert len(conditions) == 1 and len(conditions[0]["outcomes"]) == 2
    assert _ledger(machine)[-1]["status"] == "CONTRADICTED"
    assert build_card(machine).payload["progress"]["progress"]["missing_conditions"] == [conditions[0]["condition_id"]]


def _describe(machine, relations: list[dict], **extra) -> object:
    return machine.submit_answer({
        "answer_kind": "LEVER_RELATIONS",
        "description": (
            "Eight tiles in a ring are the levers; each click steps its own tile between two colours, "
            "and no press changed any other tile or the rest of the board."
        ),
        "relations": relations,
        "open_conditions": [],
        "competing_models": ["a tile may depend on another tile's colour on boards not tested"],
        "falsifier": "a later press of one tile changes another tile",
        "limitations": ["tested only from the boards these predictions were made on"],
        **extra,
    })


def test_the_description_needs_every_lever_pressed_and_rests_only_on_supported_predictions(g4b):
    machine, world = g4b
    _predict(machine, "E0053", {"E0053": "UNCHANGED"})
    _take(machine, world)  # P1: contradicted
    for entity in TILES:
        _predict(machine, entity, {entity: "STEPS", "E0055": "STEPS" if entity == "E0055" else "UNCHANGED"})
        _take(machine, world)
    assert build_card(machine).payload["answer_template"]["answer_kind"] == "LEVER_RELATIONS"
    independent = {"levers": ["E0053", "E0055"], "claim": "pressing E0053 left E0055 unchanged here", "prediction_refs": ["P2"]}
    with pytest.raises(GateContractError, match="CONTRADICTED"):
        _describe(machine, [{**independent, "prediction_refs": ["P1"]}])
    with pytest.raises(GateContractError, match="none of its cited predictions pressed or named"):
        _describe(machine, [{**independent, "levers": ["E0053", "E0057"]}])
    with pytest.raises(GateContractError, match="limitations must be a list of strings"):
        _describe(machine, [independent], limitations="a bare string")
    answer = _describe(machine, [independent])
    assert machine._adapters[RELATIONS].assess().disposition == "SATISFIED"
    product = machine.target_journal.active_product(RELATIONS).payload
    assert product["status"] == "COMPLETE" and product["answer"]["answer_id"] == answer.answer_id
    assert [item["status"] for item in product["predictions"]].count("CONTRADICTED") == 1  # kept
    assert any(line.startswith(f"[{RELATIONS}] relations: 8/9 predictions supported") for line in world_model_digest(machine))
    assert machine.gate_id == "G4-C-LEVER-LAW" and ladder_end(machine) is None  # G4-C now tests the description


# ---- the M-5 review fixes ------------------------------------------------------------------------

def test_f2_an_orbit_answer_refuses_a_bare_string_where_a_list_belongs():
    """Live E0056: limitations given as one string were stored as 250 single characters."""
    result = replay(load_record(V1_RECORD), max_steps=79, measure=False)
    lever = result.machine._adapters[ORBITS]
    template = result.machine.gate_view()["answer_template"]
    raw = {**template, "mechanism_explanation": "Each press flips the tile between its two colours and back again.",
           "falsifier": "a later press leaves the tile unchanged", "limitations": "This is one finite run."}
    with pytest.raises(G4OrbitError, match="limitations must be a list of strings"):
        validate_orbit_answer(raw, lever._completed["E0053"].orbit)
    with pytest.raises(G4OrbitError, match="competing_models must be a list of strings"):
        validate_orbit_answer({**raw, "limitations": [], "competing_models": "one model"}, lever._completed["E0053"].orbit)


def _record_tool():
    spec = importlib.util.spec_from_file_location(
        "record_from_artifacts", Path(__file__).resolve().parents[1] / "tools" / "record_from_artifacts.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f3_a_record_keeps_the_harness_reset_and_replays_the_live_restudy():
    record = load_record(V1_RECORD)
    resets = [step for step in record["steps"] if step.get("kind") == "RESET"]
    assert [step["transition_id"] for step in resets] == [89]  # after the GAME_OVER at 88
    orbits = replay(record, measure=False).machine.target_journal.active_product(ORBITS).payload
    assert orbits["life_restudies"] == {"E0056": 1}
    restudied = next(item for item in orbits["orbits"] if item["entity_id"] == "E0056")
    assert restudied["run_status"] == "CONFIRMED"  # as live; without the reset it replayed DIVERGED
    assert set(orbits["lever_classes"].values()) == {"TOGGLE"}
    before = {"row": 0, "col": 0, "before": 1, "after": 1}
    outcomes = [
        {"transition_id": 1, "action": {"action": "ACTION6", "row": 0, "col": 0},
         "changed_cells": [{"row": 0, "col": 0, "before": 1, "after": 2}],
         "site_transitions": [before]},
        {"transition_id": 3, "action": {"action": "ACTION6", "row": 0, "col": 0}, "changed_cells": [],
         "site_transitions": [before]},  # the board went back to 1 between the two probes
    ]
    steps = _record_tool()._steps(outcomes, [[1]])
    assert [(step["transition_id"], step.get("kind")) for step in steps] == [(1, None), (2, "RESET"), (3, None)]
    assert steps[1]["changed"] == [[0, 0, 2, 1]]


# ---- the clean stop -----------------------------------------------------------------------------

def test_the_harness_ends_the_game_cleanly_on_a_planned_stop(tmp_path):
    from inference.agent.tool_agent import AnalyzerTurnResult
    from inference.framework.solver import HarnessSolver, _HarnessGameSession
    from test_duck_native_observer import _Game

    class Game(_Game):
        def finish_game(self):
            self.game_run.state, self.game_run.final_score = "finished", 0.0

    calls: list[int] = []
    analyzer = SimpleNamespace(generated_tokens=0, analyze=lambda *a, **k: calls.append(1) or AnalyzerTurnResult(
        step_executed=False, planned_stop="every built gate is satisfied"))
    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    game = Game()
    game.game_run.__dict__.update(final_score=None, levels_completed=0, number_of_levels=1, actions_per_level=[])
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=analyzer, game_index=0, pass_index=0,
        state_path=tmp_path / "state.json", transcript_path=tmp_path / "t.txt",
        analysis_html_relpath="a.html", stop_event=threading.Event(), viewer_data_path=tmp_path / "v.json",
    )
    session.play()
    assert calls == [1]  # asked once, then stopped: no idle loop
    assert game.game_run.state == "finished"
    assert game.game_run.solver_note == "planned_stop: every built gate is satisfied"


# ---- end to end, production path ---------------------------------------------------------------

class Ft09LiveRun:
    """The production agent on the ft09 world the live v1 record defines, with its death and reset."""

    def __new__(cls, tmp_path, monkeypatch):
        from test_memory_m4 import LivesRun

        class _Run(LivesRun):
            def step_env(self, payload):
                result = super().step_env(payload)
                if self.world.bar_empty():  # L-1, observed live: the bar's last cells end the life
                    self.reset_pending = True
                    result.update(game_over=True, state="GAME_OVER")
                return result

        run = _Run(tmp_path, monkeypatch)
        run.world = Ft09World(load_record(V1_RECORD))
        run.initial = [row[:] for row in run.world.grid]
        from inference.agent.runtime_state import write_runtime_state

        write_runtime_state(run.state_path, current_frame=run._frame(), history=[])
        return run


def test_ft09_offline_follows_the_live_run_then_duck_studies_the_levers_together_and_the_run_stops(tmp_path, monkeypatch):
    from test_memory_m4 import CardDuck

    run = Ft09LiveRun(tmp_path, monkeypatch)
    duck = CardDuck(run)
    monkeypatch.setattr(run.agent, "_chat_completion", duck)
    stop = None
    for _ in range(600):
        result = run.turn()
        if result is not None and getattr(result, "planned_stop", ""):
            stop = result.planned_stop
            break
    assert stop == "every built gate is satisfied, through G4-C; the next slice is not built"
    live = [step["action"] for step in load_record(V1_RECORD)["steps"] if step.get("kind") != "RESET"]
    offline = [call["actions"][0] for call in run.env_calls]
    assert offline[: len(live)] == live  # the controller repeats the live run exactly, death included
    machine = run.agent._gate_machine
    product = machine.target_journal.active_product(RELATIONS).payload
    assert product["status"] == "COMPLETE" and product["unpressed_levers"] == []
    assert [item["status"] for item in product["predictions"]] == ["SUPPORTED"] * 8
    assert duck.calls.count("explain") == 8 + 8 + 1 + 1  # 8 orbits, 8 predictions, the description, G4-C's test
    law = machine.target_journal.active_product("G4-C-LEVER-LAW").payload
    assert law["status"] == "COMPLETE" and law["law_test"]["status"] == "SUPPORTED"
    assert law["description"] == product["answer"]["description"] and law["law_test"]["from_relations"] == [0]
    envelopes = run.rows("_probe_envelopes.jsonl")
    g4b_envelopes = [row for row in envelopes if row["gate_id"] == RELATIONS]
    assert len(g4b_envelopes) == 8 and {row["executor"] for row in g4b_envelopes} == {"CONTROLLER"}
    assert [row["executor"] for row in envelopes if row["gate_id"] == "G4-C-LEVER-LAW"] == ["CONTROLLER"]
    answers = [row for row in run.rows("_gate_answers.jsonl") if row["gate_id"] == RELATIONS]
    assert [row["answer_kind"] for row in answers] == ["LEVER_PREDICTION"] * 8 + ["LEVER_RELATIONS"]
    assert {row["executor"] for row in answers} == {"DUCK"}
    calls_at_stop = len(duck.calls)
    assert getattr(run.turn(), "planned_stop", "")  # asked again, it stops again: no model call
    assert len(duck.calls) == calls_at_stop
    log = run.state_path.with_name(f"{run.state_path.stem}_analyzer.txt").read_text()
    assert "planned stop: every built gate is satisfied" in log
    assert json.dumps(product["answer"]["relations"])  # the description is on the record
    tool = _record_tool()  # and the whole run, G4-B included, replays from its artifacts
    record = tool.build_record(run.state_path.parent, "ft09", "ft09-offline")
    replayed = replay(record, measure=False).machine.target_journal.active_product(RELATIONS).payload
    assert replayed["status"] == "COMPLETE" and [item["status"] for item in replayed["predictions"]] == ["SUPPORTED"] * 8
    assert replayed["answer"]["description"] == product["answer"]["description"]
    replayed_law = replay(record, measure=False).machine.target_journal.active_product("G4-C-LEVER-LAW").payload
    assert replayed_law["status"] == "COMPLETE"


def test_frozen_prediction_changes_ownership_from_duck_to_controller(g4b):
    machine, _world = g4b
    assert next_owned_step(machine).owner == "DUCK"  # semantic turn: nothing frozen
    _predict(machine, "E0053")
    assert next_owned_step(machine).owner == "CONTROLLER"  # the bound test action is now exact

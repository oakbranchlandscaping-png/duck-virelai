"""Memory stage M-4 (R9-R10): the G4 economy and lives, on the production path.

Author: Claude (Alpha build seat), 2026-09-29. DESIGN_VIRELAI_MEMORY_v2 §5.5 (the G4.1 and G4-A
rows), §6 (lives), §10 (T8); rulings D3 (the controller runs each lever, Duck explains, Duck may ask
for an extra run) and D4 (a lever study continues across a death on the same level); the
Director's 2026-09-29 ruling to build the time and action budget wakes here.

Duck is a card-only model: each time the production ToolAgent calls it, it reads the card the
agent built and writes the one tool call that card asks for (orientation, an orbit explanation, or
a scripted extra-run request). Every other step is the controller's.
"""
from __future__ import annotations

import json

import pytest

import card_duck
from inference.agent.runtime_state import HistoryEntry, write_runtime_state
from inference.agent.tool_agent import _ChatCompletionResult
from inference.framework.card_builder import build_card
from inference.framework.controller_executor import CONTROLLER, wake_reason
from test_memory_m2 import Run

ORBITS = "G4.2-LEVER-ORBITS"
NOTES = [{"subject": "WORLD", "kind": "PROPOSAL", "text": "run every lever until it cycles"}]


class CardDuck:
    """Answers only from the card; optionally asks once for an extra run before its first explanation."""

    def __init__(self, run: "LivesRun", rerun_presses: int = 0) -> None:
        self.run = run
        self.rerun_presses = rerun_presses
        self.calls: list[str] = []

    def __call__(self, messages, **_kwargs):
        machine = self.run.agent._gate_machine
        card = build_card(machine).payload
        if card["next_operation"] == "SUBMIT_ORIENTATION":
            code, kind = f"import json\nvirelai('orient', notes=json.loads({json.dumps(NOTES)!r}))", "orient"
        elif card.get("answer_template") and self.rerun_presses:
            entity = card["answer_template"]["entity_id"]
            code, kind = f"virelai('rerun', id={entity!r}, presses={self.rerun_presses})", "rerun"
            self.rerun_presses = 0
        elif card.get("answer_template"):
            answer = card_duck._answer(card, None, set())
            code, kind = f"import json\nvirelai('gate_answer', answer=json.loads({json.dumps(answer)!r}))", "explain"
        else:
            action = card_duck._choose(card)
            token = card["current_probe"]["probe_token"]
            code, kind = f"action([{action!r}], decision={{'probe_token': {token!r}}})", "act"
        self.calls.append(kind)
        call = {"id": f"d{len(self.calls)}", "type": "function",
                "function": {"name": "python", "arguments": json.dumps({"code": code})}}
        return _ChatCompletionResult(message={"role": "assistant", "content": "", "tool_calls": [call]},
                                     finish_reason="tool_calls", usage={"prompt_tokens": 1, "completion_tokens": 1})


class LivesRun(Run):
    """The ft09 run, with an optional death: a game over at one transition, then the harness reset."""

    def __init__(self, tmp_path, monkeypatch, *, die_at: int | None = None) -> None:
        super().__init__(tmp_path, monkeypatch)
        self.die_at = die_at
        self.reset_pending = False
        self.initial = [row[:] for row in self.world.grid]

    def step_env(self, payload: dict) -> dict:
        result = super().step_env(payload)
        if self.die_at is not None and self.world.transition_id == self.die_at:
            self.reset_pending = True
            result.update(game_over=True, state="GAME_OVER", valid_actions=["ACTION6"])
        return result

    def turn(self):
        if self.reset_pending:  # what solver.play does after a game over: an automatic RESET
            self.reset_pending = False
            self.world.grid = [row[:] for row in self.initial]
            self.world.transition_id += 1
            self.history.append(HistoryEntry(action="RESET", frame=self._frame()))
            write_runtime_state(self.state_path, current_frame=self._frame(), history=self.history)
        return super().turn()

    def until_satisfied(self, limit: int = 400) -> None:
        machine = None
        for _ in range(limit):
            self.turn()
            machine = self.agent._gate_machine
            if machine is not None and g4a_complete(machine):
                return
        raise AssertionError(f"not satisfied: {machine.gate_id} {machine.status}")


def g4a_complete(machine) -> bool:
    """G4-A satisfied: every lever explained (since R9-R12 the ladder then moves on to G4-B)."""
    product = machine.target_journal.active_product(ORBITS)
    return product is not None and product.payload["phase1_status"] == "COMPLETE"


def _run(tmp_path, monkeypatch, **options):
    rerun = options.pop("rerun_presses", 0)
    run = LivesRun(tmp_path, monkeypatch, **options)
    duck = CardDuck(run, rerun_presses=rerun)
    monkeypatch.setattr(run.agent, "_chat_completion", duck)
    run.until_satisfied()
    return run, duck, run.agent._gate_machine


def test_ft09_reaches_a_satisfied_g4a_with_duck_orienting_and_explaining(tmp_path, monkeypatch):
    """D3 + the G4.1 split: the controller certifies anatomy and runs every lever; Duck orients once
    and explains each of the five confirmed orbits. The counter warning crosses two ticks left
    during the fifth lever, but does not transfer the already-computable press to Duck."""
    run, duck, machine = _run(tmp_path, monkeypatch)
    orbits = machine.target_journal.active_product(ORBITS).payload
    assert orbits["phase1_status"] == "COMPLETE" and len(orbits["lever_entities"]) == 5
    assert duck.calls == ["orient", *["explain"] * 5]
    log = run.state_path.with_name(f"{run.state_path.stem}_analyzer.txt").read_text()
    assert "planned stop" not in log
    assert len(run.env_calls) == 87  # G0-G3: 67 first-witness actions; G4-A: 20 presses
    answers = run.rows("_gate_answers.jsonl")
    anatomy = [row for row in answers if row["gate_id"] == "G4-REACTIONS"]
    assert len(anatomy) == 5 and {row["executor"] for row in anatomy} == {CONTROLLER}
    orbit_answers = [row for row in answers if row["gate_id"] == ORBITS]
    assert len(orbit_answers) == 5 and {row["executor"] for row in orbit_answers} == {"DUCK"}
    envelopes = run.rows("_probe_envelopes.jsonl")
    assert [row["executor"] for row in envelopes].count("DUCK") == 0
    assert len(envelopes) == len(run.env_calls)


def test_duck_may_ask_for_an_extra_run_and_the_controller_presses_it(tmp_path, monkeypatch):
    run, duck, machine = _run(tmp_path, monkeypatch, rerun_presses=2)
    assert duck.calls[:3] == ["orient", "rerun", "explain"]
    first = machine.target_journal.active_product(ORBITS).payload["orbits"][0]
    click = first["intervention"]
    presses = [call["actions"][0] for call in run.env_calls if call["actions"][0] == click]
    baseline, _, _ = _run(tmp_path / "baseline", monkeypatch)
    plain = [call["actions"][0] for call in baseline.env_calls if call["actions"][0] == click]
    assert len(presses) == len(plain) + 2
    rerun_events = [row for row in machine._adapters[ORBITS]._events if row["run"]["kind"] == "PRESS_AFTER_CONFIRMED_RUN"]
    assert len(rerun_events) == 2  # on the record, and the confirmed run is not rewritten


def test_t8_a_death_mid_study_is_restudied_next_life_and_the_world_model_persists(tmp_path, monkeypatch):
    """T8 (D4): a game over in the middle of G4-A; the reset world is studied again; nothing is lost."""
    first_press = 73 + 1  # G0-G3 take 72 actions; the orientation turn takes none; G4-A starts at 73
    run, duck, machine = _run(tmp_path, monkeypatch, die_at=first_press)
    orbits = machine.target_journal.active_product(ORBITS).payload
    assert orbits["phase1_status"] == "COMPLETE"
    assert orbits["interrupted_lever_entities"] == [] and len(orbits["lever_entities"]) == 5
    assert sum(orbits["life_restudies"].values()) == 1
    assert machine.target_journal.active_product("G3-LEVERS") is not None  # the world model persists
    assert machine.annotations.oriented and machine.annotations.notes  # so do Duck's notes
    assert duck.calls == ["orient", *["explain"] * 5]


@pytest.mark.parametrize("before, result, expected", [
    ({"actions": 11}, {"actions_remaining": 10}, "10 actions left"),
    ({"actions": 10}, {"actions_remaining": 9}, None),  # fires once, on the crossing
    ({"seconds": 200.0}, {"time_remaining_seconds": 90.0}, "90 seconds left"),
    ({"seconds": None}, {"time_remaining_seconds": None}, None),
])
def test_the_action_and_time_budgets_wake_duck_once(before, result, expected):
    from test_memory_m2 import _ft09_machine_at

    machine, _world = _ft09_machine_at("G3-LEVERS")
    reason = wake_reason(machine, {}, result, before)
    assert (reason is None) if expected is None else (expected in reason)


def test_the_whole_g0_to_g4a_run_replays_offline(tmp_path, monkeypatch):
    """Every answer, Duck's and the controller's, is on the record: the run replays to G4-A satisfied."""
    import importlib.util
    from pathlib import Path

    from inference.framework.record_replay import load_record, replay

    tool = Path(__file__).resolve().parents[1] / "tools" / "record_from_artifacts.py"
    spec = importlib.util.spec_from_file_location("record_from_artifacts", tool)
    record_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(record_tool)
    run, _duck, _machine = _run(tmp_path, monkeypatch)
    out = tmp_path / "record.json.gz"
    record_tool.write_record(record_tool.build_record(run.state_path.parent, "ft09", "ft09-offline"), out)
    result = replay(load_record(out), measure=False)
    assert (result.steps_replayed, result.answers_used, result.stopped) == (87, 12, None)
    assert g4a_complete(result.machine) and result.machine.gate_id == "G4-B-LEVER-RELATIONS"

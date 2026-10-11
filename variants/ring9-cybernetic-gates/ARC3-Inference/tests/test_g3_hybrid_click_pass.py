"""WO-G3-DIRECTED, NAV slice piece 1: a HYBRID world's G3 CLICK pass belongs to the controller.

Author: Claude (Alpha build seat), 2026-10-11. Sol's ruling on CLICK revision 2 (relayed by the Director):
"HYBRID may offer two choices: at most one in CLICK and one in NAV ... First repair the HYBRID CLICK pass so
the controller serves its bound click and applies the CLICK handoff. Enable the NAV handoff when NAV selection
and pursuit are built." The fail-first baseline is ``db8a657``, where ``_nav_step`` returned every
``RANKED_CLICK_TARGET`` to Duck ("G3 NAV cannot compute RANKED_CLICK_TARGET").

The world is the k008 development record (ruling 10), a HYBRID game, replayed through the production gate
path to G3's entry (transition 37), then driven by the production ``ToolAgent.analyze`` with the live handoff
on. The environment answers each action with the record's own change when the record took that action at that
transition, and with no change otherwise. The model is a stub that declines the choice: it answers without a
tool call while the turn-time budget runs out.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, Frame, HistoryEntry, write_runtime_state
from inference.agent.tool_agent import ToolAgent, _ChatCompletionResult
from inference.framework import g3_selection
from inference.framework.library_agenda import lever_question_id
from inference.framework.record_replay import load_record, lossless_outcome
from test_g3_directed_click import RECORDS, _replayed

G3_ENTRY = 37  # k008: G2 closes at transition 37; G3 opens in its CLICK phase with five selectable rows


def _same(a: dict, b: dict) -> bool:
    keys = ("action", "row", "col")
    return all(a.get(key) == b.get(key) for key in keys)


class HybridRun:
    """The production agent on k008 from G3's entry, driven the way ``solver.play`` drives it."""

    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        result = pickle.loads(_replayed("k008", G3_ENTRY))
        self.machine, self.grid = result.machine, [list(row) for row in result.grid]
        self.recorded = {int(step["transition_id"]): step for step in load_record(RECORDS["k008"])["steps"]
                         if step.get("kind") != "RESET"}
        self.valid = [item.action for item in self.machine.ego.affordances]
        self.state_path = tmp_path / f"k008_{RUNTIME_STATE_FILENAME}"
        self.history: list[HistoryEntry] = []
        self.env_calls: list[dict] = []
        self.prompts: list[str] = []
        write_runtime_state(self.state_path, current_frame=self._frame(), history=[])
        self.agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                               controller_executor_enabled=True)
        assert self.agent._controller.g3_choice_handoff is True  # the live default (D3)
        self.agent._gate_machine = self.machine
        monkeypatch.setattr(self.agent, "_ensure_session", lambda _path: None)
        monkeypatch.setattr(self.agent, "_chat_completion", self._model)

    @property
    def transition(self) -> int:
        return int(self.machine.observed_through_step)

    def _frame(self) -> Frame:
        return Frame(grid=tuple(tuple(row) for row in self.grid), step=self.transition, level=1)

    def _model(self, messages, **_kwargs):
        """Duck declines the choice: no tool call, and the turn-time budget runs out."""
        content = messages[-1].get("content")
        self.prompts.append(content if isinstance(content, str)
                            else "\n".join(part.get("text", "") for part in content if isinstance(part, dict)))
        self.agent._yield_seconds = 0.0
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    def step_env(self, payload: dict) -> dict:
        self.env_calls.append(payload)
        action = dict(payload["actions"][0])
        transition = self.transition + 1
        step = self.recorded.get(transition)
        changed = step["changed"] if step is not None and _same(step["action"], action) else []
        before = [list(row) for row in self.grid]
        self.grid, _outcome = lossless_outcome(self.grid, transition, action, changed)
        self.history.append(HistoryEntry(action=str(action["action"]),
                                         frame=Frame(grid=tuple(tuple(r) for r in self.grid), step=transition, level=1)))
        write_runtime_state(self.state_path, current_frame=self.history[-1].frame, history=self.history)
        return {
            "executed": True, "action_num": transition, "transition_id": transition, "level": 1,
            "state": "NOT_FINISHED", "valid_actions": list(self.valid), "board_changed": before != self.grid,
            "done": False, "level_completed": False, "game_over": False,
        }

    def turn(self):
        return self.agent.analyze(self.state_path, self.transition, valid_actions=list(self.valid),
                                  step_env=self.step_env, analysis_step=self.transition + 1)

    def rows(self, suffix: str) -> list[dict]:
        path = self.state_path.with_name(self.state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", suffix))
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


@pytest.fixture
def run(tmp_path):
    monkeypatch = pytest.MonkeyPatch()
    yield HybridRun(tmp_path, monkeypatch)
    monkeypatch.undo()


def test_a_declined_handoff_on_the_hybrid_click_pass_is_followed_by_one_controller_click(run):
    """Fail-first on ``db8a657``: the second turn went back to Duck and executed nothing."""
    g3 = run.machine._adapters["G3-LEVERS"]
    assert run.machine.gate_id == "G3-LEVERS" and g3._phase == "CLICK" and g3._world_type == "HYBRID"
    head = run.machine.next_probe_capability()
    assert head["purpose"] == "RANKED_CLICK_TARGET"
    assert sum(1 for row in g3_selection.admission_candidates(g3) if row["selectable"]) >= 2  # a genuine choice

    declined = run.turn()  # the one CLICK handoff: Duck reaches the model and declines
    assert [item["event"] for item in run.rows("_g3_selection_events.jsonl")] == ["HANDOFF"], \
        "no CLICK handoff: the step went to Duck as an uncomputable NAV step"
    assert len(run.prompts) == 1 and run.env_calls == [] and declined is not None and not declined.step_executed
    assert f'"question_id": "{lever_question_id(1, head["target"]["entity_id"])}"' in run.prompts[0]

    acted = run.turn()  # the controller serves the bound click
    assert acted is not None and acted.step_executed, "the CLICK pass went back to Duck"
    assert len(run.prompts) == 1 and len(run.env_calls) == 1
    assert run.env_calls[0]["actions"] == head["actions"] and run.env_calls[0]["actor"] == "CONTROLLER"

    envelope, receipt, row = run.rows("_probe_envelopes.jsonl")[-1], run.rows("_gate_events.jsonl")[-1], \
        run.machine.transition_index[-1]
    assert envelope["executor"] == "CONTROLLER" and envelope["purpose"] == "RANKED_CLICK_TARGET"
    assert envelope["probe_id"] == receipt["probe_id"] == row["probe_id"] == "G3-LEVERS:CLICK:1"
    assert receipt["evidence_id"] == row["evidence_id"] and row["transition_id"] == G3_ENTRY + 1
    assert envelope["target"]["entity_id"] == head["target"]["entity_id"] and ":SEL:" not in envelope["probe_id"]
    ledger = run.rows("_turn_ledger.jsonl")
    assert [(item["executor"], item["outcome"]) for item in ledger] == [
        ("DUCK", "turn_time_budget"), ("CONTROLLER", "controller_step")]
    assert [item["event"] for item in run.rows("_g3_selection_events.jsonl")] == ["HANDOFF", "COVERAGE_RESUMED"]


def test_the_click_pass_offers_no_second_handoff_and_follows_the_record_into_nav(run):
    """The rest of the CLICK pass is the controller's; the NAV handoff stays off (Sol: until NAV selection).

    With Duck declining, the controller's six actions are exactly the live run's transitions 38-43: five
    coverage clicks, then NAV's first route step."""
    g3 = run.machine._adapters["G3-LEVERS"]
    run.turn()  # the handoff, declined
    for _ in range(6):
        result = run.turn()
        assert result is not None and result.step_executed and len(run.prompts) == 1  # no second model call
    actions = [call["actions"][0] for call in run.env_calls]
    recorded = [run.recorded[G3_ENTRY + 1 + index]["action"] for index in range(6)]
    assert all(_same(a, b) for a, b in zip(actions, recorded))
    envelopes = run.rows("_probe_envelopes.jsonl")
    assert [item["executor"] for item in envelopes] == ["CONTROLLER"] * 6
    assert [item["purpose"] for item in envelopes] == ["RANKED_CLICK_TARGET"] * 5 + ["PILOT_TO_LEVER_CONTACT"]
    assert [item["probe_id"] for item in envelopes[:5]] == [f"G3-LEVERS:CLICK:{n}" for n in range(1, 6)]
    receipts = run.rows("_gate_events.jsonl")
    assert [item["probe_id"] for item in receipts] == [row["probe_id"] for row in run.machine.transition_index[-6:]]
    assert [item["evidence_id"] for item in receipts] == [row["evidence_id"] for row in run.machine.transition_index[-6:]]
    assert g3._phase == "NAV" and not g3_selection.choice_handoff_due(g3)  # no NAV handoff until NAV selection
    events = [item["event"] for item in run.rows("_g3_selection_events.jsonl")]
    assert events == ["HANDOFF", "COVERAGE_RESUMED"]  # one CLICK handoff for the level


def test_with_the_handoff_off_the_click_pass_is_the_controllers_from_its_first_step(run):
    """Controller-only drivers (the regression guard): no model call at all through the CLICK pass."""
    run.agent._controller.g3_choice_handoff = False
    result = run.turn()
    assert result is not None and result.step_executed and run.prompts == []
    assert run.rows("_probe_envelopes.jsonl")[-1]["probe_id"] == "G3-LEVERS:CLICK:1"
    assert run.rows("_g3_selection_events.jsonl") == []
